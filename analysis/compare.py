"""Compare the two groups trait by trait, with the uncertainty stated.

    uv run --project pipeline python analysis/compare.py
"""

import csv
from pathlib import Path

import polars as pl

from endpoint_analysis import display_number, numeric_traits, trait_kind
from stats import (
    bootstrap_median_difference,
    clean,
    median,
    permutation_p_value,
    roc_auc,
)

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
COMPOUNDS = DATA / "compound_traits.parquet"
OUTPUT = DATA / "comparison.csv"
GROUPS = ("herbicide", "natural_product")


def main() -> None:
    frame = pl.read_parquet(COMPOUNDS)
    rows = []
    for trait in numeric_traits(frame):
        groups = {}
        for group in GROUPS:
            subset = frame.filter(pl.col("chemical_group") == group)
            groups[group] = clean(subset[trait].to_list())
        difference, low, high = bootstrap_median_difference(
            groups["herbicide"], groups["natural_product"]
        )
        rows.append({
            "trait": trait,
            "kind": trait_kind(trait),
            "n_herbicide": len(groups["herbicide"]),
            "n_natural": len(groups["natural_product"]),
            "median_herbicide": median(groups["herbicide"]),
            "median_natural": median(groups["natural_product"]),
            "median_difference": difference,
            "ci_low": low,
            "ci_high": high,
            "permutation_p": permutation_p_value(
                groups["herbicide"], groups["natural_product"]
            ),
            "auc": roc_auc(groups["herbicide"], groups["natural_product"]),
        })
    with OUTPUT.open("w", encoding = "utf-8", newline = "") as stream:
        writer = csv.DictWriter(stream, fieldnames = [
            "trait", "kind", "n_herbicide", "n_natural", "median_herbicide", "median_natural",
            "median_difference", "ci_low", "ci_high", "permutation_p", "auc",
        ])
        writer.writeheader()
        writer.writerows(rows)

    for kind in ("molecular_property", "endpoint_availability", "study_coverage", "assay_activity"):
        print(f"\n{kind}")
        for row in rows:
            if row["kind"] != kind:
                continue
            print(f"{row['trait']:42} herb={display_number(row['median_herbicide'])}"
                  f" nat={display_number(row['median_natural'])}"
                  f" diff={display_number(row['median_difference'])}"
                  f" CI=[{display_number(row['ci_low'])}, {display_number(row['ci_high'])}]"
                  f" p={display_number(row['permutation_p'])} AUC={display_number(row['auc'])}")
    print(f"\nwrote {len(rows)} rows to {OUTPUT}")
    print(f"Permutation p-values are unadjusted across {len(rows)} traits.")
    print("Binary endpoint distributions describe availability, not toxicity magnitude.")


if __name__ == "__main__":
    main()
