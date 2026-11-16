"""Explicit schemas for nullable, native Polars tables."""

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import polars as pl

from .contracts import Annotation, Compound

TableSchema = Mapping[str, pl.DataType | type[pl.DataType]]

COMPOUND_SCHEMA = {
    "compound_id": pl.String,
    "pubchem_cid": pl.Int64,
    "input_queries": pl.List(pl.String),
    "preferred_name": pl.String,
    "chemical_group": pl.String,
    "subgroup": pl.String,
    "hrac_group": pl.String,
    "source_notes": pl.List(pl.String),
    "inchi": pl.String,
    "inchikey": pl.String,
    "smiles": pl.String,
    "connectivity_smiles": pl.String,
    "molecular_formula": pl.String,
    "molecular_weight": pl.Float64,
    "iupac_name": pl.String,
    "resolution_status": pl.String,
    "toxicity_status": pl.String,
}

SOURCE_REFERENCE_SCHEMA = {
    "reference_number": pl.Int64,
    "source_name": pl.String,
    "source_url": pl.String,
    "reference_json": pl.String,
}

ANNOTATION_SCHEMA = {
    "annotation_id": pl.String,
    "compound_id": pl.String,
    "record_title": pl.String,
    "section_path": pl.List(pl.String),
    "information_name": pl.String,
    "description": pl.String,
    "value_raw": pl.String,
    "value_kind": pl.String,
    "reference_numbers": pl.List(pl.Int64),
    "sources": pl.List(pl.Struct(SOURCE_REFERENCE_SCHEMA)),
    "information_url": pl.String,
    "information_json": pl.String,
    "raw_file": pl.String,
    "retrieved_at": pl.String,
}

STUDY_CONTEXT_SCHEMA = dict.fromkeys((
    "study_type", "duration_class", "effect", "evidence_basis",
    "benchmark_response", "benchmark_response_type", "model_name", "model_id",
    "confidence_level", "study_id",
), pl.String)

NORMALIZED_ANNOTATION_SCHEMA = {
    **ANNOTATION_SCHEMA,
    **STUDY_CONTEXT_SCHEMA,
    "endpoint": pl.String,
    "species": pl.String,
    "organism_group": pl.String,
    "exposure_route": pl.String,
    "medium": pl.String,
    "duration_value": pl.Float64,
    "duration_unit": pl.String,
    "duration_hours": pl.Float64,
    "value_numeric": pl.Float64,
    "value_lower": pl.Float64,
    "value_upper": pl.Float64,
    "qualifier": pl.String,
    "unit_raw": pl.String,
    "unit_standardized": pl.String,
    "value_standardized": pl.Float64,
    "value_lower_standardized": pl.Float64,
    "value_upper_standardized": pl.Float64,
    "formulation_flag": pl.Boolean,
    "parse_status": pl.String,
    "parse_note": pl.String,
}
COMPOUND_CONTEXT_SCHEMA = {field: COMPOUND_SCHEMA[field] for field in (
    "pubchem_cid", "preferred_name", "chemical_group", "subgroup", "hrac_group",
    "input_queries", "source_notes",
)}
MEASUREMENT_SCHEMA = {**NORMALIZED_ANNOTATION_SCHEMA, **COMPOUND_CONTEXT_SCHEMA}


SUPPORT_SCHEMA = {
    "annotation_id": pl.String,
    "value_raw": pl.String,
    "reference_number": pl.Int64,
    "source_name": pl.String,
    "source_url": pl.String,
    "reference_json": pl.String,
}

COMPARISON_RECORD_SCHEMA = {
    "comparison": pl.String,
    "summary_eligible": pl.Boolean,
    "compound_id": pl.String,
    "preferred_name": pl.String,
    "chemical_group": pl.String,
    "endpoint": pl.String,
    **STUDY_CONTEXT_SCHEMA,
    "species": pl.String,
    "exposure_route": pl.String,
    "duration_hours": pl.Float64,
    "unit_standardized": pl.String,
    "qualifier": pl.String,
    "value_standardized": pl.Float64,
    "value_lower_standardized": pl.Float64,
    "value_upper_standardized": pl.Float64,
    "support_ids": pl.List(pl.String),
    "support_count": pl.Int64,
    "supports": pl.List(pl.Struct(SUPPORT_SCHEMA)),
}

COMPOUND_SUMMARY_SCHEMA = {
    "comparison": pl.String,
    "compound_id": pl.String,
    "preferred_name": pl.String,
    "chemical_group": pl.String,
    "n_records": pl.Int64,
    "n_exact": pl.Int64,
    "n_censored": pl.Int64,
    "n_ranges": pl.Int64,
    "exact_median": pl.Float64,
    "exact_min": pl.Float64,
    "exact_max": pl.Float64,
}

GROUP_SUMMARY_SCHEMA = {
    "comparison": pl.String,
    "chemical_group": pl.String,
    "total_compounds": pl.Int64,
    "compounds_with_data": pl.Int64,
    "compounds_with_exact": pl.Int64,
    "compounds_with_censoring": pl.Int64,
    "compounds_with_ranges": pl.Int64,
    "median_of_compound_exact_medians": pl.Float64,
    "min_compound_exact_median": pl.Float64,
    "max_compound_exact_median": pl.Float64,
}

AUDIT_SCHEMA = {
    "compound_id": pl.String,
    "preferred_name": pl.String,
    "chemical_group": pl.String,
    "resolution_status": pl.String,
    "toxicity_status": pl.String,
    "annotations": pl.Int64,
    "complete": pl.Int64,
    "partial": pl.Int64,
    "failed": pl.Int64,
    "comparison_records": pl.Int64,
    "availability_reason": pl.String,
}

REVIEW_QUEUE_SCHEMA = MEASUREMENT_SCHEMA

EPA_IDENTITY_CANDIDATE_SCHEMA = {
    "compound_id": pl.String,
    "pubchem_cid": pl.Int64,
    "search_basis": pl.String,
    "search_term": pl.String,
    "dtxsid": pl.String,
    "preferred_name": pl.String,
    "casrn": pl.String,
    "inchikey": pl.String,
    "smiles": pl.String,
    "inchi": pl.String,
    "molecular_formula": pl.String,
    "molecular_weight": pl.Float64,
    "total_assays": pl.Int64,
    "active_assays": pl.Int64,
    "detail_status": pl.String,
    "rank": pl.Int64,
    "match_strength": pl.String,
    "provider_suggestions": pl.List(pl.String),
}

EPA_IDENTITY_CROSSWALK_SCHEMA = {
    "compound_id": pl.String,
    "pubchem_cid": pl.Int64,
    "input_queries": pl.List(pl.String),
    "dtxsid": pl.String,
    "status": pl.String,
    "match_strength": pl.String,
    "inchikey": pl.String,
    "candidate_count": pl.Int64,
    "reason": pl.String,
}

TOXCAST_ASSAY_SCHEMA = {
    "compound_id": pl.String,
    "dtxsid": pl.String,
    "aeid": pl.Int64,
    "aid": pl.Int64,
    "assay_component_endpoint_name": pl.String,
    "assay_function_type": pl.String,
    "intended_target_type": pl.String,
    "intended_target_family": pl.String,
    "biological_process_target": pl.String,
    "detection_technology": pl.String,
    "assay_format_type": pl.String,
    "organism": pl.String,
    "taxon_name": pl.String,
    "tissue": pl.String,
    "cell_format": pl.String,
    "timepoint_hours": pl.Float64,
    "hit_call": pl.Float64,
    "activity_value": pl.Float64,
    "benchmark_dose": pl.Float64,
    "concentration_min": pl.Float64,
    "concentration_max": pl.Float64,
    "concentration_unit": pl.String,
    "response_min": pl.Float64,
    "response_max": pl.Float64,
    "model": pl.String,
    "model_type": pl.Int64,
    "fit_category": pl.Int64,
    "n_concentrations": pl.Int64,
    "n_replicates": pl.Float64,
    "n_points": pl.Int64,
    "measurement_kind": pl.String,
    "evidence_class": pl.String,
    "source_release": pl.String,
    "retrieved_at": pl.String,
}

TOXCAST_COVERAGE_SCHEMA = {
    "compound_id": pl.String,
    "dtxsid": pl.String,
    "assays_with_result": pl.Int64,
    "assays_with_hit": pl.Int64,
    "assays_inactive": pl.Int64,
    "assays_inconclusive": pl.Int64,
    "distinct_targets": pl.Int64,
}

EPA_HAZARD_SCHEMA = {
    "source_record_json": pl.String,
    "compound_id": pl.String,
    "dtxsid": pl.String,
    "toxval_type": pl.String,
    "toxval_type_definition": pl.String,
    "human_eco": pl.String,
    "source": pl.String,
    "subsource": pl.String,
    "qualifier": pl.String,
    "value_numeric": pl.Float64,
    "value_units": pl.String,
    "value_numeric_original": pl.Float64,
    "value_units_original": pl.String,
    "species_common": pl.String,
    "latin_name": pl.String,
    "species_supercategory": pl.String,
    "exposure_route": pl.String,
    "exposure_method": pl.String,
    "exposure_form": pl.String,
    "media": pl.String,
    "strain": pl.String,
    "sex": pl.String,
    "lifestage": pl.String,
    "study_type": pl.String,
    "study_duration_value": pl.Float64,
    "study_duration_units": pl.String,
    "study_duration_class": pl.String,
    "toxicological_effect": pl.String,
    "experimental_record": pl.String,
    "quality": pl.String,
    "qc_category": pl.String,
    "guideline": pl.String,
    "reference": pl.String,
    "doi": pl.String,
    "title": pl.String,
    "author": pl.String,
    "year": pl.String,
    "source_url": pl.String,
    "external_source_id": pl.String,
    "source_hash": pl.String,
    "retrieved_at": pl.String,
}

EPA_HAZARD_COVERAGE_SCHEMA = {
    "compound_id": pl.String,
    "dtxsid": pl.String,
    "records": pl.Int64,
    "experimental_records": pl.Int64,
    "distinct_endpoints": pl.Int64,
    "distinct_species": pl.Int64,
    "distinct_references": pl.Int64,
}

COMPARISON_INPUT_SCHEMA = {
    "compound_id": pl.String,
    "endpoint": pl.String,
    **STUDY_CONTEXT_SCHEMA,
    "species": pl.String,
    "organism_group": pl.String,
    "exposure_route": pl.String,
    "duration_hours": pl.Float64,
    "unit_standardized": pl.String,
    "parse_status": pl.String,
    "formulation_flag": pl.Boolean,
    "qualifier": pl.String,
    "value_standardized": pl.Float64,
    "value_lower_standardized": pl.Float64,
    "value_upper_standardized": pl.Float64,
}

EPA_HAZARD_AUDIT_SCHEMA = {
    "compound_id": pl.String,
    "dtxsid": pl.String,
    "epa_identity_status": pl.String,
    "records": pl.Int64,
    "complete": pl.Int64,
    "partial": pl.Int64,
    "failed": pl.Int64,
    "comparison_records": pl.Int64,
    "availability_reason": pl.String,
}

EPA_PROPERTY_SCHEMA = {
    "compound_id": pl.String,
    "dtxsid": pl.String,
    "property_name": pl.String,
    "property_value": pl.Float64,
    "property_value_text": pl.String,
    "property_unit": pl.String,
    "property_origin": pl.String,
    "source_endpoint": pl.String,
    "source_name": pl.String,
    "source_description": pl.String,
    "public_source_url": pl.String,
    "dataset": pl.String,
    "model_name": pl.String,
    "model_id": pl.Int64,
    "property_category": pl.String,
    "property_description": pl.String,
    "ad_method": pl.String,
    "ad_value": pl.Float64,
    "ad_conclusion": pl.String,
    "ad_reasoning": pl.String,
    "retrieved_at": pl.String,
}

EPA_PROPERTY_COVERAGE_SCHEMA = {
    "compound_id": pl.String,
    "dtxsid": pl.String,
    "properties": pl.Int64,
    "measured_properties": pl.Int64,
    "calculated_properties": pl.Int64,
    "distinct_sources": pl.Int64,
}

EPA_TEST_SCHEMA = {
    "compound_id": pl.String,
    "dtxsid": pl.String,
    "provider_record_id": pl.String,
    "source_name": pl.String,
    "source_description": pl.String,
    "dtxcid": pl.String,
    "smiles": pl.String,
    "qsar_smiles": pl.String,
    "property_description": pl.String,
    "provider_experimental_value": pl.Float64,
    "provider_experimental_text": pl.String,
    "provider_error": pl.String,
    "source_record_json": pl.String,
    "model_name": pl.String,
    "model_id": pl.Int64,
    "endpoint": pl.String,
    "predicted_value": pl.Float64,
    "predicted_value_text": pl.String,
    "predicted_unit": pl.String,
    "ad_method": pl.String,
    "ad_value": pl.Float64,
    "ad_conclusion": pl.String,
    "ad_reasoning": pl.String,
    "has_qmrf": pl.Boolean,
    "qmrf_url": pl.String,
    "evidence_class": pl.String,
    "retrieved_at": pl.String,
}

EPA_TEST_COVERAGE_SCHEMA = {
    "compound_id": pl.String,
    "dtxsid": pl.String,
    "predictions": pl.Int64,
    "models": pl.Int64,
    "outside_applicability_domain": pl.Int64,
}


def compound_table(rows: Iterable[Compound]) -> pl.DataFrame:
    """Construct a typed compound table, including empty and all-null columns."""
    return frame_from_rows(rows, COMPOUND_SCHEMA)


def annotation_table(rows: Iterable[Annotation]) -> pl.DataFrame:
    """Construct typed annotation tables with structured source provenance."""
    return frame_from_rows(rows, ANNOTATION_SCHEMA)


def frame_from_rows(
    rows: Iterable[Mapping[str, Any]], schema: TableSchema
) -> pl.DataFrame:
    """Build rows against an explicit schema without permissive null-producing casts."""
    return pl.DataFrame(list(rows), schema = schema, strict = True)


def read_table(path: Path, schema: TableSchema | None = None) -> pl.DataFrame:
    """Read native Parquet; missing/corrupt files raise, typed empty files are valid.

    If a schema is supplied, require its exact columns, order, and dtypes.
    No casts, column selection, or missing-file substitutions are performed.
    """
    frame = pl.read_parquet(path)
    if schema is not None and list(frame.schema.items()) != list(pl.Schema(schema).items()):
        raise ValueError(f"Table schema mismatch in {path}: expected {schema}, got {frame.schema}")
    return frame
