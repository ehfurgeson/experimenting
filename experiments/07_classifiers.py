"""Fit small classifiers to explore what the traits can and cannot explain.

Every model is a plain logistic regression with L2 regularization, fitted on
z-scored traits and evaluated by stratified five-fold cross-validation with a
fixed seed. The baseline is the majority class. The results describe this
sample only; they are not a safety score and not a claim about the chemistry.

    uv run --project pipeline python experiments/07_classifiers.py
"""

import csv
from pathlib import Path

import polars as pl
from stats import cross_validated_accuracy, impute, logistic_regression, standardize

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
COMPOUNDS = DATA / "compound_traits.parquet"
OUTPUT = DATA / "classifiers.csv"

FEATURES = [
    "xlogp", "tpsa", "hbond_donor_count", "hbond_acceptor_count",
    "rotatable_bond_count", "heavy_atom_count", "complexity", "molecular_weight",
    "exact_mass", "monoisotopic_mass",
]


def rows_for(frame, features, target_builder):
    rows = []
    for record in frame.iter_rows(named = True):
        target = target_builder(record)
        if target is None:
            continue
        rows.append({**{feature: record[feature] for feature in features}, "target": target})
    return rows


def fit_and_report(name, rows, features, description):
    positives = sum(1 for row in rows if row["target"] == 1)
    baseline = max(positives, len(rows) - positives) / len(rows) if rows else None
    accuracy = cross_validated_accuracy(rows, features, "target")
    status = "evaluated" if accuracy is not None else "insufficient_class_support"
    weights = {}
    if accuracy is not None:
        imputed, _ = impute(rows, features)
        scaled, parameters = standardize(imputed, features)
        weights, _ = logistic_regression(scaled, list(parameters), "target")
    ordered = sorted(weights.items(), key=lambda item: -abs(item[1]))
    print(f"{name}")
    print(f"  {description}")
    print(f"  n={len(rows)}  positives={positives}  majority baseline={baseline}")
    print(f"  cross-validated accuracy={accuracy:.3f}"
          if accuracy is not None else "  cross-validated accuracy=not available")
    print("  strongest weights: " + ", ".join(
        f"{feature}={value:+.2f}" for feature, value in ordered[:6]
    ))
    return {
        "model": name, "description": description, "n": len(rows),
        "positives": positives, "baseline": baseline, "accuracy": accuracy, "status": status,
        "weights": "; ".join(f"{feature}={value:+.3f}" for feature, value in ordered),
    }


def main() -> None:
    frame = pl.read_parquet(COMPOUNDS)
    results = []
    results.append(fit_and_report(
        "group_from_structure",
        rows_for(frame, FEATURES, lambda record: 1 if record["chemical_group"] == "herbicide" else 0),
        FEATURES, "Can structure alone tell a herbicide from a natural product?",
    ))
    for trait in frame.columns:
        if not trait.startswith("has_"):
            continue
        results.append(fit_and_report(
            f"{trait.removeprefix('has_')}_availability",
            rows_for(frame, FEATURES, lambda record, key = trait: record.get(key)),
            FEATURES, f"Can structure predict extracted evidence availability: {trait}?",
        ))
    results.append(fit_and_report(
        "any_complete_measurement",
        rows_for(frame, FEATURES, lambda record: 1 if (record.get("complete_count") or 0) > 0 else 0),
        FEATURES, "Can structure predict whether any PubChem measurement was extracted?",
    ))
    results.append(fit_and_report(
        "studied_at_all",
        rows_for(frame, FEATURES, lambda record: 1 if (record.get("annotation_count") or 0) > 0 else 0),
        FEATURES, "Can structure predict whether a compound has any PubChem annotation?",
    ))
    with OUTPUT.open("w", encoding = "utf-8", newline = "") as stream:
        writer = csv.DictWriter(stream, fieldnames = list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    print(f"\nwrote {len(results)} models to {OUTPUT}")


if __name__ == "__main__":
    main()
