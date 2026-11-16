"""ToxCast in-vitro bioactivity evidence, kept separate from acute toxicity."""

import json
import math
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl

from .storage import epa_assay_path, epa_bioactivity_path, write_json
from .tables import TOXCAST_ASSAY_SCHEMA, TOXCAST_COVERAGE_SCHEMA, frame_from_rows

# The bioactivity API does not report the invitrodb release it serves, so the
# source is named explicitly instead of implying a pinned release.
SOURCE_RELEASE = "comptox-bioactivity-api"
EXPERIMENTAL = "experimental"
ASSAY_FIT = "assay_fit"
INACTIVE = "inactive"
# A hit call of exactly zero is neither an active nor an inactive curve.

_ASSAY_FIELDS = {
    "aeid": "aeid",
    "aid": "aid",
    "assayComponentEndpointName": "assay_component_endpoint_name",
    "assayFunctionType": "assay_function_type",
    "intendedTargetType": "intended_target_type",
    "intendedTargetFamily": "intended_target_family",
    "biologicalProcessTarget": "biological_process_target",
    "detectionTechnology": "detection_technology",
    "assayFormatType": "assay_format_type",
    "organism": "organism",
    "taxonName": "taxon_name",
    "tissue": "tissue",
    "cellFormat": "cell_format",
    "timepointHr": "timepoint_hours",
}
_DATA_FIELDS = {
    "hitc": "hit_call",
    "actp": "activity_value",
    "bmad": "benchmark_dose",
    "concMin": "concentration_min",
    "concMax": "concentration_max",
    "testedConcUnit": "concentration_unit",
    "respMin": "response_min",
    "respMax": "response_max",
    "modl": "model",
    "modelType": "model_type",
    "fitc": "fit_category",
    "nconc": "n_concentrations",
    "nrep": "n_replicates",
    "npts": "n_points",
}


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) else None


def _integer(value: Any) -> int | None:
    number = _number(value)
    return int(number) if number is not None else None


def _text(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def parse_assay_annotation(annotation: Mapping[str, Any]) -> dict[str, Any]:
    """Read the assay endpoint annotation into the fields the evidence needs."""
    parsed: dict[str, Any] = {}
    for source, target in _ASSAY_FIELDS.items():
        value = annotation.get(source)
        if target in {"aeid", "aid"}:
            parsed[target] = _integer(value)
        elif target == "timepoint_hours":
            parsed[target] = _number(value)
        else:
            parsed[target] = _text(value)
    return parsed


def parse_bioactivity(
    records: Iterable[Mapping[str, Any]], compound_id: str, dtxsid: str,
    annotations: Mapping[int, Mapping[str, Any]], retrieved_at: str,
) -> list[dict[str, Any]]:
    """Read the bioactivity records of one substance into typed assay evidence.

    A record describes one tested chemical and assay endpoint. An inactive
    result keeps its row and is marked as inactive, so it is never confused
    with a substance that was never tested in that assay.
    """
    rows: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, Mapping):
            raise TypeError("A bioactivity record must be a mapping")
        aeid = _integer(record.get("aeid"))
        annotation = annotations.get(aeid, {}) if aeid is not None else {}
        row: dict[str, Any] = {
            "compound_id": compound_id,
            "dtxsid": dtxsid,
            **parse_assay_annotation(annotation),
        }
        # The record identifies its own assay endpoint; the annotation only
        # describes it.
        row["aeid"] = aeid
        if record.get("aid") is not None:
            row["aid"] = _integer(record.get("aid"))
        for source, target in _DATA_FIELDS.items():
            value = record.get(source)
            if target in {"fit_category", "n_concentrations", "n_points", "model_type"}:
                row[target] = _integer(value)
            elif target in {"n_replicates"}:
                row[target] = _number(value)
            elif target in {"model", "concentration_unit"}:
                row[target] = _text(value)
            else:
                row[target] = _number(value)
        hit_call = row.get("hit_call")
        # The hit call is a continuous value: a positive call is an active
        # curve, a negative call is an inactive one, and a call of exactly zero
        # is neither.
        row["measurement_kind"] = (
            INACTIVE if hit_call is not None and hit_call < 0 else ASSAY_FIT
        )
        row["evidence_class"] = EXPERIMENTAL
        row["source_release"] = SOURCE_RELEASE
        row["retrieved_at"] = retrieved_at
        rows.append(row)
    return rows


def toxcast_assays(rows: Iterable[Mapping[str, Any]]) -> pl.DataFrame:
    """Return the typed assay evidence table."""
    return frame_from_rows(list(rows), TOXCAST_ASSAY_SCHEMA)


def toxcast_coverage(assays: pl.DataFrame) -> pl.DataFrame:
    """Summarize the assay evidence available for each approved compound."""
    if assays.is_empty():
        return frame_from_rows([], TOXCAST_COVERAGE_SCHEMA)
    return (
        assays.group_by("compound_id", "dtxsid", maintain_order = True)
        .agg(
            pl.col("aeid").n_unique().cast(pl.Int64).alias("assays_with_result"),
            pl.col("hit_call").gt(0).sum().cast(pl.Int64).alias("assays_with_hit"),
            pl.col("hit_call").lt(0).sum().cast(pl.Int64).alias("assays_inactive"),
            pl.col("hit_call").eq(0).sum().cast(pl.Int64).alias("assays_inconclusive"),
            pl.col("intended_target_family").drop_nulls().n_unique().cast(pl.Int64)
            .alias("distinct_targets"),
        )
        .select(*TOXCAST_COVERAGE_SCHEMA)
        .sort("compound_id")
    )


def _read_cached(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding = "utf-8")).get("response")


def fetch_toxcast(
    root: Path, crosswalk: pl.DataFrame, client: Any,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Retrieve the assay evidence of every approved compound, reusing the cache.

    Only an approved DTXSID is requested. A compound that is unresolved or
    awaiting review is not searched, because an ambiguous identity would attach
    the wrong evidence to the wrong chemical.
    """
    rows: list[dict[str, Any]] = []
    approved = crosswalk.filter(pl.col("status") == "approved")
    for entry in approved.iter_rows(named = True):
        dtxsid = entry["dtxsid"]
        path = epa_bioactivity_path(root, dtxsid)
        cached = _read_cached(path)
        if cached is None:
            cached = client.bioactivity(dtxsid)
            write_json(path, {
                "dtxsid": dtxsid,
                "provider": "EPA CompTox",
                "retrieved_at": datetime.now(UTC).isoformat(),
                "url": f"/bioactivity/data/search/by-dtxsid/{dtxsid}",
                "status": 200,
                "response": cached,
            })
        retrieved_at = json.loads(path.read_text(encoding = "utf-8"))["retrieved_at"]
        annotations = _assay_annotations(root, cached, client)
        rows.extend(parse_bioactivity(
            cached, entry["compound_id"], dtxsid, annotations, retrieved_at,
        ))
    return toxcast_assays(rows), toxcast_coverage(toxcast_assays(rows))


def _assay_annotations(
    root: Path, records: Iterable[Mapping[str, Any]], client: Any,
) -> dict[int, Mapping[str, Any]]:
    """Read or retrieve the annotation of every assay endpoint in the records."""
    annotations: dict[int, Mapping[str, Any]] = {}
    for record in records:
        aeid = _integer(record.get("aeid"))
        if aeid is None or aeid in annotations:
            continue
        path = epa_assay_path(root, aeid)
        cached = _read_cached(path)
        if cached is None:
            cached = client.assay(aeid)
            write_json(path, {
                "aeid": aeid,
                "provider": "EPA CompTox",
                "retrieved_at": datetime.now(UTC).isoformat(),
                "url": f"/bioactivity/assay/search/by-aeid/{aeid}",
                "status": 200,
                "response": cached,
            })
        if cached:
            annotations[aeid] = cached
    return annotations
