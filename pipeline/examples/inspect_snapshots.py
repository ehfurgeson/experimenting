"""Inspect cached compounds, annotations, and normalized review rows offline."""

import argparse
import json
from pathlib import Path

import polars as pl

from agrotox.coverage import coverage_tables, load_definitions, matching_expr
from agrotox.inputs import load_queries, merge_queries
from agrotox.normalize import normalize_rows
from agrotox.workflow import parse_snapshots


def main() -> None:
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument("--data", type = Path, required = True, help = "Existing data root")
    parser.add_argument("--input", type = Path, help = "Curated CSV or TXT query file")
    parser.add_argument("--definitions", type = Path, help = "YAML coverage policies")
    parser.add_argument("queries", nargs = "*", help = "Additional selected names or CIDs")
    args = parser.parse_args()
    queries = load_queries(args.input) if args.input is not None else []
    queries = merge_queries([*queries, *({"query": query} for query in args.queries)])
    if not queries:
        parser.error("Supply at least one query or a nonempty --input file")
    annotations, compounds = parse_snapshots(args.data, queries)
    measurements = normalize_rows(annotations, compounds)
    print(f"Compounds: {compounds.height}; annotations: {annotations.height}")
    counts = {
        status: measurements.filter(pl.col("parse_status") == status).height
        for status in ["complete", "partial", "failed"]
    }
    print(
        f"Normalized rows: {measurements.height} (complete: {counts['complete']}, "
        f"partial: {counts['partial']}, failed: {counts['failed']})"
    )
    print(compounds.select(
        "compound_id", "input_queries", "resolution_status", "toxicity_status",
    ))
    print("Per-compound extraction counts (annotations are not independent studies):")
    for compound in compounds.to_dicts():
        rows = measurements.filter(pl.col("compound_id") == compound["compound_id"])
        print(json.dumps({
            "compound_id": compound["compound_id"], "input_queries": compound["input_queries"],
            "preferred_name": compound["preferred_name"], "annotations": rows.height,
            **{status: rows.filter(pl.col("parse_status") == status).height
               for status in ["complete", "partial", "failed"]},
        }, ensure_ascii = False))
    if args.definitions is not None:
        definitions = load_definitions(args.definitions)
        matrix, groups = coverage_tables(compounds, measurements, definitions)
        print("Coverage matrix (1 = at least one eligible annotation; 0 = no match):")
        for row in matrix.to_dicts():
            print(json.dumps(row, ensure_ascii = False))
        print("Group counts (denominators include unresolved and zero-data compounds):")
        for row in groups.to_dicts():
            print(json.dumps(row, ensure_ascii = False))
        print("Matching evidence (up to one example per compound and policy):")
        for name, definition in definitions.items():
            selected = measurements.filter(matching_expr(definition)).unique(
                subset = "compound_id", keep = "first", maintain_order = True,
            )
            for row in selected.to_dicts():
                print(json.dumps({
                    "policy": name, **{field: row[field] for field in [
                        "compound_id", "annotation_id", "endpoint", "species", "exposure_route",
                        "duration_hours", "qualifier", "value_standardized",
                        "value_lower_standardized", "value_upper_standardized", "unit_standardized",
                        "value_raw", "reference_numbers", "raw_file",
                    ]},
                    "sources": [{key: source[key] for key in (
                        "reference_number", "source_name", "source_url",
                    )} for source in row["sources"]],
                }, ensure_ascii = False, indent = 2))
    print("Normalization previews (one per category, source text limited to 200 characters):")
    complete = pl.col("parse_status") == "complete"
    categories = [
        ("exact", complete & (pl.col("qualifier") == "=")),
        ("threshold (check status)", pl.col("qualifier").is_in(["<", ">", "<=", ">="])),
        ("range (check status)", pl.col("qualifier") == "range"),
        ("partial", pl.col("parse_status") == "partial"),
        ("failed", pl.col("parse_status") == "failed"),
    ]
    for category, condition in categories:
        sample = measurements.filter(condition).head(1).to_dicts()
        if not sample:
            continue
        row = sample[0]
        print(json.dumps({
            "category": category,
            "annotation_id": row["annotation_id"], "compound_id": row["compound_id"],
            "value_raw": row["value_raw"][:200], "section_path": row["section_path"],
            **{field: row[field] for field in [
                "endpoint", "species", "organism_group", "exposure_route", "duration_hours",
                "medium", "value_numeric", "value_lower", "value_upper", "unit_raw", "qualifier",
                "value_standardized", "value_lower_standardized", "value_upper_standardized",
                "unit_standardized", "formulation_flag", "parse_status", "parse_note",
            ]},
            "reference_numbers": row["reference_numbers"],
            "sources": [{key: source[key] for key in (
                "reference_number", "source_name", "source_url",
            )} for source in row["sources"]],
            "raw_file": row["raw_file"],
        }, ensure_ascii = False, indent = 2))


if __name__ == "__main__":
    main()
