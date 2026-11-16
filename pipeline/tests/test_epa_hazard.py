"""EPA experimental hazard evidence and its mapping onto the comparison rules."""

import json

import polars as pl
import pytest

from agrotox.coverage import coverage_tables
from agrotox.epa_hazard import (
    as_comparison_input,
    fetch_hazard,
    hazard_coverage,
    hazard_table,
    normalize_hazards,
    parse_toxval,
)
from agrotox.storage import epa_hazard_path

RULES = {
    "rat_oral": {"endpoint": "LD50", "species": "rat", "preferred_route": "oral"},
    "fish_96h": {
        "endpoint": "LC50", "organism_group": "fish", "preferred_duration_hours": 96,
    },
}


def record(**overrides):
    row = {
        "dtxsid": "DTXSID7020182",
        "casrn": "50-00-0",
        "name": "Ethanol",
        "source": "ECOTOX",
        "subsource": "DMS",
        "toxvalType": "LD50",
        "toxvalTypeDefinition": "Dose that causes 50% mortality",
        "toxvalSubtype": "Acute",
        "qualifier": "=",
        "toxvalNumeric": 5000.0,
        "toxvalUnits": "mg/kg",
        "humanEco": "Eco",
        "studyType": "Laboratory",
        "studyDurationValue": 14.0,
        "studyDurationUnits": "day",
        "speciesCommon": "Rat",
        "latinName": "Rattus norvegicus",
        "speciesSupercategory": "Mammal",
        "exposureRoute": "Oral",
        "exposureMethod": "gavage",
        "exposureForm": "Whole",
        "media": "",
        "toxicologicalEffect": "Mortality",
        "experimentalRecord": "experimental",
        "quality": "Acceptable",
        "qcCategory": "Complete",
        "guideline": "OECD 401",
        "longRef": "Ref-1",
        "doi": "10.1000/example",
        "title": "A rat study",
        "author": "Someone",
        "year": "2019",
        "sourceUrl": "https://example.org/study",
        "externalSourceId": "TOXVAL-1",
        "sourceHash": "abc123",
    }
    row.update(overrides)
    return row


def crosswalk(*rows):
    return pl.DataFrame(list(rows), schema = {
        "compound_id": pl.String, "dtxsid": pl.String, "status": pl.String,
    })


class FakeClient:
    def __init__(self, records = None):
        self.records = records if records is not None else [record()]
        self.calls = []

    def hazard(self, dtxsid):
        self.calls.append(dtxsid)
        return self.records


def test_a_hazard_record_keeps_its_context_and_provenance():
    rows = parse_toxval([record()], "PUBCHEM:1", "2026-01-01T00:00:00Z")
    row = rows[0]
    assert row["toxval_type"] == "LD50"
    assert row["value_numeric"] == 5000.0
    assert row["value_units"] == "mg/kg"
    assert row["latin_name"] == "Rattus norvegicus"
    assert row["exposure_route"] == "Oral"
    assert row["study_duration_value"] == 14.0
    assert row["experimental_record"] == "experimental"
    assert row["reference"] == "Ref-1"
    assert row["doi"] == "10.1000/example"


def test_a_predicted_record_is_kept_and_marked():
    rows = parse_toxval([record(experimentalRecord = "not experimental")], "PUBCHEM:1", "now")
    assert rows[0]["experimental_record"] == "not experimental"


def test_the_experimental_marking_follows_the_source_wording():
    rows = parse_toxval([record(experimentalRecord = "experimental")], "PUBCHEM:1", "now")
    assert rows[0]["experimental_record"] == "experimental"


@pytest.mark.parametrize("mark", ["not experimental", "undetermined", None])
def test_only_experimental_hazards_enter_comparisons(mark):
    hazards = hazard_table(parse_toxval([
        record(), record(experimentalRecord = mark, toxvalNumeric = 9000.0),
    ], "PUBCHEM:1", "now"))
    assert hazards.height == 2
    comparison = as_comparison_input(hazards)
    assert comparison["value_standardized"].to_list() == [5000.0]
    assert as_comparison_input(hazards.tail(1)).is_empty()


def test_a_missing_value_stays_null():
    rows = parse_toxval([record(toxvalNumeric = None)], "PUBCHEM:1", "now")
    assert rows[0]["value_numeric"] is None


def test_a_malformed_record_is_rejected():
    with pytest.raises(TypeError):
        parse_toxval(["not a record"], "PUBCHEM:1", "now")


def test_coverage_counts_records_endpoints_species_and_references():
    hazards = hazard_table(parse_toxval([
        record(), record(toxvalType = "LC50", toxvalNumeric = 10.0, toxvalUnits = "mg/L",
                         latinName = "Oncorhynchus mykiss"),
        record(longRef = "Ref-2", experimentalRecord = "not experimental"),
    ], "PUBCHEM:1", "now"))
    coverage = hazard_coverage(hazards)
    assert coverage["records"].to_list() == [3]
    assert coverage["experimental_records"].to_list() == [2]
    assert coverage["distinct_endpoints"].to_list() == [2]
    assert coverage["distinct_species"].to_list() == [2]
    assert coverage["distinct_references"].to_list() == [2]


def test_a_matching_record_becomes_comparison_input():
    hazards = hazard_table(parse_toxval([record()], "PUBCHEM:1", "now"))
    comparison = as_comparison_input(hazards)
    row = comparison.row(0, named = True)
    assert row["endpoint"] == "LD50"
    assert row["species"] == "rattus norvegicus"
    assert row["organism_group"] == "mammal"
    assert row["exposure_route"] == "oral"
    assert row["duration_hours"] == 336.0
    assert row["unit_standardized"] == "mg/kg"
    assert row["value_standardized"] == 5000.0
    assert row["parse_status"] == "complete"


def test_a_missing_duration_sentinel_leaves_the_duration_unknown():
    hazards = hazard_table(parse_toxval([
        record(studyDurationValue = -999.0, studyDurationUnits = "-"),
    ], "PUBCHEM:1", "now"))
    comparison = as_comparison_input(hazards)
    assert comparison.height == 1
    assert comparison["duration_hours"].to_list() == [None]


def test_an_unconvertible_duration_leaves_the_duration_unknown():
    hazards = hazard_table(parse_toxval([
        record(studyDurationValue = 2.0, studyDurationUnits = "years"),
    ], "PUBCHEM:1", "now"))
    comparison = as_comparison_input(hazards)
    assert comparison["duration_hours"].to_list() == [None]


def test_the_plural_organism_category_is_mapped():
    hazards = hazard_table(parse_toxval([
        record(speciesSupercategory = "Mammals"),
    ], "PUBCHEM:1", "now"))
    comparison = as_comparison_input(hazards)
    assert comparison["organism_group"].to_list() == ["mammal"]


def test_an_incompatible_unit_stays_outside_the_comparison():
    hazards = hazard_table(parse_toxval([
        record(toxvalType = "LC50", toxvalUnits = "mg/kg", toxvalNumeric = 10.0),
    ], "PUBCHEM:1", "now"))
    assert as_comparison_input(hazards).is_empty()
    assert hazards.height == 1


def test_an_unsupported_endpoint_stays_outside_the_comparison():
    hazards = hazard_table(parse_toxval([
        record(toxvalType = "NOEC", toxvalNumeric = 100.0),
    ], "PUBCHEM:1", "now"))
    assert as_comparison_input(hazards).is_empty()


def test_the_mapped_records_work_with_the_existing_matching_rules():
    hazards = hazard_table(parse_toxval([record()], "PUBCHEM:1", "now"))
    comparison = as_comparison_input(hazards)
    compounds = pl.DataFrame({
        "compound_id": ["PUBCHEM:1"],
        "input_queries": [["ethanol"]],
        "chemical_group": ["herbicide"],
    })
    matrix, _ = coverage_tables(compounds, comparison, RULES)
    assert matrix["rat_oral"].to_list() == [0]
    fish, _ = coverage_tables(compounds, comparison, {
        "mammal": {"endpoint": "LD50", "organism_group": "mammal"},
    })
    assert fish["mammal"].to_list() == [1]


def test_only_approved_compounds_are_requested(tmp_path):
    client = FakeClient()
    approved = crosswalk(
        {"compound_id": "PUBCHEM:1", "dtxsid": "DTXSID1", "status": "approved"},
        {"compound_id": "PUBCHEM:2", "dtxsid": "DTXSID2", "status": "needs_review"},
    )
    hazards, coverage, comparison = fetch_hazard(tmp_path, approved, client)
    assert client.calls == ["DTXSID1"]
    assert hazards.height == 1
    assert coverage["compound_id"].to_list() == ["PUBCHEM:1"]
    assert comparison.height == 1


def test_cached_responses_are_reused(tmp_path):
    client = FakeClient()
    approved = crosswalk({"compound_id": "PUBCHEM:1", "dtxsid": "DTXSID1",
                          "status": "approved"})
    first, _, _ = fetch_hazard(tmp_path, approved, client)
    stored = json.loads(epa_hazard_path(tmp_path, "DTXSID1").read_text(encoding = "utf-8"))
    assert stored["dtxsid"] == "DTXSID1"
    assert "api_key" not in json.dumps(stored)
    calls = len(client.calls)
    second, _, _ = fetch_hazard(tmp_path, approved, client)
    assert len(client.calls) == calls
    assert first.to_dicts() == second.to_dicts()


def test_an_empty_selection_gives_typed_empty_tables(tmp_path):
    hazards, coverage, comparison = fetch_hazard(tmp_path, crosswalk(), FakeClient())
    assert hazards.is_empty()
    assert coverage.is_empty()
    assert comparison.is_empty()
    assert hazards.schema["value_numeric"] == pl.Float64
    assert comparison.schema["value_standardized"] == pl.Float64


@pytest.mark.parametrize("label, endpoint, basis, response", [
    ("NOAEL", "NOAEL", "observed", None),
    ("LOAEL", "LOAEL", "observed", None),
    ("BMD", "BMD", "model_derived", None),
    ("BMDL (10)", "BMDL", "model_derived", "10"),
])
def test_point_of_departure_rows_keep_source_context(label, endpoint, basis, response):
    original = record(toxvalType = label, toxvalUnits = "ug/kg/day", toxvalNumeric = 500.0,
                      studyType = "chronic", studyDurationClass = "chronic",
                      toxicologicalEffect = "body weight", unfamiliarField = {"keep": True})
    hazards = hazard_table(parse_toxval([original], "PUBCHEM:1", "now"))
    normalized = normalize_hazards(hazards)
    row = normalized.row(0, named = True)
    assert row["endpoint"] == endpoint
    assert row["evidence_basis"] == basis
    assert row["information_name"] == label
    assert row["value_standardized"] == 0.5
    assert row["unit_standardized"] == "mg/kg-day"
    assert row["qualifier"] == "="
    assert row["study_type"] == "chronic"
    assert row["duration_class"] == "chronic"
    assert row["effect"] == "body weight"
    assert row["benchmark_response"] == response
    assert row["benchmark_response_type"] is None
    assert row["model_name"] is None
    assert row["confidence_level"] is None
    assert json.loads(row["information_json"]) == original
    assert json.loads(row["sources"][0]["reference_json"]) == original
    comparison = as_comparison_input(hazards)
    assert comparison["endpoint"].to_list() == [endpoint]
    assert comparison["evidence_basis"].to_list() == [basis]
    assert normalized.height == 1  # A standalone BMDL never fabricates a BMD.


@pytest.mark.parametrize("changes, reason", [
    ({"experimentalRecord": "undetermined"}, "not explicitly experimental"),
    ({"toxvalNumeric": None}, "positive finite"),
    ({"toxvalNumeric": float("nan")}, "positive finite"),
    ({"toxvalNumeric": float("inf")}, "positive finite"),
    ({"toxvalNumeric": 1e308, "toxvalUnits": "g/kg-day"}, "converted value"),
    ({"toxvalUnits": "ppm"}, "unsupported or incompatible unit"),
    ({"qualifier": "approximately"}, "unsupported qualifier"),
    ({"exposureForm": "formulation"}, "formulation or mixture"),
    ({"toxvalType": "LOAEL (HEC)"}, "unsupported endpoint"),
])
def test_ineligible_hazards_remain_reviewable(changes, reason):
    original = record(**{"toxvalType": "NOAEL", "toxvalUnits": "mg/kg-day", **changes})
    hazards = hazard_table(parse_toxval([original], "PUBCHEM:1", "now"))
    normalized = normalize_hazards(hazards)
    assert normalized.height == 1
    assert normalized["parse_status"][0] in {"partial", "failed"}
    assert reason in normalized["parse_note"][0]
    assert as_comparison_input(hazards).is_empty()


def test_hazard_annotation_ids_are_stable_but_compound_specific():
    def normalize(compound, time):
        return normalize_hazards(hazard_table(parse_toxval([record()], compound, time)))

    first = normalize("PUBCHEM:1", "before")
    assert first["annotation_id"].to_list() == normalize("PUBCHEM:1", "after")["annotation_id"].to_list()
    assert first["annotation_id"].to_list() != normalize("PUBCHEM:2", "before")["annotation_id"].to_list()
