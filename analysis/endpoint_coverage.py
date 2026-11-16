"""Compare all seven endpoints using current raw evidence and equal denominators.

    uv run --project pipeline python analysis/endpoint_coverage.py
"""

import csv
from pathlib import Path

from endpoint_analysis import build_sources, export_epa

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
DEFINITIONS = HERE.parent / "pipeline" / "examples" / "endpoints.yaml"
OUTPUT = DATA / "epa_endpoint_coverage.csv"


def main() -> None:
    definitions, pubchem, epa = build_sources(DATA, DEFINITIONS)
    if epa is None:
        raise SystemExit("Run 03_fetch_epa.py first: no EPA identity crosswalk.")
    export_epa(epa, DATA, DEFINITIONS, output_data = OUTPUT.parent)
    rows = []
    for source, analysis in [("pubchem", pubchem), ("epa_hazard", epa)]:
        for row in analysis["coverage_by_group"].iter_rows(named = True):
            rows.append({"source": source, **row})
        counts = {name: int(analysis["coverage"][name].sum()) for name in definitions}
        print(f"{source}: {counts}")
    with OUTPUT.open("w", encoding = "utf-8", newline = "") as stream:
        writer = csv.DictWriter(stream, fieldnames = [
            "source", "chemical_group", "endpoint", "compounds_with_data", "total_compounds",
        ])
        writer.writeheader()
        writer.writerows(rows)
    print("Both sources retain every selected compound in the denominator.")
    print("PubChem chronic zeros reflect acute-only prose extraction.")
    print("Chronic policies count availability; their potency medians remain null.")
    print(epa["audit"].group_by("availability_reason").len())
    print(f"wrote {len(rows)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
