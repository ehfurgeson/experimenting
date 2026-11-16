"""Analyze selected cached EPA hazard evidence without network requests."""

import argparse
from pathlib import Path

from agrotox import __version__
from agrotox.coverage import load_definitions
from agrotox.epa_workflow import build_epa_hazard_offline
from agrotox.inputs import load_queries
from agrotox.storage import save_table


def main() -> None:
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument("--data", type = Path, required = True)
    parser.add_argument("--input", type = Path, required = True)
    parser.add_argument("--definitions", type = Path,
                        default = Path(__file__).with_name("endpoints.yaml"))
    parser.add_argument("--output", type = Path, help = "Optional directory for Parquet products")
    args = parser.parse_args()
    analysis = build_epa_hazard_offline(
        args.data, load_queries(args.input), load_definitions(args.definitions),
    )
    print("EPA hazard coverage (all selected compounds are in the denominator):")
    for row in analysis["coverage_by_group"].to_dicts():
        print(row)
    print("Review states:")
    print(analysis["audit"].group_by("availability_reason").len())
    if args.output is not None:
        package = Path(__file__).resolve().parents[1] / "src" / "agrotox"
        sources = [*(Path(path) for path in analysis.dependencies),
                   args.input, args.definitions, Path(__file__), *sorted(package.rglob("*.py"))]
        for name, frame in analysis.tables.items():
            save_table(args.output / f"{name}.parquet", frame, sources,
                       code_version = __version__)
        print(f"Saved {len(analysis.tables)} tables and dependency sidecars to {args.output}")


if __name__ == "__main__":
    main()
