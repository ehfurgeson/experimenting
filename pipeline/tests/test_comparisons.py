"""Consolidation of comparable measurements into comparison records."""

import polars as pl
import pytest

from agrotox.analysis import (
    comparison_records,
    comparison_tables,
    compound_summaries,
    group_summaries,
)
from agrotox.tables import MEASUREMENT_SCHEMA, frame_from_rows

RULES = {
    "rat_oral": {"endpoint": "LD50", "species": "rat", "preferred_route": "oral"},
    "fish_96h": {
        "endpoint": "LC50", "organism_group": "fish", "preferred_duration_hours": 96,
    },
}


def measurement(**overrides):
    row = {
        "annotation_id": "ann-1",
        "compound_id": "PUBCHEM:1",
        "record_title": "Toxicity",
        "section_path": ["Toxicity", "Acute Effects"],
        "information_name": "LD50",
        "description": "Rat oral LD50",
        "value_raw": "LD50 rat oral 1000 mg/kg",
        "value_kind": "String",
        "reference_numbers": [1],
        "sources": [{
            "reference_number": 1,
            "source_name": "Source A",
            "source_url": "https://example.org/a",
            "reference_json": "{\"n\":1}",
        }],
        "information_url": None,
        "information_json": "{}",
        "raw_file": "raw/pubchem/1/toxicity.json",
        "retrieved_at": "2026-01-01T00:00:00Z",
        "endpoint": "LD50",
        "species": "rat",
        "organism_group": "mammal",
        "exposure_route": "oral",
        "medium": None,
        "duration_value": None,
        "duration_unit": None,
        "duration_hours": None,
        "value_numeric": 1000.0,
        "value_lower": None,
        "value_upper": None,
        "qualifier": "=",
        "unit_raw": "mg/kg",
        "unit_standardized": "mg/kg",
        "value_standardized": 1000.0,
        "value_lower_standardized": None,
        "value_upper_standardized": None,
        "formulation_flag": False,
        "parse_status": "complete",
        "parse_note": "",
        "pubchem_cid": 1,
        "preferred_name": "Alpha",
        "chemical_group": "herbicide",
        "subgroup": None,
        "hrac_group": "1",
        "input_queries": ["alpha"],
        "source_notes": [],
    }
    row.update(overrides)
    return row


def frame(*rows):
    return frame_from_rows(rows, MEASUREMENT_SCHEMA)


def test_equal_values_from_different_sources_consolidate():
    rows = frame(
        measurement(),
        measurement(
            annotation_id = "ann-2",
            value_raw = "LD50 rat oral 1000 mg/kg (study B)",
            sources = [{
                "reference_number": 7,
                "source_name": "Source B",
                "source_url": "https://example.org/b",
                "reference_json": "{\"n\":7}",
            }],
        ),
    )
    records = comparison_records(rows, RULES)
    assert records.height == 1
    record = records.row(0, named = True)
    assert record["support_ids"] == ["ann-1", "ann-2"]
    assert record["support_count"] == 2
    assert [support["source_name"] for support in record["supports"]] == ["Source A", "Source B"]
    assert record["supports"][0]["value_raw"] == "LD50 rat oral 1000 mg/kg"


def test_equal_results_for_different_compounds_remain_separate():
    rows = frame(
        measurement(),
        measurement(annotation_id = "ann-2", compound_id = "PUBCHEM:2",
                    preferred_name = "Beta", chemical_group = "other"),
    )
    records = comparison_records(rows, RULES)
    assert records.select(
        "compound_id", "preferred_name", "chemical_group", "support_ids",
    ).to_dicts() == [
        {"compound_id": "PUBCHEM:1", "preferred_name": "Alpha",
         "chemical_group": "herbicide", "support_ids": ["ann-1"]},
        {"compound_id": "PUBCHEM:2", "preferred_name": "Beta",
         "chemical_group": "other", "support_ids": ["ann-2"]},
    ]
    assert comparison_records(rows.reverse(), RULES).to_dicts() == records.to_dicts()


def test_different_contexts_remain_separate_records():
    rules = {"mammal": {"endpoint": "LD50", "organism_group": "mammal"}}
    rows = frame(
        measurement(),
        measurement(annotation_id = "ann-2", species = "mouse"),
        measurement(annotation_id = "ann-3", exposure_route = "dermal"),
        measurement(annotation_id = "ann-4", duration_hours = 24.0),
    )
    records = comparison_records(rows, rules)
    assert records.height == 4
    assert sorted(records["species"].to_list()) == ["mouse", "rat", "rat", "rat"]
    assert sorted(records["exposure_route"].to_list()) == ["dermal", "oral", "oral", "oral"]


def test_alias_and_row_order_do_not_change_records():
    rows = frame(
        measurement(annotation_id = "ann-1"),
        measurement(annotation_id = "ann-2", value_standardized = 3000.0),
    )
    reversed_rows = frame(
        measurement(annotation_id = "ann-2", value_standardized = 3000.0),
        measurement(annotation_id = "ann-1"),
    )
    aliased = frame(
        measurement(annotation_id = "ann-1", input_queries = ["alpha", "101"]),
        measurement(annotation_id = "ann-2", value_standardized = 3000.0, input_queries = ["alpha"]),
    )
    first = comparison_records(rows, RULES)
    assert comparison_records(reversed_rows, RULES).to_dicts() == first.to_dicts()
    assert comparison_records(aliased, RULES).to_dicts() == first.to_dicts()


def test_null_durations_consolidate_and_are_kept():
    rows = frame(
        measurement(annotation_id = "ann-1", duration_hours = None),
        measurement(annotation_id = "ann-2", duration_hours = None),
    )
    records = comparison_records(rows, RULES)
    assert records.height == 1
    assert records["duration_hours"].to_list() == [None]
    assert records["support_ids"].to_list() == [["ann-1", "ann-2"]]


def test_inequalities_ranges_and_exact_values_stay_distinct():
    rows = frame(
        measurement(annotation_id = "ann-1"),
        measurement(annotation_id = "ann-2", qualifier = ">", value_standardized = 8000.0),
        measurement(
            annotation_id = "ann-3", qualifier = "range", value_standardized = None,
            value_lower_standardized = 2000.0, value_upper_standardized = 4000.0,
        ),
    )
    records = comparison_records(rows, RULES)
    assert records.height == 3
    assert sorted(records["qualifier"].to_list()) == ["=", ">", "range"]
    bounds = records.filter(pl.col("qualifier") == "range").row(0, named = True)
    assert bounds["value_lower_standardized"] == 2000.0
    assert bounds["value_upper_standardized"] == 4000.0
    assert bounds["value_standardized"] is None


def test_ineligible_and_unmatched_measurements_are_excluded():
    rows = frame(
        measurement(),
        measurement(annotation_id = "ann-2", parse_status = "partial"),
        measurement(annotation_id = "ann-3", formulation_flag = True),
        measurement(annotation_id = "ann-4", species = "rabbit"),
        measurement(annotation_id = "ann-5", unit_standardized = "mg/L"),
    )
    records = comparison_records(rows, RULES)
    assert records.height == 1
    assert records["support_ids"].to_list() == [["ann-1"]]


def test_each_definition_produces_its_own_comparison():
    rows = frame(
        measurement(),
        measurement(
            annotation_id = "ann-2", endpoint = "LC50", species = "rainbow_trout",
            organism_group = "fish", unit_standardized = "mg/L", value_standardized = 2.0,
            duration_hours = 96.0,
        ),
    )
    records = comparison_records(rows, RULES)
    assert records["comparison"].to_list() == ["rat_oral", "fish_96h"]
    assert records["compound_id"].to_list() == ["PUBCHEM:1", "PUBCHEM:1"]


def test_empty_inputs_return_typed_empty_records():
    records = comparison_records(frame_from_rows([], MEASUREMENT_SCHEMA), RULES)
    assert records.is_empty()
    assert records.schema["support_ids"] == pl.List(pl.String)
    assert records.schema["compound_id"] == pl.String
    with pytest.raises(ValueError, match = "nonempty"):
        comparison_records(frame(measurement()), {})


def compound_row(compound_id, chemical_group, name = "Alpha"):
    return {
        "compound_id": compound_id,
        "pubchem_cid": None,
        "preferred_name": name,
        "chemical_group": chemical_group,
        "subgroup": None,
        "hrac_group": None,
        "input_queries": [compound_id],
        "source_notes": [],
    }


def compounds_frame(*rows):
    return frame_from_rows(rows, {
        "compound_id": pl.String,
        "pubchem_cid": pl.Int64,
        "preferred_name": pl.String,
        "chemical_group": pl.String,
        "subgroup": pl.String,
        "hrac_group": pl.String,
        "input_queries": pl.List(pl.String),
        "source_notes": pl.List(pl.String),
    })


def test_compound_summary_separates_exact_censored_and_range():
    rows = frame(
        measurement(annotation_id = "ann-1", value_standardized = 1000.0),
        measurement(annotation_id = "ann-2", value_standardized = 1000.0),
        measurement(annotation_id = "ann-3", value_standardized = 3000.0),
        measurement(annotation_id = "ann-4", qualifier = ">", value_standardized = 8000.0),
        measurement(
            annotation_id = "ann-5", qualifier = "range", value_standardized = None,
            value_lower_standardized = 2000.0, value_upper_standardized = 4000.0,
        ),
    )
    records = comparison_records(rows, RULES)
    summaries = compound_summaries(records)
    assert summaries.height == 1
    summary = summaries.row(0, named = True)
    assert summary["n_records"] == 4
    assert summary["n_exact"] == 2
    assert summary["n_censored"] == 1
    assert summary["n_ranges"] == 1
    assert summary["exact_median"] == 2000.0
    assert summary["exact_min"] == 1000.0
    assert summary["exact_max"] == 3000.0


def test_group_summary_weights_compounds_equally():
    compounds = compounds_frame(
        compound_row("PUBCHEM:1", "herbicide", "Alpha"),
        compound_row("PUBCHEM:2", "herbicide", "Beta"),
    )
    rows = frame(
        measurement(annotation_id = "ann-1", value_standardized = 1000.0),
        measurement(annotation_id = "ann-2", value_standardized = 3000.0),
        measurement(annotation_id = "ann-3", value_standardized = 3000.0),
        measurement(annotation_id = "ann-4", compound_id = "PUBCHEM:2",
                    value_standardized = 10000.0),
    )
    records, summaries, groups = comparison_tables(compounds, rows, RULES)
    assert records.height == 3
    alpha = summaries.filter(pl.col("compound_id") == "PUBCHEM:1").row(0, named = True)
    assert alpha["n_records"] == 2
    herbicide = groups.filter(
        (pl.col("comparison") == "rat_oral") & (pl.col("chemical_group") == "herbicide")
    ).row(0, named = True)
    assert herbicide["total_compounds"] == 2
    assert herbicide["compounds_with_data"] == 2
    assert herbicide["compounds_with_exact"] == 2
    assert herbicide["median_of_compound_exact_medians"] == 6000.0


def test_group_median_is_not_a_pooled_record_median():
    compounds = compounds_frame(
        compound_row("PUBCHEM:1", "herbicide", "Alpha"),
        compound_row("PUBCHEM:2", "herbicide", "Beta"),
    )
    rows = frame(
        measurement(annotation_id = "ann-1", value_standardized = 1000.0),
        measurement(annotation_id = "ann-2", value_standardized = 1000.0),
        measurement(annotation_id = "ann-3", value_standardized = 1000.0),
        measurement(annotation_id = "ann-4", compound_id = "PUBCHEM:2",
                    value_standardized = 9000.0),
    )
    records, summaries, groups = comparison_tables(compounds, rows, RULES)
    assert records.height == 2
    alpha = summaries.filter(pl.col("compound_id") == "PUBCHEM:1").row(0, named = True)
    assert alpha["exact_median"] == 1000.0
    herbicide = groups.filter(
        (pl.col("comparison") == "rat_oral") & (pl.col("chemical_group") == "herbicide")
    ).row(0, named = True)
    # The pooled record median is 1000.0; the median of compound medians is 5000.0.
    assert herbicide["median_of_compound_exact_medians"] == 5000.0


def test_unexpected_and_zero_data_groups_keep_denominators():
    compounds = compounds_frame(
        compound_row("PUBCHEM:1", "herbicide", "Alpha"),
        compound_row("PUBCHEM:2", None, "Ungrouped"),
        compound_row("PUBCHEM:3", "synthetic_analogue", "Gamma"),
    )
    rows = frame(measurement(annotation_id = "ann-1", value_standardized = 1000.0))
    records, summaries, groups = comparison_tables(compounds, rows, RULES)
    assert records.height == 1
    assert summaries.height == 1
    assert groups.height == 6
    assert {row["chemical_group"] for row in groups.to_dicts()} == {
        "herbicide", None, "synthetic_analogue",
    }
    assert all(row["compounds_with_data"] == 0 for row in groups.to_dicts() if
               row["comparison"] == "fish_96h")
    ungrouped = groups.filter(pl.col("chemical_group").is_null()).row(0, named = True)
    assert ungrouped["total_compounds"] == 1
    assert ungrouped["median_of_compound_exact_medians"] is None


def test_censored_only_compound_has_a_typed_null_median():
    compounds = compounds_frame(compound_row("PUBCHEM:1", "herbicide", "Alpha"))
    rows = frame(
        measurement(annotation_id = "ann-1", qualifier = ">", value_standardized = 8000.0),
    )
    _records, summaries, groups = comparison_tables(compounds, rows, RULES)
    assert summaries.schema["exact_median"] == pl.Float64
    assert summaries["exact_median"].to_list() == [None]
    assert summaries["n_censored"].to_list() == [1]
    assert summaries["n_exact"].to_list() == [0]
    herbicide = groups.filter(
        (pl.col("comparison") == "rat_oral") & (pl.col("chemical_group") == "herbicide")
    ).row(0, named = True)
    assert herbicide["median_of_compound_exact_medians"] is None
    assert herbicide["compounds_with_censoring"] == 1
    assert herbicide["compounds_with_exact"] == 0


def test_empty_measurements_give_typed_empty_summaries():
    compounds = compounds_frame(compound_row("PUBCHEM:1", "herbicide", "Alpha"))
    empty = frame_from_rows([], MEASUREMENT_SCHEMA)
    records, summaries, groups = comparison_tables(compounds, empty, RULES)
    assert records.is_empty() and summaries.is_empty()
    assert summaries.schema["exact_median"] == pl.Float64
    assert groups.height == 2
    assert groups["total_compounds"].to_list() == [1, 1]
    assert groups["compounds_with_data"].to_list() == [0, 0]


def test_conflicting_compound_identities_are_rejected():
    compounds = compounds_frame(
        compound_row("PUBCHEM:1", "herbicide", "Alpha"),
        compound_row("PUBCHEM:1", "natural_product", "Alpha"),
    )
    with pytest.raises(ValueError, match = "conflicting"):
        group_summaries(
            compound_summaries(comparison_records(frame(measurement()), RULES)),
            compounds, RULES,
        )


@pytest.mark.parametrize("field", [
    "study_type", "duration_class", "effect", "evidence_basis",
    "benchmark_response", "benchmark_response_type", "model_name", "model_id",
    "confidence_level", "study_id",
])
def test_study_context_is_preserved_and_constrains_comparisons(field):
    rows = frame(
        measurement(**{field: "context-a"}),
        measurement(annotation_id = "ann-2", **{field: "context-b"}),
        measurement(annotation_id = "ann-3"),
    )
    broad = comparison_records(rows, RULES)
    assert broad.height == 3
    assert set(broad[field].to_list()) == {"context-a", "context-b", None}
    selected = comparison_records(rows, {
        "contextual": {**RULES["rat_oral"], field: "context-a"},
    })
    assert selected.height == 1
    assert selected["support_ids"].to_list() == [["ann-1"]]
