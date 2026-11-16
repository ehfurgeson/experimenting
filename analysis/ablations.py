"""Structural feature-block experiments on a common scaffold-held-out cohort."""

import argparse
import json
from importlib.metadata import version
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.feature_selection import VarianceThreshold
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from formula import FORMULA_FEATURES
from screen import HERE, hashes, write_csv
from structure import DESCRIPTORS, FINGERPRINT_SIZE
from structure_models import SEED, eligible, feature_matrix

FORMULA = tuple(range(len(FORMULA_FEATURES)))
DESCRIPTOR = tuple(range(len(FORMULA), len(FORMULA) + len(DESCRIPTORS)))
MORGAN = tuple(range(len(FORMULA) + len(DESCRIPTOR),
                     len(FORMULA) + len(DESCRIPTOR) + FINGERPRINT_SIZE))
# Each profile specifies (scaled preserved columns, scaled/PCA-projected columns).
PROFILES = {
    "formula": ((), FORMULA), "descriptors": ((), DESCRIPTOR), "morgan": ((), MORGAN),
    "combined": ((), FORMULA + DESCRIPTOR + MORGAN),
    "formula_descriptors": ((), FORMULA + DESCRIPTOR),
    "formula_morgan": ((), FORMULA + MORGAN),
    "combined_formula_outside_pca": (FORMULA, DESCRIPTOR + MORGAN),
    "combined_morgan_pca": (FORMULA + DESCRIPTOR, MORGAN),
    "formula_morgan_pca": (FORMULA, MORGAN),
}
C_GRID = (.01, .1, 1.0, 10.0, 100.0)


def _cohort(rows, target):
    if target not in {"selection_target", "activity_target", "origin_target",
                      "provenance_comparator_target"}:
        raise ValueError("Unsupported target")
    ids = [r.get("compound_id") for r in rows]
    if any(not isinstance(i, str) or not i.strip() for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("Unique nonempty compound_id values are required")
    unique = {}
    for row in rows:
        label = row.get(target)
        if label is not None and (type(label) is not int or label not in (0, 1)):
            raise ValueError("Targets must be binary integers or null")
        if target == "provenance_comparator_target" and label is not None:
            expected_group = {0: "reviewed_natural_occurrence",
                              1: "documented_commercial_herbicide_comparator"}[label]
            if row.get("contrast_group") != expected_group:
                raise ValueError("Provenance comparator target/group disagreement")
        if label is None or not eligible(row, "formula"):
            continue
        identity = row.get("canonical_structure")
        if not isinstance(identity, str) or not identity:
            raise ValueError("Valid chemistry requires canonical_structure")
        previous = unique.get(identity)
        if previous and previous[target] != label:
            raise ValueError(f"Conflicting target for structure {identity}")
        if not previous or row["compound_id"] < previous["compound_id"]:
            unique[identity] = row
    return [unique[key] for key in sorted(unique)]


def _splits(x, y, groups, count):
    if any(np.sum(y == label) < count for label in (0, 1)):
        return "insufficient_class_support", []
    if any(len(set(groups[y == label])) < count for label in (0, 1)):
        return "insufficient_scaffold_support", []
    splits = list(StratifiedGroupKFold(n_splits = count, shuffle = True, random_state = SEED)
                  .split(x, y, groups))
    if any(len(set(y[a])) < 2 or len(set(y[b])) < 2 for a, b in splits):
        return "insufficient_scaffold_support", []
    return "evaluated", splits


def _estimator(profile, c = 1.0):
    preserved, projected = PROFILES[profile]
    pca = Pipeline([("vary", VarianceThreshold()), ("scale", StandardScaler()),
                    ("pca", PCA(n_components = .95, svd_solver = "full"))])
    branches = [("projected", pca, list(projected))]
    if preserved:
        branches.insert(0, ("preserved", StandardScaler(), list(preserved)))
    return Pipeline([
        ("features", ColumnTransformer(branches, remainder = "drop")),
        ("classifier", LogisticRegression(C = c, class_weight = "balanced", max_iter = 2000,
                                          random_state = SEED)),
    ])


def _choose_c(profile, x, y, splits, outer_fold):
    scores = {c: [] for c in C_GRID}
    history = []
    for fold, (train, test) in enumerate(splits):
        # Preprocessing is independent of C and reusable only within this split.
        transform = _estimator(profile).named_steps["features"]
        train_x = transform.fit_transform(x[train], y[train])
        test_x = transform.transform(x[test])
        for c in C_GRID:
            classifier = _estimator(profile, c).named_steps["classifier"]
            classifier.fit(train_x, y[train])
            score = float(balanced_accuracy_score(y[test], classifier.predict(test_x)))
            scores[c].append(score)
            history.append({"profile": profile, "fold": outer_fold, "inner_fold": fold,
                            "c": c, "balanced_accuracy": score,
                            "train_n": len(train), "test_n": len(test)})
    means = {c: float(np.mean(values)) for c, values in scores.items()}
    best = max(means.values())
    chosen = min(c for c, value in means.items() if abs(value - best) <= 1e-12)
    return chosen, means[chosen], history


def ablate(rows, target = "selection_target", tune = False):
    """Compare fixed or nested-selected C without changing production models."""
    if type(tune) is not bool:
        raise ValueError("tune must be a boolean")
    cohort = _cohort(rows, target)
    x = feature_matrix(cohort, "combined") if cohort else np.empty((0, len(MORGAN) + 38))
    if not np.isfinite(x).all():
        raise ValueError("Ablations require complete finite chemistry; no imputation is performed")
    y = np.array([r[target] for r in cohort], dtype = int)
    groups = np.array([r["scaffold"] for r in cohort])
    status, splits = _splits(x, y, groups, 5)
    inner = []
    if tune:
        for train, _ in splits:
            inner_status, partitions = _splits(x[train], y[train], groups[train], 3)
            if inner_status != "evaluated":
                status, splits = "insufficient_inner_scaffold_support", []
                break
            inner.append(partitions)
    result = {"reports": [], "folds": [], "oof": [], "search": [], "cohort": [
        {"compound_id": r["compound_id"], "canonical_structure": r["canonical_structure"],
         "scaffold": r["scaffold"], "label": r[target]} for r in cohort]}
    for profile, (preserved, projected) in PROFILES.items():
        report = {"profile": profile, "target": target, "nested": tune, "n": len(cohort),
                  "positives": int(y.sum()), "negatives": int(len(y) - y.sum()), "status": status,
                  **dict.fromkeys(["accuracy", "balanced_accuracy", "roc_auc", "average_precision",
                                   "baseline_accuracy", "tn", "fp", "fn", "tp"])}
        result["reports"].append(report)
        if not splits:
            continue
        partitions = [train for train, _ in splits]
        if tune:
            partitions += [train[a] for (train, _), subsplits in zip(splits, inner, strict = True)
                           for a, _ in subsplits]
        if any(not np.any(np.ptp(x[train][:, projected], axis = 0) > 0) for train in partitions):
            report["status"] = "no_training_variation"
            continue
        oof, fold_rows = [], []
        for fold, (train, test) in enumerate(splits):
            c, inner_score = 1.0, None
            if tune:
                c, inner_score, search = _choose_c(profile, x[train], y[train], inner[fold], fold)
                result["search"] += search
            estimator = _estimator(profile, c)
            estimator.fit(x[train], y[train])
            probability = estimator.predict_proba(x[test])[:, 1]
            baseline = int(y[train].sum() > len(train) / 2)
            components = estimator.named_steps["features"].named_transformers_["projected"].named_steps["pca"]
            fold_rows.append({"profile": profile, "fold": fold, "train_n": len(train),
                              "test_n": len(test), "selected_c": c,
                              "inner_best_balanced_accuracy": inner_score,
                              "preserved_features": len(preserved),
                              "pca_components": int(components.n_components_),
                              "model_features": int(estimator.named_steps["classifier"].n_features_in_),
                              "training_balanced_accuracy": float(balanced_accuracy_score(
                                  y[train], estimator.predict(x[train]))),
                              "test_balanced_accuracy": float(balanced_accuracy_score(
                                  y[test], probability >= .5))})
            oof += [{"profile": profile, "compound_id": cohort[i]["compound_id"],
                     "scaffold": cohort[i]["scaffold"], "fold": fold, "label": int(y[i]),
                     "probability": float(p), "baseline_prediction": baseline}
                    for i, p in zip(test, probability, strict = True)]
        order = {r["compound_id"]: i for i, r in enumerate(cohort)}
        oof.sort(key = lambda r: order[r["compound_id"]])
        probability = np.array([r["probability"] for r in oof])
        prediction = probability >= .5
        tn, fp, fn, tp = confusion_matrix(y, prediction, labels = [0, 1]).ravel()
        report.update(accuracy = float(accuracy_score(y, prediction)),
                      balanced_accuracy = float(balanced_accuracy_score(y, prediction)),
                      roc_auc = float(roc_auc_score(y, probability)),
                      average_precision = float(average_precision_score(y, probability)),
                      baseline_accuracy = float(accuracy_score(y, [r["baseline_prediction"] for r in oof])),
                      tn = int(tn), fp = int(fp), fn = int(fn), tp = int(tp))
        result["folds"] += fold_rows
        result["oof"] += oof
    return result


def run(features, output, target = "selection_target", tune = False):
    features, output = Path(features).resolve(), Path(output).resolve()
    if features.is_relative_to(output):
        raise ValueError("Output must be outside input paths")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use an empty output directory")
    result = ablate(pl.read_parquet(features).to_dicts(), target, tune)
    output.mkdir(parents = True, exist_ok = True)
    for name, key, empty_columns in [
        ("ablation_models.csv", "reports", []),
        ("folds.csv", "folds", ["profile", "fold", "train_n", "test_n", "selected_c",
                                "inner_best_balanced_accuracy",
                                "preserved_features", "pca_components", "model_features",
                                "training_balanced_accuracy", "test_balanced_accuracy"]),
        ("out_of_fold.csv", "oof", ["profile", "compound_id", "scaffold", "fold", "label",
                                   "probability", "baseline_prediction"]),
        ("cohort.csv", "cohort", ["compound_id", "canonical_structure", "scaffold", "label"]),
        ("inner_scores.csv", "search", ["profile", "fold", "inner_fold", "c",
                                        "balanced_accuracy", "train_n", "test_n"]),
    ]:
        write_csv(output / name, result[key], list(result[key][0]) if result[key] else empty_columns)
    manifest = {
        "input_hashes": hashes([features]), "code_hashes": hashes(list(HERE.glob("*.py"))),
        "lock_hashes": hashes([HERE / "uv.lock", HERE / "pyproject.toml"]),
        "output_hashes": hashes(list(output.iterdir())),
        "versions": {name: version(name) for name in ("rdkit", "scikit-learn", "numpy", "polars")},
        "target": target, "seed": SEED, "outer_folds": 5, "imputed_cells": 0,
        "nested": tune, "inner_folds": 3 if tune else None,
        "c": None if tune else 1.0, "c_grid": list(C_GRID) if tune else [],
        "profiles": {name: {"preserved": list(a), "projected": list(b)}
                     for name, (a, b) in PROFILES.items()},
        "scope": "Exploratory selection ablations; no activity validation or production replacement.",
        "reports": result["reports"],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent = 2, allow_nan = False) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument("--features", type = Path, required = True)
    parser.add_argument("--output", type = Path, required = True)
    parser.add_argument("--target", default = "selection_target")
    parser.add_argument("--tune", action = "store_true", help = "Select C within inner scaffold folds")
    args = parser.parse_args()
    manifest = run(args.features, args.output, args.target, args.tune)
    for report in manifest["reports"]:
        print(report["profile"], report["status"], report["balanced_accuracy"], flush = True)


if __name__ == "__main__":
    main()
