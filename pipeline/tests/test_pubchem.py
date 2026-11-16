"""PubChem source behavior with fake HTTP; no live requests."""

import json
from datetime import UTC, datetime
from email.utils import format_datetime

import pytest
import requests

from agrotox.sources.pubchem import PubChemClient


class Response:
    def __init__(self, payload = None, status = 200, error = None, headers = None):
        self.payload = payload
        self.status_code = status
        self.error = error
        self.headers = requests.structures.CaseInsensitiveDict(headers or {})

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}", response = self)

    def json(self):
        if self.error is not None:
            raise self.error
        return self.payload


class FakeHTTP:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


def test_names_are_trimmed_and_encoded_as_one_path_segment():
    http = FakeHTTP(Response({"IdentifierList": {"CID": [101]}}))
    client = PubChemClient(http)
    assert http.calls == []
    assert client.resolve(" α/b ?#% ") == 101
    url, options = http.calls[0]
    assert url == (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
        "%CE%B1%2Fb%20%3F%23%25/cids/JSON"
    )
    assert options["timeout"] == (10, 40)


@pytest.mark.parametrize("query", ["101", " 00101 "])
def test_numeric_queries_bypass_http(query):
    http = FakeHTTP()
    assert PubChemClient(http).resolve(query) == 101
    assert http.calls == []


@pytest.mark.parametrize("query", ["", " ", "0", "000"])
def test_invalid_queries_fail_before_http(query):
    http = FakeHTTP()
    with pytest.raises(ValueError):
        PubChemClient(http).resolve(query)
    assert http.calls == []


@pytest.mark.parametrize("payload, error", [
    ({"IdentifierList": {"CID": []}}, LookupError),
    ({"IdentifierList": {"CID": [101, 102]}}, ValueError),
    ({"IdentifierList": {"CID": [101, 101]}}, ValueError),
    ({}, ValueError), ({"IdentifierList": None}, ValueError),
    ({"IdentifierList": {"CID": "101"}}, ValueError),
    ({"IdentifierList": {"CID": [True]}}, ValueError),
    ({"IdentifierList": {"CID": [0]}}, ValueError),
    ({"IdentifierList": {"CID": ["101"]}}, ValueError),
])
def test_name_resolution_requires_one_valid_cid(payload, error):
    with pytest.raises(error):
        PubChemClient(FakeHTTP(Response(payload))).resolve("alpha")


def test_properties_request_and_response_envelope():
    payload = {"PropertyTable": {"Properties": [{"CID": 101, "SMILES": "C"}]}}
    http = FakeHTTP(Response(payload))
    assert PubChemClient(http).properties(101) == payload
    url, options = http.calls[0]
    base, properties = url.split("/property/")
    assert base == "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/101"
    assert properties.endswith("/JSON")
    assert set(properties.removesuffix("/JSON").split(",")) == {
        "Title", "MolecularFormula", "MolecularWeight", "SMILES", "ConnectivitySMILES",
        "InChI", "InChIKey", "IUPACName",
    }
    assert options["timeout"] == (10, 40)


@pytest.mark.parametrize("payload", [
    {}, {"PropertyTable": None}, {"PropertyTable": {"Properties": []}},
    {"PropertyTable": {"Properties": [{"CID": 102}]}},
    {"PropertyTable": {"Properties": [{"CID": 101}, {"CID": 102}]}},
    {"PropertyTable": {"Properties": [{"CID": True}]}},
])
def test_invalid_properties_remain_errors(payload):
    with pytest.raises(ValueError):
        PubChemClient(FakeHTTP(Response(payload))).properties(101)


def test_toxicity_request_and_validated_response():
    payload = {"Record": {"RecordNumber": 101, "RecordType": "CID", "Section": []}}
    http = FakeHTTP(Response(payload))
    assert PubChemClient(http).toxicity(101) == payload
    url, options = http.calls[0]
    assert url == "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/101/JSON"
    assert options["params"] == {"heading": "Toxicity"}
    assert options["timeout"] == (10, 40)


@pytest.mark.parametrize("payload", [
    {}, {"Record": {}}, {"missing_section": "Toxicity"},
    {"Record": {"RecordNumber": 102, "RecordType": "CID", "Section": []}},
    {"Record": {"RecordNumber": 101, "RecordType": "SID", "Section": []}},
    {"Record": {"RecordNumber": 101, "RecordType": "CID", "Section": "invalid"}},
])
def test_invalid_toxicity_is_never_absence(payload):
    with pytest.raises(ValueError):
        PubChemClient(FakeHTTP(Response(payload))).toxicity(101)


def test_only_toxicity_404_is_missing_without_parsing_error_body():
    http = FakeHTTP(Response(status = 404, error = AssertionError("must not parse body")))
    assert PubChemClient(http).toxicity(101) is None


@pytest.mark.parametrize("method, argument", [("resolve", "alpha"), ("properties", 101)])
def test_identity_404_remains_an_error(method, argument):
    client = PubChemClient(FakeHTTP(Response(status = 404)))
    with pytest.raises(requests.HTTPError):
        getattr(client, method)(argument)


@pytest.mark.parametrize("method, argument", [
    ("resolve", "alpha"), ("properties", 101), ("toxicity", 101),
])
@pytest.mark.parametrize("payload", [[], None, "not an object"])
def test_json_responses_require_objects(method, argument, payload):
    client = PubChemClient(FakeHTTP(Response(payload)))
    with pytest.raises(ValueError):
        getattr(client, method)(argument)


def test_malformed_json_propagates():
    response = Response(error = json.JSONDecodeError("invalid", "{", 1))
    with pytest.raises(ValueError):
        PubChemClient(FakeHTTP(response)).properties(101)


@pytest.mark.parametrize("failure", [requests.Timeout("timeout"), requests.ConnectionError("offline")])
def test_transport_failure_propagates_without_retry(failure):
    http = FakeHTTP(failure)
    with pytest.raises(type(failure)):
        PubChemClient(http, retries = 0).properties(101)
    assert len(http.calls) == 1


@pytest.mark.parametrize("method", ["properties", "toxicity"])
@pytest.mark.parametrize("cid", [None, 0, -1, True, "101"])
def test_invalid_cids_fail_before_http(method, cid):
    http = FakeHTTP()
    with pytest.raises(ValueError):
        getattr(PubChemClient(http), method)(cid)
    assert http.calls == []


@pytest.mark.parametrize("status", [400, 403, 429, 500, 503])
def test_other_http_errors_are_not_missing(status):
    http = FakeHTTP(Response(status = status))
    with pytest.raises(requests.HTTPError):
        PubChemClient(http, retries = 0).toxicity(101)
    assert len(http.calls) == 1


@pytest.mark.parametrize("status", [202, 301, 302])
def test_nonterminal_http_responses_are_not_treated_as_results(status):
    http = FakeHTTP(Response(status = status))
    with pytest.raises(requests.HTTPError):
        PubChemClient(http).toxicity(101)
    assert http.calls[0][1]["allow_redirects"] is False


def test_null_sections_are_valid_source_content():
    payload = {"Record": {"RecordNumber": 101, "RecordType": "CID", "Section": None}}
    assert PubChemClient(FakeHTTP(Response(payload))).toxicity(101) == payload


def test_default_transport_construction_and_numeric_lookup_are_offline():
    client = PubChemClient()
    assert client.resolve("00101") == 101


@pytest.fixture(autouse = True)
def forbid_real_sleep(monkeypatch):
    def fail(seconds):
        raise AssertionError("PubChem tests must use injected sleep")

    monkeypatch.setattr("time.sleep", fail)


class FakeTime:
    def __init__(self):
        self.now = 0.0
        self.epoch = datetime(2026, 1, 1, tzinfo = UTC).timestamp()
        self.waits = []

    def clock(self):
        return self.now

    def wall_clock(self):
        return self.epoch + self.now

    def sleep(self, seconds):
        self.waits.append(seconds)
        self.now += seconds


def timed_client(*responses, **options):
    timer = FakeTime()

    class TimedHTTP(FakeHTTP):
        def __init__(self):
            super().__init__(*responses)
            self.starts = []

        def get(self, url, **kwargs):
            self.starts.append(timer.clock())
            return super().get(url, **kwargs)

    http = TimedHTTP()
    client = PubChemClient(
        http, clock = timer.clock, wall_clock = timer.wall_clock, sleep = timer.sleep,
        **options,
    )
    return client, http, timer


def found():
    return Response({"Record": {"RecordNumber": 101, "RecordType": "CID", "Section": []}})


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_transient_status_retries_then_succeeds(status):
    client, http, timer = timed_client(Response(status = status), found())
    assert client.toxicity(101)["Record"]["RecordNumber"] == 101
    assert http.starts == [0.0, 1.0]
    assert timer.waits == [1.0]
    assert all(options["timeout"] == (10, 40) for _, options in http.calls)


@pytest.mark.parametrize("error", [
    requests.ConnectTimeout("connect"), requests.ReadTimeout("read"),
    requests.ConnectionError("temporary connection failure"),
])
def test_transient_transport_failure_retries(error):
    client, http, timer = timed_client(error, found())
    assert client.toxicity(101) is not None
    assert http.starts == [0.0, 1.0]
    assert timer.waits == [1.0]


@pytest.mark.parametrize("failure, expected", [
    (Response(status = 503), requests.HTTPError),
    (requests.Timeout("timeout"), requests.Timeout),
])
def test_default_retry_budget_is_five_total_attempts(failure, expected):
    client, http, timer = timed_client(*[failure for _ in range(5)])
    with pytest.raises(expected):
        client.toxicity(101)
    assert len(http.calls) == 5
    assert timer.waits == [1.0, 2.0, 4.0, 8.0]


def test_pacing_covers_operations_and_retries():
    client, http, timer = timed_client(found(), Response(status = 503), found())
    client.toxicity(101)
    client.toxicity(101)
    assert http.starts == [0.0, 0.25, 1.25]
    assert timer.waits == [0.25, 1.0]


def test_retry_and_pacing_delays_overlap():
    client, http, timer = timed_client(Response(status = 503), found(), interval = 3.0)
    client.toxicity(101)
    assert http.starts == [0.0, 3.0]
    assert timer.waits == [3.0]


def test_elapsed_request_time_counts_toward_pacing():
    client, http, timer = timed_client(found(), found())
    client.toxicity(101)
    timer.now += 0.1
    client.toxicity(101)
    assert http.starts == pytest.approx([0.0, 0.25])
    assert timer.waits == pytest.approx([0.15])


@pytest.mark.parametrize("header, expected", [
    ("3", 3.0), (" 2 ", 2.0), ("0", 1.0), ("-1", 1.0), ("1.5", 1.0),
    ("invalid", 1.0), ("NaN", 1.0), ("Infinity", 1.0),
    ("Wed, 31 Dec 2025 23:59:59 GMT", 1.0),
    ("Thu, 01 Jan 2026 00:00:04 GMT", 4.0),
    ("Thu, 01 Jan 2026 00:00:04", 1.0),
])
def test_retry_after_seconds_and_dates(header, expected):
    client, http, timer = timed_client(
        Response(status = 429, headers = {"retry-after": header}), found(),
    )
    client.toxicity(101)
    assert timer.waits == [expected]
    assert len(http.calls) == 2


def test_retry_after_date_uses_current_injected_wall_clock():
    deadline = format_datetime(datetime(2026, 1, 1, 0, 0, 10, tzinfo = UTC), usegmt = True)
    client, http, timer = timed_client(
        found(), Response(status = 503, headers = {"Retry-After": deadline}), found(),
    )
    client.toxicity(101)
    timer.now = 6.0
    client.toxicity(101)
    assert http.starts == [0.0, 6.0, 10.0]
    assert timer.waits == [4.0]


@pytest.mark.parametrize("response, expected", [
    (Response(status = 400), requests.HTTPError),
    (Response(status = 404), type(None)),
    (Response(error = ValueError("bad JSON")), ValueError),
    (Response({"Record": {}}), ValueError),
    (requests.exceptions.SSLError("certificate failure"), requests.exceptions.SSLError),
])
def test_permanent_failures_and_missing_sections_do_not_retry(response, expected):
    client, http, timer = timed_client(response)
    if expected is type(None):
        assert client.toxicity(101) is None
    else:
        with pytest.raises(expected):
            client.toxicity(101)
    assert len(http.calls) == 1
    assert timer.waits == []


@pytest.mark.parametrize("options", [
    {"interval": -1}, {"interval": float("nan")}, {"interval": float("inf")},
    {"interval": True}, {"retries": -1}, {"retries": 1.5}, {"retries": True},
])
def test_invalid_retry_policy_is_rejected(options):
    with pytest.raises(ValueError):
        PubChemClient(FakeHTTP(), **options)


def test_requests_session_adapter_retries_are_disabled():
    session = requests.Session()
    session.mount("https://", requests.adapters.HTTPAdapter(max_retries = 3))
    PubChemClient(session)
    assert all(adapter.max_retries.total == 0 for adapter in session.adapters.values())


def test_short_retry_after_never_shortens_exponential_backoff():
    client, http, timer = timed_client(
        Response(status = 503, headers = {"Retry-After": "0"}),
        Response(status = 503, headers = {"Retry-After": "1"}), found(),
    )
    client.toxicity(101)
    assert timer.waits == [1.0, 2.0]
    assert http.starts == [0.0, 1.0, 3.0]


def test_wall_clock_changes_do_not_affect_pacing():
    client, http, timer = timed_client(found(), found())
    client.toxicity(101)
    timer.epoch += 100000.0
    assert client.resolve("00101") == 101
    client.toxicity(101)
    assert http.starts == [0.0, 0.25]
    assert timer.waits == [0.25]


def test_successful_retry_to_missing_toxicity_stays_missing():
    client, http, timer = timed_client(Response(status = 503), Response(status = 404))
    assert client.toxicity(101) is None
    assert len(http.calls) == 2
    assert timer.waits == [1.0]


def test_zero_interval_and_zero_retries_are_supported():
    client, http, timer = timed_client(found(), found(), interval = 0, retries = 0)
    client.toxicity(101)
    client.toxicity(101)
    assert http.starts == [0.0, 0.0]
    assert timer.waits == []
