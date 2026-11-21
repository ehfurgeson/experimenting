"""Load, validate, and reconcile curated chemical queries."""

import csv
import hashlib
from collections.abc import Iterable
from pathlib import Path
from typing import Literal, cast

from .contracts import Query

QUERY_FIELDS = frozenset(Query.__annotations__)


def classify_query(query: str) -> tuple[Literal["cid", "name"], str]:
    """Return a query kind and trimmed name or canonical positive ASCII CID.

    Only strings consisting entirely of ASCII digits are interpreted as CIDs.
    Names retain their spelling and internal whitespace. Blank queries and
    all-zero CIDs raise ValueError.
    """
    value = query.strip()
    if not value:
        raise ValueError("Chemical query must not be blank")
    if value.isascii() and value.isdecimal():
        canonical = value.lstrip("0")
        if not canonical:
            raise ValueError("PubChem CID must be positive")
        return "cid", canonical
    return "name", value


def query_key(query: str) -> str:
    """Hash kind and canonical text into a stable, filename-safe SHA-256 key.

    Name equivalence uses casefolding only; chemical synonyms are not inferred.
    Keep the input spelling in the Query record rather than replacing it with
    this key or its casefolded text.
    """
    kind, value = classify_query(query)
    identity = f"{kind}:{value.casefold()}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def merge_queries(rows: Iterable[Query]) -> list[Query]:
    """Merge equivalent inputs in order, enriching blank curated metadata.

    Retain the first trimmed query spelling. Conflicting nonempty metadata,
    unsupported fields, nonstring values, and invalid queries raise ValueError.
    Input records are never mutated.
    """
    unique: dict[str, dict[str, str]] = {}
    for row in rows:
        if set(row) - QUERY_FIELDS:
            raise ValueError(f"Unsupported query fields: {sorted(set(row) - QUERY_FIELDS)}")
        if "query" not in row or any(not isinstance(value, str) for value in row.values()):
            raise ValueError("Query records require a query and string field values")
        item = {field: value.strip() for field, value in row.items()}
        key = query_key(item["query"])
        if key not in unique:
            unique[key] = item
            continue
        existing = unique[key]
        for field, value in item.items():
            if field == "query":
                continue
            previous = existing.get(field, "")
            if previous and value and previous != value:
                raise ValueError(
                    f"Conflicting metadata for {existing['query']!r}, field {field!r}: "
                    f"{previous!r} versus {value!r}"
                )
            if not previous:
                existing[field] = value
    return [cast(Query, item) for item in unique.values()]


def load_queries(path: Path) -> list[Query]:
    """Load UTF-8/BOM CSV or TXT and merge equivalent inputs.

    CSV headers use the Query field names. Headerless CSV uses only the first
    column. Blank rows and rows whose first cell starts with # are ignored.
    Headered rows must match the header width; unknown or duplicate headers
    are errors. TXT treats each nonblank, noncomment line as a whole query.
    """
    if path.suffix.lower() not in {".csv", ".txt"}:
        raise ValueError(f"Expected a .csv or .txt input file: {path}")
    try:
        with path.open(encoding = "utf-8-sig", newline = None) as stream:
            if path.suffix.lower() == ".txt":
                rows = (
                    {"query": line.strip()}
                    for line in stream
                    if line.strip() and not line.lstrip().startswith("#")
                )
                return merge_queries(rows)
            reader = csv.reader(stream, strict = True)
            records = (
                [cell.strip() for cell in row]
                for row in reader
                if any(cell.strip() for cell in row)
                and not row[0].lstrip().startswith("#")
            )
            first = next(records, None)
            if first is None:
                return []
            if not QUERY_FIELDS.intersection(first):
                inputs = [{"query": first[0]}] if first[0] else []
                inputs.extend({"query": row[0]} for row in records if row[0])
                return merge_queries(inputs)
            if "query" not in first:
                raise ValueError("CSV header must contain 'query'")
            if len(first) != len(set(first)):
                raise ValueError("CSV header contains duplicate fields")
            if set(first) - QUERY_FIELDS:
                raise ValueError(f"Unsupported CSV fields: {sorted(set(first) - QUERY_FIELDS)}")
            inputs = []
            for row in records:
                if len(row) != len(first):
                    raise ValueError(f"CSV row {reader.line_num} has an invalid column count")
                inputs.append(cast(Query, dict(zip(first, row, strict = True))))
            return merge_queries(inputs)
    except (csv.Error, ValueError) as error:
        raise ValueError(f"{path}: {error}") from error
