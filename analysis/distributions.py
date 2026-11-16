"""Describe the trait distributions of each group.

    uv run --project pipeline python analysis/distributions.py
"""

import csv
from pathlib import Path

import polars as pl

from endpoint_analysis import display_number, numeric_traits, trait_kind
from stats import summarize

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
COMPOUNDS = DATA / "compound_traits.parquet"
OUTPUT = DATA / "distributions.csv"
GROUPS = ("herbicide", "natural_product")
SKIP = {"pubchem_cid", "hrac_group"}


def main() -> None:
    frame = pl.read_parquet(COMPOUNDS)
    rows = []
    for trait in numeric_traits(frame):
        for group in GROUPS:
            subset = frame.filter(pl.col("chemical_group") == group)
            statistics = summarize(subset[trait].to_list())
            rows.append({
                "trait": trait, "kind": trait_kind(trait),
                "chemical_group": group,
                "n_selected": subset.height,
                "n_present": statistics["n_present"],
                "n_missing": subset.height - statistics["n_present"],
                "mean": statistics["mean"], "sd": statistics["sd"], "min": statistics["min"],
                "q25": statistics["q25"], "median": statistics["median"],
                "q75": statistics["q75"], "max": statistics["max"],
            })
    with OUTPUT.open("w", encoding = "utf-8", newline = "") as stream:
        writer = csv.DictWriter(stream, fieldnames = [
            "trait", "kind", "chemical_group", "n_selected", "n_present", "n_missing",
            "mean", "sd", "min", "q25", "median", "q75", "max",
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"{'trait':34} {'group':17} {'n':>4} {'median':>12} {'q25':>12} {'q75':>12}")
    print("-" * 96)
    for row in rows:
        print(f"{row['trait']:34} {row['chemical_group']:17} {row['n_present']:>4}"
              f" {display_number(row['median']):>12} {display_number(row['q25']):>12}"
              f" {display_number(row['q75']):>12}")
    print(f"\nwrote {len(rows)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
