"""Common-cohort structural diagnostics and shuffled-label controls."""

import argparse
import json
from collections import Counter
from importlib.metadata import version
from pathlib import Path

import numpy as np
import polars as pl

from screen import HERE, hashes, write_csv
from structure_models import REPRESENTATIONS, SEED, evaluate


def stress(rows, target = "selection_target", permutations = 20):
    """Retain every diagnostic status without choosing a favorable model."""
    if target not in {"selection_target", "activity_target", "origin_target"}:
        raise ValueError("Unsupported structural target")
    if type(permutations) is not int or not 0 <= permutations <= 1000:
        raise ValueError("permutations must be an integer from zero through 1000")
    # Formula eligibility is the intersection of all four chemistry representations.
    # Reuse public validation and identity deduplication before shuffling any labels.
    cohort = evaluate(rows, target, "formula")["training"]
    counts = Counter(row["scaffold"] for row in cohort)
    largest = min(counts, key = lambda scaffold: (-counts[scaffold], scaffold)) if counts else None
    reports = []

    def compare(compounds, scenario, folds = 5, iteration = None, permutation_seed = None):
        for representation in REPRESENTATIONS:
            report = evaluate(compounds, target, representation, folds = folds)["report"]
            reports.append({"scenario": scenario, "iteration": iteration,
                            "permutation_seed": permutation_seed,
                            "omitted_scaffold": largest if scenario == "omit_largest_scaffold"
                            else None, **report})

    compare(cohort, "common")
    compare(cohort, "common_3fold", folds = 3)
    compare(cohort, "common_10fold", folds = 10)
    compare([row for row in cohort if row["scaffold"] != largest], "omit_largest_scaffold")
    labels = [row[target] for row in cohort]
    for iteration in range(permutations):
        seed = SEED + iteration
        shuffled = np.random.default_rng(seed).permutation(labels)
        control = [{**row, target: int(label)} for row, label in zip(cohort, shuffled, strict = True)]
        compare(control, "shuffled_labels", iteration = iteration, permutation_seed = seed)
    return reports


def run(features, output, target = "selection_target", permutations = 20):
    """Write diagnostics from an existing structural-feature Parquet, offline."""
    features, output = Path(features).resolve(), Path(output).resolve()
    if features.is_relative_to(output):
        raise ValueError("Output must be outside input paths")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use an empty output directory")
    reports = stress(pl.read_parquet(features).to_dicts(), target, permutations)
    output.mkdir(parents = True, exist_ok = True)
    write_csv(output / "stress_models.csv", reports, list(reports[0]))
    manifest = {
        "input_hashes": hashes([features]), "code_hashes": hashes(list(HERE.glob("*.py"))),
        "lock_hashes": hashes([HERE / "uv.lock", HERE / "pyproject.toml"]),
        "output_hashes": hashes([output / "stress_models.csv"]),
        "versions": {name: version(name) for name in ("rdkit", "scikit-learn", "numpy", "polars")},
        "seed": SEED, "target": target, "permutations": permutations,
        "scope": "exploratory sensitivity; selection membership is not herbicidal activity",
        "reports": reports,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent = 2, allow_nan = False) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument("--features", type = Path, required = True)
    parser.add_argument("--output", type = Path, required = True)
    parser.add_argument("--target", default = "selection_target",
                        choices = ["selection_target", "activity_target", "origin_target"])
    parser.add_argument("--permutations", type = int, default = 20)
    args = parser.parse_args()
    manifest = run(args.features, args.output, args.target, args.permutations)
    print(f"Wrote {len(manifest['reports'])} diagnostic rows to {args.output}")


if __name__ == "__main__":
    main()
