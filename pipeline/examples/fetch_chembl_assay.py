"""Freeze one bounded ChEMBL assay with raw measurements and source provenance."""

import argparse
from pathlib import Path

from agrotox.chembl import fetch_assay


def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument("assay_id", help = "Explicit ChEMBL assay ID")
    parser.add_argument("--data", type = Path, required = True, help = "New snapshot root")
    parser.add_argument("--max-activities", type = int, default = 10000)
    parser.add_argument("--page-size", type = int, default = 1000)
    args = parser.parse_args()
    print(fetch_assay(args.data, args.assay_id, max_activities = args.max_activities,
                      page_size = args.page_size))


if __name__ == "__main__":
    main()
