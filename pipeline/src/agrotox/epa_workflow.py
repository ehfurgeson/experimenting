"""Offline analysis of selected approved EPA hazard caches."""

import json
from pathlib import Path

import polars as pl

from .analysis import comparison_tables, review_queue
from .contracts import Query
from .coverage import coverage_tables, validate_definitions
from .epa_hazard import hazard_table, normalize_hazards, parse_toxval
from .identity import reconcile_compounds
from .storage import epa_hazard_path
from .tables import (
    ANNOTATION_SCHEMA,
    COMPOUND_CONTEXT_SCHEMA,
    EPA_HAZARD_AUDIT_SCHEMA,
    EPA_IDENTITY_CROSSWALK_SCHEMA,
    compound_table,
    frame_from_rows,
    read_table,
)
from .workflow import Definitions, OfflineAnalysis, _hash_paths, _selected_evidence


def build_epa_hazard_offline(
    root: Path, queries: list[Query], definitions: Definitions,
) -> OfflineAnalysis:
    """Build EPA hazard analysis tables without requests or cache mutations.

    Selected compounds retain their denominator even without an approved EPA
    identity. Every selected approved identity requires a valid saved hazard
    response; missing evidence raises instead of becoming zero coverage.
    """
    rules = validate_definitions(definitions)
    selected, snapshots, _by_cid, consumed = _selected_evidence(root, queries)
    compounds = compound_table(reconcile_compounds(selected, snapshots))
    crosswalk_path = root / "epa_identity_crosswalk.parquet"
    crosswalk = read_table(crosswalk_path, EPA_IDENTITY_CROSSWALK_SCHEMA).filter(
        pl.col("compound_id").is_in(compounds["compound_id"].implode()),
    )
    consumed.append(crosswalk_path)
    if crosswalk["compound_id"].is_duplicated().any():
        raise ValueError("EPA crosswalk contains duplicate selected compound identities")
    entries = {row["compound_id"]: row for row in crosswalk.iter_rows(named = True)}
    rows = []
    raw_paths = {}
    for entry in crosswalk.filter(pl.col("status") == "approved").iter_rows(named = True):
        dtxsid = entry["dtxsid"]
        path = epa_hazard_path(root, dtxsid)
        payload = json.loads(path.read_text(encoding = "utf-8"))
        if (not isinstance(payload, dict) or payload.get("dtxsid") != dtxsid
                or payload.get("status") != 200 or not isinstance(payload.get("response"), list)
                or not isinstance(payload.get("retrieved_at"), str) or not payload["retrieved_at"]):
            raise ValueError(f"Invalid selected EPA hazard cache: {path}")
        records = payload["response"]
        if any(not isinstance(record, dict) or record.get("dtxsid") not in (None, dtxsid)
               for record in records):
            raise ValueError(f"Mismatched record in selected EPA hazard cache: {path}")
        rows.extend(parse_toxval(records, entry["compound_id"], payload["retrieved_at"]))
        raw_paths[entry["compound_id"]] = str(path)
        consumed.append(path)
    hazards = hazard_table(rows)
    normalized = normalize_hazards(hazards).with_columns(
        pl.col("compound_id").replace_strict(
            raw_paths, default = None, return_dtype = pl.String,
        ).alias("raw_file"),
    )
    measurements = normalized.join(
        compounds.select("compound_id", *COMPOUND_CONTEXT_SCHEMA), on = "compound_id",
        how = "left", validate = "m:1", maintain_order = "left",
    )
    coverage, coverage_by_group = coverage_tables(compounds, measurements, rules)
    records, summaries, groups = comparison_tables(compounds, measurements, rules)
    audit_rows = []
    for compound in compounds.iter_rows(named = True):
        compound_id = compound["compound_id"]
        entry = entries.get(compound_id)
        subset = measurements.filter(pl.col("compound_id") == compound_id)
        counts = {status: subset.filter(pl.col("parse_status") == status).height
                  for status in ("complete", "partial", "failed")}
        comparable = records.filter(pl.col("compound_id") == compound_id).height
        if entry is None:
            reason = "identity_not_in_crosswalk"
        elif entry["status"] != "approved":
            reason = "identity_not_approved"
        elif subset.is_empty():
            reason = "no_hazard_records_in_saved_response"
        elif not counts["complete"]:
            reason = "no_supported_complete_measurement"
        elif not comparable:
            reason = "complete_measurements_outside_comparison_contexts"
        else:
            reason = "comparison_data_available"
        audit_rows.append({
            "compound_id": compound_id,
            "dtxsid": entry["dtxsid"] if entry else None,
            "epa_identity_status": entry["status"] if entry else None,
            "records": subset.height, **counts, "comparison_records": comparable,
            "availability_reason": reason,
        })
    tables = {
        "compounds": compounds, "hazards": hazards,
        "annotations": normalized.select(*ANNOTATION_SCHEMA),
        "measurements": measurements, "coverage": coverage,
        "coverage_by_group": coverage_by_group, "comparison_records": records,
        "compound_summary": summaries, "group_summary": groups,
        "audit": frame_from_rows(audit_rows, EPA_HAZARD_AUDIT_SCHEMA),
        "review_queue": review_queue(measurements),
    }
    return OfflineAnalysis(tables = tables, dependencies = _hash_paths(consumed))
