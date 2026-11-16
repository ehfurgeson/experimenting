"""Fetch selected PubChem snapshots, reusing validated cached bundles on reruns."""

import argparse
import json
from pathlib import Path

from agrotox.inputs import load_queries, merge_queries
from agrotox.retrieval import fetch_one
from agrotox.sources.pubchem import PubChemClient


def main() -> None:
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument("--data", type = Path, required = True, help = "Snapshot data root")
    parser.add_argument("--input", type = Path, help = "Curated CSV or TXT selection")
    parser.add_argument("queries", nargs = "*", help = "Additional names or explicit CIDs")
    args = parser.parse_args()
    queries = merge_queries([
        *(load_queries(args.input) if args.input is not None else []),
        *({"query": query} for query in args.queries),
    ])
    if not queries:
        parser.error("Supply at least one query or a nonempty --input file")
    source = PubChemClient()
    failed = False
    for query in queries:
        outcome = fetch_one(source, args.data, query)
        print(json.dumps(outcome, ensure_ascii = False), flush = True)
        failed = failed or outcome["status"] == "error"
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
