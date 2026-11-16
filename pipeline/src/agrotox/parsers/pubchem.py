"""Flatten PUG-View annotations without interpreting toxicity measurements."""

import hashlib
import json
import math
from typing import Any

from ..contracts import Annotation, SourceReference
from ..identity import compound_key


def _json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii = False, sort_keys = True, separators = (",", ":"), allow_nan = False,
    )


def extract_values(value: Any) -> list[tuple[str, str]]:
    """Extract text/kind pairs; keep arrays together and serialize unknown shapes."""
    if isinstance(value, str):
        return [(value, "String")]
    if not isinstance(value, dict) or not value:
        return [(_json(value), "unknown")]
    result = []
    for kind, items in value.items():
        if kind == "Unit" and "Number" in value:
            continue
        if kind == "StringWithMarkup":
            if not isinstance(items, list) or not items:
                result.append((_json(items), "unknown"))
                continue
            for item in items:
                if isinstance(item, dict) and isinstance(item.get("String"), str):
                    result.append((item["String"], kind))
                else:
                    result.append((_json(item), "unknown"))
        elif kind == "Number":
            numbers = items if isinstance(items, list) else [items]
            unit = value.get("Unit")
            if (
                not numbers or any(type(number) not in (int, float) for number in numbers)
                or any(isinstance(number, float) and not math.isfinite(number) for number in numbers)
                or (unit is not None and not isinstance(unit, str))
            ):
                result.append((_json({"Number": items, "Unit": unit}), "unknown"))
                continue
            text = ", ".join(str(number) for number in numbers)
            result.append((
                f"{text} {unit or ''}".strip(), "NumberArray" if len(numbers) > 1 else kind,
            ))
        else:
            result.append((_json(items), kind))
    return result


def _entries(value: Any, context: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"Expected a list of objects or null for {context}")
    return value


def _text(value: Any) -> str | None:
    return value if value is None or isinstance(value, str) else _json(value)


def _reference_numbers(value: Any) -> list[int]:
    if value is None:
        return []
    numbers = value if isinstance(value, list) else [value]
    if any(type(number) is not int or number <= 0 for number in numbers):
        raise ValueError("Reference numbers must be positive integers")
    return sorted(set(numbers))


def flatten_sections(
    payload: dict[str, Any], *, cid: int, raw_file: str, retrieved_at: str
) -> list[Annotation]:
    """Walk nested sections and retain annotations with content-based SHA-256 IDs.

    IDs include compound, context, original information/value content, and resolved
    references. They exclude file location, retrieval time, aliases, and traversal
    positions. Repeated content keeps its rows and may share an ID.
    """
    if cid is None:
        raise ValueError("Annotations require a resolved CID")
    compound_id = compound_key(cid, "")
    record = payload.get("Record")
    if not isinstance(record, dict):
        # Invalid source data follows the parser's ValueError contract.
        raise ValueError("Expected a PUG-View Record object")  # noqa: TRY004
    references: dict[int, list[dict[str, Any]]] = {}
    for reference in _entries(record.get("Reference"), "Reference"):
        numbers = _reference_numbers(reference.get("ReferenceNumber"))
        if len(numbers) != 1:
            raise ValueError("Each source reference requires one reference number")
        references.setdefault(numbers[0], []).append(reference)
    rows: list[Annotation] = []

    def visit(sections: Any, path: list[str]) -> None:
        for section in _entries(sections, "Section"):
            heading = _text(section.get("TOCHeading"))
            current = [*path, heading] if heading else path.copy()
            for information in _entries(section.get("Information"), "Information"):
                numbers = _reference_numbers(information.get("ReferenceNumber"))
                sources: list[SourceReference] = []
                for number in numbers:
                    for reference in references.get(number, [None]):
                        sources.append({
                            "reference_number": number,
                            "source_name": _text(
                                reference.get("SourceName") or reference.get("Name")
                            ) if reference else None,
                            "source_url": _text(reference.get("URL")) if reference else None,
                            "reference_json": _json(reference) if reference else None,
                        })
                # Canonical source ordering also makes duplicate reference rows harmless.
                unique_sources = {_json(source): source for source in sources}
                sources = [unique_sources[key] for key in sorted(unique_sources)]
                content = {
                    "compound_id": compound_id, "record_title": _text(record.get("RecordTitle")),
                    "section_path": current,
                    "information": {
                        key: value for key, value in information.items() if key != "ReferenceNumber"
                    },
                    "reference_numbers": numbers, "sources": sources,
                }
                for raw, kind in extract_values(information.get("Value")):
                    identity = {**content, "value_raw": raw, "value_kind": kind}
                    annotation_id = "sha256:" + hashlib.sha256(
                        _json(identity).encode("utf-8")
                    ).hexdigest()
                    rows.append({
                        "annotation_id": annotation_id,
                        "compound_id": compound_id, "record_title": content["record_title"],
                        "section_path": current.copy(),
                        "information_name": _text(information.get("Name")),
                        "description": _text(information.get("Description")),
                        "value_raw": raw, "value_kind": kind,
                        "reference_numbers": numbers.copy(),
                        "sources": [source.copy() for source in sources],
                        "information_url": _text(information.get("URL")),
                        "information_json": _json(information),
                        "raw_file": raw_file, "retrieved_at": retrieved_at,
                    })
            visit(section.get("Section"), current)

    visit(record.get("Section"), [])
    return rows
