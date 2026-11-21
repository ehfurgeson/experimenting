"""Deterministic offline composition of every analysis table."""

import hashlib
from pathlib import Path

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from agrotox.storage import compound_path, query_path, write_json
from agrotox.workflow import TABLE_NAMES, build_offline

DEFINITIONS = {
    "mammal_oral_ld50": {
        "endpoint": "LD50", "organism_group": "mammal", "preferred_route": "oral",
        "standard_unit": "mg/kg",
    },
}


def test_offline_workflow_composes_every_table(snapshot_cache, curated_queries):
    analysis = build_offline(snapshot_cache, curated_queries, DEFINITIONS)
    assert set(analysis.tables) == set(TABLE_NAMES)
    tables = analysis.tables
    assert tables["compounds"].height == 4
    assert tables["annotations"].height == 7
    assert tables["measurements"].height == 7
    assert tables["review_queue"].height == 2
    assert tables["comparison_records"].height == 4
    assert tables["coverage"].height == 4
    assert tables["audit"].height == 4


def test_group_descriptions_weight_compounds(snapshot_cache, curated_queries):
    tables = build_offline(snapshot_cache, curated_queries, DEFINITIONS).tables
    summary = tables["group_summary"].filter(
        pl.col("comparison") == "mammal_oral_ld50"
    )
    herbicide = summary.filter(pl.col("chemical_group") == "herbicide").row(0, named = True)
    natural = summary.filter(pl.col("chemical_group") == "natural_product").row(0, named = True)
    assert herbicide["total_compounds"] == 1
    assert herbicide["median_of_compound_exact_medians"] == 2000.0
    assert natural["total_compounds"] == 3
    assert natural["compounds_with_data"] == 1
    assert natural["median_of_compound_exact_medians"] == 10000.0


def test_reruns_produce_identical_tables(snapshot_cache, curated_queries):
    first = build_offline(snapshot_cache, curated_queries, DEFINITIONS)
    second = build_offline(snapshot_cache, curated_queries, DEFINITIONS)
    for name in TABLE_NAMES:
        assert_frame_equal(first.tables[name], second.tables[name])
    assert first.dependencies == second.dependencies


def test_raw_evidence_is_not_modified(snapshot_cache, curated_queries):
    before = {
        path: path.read_bytes()
        for path in sorted(snapshot_cache.rglob("*.json"))
    }
    analysis = build_offline(snapshot_cache, curated_queries, DEFINITIONS)
    after = {path: path.read_bytes() for path in sorted(snapshot_cache.rglob("*.json"))}
    assert after == before
    for path, digest in analysis.dependencies.items():
        with open(path, "rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == digest


def test_dependencies_cover_the_selected_evidence(snapshot_cache, curated_queries):
    analysis = build_offline(snapshot_cache, curated_queries, DEFINITIONS)
    names = {Path(path).name for path in analysis.dependencies}
    assert "properties.json" in names
    assert "metadata.json" in names
    assert "toxicity.json" in names
    aliases = [path for path in analysis.dependencies if "queries" in Path(path).parts]
    assert len(aliases) == 3
    # The unresolved query has no alias and therefore no consumed file.
    assert len(analysis.dependencies) == 12


def test_aliases_do_not_change_the_compound_universe(snapshot_cache, curated_queries):
    before = build_offline(snapshot_cache, curated_queries, DEFINITIONS)
    write_json(query_path(snapshot_cache, "101"), {"query": "101", "cid": 101})
    after = build_offline(snapshot_cache, [*curated_queries, {"query": "101"}], DEFINITIONS)
    assert after.tables["compounds"].height == before.tables["compounds"].height
    assert after.tables["annotations"].height == before.tables["annotations"].height
    assert after.tables["comparison_records"].height == before.tables["comparison_records"].height
    assert after.tables["compounds"]["input_queries"].to_list() == [
        ["alpha", "101"], ["beta"], ["gamma"], ["unknown"],
    ]


def test_unselected_cached_records_do_not_leak(snapshot_cache, curated_queries):
    before = build_offline(snapshot_cache, curated_queries, DEFINITIONS)
    write_json(query_path(snapshot_cache, "999"), {"query": "999", "cid": 999})
    write_json(compound_path(snapshot_cache, 999, "properties"), {
        "PropertyTable": {"Properties": [{"CID": 999, "Title": "Unselected"}]},
    })
    write_json(compound_path(snapshot_cache, 999, "metadata"), {
        "cid": 999, "source": "PubChem", "retrieved_at": "2026-01-01T00:00:00Z",
        "toxicity_status": "found",
    })
    write_json(compound_path(snapshot_cache, 999, "toxicity"),
               {"Record": {"RecordNumber": 999, "RecordType": "CID", "Section": []}})
    after = build_offline(snapshot_cache, curated_queries, DEFINITIONS)
    assert_frame_equal(after.tables["compounds"], before.tables["compounds"])
    assert_frame_equal(after.tables["annotations"], before.tables["annotations"])
    assert "999" not in " ".join(after.tables["compounds"]["compound_id"].to_list())


def test_a_selection_without_evidence_gives_typed_empty_tables(snapshot_cache, curated_queries):
    analysis = build_offline(snapshot_cache, [{"query": "not-selected"}], DEFINITIONS)
    for name in ("annotations", "measurements", "comparison_records", "compound_summary",
                 "review_queue"):
        assert analysis.tables[name].height == 0, name
    # The selected query still belongs to the compound universe.
    assert analysis.tables["compounds"].height == 1
    assert analysis.tables["compounds"]["resolution_status"].to_list() == ["unresolved"]
    assert analysis.tables["audit"]["availability_reason"].to_list() == ["unresolved_query"]
    assert analysis.tables["compounds"].schema["compound_id"] == pl.String
    assert analysis.tables["measurements"].schema["value_standardized"] == pl.Float64
    assert analysis.tables["comparison_records"].schema["support_ids"] == pl.List(pl.String)
    assert analysis.dependencies == {}


def test_the_workflow_makes_no_network_request(snapshot_cache, curated_queries, monkeypatch):
    import requests

    def blocked(*args, **kwargs):
        raise AssertionError("The offline workflow must not use the network")

    monkeypatch.setattr(requests.sessions.Session, "request", blocked)
    analysis = build_offline(snapshot_cache, curated_queries, DEFINITIONS)
    assert analysis.tables["compounds"].height == 4


def test_invalid_definitions_are_rejected(snapshot_cache, curated_queries):
    with pytest.raises(ValueError):
        build_offline(snapshot_cache, curated_queries, {"bad": {"endpoint": "UNKNOWN"}})
