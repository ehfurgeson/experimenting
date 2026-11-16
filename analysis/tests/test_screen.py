"""The offline workflow preserves source files and exports reviewable evidence."""
import csv
import json
import socket
import sys
from pathlib import Path

import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from screen import prepare, run, score_candidates
from structure import FINGERPRINT_SIZE
from structure_models import evaluate


def test_preparation_keeps_identity_conflicts_and_unusable_rows_for_review():
    rows = prepare([
        {"compound_id": "a", "smiles": "CCO", "molecular_formula": "C2H6O"},
        {"compound_id": "b", "smiles": "COC", "molecular_formula": "CH4"},
        {"compound_id": "c", "smiles": "CCO", "inchikey": "WRONG"},
        {"compound_id": "d", "smiles": None},
    ])
    assert len(rows) == 4
    assert rows[0]["formula_comparison"] == "match"
    assert rows[1]["structure_status"] == "identity_mismatch"
    assert rows[1]["formula_comparison"] == "mismatch"
    assert rows[2]["structure_status"] == "identity_mismatch"
    assert rows[3]["structure_status"] == "missing"


def test_offline_run_preserves_inputs_and_exports_null_activity_metrics(tmp_path, monkeypatch):
    def no_network(*args, **kwargs):
        pytest.fail("Screening attempted network access")

    monkeypatch.setattr(socket, "create_connection", no_network)
    source = tmp_path / "traits.csv"
    source.write_text("compound_id,canonical_smiles,chemical_group,molecular_formula\n"
                      "a,CCO,herbicide,C2H6O\nb,COC,natural_product,C2H6O\nc,,,\n")
    before = source.read_bytes()
    output = tmp_path / "products"
    manifest = run(source, output)
    assert source.read_bytes() == before
    features = pl.read_parquet(output / "structural_features.parquet")
    assert features.height == 3
    assert features.filter(pl.col("structure_status") == "missing").height == 1
    metrics = pl.read_csv(output / "structure_models.csv")
    assert metrics.height == 12
    assert metrics["accuracy"].null_count() == 12
    assert set(metrics["target"]) == {"selection_target", "activity_target", "origin_target"}
    assert (output / "label_review_template.csv").exists()
    assert (output / "out_of_fold.csv").read_text().startswith("compound_id,")
    assert manifest["input_hashes"][str(source.resolve())]
    assert manifest["versions"]["rdkit"]
    assert "fingerprint" not in pl.read_csv(output / "structural_features.csv").columns
    saved = json.loads((output / "manifest.json").read_text())
    assert saved["output_hashes"] == manifest["output_hashes"]


def test_bad_labels_or_reused_output_fail_before_writing_products(tmp_path):
    source = tmp_path / "traits.csv"
    source.write_text("compound_id,smiles\na,CCO\n")
    output = tmp_path / "output"
    output.mkdir()
    sentinel = output / "existing.csv"
    sentinel.write_text("keep")
    with pytest.raises(ValueError, match = "empty output"):
        run(source, output)
    assert sentinel.read_text() == "keep"
    labels = tmp_path / "labels.csv"
    labels.write_text("compound_id,herbicidal_activity\na,active\n")
    clean = tmp_path / "clean"
    with pytest.raises(ValueError, match = "activity_reference"):
        run(source, clean, labels = labels)
    assert not clean.exists()
    with pytest.raises(ValueError, match = "outside"):
        run(source, source.parent)


def test_candidates_are_retained_with_blocked_status_without_activity_labels(tmp_path):
    source = tmp_path / "compounds.csv"
    source.write_text("compound_id,smiles\na,CCO\n")
    candidates = tmp_path / "candidates.csv"
    candidates.write_text("compound_id,smiles\nnp1,COC\nnp2,invalid\n")
    output = tmp_path / "products"
    run(source, output, candidates = candidates)
    scores = list(csv.DictReader((output / "candidate_scores.csv").open()))
    assert len(scores) == 8  # one review row for every candidate/representation
    assert {row["status"] for row in scores} == {"activity_model_unavailable", "invalid_smiles"}
    assert all(not row["probability"] for row in scores)


def test_reviewed_activity_can_score_new_candidates_with_similarity_and_scaffold_context():
    # Separate model test uses synthetic features to guarantee class/scaffold support.
    from test_structure_models import examples

    rows = examples()
    result = evaluate(rows, "activity_target", "combined")
    new = {**rows[0], "compound_id": "new", "canonical_structure": "novel",
           "scaffold": "new_scaffold"}
    same = {**rows[0], "compound_id": "alias"}
    scores = score_candidates(result, [new, same])
    assert scores[0]["status"] == "scored_exploratory"
    assert 0 <= scores[0]["probability"] <= 1
    assert scores[0]["nearest_training_tanimoto"] == 1
    assert not scores[0]["scaffold_seen"]
    assert scores[1]["status"] == "already_labeled_structure"
    assert scores[1]["probability"] is None
    assert len(new["fingerprint"]) == FINGERPRINT_SIZE


def test_candidate_ids_must_be_unique_and_separate_from_training(tmp_path):
    source = tmp_path / "compounds.csv"
    source.write_text("compound_id,smiles\na,CCO\n")
    candidates = tmp_path / "candidates.csv"
    candidates.write_text("compound_id,smiles\na,COC\n")
    with pytest.raises(ValueError, match = "overlap"):
        run(source, tmp_path / "products", candidates = candidates)


def test_formula_identity_checks_all_elements_even_outside_predictor_list():
    row = prepare([{"compound_id": "a", "smiles": "C[Ge](C)(C)C",
                    "molecular_formula": "C4H12Sn"}])[0]
    assert row["formula_comparison"] == "mismatch"
    assert row["structure_status"] == "identity_mismatch"


def test_reviewed_screening_exports_predictions_from_rdkit_chemistry_end_to_end(tmp_path):
    # Real SMILES exercise chemistry/serialization; all outcomes and citations
    # below are synthetic workflow fixtures, not evidence of biological activity.
    rings = ["c1ccccc1", "c1ccncc1", "c1cncnc1", "c1ccoc1", "c1ccsc1", "c1cc[nH]c1",
             "C1CCCCC1", "C1CCCC1", "C1CCC1", "C1CC1", "C1CCCCCC1", "C1CCOCC1",
             "C1CCNCC1", "C1CCSCC1", "c1ccc2ccccc2c1"]
    source = tmp_path / "compounds.csv"
    labels = tmp_path / "labels.csv"
    candidates = tmp_path / "candidates.csv"
    with source.open("w", newline = "") as stream:
        writer = csv.writer(stream)
        writer.writerow(["compound_id", "smiles"])
        for index, ring in enumerate(rings):
            for prefix in ("C", "O"):
                writer.writerow([f"synthetic-{index}-{prefix}", prefix + ring])
    with labels.open("w", newline = "") as stream:
        writer = csv.writer(stream)
        writer.writerow(["compound_id", "herbicidal_activity", "activity_reference",
                         "activity_context", "activity_policy"])
        for index in range(len(rings)):
            for prefix, outcome in (("C", "inactive"), ("O", "active")):
                writer.writerow([f"synthetic-{index}-{prefix}", outcome, "synthetic:test-only",
                                 "Artificial label for workflow validation", "synthetic-policy"])
    candidates.write_text("compound_id,smiles\nnew,OC1CCCCCCC1\nalias,Cc1ccccc1\nbad,invalid\n")
    before = {path: path.read_bytes() for path in (source, labels, candidates)}
    output = tmp_path / "screen"
    manifest = run(source, output, labels = labels, candidates = candidates)
    activity = [row for row in manifest["reports"] if row["target"] == "activity_target"]
    assert len(activity) == 4
    assert {row["status"] for row in activity} == {"evaluated"}
    assert {row["n"] for row in activity} == {30}
    assert {row["scaffolds"] for row in activity} == {15}
    assert all(path.read_bytes() == content for path, content in before.items())
    oof = pl.read_csv(output / "out_of_fold.csv")
    assert oof.height == 120
    for representation in ("formula", "descriptors", "morgan", "combined"):
        predictions = oof.filter(pl.col("representation") == representation)
        assert predictions["compound_id"].n_unique() == 30
        assert predictions.group_by("scaffold").agg(pl.col("fold").n_unique())["fold"].max() == 1
    scores = pl.read_csv(output / "candidate_scores.csv")
    new = scores.filter(pl.col("compound_id") == "new")
    assert new.height == 4
    assert set(new["status"]) == {"scored_exploratory"}
    assert new["probability"].is_between(0, 1).all()
    assert new["nearest_training_tanimoto"].is_between(0, 1).all()
    assert not new["scaffold_seen"].any()
    assert set(scores.filter(pl.col("compound_id") == "alias")["status"]) == {
        "already_labeled_structure"}
    assert set(scores.filter(pl.col("compound_id") == "bad")["status"]) == {"invalid_smiles"}
    assert scores.filter(pl.col("compound_id") != "new")["probability"].null_count() == 8
