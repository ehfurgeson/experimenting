"""Extraction audit and review queue for compounds without comparable data."""

import polars as pl
import pytest

from agrotox.analysis import comparison_records, extraction_audit, review_queue
from agrotox.tables import MEASUREMENT_SCHEMA, compound_table, frame_from_rows

RULES = {"rat_oral": {"endpoint": "LD50", "species": "rat", "preferred_route": "oral"}}


def compound(compound_id, resolution_status = "resolved", toxicity_status = "found"):
    return {
        "compound_id": compound_id,
        "pubchem_cid": 1,
        "input_queries": [compound_id],
        "preferred_name": compound_id,
        "chemical_group": "herbicide",
        "subgroup": None,
        "hrac_group": None,
        "source_notes": [],
        "inchi": None,
        "inchikey": None,
        "smiles": None,
        "connectivity_smiles": None,
        "molecular_formula": None,
        "molecular_weight": None,
        "iupac_name": None,
        "resolution_status": resolution_status,
        "toxicity_status": toxicity_status,
    }


def measurement(compound_id, parse_status = "complete", note = "", **overrides):
    row = {
        "annotation_id": f"ann-{compound_id}-{parse_status}",
        "compound_id": compound_id,
        "record_title": "Toxicity",
        "section_path": ["Toxicity"],
        "information_name": "LD50",
        "description": "Rat oral LD50",
        "value_raw": "LD50 rat oral 1000 mg/kg",
        "value_kind": "String",
        "reference_numbers": [1],
        "sources": [{
            "reference_number": 1,
            "source_name": "Source A",
            "source_url": "https://example.org/a",
            "reference_json": "{}",
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
        "parse_status": parse_status,
        "parse_note": note,
        "pubchem_cid": 1,
        "preferred_name": compound_id,
        "chemical_group": "herbicide",
        "subgroup": None,
        "hrac_group": None,
        "input_queries": [compound_id],
        "source_notes": [],
    }
    row.update(overrides)
    return row


def annotations_frame(*compound_ids):
    return frame_from_rows(
        [{"annotation_id": f"ann-{name}", "compound_id": name} for name in compound_ids],
        {"annotation_id": pl.String, "compound_id": pl.String},
    )


@pytest.mark.parametrize("resolution, toxicity, reason", [
    ("unresolved", "not_retrieved", "unresolved_query"),
    ("resolved", "pending", "toxicity_request_failed_or_pending"),
    ("resolved", "not_retrieved", "toxicity_request_failed_or_pending"),
    ("resolved", "missing", "toxicity_section_missing"),
    ("resolved", "found", "no_annotations_in_saved_section"),
])
def test_audit_reasons(resolution, toxicity, reason):
    compounds = compound_table([compound("C1", resolution, toxicity)])
    audit = extraction_audit(
        compounds, annotations_frame(), frame_from_rows([], MEASUREMENT_SCHEMA),
        frame_from_rows([], {"compound_id": pl.String}),
    )
    assert audit["availability_reason"].to_list() == [reason]


def test_audit_reasons_for_extracted_and_unmatched_measurements():
    compounds = compound_table([
        compound("C1"),
        compound("C2"),
        compound("C3"),
    ])
    measurements = frame_from_rows([
        measurement("C1", parse_status = "partial", note = "formulation or mixture context"),
        measurement("C2", species = "rabbit"),
    ], MEASUREMENT_SCHEMA)
    records = comparison_records(measurements, RULES)
    audit = extraction_audit(compounds, annotations_frame("C1", "C2"),
                             measurements, records)
    reasons = dict(zip(audit["compound_id"].to_list(), audit["availability_reason"].to_list()))
    assert reasons["C1"] == "annotations_present_no_supported_complete_measurement"
    assert reasons["C2"] == "complete_measurements_outside_comparison_contexts"
    assert reasons["C3"] == "no_annotations_in_saved_section"


def test_audit_reports_comparable_data():
    compounds = compound_table([compound("C1")])
    measurements = frame_from_rows([measurement("C1")], MEASUREMENT_SCHEMA)
    records = comparison_records(measurements, RULES)
    audit = extraction_audit(compounds, annotations_frame("C1"), measurements, records)
    assert audit["availability_reason"].to_list() == ["comparison_data_available"]
    assert audit["annotations"].to_list() == [1]
    assert audit["complete"].to_list() == [1]
    assert audit["comparison_records"].to_list() == [1]


def test_audit_keeps_counts_for_review_rows():
    compounds = compound_table([compound("C1")])
    measurements = frame_from_rows([
        measurement("C1", parse_status = "partial", note = "note one"),
        measurement("C1", parse_status = "failed", note = "note two"),
    ], MEASUREMENT_SCHEMA)
    audit = extraction_audit(compounds, annotations_frame("C1"), measurements,
                             frame_from_rows([], {"compound_id": pl.String}))
    assert audit["annotations"].to_list() == [1]
    assert audit["partial"].to_list() == [1]
    assert audit["failed"].to_list() == [1]
    assert audit["complete"].to_list() == [0]


def test_review_queue_keeps_only_partial_and_failed_rows():
    measurements = frame_from_rows([
        measurement("C1", parse_status = "complete"),
        measurement("C1", parse_status = "partial", note = "formulation or mixture context"),
        measurement("C1", parse_status = "failed", note = "no single supported result"),
    ], MEASUREMENT_SCHEMA)
    queue = review_queue(measurements)
    assert queue.height == 2
    assert sorted(queue["parse_status"].to_list()) == ["failed", "partial"]
    assert "formulation or mixture context" in queue["parse_note"].to_list()
    assert queue["sources"].to_list()[0][0]["source_name"] == "Source A"
    assert queue["value_raw"].to_list()[0] == "LD50 rat oral 1000 mg/kg"


def test_review_queue_of_empty_measurements_is_typed_empty():
    queue = review_queue(frame_from_rows([], MEASUREMENT_SCHEMA))
    assert queue.is_empty()
    assert queue.schema["annotation_id"] == pl.String
    assert queue.schema["sources"] == pl.List(pl.Struct({
        "reference_number": pl.Int64, "source_name": pl.String,
        "source_url": pl.String, "reference_json": pl.String,
    }))
