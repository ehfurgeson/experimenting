"""Selected cached snapshots compose into stable, typed ingestion tables."""

import hashlib
import json
import runpy
import sys
from pathlib import Path

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from agrotox.storage import compound_path, query_path, write_json
from agrotox.tables import ANNOTATION_SCHEMA, COMPOUND_SCHEMA, read_table
from agrotox.workflow import parse_snapshots


def raw_hashes(root):
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (root / "raw").rglob("*.json")
    }


def test_synthetic_ingestion_retains_compound_universe_and_raw_evidence(
    snapshot_cache, curated_queries
):
    before = raw_hashes(snapshot_cache)
    annotations, compounds = parse_snapshots(snapshot_cache, curated_queries)
    assert annotations.height == 7
    assert compounds.height == 4
    assert annotations.schema == ANNOTATION_SCHEMA
    assert compounds.schema == COMPOUND_SCHEMA
    assert compounds["input_queries"].to_list() == [["alpha"], ["beta"], ["gamma"], ["unknown"]]
    assert compounds["toxicity_status"].to_list() == ["found", "found", "missing", "not_retrieved"]
    assert compounds["resolution_status"].to_list() == ["resolved", "resolved", "resolved", "unresolved"]
    assert compounds.filter(pl.col("chemical_group") == "natural_product").height == 3
    assert annotations["compound_id"].to_list().count("PUBCHEM:101") == 6
    assert raw_hashes(snapshot_cache) == before
    repeated = parse_snapshots(snapshot_cache, curated_queries)
    assert_frame_equal(repeated[0], annotations)
    assert_frame_equal(repeated[1], compounds)


def test_alias_does_not_duplicate_annotations_or_reread_cid_bundle(
    snapshot_cache, curated_queries, monkeypatch
):
    expected, _ = parse_snapshots(snapshot_cache, curated_queries)
    write_json(query_path(snapshot_cache, "101"), {"query": "101", "cid": 101})
    reads = []
    read_text = Path.read_text

    def observe(path, *args, **kwargs):
        reads.append(path)
        return read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", observe)
    annotations, compounds = parse_snapshots(snapshot_cache, [
        *curated_queries, {"query": "101", "chemical_group": "herbicide"},
    ])
    assert_frame_equal(annotations, expected)
    assert compounds.height == 4
    assert compounds["input_queries"][0].to_list() == ["alpha", "101"]
    for component in ["properties", "metadata", "toxicity"]:
        assert reads.count(compound_path(snapshot_cache, 101, component)) == 1


def test_selection_never_reads_unrelated_cache(snapshot_cache, curated_queries):
    # A corrupt unrelated alias would raise if the workflow scanned all caches.
    path = query_path(snapshot_cache, "unrelated")
    path.write_text("{broken", encoding = "utf-8")
    annotations, compounds = parse_snapshots(snapshot_cache, curated_queries[:1])
    assert annotations.height == 6
    assert compounds["pubchem_cid"].to_list() == [101]


def test_pending_identity_survives_but_stale_toxicity_is_not_parsed(
    snapshot_cache, curated_queries
):
    path = compound_path(snapshot_cache, 101, "metadata")
    metadata = json.loads(path.read_text())
    metadata["toxicity_status"] = "pending"
    write_json(path, metadata)
    compound_path(snapshot_cache, 101, "toxicity").write_text("{stale", encoding = "utf-8")
    annotations, compounds = parse_snapshots(snapshot_cache, curated_queries)
    assert annotations.height == 1
    assert annotations["compound_id"].to_list() == ["PUBCHEM:102"]
    assert compounds["toxicity_status"].to_list() == ["pending", "found", "missing", "not_retrieved"]
    assert compounds["pubchem_cid"].to_list() == [101, 102, 103, None]


def test_empty_selection_is_typed_and_does_not_inspect_cache(tmp_path):
    annotations, compounds = parse_snapshots(tmp_path / "absent", [])
    assert annotations.height == compounds.height == 0
    assert annotations.schema == ANNOTATION_SCHEMA
    assert compounds.schema == COMPOUND_SCHEMA
    assert not (tmp_path / "absent").exists()


def test_missing_alias_stays_unresolved_even_if_cid_bundle_exists(snapshot_cache):
    annotations, compounds = parse_snapshots(snapshot_cache, [{"query": "101"}])
    assert annotations.is_empty()
    assert compounds["resolution_status"].to_list() == ["unresolved"]
    assert compounds["pubchem_cid"].to_list() == [None]


@pytest.mark.parametrize("component", ["alias", "properties", "toxicity"])
def test_selected_corruption_is_visible(snapshot_cache, curated_queries, component):
    path = query_path(snapshot_cache, "alpha") if component == "alias" else compound_path(snapshot_cache, 101, component)
    path.write_text("{broken", encoding = "utf-8")
    with pytest.raises(ValueError):
        parse_snapshots(snapshot_cache, curated_queries)


def test_conflicting_resolved_alias_labels_are_not_arbitrarily_selected(snapshot_cache):
    write_json(query_path(snapshot_cache, "101"), {"query": "101", "cid": 101})
    with pytest.raises(ValueError, match = "chemical_group"):
        parse_snapshots(snapshot_cache, [
            {"query": "alpha", "chemical_group": "h"},
            {"query": "101", "chemical_group": "n"},
        ])


def test_ingestion_tables_round_trip_with_nested_provenance(snapshot_cache, curated_queries):
    annotations, compounds = parse_snapshots(snapshot_cache, curated_queries)
    for name, frame in [("annotations", annotations), ("compounds", compounds)]:
        path = snapshot_cache / f"{name}.parquet"
        frame.write_parquet(path)
        assert_frame_equal(read_table(path, frame.schema), frame)
    assert annotations.schema["sources"].inner == pl.Struct({
        "reference_number": pl.Int64, "source_name": pl.String, "source_url": pl.String,
        "reference_json": pl.String,
    })


def test_found_empty_sections_and_missing_sections_keep_compounds(snapshot_cache):
    write_json(compound_path(snapshot_cache, 101, "toxicity"), {
        "Record": {"RecordNumber": 101, "RecordType": "CID", "Section": []},
    })
    annotations, compounds = parse_snapshots(snapshot_cache, [{"query": "alpha"}, {"query": "gamma"}])
    assert annotations.is_empty()
    assert annotations.schema == ANNOTATION_SCHEMA
    assert compounds["toxicity_status"].to_list() == ["found", "missing"]


def test_selected_curated_labels_are_used_instead_of_saved_alias_metadata(snapshot_cache):
    write_json(query_path(snapshot_cache, "alpha"), {
        "query": "alpha", "cid": 101,
        "input_metadata": {"query": "alpha", "chemical_group": "old label"},
    })
    _, compounds = parse_snapshots(snapshot_cache, [{"query": "alpha", "chemical_group": "current label"}])
    assert compounds["chemical_group"].to_list() == ["current label"]


def test_runnable_example_composes_selected_snapshots_offline(snapshot_cache, monkeypatch, capsys):
    before = raw_hashes(snapshot_cache)
    example = Path(__file__).resolve().parents[1] / "examples" / "inspect_snapshots.py"
    query_file = snapshot_cache / "queries.txt"
    query_file.write_text("alpha\nbeta\ngamma\n", encoding = "utf-8")
    monkeypatch.setattr(sys, "argv", [
        str(example), "--data", str(snapshot_cache), "--input", str(query_file), "unknown",
        "--definitions", str(example.parent / "endpoints.yaml"),
    ])
    runpy.run_path(str(example), run_name = "__main__")
    output = capsys.readouterr().out
    assert "Compounds: 4; annotations: 7" in output
    assert "Normalized rows: 7 (complete: 5, partial: 1, failed: 1)" in output
    assert "https://example.org/a" in output
    assert "1 g/kg" in output
    assert '"endpoint": "mammal_oral_ld50", "compounds_with_data": 2' in output
    assert '"endpoint": "trout_lc50_96h", "compounds_with_data": 1' in output
    assert '"total_compounds": 4' in output
    assert raw_hashes(snapshot_cache) == before
