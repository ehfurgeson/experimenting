"""Bounded plant-assay acquisition with synthetic responses and no live requests."""

import copy
import json

import pytest
import requests

from agrotox.chembl import fetch_assay

ASSAY = "CHEMBL100"
DOCUMENT = "CHEMBL200"


def activity(identity):
    return {"activity_id": identity, "assay_chembl_id": ASSAY,
            "document_chembl_id": DOCUMENT, "molecule_chembl_id": "CHEMBL300",
            "canonical_smiles": "CCO", "standard_type": "Inhibition",
            "standard_value": "0.0", "standard_relation": "=", "standard_units": "%",
            "activity_comment": None, "unrecognized_source_field": "preserve"}


def page(records, offset = 0, total = 3):
    return {"activities": records, "page_meta": {
        "offset": offset, "limit": 2, "total_count": total,
        "next": "https://untrusted.example/ignored", "previous": None,
    }}


def responses():
    return [{"chembl_db_version": "ChEMBL_test"},
            {"assay_chembl_id": ASSAY, "document_chembl_id": DOCUMENT,
             "description": "Growth inhibition in a defined plant assay"},
            {"document_chembl_id": DOCUMENT, "doi": "10.1000/synthetic"},
            page([activity(1), activity(2)]), page([activity(3)], offset = 2)]


class Response:
    def __init__(self, data):
        self.data = data
        self.status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return copy.deepcopy(self.data)


class HTTP:
    def __init__(self, data):
        self.data = iter(data)
        self.calls = []

    def get(self, url, **options):
        self.calls.append((url, options))
        item = next(self.data)
        if isinstance(item, Exception):
            raise item
        return Response(item)


def fetch(root, http, **options):
    return fetch_assay(root, ASSAY, http = http, page_size = 2,
                       sleep = lambda delay: None, **options)


def test_complete_snapshot_preserves_raw_values_context_structures_and_version(tmp_path):
    raw = responses()
    http = HTTP(raw)
    path = fetch(tmp_path, http)
    assert path == tmp_path / "raw/chembl/CHEMBL100.json"
    bundle = json.loads(path.read_text())
    assert bundle["status"] == raw[0]
    assert bundle["assay"] == raw[1]
    assert bundle["document"] == raw[2]
    assert bundle["activity_pages"] == raw[3:]
    assert bundle["activity_count"] == 3
    assert bundle["retrieved_at"].endswith("+00:00")
    assert bundle["source"] == "ChEMBL"
    assert "activity_target" not in path.read_text()
    assert len(http.calls) == 5
    for url, options in http.calls:
        assert url.startswith("https://www.ebi.ac.uk/chembl/api/data/")
        assert options["timeout"] == (10, 40)
        assert options["allow_redirects"] is False
    assert [options["params"]["offset"] for _, options in http.calls[-2:]] == ["0", "2"]
    # Preserve a frozen snapshot; a rerun must choose a new data root.
    before = path.read_bytes()
    with pytest.raises(FileExistsError, match = "snapshot"):
        fetch(tmp_path, HTTP([]))
    assert path.read_bytes() == before


@pytest.mark.parametrize("identity", ["", "CHEMBL0", "CHEMBL1/../../x", "chembl1", None, 123])
def test_invalid_assay_id_is_rejected_before_http(tmp_path, identity):
    http = HTTP([])
    with pytest.raises(ValueError, match = "ChEMBL ID"):
        fetch_assay(tmp_path, identity, http = http)
    assert not http.calls
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("options", [{"page_size": 0}, {"page_size": True},
                                    {"page_size": 1001}, {"max_activities": -1},
                                    {"max_activities": True}, {"max_activities": 1.5}])
def test_invalid_bounds_are_rejected_before_http(tmp_path, options):
    http = HTTP([])
    with pytest.raises(ValueError, match = "positive integer"):
        fetch_assay(tmp_path, ASSAY, http = http, **options)
    assert not http.calls


@pytest.mark.parametrize("change,message", [
    ("oversize", "bound"), ("changing_count", "count"), ("empty_page", "page"),
    ("duplicate", "activity_id"), ("wrong_assay", "assay"),
    ("wrong_document", "document"), ("wrong_offset", "offset"),
    ("invalid_activity_id", "activity_id"), ("invalid_molecule", "ChEMBL ID"),
    ("missing_version", "version"), ("wrong_document_response", "document"),
])
def test_incomplete_or_mismatched_responses_never_publish_snapshot(tmp_path, change, message):
    raw = responses()
    if change == "oversize":
        raw[3]["page_meta"]["total_count"] = 10001
    elif change == "changing_count":
        raw[4]["page_meta"]["total_count"] = 4
    elif change == "empty_page":
        raw[4]["activities"] = []
    elif change == "duplicate":
        raw[4]["activities"][0]["activity_id"] = 1
    elif change == "wrong_assay":
        raw[3]["activities"][0]["assay_chembl_id"] = "CHEMBL999"
    elif change == "wrong_document":
        raw[3]["activities"][0]["document_chembl_id"] = "CHEMBL999"
    elif change == "wrong_offset":
        raw[4]["page_meta"]["offset"] = 0
    elif change == "invalid_activity_id":
        raw[3]["activities"][0]["activity_id"] = True
    elif change == "invalid_molecule":
        raw[3]["activities"][0]["molecule_chembl_id"] = None
    elif change == "missing_version":
        raw[0] = {}
    elif change == "wrong_document_response":
        raw[2]["document_chembl_id"] = "CHEMBL999"
    with pytest.raises(ValueError, match = message):
        fetch(tmp_path, HTTP(raw))
    assert not list(tmp_path.iterdir())


def test_empty_assay_is_complete_with_zero_records(tmp_path):
    raw = responses()[:3] + [page([], total = 0)]
    path = fetch(tmp_path, HTTP(raw))
    bundle = json.loads(path.read_text())
    assert bundle["activity_count"] == 0
    assert len(bundle["activity_pages"]) == 1


@pytest.mark.parametrize("error", [requests.Timeout("timeout"), requests.HTTPError("503")])
def test_transport_failures_leave_no_snapshot(tmp_path, error):
    with pytest.raises(type(error)):
        fetch(tmp_path, HTTP(responses()[:3] + [error]))
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("bad_page,message", [
    ({}, "metadata"),
    ({"page_meta": {"total_count": True}}, "count"),
    (page([activity(1)], offset = True), "offset"),
    (page("not a list"), "page"),
    (page([None, activity(2)]), "activity object"),
    (page([activity(1), activity(2), activity(3)]), "page"),
    (page([activity(1)], total = 0), "page"),
])
def test_malformed_activity_pages_are_rejected(tmp_path, bad_page, message):
    with pytest.raises(ValueError, match = message):
        fetch(tmp_path, HTTP(responses()[:3] + [bad_page]))
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("payload", [[], None, "not json object"])
def test_invalid_response_shape_is_rejected(tmp_path, payload):
    with pytest.raises(ValueError, match = "JSON object"):
        fetch(tmp_path, HTTP([payload]))
    assert not list(tmp_path.iterdir())
