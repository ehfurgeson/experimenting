"""Resumable retrieval and refresh recovery using synthetic sources."""

import json
import runpy
import sys
from pathlib import Path

import pytest
import requests

from agrotox import retrieval
from agrotox.retrieval import fetch_batch, fetch_one
from agrotox.storage import complete_record, compound_path, query_path, read_snapshot


class FakeSource:
    def __init__(self, cid = 101, failure = None, missing = False):
        self.cid = cid
        self.failure = failure
        self.missing = missing
        self.calls = []

    def resolve(self, query):
        self.calls.append(("resolve", query))
        if self.failure == "resolve":
            raise LookupError("synthetic unresolved query")
        return self.cid

    def properties(self, cid):
        self.calls.append(("properties", cid))
        if self.failure == "properties":
            raise requests.ConnectionError("synthetic property failure")
        return {"PropertyTable": {"Properties": [{"CID": cid, "Title": "Synthetic Alpha"}]}}

    def toxicity(self, cid):
        self.calls.append(("toxicity", cid))
        if self.failure == "toxicity":
            raise requests.Timeout("synthetic toxicity failure")
        if self.missing:
            return None
        return {"Record": {"RecordNumber": cid, "RecordType": "CID", "Section": []}}


@pytest.mark.parametrize("failure", [None, "resolve"])
def test_fetch_example_reports_outcomes_and_exit_status(tmp_path, monkeypatch, capsys, failure):
    from agrotox.sources import pubchem

    source = FakeSource(failure = failure)
    monkeypatch.setattr(pubchem, "PubChemClient", lambda: source)
    example = Path(__file__).resolve().parents[1] / "examples" / "fetch_snapshots.py"
    monkeypatch.setattr(sys, "argv", [str(example), "--data", str(tmp_path), "alpha"])
    if failure:
        with pytest.raises(SystemExit) as error:
            runpy.run_path(str(example), run_name = "__main__")
        assert error.value.code == 1
        assert json.loads(capsys.readouterr().out)["status"] == "error"
    else:
        runpy.run_path(str(example), run_name = "__main__")
        assert json.loads(capsys.readouterr().out)["status"] == "fetched"
        source.calls.clear()
        runpy.run_path(str(example), run_name = "__main__")
        assert json.loads(capsys.readouterr().out)["status"] == "skipped"
        assert not source.calls


def test_complete_cache_reuse_preserves_bundle_and_updates_alias_metadata(tmp_path):
    source = FakeSource()
    query = {"query": "Alpha", "chemical_group": "h"}
    assert fetch_one(source, tmp_path, query)["status"] == "fetched"
    before = {path: path.read_bytes() for path in (tmp_path / "raw/pubchem/101").iterdir()}
    outcome = fetch_one(source, tmp_path, {"query": "alpha", "chemical_group": "h", "subgroup": "s"})
    assert outcome["status"] == "skipped"
    assert outcome["cid"] == 101
    assert len(source.calls) == 3
    assert {path: path.read_bytes() for path in before} == before
    alias = json.loads(query_path(tmp_path, "alpha").read_text())
    assert alias["query"] == "Alpha"
    assert alias["input_metadata"]["subgroup"] == "s"


def test_shared_cid_aliases_do_not_refetch_bundle(tmp_path):
    source = FakeSource()
    outcomes = fetch_batch(source, tmp_path, [{"query": "alpha"}, {"query": "101"}])
    assert [outcome["status"] for outcome in outcomes] == ["fetched", "skipped"]
    assert [call[0] for call in source.calls].count("properties") == 1
    assert [call[0] for call in source.calls].count("toxicity") == 1
    assert read_snapshot(tmp_path, "101")["cid"] == 101


def test_missing_section_is_cached_as_observed_absence(tmp_path):
    source = FakeSource(missing = True)
    assert fetch_one(source, tmp_path, {"query": "alpha"})["status"] == "fetched"
    assert read_snapshot(tmp_path, "alpha")["toxicity"] == {"missing_section": "Toxicity"}
    assert complete_record(tmp_path, 101)
    assert fetch_one(source, tmp_path, {"query": "alpha"})["status"] == "skipped"
    assert len(source.calls) == 3


def test_failed_toxicity_preserves_identity_and_resume_uses_it(tmp_path):
    source = FakeSource(failure = "toxicity")
    outcome = fetch_one(source, tmp_path, {"query": "alpha"})
    assert outcome == {
        "query": "alpha", "cid": 101, "status": "error", "stage": "toxicity",
        "error_type": "Timeout", "message": "synthetic toxicity failure",
    }
    snapshot = read_snapshot(tmp_path, "alpha")
    assert snapshot["properties"]["CID"] == 101
    assert snapshot["toxicity"] is None
    assert not complete_record(tmp_path, 101)
    source.failure = None
    source.calls.clear()
    assert fetch_one(source, tmp_path, {"query": "alpha"})["status"] == "fetched"
    assert source.calls == [("toxicity", 101)]


def test_failed_force_refresh_hides_old_toxicity(tmp_path):
    source = FakeSource()
    fetch_one(source, tmp_path, {"query": "alpha"})
    toxicity = compound_path(tmp_path, 101, "toxicity")
    before = toxicity.read_bytes()
    source.failure = "toxicity"
    assert fetch_one(source, tmp_path, {"query": "alpha"}, force = True)["status"] == "error"
    assert toxicity.read_bytes() == before
    assert read_snapshot(tmp_path, "alpha")["toxicity"] is None
    assert not complete_record(tmp_path, 101)


def test_force_reresolves_name_and_can_change_cid(tmp_path):
    source = FakeSource()
    fetch_one(source, tmp_path, {"query": "alpha"})
    source.cid = 102
    source.calls.clear()
    outcome = fetch_one(source, tmp_path, {"query": "alpha"}, force = True)
    assert outcome["cid"] == 102
    assert outcome["status"] == "fetched"
    assert source.calls == [("resolve", "alpha"), ("properties", 102), ("toxicity", 102)]
    assert read_snapshot(tmp_path, "alpha")["cid"] == 102
    assert complete_record(tmp_path, 101)


@pytest.mark.parametrize("component", ["properties", "metadata", "toxicity", "alias"])
def test_corrupt_cache_is_repaired(tmp_path, component):
    source = FakeSource()
    fetch_one(source, tmp_path, {"query": "alpha"})
    path = query_path(tmp_path, "alpha") if component == "alias" else compound_path(tmp_path, 101, component)
    path.write_text("{broken", encoding = "utf-8")
    assert fetch_one(source, tmp_path, {"query": "alpha"})["status"] in {"fetched", "skipped"}
    assert complete_record(tmp_path, 101)
    assert read_snapshot(tmp_path, "alpha")["properties"]["CID"] == 101


def test_batch_continues_after_remote_failure(tmp_path):
    class MixedSource(FakeSource):
        def resolve(self, query):
            if query == "bad":
                raise LookupError("unresolved")
            return super().resolve(query)

    outcomes = fetch_batch(MixedSource(), tmp_path, [{"query": "bad"}, {"query": "alpha"}])
    assert [outcome["status"] for outcome in outcomes] == ["error", "fetched"]
    assert outcomes[0]["stage"] == "resolve"
    assert outcomes[0]["cid"] is None
    assert read_snapshot(tmp_path, "alpha")["cid"] == 101


@pytest.mark.parametrize("stage", ["pending", "properties_write", "alias", "toxicity_write", "complete"])
def test_refresh_write_failure_is_recoverable(tmp_path, monkeypatch, stage):
    source = FakeSource()
    fetch_one(source, tmp_path, {"query": "alpha"})
    before = read_snapshot(tmp_path, "alpha")
    writer = retrieval.write_json

    def failing_write(path, payload):
        write_stage = {
            "properties.json": "properties_write", "toxicity.json": "toxicity_write",
        }.get(path.name, "alias")
        if path.name == "metadata.json":
            write_stage = "pending" if payload["toxicity_status"] == "pending" else "complete"
        if write_stage == stage:
            if stage == "properties_write":
                assert read_snapshot(tmp_path, "alpha")["toxicity"] is None
            raise OSError(f"synthetic {stage} failure")
        writer(path, payload)

    monkeypatch.setattr(retrieval, "write_json", failing_write)
    outcome = fetch_one(source, tmp_path, {"query": "alpha"}, force = True)
    assert outcome["status"] == "error"
    assert outcome["stage"] == stage
    assert outcome["error_type"] == "OSError"
    if stage == "pending":
        assert read_snapshot(tmp_path, "alpha") == before
    else:
        assert read_snapshot(tmp_path, "alpha")["toxicity"] is None
        assert not complete_record(tmp_path, 101)
    monkeypatch.setattr(retrieval, "write_json", writer)
    assert fetch_one(source, tmp_path, {"query": "alpha"})["status"] in {"fetched", "skipped"}
    assert complete_record(tmp_path, 101)


def test_invalid_batch_fails_before_requests_or_files(tmp_path):
    source = FakeSource()
    with pytest.raises(ValueError):
        fetch_batch(source, tmp_path, [
            {"query": "Alpha", "chemical_group": "h"},
            {"query": "alpha", "chemical_group": "n"},
        ])
    assert source.calls == []
    assert list(tmp_path.iterdir()) == []


def test_empty_batch_and_equivalent_inputs(tmp_path):
    source = FakeSource()
    assert fetch_batch(source, tmp_path, []) == []
    outcomes = fetch_batch(source, tmp_path, [{"query": "Alpha"}, {"query": " alpha "}])
    assert len(outcomes) == 1
    assert outcomes[0]["query"] == "Alpha"


@pytest.mark.parametrize("failure", ["resolve", "properties"])
def test_early_source_failure_has_stage_and_no_false_completion(tmp_path, failure):
    outcome = fetch_one(FakeSource(failure = failure), tmp_path, {"query": "alpha"})
    assert outcome["status"] == "error"
    assert outcome["stage"] == failure
    assert outcome["cid"] == (None if failure == "resolve" else 101)
    assert read_snapshot(tmp_path, "alpha") is None
    assert not complete_record(tmp_path, 101)


def test_property_failure_before_refresh_publication_preserves_previous_snapshot(tmp_path):
    source = FakeSource()
    fetch_one(source, tmp_path, {"query": "alpha"})
    before = read_snapshot(tmp_path, "alpha")
    source.failure = "properties"
    outcome = fetch_one(source, tmp_path, {"query": "alpha"}, force = True)
    assert outcome["stage"] == "properties"
    assert read_snapshot(tmp_path, "alpha") == before


def test_batch_continues_after_a_storage_failure(tmp_path, monkeypatch):
    writer = retrieval.write_json
    failed = False

    def fail_once(path, payload):
        nonlocal failed
        if not failed:
            failed = True
            raise OSError("synthetic storage failure")
        writer(path, payload)

    monkeypatch.setattr(retrieval, "write_json", fail_once)
    outcomes = fetch_batch(FakeSource(), tmp_path, [{"query": "alpha"}, {"query": "beta"}])
    assert [outcome["status"] for outcome in outcomes] == ["error", "fetched"]
    assert outcomes[0]["stage"] == "pending"


@pytest.mark.parametrize("method", ["properties", "toxicity"])
def test_malformed_source_payload_does_not_publish_completion(tmp_path, method):
    source = FakeSource()
    setattr(source, method, lambda cid: {})
    outcome = fetch_one(source, tmp_path, {"query": "alpha"})
    assert outcome["status"] == "error"
    assert outcome["stage"] == method
    assert not complete_record(tmp_path, 101)


def test_numeric_query_cannot_save_a_wrong_resolved_cid(tmp_path):
    outcome = fetch_one(FakeSource(cid = 102), tmp_path, {"query": "101"})
    assert outcome["status"] == "error"
    assert outcome["stage"] == "resolve"
    assert list(tmp_path.iterdir()) == []


def test_cache_permission_failure_is_reported_without_remote_repair(tmp_path, monkeypatch):
    source = FakeSource()

    def denied(*args):
        raise PermissionError("synthetic cache permission failure")

    monkeypatch.setattr(retrieval, "read_alias", denied)
    outcome = fetch_one(source, tmp_path, {"query": "alpha"})
    assert outcome["status"] == "error"
    assert outcome["stage"] == "cache"
    assert outcome["error_type"] == "PermissionError"
    assert source.calls == []
