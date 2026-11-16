"""Atomic JSON writes and explicit PubChem storage paths."""

import json
import os
from pathlib import Path

import pytest

from agrotox.inputs import query_key
from agrotox.storage import complete_record, compound_path, query_path, read_snapshot, write_json


def test_json_round_trip_creates_parents_and_preserves_unicode(tmp_path):
    path = tmp_path / "nested" / "data.json"
    payload = {"text": "µg, μg, α", "values": [None, True, 2.5], "nested": {"cid": 101}}
    write_json(path, payload)
    assert json.loads(path.read_text(encoding = "utf-8")) == payload
    assert "µg, μg, α" in path.read_text(encoding = "utf-8")
    assert list(path.parent.iterdir()) == [path]


def test_replacement_publishes_complete_json_using_unique_sibling_files(tmp_path, monkeypatch):
    path = tmp_path / "data.json"
    write_json(path, {"version": 0})
    replace = os.replace
    temporary_paths = []

    def inspect_replace(source, destination):
        source, destination = Path(source), Path(destination)
        assert source.parent == destination.parent == path.parent
        assert source != destination
        assert source not in temporary_paths
        current = len(temporary_paths)
        assert json.loads(destination.read_text()) == {"version": current}
        assert json.loads(source.read_text()) == {"version": current + 1}
        temporary_paths.append(source)
        replace(source, destination)

    monkeypatch.setattr(os, "replace", inspect_replace)
    write_json(path, {"version": 1})
    write_json(path, {"version": 2})
    assert json.loads(path.read_text()) == {"version": 2}
    assert len(temporary_paths) == 2
    assert list(tmp_path.iterdir()) == [path]


@pytest.fixture
def cached_bundle(tmp_path):
    write_json(query_path(tmp_path, "alpha"), {"query": "Alpha", "cid": 101})
    write_json(compound_path(tmp_path, 101, "properties"), {
        "PropertyTable": {"Properties": [{"CID": 101, "Title": "Synthetic Alpha"}]}
    })
    write_json(compound_path(tmp_path, 101, "metadata"), {
        "cid": 101, "source": "PubChem", "retrieved_at": "2026-01-01T00:00:00Z",
        "toxicity_status": "found",
    })
    write_json(compound_path(tmp_path, 101, "toxicity"), {
        "Record": {"RecordNumber": 101, "RecordType": "CID", "Section": []}
    })
    return tmp_path


def test_found_snapshot_unwraps_properties_without_modifying_raw(cached_bundle):
    root = cached_bundle
    before = {path: path.read_bytes() for path in root.rglob("*.json")}
    snapshot = read_snapshot(root, " ALPHA ")
    assert snapshot["cid"] == 101
    assert snapshot["properties"] == {"CID": 101, "Title": "Synthetic Alpha"}
    assert snapshot["toxicity"]["Record"]["RecordNumber"] == 101
    assert snapshot["metadata"]["toxicity_status"] == "found"
    assert complete_record(root, 101)
    assert {path: path.read_bytes() for path in root.rglob("*.json")} == before


def test_missing_section_is_complete(cached_bundle):
    root = cached_bundle
    metadata_path = compound_path(root, 101, "metadata")
    metadata = json.loads(metadata_path.read_text())
    metadata["toxicity_status"] = "missing"
    write_json(metadata_path, metadata)
    write_json(compound_path(root, 101, "toxicity"), {"missing_section": "Toxicity"})
    assert complete_record(root, 101)
    assert read_snapshot(root, "alpha")["toxicity"] == {"missing_section": "Toxicity"}


@pytest.mark.parametrize("old_toxicity", ["valid", "corrupt", "absent"])
def test_pending_hides_old_toxicity(cached_bundle, old_toxicity):
    root = cached_bundle
    path = compound_path(root, 101, "metadata")
    metadata = json.loads(path.read_text())
    metadata["toxicity_status"] = "pending"
    write_json(path, metadata)
    toxicity_path = compound_path(root, 101, "toxicity")
    if old_toxicity == "corrupt":
        toxicity_path.write_text("{truncated", encoding = "utf-8")
    elif old_toxicity == "absent":
        toxicity_path.unlink()
    snapshot = read_snapshot(root, "alpha")
    assert snapshot["properties"]["CID"] == 101
    assert snapshot["toxicity"] is None
    assert not complete_record(root, 101)


def test_absent_alias_is_unresolved_and_completion_is_alias_independent(cached_bundle):
    root = cached_bundle
    assert read_snapshot(root, "unknown") is None
    query_path(root, "alpha").unlink()
    assert read_snapshot(root, "alpha") is None
    assert complete_record(root, 101)
    assert not complete_record(root, 102)


@pytest.mark.parametrize("component", ["properties", "metadata", "toxicity"])
@pytest.mark.parametrize("damage", ["absent", "truncated", "not-object", "invalid-utf8"])
def test_damaged_bundle_is_not_complete(cached_bundle, component, damage):
    path = compound_path(cached_bundle, 101, component)
    if damage == "absent":
        path.unlink()
    else:
        path.write_bytes({"truncated": b"{", "not-object": b"[]", "invalid-utf8": b"\xff"}[damage])
    assert not complete_record(cached_bundle, 101)
    with pytest.raises(ValueError):
        read_snapshot(cached_bundle, "alpha")


@pytest.mark.parametrize("component, payload", [
    ("properties", {"PropertyTable": {"Properties": []}}),
    ("properties", {"PropertyTable": {"Properties": [{"CID": 101}, {"CID": 101}]}}),
    ("properties", {"PropertyTable": {"Properties": [{"CID": 102}]}}),
    ("properties", {"PropertyTable": {"Properties": [{"CID": True}]}}),
    ("properties", {"CID": 101}),
    ("toxicity", {"Record": {"RecordNumber": 102, "RecordType": "CID", "Section": []}}),
    ("toxicity", {"Record": {"RecordNumber": 101, "RecordType": "SID", "Section": []}}),
    ("toxicity", {"Record": {"Section": []}}),
    ("toxicity", {"Record": {"RecordNumber": 101, "RecordType": "CID", "Section": "bad"}}),
    ("toxicity", {"missing_section": "Toxicity"}),
    ("toxicity", {"Fault": {"Message": "remote failure"}}),
])
def test_invalid_envelopes_and_status_payload_mismatches(cached_bundle, component, payload):
    write_json(compound_path(cached_bundle, 101, component), payload)
    assert not complete_record(cached_bundle, 101)
    with pytest.raises(ValueError):
        read_snapshot(cached_bundle, "alpha")


@pytest.mark.parametrize("field, value", [
    ("cid", 102), ("cid", "101"), ("toxicity_status", "not_retrieved"),
    ("source", "other"), ("retrieved_at", "invalid"),
    ("retrieved_at", "2026-01-01T00:00:00"),
])
def test_invalid_metadata(cached_bundle, field, value):
    path = compound_path(cached_bundle, 101, "metadata")
    metadata = json.loads(path.read_text())
    metadata[field] = value
    write_json(path, metadata)
    assert not complete_record(cached_bundle, 101)
    with pytest.raises(ValueError):
        read_snapshot(cached_bundle, "alpha")


@pytest.mark.parametrize("payload", [
    {"query": "beta", "cid": 101}, {"query": "alpha", "cid": 0},
    {"query": "alpha", "cid": "101"}, {"cid": 101}, [],
])
def test_corrupt_alias_raises(cached_bundle, payload):
    write_json(query_path(cached_bundle, "alpha"), payload)
    with pytest.raises(ValueError):
        read_snapshot(cached_bundle, "alpha")


def test_missing_status_cannot_publish_found_payload(cached_bundle):
    path = compound_path(cached_bundle, 101, "metadata")
    metadata = json.loads(path.read_text())
    metadata["toxicity_status"] = "missing"
    write_json(path, metadata)
    assert not complete_record(cached_bundle, 101)
    with pytest.raises(ValueError):
        read_snapshot(cached_bundle, "alpha")


@pytest.mark.parametrize("field", ["cid", "source", "retrieved_at", "toxicity_status"])
def test_required_metadata_fields(cached_bundle, field):
    path = compound_path(cached_bundle, 101, "metadata")
    metadata = json.loads(path.read_text())
    del metadata[field]
    write_json(path, metadata)
    assert not complete_record(cached_bundle, 101)
    with pytest.raises(ValueError):
        read_snapshot(cached_bundle, "alpha")


@pytest.mark.parametrize("content", ["{", "NaN", '{"query":"alpha","cid":NaN}'])
def test_invalid_alias_json(cached_bundle, content):
    query_path(cached_bundle, "alpha").write_text(content, encoding = "utf-8")
    with pytest.raises(ValueError):
        read_snapshot(cached_bundle, "alpha")


def test_numeric_alias_cannot_resolve_to_a_different_cid(cached_bundle):
    write_json(query_path(cached_bundle, "102"), {"query": "00102", "cid": 101})
    with pytest.raises(ValueError, match = "CID"):
        read_snapshot(cached_bundle, "102")


def test_first_fetch_interrupted_between_properties_and_metadata(cached_bundle):
    compound_path(cached_bundle, 101, "metadata").unlink()
    assert not complete_record(cached_bundle, 101)
    with pytest.raises(ValueError, match = "Incomplete bundle"):
        read_snapshot(cached_bundle, "alpha")


def test_readers_do_not_hide_permission_errors(cached_bundle, monkeypatch):
    def denied(*args, **kwargs):
        raise PermissionError("simulated permission error")

    monkeypatch.setattr(Path, "read_text", denied)
    with pytest.raises(PermissionError):
        complete_record(cached_bundle, 101)
    with pytest.raises(PermissionError):
        read_snapshot(cached_bundle, "alpha")


@pytest.mark.parametrize("existing", [False, True])
def test_failed_replacement_preserves_destination_and_cleans_temporary_file(
    tmp_path, monkeypatch, existing
):
    path = tmp_path / "data.json"
    if existing:
        write_json(path, {"value": "µg"})
    before = path.read_bytes() if existing else None

    def fail(*args, **kwargs):
        raise OSError("simulated replacement failure")

    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(OSError, match = "simulated replacement failure"):
        write_json(path, {"value": "new"})
    assert (path.read_bytes() if path.exists() else None) == before
    assert set(tmp_path.iterdir()) == ({path} if existing else set())


@pytest.mark.parametrize("payload, error", [
    ({"bad": object()}, TypeError),
    ({"bad": float("nan")}, ValueError),
    ({"bad": float("inf")}, ValueError),
])
def test_serialization_failure_preserves_existing_file(tmp_path, payload, error):
    path = tmp_path / "data.json"
    write_json(path, {"original": True})
    before = path.read_bytes()
    with pytest.raises(error):
        write_json(path, payload)
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]


def test_paths_use_explicit_root_without_creating_directories(tmp_path, monkeypatch):
    root = tmp_path / "selected-data"
    monkeypatch.chdir(tmp_path)
    assert query_path(root, " Alpha ") == root / "raw/pubchem/queries" / f"{query_key('alpha')}.json"
    for component in ["properties", "toxicity", "metadata"]:
        assert compound_path(root, 101, component) == root / "raw/pubchem/101" / f"{component}.json"
    assert not root.exists()


@pytest.mark.parametrize("cid", [None, 0, -1, True, "101"])
def test_compound_paths_reject_invalid_cids(tmp_path, cid):
    with pytest.raises(ValueError, match = "CID"):
        compound_path(tmp_path, cid, "properties")


def test_compound_paths_reject_unknown_components(tmp_path):
    with pytest.raises(ValueError, match = "component"):
        compound_path(tmp_path, 101, "../escape")


@pytest.mark.parametrize("stage", ["write", "flush"])
def test_io_failure_preserves_existing_file(tmp_path, monkeypatch, stage):
    path = tmp_path / "data.json"
    write_json(path, {"original": True})
    before = path.read_bytes()

    def fail_write(payload, stream, **kwargs):
        stream.write('{"partial":')
        raise OSError("simulated write failure")

    def fail_flush(*args):
        raise OSError("simulated flush failure")

    if stage == "write":
        monkeypatch.setattr(json, "dump", fail_write)
    else:
        monkeypatch.setattr(os, "fsync", fail_flush)
    with pytest.raises(OSError, match = f"simulated {stage} failure"):
        write_json(path, {"value": "new"})
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]
