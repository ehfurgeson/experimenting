"""Resumable PubChem bundles with explicit refresh state and batch outcomes."""

from datetime import UTC, datetime
from pathlib import Path

import requests

from .contracts import Outcome, Query, Source
from .identity import compound_key
from .inputs import classify_query, merge_queries
from .sources.pubchem_payloads import validate_properties, validate_toxicity
from .storage import (
    complete_record,
    compound_path,
    query_path,
    read_alias,
    read_snapshot,
    write_json,
)


def fetch_one(source: Source, root: Path, query: Query, *, force: bool = False) -> Outcome:
    """Reuse valid bundles or fetch one query, preserving identity on toxicity failure.

    Cache corruption triggers repair; filesystem access failures become structured
    errors. Force re-resolves queries. Pending is committed before replacing any
    bundle evidence. Callers must serialize access to this data root.
    """
    outcome: Outcome = {
        "query": query.get("query", ""), "cid": None, "status": "error", "stage": "input",
        "error_type": None, "message": None,
    }
    try:
        curated = merge_queries([query])[0]
        spelling = curated["query"]
        outcome["query"] = spelling
        outcome["stage"] = "cache"
        alias, snapshot = None, None
        try:
            alias = read_alias(root, spelling)
            if not force and alias is not None:
                snapshot = read_snapshot(root, spelling)
        except ValueError:
            # Invalid cached content is repairable; do not hide filesystem errors.
            pass
        cid = alias["cid"] if alias is not None and not force else None
        if cid is None:
            outcome["stage"] = "resolve"
            cid = source.resolve(spelling)
            if cid is None:
                raise ValueError("Resolved CID must be positive")
            compound_key(cid, spelling)
            kind, value = classify_query(spelling)
            if kind == "cid" and str(cid) != value:
                raise ValueError("Resolved CID does not match the numeric query")
        outcome["cid"] = cid
        alias_payload = {
            "query": alias["query"] if alias is not None else spelling,
            "cid": cid, "input_metadata": curated,
        }
        outcome["stage"] = "cache"
        if not force and complete_record(root, cid):
            outcome["stage"] = "alias"
            write_json(query_path(root, spelling), alias_payload)
            outcome.update(status = "skipped", stage = "complete")
            return outcome
        properties = None
        if force or snapshot is None:
            outcome["stage"] = "properties"
            properties = source.properties(cid)
            if not isinstance(properties, dict):
                raise ValueError("Expected a property response object")
            validate_properties(properties, cid)
        metadata = {
            "cid": cid, "source": "PubChem", "retrieved_at": datetime.now(UTC).isoformat(),
            "toxicity_status": "pending",
        }
        outcome["stage"] = "pending"
        write_json(compound_path(root, cid, "metadata"), metadata)
        if properties is not None:
            outcome["stage"] = "properties_write"
            write_json(compound_path(root, cid, "properties"), properties)
        outcome["stage"] = "alias"
        write_json(query_path(root, spelling), alias_payload)
        outcome["stage"] = "toxicity"
        toxicity = source.toxicity(cid)
        if toxicity is not None:
            if not isinstance(toxicity, dict):
                raise ValueError("Expected a toxicity response object")
            validate_toxicity(toxicity, cid)
        outcome["stage"] = "toxicity_write"
        write_json(
            compound_path(root, cid, "toxicity"),
            toxicity if toxicity is not None else {"missing_section": "Toxicity"},
        )
        outcome["stage"] = "complete"
        write_json(compound_path(root, cid, "metadata"), {
            **metadata, "retrieved_at": datetime.now(UTC).isoformat(),
            "toxicity_status": "missing" if toxicity is None else "found",
        })
        outcome["status"] = "fetched"
    except (requests.RequestException, OSError, ValueError, LookupError, TypeError) as error:
        outcome.update(error_type = type(error).__name__, message = str(error))
    return outcome


def fetch_batch(
    source: Source, root: Path, queries: list[Query], *, force: bool = False
) -> list[Outcome]:
    """Validate the whole selection, then continue independent queries after errors."""
    selected = merge_queries(queries)
    return [fetch_one(source, root, query, force = force) for query in selected]
