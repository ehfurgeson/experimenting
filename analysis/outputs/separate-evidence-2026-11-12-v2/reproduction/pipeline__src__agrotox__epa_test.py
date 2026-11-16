"""EPA TEST predictions, kept apart from every measured value."""

import json
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl

from .storage import epa_property_path, write_json
from .tables import EPA_TEST_COVERAGE_SCHEMA, EPA_TEST_SCHEMA, frame_from_rows

PREDICTED = "predicted"
# The source names its models; the TEST models are the ones this stage keeps.
TEST_MODEL_PREFIX = "TEST"


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


def is_test_model(model_name: str | None) -> bool:
    """Return whether a model name identifies a TEST prediction."""
    return bool(model_name) and model_name.upper().startswith(TEST_MODEL_PREFIX)


def parse_test_predictions(
    records: Iterable[Mapping[str, Any]], compound_id: str, retrieved_at: str,
) -> list[dict[str, Any]]:
    """Read the stored TEST predictions of one substance.

    Only the records the source attributes to a TEST model are kept. The
    applicability domain information is kept with the prediction, so a caller
    can distinguish provider domain strata without treating Inside as accuracy.
    """
    rows: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, Mapping):
            raise TypeError("A prediction record must be a mapping")
        model = _text(record.get("modelName"))
        if not is_test_model(model):
            continue
        rows.append({
            "compound_id": compound_id,
            "dtxsid": _text(record.get("dtxsid")),
            "provider_record_id": str(record["id"]) if record.get("id") is not None else None,
            "source_name": _text(record.get("sourceName")),
            "source_description": _text(record.get("sourceDescription")),
            "dtxcid": _text(record.get("dtxcid")),
            "smiles": _text(record.get("smiles")),
            "qsar_smiles": _text(record.get("canonQsarSmiles")),
            "property_description": _text(record.get("propDescription")),
            "provider_experimental_value": _number(record.get("propValueExperimental")),
            "provider_experimental_text": _text(record.get("propValueExperimentalString")),
            "provider_error": _text(record.get("propValueError")),
            "source_record_json": json.dumps(dict(record), sort_keys = True),
            "model_name": model,
            "model_id": _number(record.get("modelId")),
            "endpoint": _text(record.get("propName")),
            "predicted_value": _number(record.get("propValue")),
            "predicted_value_text": _text(record.get("propValueString")),
            "predicted_unit": _text(record.get("propUnit")),
            "ad_method": _text(record.get("adMethod")),
            "ad_value": _number(record.get("adValue")),
            "ad_conclusion": _text(record.get("adConclusion")),
            "ad_reasoning": _text(record.get("adReasoning")),
            "has_qmrf": record.get("hasQmrf") is True,
            "qmrf_url": _text(record.get("qmrfUrl")),
            "evidence_class": PREDICTED,
            "retrieved_at": retrieved_at,
        })
    return rows


def prediction_table(rows: Iterable[Mapping[str, Any]]) -> pl.DataFrame:
    """Return the typed prediction table."""
    return frame_from_rows(list(rows), EPA_TEST_SCHEMA)


def prediction_coverage(predictions: pl.DataFrame) -> pl.DataFrame:
    """Summarize the stored predictions available for each compound."""
    if predictions.is_empty():
        return frame_from_rows([], EPA_TEST_COVERAGE_SCHEMA)
    outside = pl.col("ad_conclusion").is_in(["Outside", "outside", "OUTSIDE"])
    return (
        predictions.group_by("compound_id", "dtxsid", maintain_order = True)
        .agg(
            pl.len().cast(pl.Int64).alias("predictions"),
            pl.col("model_name").drop_nulls().n_unique().cast(pl.Int64).alias("models"),
            outside.sum().cast(pl.Int64).alias("outside_applicability_domain"),
        )
        .select(*EPA_TEST_COVERAGE_SCHEMA)
        .sort("compound_id")
    )


def fetch_test_predictions(
    root: Path, crosswalk: pl.DataFrame, client: Any,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Read the stored TEST predictions of every approved compound.

    This stage never predicts a new molecule. It reads the predictions the
    provider has already stored for the approved identities, and reuses the
    cached predicted-property response when there is one.
    """
    rows: list[dict[str, Any]] = []
    approved = crosswalk.filter(pl.col("status") == "approved")
    for entry in approved.iter_rows(named = True):
        dtxsid = entry["dtxsid"]
        path = epa_property_path(root, "predicted", dtxsid)
        cached = None
        if path.exists():
            cached = json.loads(path.read_text(encoding = "utf-8")).get("response")
        if cached is None:
            cached = client.property_predicted(dtxsid)
            retrieved_at = datetime.now(UTC).isoformat()
            write_json(path, {
                "dtxsid": dtxsid,
                "provider": "EPA CompTox",
                "property_kind": "predicted",
                "retrieved_at": retrieved_at,
                "url": f"/chemical/property/predicted/search/by-dtxsid/{dtxsid}",
                "status": 200,
                "response": cached,
            })
        else:
            retrieved_at = json.loads(path.read_text(encoding = "utf-8"))["retrieved_at"]
        rows.extend(parse_test_predictions(cached, entry["compound_id"], retrieved_at))
    predictions = prediction_table(rows)
    return predictions, prediction_coverage(predictions)
