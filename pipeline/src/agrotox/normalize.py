"""Conservative extraction of numeric toxicity results and uncertainty."""

import math
import re
from copy import deepcopy
from typing import cast

import polars as pl

from ._context import extract_context
from .contracts import Annotation, Measurement, ParsedValue, ValueQualifier
from .tables import (
    ANNOTATION_SCHEMA,
    COMPOUND_CONTEXT_SCHEMA,
    COMPOUND_SCHEMA,
    MEASUREMENT_SCHEMA,
    NORMALIZED_ANNOTATION_SCHEMA,
    STUDY_CONTEXT_SCHEMA,
    frame_from_rows,
)
from .units import normalize_unit

NUMBER = r"(?:(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
MASS = r"(?:mg|ug|[µμ]g|g)"
UNIT = (
    rf"(?:{MASS}\s*(?:/\s*kg|kg\s*-\s*1)(?:\s+(?:bw|body\s*weight))?"
    rf"|{MASS}\s*(?:/\s*l|l\s*-\s*1)|ppm)(?![\w/^%\-])"
)
RESULT = re.compile(
    rf"(?<![\w.,/+\-−‐‑‒–—<>=≤≥])(?P<qualifier>>=|<=|≥|≤|>|<|=)?\s*"
    rf"(?P<lower>{NUMBER})(?:\s*(?:[-–—]|\bto\b)\s*(?P<upper>{NUMBER}))?"
    rf"\s*(?P<unit>{UNIT})",
    re.IGNORECASE,
)
ENDPOINT_LABEL = re.compile(r"\b(?:LD|LC|EC)\s*50\b", re.IGNORECASE)
DURATION_CONTEXT = re.compile(
    rf"(?<![\w.,]){NUMBER}\s*(?:hours?|hrs?|h|days?|d|weeks?|wks?)\b", re.IGNORECASE,
)
UNSUPPORTED_PROSE = re.compile(
    r"[~≈≃≅∼∞±]|\+\s*/\s*-|\b(?:about|approx(?:imately|imate|imation)?|around|"
    r"roughly|estimated?|circa|ca|"
    r"nan|inf(?:inity)?)\b|\b(?:less|greater|more|fewer)\s+than\b|"
    r"\b(?:at\s+(?:least|most)|up\s+to)\b",
    re.IGNORECASE,
)


def _positive_number(token: str) -> float | None:
    value = float(token.replace(",", ""))
    return value if math.isfinite(value) and value > 0 else None


def parse_value(text: str | None) -> ParsedValue | None:
    """Extract one positive finite exact value, inequality threshold, or range.

    Unsupported, approximate, malformed, and ambiguous results return None.
    Endpoint labels and explicit hour/day/week durations may accompany the result;
    other unconsumed numbers cause rejection. Preserve raw units without conversion.
    """
    if text is None:
        return None
    if not isinstance(text, str):
        raise TypeError("Toxicity result text must be a string or None")
    if UNSUPPORTED_PROSE.search(text):
        return None
    # Preserve positions so unit text still comes directly from the input.
    masked = ENDPOINT_LABEL.sub(lambda match: " " * len(match.group()), text)
    matches = list(RESULT.finditer(masked))
    if len(matches) != 1:
        return None
    match = matches[0]
    prefix = masked[:match.start()].rstrip()
    while prefix.endswith(("(", "[")):
        prefix = prefix[:-1].rstrip()
    if prefix.endswith(tuple("+-−‐‑‒–—<>=≤≥")):
        return None
    if re.search(
        r"\b(?:below|above|under|over|to|or|minus|negative|exceeds?)$", prefix, re.IGNORECASE,
    ):
        return None
    if re.match(r"\s+(?:per|bw|body\s*weight)\b", masked[match.end():], re.IGNORECASE):
        return None
    remainder = masked[:match.start()] + masked[match.end():]
    remainder = DURATION_CONTEXT.sub("", remainder)
    if any(character.isnumeric() for character in remainder) or re.search(r"[<>=≤≥]", remainder):
        return None
    lower = _positive_number(match.group("lower"))
    if lower is None:
        return None
    upper_token = match.group("upper")
    qualifier = match.group("qualifier")
    upper = _positive_number(upper_token) if upper_token is not None else None
    if upper_token is not None:
        if qualifier is not None or upper is None or upper <= lower:
            return None
        return {
            "value_numeric": None, "value_lower": lower, "value_upper": upper,
            "qualifier": "range", "unit_raw": match.group("unit"),
        }
    scalar_qualifier = cast(ValueQualifier, {"≥": ">=", "≤": "<="}.get(qualifier, qualifier or "="))
    return {
        "value_numeric": lower, "value_lower": None, "value_upper": None,
        "qualifier": scalar_qualifier,
        "unit_raw": match.group("unit"),
    }


def normalize_annotation(annotation: Annotation) -> Measurement:
    """Preserve source evidence and assign complete/partial/failed extraction status."""
    raw = annotation["value_raw"]
    text = " ".join([
        *annotation["section_path"], annotation["information_name"] or "",
        annotation["description"] or "", raw,
    ])
    labels = list(re.finditer(r"\bConcentration\s*:", raw, re.IGNORECASE))
    measured = raw
    if len(labels) == 1:
        measured = re.split(r"[;(]", raw[labels[0].end():], maxsplit = 1)[0].strip()
    context = extract_context(text, measured if len(labels) == 1 else text)
    notes = context.pop("notes")
    has_supported_endpoint = context.pop("has_supported_endpoint")
    formulation = re.search(
        r"\b(?:mixtures?|formulations?|formulated|extracts?)\b", text, re.IGNORECASE,
    ) is not None
    result = {
        **deepcopy(annotation), **context,
        **dict.fromkeys(STUDY_CONTEXT_SCHEMA),
        **dict.fromkeys([
            "value_numeric", "value_lower", "value_upper", "qualifier", "unit_raw",
            "unit_standardized", "value_standardized", "value_lower_standardized",
            "value_upper_standardized",
        ]),
        "formulation_flag": formulation,
    }
    blocked = False
    if len(labels) > 1:
        notes.append("multiple Concentration fields")
        blocked = True
    elif not labels and re.search(
        r"\b(?:hardness|age|confidence\s+interval|CI)\b", raw, re.IGNORECASE,
    ):
        notes.append("result mixed with ancillary context; no isolated Concentration field")
        blocked = True
    if annotation["value_kind"] not in {"String", "StringWithMarkup", "Number"}:
        notes.append("unsupported value representation: " + annotation["value_kind"])
        blocked = True
    if formulation:
        notes.append("formulation or mixture context")
    if (not labels and re.search(r"[.!?]\s+\S", raw)) or any(
        "interaction" in heading.casefold() for heading in annotation["section_path"]
    ):
        notes.append("narrative or interaction evidence requires attribution review")
    if context["endpoint"] is not None and not blocked:
        parsed = parse_value(measured)
        if parsed is None:
            notes.append("no single supported positive numeric result")
        else:
            result.update(parsed)
            unit, factor = normalize_unit(parsed["unit_raw"], context["endpoint"], context["medium"])
            result["unit_standardized"] = unit
            if factor is None:
                notes.append("unsupported or incompatible unit/medium")
            else:
                converted = {
                    target: parsed[source] * factor if parsed[source] is not None else None
                    for source, target in [
                        ("value_numeric", "value_standardized"),
                        ("value_lower", "value_lower_standardized"),
                        ("value_upper", "value_upper_standardized"),
                    ]
                }
                if any(
                    value is not None and (not math.isfinite(value) or value <= 0)
                    for value in converted.values()
                ):
                    notes.append("converted value is nonpositive or nonfinite")
                else:
                    result.update(converted)
    result["parse_status"] = (
        "failed" if not has_supported_endpoint else "partial" if notes else "complete"
    )
    result["parse_note"] = "; ".join(dict.fromkeys(notes))
    return cast(Measurement, result)


def normalize_rows(annotations: pl.DataFrame, compounds: pl.DataFrame) -> pl.DataFrame:
    """Normalize each annotation and join compound labels without multiplying rows."""
    for label, frame, schema in [
        ("annotations", annotations, ANNOTATION_SCHEMA), ("compounds", compounds, COMPOUND_SCHEMA),
    ]:
        if any(frame.schema.get(field) != dtype for field, dtype in schema.items()):
            raise ValueError(f"Invalid {label} schema")
    reserved = set(annotations.columns) & (set(MEASUREMENT_SCHEMA) - set(ANNOTATION_SCHEMA))
    if reserved:
        raise ValueError(f"Annotation columns collide with derived fields: {sorted(reserved)}")
    if compounds["compound_id"].null_count() or compounds["compound_id"].is_duplicated().any():
        raise ValueError("Compound identities must be nonnull and unique")
    missing = annotations.select("compound_id").unique().join(
        compounds.select("compound_id"), on = "compound_id", how = "anti",
    )
    if missing.height:
        raise ValueError("Annotations reference compounds outside the selected universe")
    extras = {
        field: dtype for field, dtype in annotations.schema.items() if field not in ANNOTATION_SCHEMA
    }
    normalized = frame_from_rows(
        [normalize_annotation(row) for row in annotations.iter_rows(named = True)],
        {**NORMALIZED_ANNOTATION_SCHEMA, **extras},
    )
    return normalized.join(
        compounds.select("compound_id", *COMPOUND_CONTEXT_SCHEMA), on = "compound_id",
        how = "left", validate = "m:1", maintain_order = "left",
    ).select(*MEASUREMENT_SCHEMA, *extras)
