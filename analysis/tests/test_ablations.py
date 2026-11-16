"""Structural ablations compare identical compounds and evaluation partitions."""

import copy
import json
import sys
from pathlib import Path

import numpy as np
import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_structure_models import examples

import ablations
from formula import FORMULA_FEATURES
from structure_models import evaluate


def records():
    return [{**row, "selection_target": row["activity_target"]} for row in examples()]


def test_fixed_comparisons_share_compounds_folds_and_reproduce_original_baselines():
    rows = records()
    before = copy.deepcopy(rows)
    result = ablations.ablate(rows)
    assert len(result["reports"]) == 9
    assert {r["n"] for r in result["reports"]} == {30}
    assert {r["status"] for r in result["reports"]} == {"evaluated"}
    assert len(result["oof"]) == 9 * 30
    assignments = {}
    for row in result["oof"]:
        key = row["compound_id"]
        assert assignments.setdefault(key, row["fold"]) == row["fold"]
    for profile in ("formula", "descriptors", "morgan", "combined"):
        original = evaluate(rows, "selection_target", profile)
        report = next(r for r in result["reports"] if r["profile"] == profile)
        assert report["balanced_accuracy"] == original["report"]["balanced_accuracy"]
        actual = [r for r in result["oof"] if r["profile"] == profile]
        assert [r["probability"] for r in actual] == pytest.approx(
            [r["probability"] for r in original["oof"]], abs = 1e-10)
        assert [r["fold"] for r in actual] == [r["fold"] for r in original["oof"]]
    assert rows == before
    assert ablations.ablate(list(reversed(rows))) == result


def test_formulas_outside_pca_preserve_all_formula_inputs_in_each_fold():
    result = ablations.ablate(records())
    for row in result["folds"]:
        if row["profile"] in {"combined_formula_outside_pca", "formula_morgan_pca"}:
            assert row["preserved_features"] == len(FORMULA_FEATURES)
        elif row["profile"] == "combined_morgan_pca":
            assert row["preserved_features"] == 38
        else:
            assert row["preserved_features"] == 0
        assert row["model_features"] == row["preserved_features"] + row["pca_components"]


def test_preprocessing_sees_only_outer_training_rows(monkeypatch):
    from sklearn.compose import ColumnTransformer

    original = ColumnTransformer.fit_transform
    observed = []

    def traced(self, x, *args, **kwargs):
        observed.append(set(x[:, len(FORMULA_FEATURES)]))
        return original(self, x, *args, **kwargs)

    monkeypatch.setattr(ColumnTransformer, "fit_transform", traced)
    rows = records()
    for index, row in enumerate(rows):
        row["mw"] = index + 1.0
    result = ablations.ablate(rows)
    assignment = {r["compound_id"]: r["fold"] for r in result["oof"]}
    expected = [{r["mw"] for r in rows if assignment[r["compound_id"]] != fold}
                for fold in range(5)]
    assert len(observed) == 45
    assert all(group in expected for group in observed)


@pytest.mark.parametrize("change,status", [("unknown", "insufficient_class_support"),
                                          ("scaffold", "insufficient_scaffold_support"),
                                          ("constant", "no_training_variation")])
@pytest.mark.parametrize("tune", [False, True])
def test_support_failures_are_retained_without_partial_predictions(change, status, tune):
    rows = records()
    for row in rows:
        if change == "unknown": row["selection_target"] = None
        elif change == "scaffold": row["scaffold"] = "shared"
        elif change == "constant":
            for key, value in list(row.items()):
                if isinstance(value, float): row[key] = 1.0
            row["fingerprint"] = [0] * 2048
    result = ablations.ablate(rows, tune = tune)
    assert len(result["reports"]) == 9
    assert {r["status"] for r in result["reports"]} == {status}
    assert all(r["balanced_accuracy"] is None for r in result["reports"])
    assert not result["oof"] and not result["folds"]


def test_common_cohort_excludes_unsupported_formulas_and_deduplicates_aliases():
    rows = records()
    rows[0]["formula_status"] = "unsupported"
    result = ablations.ablate(rows + [{**rows[1], "compound_id": "alias"}])
    assert len(result["cohort"]) == 29
    assert {r["n"] for r in result["reports"]} == {29}
    with pytest.raises(ValueError, match = "Conflicting"):
        ablations.ablate(rows + [{**rows[1], "compound_id": "alias", "selection_target": 0}])


@pytest.mark.parametrize("change,message", [("target", "binary"), ("missing", "complete"),
                                          ("id", "compound_id")])
def test_invalid_inputs_fail_explicitly(change, message):
    rows = records()
    if change == "target": rows[0]["selection_target"] = "active"
    elif change == "missing": rows[0]["mw"] = np.nan
    elif change == "id": rows[0]["compound_id"] = rows[1]["compound_id"]
    with pytest.raises(ValueError, match = message):
        ablations.ablate(rows)


def test_exports_preserve_source_and_capture_all_predictions_and_hashes(tmp_path):
    source = tmp_path / "features.parquet"
    pl.DataFrame(records()).write_parquet(source)
    before = source.read_bytes()
    output = tmp_path / "ablation"
    manifest = ablations.run(source, output)
    assert source.read_bytes() == before
    assert pl.read_csv(output / "ablation_models.csv").height == 9
    assert pl.read_csv(output / "out_of_fold.csv").height == 270
    assert pl.read_csv(output / "cohort.csv").height == 30
    assert manifest["imputed_cells"] == 0
    assert json.loads((output / "manifest.json").read_text()) == manifest
    with pytest.raises(ValueError, match = "empty output"):
        ablations.run(source, output)
    with pytest.raises(ValueError, match = "outside"):
        ablations.run(source, source.parent)


def test_identity_deduplication_and_metadata_do_not_change_experimental_predictions():
    rows = records()
    reference = ablations.ablate(rows)
    for row in rows:
        row.update(has_toxicity = 999, chemical_group = "irrelevant", inchikey = "metadata")
    result = ablations.ablate(rows + [{**rows[0], "compound_id": "z-last-alias"}])
    assert result == reference
    assert {r["n"] for r in result["reports"]} == {30}


@pytest.mark.parametrize("change,message", [("representation", "fingerprint"),
                                          ("identity", "canonical_structure"),
                                          ("unknown_target", "Unsupported target")])
def test_inconsistent_chemistry_or_configuration_is_not_silently_repaired(change, message):
    rows = records()
    options = {}
    if change == "representation": rows[0]["fingerprint"] = [1, 0]
    elif change == "identity": rows[0]["canonical_structure"] = ""
    elif change == "unknown_target": options["target"] = "toxicity"
    with pytest.raises(ValueError, match = message):
        ablations.ablate(rows, **options)


def test_failed_model_exports_have_headers_and_no_partial_oof_rows(tmp_path):
    import hashlib

    rows = records()
    for row in rows:
        row["selection_target"] = None
    source = tmp_path / "features.parquet"
    pl.DataFrame(rows).write_parquet(source)
    output = tmp_path / "products"
    manifest = ablations.run(source, output)
    assert len(manifest["reports"]) == 9
    assert {r["status"] for r in manifest["reports"]} == {"insufficient_class_support"}
    for filename in ("cohort.csv", "folds.csv", "out_of_fold.csv"):
        assert (output / filename).read_text().strip()
        assert len((output / filename).read_text().splitlines()) == 1
    for section in ("input_hashes", "code_hashes", "lock_hashes", "output_hashes"):
        for path, digest in manifest[section].items():
            assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest


def test_nested_search_records_every_score_and_selects_only_by_inner_validation():
    from collections import defaultdict

    result = ablations.ablate(records(), tune = True)
    assert {r["status"] for r in result["reports"]} == {"evaluated"}
    assert len(result["search"]) == 9 * 5 * 3 * 5
    scores = defaultdict(lambda: defaultdict(list))
    for row in result["search"]:
        scores[(row["profile"], row["fold"])][row["c"]].append(row["balanced_accuracy"])
        assert row["train_n"] + row["test_n"] == 24
    for fold in result["folds"]:
        choices = scores[(fold["profile"], fold["fold"])]
        means = {c: np.mean(values) for c, values in choices.items()}
        assert len(means) == 5
        best = min(c for c, score in means.items() if np.isclose(score, max(means.values()),
                                                               rtol = 0, atol = 1e-12))
        assert fold["selected_c"] == best == .01  # synthetic perfect separation ties
        assert fold["inner_best_balanced_accuracy"] == pytest.approx(means[best])


def test_nested_preprocessing_never_fits_on_outer_holdout_compounds(monkeypatch):
    from sklearn.compose import ColumnTransformer

    original = ColumnTransformer.fit_transform
    observed = []

    def traced(self, x, *args, **kwargs):
        observed.append(set(x[:, len(FORMULA_FEATURES)]))
        return original(self, x, *args, **kwargs)

    monkeypatch.setattr(ColumnTransformer, "fit_transform", traced)
    rows = records()
    for index, row in enumerate(rows): row["mw"] = float(index + 1)
    result = ablations.ablate(rows, tune = True)
    assignment = {r["compound_id"]: r["fold"] for r in result["oof"]}
    assert len(observed) == 9 * 5 * 4  # three inner fits plus one outer fit
    for start in range(0, len(observed), 20):
        for fold in range(5):
            outer = {r["mw"] for r in rows if assignment[r["compound_id"]] != fold}
            inner = observed[start + fold * 4:start + fold * 4 + 3]
            assert all(group < outer for group in inner)
            assert set.union(*inner) == outer
            assert observed[start + fold * 4 + 3] == outer


def test_nested_exports_include_search_history_and_same_outer_fold_assignments(tmp_path):
    source = tmp_path / "features.parquet"
    pl.DataFrame(records()).write_parquet(source)
    output = tmp_path / "nested"
    manifest = ablations.run(source, output, tune = True)
    assert manifest["nested"] is True and manifest["inner_folds"] == 3
    assert manifest["c_grid"] == [.01, .1, 1.0, 10.0, 100.0]
    assert pl.read_csv(output / "inner_scores.csv").height == 675
    reference = ablations.ablate(records())
    actual = pl.read_csv(output / "out_of_fold.csv",
                         schema_overrides = {"compound_id": pl.String}).to_dicts()
    fields = ("profile", "compound_id", "scaffold", "label", "fold")
    assert [tuple(r[k] for k in fields) for r in actual] == [
        tuple(r[k] for k in fields) for r in reference["oof"]]


@pytest.mark.parametrize("flag", [1, "yes", None])
def test_nested_option_requires_boolean(flag):
    with pytest.raises(ValueError, match = "tune"):
        ablations.ablate(records(), tune = flag)


def test_unsupported_inner_partitions_produce_status_without_fallback_or_predictions(monkeypatch):
    from sklearn.model_selection import StratifiedGroupKFold

    original = StratifiedGroupKFold.split

    def split(self, x, y, groups):
        if self.n_splits == 5:
            yield from original(self, x, y, groups)
        else:
            # Simulate an inner splitter that cannot place both classes in a fold.
            yield np.flatnonzero(y == 0), np.flatnonzero(y == 1)

    monkeypatch.setattr(StratifiedGroupKFold, "split", split)
    result = ablations.ablate(records(), tune = True)
    assert {r["status"] for r in result["reports"]} == {"insufficient_inner_scaffold_support"}
    assert all(r["balanced_accuracy"] is None for r in result["reports"])
    assert not result["oof"] and not result["folds"] and not result["search"]
