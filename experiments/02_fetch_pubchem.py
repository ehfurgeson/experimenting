"""Retrieve the PubChem evidence for the curated compound list.

Uses the pipeline's own retrieval stage, so the snapshots are the same validated
bundles the analysis stages read. The data root is inside this directory and is
never committed.

    uv run --project pipeline python experiments/02_fetch_pubchem.py
    uv run --project pipeline python experiments/02_fetch_pubchem.py --group natural_product
"""

import argparse
import csv
import json
from pathlib import Path

from agrotox.inputs import load_queries
from agrotox.retrieval import fetch_one
from agrotox.sources.pubchem import PubChemClient

HERE = Path(__file__).resolve().parent
SELECTION = HERE / "data" / "compounds.csv"
DATA_ROOT = HERE / "data"
FAILURES = HERE / "data" / "pubchem_failures.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument("--group", choices = ["herbicide", "natural_product"],
                        help = "Only fetch one group")
    parser.add_argument("--limit", type = int, help = "Only fetch the first N compounds")
    args = parser.parse_args()

    queries = load_queries(SELECTION)
    if args.group:
        queries = [query for query in queries if query.get("chemical_group") == args.group]
    if args.limit:
        queries = queries[:args.limit]
    if not queries:
        parser.error("The selection is empty")

    source = PubChemClient()
    failures = []
    for index, query in enumerate(queries, start = 1):
        outcome = fetch_one(source, DATA_ROOT, query)
        if outcome["status"] == "error":
            failures.append(outcome)
        print(
            f"[{index}/{len(queries)}] {outcome['status']:>7} {outcome['query']}"
            f"  cid={outcome['cid']}  {outcome['message'] or ''}",
            flush = True,
        )
    if failures:
        with FAILURES.open("w", encoding = "utf-8", newline = "") as stream:
            writer = csv.DictWriter(stream, fieldnames = [
                "query", "cid", "status", "stage", "error_type", "message",
            ])
            writer.writeheader()
            writer.writerows(failures)
    summary = {
        "requested": len(queries),
        "failed": len(failures),
        "failure_file": str(FAILURES) if failures else None,
    }
    print(json.dumps(summary, indent = 2))


if __name__ == "__main__":
    main()
