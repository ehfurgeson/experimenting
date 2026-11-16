"""EPA chemical properties, with measured and calculated values kept apart."""

import json
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl

from .storage import epa_property_path, write_json
from .tables import EPA_PROPERTY_COVERAGE_SCHEMA, EPA_PROPERTY_SCHEMA, frame_from_rows

MEASURED = "measured"
CALCULATED = "calculated"
UNKNOWN = "unknown"


def _text(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def parse_properties(
    records: Iterable[Mapping[str, Any]], compound_id: str, origin: str,
    retrieved_at: str,
) -> list[dict[str, Any]]:
    """Read the property records of one substance into long-form rows.

    The origin comes from the endpoint the record came from: the experimental
    property endpoint holds measured values and the predicted property endpoint
    holds calculated ones. The endpoint is kept in the row, so the basis of
    every value is visible.
    """
    rows: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, Mapping):
            raise TypeError("A property record must be a mapping")
        rows.append({
            "compound_id": compound_id,
            "dtxsid": _text(record.get("dtxsid")),
            "property_name": _text(record.get("propName")),
            "property_value": _number(record.get("propValue")),
            "property_value_text": (
                _text(record.get("propValueString")) or _text(record.get("propValueText"))
            ),
            "property_unit": _text(record.get("propUnit")),
            "property_origin": origin,
            "source_endpoint": origin,
            "source_name": _text(record.get("sourceName")),
            "source_description": _text(record.get("sourceDescription")),
            "public_source_url": _text(record.get("publicSourceUrl")),
            "dataset": _text(record.get("dataset")),
            "model_name": _text(record.get("modelName")),
            "model_id": _number(record.get("modelId")),
            "property_category": _text(record.get("propCategory")),
            "property_description": _text(record.get("propDescription")),
            "ad_method": _text(record.get("adMethod")),
            "ad_value": _number(record.get("adValue")),
            "ad_conclusion": _text(record.get("adConclusion")),
            "ad_reasoning": _text(record.get("adReasoning")),
            "retrieved_at": retrieved_at,
        })
    return rows


def property_table(rows: Iterable[Mapping[str, Any]]) -> pl.DataFrame:
    """Return the long-form property table."""
    return frame_from_rows(list(rows), EPA_PROPERTY_SCHEMA)


def property_coverage(properties: pl.DataFrame) -> pl.DataFrame:
    """Summarize the properties available for each compound."""
    if properties.is_empty():
        return frame_from_rows([], EPA_PROPERTY_COVERAGE_SCHEMA)
    return (
        properties.group_by("compound_id", "dtxsid", maintain_order = True)
        .agg(
            pl.len().cast(pl.Int64).alias("properties"),
            (pl.col("property_origin") == MEASURED).sum().cast(pl.Int64)
            .alias("measured_properties"),
            (pl.col("property_origin") == CALCULATED).sum().cast(pl.Int64)
            .alias("calculated_properties"),
            pl.col("source_name").drop_nulls().n_unique().cast(pl.Int64)
            .alias("distinct_sources"),
        )
        .select(*EPA_PROPERTY_COVERAGE_SCHEMA)
        .sort("compound_id")
    )


def _read_cached(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding = "utf-8")).get("response")


def _store(path: Path, kind: str, dtxsid: str, response: list[dict[str, Any]]) -> str:
    retrieved_at = datetime.now(UTC).isoformat()
    write_json(path, {
        "dtxsid": dtxsid,
        "provider": "EPA CompTox",
        "property_kind": kind,
        "retrieved_at": retrieved_at,
        "url": f"/chemical/property/{kind}/search/by-dtxsid/{dtxsid}",
        "status": 200,
        "response": response,
    })
    return retrieved_at


def fetch_properties(
    root: Path, crosswalk: pl.DataFrame, client: Any,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Retrieve the property records of every approved compound.

    The experimental and the predicted responses are cached separately, so a
    rerun makes no request for a response that was already retrieved. The
    PubChem property values are not touched: both sources are kept, each with
    its own row.
    """
    rows: list[dict[str, Any]] = []
    approved = crosswalk.filter(pl.col("status") == "approved")
    for entry in approved.iter_rows(named = True):
        dtxsid = entry["dtxsid"]
        for kind, origin, method in [
            ("experimental", MEASURED, "property_experimental"),
            ("predicted", CALCULATED, "property_predicted"),
        ]:
            path = epa_property_path(root, kind, dtxsid)
            cached = _read_cached(path)
            if cached is None:
                cached = getattr(client, method)(dtxsid)
                _store(path, kind, dtxsid, cached)
            retrieved_at = json.loads(path.read_text(encoding = "utf-8"))["retrieved_at"]
            rows.extend(parse_properties(cached, entry["compound_id"], origin, retrieved_at))
    properties = property_table(rows)
    return properties, property_coverage(properties)
