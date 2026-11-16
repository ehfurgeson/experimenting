"""Validation separates scaffolds and fits every learned transform on training data."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from formula import FORMULA_FEATURES
from structure import DESCRIPTORS, FINGERPRINT_SIZE
from structure_models import evaluate


def examples():
    # Synthetic chemistry features isolate the evaluation contract, not chemical accuracy.
    rows = []
    for index in range(30):
        target = index % 2
        rows.append({
            "compound_id": str(index), "canonical_structure": f"identity{index}",
            "structure_status": "valid", "formula_status": "valid",
            "scaffold": f"scaffold{index // 2}", "activity_target": target,
            **{key: float(target) for key in FORMULA_FEATURES + DESCRIPTORS},
            "fingerprint": [target, 1 - target] + [0] * (FINGERPRINT_SIZE - 2),
            "has_toxicity": 1 - target,
        })
    return rows


@pytest.mark.parametrize("representation", ["formula", "descriptors", "morgan", "combined"])
def test_reproducible_evaluation_covers_each_compound_once_without_scaffold_leak(representation):
    rows = examples()
    result = evaluate(rows, "activity_target", representation)
    assert result["report"]["status"] == "evaluated"
    assert result["report"]["balanced_accuracy"] == 1
    assert result["report"]["roc_auc"] == 1
    assert result["report"]["baseline_accuracy"] == .5
    assert len(result["oof"]) == len(rows)
    assigned = {row["compound_id"]: row["fold"] for row in result["oof"]}
    for index in range(0, 30, 2):
        assert assigned[str(index)] == assigned[str(index + 1)]
    repeated = evaluate(rows, "activity_target", representation)
    assert repeated["oof"] == result["oof"]
    assert 0 < result["report"]["max_components"] < FINGERPRINT_SIZE


def test_unreviewed_and_unusable_rows_do_not_become_negative_training_examples():
    rows = examples()
    rows[0]["activity_target"] = None
    rows[1]["structure_status"] = "missing"
    rows[2]["formula_status"] = "unsupported"
    result = evaluate(rows, "activity_target", "formula")
    assert result["report"]["n"] == 27
    assert result["report"]["excluded"] == 3


@pytest.mark.parametrize("change,status", [
    ("unlabeled", "insufficient_class_support"),
    ("one_class", "insufficient_class_support"),
    ("one_scaffold", "insufficient_scaffold_support"),
    ("constant", "no_training_variation"),
])
def test_support_failures_have_no_predictions_or_fitted_model(change, status):
    rows = examples()
    for row in rows:
        if change == "unlabeled":
            row["activity_target"] = None
        elif change == "one_class":
            row["activity_target"] = 1
        elif change == "one_scaffold":
            row["scaffold"] = "shared"
        elif change == "constant":
            row.update(dict.fromkeys(DESCRIPTORS, 1.0))
    result = evaluate(rows, "activity_target", "descriptors")
    assert result["report"]["status"] == status
    assert result["report"]["accuracy"] is None
    assert result["oof"] == []
    assert result["estimator"] is None


def test_duplicate_structures_are_counted_once_and_conflicting_labels_raise():
    rows = examples()
    duplicate = {**rows[0], "compound_id": "alias"}
    result = evaluate(rows + [duplicate], "activity_target", "formula")
    assert result["report"]["n"] == 30
    assert result["report"]["duplicates"] == 1
    with pytest.raises(ValueError, match = "Conflicting target"):
        evaluate(rows + [{**duplicate, "activity_target": 1}], "activity_target", "formula")


def test_extreme_held_out_values_cannot_change_training_imputer_or_pca(monkeypatch):
    import structure_models

    original = structure_models.make_estimator
    fitted = []

    def traced():
        estimator = original()
        original_fit = estimator.fit

        def fit(x, y):
            result = original_fit(x, y)
            fitted.append((x.copy(), estimator.named_steps["impute"].statistics_.copy(),
                           estimator.named_steps["pca"].mean_.copy()))
            return result

        estimator.fit = fit
        return estimator

    monkeypatch.setattr(structure_models, "make_estimator", traced)
    rows = examples()
    rows[0]["mw"] = 1e9
    result = evaluate(rows, "activity_target", "descriptors")
    assert result["report"]["status"] == "evaluated"
    assert len(fitted) == 6  # five fold fits plus explicitly separate full-data fit
    for matrix, medians, pca_mean in fitted:
        assert medians == pytest.approx(np.nanmedian(matrix, axis = 0))
        assert np.abs(pca_mean).max() < 1e-6
    assert sum(np.max(matrix) < 1e9 for matrix, _, _ in fitted) == 1


def test_metadata_and_toxicity_cannot_change_predictions():
    rows = examples()
    first = evaluate(rows, "activity_target", "combined")["oof"]
    for row in rows:
        row.update(has_toxicity = 1000, inchikey = "arbitrary", chemical_group = "changed")
    assert evaluate(rows, "activity_target", "combined")["oof"] == first


def test_invalid_model_configuration_is_rejected():
    with pytest.raises(ValueError, match = "representation"):
        evaluate(examples(), "activity_target", "toxicity")
    with pytest.raises(ValueError, match = "folds"):
        evaluate(examples(), "activity_target", "formula", folds = 1)
    rows = examples()
    rows[0]["activity_target"] = "active"
    with pytest.raises(ValueError, match = "binary"):
        evaluate(rows, "activity_target", "formula")


@pytest.mark.parametrize("representation", ["formula", "descriptors", "morgan", "combined"])
@pytest.mark.parametrize("with_alias", [False, True])
def test_row_order_cannot_change_scaffold_folds_or_model_evidence(representation, with_alias):
    rows = examples()
    # Unequal chemistry prevents identical predictions from masking changed folds.
    for index, row in enumerate(rows):
        row["mw"] = float(index + 1)
    if with_alias:
        rows.append({**rows[0], "compound_id": "-alias"})
    reference = evaluate(rows, "activity_target", representation)
    shuffled = list(np.random.default_rng(42).permutation(rows))
    reordered = evaluate(shuffled, "activity_target", representation)
    assert reference["report"]["status"] == "evaluated"
    assert reordered["report"] == reference["report"]
    assert reordered["oof"] == reference["oof"]
    assert [row["canonical_structure"] for row in reordered["training"]] == [
        row["canonical_structure"] for row in reference["training"]
    ]
    if with_alias:
        assert reference["report"]["duplicates"] == 1
        assert next(row for row in reference["oof"]
                    if row["scaffold"] == "scaffold0" and row["label"] == 0
                    )["compound_id"] == "-alias"
