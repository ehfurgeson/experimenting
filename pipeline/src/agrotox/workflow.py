"""Offline composition of selected source evidence into typed stage tables."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from .analysis import (
    comparison_records,
    compound_summaries,
    extraction_audit,
    group_summaries,
    review_queue,
)
from .contracts import Annotation, Query, Snapshot
from .coverage import coverage_tables
from .identity import reconcile_compounds
from .inputs import merge_queries
from .normalize import normalize_rows
from .parsers.pubchem import flatten_sections
from .storage import compound_path, query_path, read_alias, read_snapshot
from .tables import annotation_table, compound_table

Definitions = dict[str, dict[str, str | float | int]]

TABLE_NAMES = (
    "compounds", "annotations", "measurements", "coverage", "coverage_by_group",
    "comparison_records", "compound_summary", "group_summary", "audit", "review_queue",
)


@dataclass(frozen = True)
class OfflineAnalysis:
    """Named analysis tables and the raw evidence they were built from."""

    tables: dict[str, pl.DataFrame]
    dependencies: dict[str, str]

    def __getitem__(self, name: str) -> pl.DataFrame:
        return self.tables[name]


def _selected_evidence(
    root: Path, queries: list[Query],
) -> tuple[list[Query], dict[str, Snapshot], dict[int, Snapshot], list[Path]]:
    """Read the selected aliases and bundles, and report every file consumed."""
    selected = merge_queries(queries)
    snapshots: dict[str, Snapshot] = {}
    by_cid: dict[int, Snapshot] = {}
    consumed: list[Path] = []
    for query in selected:
        spelling = query["query"]
        alias = read_alias(root, spelling)
        if alias is None:
            continue
        consumed.append(query_path(root, spelling))
        cid = alias["cid"]
        if cid not in by_cid:
            snapshot = read_snapshot(root, spelling)
            if snapshot is None:
                raise ValueError(f"Selected alias disappeared while reading {spelling!r}")
            by_cid[cid] = snapshot
            components = ["properties", "metadata"]
            if snapshot["metadata"]["toxicity_status"] != "pending":
                components.append("toxicity")
            consumed.extend(compound_path(root, cid, component) for component in components)
        snapshots[spelling] = by_cid[cid]
    return selected, snapshots, by_cid, consumed


def parse_snapshots(root: Path, queries: list[Query]) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Return annotations and compounds from selected caches, without writes or HTTP.

    Validate the selection before reading. Load and flatten each selected CID
    once, retain unresolved queries, and propagate corrupt selected evidence.
    Pending/missing toxicity yields identity rows without annotation rows.
    """
    selected, snapshots, by_cid, _ = _selected_evidence(root, queries)
    compounds = reconcile_compounds(selected, snapshots)
    annotations: list[Annotation] = []
    for cid, snapshot in by_cid.items():
        if snapshot["metadata"]["toxicity_status"] != "found":
            continue
        annotations.extend(flatten_sections(
            snapshot["toxicity"], cid = cid,
            raw_file = str(compound_path(root, cid, "toxicity")),
            retrieved_at = snapshot["metadata"]["retrieved_at"],
        ))
    return annotation_table(annotations), compound_table(compounds)


def _hash_paths(paths: list[Path]) -> dict[str, str]:
    """Hash every consumed file so a manifest can record what was read."""
    hashed = {}
    for path in sorted({str(path) for path in paths}):
        with Path(path).open("rb") as stream:
            hashed[path] = hashlib.file_digest(stream, "sha256").hexdigest()
    return hashed


def build_offline(
    root: Path, queries: list[Query], definitions: Definitions,
) -> OfflineAnalysis:
    """Build every analysis table from the selected snapshots, without network.

    The composition is deterministic: the same selection, evidence, and
    definitions produce the same rows. Raw evidence is only read, never written,
    and the returned dependency hashes identify every file that was consumed.
    """
    selected, snapshots, by_cid, consumed = _selected_evidence(root, queries)
    compound_frame = compound_table(reconcile_compounds(selected, snapshots))
    annotations: list[Annotation] = []
    for cid, snapshot in by_cid.items():
        if snapshot["metadata"]["toxicity_status"] != "found":
            continue
        annotations.extend(flatten_sections(
            snapshot["toxicity"], cid = cid,
            raw_file = str(compound_path(root, cid, "toxicity")),
            retrieved_at = snapshot["metadata"]["retrieved_at"],
        ))
    annotation_frame = annotation_table(annotations)
    measurements = normalize_rows(annotation_frame, compound_frame)
    coverage, coverage_by_group = coverage_tables(compound_frame, measurements, definitions)
    records = comparison_records(measurements, definitions)
    summaries = compound_summaries(records)
    groups = group_summaries(summaries, compound_frame, definitions)
    audit = extraction_audit(compound_frame, annotation_frame, measurements, records)
    queue = review_queue(measurements)
    tables = {
        "compounds": compound_frame,
        "annotations": annotation_frame,
        "measurements": measurements,
        "coverage": coverage,
        "coverage_by_group": coverage_by_group,
        "comparison_records": records,
        "compound_summary": summaries,
        "group_summary": groups,
        "audit": audit,
        "review_queue": queue,
    }
    return OfflineAnalysis(tables = tables, dependencies = _hash_paths(consumed))
