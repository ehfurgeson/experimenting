from copy import deepcopy

import polars as pl
import pytest

from agrotox.coverage import matches, matching_expr
from agrotox.normalize import normalize_rows
from agrotox.tables import MEASUREMENT_SCHEMA
from agrotox.workflow import parse_snapshots


@pytest.fixture
def definition():
    return {
        "endpoint": "LC50", "organism_group": "fish", "species": "rainbow_trout",
        "preferred_duration_hours": 96, "preferred_route": "inhalation",
        "standard_unit": "mg/L", "label": "Display only", "endpoint_family": "aquatic",
        "context_note": "No context is supplied by this text",
    }


@pytest.fixture
def record():
    return {
        "endpoint": "LC50", "organism_group": "fish", "species": "rainbow_trout",
        "duration_hours": 96.0, "exposure_route": "inhalation", "unit_standardized": "mg/L",
        "parse_status": "complete", "formulation_flag": False, "qualifier": "=",
        "value_standardized": 2.0, "value_lower_standardized": None,
        "value_upper_standardized": None,
    }


def check_agreement(record, definition, expected):
    original = deepcopy(record)
    assert matches(record, definition) is expected
    schema = {key: MEASUREMENT_SCHEMA[key] for key in record}
    frame = pl.DataFrame([record], schema = schema)
    assert frame.select(matching_expr(definition)).item() is expected
    assert record == original


@pytest.mark.parametrize("qualifier", ["=", "<", ">", "<=", ">=", "range"])
def test_valid_results(record, definition, qualifier):
    record["qualifier"] = qualifier
    if qualifier == "range":
        record.update(value_standardized = None, value_lower_standardized = 1.0,
                      value_upper_standardized = 3.0)
    check_agreement(record, definition, True)


@pytest.mark.parametrize("field,value", [
    ("endpoint", "LD50"), ("organism_group", "mammal"), ("species", "fish"),
    ("duration_hours", 48.0), ("exposure_route", "oral"), ("unit_standardized", "mg/kg"),
    ("parse_status", "partial"), ("parse_status", "failed"), ("formulation_flag", True),
    ("qualifier", "approx"), ("value_standardized", 0.0),
    ("value_standardized", -1.0), ("value_standardized", float("inf")),
    ("value_standardized", float("nan")), ("value_standardized", None),
    ("value_lower_standardized", 1.0), ("value_upper_standardized", 3.0),
])
def test_exclusions(record, definition, field, value):
    check_agreement({**record, field: value}, definition, False)


@pytest.mark.parametrize("field", [
    "endpoint", "organism_group", "species", "duration_hours", "exposure_route",
    "unit_standardized", "parse_status", "formulation_flag", "qualifier",
])
def test_missing_context(record, definition, field):
    check_agreement({**record, field: None}, definition, False)
    del record[field]
    assert not matches(record, definition)


@pytest.mark.parametrize("lower,upper", [(None, 3.0), (1.0, None), (3.0, 1.0),
    (1.0, 1.0), (0.0, 3.0), (1.0, float("inf")), (float("nan"), 3.0)])
def test_invalid_ranges(record, definition, lower, upper):
    record.update(qualifier = "range", value_standardized = None,
                  value_lower_standardized = lower, value_upper_standardized = upper)
    check_agreement(record, definition, False)


def test_broad_coverage_differs_from_comparison(record, definition):
    broad = {"endpoint": "LC50", "organism_group": "fish", "standard_unit": "mg/L"}
    for changes in [{"species": "fathead_minnow"}, {"duration_hours": None},
                    {"exposure_route": None}, {"duration_hours": 48.0}]:
        check_agreement({**record, **changes}, broad, True)
        check_agreement({**record, **changes}, definition, False)


def test_empty_frame_and_invalid_policy(record):
    frame = pl.DataFrame(schema = MEASUREMENT_SCHEMA)
    assert frame.filter(matching_expr({"endpoint": "LC50"})).is_empty()
    with pytest.raises(ValueError):
        matches(record, {"endpoint": "LC50", "typo": "fish"})
    with pytest.raises(ValueError):
        matching_expr({"endpoint": "LC50", "typo": "fish"})


@pytest.mark.parametrize("endpoint,unit", [("LD50", "mg/kg"), ("EC50", "mg/L")])
def test_other_endpoints(record, endpoint, unit):
    record.update(endpoint = endpoint, unit_standardized = unit)
    check_agreement(record, {"endpoint": endpoint}, True)
    record["unit_standardized"] = "ug/L"
    check_agreement(record, {"endpoint": endpoint}, False)


@pytest.mark.parametrize("field,value", [
    ("value_standardized", True), ("duration_hours", "96"),
    ("formulation_flag", 0), ("species", 1),
])
def test_malformed_row_types(record, definition, field, value):
    assert not matches({**record, field: value}, definition)


def test_range_cannot_also_have_scalar(record, definition):
    record.update(qualifier = "range", value_lower_standardized = 1.0,
                  value_upper_standardized = 3.0)
    check_agreement(record, definition, False)


def test_batch_agrees_with_rows(record, definition):
    rows = [record, {**record, "species": None}, {**record, "value_standardized": None}]
    schema = {key: MEASUREMENT_SCHEMA[key] for key in record}
    frame = pl.DataFrame(rows, schema = schema)
    assert frame.select(matching_expr(definition)).to_series().to_list() == [
        matches(row, definition) for row in rows
    ] == [True, False, False]


def test_saved_annotations_match_without_losing_range(snapshot_cache, curated_queries):
    annotations, compounds = parse_snapshots(snapshot_cache, curated_queries)
    measurements = normalize_rows(annotations, compounds)
    rule = {"endpoint": "LC50", "species": "rainbow_trout",
            "preferred_duration_hours": 96, "standard_unit": "mg/L"}
    selected = measurements.filter(matching_expr(rule))
    assert selected.height == 1
    row = selected.row(0, named = True)
    assert matches(row, rule)
    assert row["qualifier"] == "range"
    assert row["value_standardized"] is None
    assert row["value_lower_standardized"] == 2.0
    assert row["value_upper_standardized"] == 4.0
    assert not matches(row, {**rule, "preferred_duration_hours": 48})
