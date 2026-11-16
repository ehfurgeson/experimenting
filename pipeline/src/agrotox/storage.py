"""Explicit raw storage paths and atomic JSON replacement."""

import hashlib
import json
import os
import tempfile
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

import polars as pl

from .contracts import Snapshot
from .identity import compound_key
from .inputs import classify_query, query_key
from .sources.pubchem_payloads import validate_properties, validate_toxicity


def query_path(root: Path, query: str) -> Path:
    """Locate a query alias under the caller's data root without creating it."""
    return root / "raw" / "pubchem" / "queries" / f"{query_key(query)}.json"


def compound_path(
    root: Path, cid: int, component: Literal["properties", "toxicity", "metadata"]
) -> Path:
    """Locate a validated CID bundle component without creating directories."""
    if cid is None:
        raise ValueError("Storage requires a resolved CID")
    compound_key(cid, "")
    if component not in {"properties", "toxicity", "metadata"}:
        raise ValueError(f"Unsupported snapshot component: {component!r}")
    return root / "raw" / "pubchem" / str(cid) / f"{component}.json"


def epa_search_path(root: Path, term: str) -> Path:
    """Locate a cached EPA chemical search by term without creating anything."""
    if not isinstance(term, str) or not term.strip():
        raise ValueError("An EPA search term must be a nonempty string")
    digest = hashlib.sha256(term.strip().encode("utf-8")).hexdigest()
    return root / "raw" / "comptox" / "chemical" / "search" / f"{digest}.json"


def epa_detail_path(root: Path, dtxsid: str) -> Path:
    """Locate a cached EPA chemical detail record without creating anything."""
    if not isinstance(dtxsid, str) or not dtxsid.strip():
        raise ValueError("A DTXSID must be a nonempty string")
    return root / "raw" / "comptox" / "chemical" / "detail" / f"{dtxsid.strip()}.json"


def epa_bioactivity_path(root: Path, dtxsid: str) -> Path:
    """Locate a cached EPA bioactivity response without creating anything."""
    if not isinstance(dtxsid, str) or not dtxsid.strip():
        raise ValueError("A DTXSID must be a nonempty string")
    return root / "raw" / "comptox" / "bioactivity" / f"{dtxsid.strip()}.json"


def epa_assay_path(root: Path, aeid: int) -> Path:
    """Locate a cached EPA assay annotation without creating anything."""
    if type(aeid) is not int or aeid <= 0:
        raise ValueError("A ToxCast assay endpoint ID must be a positive integer")
    return root / "raw" / "comptox" / "assay" / f"{aeid}.json"


def epa_hazard_path(root: Path, dtxsid: str) -> Path:
    """Locate a cached EPA hazard response without creating anything."""
    if not isinstance(dtxsid, str) or not dtxsid.strip():
        raise ValueError("A DTXSID must be a nonempty string")
    return root / "raw" / "comptox" / "hazard" / f"{dtxsid.strip()}.json"


def epa_property_path(root: Path, kind: str, dtxsid: str) -> Path:
    """Locate a cached EPA property response without creating anything."""
    if kind not in {"experimental", "predicted"}:
        raise ValueError("Property responses are experimental or predicted")
    if not isinstance(dtxsid, str) or not dtxsid.strip():
        raise ValueError("A DTXSID must be a nonempty string")
    return root / "raw" / "comptox" / "chemical" / "property" / kind / f"{dtxsid.strip()}.json"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Publish UTF-8 JSON by replacing the destination with a complete sibling.

    Create parents and use a unique temporary file on the destination filesystem.
    Serialization, write, and replacement failures preserve any prior destination
    and remove the temporary file. Atomicity applies to one file, not a bundle.
    Nonfinite floats are rejected rather than emitting nonstandard JSON.
    """
    path.parent.mkdir(parents = True, exist_ok = True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode = "w", encoding = "utf-8", newline = "\n",
            dir = path.parent, prefix = ".agrotox-", suffix = ".tmp", delete = False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, ensure_ascii = False, allow_nan = False, indent = 2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok = True)


def _reject_constant(value: str) -> None:
    raise ValueError(f"Nonstandard JSON number: {value}")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding = "utf-8"), parse_constant = _reject_constant)
    except (UnicodeError, ValueError) as error:
        raise ValueError(f"Invalid JSON in {path}: {error}") from error
    if not isinstance(payload, dict):
        # Persisted malformed data is a ValueError under the cache-read contract.
        raise ValueError(f"Expected a JSON object in {path}")  # noqa: TRY004
    return payload


def _matching_cid(value: object, cid: int) -> bool:
    return type(value) is int and value == cid


def _read_bundle(root: Path, cid: int) -> Snapshot:
    envelope = _read_json(compound_path(root, cid, "properties"))
    properties = validate_properties(envelope, cid)
    metadata = _read_json(compound_path(root, cid, "metadata"))
    if not _matching_cid(metadata.get("cid"), cid) or metadata.get("source") != "PubChem":
        raise ValueError(f"Metadata identity does not match PubChem CID {cid}")
    try:
        retrieved_at = datetime.fromisoformat(metadata["retrieved_at"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Invalid retrieved_at for CID {cid}") from error
    if retrieved_at.utcoffset() != timedelta(0):
        raise ValueError(f"retrieved_at must be timezone-aware UTC for CID {cid}")
    status = metadata.get("toxicity_status")
    if status not in ("found", "missing", "pending"):
        raise ValueError(f"Invalid toxicity_status for CID {cid}: {status!r}")
    snapshot: Snapshot = {
        "cid": cid, "properties": properties, "metadata": metadata, "toxicity": None,
    }
    if status == "pending":
        return snapshot
    toxicity = _read_json(compound_path(root, cid, "toxicity"))
    if status == "missing":
        if toxicity != {"missing_section": "Toxicity"}:
            raise ValueError(f"Missing status requires a Toxicity absence marker for CID {cid}")
    else:
        validate_toxicity(toxicity, cid)
    snapshot["toxicity"] = toxicity
    return snapshot


def read_alias(root: Path, query: str) -> dict[str, Any] | None:
    """Read and validate an alias independently of its possibly incomplete bundle."""
    path = query_path(root, query)
    try:
        alias = _read_json(path)
    except FileNotFoundError:
        return None
    spelling, cid = alias.get("query"), alias.get("cid")
    if not isinstance(spelling, str) or query_key(spelling) != query_key(query):
        raise ValueError(f"Alias query does not match {path}")
    if type(cid) is not int or cid <= 0:
        raise ValueError(f"Alias requires a positive integer CID: {path}")
    kind, value = classify_query(query)
    if kind == "cid" and value != str(cid):
        raise ValueError(f"Numeric query CID does not match alias CID: {path}")
    return alias


def read_snapshot(root: Path, query: str) -> Snapshot | None:
    """Read a selected alias and validated bundle; return None for absent aliases.

    Invalid aliases and missing or corrupt bundle components raise ValueError.
    Pending bundles expose identity but never read or expose saved toxicity.
    Raw property envelopes remain unchanged; consumers get the single record.
    """
    alias = read_alias(root, query)
    if alias is None:
        return None
    cid = alias["cid"]
    try:
        return _read_bundle(root, cid)
    except FileNotFoundError as error:
        raise ValueError(f"Incomplete bundle for CID {cid}: {error.filename}") from error


def complete_record(root: Path, cid: int) -> bool:
    """Return whether a CID has a valid found/missing bundle, independently of aliases.

    Absent, corrupt, and pending bundles return False. Filesystem access errors
    other than absent files propagate to the caller.
    """
    try:
        snapshot = _read_bundle(root, cid)
    except (FileNotFoundError, ValueError):
        return False
    return snapshot["metadata"]["toxicity_status"] in ("found", "missing")


def save_table(
    path: Path, frame: pl.DataFrame, sources: Iterable[Path], *, code_version: str
) -> None:
    """Save native Parquet and a JSON sidecar hashing every supplied dependency.

    Hash dependencies before modifying outputs. Callers must list all consumed
    inputs, configs, and implementation files. Preserve the frame's own schema.
    Table and sidecar replacement are individually atomic, not a transaction.
    """
    sidecar = path.with_suffix(".metadata.json")
    outputs = {path.resolve(), sidecar.resolve()}
    input_hashes = {}
    for source in sources:
        if source.resolve() in outputs:
            raise ValueError(f"Output would overwrite a consumed dependency: {source}")
        with source.open("rb") as stream:
            input_hashes[str(source)] = hashlib.file_digest(stream, "sha256").hexdigest()
    metadata = {
        "generated_at": datetime.now(UTC).isoformat(),
        "code_version": code_version,
        "row_count": frame.height,
        "input_hashes": input_hashes,
    }
    path.parent.mkdir(parents = True, exist_ok = True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir = path.parent, prefix = ".agrotox-", suffix = ".parquet.tmp", delete = False,
        ) as stream:
            temporary = Path(stream.name)
        frame.write_parquet(temporary, use_pyarrow = False)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok = True)
    write_json(sidecar, metadata)
