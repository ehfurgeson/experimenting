"""Resolve EPA identities and retrieve the EPA evidence for the curated list.

This step needs an EPA CompTox API key. It is read from the COMPTOX_API_KEY
environment variable, or from the repository's .env file when that variable is
not set. The key is only ever used as a request header: it is never printed,
never written to a file, and never included in an error message.

    uv run --project pipeline python experiments/03_fetch_epa.py

Every later script works without this step and reports which parts of the
analysis are missing rather than pretending they are empty.
"""

import argparse
import json
import os
import time
from pathlib import Path

import polars as pl

from agrotox.epa_hazard import fetch_hazard
from agrotox.epa_identity import resolve_identities
from agrotox.epa_properties import fetch_properties
from agrotox.epa_test import fetch_test_predictions
from agrotox.inputs import load_queries
from agrotox.sources.comptox import ComptoxClient
from agrotox.toxcast import fetch_toxcast
from agrotox.workflow import parse_snapshots

HERE = Path(__file__).resolve().parent
DATA_ROOT = HERE / "data"
SELECTION = DATA_ROOT / "compounds.csv"
ENV_FILE = HERE.parent / ".env"


def load_api_key():
    """Put the EPA key in the environment without ever displaying it."""
    if os.environ.get("COMPTOX_API_KEY"):
        return "environment"
    if not ENV_FILE.exists():
        raise SystemExit(
            "No EPA API key. Set COMPTOX_API_KEY, or add it to the repository .env file."
        )
    for line in ENV_FILE.read_text(encoding = "utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        value = value.strip().strip('"').strip("'")
        if name.strip() == "COMPTOX_API_KEY" and value:
            os.environ["COMPTOX_API_KEY"] = value
            return "file"
    raise SystemExit("The .env file has no COMPTOX_API_KEY entry.")


def write(frame, name):
    """Write a table as Parquet, and a flat CSV beside it for reading."""
    frame.write_parquet(DATA_ROOT / f"{name}.parquet")
    nested = [
        column for column, dtype in frame.schema.items()
        if isinstance(dtype, (pl.List, pl.Struct))
    ]
    if nested:
        frame = frame.with_columns([
            pl.col(column).map_elements(str, return_dtype = pl.String).alias(column)
            for column in nested
        ])
    frame.write_csv(DATA_ROOT / f"{name}.csv")


def main() -> None:
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument("--skip-toxicast", action = "store_true",
                        help = "Do not retrieve ToxCast at all")
    parser.add_argument("--limit", type = int, help = "Only process the first N compounds")
    args = parser.parse_args()

    source = load_api_key()
    print(f"EPA key loaded from the {source}; it is never printed or stored.")

    queries = load_queries(SELECTION)
    if args.limit:
        queries = queries[:args.limit]
    _annotations, compounds = parse_snapshots(DATA_ROOT, queries)
    client = ComptoxClient()
    print(f"compounds with a resolved identity: {compounds.height}", flush = True)

    started = time.monotonic()
    candidates, crosswalk = resolve_identities(DATA_ROOT, compounds, client)
    write(candidates, "epa_identity_candidates")
    write(crosswalk, "epa_identity_crosswalk")
    print("identity status:")
    print(crosswalk.group_by("status").len().sort("status"))
    print(f"identity took {time.monotonic() - started:.0f}s", flush = True)

    if not args.skip_toxicast:
        started = time.monotonic()
        assays, coverage = fetch_toxcast(DATA_ROOT, crosswalk, client)
        write(assays, "toxcast_assays")
        write(coverage, "toxcast_coverage")
        print(f"toxcast rows: {assays.height} in {time.monotonic() - started:.0f}s", flush = True)

    started = time.monotonic()
    hazards, hazard_coverage, comparison = fetch_hazard(DATA_ROOT, crosswalk, client)
    write(hazards, "epa_hazard")
    write(hazard_coverage, "epa_hazard_coverage")
    write(comparison, "epa_hazard_comparison")
    print(f"hazard rows: {hazards.height} in {time.monotonic() - started:.0f}s", flush = True)

    started = time.monotonic()
    properties, property_coverage = fetch_properties(DATA_ROOT, crosswalk, client)
    write(properties, "epa_properties")
    write(property_coverage, "epa_property_coverage")
    print(f"property rows: {properties.height} in {time.monotonic() - started:.0f}s", flush = True)

    predictions, prediction_coverage = fetch_test_predictions(DATA_ROOT, crosswalk, client)
    write(predictions, "epa_test_predictions")
    write(prediction_coverage, "epa_test_coverage")
    print(f"TEST prediction rows: {predictions.height}")

    print(json.dumps({
        "compounds": compounds.height,
        "approved": int(crosswalk["status"].eq("approved").sum()),
        "needs_review": int(crosswalk["status"].eq("needs_review").sum()),
        "unresolved": int(crosswalk["status"].eq("unresolved").sum()),
    }, indent = 2))


if __name__ == "__main__":
    main()
