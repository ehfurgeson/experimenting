"""Frozen assay review exports retain evidence without inventing labels."""

import copy
import csv
import hashlib
import json
import socket
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from labels import LABEL_FIELDS, attach_labels
from review_assays import run
from screen import prepare


def activity(identity = 1, molecule = "CHEMBL300", **changes):
    return {"activity_id": identity, "assay_chembl_id": "CHEMBL100",
            "document_chembl_id": "CHEMBL200", "molecule_chembl_id": molecule,
            "canonical_smiles": "CCO", "standard_type": "Inhibition",
            "standard_relation": "<=", "standard_value": "50.0", "standard_units": "%",
            "activity_comment": None, "unrecognized_source_field": {"retain": [1, None]},
            **changes}


def bundle(records = None):
    records = [activity()] if records is None else records
    return {"source": "ChEMBL", "retrieved_at": "2026-10-29T12:00:00+00:00",
            "status": {"chembl_db_version": "ChEMBL_test"},
            "assay": {"assay_chembl_id": "CHEMBL100", "document_chembl_id": "CHEMBL200",
                      "description": "Synthetic plant assay, 15 days", "assay_organism": "plant"},
            "document": {"document_chembl_id": "CHEMBL200", "doi": "10.1000/synthetic",
                         "title": "Synthetic source", "year": 2026},
            "activity_count": len(records), "activity_pages": [{"activities": records,
                "page_meta": {"offset": 0, "total_count": len(records)}}]}


def snapshot(tmp_path, payload, name = "CHEMBL100"):
    root = tmp_path / "snapshots"
    path = root / "raw/chembl" / f"{name}.json"
    path.parent.mkdir(parents = True, exist_ok = True)
    path.write_text(json.dumps(payload), encoding = "utf-8")
    return root, path


def read_csv(path):
    with path.open(encoding = "utf-8", newline = "") as stream:
        return list(csv.DictReader(stream))


def test_offline_export_preserves_raw_evidence_provenance_and_unknown_labels(tmp_path, monkeypatch):
    def no_network(*args, **kwargs):
        pytest.fail("Review export attempted network access")

    monkeypatch.setattr(socket, "create_connection", no_network)
    records = [activity(2, "CHEMBL301", canonical_smiles = None, standard_value = None,
                        standard_relation = None, activity_comment = "Not Determined"), activity()]
    root, source = snapshot(tmp_path, bundle(records))
    before = source.read_bytes()
    output = tmp_path / "review"
    manifest = run(root, output)
    assert source.read_bytes() == before
    assert manifest["activity_records"] == 2
    assert manifest["compounds"] == 2
    assert manifest["missing_structures"] == 1
    rows = read_csv(output / "activity_review.csv")
    assert [row["activity_id"] for row in rows] == ["1", "2"]
    assert rows[0]["standard_relation"] == "<="
    assert rows[0]["standard_value"] == "50.0"
    assert rows[0]["doi"] == "10.1000/synthetic"
    assert rows[0]["assay_description"] == "Synthetic plant assay, 15 days"
    assert rows[0]["chembl_db_version"] == "ChEMBL_test"
    assert Path(rows[0]["snapshot_path"]) == source.resolve()
    assert rows[0]["snapshot_sha256"] == hashlib.sha256(before).hexdigest()
    assert json.loads(rows[0]["raw_activity_json"]) == records[1]
    assert json.loads(rows[1]["raw_activity_json"])["standard_value"] is None
    candidates = read_csv(output / "candidates.csv")
    assert [row["compound_id"] for row in candidates] == ["CHEMBL300", "CHEMBL301"]
    assert candidates[1]["canonical_smiles"] == ""
    labels = read_csv(output / "label_review_template.csv")
    assert set(labels[0]) == LABEL_FIELDS
    attached = attach_labels(prepare(candidates), labels)
    assert all(row["activity_target"] is row["origin_target"] is None for row in attached)
    assert all(row["activity_reference"] == "" for row in labels)
    assert json.loads((output / "manifest.json").read_text()) == manifest
    for section in ("input_hashes", "code_hashes", "lock_hashes", "output_hashes"):
        for path, digest in manifest[section].items():
            assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest


def test_candidate_deduplication_enriches_only_consistent_source_identities(tmp_path):
    records = [activity(3), activity(1, canonical_smiles = None), activity(2)]
    root, _ = snapshot(tmp_path, bundle(records))
    first = tmp_path / "first"
    run(root, first)
    assert len(read_csv(first / "activity_review.csv")) == 3
    assert read_csv(first / "candidates.csv") == [{"compound_id": "CHEMBL300",
                                                  "canonical_smiles": "CCO"}]
    root, _ = snapshot(tmp_path, bundle(list(reversed(records))))
    second = tmp_path / "second"
    run(root, second)
    for name in ("candidates.csv", "label_review_template.csv"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
    # Raw input order changes its hash; scientific fields and raw records stay ordered.
    a, b = read_csv(first / "activity_review.csv"), read_csv(second / "activity_review.csv")
    assert [{k: v for k, v in row.items() if k != "snapshot_sha256"} for row in a] == [
        {k: v for k, v in row.items() if k != "snapshot_sha256"} for row in b]


@pytest.mark.parametrize("change,message", [
    ("source", "source"), ("assay", "assay"), ("document", "document"),
    ("activity_assay", "assay"), ("activity_document", "document"),
    ("count", "count"), ("duplicate", "activity_id"), ("offset", "offset"),
    ("page_total", "count"), ("empty_page", "page"), ("missing_pages", "page"),
    ("version", "version"), ("timestamp", "UTC"), ("nonutc", "UTC"),
    ("molecule", "ChEMBL ID"), ("smiles", "SMILES"), ("structure_conflict", "Conflicting"),
])
def test_invalid_snapshots_fail_before_any_exports(tmp_path, change, message):
    payload = bundle()
    if change == "source": payload["source"] = "Other"
    elif change == "assay": payload["assay"]["assay_chembl_id"] = "CHEMBL999"
    elif change == "document": payload["document"]["document_chembl_id"] = "CHEMBL999"
    elif change == "activity_assay":
        payload["activity_pages"][0]["activities"][0]["assay_chembl_id"] = "CHEMBL999"
    elif change == "activity_document":
        payload["activity_pages"][0]["activities"][0]["document_chembl_id"] = "CHEMBL999"
    elif change == "count": payload["activity_count"] = True
    elif change == "duplicate": payload = bundle([activity(), activity()])
    elif change == "offset": payload["activity_pages"][0]["page_meta"]["offset"] = True
    elif change == "page_total": payload["activity_pages"][0]["page_meta"]["total_count"] = 2
    elif change == "empty_page": payload["activity_pages"][0]["activities"] = []
    elif change == "missing_pages": payload["activity_pages"] = []
    elif change == "version": payload["status"] = {}
    elif change == "timestamp": payload["retrieved_at"] = "2026-10-29T12:00:00"
    elif change == "nonutc": payload["retrieved_at"] = "2026-10-29T12:00:00+02:00"
    elif change == "molecule": payload["activity_pages"][0]["activities"][0]["molecule_chembl_id"] = 3
    elif change == "smiles": payload["activity_pages"][0]["activities"][0]["canonical_smiles"] = 42
    elif change == "structure_conflict": payload = bundle([activity(), activity(2, canonical_smiles = "COC")])
    root, _ = snapshot(tmp_path, payload)
    output = tmp_path / "review"
    with pytest.raises(ValueError, match = message):
        run(root, output)
    assert not output.exists()


def test_multiple_assays_preserve_every_measurement_but_share_candidate_ids(tmp_path):
    root, _ = snapshot(tmp_path, bundle())
    other = bundle([activity(2)])
    other["assay"]["assay_chembl_id"] = "CHEMBL101"
    other["activity_pages"][0]["activities"][0]["assay_chembl_id"] = "CHEMBL101"
    snapshot(tmp_path, other, name = "CHEMBL101")
    manifest = run(root, tmp_path / "review")
    assert manifest["assays"] == 2 and manifest["activity_records"] == 2
    assert manifest["compounds"] == 1


@pytest.mark.parametrize("change,message", [("version", "version"), ("duplicate", "activity_id")])
def test_incompatible_snapshot_sets_are_rejected(tmp_path, change, message):
    root, _ = snapshot(tmp_path, bundle())
    other = copy.deepcopy(bundle())
    other["assay"]["assay_chembl_id"] = "CHEMBL101"
    other["activity_pages"][0]["activities"][0]["assay_chembl_id"] = "CHEMBL101"
    if change == "version":
        other["status"]["chembl_db_version"] = "Different_version"
        other["activity_pages"][0]["activities"][0]["activity_id"] = 2
    snapshot(tmp_path, other, name = "CHEMBL101")
    with pytest.raises(ValueError, match = message):
        run(root, tmp_path / "review")
    assert not (tmp_path / "review").exists()


def test_empty_assay_retains_header_only_exports_and_manifest(tmp_path):
    root, _ = snapshot(tmp_path, bundle([]))
    output = tmp_path / "review"
    manifest = run(root, output)
    assert manifest["assays"] == 1 and manifest["activity_records"] == 0
    for name in ("activity_review.csv", "candidates.csv", "label_review_template.csv"):
        assert read_csv(output / name) == []
        assert (output / name).read_text().strip()


def test_missing_snapshots_and_unsafe_outputs_do_not_modify_sources(tmp_path):
    root, source = snapshot(tmp_path, bundle())
    before = source.read_bytes()
    for output in (root, root / "review", root.parent):
        with pytest.raises(ValueError, match = "separate"):
            run(root, output)
    output = tmp_path / "review"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("keep")
    with pytest.raises(ValueError, match = "empty output"):
        run(root, output)
    assert sentinel.read_text() == "keep" and source.read_bytes() == before
    with pytest.raises(ValueError, match = "No .*snapshot"):
        run(tmp_path / "missing", tmp_path / "new")


def test_complete_multipage_snapshot_exports_every_record_once(tmp_path):
    payload = bundle([activity(1), activity(2, "CHEMBL301"), activity(3)])
    records = payload["activity_pages"][0]["activities"]
    payload["activity_pages"] = [
        {"activities": records[:2], "page_meta": {"offset": 0, "total_count": 3}},
        {"activities": records[2:], "page_meta": {"offset": 2, "total_count": 3}},
    ]
    root, _ = snapshot(tmp_path, payload)
    output = tmp_path / "review"
    manifest = run(root, output)
    assert manifest["activity_records"] == 3 and manifest["compounds"] == 2
    assert [row["activity_id"] for row in read_csv(output / "activity_review.csv")] == ["1", "2", "3"]


@pytest.mark.parametrize("change,message", [
    ("invalid_json", "JSON"), ("nonfinite", "Nonstandard"),
    ("exponent_overflow", "Nonfinite"),
    ("array_snapshot", "snapshot object"), ("structured_value", "scalar review field"),
])
def test_malformed_json_and_nonscalar_values_are_rejected(tmp_path, change, message):
    payload = bundle()
    if change == "array_snapshot":
        payload = []
    elif change == "structured_value":
        payload["activity_pages"][0]["activities"][0]["standard_value"] = {"value": "50"}
    elif change == "nonfinite":
        payload["activity_pages"][0]["activities"][0]["unrecognized_source_field"] = float("nan")
    root, path = snapshot(tmp_path, payload)
    if change == "invalid_json":
        path.write_text("{not JSON}")
    elif change == "exponent_overflow":
        path.write_text(path.read_text().replace('"year": 2026', '"year": 1e999'))
    with pytest.raises(ValueError, match = message):
        run(root, tmp_path / "review")
    assert not (tmp_path / "review").exists()
