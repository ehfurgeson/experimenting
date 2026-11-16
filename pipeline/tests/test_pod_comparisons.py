"""Unit-specific point of departure coverage with explicit summary eligibility."""

import pytest

from agrotox.analysis import comparison_tables
from agrotox.coverage import coverage_tables, matches, matching_expr, validate_definitions
from agrotox.tables import MEASUREMENT_SCHEMA, compound_table, frame_from_rows


def observation(endpoint = "NOAEL", **changes):
    row = {
        "compound_id": "PUBCHEM:1", "annotation_id": "one", "sources": [],
        "value_raw": "reported dose", "endpoint": endpoint,
        "species": "rat", "organism_group": "mammal", "exposure_route": "oral",
        "duration_hours": 2160.0, "study_type": "repeat dose",
        "duration_class": "subchronic", "effect": "body weight",
        "evidence_basis": "model_derived" if endpoint in {"BMD", "BMDL"} else "observed",
        "unit_standardized": "mg/kg-day", "value_standardized": 10.0,
        "qualifier": "=", "parse_status": "complete", "formulation_flag": False,
        "benchmark_response": "10", "benchmark_response_type": "extra risk percent",
        "model_name": "synthetic model", "confidence_level": "95%",
    }
    return {**row, **changes}


def definition(endpoint = "NOAEL", **changes):
    return {"endpoint": endpoint, "standard_unit": "mg/kg-day", **changes}


def potency(endpoint = "NOAEL", **changes):
    rule = definition(endpoint, summary_mode = "potency", species = "rat",
                      preferred_route = "oral", preferred_duration_hours = 2160,
                      study_type = "repeat dose", effect = "body weight")
    if endpoint in {"BMD", "BMDL"}:
        rule.update(benchmark_response = "10", benchmark_response_type = "extra risk percent",
                    model_name = "synthetic model")
    if endpoint == "BMDL":
        rule["confidence_level"] = "95%"
    return {**rule, **changes}


@pytest.mark.parametrize("endpoint", ["NOAEL", "LOAEL", "BMD", "BMDL"])
def test_each_point_of_departure_matches_only_its_unit_and_basis(endpoint):
    row = observation(endpoint)
    rule = definition(endpoint)
    assert matches(row, rule)
    frame = frame_from_rows([row], MEASUREMENT_SCHEMA)
    assert frame.select(matching_expr(rule)).item()
    assert not matches({**row, "unit_standardized": "mg/kg"}, rule)
    assert not matches({**row, "evidence_basis": "predicted"}, rule)
    assert not matches({**row, "evidence_basis": None}, rule)
    assert not matches({**row, "endpoint": "LD50"}, rule)
    assert matches({**row, "unit_standardized": "mg/kg"},
                   {**rule, "standard_unit": "mg/kg"})
    with pytest.raises(ValueError, match = "standard_unit"):
        validate_definitions({"bad": {"endpoint": endpoint}})
    with pytest.raises(ValueError, match = "standard_unit"):
        validate_definitions({"bad": {**rule, "standard_unit": "mg/L"}})


@pytest.mark.parametrize("endpoint", ["NOAEL", "LOAEL", "BMD", "BMDL"])
def test_availability_keeps_reported_values_without_a_potency_median(endpoint):
    compounds = compound_table([
        {"compound_id": "PUBCHEM:1", "input_queries": ["one"], "chemical_group": "herbicide"},
        {"compound_id": "PUBCHEM:2", "input_queries": ["two"], "chemical_group": "herbicide"},
    ])
    rows = frame_from_rows([
        observation(endpoint),
        observation(endpoint, annotation_id = "two", value_standardized = 30.0, effect = "liver"),
        observation(endpoint, annotation_id = "three", unit_standardized = "mg/kg"),
    ], MEASUREMENT_SCHEMA)
    rules = {"daily": definition(endpoint), "total": definition(endpoint, standard_unit = "mg/kg")}
    matrix, _ = coverage_tables(compounds, rows, rules)
    assert matrix["daily"].to_list() == [1, 0]
    assert matrix["total"].to_list() == [1, 0]
    records, summaries, groups = comparison_tables(compounds, rows, rules)
    assert records.height == 3
    assert not records["summary_eligible"].any()
    assert summaries["n_exact"].to_list() == [2, 1]
    assert summaries["exact_median"].null_count() == 2
    assert groups["median_of_compound_exact_medians"].null_count() == 2
    assert groups["total_compounds"].to_list() == [2, 2]


@pytest.mark.parametrize("endpoint", ["NOAEL", "LOAEL", "BMD", "BMDL"])
def test_explicit_potency_context_allows_only_matching_reported_values(endpoint):
    compounds = compound_table([{"compound_id": "PUBCHEM:1", "input_queries": ["one"]}])
    rows = frame_from_rows([
        observation(endpoint),
        observation(endpoint, annotation_id = "two", value_standardized = 30.0),
        observation(endpoint, annotation_id = "three", value_standardized = 900.0, effect = None),
        observation(endpoint, annotation_id = "four", qualifier = ">", value_standardized = 100.0),
    ], MEASUREMENT_SCHEMA)
    records, summaries, _ = comparison_tables(compounds, rows, {"narrow": potency(endpoint)})
    assert records.height == 3
    assert records["summary_eligible"].all()
    assert summaries["exact_median"].to_list() == [20.0]
    assert summaries["n_censored"].to_list() == [1]


@pytest.mark.parametrize("field", [
    "species", "preferred_route", "preferred_duration_hours", "study_type", "effect",
    "benchmark_response", "benchmark_response_type", "model_name", "confidence_level",
])
def test_benchmark_potency_definition_requires_explicit_context(field):
    rule = potency("BMDL")
    del rule[field]
    with pytest.raises(ValueError, match = field):
        validate_definitions({"unsafe": rule})


def test_invalid_summary_modes_and_conflicting_evidence_basis_are_rejected():
    with pytest.raises(ValueError, match = "summary_mode"):
        validate_definitions({"bad": definition(summary_mode = "yes")})
    with pytest.raises(ValueError, match = "evidence_basis"):
        validate_definitions({"bad": definition("BMDL", evidence_basis = "observed")})
