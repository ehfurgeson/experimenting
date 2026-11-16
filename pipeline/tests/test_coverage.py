import polars as pl
import pytest
from polars.testing import assert_frame_equal

from agrotox.coverage import coverage_tables
from agrotox.normalize import normalize_rows
from agrotox.storage import query_path, write_json
from agrotox.tables import MEASUREMENT_SCHEMA, compound_table, frame_from_rows
from agrotox.workflow import parse_snapshots

RULES = {
    "rat_oral": {"endpoint": "LD50", "species": "rat", "preferred_route": "oral"},
    "fish": {"endpoint": "LC50", "organism_group": "fish"},
}


def test_distinct_compounds_and_selected_denominators(snapshot_cache, curated_queries):
    write_json(query_path(snapshot_cache, "101"), {"query": "101", "cid": 101})
    annotations, compounds = parse_snapshots(snapshot_cache, [
        *curated_queries, {"query": "101", "chemical_group": "herbicide"},
    ])
    measurements = normalize_rows(annotations, compounds)
    originals = compounds.clone(), measurements.clone()
    matrix, groups = coverage_tables(compounds, pl.concat([measurements] * 10), RULES)
    assert matrix["compound_id"].to_list() == compounds["compound_id"].to_list()
    assert matrix["input_queries"][0].to_list() == ["alpha", "101"]
    assert matrix["rat_oral"].to_list() == [1, 1, 0, 0]
    assert matrix["fish"].to_list() == [1, 0, 0, 0]
    natural = groups.filter(pl.col("chemical_group") == "natural_product")
    assert natural["total_compounds"].to_list() == [3, 3]
    assert natural["compounds_with_data"].to_list() == [1, 0]
    assert_frame_equal(compounds, originals[0])
    assert_frame_equal(measurements, originals[1])


def test_null_and_third_groups_and_identical_duplicates():
    compounds = compound_table([
        {"compound_id": "A", "input_queries": ["a"], "chemical_group": None},
        {"compound_id": "B", "input_queries": ["b"], "chemical_group": "third"},
        {"compound_id": "C", "input_queries": ["c"], "chemical_group": "other"},
    ])
    matrix, groups = coverage_tables(pl.concat([compounds, compounds]),
                                     frame_from_rows([], MEASUREMENT_SCHEMA), RULES)
    assert matrix.height == 3
    assert groups.height == 6
    assert groups["compounds_with_data"].to_list() == [0] * 6
    assert groups["total_compounds"].to_list() == [1] * 6
    assert groups.filter(pl.col("chemical_group").is_null()).height == 2


@pytest.mark.parametrize("change", [
    {"chemical_group": "different"}, {"input_queries": ["different"]},
    {"preferred_name": "different"},
])
def test_conflicting_duplicate_identities_rejected(change):
    row = {"compound_id": "A", "input_queries": ["a"], "chemical_group": "group"}
    with pytest.raises(ValueError, match = "conflict"):
        coverage_tables(compound_table([row, {**row, **change}]),
                        frame_from_rows([], MEASUREMENT_SCHEMA), RULES)


@pytest.mark.parametrize("qualifier", [">", "<=", "range"])
def test_thresholds_and_ranges_supply_availability(qualifier):
    compounds = compound_table([{"compound_id": "A", "input_queries": ["a"]}])
    row = {"compound_id": "A", "endpoint": "LC50", "organism_group": "fish",
           "unit_standardized": "mg/L", "parse_status": "complete", "formulation_flag": False,
           "qualifier": qualifier, "value_standardized": 2.0}
    if qualifier == "range":
        row.update(value_standardized = None, value_lower_standardized = 1.0,
                   value_upper_standardized = 3.0)
    matrix, _ = coverage_tables(compounds, frame_from_rows([row], MEASUREMENT_SCHEMA), RULES)
    assert matrix["fish"].to_list() == [1]


def test_empty_inputs_have_stable_types():
    matrix, groups = coverage_tables(compound_table([]),
                                     frame_from_rows([], MEASUREMENT_SCHEMA), RULES)
    assert matrix.is_empty() and groups.is_empty()
    assert matrix.schema == {
        "compound_id": pl.String, "input_queries": pl.List(pl.String),
        "chemical_group": pl.String, "rat_oral": pl.Int64, "fish": pl.Int64,
    }
    assert groups.schema == {
        "chemical_group": pl.String, "endpoint": pl.String,
        "compounds_with_data": pl.Int64, "total_compounds": pl.Int64,
    }


def test_invalid_schema_identity_and_policy_names():
    empty = frame_from_rows([], MEASUREMENT_SCHEMA)
    with pytest.raises(ValueError, match = "schema"):
        coverage_tables(pl.DataFrame(), empty, RULES)
    with pytest.raises(ValueError, match = "nonnull"):
        coverage_tables(compound_table([{}]), empty, RULES)
    with pytest.raises(ValueError, match = "outside"):
        coverage_tables(compound_table([]),
                        frame_from_rows([{"compound_id": "orphan"}], MEASUREMENT_SCHEMA), RULES)
    with pytest.raises(ValueError, match = "collide"):
        coverage_tables(compound_table([]), empty, {"compound_id": {"endpoint": "LD50"}})


def test_no_matches_keeps_denominators(snapshot_cache, curated_queries):
    annotations, compounds = parse_snapshots(snapshot_cache, curated_queries)
    measurements = normalize_rows(annotations, compounds)
    matrix, groups = coverage_tables(compounds, measurements, {
        "unavailable": {"endpoint": "LC50", "species": "rainbow_trout",
                        "preferred_duration_hours": 48},
    })
    assert matrix["unavailable"].to_list() == [0] * 4
    assert groups["compounds_with_data"].sum() == 0
    assert groups["total_compounds"].sum() == 4
