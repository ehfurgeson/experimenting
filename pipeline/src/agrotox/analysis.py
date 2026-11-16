"""Consolidation of comparable measurements into reviewable comparison records."""

from collections.abc import Mapping

import polars as pl

from .coverage import matching_expr, validate_definitions
from .endpoints import POINT_OF_DEPARTURE_UNITS
from .tables import (
    AUDIT_SCHEMA,
    COMPARISON_RECORD_SCHEMA,
    COMPOUND_SUMMARY_SCHEMA,
    GROUP_SUMMARY_SCHEMA,
    REVIEW_QUEUE_SCHEMA,
    STUDY_CONTEXT_SCHEMA,
    frame_from_rows,
)

# The consolidation key separates records that differ in comparison context or
# in the result itself. ``organism_group`` is deliberately absent: a definition
# that constrains it already fixes that value, and species, route, and duration
# carry the remaining context.
_CONSOLIDATION_FIELDS = (
    "endpoint", "species", "exposure_route", "duration_hours", "unit_standardized",
    "qualifier", "value_standardized", "value_lower_standardized", "value_upper_standardized",
    *STUDY_CONTEXT_SCHEMA,
)
_REQUIRED_COLUMNS = {
    "annotation_id", "compound_id", "preferred_name", "chemical_group", "sources",
    "value_raw", *_CONSOLIDATION_FIELDS,
}


def comparison_records(
    measurements: pl.DataFrame, definitions: Mapping[str, Mapping[str, str | float | int]],
) -> pl.DataFrame:
    """Return one record per comparable value and context, with every supporter.

    Eligibility is shared with :func:`agrotox.coverage.matching_expr`, so a
    record exists only where a configured comparison applies. Equal values from
    different sources consolidate into one record that keeps the unique support
    identifiers, the original value text, and the nested source provenance of
    every supporter. Consolidation is equal-value consolidation, not evidence of
    independent studies.
    """
    rules = validate_definitions(definitions)
    missing = _REQUIRED_COLUMNS - set(measurements.columns)
    if missing:
        raise ValueError(f"Measurements are missing required columns: {sorted(missing)}")
    if measurements["compound_id"].null_count():
        raise ValueError("Measurement identities must be nonnull")
    records: dict[tuple, dict] = {}
    order: list[tuple] = []
    for name, rule in rules.items():
        matched = measurements.filter(matching_expr(rule))
        for row in matched.iter_rows(named = True):
            key = (name, row["compound_id"], *(row[field] for field in _CONSOLIDATION_FIELDS))
            record = records.get(key)
            if record is None:
                record = {
                    "comparison": name,
                    "summary_eligible": rule.get(
                        "summary_mode", "availability" if rule["endpoint"] in POINT_OF_DEPARTURE_UNITS
                        else "potency",
                    ) == "potency",
                    "compound_id": row["compound_id"],
                    "preferred_name": row["preferred_name"],
                    "chemical_group": row["chemical_group"],
                    **{field: row[field] for field in _CONSOLIDATION_FIELDS},
                    "support_ids": [],
                    "supports": [],
                }
                records[key] = record
                order.append(key)
            annotation_id = row["annotation_id"]
            if annotation_id not in record["support_ids"]:
                record["support_ids"].append(annotation_id)
            for source in row["sources"] or []:
                support = {
                    "annotation_id": annotation_id,
                    "value_raw": row["value_raw"],
                    "reference_number": source["reference_number"],
                    "source_name": source["source_name"],
                    "source_url": source["source_url"],
                    "reference_json": source["reference_json"],
                }
                if support not in record["supports"]:
                    record["supports"].append(support)
    rows = []
    for key in order:
        record = records[key]
        record["support_ids"] = sorted(record["support_ids"])
        record["supports"] = sorted(
            record["supports"], key = lambda support: (
                support["annotation_id"], support["reference_number"] or 0,
            ),
        )
        record["support_count"] = len(record["support_ids"])
        rows.append(record)
    # A deterministic order keeps the same inputs mapped to the same rows:
    # definition order first, then the consolidation fields.
    order_of = {name: position for position, name in enumerate(rules)}
    rows.sort(key = lambda record: (
        order_of[record["comparison"]], record["compound_id"],
        *[(record[field] is None, record[field]) for field in _CONSOLIDATION_FIELDS],
    ))
    return frame_from_rows(rows, COMPARISON_RECORD_SCHEMA)


def compound_summaries(records: pl.DataFrame) -> pl.DataFrame:
    """Summarize each compound's consolidated records for one comparison.

    Exact medians use the unique consolidated exact results only. Thresholds and
    ranges are counted separately and never enter the median. A compound with
    many studies contributes one summary row.
    """
    if records.is_empty():
        return frame_from_rows([], COMPOUND_SUMMARY_SCHEMA)
    exact = pl.col("value_standardized").filter(
        (pl.col("qualifier") == "=") & pl.col("value_standardized").is_not_null()
    )
    summarizable = pl.col("value_standardized").filter(
        (pl.col("qualifier") == "=") & pl.col("value_standardized").is_not_null()
        & pl.col("summary_eligible")
    )
    return (
        records.group_by("comparison", "compound_id", maintain_order = True)
        .agg(
            pl.col("preferred_name").first(),
            pl.col("chemical_group").first(),
            pl.len().cast(pl.Int64).alias("n_records"),
            exact.len().cast(pl.Int64).alias("n_exact"),
            pl.col("qualifier").is_in(["<", ">", "<=", ">="]).sum().cast(pl.Int64)
            .alias("n_censored"),
            (pl.col("qualifier") == "range").sum().cast(pl.Int64).alias("n_ranges"),
            summarizable.median().alias("exact_median"),
            summarizable.min().alias("exact_min"),
            summarizable.max().alias("exact_max"),
        )
        .select(*COMPOUND_SUMMARY_SCHEMA)
        .sort("comparison", "compound_id")
    )


def group_summaries(
    summaries: pl.DataFrame, compounds: pl.DataFrame,
    definitions: Mapping[str, Mapping[str, str | float | int]],
) -> pl.DataFrame:
    """Describe each comparison and chemical group from equally weighted compounds.

    Every observed chemical group appears for every comparison, including groups
    with no matching evidence and groups that were not anticipated. The group
    median is the median of compound medians, so a heavily studied compound
    cannot dominate the group description.
    """
    rules = validate_definitions(definitions)
    identity = compounds.select("compound_id", "chemical_group")
    if identity["compound_id"].null_count():
        raise ValueError("Compound identities must be nonnull")
    conflicting = identity.group_by("compound_id").agg(
        pl.col("chemical_group").n_unique().alias("groups")
    )
    if (conflicting["groups"].max() or 0) > 1:
        raise ValueError("Compound rows contain conflicting duplicate identities")
    universe = identity.unique(subset = ["compound_id"], keep = "first", maintain_order = True)
    totals = universe.group_by("chemical_group", maintain_order = True).agg(
        pl.len().cast(pl.Int64).alias("total_compounds")
    )
    group_values = totals["chemical_group"].to_list()
    grid = pl.DataFrame({
        "comparison": [name for name in rules for _ in group_values],
        "chemical_group": [group for _ in rules for group in group_values],
    }, schema = {"comparison": pl.String, "chemical_group": pl.String})
    if summaries.is_empty():
        aggregates = frame_from_rows([], {
            key: dtype for key, dtype in GROUP_SUMMARY_SCHEMA.items()
            if key not in {"total_compounds"}
        })
    else:
        aggregates = summaries.group_by("comparison", "chemical_group", maintain_order = True).agg(
            pl.len().cast(pl.Int64).alias("compounds_with_data"),
            (pl.col("n_exact") > 0).sum().cast(pl.Int64).alias("compounds_with_exact"),
            (pl.col("n_censored") > 0).sum().cast(pl.Int64).alias("compounds_with_censoring"),
            (pl.col("n_ranges") > 0).sum().cast(pl.Int64).alias("compounds_with_ranges"),
            pl.col("exact_median").median().alias("median_of_compound_exact_medians"),
            pl.col("exact_median").min().alias("min_compound_exact_median"),
            pl.col("exact_median").max().alias("max_compound_exact_median"),
        )
    return (
        grid.join(totals, on = "chemical_group", how = "left", maintain_order = "left",
                  nulls_equal = True)
        .join(aggregates, on = ["comparison", "chemical_group"], how = "left",
              maintain_order = "left", nulls_equal = True)
        .with_columns(pl.col([
            "total_compounds", "compounds_with_data", "compounds_with_exact",
            "compounds_with_censoring", "compounds_with_ranges",
        ]).fill_null(0))
        .select(*GROUP_SUMMARY_SCHEMA)
    )


def comparison_tables(
    compounds: pl.DataFrame, measurements: pl.DataFrame,
    definitions: Mapping[str, Mapping[str, str | float | int]],
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Return comparison records, compound summaries, and group summaries."""
    records = comparison_records(measurements, definitions)
    summaries = compound_summaries(records)
    return records, summaries, group_summaries(summaries, compounds, definitions)


def extraction_audit(
    compounds: pl.DataFrame, annotations: pl.DataFrame, measurements: pl.DataFrame,
    records: pl.DataFrame,
) -> pl.DataFrame:
    """Explain, for every selected compound, why comparable data is or is not there.

    The reasons are applied in a fixed order, so the first applicable state
    explains the compound. The states describe PubChem retrieval: an unresolved
    query, an unfinished or failed toxicity request, an absent toxicity section,
    an empty saved section, no supported complete measurement, complete
    measurements outside every comparison context, and comparable data.
    """
    rows = []
    selected = compounds.unique(subset = ["compound_id"], keep = "first", maintain_order = True)
    for compound in selected.iter_rows(named = True):
        compound_id = compound["compound_id"]
        subset = measurements.filter(pl.col("compound_id") == compound_id)
        annotation_count = annotations.filter(pl.col("compound_id") == compound_id).height
        complete = subset.filter(pl.col("parse_status") == "complete").height
        partial = subset.filter(pl.col("parse_status") == "partial").height
        failed = subset.filter(pl.col("parse_status") == "failed").height
        comparable = records.filter(pl.col("compound_id") == compound_id).height
        status = compound["toxicity_status"]
        if compound["resolution_status"] != "resolved":
            reason = "unresolved_query"
        elif status in {"pending", "not_retrieved"}:
            reason = "toxicity_request_failed_or_pending"
        elif status == "missing":
            reason = "toxicity_section_missing"
        elif not annotation_count:
            reason = "no_annotations_in_saved_section"
        elif not complete:
            reason = "annotations_present_no_supported_complete_measurement"
        elif not comparable:
            reason = "complete_measurements_outside_comparison_contexts"
        else:
            reason = "comparison_data_available"
        rows.append({
            "compound_id": compound_id,
            "preferred_name": compound["preferred_name"],
            "chemical_group": compound["chemical_group"],
            "resolution_status": compound["resolution_status"],
            "toxicity_status": status,
            "annotations": annotation_count,
            "complete": complete,
            "partial": partial,
            "failed": failed,
            "comparison_records": comparable,
            "availability_reason": reason,
        })
    return frame_from_rows(rows, AUDIT_SCHEMA)


def review_queue(measurements: pl.DataFrame) -> pl.DataFrame:
    """Return the partial and failed measurement rows that need human review.

    Each row keeps its parse note and its full source provenance, so a reviewer
    can read the original evidence beside the reason extraction did not succeed.
    """
    if measurements.is_empty():
        return frame_from_rows([], REVIEW_QUEUE_SCHEMA)
    queue = measurements.filter(pl.col("parse_status").is_in(["partial", "failed"]))
    return queue.select(*REVIEW_QUEUE_SCHEMA)
