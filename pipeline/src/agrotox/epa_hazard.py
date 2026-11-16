"""EPA experimental hazard observations, mapped for the existing comparisons."""

import hashlib
import json
import math
import re
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl

from .endpoints import ENDPOINT_UNITS, POINT_OF_DEPARTURE_UNITS
from .storage import epa_hazard_path, write_json
from .tables import (
    COMPARISON_INPUT_SCHEMA,
    EPA_HAZARD_COVERAGE_SCHEMA,
    EPA_HAZARD_SCHEMA,
    NORMALIZED_ANNOTATION_SCHEMA,
    STUDY_CONTEXT_SCHEMA,
    frame_from_rows,
)
from .units import duration_hours, normalize_unit

# The source's organism categories are mapped to the pipeline's vocabulary.
# An unmapped category stays null, and the original text is kept.
# The source names its organism categories in the plural, and a single value may
# arrive with either form, so both are accepted. An unmapped category stays
# null and the original text is kept in the hazard table.
ORGANISM_GROUPS = {
    "mammal": "mammal", "mammals": "mammal",
    "fish": "fish", "fishes": "fish",
    "aquatic invertebrate": "aquatic_invertebrate",
    "aquatic invertebrates": "aquatic_invertebrate",
    "algae": "algae", "algae ": "algae",
    "plant": "plant", "plants": "plant",
    "bird": "bird", "birds": "bird",
    "amphibian": "amphibian", "amphibians": "amphibian",
    "reptile": "reptile", "reptiles": "reptile",
    "invertebrate": "invertebrate", "invertebrates": "invertebrate",
}
# The source marks a record as experimental, as not experimental, or as
# undetermined. Only the first is a measured observation.
EXPERIMENTAL = "experimental"
# Retain the adapter's existing endpoint set, derived from the shared policy.
SUPPORTED_ENDPOINTS = {*ENDPOINT_UNITS, *POINT_OF_DEPARTURE_UNITS}


def _duration_hours(value: float | None, unit: str | None) -> float | None:
    """Return the duration in hours, or unknown when the source has no duration.

    The source uses a negative sentinel and a placeholder unit for a missing
    duration, and it may report a unit the pipeline does not convert. None of
    those is an error: the duration is simply unknown.
    """
    if value is None or value <= 0:
        return None
    if unit is None or not unit.strip() or unit.strip() == "-":
        return None
    try:
        return duration_hours(value, unit)
    except (TypeError, ValueError):
        return None


def _text(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def parse_toxval(
    records: Iterable[Mapping[str, Any]], compound_id: str, retrieved_at: str,
) -> list[dict[str, Any]]:
    """Read the hazard observations of one substance into typed evidence.

    Every field comes from the record itself, including whether the record is
    experimental or predicted. A record whose value cannot be read is kept with
    a null value rather than being dropped or turned into zero.
    """
    rows: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, Mapping):
            raise TypeError("A hazard record must be a mapping")
        rows.append({
            "source_record_json": json.dumps(record, sort_keys = True, ensure_ascii = False),
            "compound_id": compound_id,
            "dtxsid": _text(record.get("dtxsid")),
            "toxval_type": _text(record.get("toxvalType")),
            "toxval_type_definition": _text(record.get("toxvalTypeDefinition")),
            "human_eco": _text(record.get("humanEco")),
            "source": _text(record.get("source")),
            "subsource": _text(record.get("subsource")),
            "qualifier": _text(record.get("qualifier")),
            "value_numeric": _number(record.get("toxvalNumeric")),
            "value_units": _text(record.get("toxvalUnits")),
            "value_numeric_original": _number(record.get("toxvalNumericOriginal")),
            "value_units_original": _text(record.get("toxvalUnitsOriginal")),
            "species_common": _text(record.get("speciesCommon")),
            "latin_name": _text(record.get("latinName")),
            "species_supercategory": _text(record.get("speciesSupercategory")),
            "exposure_route": _text(record.get("exposureRoute")),
            "exposure_method": _text(record.get("exposureMethod")),
            "exposure_form": _text(record.get("exposureForm")),
            "media": _text(record.get("media")),
            "strain": _text(record.get("strain")),
            "sex": _text(record.get("sex")),
            "lifestage": _text(record.get("lifestage")),
            "study_type": _text(record.get("studyType")),
            "study_duration_value": _number(record.get("studyDurationValue")),
            "study_duration_units": _text(record.get("studyDurationUnits")),
            "study_duration_class": _text(record.get("studyDurationClass")),
            "toxicological_effect": _text(record.get("toxicologicalEffect")),
            "experimental_record": _text(record.get("experimentalRecord")),
            "quality": _text(record.get("quality")),
            "qc_category": _text(record.get("qcCategory")),
            "guideline": _text(record.get("guideline")),
            "reference": _text(record.get("longRef")),
            "doi": _text(record.get("doi")),
            "title": _text(record.get("title")),
            "author": _text(record.get("author")),
            "year": _text(record.get("year")),
            "source_url": _text(record.get("sourceUrl")),
            "external_source_id": _text(record.get("externalSourceId")),
            "source_hash": _text(record.get("sourceHash")),
            "retrieved_at": retrieved_at,
        })
    return rows


def hazard_table(rows: Iterable[Mapping[str, Any]]) -> pl.DataFrame:
    """Return the typed hazard evidence table."""
    return frame_from_rows(list(rows), EPA_HAZARD_SCHEMA)


def hazard_coverage(hazards: pl.DataFrame) -> pl.DataFrame:
    """Summarize the hazard evidence available for each compound."""
    if hazards.is_empty():
        return frame_from_rows([], EPA_HAZARD_COVERAGE_SCHEMA)
    return (
        hazards.group_by("compound_id", "dtxsid", maintain_order = True)
        .agg(
            pl.len().cast(pl.Int64).alias("records"),
            (pl.col("experimental_record") == EXPERIMENTAL).sum().cast(pl.Int64)
            .alias("experimental_records"),
            pl.col("toxval_type").drop_nulls().n_unique().cast(pl.Int64)
            .alias("distinct_endpoints"),
            pl.col("latin_name").drop_nulls().n_unique().cast(pl.Int64)
            .alias("distinct_species"),
            pl.col("reference").drop_nulls().n_unique().cast(pl.Int64)
            .alias("distinct_references"),
        )
        .select(*EPA_HAZARD_COVERAGE_SCHEMA)
        .sort("compound_id")
    )


def _context_text(value: str | None) -> str | None:
    """Normalize source context without treating placeholders as known values."""
    text = (value or "").strip().casefold()
    return None if text in {"", "-", "nr", "not specified", "unknown"} else text


def normalize_hazards(hazards: pl.DataFrame) -> pl.DataFrame:
    """Normalize every hazard row, retaining excluded evidence for review.

    Study and benchmark metadata absent from the source stays null. BMD/BMDL
    parenthetical numbers are response tokens, without an inferred risk scale.
    """
    rows = []
    for record in hazards.iter_rows(named = True):
        source_json = record.get("source_record_json") or json.dumps(
            {key: value for key, value in record.items()
             if key not in {"retrieved_at", "source_record_json"}},
            sort_keys = True, ensure_ascii = False,
        )
        identity = record["compound_id"] + ":" + source_json
        label = (record["toxval_type"] or "").strip()
        benchmark = re.fullmatch(r"(BMDL|BMD)(?:\s*\((\d+(?:\.\d+)?)\))?", label)
        endpoint = benchmark[1] if benchmark else label if label in SUPPORTED_ENDPOINTS else None
        value = record["value_numeric"]
        qualifier = record["qualifier"] or "="
        unit, factor = normalize_unit(record["value_units"], endpoint, record["media"])
        notes = []
        if endpoint is None:
            notes.append("unsupported endpoint")
        if record["experimental_record"] != EXPERIMENTAL:
            notes.append("record is not explicitly experimental")
        if value is None or not math.isfinite(value) or value <= 0:
            notes.append("no positive finite numeric result")
        if factor is None:
            notes.append("unsupported or incompatible unit/medium")
        converted = value * factor if value is not None and factor is not None else None
        if converted is not None and (not math.isfinite(converted) or converted <= 0):
            notes.append("converted value is nonpositive or nonfinite")
            converted = None
        if qualifier not in {"=", "<", ">", "<=", ">="}:
            notes.append("unsupported qualifier")
        formulation = re.search(
            r"\b(?:mixtures?|formulations?|formulated|extracts?)\b",
            record["exposure_form"] or "", re.IGNORECASE,
        ) is not None
        if formulation:
            notes.append("formulation or mixture context")
        raw_value = f"{qualifier} {value} {record['value_units'] or ''}".strip()
        row = dict.fromkeys(NORMALIZED_ANNOTATION_SCHEMA)
        row.update({
            **dict.fromkeys(STUDY_CONTEXT_SCHEMA),
            "annotation_id": "EPA:" + hashlib.sha256(identity.encode()).hexdigest(),
            "compound_id": record["compound_id"], "record_title": record["title"],
            "section_path": ["EPA CompTox", "Hazard"],
            "information_name": record["toxval_type"],
            "description": record["toxval_type_definition"],
            "value_raw": raw_value, "value_kind": "Number", "reference_numbers": [1],
            "sources": [{"reference_number": 1, "source_name": record["source"],
                         "source_url": record["source_url"], "reference_json": source_json}],
            "information_url": record["source_url"], "information_json": source_json,
            "retrieved_at": record["retrieved_at"], "endpoint": endpoint,
            "species": _context_text(record["latin_name"]) or _context_text(record["species_common"]),
            "organism_group": ORGANISM_GROUPS.get(
                (record["species_supercategory"] or "").strip().casefold(),
            ),
            "exposure_route": _context_text(record["exposure_route"]),
            "medium": _context_text(record["media"]),
            "duration_value": record["study_duration_value"],
            "duration_unit": record["study_duration_units"],
            "duration_hours": _duration_hours(
                record["study_duration_value"], record["study_duration_units"],
            ),
            "study_type": _context_text(record["study_type"]),
            "duration_class": _context_text(record["study_duration_class"]),
            "effect": _context_text(record["toxicological_effect"]),
            "evidence_basis": "model_derived" if endpoint in {"BMD", "BMDL"} else
            "observed" if record["experimental_record"] == EXPERIMENTAL else None,
            "benchmark_response": benchmark[2] if benchmark else None,
            "qualifier": qualifier, "value_numeric": value,
            "unit_raw": record["value_units"], "unit_standardized": unit,
            "value_standardized": converted, "formulation_flag": formulation,
            "parse_status": "failed" if endpoint is None else "partial" if notes else "complete",
            "parse_note": "; ".join(notes),
        })
        rows.append(row)
    return frame_from_rows(rows, NORMALIZED_ANNOTATION_SCHEMA)


def as_comparison_input(hazards: pl.DataFrame) -> pl.DataFrame:
    """Return complete normalized experimental hazard rows for coverage.

    All other records remain inspectable through normalize_hazards, including
    unsupported units/endpoints and uncertain source experimental status.
    """
    return normalize_hazards(hazards).filter(
        (pl.col("parse_status") == "complete") & ~pl.col("formulation_flag"),
    ).select(*COMPARISON_INPUT_SCHEMA)


def _read_cached(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding = "utf-8")).get("response")


def fetch_hazard(
    root: Path, crosswalk: pl.DataFrame, client: Any,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Retrieve the hazard evidence of every approved compound, reusing the cache.

    Only an approved DTXSID is requested. The returned tables are the hazard
    evidence, its coverage, and the comparison input the existing rules can use.
    """
    rows: list[dict[str, Any]] = []
    approved = crosswalk.filter(pl.col("status") == "approved")
    for entry in approved.iter_rows(named = True):
        dtxsid = entry["dtxsid"]
        path = epa_hazard_path(root, dtxsid)
        cached = _read_cached(path)
        if cached is None:
            cached = client.hazard(dtxsid)
            write_json(path, {
                "dtxsid": dtxsid,
                "provider": "EPA CompTox",
                "retrieved_at": datetime.now(UTC).isoformat(),
                "url": f"/hazard/toxval/search/by-dtxsid/{dtxsid}",
                "status": 200,
                "response": cached,
            })
        retrieved_at = json.loads(path.read_text(encoding = "utf-8"))["retrieved_at"]
        rows.extend(parse_toxval(cached, entry["compound_id"], retrieved_at))
    hazards = hazard_table(rows)
    return hazards, hazard_coverage(hazards), as_comparison_input(hazards)
