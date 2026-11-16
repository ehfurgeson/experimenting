"""Structural stress comparisons use equal cohorts and retain failed controls."""

import copy
import json
import sys
from pathlib import Path

import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_structure_models import examples

import stress as diagnostics


def rows():
    return [{**row, "selection_target": row["activity_target"]} for row in examples()]


def test_all_representations_share_cohort_and_deterministic_controls_without_mutation():
    compounds = rows()
    compounds[0]["formula_status"] = "unsupported"
    before = copy.deepcopy(compounds)
    result = diagnostics.stress(compounds, permutations = 2)
    common = [row for row in result if row["scenario"] == "common"]
    assert len(common) == 4
    assert {row["n"] for row in common} == {29}
    assert {row["positives"] for row in common} == {15}
    assert len(result) == 24  # four fixed scenarios plus two shuffled controls
    assert compounds == before
    assert diagnostics.stress(list(reversed(compounds)), permutations = 2) == result
    controls = [row for row in result if row["scenario"] == "shuffled_labels"]
    assert {row["iteration"] for row in controls} == {0, 1}
    assert {row["n"] for row in controls} == {29}
    assert {row["positives"] for row in controls} == {15}


def test_dominant_scaffold_is_omitted_once_with_deterministic_tie_breaking():
    result = diagnostics.stress(rows(), permutations = 0)
    omitted = [row for row in result if row["scenario"] == "omit_largest_scaffold"]
    assert len(omitted) == 4
    assert {row["omitted_scaffold"] for row in omitted} == {"scaffold0"}
    assert {row["n"] for row in omitted} == {28}
    assert {row["folds"] for row in result if row["scenario"] == "common_3fold"} == {3}
    assert {row["folds"] for row in result if row["scenario"] == "common_10fold"} == {10}


def test_controls_shuffle_real_labels_identically_across_representations(monkeypatch):
    original = diagnostics.evaluate
    observed = []

    def traced(compounds, target, representation, **options):
        observed.append((representation, [(row["compound_id"], row[target])
                                          for row in compounds]))
        return original(compounds, target, representation, **options)

    monkeypatch.setattr(diagnostics, "evaluate", traced)
    diagnostics.stress(rows(), permutations = 1)
    shuffled = observed[-4:]
    assert all(labels == shuffled[0][1] for _, labels in shuffled)
    assert sorted(label for _, label in shuffled[0][1]) == [0] * 15 + [1] * 15
    assert dict(shuffled[0][1]) != {row["compound_id"]: row["selection_target"] for row in rows()}


def test_sparse_and_unlabeled_support_failures_remain_visible():
    compounds = rows()
    for row in compounds:
        row["selection_target"] = None
    result = diagnostics.stress(compounds, permutations = 1)
    assert len(result) == 20
    assert {row["status"] for row in result} == {"insufficient_class_support"}
    assert all(row["balanced_accuracy"] is None for row in result)


@pytest.mark.parametrize("count", [-1, True, 1.5, 1001])
def test_invalid_permutation_budget_fails_explicitly(count):
    with pytest.raises(ValueError, match = "permutations"):
        diagnostics.stress(rows(), permutations = count)


def test_unknown_target_is_rejected():
    with pytest.raises(ValueError, match = "target"):
        diagnostics.stress(rows(), target = "toxicity")


def test_offline_diagnostic_exports_hash_inputs_and_retain_unavailable_reports(tmp_path):
    source = tmp_path / "features.parquet"
    compounds = rows()[:2]
    pl.DataFrame(compounds).write_parquet(source)
    before = source.read_bytes()
    output = tmp_path / "stress"
    manifest = diagnostics.run(source, output, permutations = 1)
    assert len(manifest["reports"]) == 20
    assert all(row["balanced_accuracy"] is None for row in manifest["reports"])
    assert source.read_bytes() == before
    assert str(source.resolve()) in manifest["input_hashes"]
    saved = json.loads((output / "manifest.json").read_text())
    assert saved == manifest
    assert pl.read_csv(output / "stress_models.csv").height == 20
    with pytest.raises(ValueError, match = "empty output"):
        diagnostics.run(source, output, permutations = 0)
    with pytest.raises(ValueError, match = "outside"):
        diagnostics.run(source, source.parent, permutations = 0)
