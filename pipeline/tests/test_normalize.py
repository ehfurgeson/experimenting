"""Annotation interpretation preserves provenance and explicit uncertainty."""

import json
from copy import deepcopy

import polars as pl
import pytest

from agrotox.identity import reconcile_compounds
from agrotox.normalize import normalize_annotation, normalize_rows
from agrotox.tables import MEASUREMENT_SCHEMA, annotation_table, compound_table
from agrotox.workflow import parse_snapshots


@pytest.fixture
def annotation():
    return {
        "annotation_id": "synthetic:one", "compound_id": "PUBCHEM:101",
        "record_title": "Synthetic Alpha", "section_path": ["Toxicity"],
        "information_name": "LD50", "description": "rat oral",
        "value_raw": "1 g/kg", "value_kind": "StringWithMarkup",
        "reference_numbers": [1], "sources": [{
            "reference_number": 1, "source_name": "Synthetic source", "source_url": None,
            "reference_json": '{"ReferenceNumber":1,"SourceName":"Synthetic source"}',
        }],
        "information_url": "https://example.org/info", "information_json": '{"note":"keep"}',
        "raw_file": "synthetic.json", "retrieved_at": "2026-01-01T00:00:00Z",
    }


def test_value_conversion_and_every_provenance_field_survive(annotation):
    original = deepcopy(annotation)
    result = normalize_annotation(annotation)
    assert result["parse_status"] == "complete"
    assert result["value_numeric"] == 1.0
    assert result["value_standardized"] == 1000.0
    assert result["unit_standardized"] == "mg/kg"
    assert result["species"] == "rat"
    assert result["exposure_route"] == "oral"
    assert result["duration_hours"] is None
    for field, value in original.items():
        assert result[field] == value
    result["sources"][0]["source_name"] = "edited output"
    assert annotation == original


@pytest.mark.parametrize("text, species, group", [
    ("rat", "rat", "mammal"), ("mice", "mouse", "mammal"), ("rabbit", "rabbit", "mammal"),
    ("Rattus norvegicus", "rat", "mammal"), ("Mus musculus", "mouse", "mammal"),
    ("fish", "fish", "fish"), ("trout", "trout", "fish"), ("carp", "carp", "fish"),
    ("bluegill", "bluegill", "fish"), ("rainbow trout fish", "rainbow_trout", "fish"),
    ("Oncorhynchus mykiss", "rainbow_trout", "fish"),
    ("Oncorhynchus\n  mykiss", "rainbow_trout", "fish"),
    ("Salmo gairdneri", "rainbow_trout", "fish"),
    ("Pimephales promelas fish", "fathead_minnow", "fish"),
    ("fathead minnow", "fathead_minnow", "fish"),
    ("Daphnia magna", "daphnia_magna", "aquatic_invertebrate"),
    ("daphnia", "daphnia", "aquatic_invertebrate"),
    ("algae", "algae", "algae"), ("bee", "bee", "bee"), ("mallard", "mallard", "bird"),
])
def test_species_aliases(annotation, text, species, group):
    result = normalize_annotation({**annotation, "description": text})
    assert result["parse_status"] == "complete"
    assert result["species"] == species
    assert result["organism_group"] == group


@pytest.mark.parametrize("text, route", [
    ("oral", "oral"), ("dermal", "dermal"), ("percutaneous", "dermal"),
    ("inhalation", "inhalation"), ("contact", "contact"),
    ("intraperitoneal", "intraperitoneal"), ("ip", "intraperitoneal"),
    ("intravenous", "intravenous"), ("iv", "intravenous"),
    ("subcutaneous", "subcutaneous"), ("sc", "subcutaneous"),
])
def test_route_aliases(annotation, text, route):
    result = normalize_annotation({**annotation, "description": text})
    assert result["parse_status"] == "complete"
    assert result["exposure_route"] == route


@pytest.mark.parametrize("context, hours", [
    ("96 h", 96.0), ("4 days", 96.0), ("4 days; 96 h", 96.0),
    ("1 week", 168.0), ("2 wk; 14 days", 336.0),
])
def test_explicit_equivalent_durations(annotation, context, hours):
    result = normalize_annotation({**annotation, "description": context})
    assert result["parse_status"] == "complete"
    assert result["duration_hours"] == hours


@pytest.mark.parametrize("context", [
    "-96 h", "− 96 h", "NaN h", "inf h", "∞ h", "0 h", "24-96 h", "1 month",
    "1–2 weeks", "1 week; 96 h",
])
def test_invalid_or_unsupported_exposure_duration_is_partial(annotation, context):
    result = normalize_annotation({**annotation, "description": context})
    assert result["parse_status"] == "partial"
    assert result["duration_hours"] is None
    assert result["parse_note"]


@pytest.mark.parametrize("context", [
    "rat and mouse oral", "rat oral and dermal", "trout 24 h 96 h", "LD50 and LC50 rat",
    "rainbow trout and fathead minnow", "LD50 and IC50", "water and air",
])
def test_ambiguous_context_remains_partial(annotation, context):
    result = normalize_annotation({**annotation, "description": context})
    assert result["parse_status"] == "partial"
    assert result["parse_note"]


@pytest.mark.parametrize("label", ["mixture", "formulation", "formulated product", "extract"])
def test_formulations_are_flagged_and_partial(annotation, label):
    result = normalize_annotation({**annotation, "description": f"rat oral {label}"})
    assert result["formulation_flag"] is True
    assert result["parse_status"] == "partial"


def test_missing_context_is_not_invented(annotation):
    result = normalize_annotation({**annotation, "description": ""})
    assert result["parse_status"] == "complete"
    for field in ["species", "organism_group", "exposure_route", "duration_hours", "medium"]:
        assert result[field] is None


@pytest.mark.parametrize("text, qualifier, scalar, low, high", [
    ("2-4 g/kg", "range", None, 2000.0, 4000.0),
    ("> 8 g/kg", ">", 8000.0, None, None),
    ("≤ 2 g/kg", "<=", 2000.0, None, None),
])
def test_scalars_thresholds_and_bounds_use_the_same_factor(annotation, text, qualifier, scalar, low, high):
    result = normalize_annotation({**annotation, "value_raw": text})
    assert result["parse_status"] == "complete"
    assert result["qualifier"] == qualifier
    assert result["value_standardized"] == scalar
    assert result["value_lower_standardized"] == low
    assert result["value_upper_standardized"] == high


def test_labelled_concentration_excludes_age_hardness_and_confidence_interval(annotation):
    text = (
        "LC50; Species: Pimephales promelas age 28 days; hardness 44 mg/L; "
        "Concentration: 102000 ug/L for 96 hr (95% CI 95000-109000 ug/L)"
    )
    result = normalize_annotation({**annotation, "information_name": "", "description": "", "value_raw": text})
    assert result["parse_status"] == "complete"
    assert result["species"] == "fathead_minnow"
    assert result["duration_hours"] == 96.0
    assert result["value_standardized"] == pytest.approx(102.0)
    assert result["unit_standardized"] == "mg/L"
    assert result["value_raw"] == text


@pytest.mark.parametrize("text", [
    "LC50; Concentration: 1 mg/L; Concentration: 2 mg/L",
    "LC50; hardness 44 mg/L; age 28 days",
    "LC50; Concentration: ; hardness 44 mg/L",
])
def test_ancillary_values_cannot_replace_missing_or_ambiguous_concentration(annotation, text):
    result = normalize_annotation({**annotation, "information_name": "", "description": "", "value_raw": text})
    assert result["parse_status"] == "partial"
    assert result["value_standardized"] is None


@pytest.mark.parametrize("description", [
    "rat age 28 days", "rat aged 28 days", "rat age of 28 days", "rat age (28 days)",
    "28 days old rat", "rat age 2 weeks", "2 wk old rat",
])
def test_explicit_age_in_metadata_is_not_exposure_duration(annotation, description):
    result = normalize_annotation({**annotation, "description": description})
    assert result["parse_status"] == "complete"
    assert result["duration_hours"] is None


@pytest.mark.parametrize("medium, status, value", [
    ("water", "complete", 5.0), ("aqueous", "complete", 5.0),
    ("air", "partial", None), ("fish", "partial", None), ("", "partial", None),
])
def test_ppm_does_not_infer_water_from_fish(annotation, medium, status, value):
    result = normalize_annotation({
        **annotation, "information_name": "LC50", "description": medium, "value_raw": "5 ppm",
    })
    assert result["parse_status"] == status
    assert result["value_standardized"] == value


@pytest.mark.parametrize("kind, text", [
    ("NumberArray", "3, 5 mg/kg"), ("NumberArray", "5 mg/kg"),
    ("CustomShape", '{"text":"LD50 5 mg/kg"}'),
])
def test_unsupported_value_kinds_never_become_complete(annotation, kind, text):
    result = normalize_annotation({**annotation, "value_kind": kind, "value_raw": text})
    assert result["parse_status"] == "partial"
    assert result["value_standardized"] is None


def test_unknown_narrative_is_retained_as_failed(annotation):
    source = {**annotation, "information_name": "Narrative", "description": "", "value_raw": "not a measurement"}
    result = normalize_annotation(source)
    assert result["parse_status"] == "failed"
    assert result["parse_note"]
    assert result["value_raw"] == source["value_raw"]


@pytest.mark.parametrize("text", ["approximately 3 mg/kg", "-5 mg/kg", "0 mg/kg", "5 mg/L", "1e308 g/kg"])
def test_invalid_or_incompatible_values_stay_partial(annotation, text):
    result = normalize_annotation({**annotation, "value_raw": text})
    assert result["parse_status"] == "partial"
    assert result["value_standardized"] is None


def test_synthetic_pipeline_produces_one_row_per_annotation(snapshot_cache, curated_queries):
    annotations, compounds = parse_snapshots(snapshot_cache, curated_queries)
    measurements = normalize_rows(annotations, compounds)
    assert measurements.height == 7
    assert measurements.schema == MEASUREMENT_SCHEMA
    assert measurements["parse_status"].to_list().count("complete") == 5
    assert measurements["parse_status"].to_list().count("partial") == 1
    assert measurements["parse_status"].to_list().count("failed") == 1
    for field in annotations.columns:
        assert measurements[field].to_list() == annotations[field].to_list()
    assert measurements["chemical_group"].to_list() == ["herbicide"] * 6 + ["natural_product"]
    assert measurements["annotation_id"].to_list() == annotations["annotation_id"].to_list()
    assert json.loads(measurements["information_json"][0])


def test_empty_normalization_retains_schema():
    assert normalize_rows(annotation_table([]), compound_table([])).schema == MEASUREMENT_SCHEMA


def test_extra_provenance_columns_survive_table_normalization(snapshot_cache, curated_queries):
    annotations, compounds = parse_snapshots(snapshot_cache, curated_queries)
    annotations = annotations.with_columns(pl.lit("trace").alias("custom_provenance"))
    normalized = normalize_rows(annotations, compounds)
    assert normalized["custom_provenance"].to_list() == ["trace"] * 7


def test_missing_or_duplicate_compounds_raise(snapshot_cache, curated_queries):
    annotations, compounds = parse_snapshots(snapshot_cache, curated_queries)
    with pytest.raises(ValueError):
        normalize_rows(annotations, compound_table([]))
    with pytest.raises(ValueError):
        normalize_rows(annotations, pl.concat([compounds, compounds.head(1)]))


def test_compound_names_cannot_supply_measurement_context(annotation):
    source = {**annotation, "information_name": "Narrative", "description": ""}
    compounds = compound_table(reconcile_compounds([{"query": "alpha"}], {
        "alpha": {"cid": 101, "properties": {"CID": 101, "Title": "LD50 rat oral 96 h"}, "metadata": {}},
    }))
    normalized = normalize_rows(annotation_table([source]), compounds)
    assert normalized["parse_status"].to_list() == ["failed"]
    assert normalized["species"].to_list() == [None]


@pytest.mark.parametrize("context, field", [
    ("rat and mouse", "species"), ("oral and dermal", "exposure_route"),
    ("24 h and 96 h", "duration_hours"), ("LD50 and LC50", "endpoint"),
    ("water and air", "medium"),
])
def test_conflicting_context_is_not_arbitrarily_selected(annotation, context, field):
    result = normalize_annotation({**annotation, "description": context})
    assert result["parse_status"] == "partial"
    assert result[field] is None


@pytest.mark.parametrize("endpoint", ["IC50", "NOEC", "LD10"])
def test_unsupported_endpoint_is_failed(annotation, endpoint):
    result = normalize_annotation({**annotation, "information_name": endpoint})
    assert result["parse_status"] == "failed"
    assert result["endpoint"] is None
    assert result["value_standardized"] is None


@pytest.mark.parametrize("text", ["1e305-1e308 g/kg", "1e-323 ug/kg"])
def test_invalid_conversion_does_not_expose_zero_or_half_a_range(annotation, text):
    result = normalize_annotation({**annotation, "value_raw": text})
    assert result["parse_status"] == "partial"
    assert all(result[field] is None for field in [
        "value_standardized", "value_lower_standardized", "value_upper_standardized",
    ])


def test_wrapper_rejects_bad_schema_and_reserved_columns(snapshot_cache, curated_queries):
    annotations, compounds = parse_snapshots(snapshot_cache, curated_queries)
    with pytest.raises(ValueError, match = "schema"):
        normalize_rows(annotations.drop("value_raw"), compounds)
    with pytest.raises(ValueError, match = "collide"):
        normalize_rows(annotations.with_columns(pl.lit("old").alias("chemical_group")), compounds)


def test_context_cannot_come_from_titles_or_reference_metadata(annotation):
    source = {
        **annotation, "record_title": "LD50 rat oral 96 h", "information_name": "Narrative",
        "description": "", "information_json": '{"note":"LD50 mouse dermal"}',
    }
    source["sources"][0]["source_name"] = "LD50 fish 24 h"
    result = normalize_annotation(source)
    assert result["parse_status"] == "failed"
    assert result["species"] is None
    assert result["duration_hours"] is None


def test_narrative_attribution_and_follow_up_are_not_direct_measurement_context(annotation):
    source = {
        **annotation, "information_name": "", "description": "",
        "value_raw": (
            "Several agents were compared relative to their LD50. "
            "Another chemical was administered at 3-5 mg/kg. "
            "Survival was recorded at the end of 14 days."
        ),
    }
    result = normalize_annotation(source)
    assert result["parse_status"] == "partial"
    assert "attribution review" in result["parse_note"]
    assert result["duration_hours"] is None


@pytest.mark.parametrize("duration", ["14 days", "2 weeks", "2 wk"])
def test_follow_up_duration_in_metadata_is_not_exposure(annotation, duration):
    result = normalize_annotation({**annotation, "description": f"rat oral; follow-up {duration}"})
    assert result["parse_status"] == "complete"
    assert result["duration_hours"] is None


def test_interaction_section_is_retained_for_review(annotation):
    result = normalize_annotation({**annotation, "section_path": ["Toxicity", "Interactions"]})
    assert result["parse_status"] == "partial"
    assert "attribution review" in result["parse_note"]
