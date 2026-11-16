"""Audited PubChem to EPA DTXSID identity crosswalk."""

import json

import pytest

from agrotox.epa_identity import (
    APPROVED,
    CONNECTIVITY_ONLY,
    EXACT_STRUCTURE,
    NAME_ONLY,
    NEEDS_REVIEW,
    UNRESOLVED,
    identity_candidates,
    identity_crosswalk,
    identity_review_queue,
    match_strength,
    resolve_identities,
)
from agrotox.sources.comptox import ComptoxClient
from agrotox.storage import epa_detail_path, epa_search_path
from agrotox.tables import compound_table

KEY = "VLGXYZABCD1234567890UVWXYZ012"  # 27 characters
OTHER = "ZZZZZZABCD1234567890UVWXYZ999"


def compound(compound_id, inchikey = KEY, **overrides):
    row = {
        "compound_id": compound_id,
        "pubchem_cid": 1,
        "input_queries": [compound_id],
        "preferred_name": "Alpha",
        "chemical_group": "herbicide",
        "subgroup": None,
        "hrac_group": None,
        "source_notes": [],
        "inchi": None,
        "inchikey": inchikey,
        "smiles": None,
        "connectivity_smiles": None,
        "molecular_formula": None,
        "molecular_weight": None,
        "iupac_name": None,
        "resolution_status": "resolved",
        "toxicity_status": "found",
    }
    row.update(overrides)
    return row


def candidate(dtxsid = "DTXSID7020182", **overrides):
    row = {
        "dtxsid": dtxsid,
        "preferredName": "Alpha",
        "casrn": "50-00-0",
        "smiles": "CCO",
        "rank": 1,
    }
    row.update(overrides)
    return row


def detail(inchikey = KEY, **overrides):
    row = {
        "dtxsid": "DTXSID7020182",
        "inchikey": inchikey,
        "smiles": "CCO",
        "inchiString": "InChI=1S/CCO/c1/2H",
        "molFormula": "C2H6O",
        "averageMass": 46.07,
        "totalAssays": 12,
        "activeAssays": 3,
    }
    row.update(overrides)
    return row


def evidence(compound_id, searches, inchikey = KEY):
    return {
        "compound_id": compound_id,
        "pubchem_cid": 1,
        "inchikey": inchikey,
        "searches": searches,
    }


def test_an_exact_inchikey_is_approved():
    compounds = compound_table([compound("PUBCHEM:1")])
    candidates = identity_candidates(compounds, [evidence("PUBCHEM:1", [
        {"search_basis": "inchikey", "search_term": KEY, "suggestions": [],
         "candidates": [{**candidate(), "detail": detail()}]},
    ])])
    crosswalk = identity_crosswalk(compounds, candidates)
    assert crosswalk["status"].to_list() == [APPROVED]
    assert crosswalk["dtxsid"].to_list() == ["DTXSID7020182"]
    assert crosswalk["match_strength"].to_list() == [EXACT_STRUCTURE]
    assert crosswalk["candidate_count"].to_list() == [1]


def test_the_candidate_record_supplies_the_structure_evidence():
    compounds = compound_table([compound("PUBCHEM:1")])
    candidates = identity_candidates(compounds, [evidence("PUBCHEM:1", [
        {"search_basis": "inchikey", "search_term": KEY, "suggestions": [],
         "candidates": [{**candidate(), "detail": detail()}]},
    ])])
    row = candidates.row(0, named = True)
    assert row["inchikey"] == KEY
    assert row["molecular_formula"] == "C2H6O"
    assert row["total_assays"] == 12
    assert row["detail_status"] == "resolved"


def test_a_candidate_without_a_record_is_never_approved():
    compounds = compound_table([compound("PUBCHEM:1")])
    candidates = identity_candidates(compounds, [evidence("PUBCHEM:1", [
        {"search_basis": "inchikey", "search_term": KEY, "suggestions": [],
         "candidates": [{**candidate(), "detail": None}]},
    ])])
    crosswalk = identity_crosswalk(compounds, candidates)
    assert crosswalk["status"].to_list() == [UNRESOLVED]
    assert candidates["detail_status"].to_list() == ["unavailable"]


def test_several_exact_candidates_require_review():
    compounds = compound_table([compound("PUBCHEM:1")])
    candidates = identity_candidates(compounds, [evidence("PUBCHEM:1", [
        {"search_basis": "inchikey", "search_term": KEY, "suggestions": [],
         "candidates": [
             {**candidate("DTXSID1"), "detail": detail()},
             {**candidate("DTXSID2"), "detail": detail()},
         ]},
    ])])
    crosswalk = identity_crosswalk(compounds, candidates)
    assert crosswalk["status"].to_list() == [NEEDS_REVIEW]
    assert crosswalk["dtxsid"].to_list() == [None]
    assert crosswalk["reason"].to_list() == ["several candidates share the full InChIKey"]


def test_a_connectivity_only_candidate_requires_review():
    stereo = KEY[:14] + "BBBBBBBBBBBBB"
    compounds = compound_table([compound("PUBCHEM:1")])
    candidates = identity_candidates(compounds, [evidence("PUBCHEM:1", [
        {"search_basis": "name", "search_term": "Alpha", "suggestions": [],
         "candidates": [{**candidate("DTXSID9"), "detail": detail(stereo)}]},
    ])])
    crosswalk = identity_crosswalk(compounds, candidates)
    assert crosswalk["status"].to_list() == [NEEDS_REVIEW]
    assert crosswalk["match_strength"].to_list() == [CONNECTIVITY_ONLY]


def test_a_different_connection_layer_is_not_a_match():
    salt = "AAAAAAAAAAAA" + KEY[14:]
    compounds = compound_table([compound("PUBCHEM:1")])
    candidates = identity_candidates(compounds, [evidence("PUBCHEM:1", [
        {"search_basis": "name", "search_term": "Alpha", "suggestions": [],
         "candidates": [{**candidate("DTXSID8"), "detail": detail(salt)}]},
    ])])
    crosswalk = identity_crosswalk(compounds, candidates)
    assert crosswalk["status"].to_list() == [UNRESOLVED]
    assert crosswalk["match_strength"].to_list() == ["none"]


def test_a_name_only_candidate_requires_review():
    compounds = compound_table([compound("PUBCHEM:1")])
    candidates = identity_candidates(compounds, [evidence("PUBCHEM:1", [
        {"search_basis": "name", "search_term": "Alpha", "suggestions": [],
         "candidates": [{**candidate("DTXSID7"), "detail": {}}]},
    ])])
    crosswalk = identity_crosswalk(compounds, candidates)
    assert crosswalk["status"].to_list() == [NEEDS_REVIEW]
    assert crosswalk["match_strength"].to_list() == [NAME_ONLY]


def test_the_provider_suggestions_are_kept():
    compounds = compound_table([compound("PUBCHEM:1")])
    candidates = identity_candidates(compounds, [evidence("PUBCHEM:1", [
        {"search_basis": "inchikey", "search_term": KEY,
         "suggestions": [KEY[:14] + "NAAAAAAAAAAA"], "candidates": []},
    ])])
    assert candidates["provider_suggestions"].to_list() == [[KEY[:14] + "NAAAAAAAAAAA"]]


def test_an_unmatched_compound_is_unresolved():
    compounds = compound_table([compound("PUBCHEM:1")])
    candidates = identity_candidates(compounds, [evidence("PUBCHEM:1", [
        {"search_basis": "inchikey", "search_term": KEY, "suggestions": [], "candidates": []},
    ])])
    crosswalk = identity_crosswalk(compounds, candidates)
    assert crosswalk["status"].to_list() == [UNRESOLVED]
    assert crosswalk["candidate_count"].to_list() == [0]


def test_an_unresolved_pubchem_identity_is_unresolved():
    compounds = compound_table([compound("PUBCHEM:1", resolution_status = "unresolved")])
    crosswalk = identity_crosswalk(compounds, identity_candidates(compounds, []))
    assert crosswalk["status"].to_list() == [UNRESOLVED]
    assert crosswalk["reason"].to_list() == ["unresolved PubChem identity"]


def test_the_review_queue_holds_only_ambiguous_mappings():
    compounds = compound_table([compound("PUBCHEM:1"), compound("PUBCHEM:2")])
    candidates = identity_candidates(compounds, [
        evidence("PUBCHEM:1", [
            {"search_basis": "name", "search_term": "Alpha", "suggestions": [],
             "candidates": [{**candidate("DTXSID7"), "detail": {}}]},
        ]),
        evidence("PUBCHEM:2", [
            {"search_basis": "inchikey", "search_term": KEY, "suggestions": [],
             "candidates": [{**candidate("DTXSID3"), "detail": detail()}]},
        ]),
    ])
    crosswalk = identity_crosswalk(compounds, candidates)
    queue = identity_review_queue(crosswalk)
    assert queue.height == 1
    assert queue["compound_id"].to_list() == ["PUBCHEM:1"]


def test_duplicate_aliases_produce_one_crosswalk_row():
    compounds = compound_table([compound("PUBCHEM:1", input_queries = ["alpha", "101"])])
    candidates = identity_candidates(compounds, [evidence("PUBCHEM:1", [
        {"search_basis": "inchikey", "search_term": KEY, "suggestions": [],
         "candidates": [{**candidate(), "detail": detail()}]},
    ])])
    crosswalk = identity_crosswalk(compounds, candidates)
    assert crosswalk.height == 1
    assert crosswalk["input_queries"].to_list() == [["alpha", "101"]]


def test_match_strength_rules():
    assert match_strength(KEY, KEY) == EXACT_STRUCTURE
    assert match_strength(KEY, KEY[:14] + "ZZZZZZZZZZZZZ") == CONNECTIVITY_ONLY
    assert match_strength(KEY, "QQQQQQQQQQQQQQ" + KEY[14:]) == "none"
    assert match_strength(None, KEY) == "none"
    assert match_strength(KEY, None) == "none"


class FakeResponse:
    def __init__(self, payload, status_code = 200):
        self.payload = payload
        self.status_code = status_code
        self.headers = {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError("unexpected error response")

    def json(self):
        return self.payload


class FakeHTTP:
    def __init__(self, candidates = None, details = None, not_found = None):
        self.candidates = candidates if candidates is not None else [candidate()]
        self.details = details if details is not None else detail()
        self.not_found = not_found
        self.calls = []

    def get(self, url, *, params, headers, timeout, allow_redirects):
        self.calls.append((url, headers))
        if "/chemical/detail/" in url:
            return FakeResponse(self.details)
        if self.not_found is not None and self.not_found in url:
            return FakeResponse(
                {"detail": f"Found 0 results for {self.not_found}.",
                 "suggestions": ["BACHBFVBHLGWSL-UHFFFAOYNA-N"]},
                status_code = 400,
            )
        return FakeResponse(self.candidates)


def test_the_client_sends_the_key_in_a_header_only():
    http = FakeHTTP()
    client = ComptoxClient(http, api_key = "secret-key")
    result = client.search_equal(KEY)
    assert len(result.candidates) == 1
    url, headers = http.calls[0]
    assert "secret-key" not in url
    assert headers["x-api-key"] == "secret-key"


def test_the_client_requires_a_key():
    client = ComptoxClient(FakeHTTP(), api_key = "")
    with pytest.raises(ValueError, match = "API key"):
        client.search_equal(KEY)


def test_a_search_with_no_match_is_an_empty_result_with_suggestions():
    http = FakeHTTP(not_found = "NOSUCHKEY")
    client = ComptoxClient(http, api_key = "secret-key")
    result = client.search_equal("NOSUCHKEY")
    assert result.candidates == []
    assert result.suggestions == ["BACHBFVBHLGWSL-UHFFFAOYNA-N"]


def test_resolve_identities_caches_the_search_and_the_record(tmp_path):
    http = FakeHTTP()
    client = ComptoxClient(http, api_key = "secret-key")
    compounds = compound_table([compound("PUBCHEM:1")])
    _candidates, crosswalk = resolve_identities(tmp_path, compounds, client)
    assert crosswalk["status"].to_list() == [APPROVED]
    stored = json.loads(epa_search_path(tmp_path, KEY).read_text(encoding = "utf-8"))
    assert stored["search_term"] == KEY
    assert "secret-key" not in json.dumps(stored)
    record = json.loads(
        epa_detail_path(tmp_path, "DTXSID7020182").read_text(encoding = "utf-8")
    )
    assert "secret-key" not in json.dumps(record)
    calls = len(http.calls)
    resolve_identities(tmp_path, compounds, client)
    assert len(http.calls) == calls


def test_the_crosswalk_round_trips_through_the_cache(tmp_path):
    http = FakeHTTP()
    client = ComptoxClient(http, api_key = "secret-key")
    compounds = compound_table([compound("PUBCHEM:1")])
    resolve_identities(tmp_path, compounds, client)
    cached = json.loads(epa_search_path(tmp_path, KEY).read_text(encoding = "utf-8"))
    searches = [{
        "search_basis": "inchikey",
        "search_term": KEY,
        "suggestions": cached["response"].get("suggestions", []),
        "candidates": [
            {**candidate, "detail": detail()} for candidate in cached["response"]["candidates"]
        ],
    }]
    candidates = identity_candidates(compounds, [evidence("PUBCHEM:1", searches)])
    crosswalk = identity_crosswalk(compounds, candidates)
    assert crosswalk["status"].to_list() == [APPROVED]
    assert crosswalk["dtxsid"].to_list() == ["DTXSID7020182"]
