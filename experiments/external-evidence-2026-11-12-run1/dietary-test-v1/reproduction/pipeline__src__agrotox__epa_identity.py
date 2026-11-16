"""Audited crosswalk between PubChem compounds and EPA DTXSID identities."""

import json
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl

from .storage import epa_detail_path, epa_search_path, write_json
from .tables import (
    EPA_IDENTITY_CANDIDATE_SCHEMA,
    EPA_IDENTITY_CROSSWALK_SCHEMA,
    frame_from_rows,
)

# The first block of an InChIKey identifies the connection layer. Two keys with
# the same block describe the same skeleton and may differ in stereochemistry,
# tautomer, or protonation, so they are not the same substance.
CONNECTIVITY_LENGTH = 14

EXACT_STRUCTURE = "exact_structure"
CONNECTIVITY_ONLY = "connectivity_only"
NAME_ONLY = "name_only"
NO_MATCH = "none"

APPROVED = "approved"
UNRESOLVED = "unresolved"
NEEDS_REVIEW = "needs_review"


def connectivity_key(inchikey: str) -> str:
    """Return the connection-layer block of an InChIKey."""
    return inchikey[:CONNECTIVITY_LENGTH]


def match_strength(source_inchikey: str | None, candidate_inchikey: str | None) -> str:
    """Classify one candidate against the source compound's structure.

    An identical InChIKey is an exact structure. A candidate that shares the
    connection layer but not the full key differs in stereochemistry, tautomer,
    or protonation, and a candidate with a different connection layer is a
    different substance, such as a salt or an ester.
    """
    if not source_inchikey or not candidate_inchikey:
        return NO_MATCH
    if candidate_inchikey == source_inchikey:
        return EXACT_STRUCTURE
    if connectivity_key(candidate_inchikey) == connectivity_key(source_inchikey):
        return CONNECTIVITY_ONLY
    return NO_MATCH


def search_plan(compound: Mapping[str, Any]) -> list[dict[str, str]]:
    """Return the ordered EPA searches for one compound.

    The full InChIKey is searched first because it is a structure comparison.
    The preferred name is searched afterwards and can only produce a candidate
    for review, never an approval.
    """
    plan = []
    inchikey = compound.get("inchikey")
    if isinstance(inchikey, str) and inchikey.strip():
        plan.append({"search_basis": "inchikey", "search_term": inchikey.strip()})
    name = compound.get("preferred_name")
    if isinstance(name, str) and name.strip():
        plan.append({"search_basis": "name", "search_term": name.strip()})
    return plan


def identity_candidates(
    compounds: pl.DataFrame, evidence: Iterable[Mapping[str, Any]],
) -> pl.DataFrame:
    """Return every EPA candidate found for the selected compounds.

    All candidates are retained with their search basis, their identifiers, and
    the strength of their match. Nothing is dropped for being unsuitable, so a
    reviewer can see what was rejected and why.
    """
    strongest = {
        EXACT_STRUCTURE: 3, CONNECTIVITY_ONLY: 2, NAME_ONLY: 1, NO_MATCH: 0,
    }
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in evidence:
        inchikey = entry.get("inchikey")
        for search in entry.get("searches", []):
            found_in_search = 0
            for candidate in search.get("candidates", []):
                if not isinstance(candidate, dict):
                    continue
                found_in_search += 1
                detail = candidate.get("detail") or {}
                candidate_inchikey = detail.get("inchikey")
                if not isinstance(candidate_inchikey, str) or not candidate_inchikey.strip():
                    candidate_inchikey = None
                    strength = NAME_ONLY if search.get("search_basis") == "name" else NO_MATCH
                else:
                    strength = match_strength(inchikey, candidate_inchikey)
                dtxsid = candidate.get("dtxsid")
                row = {
                    "compound_id": entry["compound_id"],
                    "pubchem_cid": entry.get("pubchem_cid"),
                    "search_basis": search.get("search_basis"),
                    "search_term": search.get("search_term"),
                    "dtxsid": dtxsid,
                    "preferred_name": candidate.get("preferredName"),
                    "casrn": candidate.get("casrn"),
                    "inchikey": candidate_inchikey,
                    "smiles": detail.get("smiles") or candidate.get("smiles"),
                    "inchi": detail.get("inchiString"),
                    "molecular_formula": detail.get("molFormula"),
                    "molecular_weight": detail.get("averageMass"),
                    "total_assays": detail.get("totalAssays"),
                    "active_assays": detail.get("activeAssays"),
                    "detail_status": "resolved" if detail else "unavailable",
                    "rank": candidate.get("rank"),
                    "match_strength": strength,
                    "provider_suggestions": search.get("suggestions", []),
                }
                # The same substance can be found by more than one search. It is
                # one candidate, described by its strongest evidence.
                key = (entry["compound_id"], dtxsid if isinstance(dtxsid, str) else id(candidate))
                existing = rows.get(key)
                if existing is None or (
                    strongest[strength] > strongest[existing["match_strength"]]
                ):
                    rows[key] = row
    # A search that found nothing still carries the provider's near misses, so
    # a reviewer can see which alternative structure the provider offered.
    for entry in evidence:
        for search in entry.get("searches", []):
            if search.get("candidates"):
                continue
            rows[(entry["compound_id"], f"search:{search.get('search_term')}")] = {
                "compound_id": entry["compound_id"],
                "pubchem_cid": entry.get("pubchem_cid"),
                "search_basis": search.get("search_basis"),
                "search_term": search.get("search_term"),
                "dtxsid": None,
                "preferred_name": None,
                "casrn": None,
                "inchikey": None,
                "smiles": None,
                "inchi": None,
                "molecular_formula": None,
                "molecular_weight": None,
                "total_assays": None,
                "active_assays": None,
                "detail_status": "unavailable",
                "rank": None,
                "match_strength": NO_MATCH,
                "provider_suggestions": search.get("suggestions", []),
            }
    ordered = sorted(
        rows.values(),
        key = lambda row: (row["compound_id"], row["search_basis"], row["search_term"],
                           row["dtxsid"] or ""),
    )
    return frame_from_rows(ordered, EPA_IDENTITY_CANDIDATE_SCHEMA)


def identity_crosswalk(
    compounds: pl.DataFrame, candidates: pl.DataFrame,
) -> pl.DataFrame:
    """Approve, defer, or leave unresolved every selected compound's EPA identity.

    A crosswalk row is approved only when exactly one candidate has the same
    full InChIKey as the source compound. Ambiguity is never resolved by
    choosing the first or the highest ranked candidate.
    """
    by_compound: dict[str, list[dict[str, Any]]] = {}
    for row in candidates.iter_rows(named = True):
        by_compound.setdefault(row["compound_id"], []).append(row)
    rows: list[dict[str, Any]] = []
    selected = compounds.unique(subset = ["compound_id"], keep = "first", maintain_order = True)
    for compound in selected.iter_rows(named = True):
        compound_id = compound["compound_id"]
        found = by_compound.get(compound_id, [])
        exact = [row for row in found if row["match_strength"] == EXACT_STRUCTURE]
        connectivity = [row for row in found if row["match_strength"] == CONNECTIVITY_ONLY]
        name_only = [row for row in found if row["match_strength"] == NAME_ONLY]
        if compound.get("resolution_status") != "resolved":
            status, dtxsid, strength = UNRESOLVED, None, NO_MATCH
            reason = "unresolved PubChem identity"
        elif len(exact) == 1:
            status = APPROVED
            dtxsid = exact[0]["dtxsid"]
            strength = EXACT_STRUCTURE
            reason = "one candidate has the same full InChIKey"
        elif len(exact) > 1:
            status, dtxsid, strength = NEEDS_REVIEW, None, EXACT_STRUCTURE
            reason = "several candidates share the full InChIKey"
        elif connectivity:
            status, dtxsid, strength = NEEDS_REVIEW, None, CONNECTIVITY_ONLY
            reason = "a candidate shares the connection layer but not the full InChIKey"
        elif name_only:
            status, dtxsid, strength = NEEDS_REVIEW, None, NAME_ONLY
            reason = "a candidate was found by name only"
        else:
            status, dtxsid, strength = UNRESOLVED, None, NO_MATCH
            reason = "no EPA candidate matches this structure"
        rows.append({
            "compound_id": compound_id,
            "pubchem_cid": compound.get("pubchem_cid"),
            "input_queries": compound.get("input_queries"),
            "dtxsid": dtxsid,
            "status": status,
            "match_strength": strength,
            "inchikey": compound.get("inchikey"),
            "candidate_count": sum(
                1 for row in found if isinstance(row.get("dtxsid"), str)
            ),
            "reason": reason,
        })
    return frame_from_rows(rows, EPA_IDENTITY_CROSSWALK_SCHEMA)


def identity_review_queue(crosswalk: pl.DataFrame) -> pl.DataFrame:
    """Return the crosswalk rows that a human must decide."""
    if crosswalk.is_empty():
        return frame_from_rows([], EPA_IDENTITY_CROSSWALK_SCHEMA)
    return crosswalk.filter(pl.col("status") == NEEDS_REVIEW)


def _cached_search(root: Path, term: str) -> list[dict[str, Any]] | None:
    path = epa_search_path(root, term)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding = "utf-8"))
    response = payload.get("response")
    return response if isinstance(response, list) else []


def _store_search(
    root: Path, term: str, basis: str, response: list[dict[str, Any]],
) -> None:
    write_json(epa_search_path(root, term), {
        "search_term": term,
        "search_basis": basis,
        "provider": "EPA CompTox",
        "retrieved_at": datetime.now(UTC).isoformat(),
        "url": f"/chemical/search/equal/{term}",
        "status": 200,
        "response": response,
    })


def _read_cached(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding = "utf-8")).get("response")


def candidate_detail(root: Path, dtxsid: str, client: Any) -> dict[str, Any] | None:
    """Return the candidate's own chemical record, reusing the cache.

    The search response does not carry the candidate's structure, so the
    structure comparison needs this record. A candidate whose record cannot be
    read keeps a null structure and is never approved.
    """
    if not isinstance(dtxsid, str) or not dtxsid.strip():
        return None
    path = epa_detail_path(root, dtxsid.strip())
    cached = _read_cached(path)
    if cached is None:
        cached = client.details(dtxsid.strip())
        if cached is not None:
            write_json(path, {
                "dtxsid": dtxsid.strip(),
                "provider": "EPA CompTox",
                "retrieved_at": datetime.now(UTC).isoformat(),
                "url": f"/chemical/detail/search/by-dtxsid/{dtxsid.strip()}",
                "status": 200,
                "response": cached,
            })
    return cached


def resolve_identities(
    root: Path, compounds: pl.DataFrame, client: Any,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Resolve EPA identities for the selected compounds, reusing cached searches.

    A cached search is reused, so a rerun makes no request for a term that was
    already retrieved. The API key is never written to the cache: it travels in
    a request header, and the stored envelope records the term and the path.
    """
    evidence = []
    selected = compounds.unique(subset = ["compound_id"], keep = "first", maintain_order = True)
    for compound in selected.iter_rows(named = True):
        searches = []
        for plan in search_plan(compound):
            term = plan["search_term"]
            path = epa_search_path(root, term)
            cached = _read_cached(path)
            if not isinstance(cached, dict) or "candidates" not in cached:
                # A cache written in an older format is refetched rather than read.
                cached = None
            if cached is None:
                result = client.search_equal(term)
                cached = {"candidates": result.candidates, "suggestions": result.suggestions}
                write_json(path, {
                    "search_term": term,
                    "search_basis": plan["search_basis"],
                    "provider": "EPA CompTox",
                    "retrieved_at": datetime.now(UTC).isoformat(),
                    "url": f"/chemical/search/equal/{term}",
                    "status": 200,
                    "response": cached,
                })
            candidates = []
            for candidate in cached.get("candidates", []):
                detail = candidate_detail(root, candidate.get("dtxsid"), client)
                candidates.append({**candidate, "detail": detail})
            searches.append({
                **plan,
                "candidates": candidates,
                "suggestions": cached.get("suggestions", []),
            })
        evidence.append({
            "compound_id": compound["compound_id"],
            "pubchem_cid": compound.get("pubchem_cid"),
            "inchikey": compound.get("inchikey"),
            "searches": searches,
        })
    candidates = identity_candidates(compounds, evidence)
    return candidates, identity_crosswalk(compounds, candidates)
