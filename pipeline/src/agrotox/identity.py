"""Reconcile curated aliases using resolved PubChem identities."""

import math
from collections.abc import Mapping
from typing import Any, cast

from .contracts import Compound, Query, Snapshot
from .inputs import merge_queries, query_key

PROPERTY_FIELDS = {
    "preferred_name": ("Title",),
    "inchi": ("InChI",),
    "inchikey": ("InChIKey",),
    "smiles": ("SMILES", "IsomericSMILES"),
    "connectivity_smiles": ("ConnectivitySMILES", "CanonicalSMILES"),
    "molecular_formula": ("MolecularFormula",),
    "iupac_name": ("IUPACName",),
}
CLASSIFICATIONS = ("chemical_group", "subgroup", "hrac_group")
TOXICITY_STATUSES = {"found", "missing", "pending", "not_retrieved"}


def compound_key(cid: int | None, query: str) -> str:
    """Return a resolved positive integer CID identity or an unresolved query key."""
    if cid is None:
        return f"QUERY:{query_key(query)}"
    if type(cid) is not int or cid <= 0:
        raise ValueError("Resolved CID must be a positive integer")
    return f"PUBCHEM:{cid}"


def _snapshot_fields(snapshot: Snapshot) -> dict[str, object]:
    """Read identity properties without interpreting toxicity content."""
    cid = snapshot["cid"]
    if cid is None:
        raise ValueError("Resolved snapshot requires a CID")
    compound_key(cid, "")
    properties, metadata = snapshot["properties"], snapshot["metadata"]
    for record, field in [(properties, "CID"), (metadata, "cid")]:
        if field in record and (type(record[field]) is not int or record[field] != cid):
            raise ValueError("Snapshot CID does not match its property or metadata CID")
    status = metadata.get("toxicity_status", "not_retrieved")
    if status not in TOXICITY_STATUSES:
        raise ValueError(f"Unsupported toxicity_status: {status!r}")
    result: dict[str, object] = {"toxicity_status": status}
    for field, names in PROPERTY_FIELDS.items():
        result[field] = None
        for name in names:
            value = properties.get(name)
            if value is None:
                continue
            if not isinstance(value, str):
                raise TypeError(f"{field} must be text or null")
            if value.strip():
                result[field] = value.strip()
                break
    weight = properties.get("MolecularWeight")
    result["molecular_weight"] = None
    if weight is not None:
        try:
            numeric = float(weight)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError("Invalid molecular_weight") from error
        if isinstance(weight, bool) or not math.isfinite(numeric) or numeric <= 0:
            raise ValueError("molecular_weight must be positive and finite")
        result["molecular_weight"] = numeric
    return result


def reconcile_compounds(
    queries: list[Query], snapshots: Mapping[str, Snapshot]
) -> list[Compound]:
    """Merge selected aliases by CID; retain unresolved identities and all notes.

    Snapshots are keyed by input spelling (surrounding whitespace is permitted).
    Missing snapshots leave queries unresolved. Nonempty classifications and
    properties must agree among aliases; conflicting retrieval statuses also
    raise ValueError. No files are read and input records are never mutated.
    """
    compounds: dict[str, dict[str, Any]] = {}
    for original in queries:
        query = merge_queries([original])[0]
        spelling = query["query"]
        snapshot = snapshots.get(original["query"], snapshots.get(spelling))
        cid = snapshot["cid"] if snapshot is not None else None
        fields = _snapshot_fields(snapshot) if snapshot is not None else {}
        key = compound_key(cid, spelling)
        incoming = {
            **{field: None for field in PROPERTY_FIELDS},
            "molecular_weight": None,
            **{field: query.get(field) or None for field in CLASSIFICATIONS},
            **fields,
        }
        if key not in compounds:
            compounds[key] = {
                "compound_id": key,
                "pubchem_cid": cid,
                "input_queries": [],
                "source_notes": [],
                "resolution_status": "resolved" if cid is not None else "unresolved",
                "toxicity_status": "not_retrieved",
                **incoming,
            }
        else:
            existing = compounds[key]
            for field, value in incoming.items():
                if value is None:
                    continue
                if existing[field] is not None and existing[field] != value:
                    raise ValueError(f"Conflicting {field} for {key}: {existing[field]!r} / {value!r}")
                existing[field] = value
        compound = compounds[key]
        if spelling not in compound["input_queries"]:
            compound["input_queries"].append(spelling)
        note = query.get("source_note", "")
        if note and note not in compound["source_notes"]:
            compound["source_notes"].append(note)
    return [cast(Compound, row) for row in compounds.values()]
