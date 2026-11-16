"""Scaffold-held-out structural models; selection is not activity."""
import numpy as np
from sklearn.decomposition import PCA
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from formula import FORMULA_FEATURES
from structure import DESCRIPTORS, FINGERPRINT_SIZE

REPRESENTATIONS = ("formula", "descriptors", "morgan", "combined")
SEED = 20261027


def feature_matrix(rows, representation):
    """Use fixed chemistry allowlists; IDs, labels and toxicity never enter X."""
    if representation not in REPRESENTATIONS:
        raise ValueError(f"Unknown representation: {representation}")
    columns = []
    if representation in {"formula", "combined"}:
        columns += FORMULA_FEATURES
    if representation in {"descriptors", "combined"}:
        columns += DESCRIPTORS
    matrix = []
    for row in rows:
        values = [row.get(key) for key in columns]
        if representation in {"morgan", "combined"}:
            bits = row.get("fingerprint")
            if bits is None or len(bits) != FINGERPRINT_SIZE or any(v not in (0, 1) for v in bits):
                raise ValueError("A valid Morgan fingerprint is required")
            values += bits
        matrix.append(values)
    result = np.array(matrix, dtype = float)
    result[~np.isfinite(result)] = np.nan
    return result


def make_estimator():
    """All fitted preprocessing stays inside the fold's estimator."""
    return Pipeline([
        ("impute", SimpleImputer(strategy = "median", keep_empty_features = True)),
        ("vary", VarianceThreshold()),
        ("scale", StandardScaler()),
        ("pca", PCA(n_components = .95, svd_solver = "full")),
        ("classifier", LogisticRegression(C = 1.0, class_weight = "balanced",
                                          max_iter = 2000, random_state = SEED)),
    ])


def eligible(row, representation):
    return (row.get("structure_status") == "valid" and bool(row.get("scaffold"))
            and (representation != "formula" or row.get("formula_status") == "valid"))


def evaluate(rows, target, representation, folds = 5):
    """Return out-of-fold evidence plus a separate exploratory full-sample fit."""
    if representation not in REPRESENTATIONS:
        raise ValueError(f"Unknown representation: {representation}")
    if not isinstance(folds, int) or isinstance(folds, bool) or folds < 2:
        raise ValueError("folds must be an integer of at least two")
    unique = {}
    excluded = duplicates = 0
    for row in rows:
        label = row.get(target)
        if label is not None and (type(label) is not int or label not in (0, 1)):
            raise ValueError(f"{target} must contain binary integers or null")
        if label is None or not eligible(row, representation):
            excluded += 1
            continue
        identity = row.get("canonical_structure")
        if not identity:
            raise ValueError("Valid structures require canonical_structure")
        if identity in unique:
            if unique[identity][target] != label:
                raise ValueError(f"Conflicting target for structure {identity}")
            duplicates += 1
            if row["compound_id"] < unique[identity]["compound_id"]:
                unique[identity] = row
        else:
            unique[identity] = row
    # Stabilize split inputs, numerical fits and audit rows across table reorderings.
    training = [unique[identity] for identity in sorted(unique)]
    y = np.array([row[target] for row in training], dtype = int)
    groups = np.array([row["scaffold"] for row in training])
    positives = int(y.sum())
    report = {
        "target": target, "representation": representation, "n": len(training),
        "positives": positives, "negatives": len(training) - positives,
        "excluded": excluded, "duplicates": duplicates, "scaffolds": len(set(groups)),
        "folds": folds, "status": "insufficient_class_support",
        **dict.fromkeys(["accuracy", "balanced_accuracy", "roc_auc", "average_precision",
                         "precision", "recall", "f1", "baseline_accuracy", "baseline_balanced_accuracy",
                         "tn", "fp", "fn", "tp", "max_components"]),
    }
    result = {"report": report, "oof": [], "estimator": None, "training": training}
    if min(positives, len(training) - positives) < folds:
        return result
    report["status"] = "insufficient_scaffold_support"
    if any(len(set(groups[y == label])) < folds for label in (0, 1)):
        return result
    x = feature_matrix(training, representation)
    splits = list(StratifiedGroupKFold(n_splits = folds, shuffle = True, random_state = SEED)
                  .split(x, y, groups))
    if any(len(set(y[train])) < 2 or len(set(y[test])) < 2 for train, test in splits):
        return result
    probabilities = np.zeros(len(training))
    baseline = np.zeros(len(training), dtype = int)
    assignments = np.zeros(len(training), dtype = int)
    components = []
    for fold, (train, test) in enumerate(splits):
        # Missing/constant features are assessed only on the training partition.
        if not any(len(set(column[np.isfinite(column)])) > 1 for column in x[train].T):
            report["status"] = "no_training_variation"
            return result
        estimator = make_estimator()
        estimator.fit(x[train], y[train])
        probabilities[test] = estimator.predict_proba(x[test])[:, 1]
        baseline[test] = int(y[train].sum() > len(train) / 2)
        assignments[test] = fold
        components.append(int(estimator.named_steps["pca"].n_components_))
    prediction = (probabilities >= .5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, prediction, labels = [0, 1]).ravel()
    report.update(
        status = "evaluated", accuracy = float(accuracy_score(y, prediction)),
        balanced_accuracy = float(balanced_accuracy_score(y, prediction)),
        roc_auc = float(roc_auc_score(y, probabilities)),
        average_precision = float(average_precision_score(y, probabilities)),
        precision = float(precision_score(y, prediction, zero_division = 0)),
        recall = float(recall_score(y, prediction, zero_division = 0)),
        f1 = float(f1_score(y, prediction, zero_division = 0)),
        baseline_accuracy = float(accuracy_score(y, baseline)),
        baseline_balanced_accuracy = float(balanced_accuracy_score(y, baseline)),
        tn = int(tn), fp = int(fp), fn = int(fn), tp = int(tp), max_components = max(components),
    )
    result["oof"] = [
        {"compound_id": row["compound_id"], "target": target, "representation": representation,
         "label": int(y[i]), "fold": int(assignments[i]), "scaffold": row["scaffold"],
         "probability": float(probabilities[i]), "baseline_prediction": int(baseline[i])}
        for i, row in enumerate(training)
    ]
    result["estimator"] = make_estimator().fit(x, y)
    return result
