"""Rebuild review materials from frozen ChEMBL assay bundles, offline."""

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timedelta
from pathlib import Path

from labels import LABEL_FIELDS
from screen import HERE, hashes, write_csv

ACTIVITY_FIELDS = ["activity_id", "assay_chembl_id", "molecule_chembl_id", "canonical_smiles",
                   "standard_type", "standard_relation", "standard_value", "standard_units",
                   "activity_comment", "data_validity_comment", "potential_duplicate",
                   "document_chembl_id"]
REVIEW_FIELDS = ACTIVITY_FIELDS + ["assay_description", "assay_organism", "doi", "document_title",
                                  "document_year", "chembl_db_version", "retrieved_at",
                                  "snapshot_path", "snapshot_sha256", "raw_activity_json"]


def _object(value, name):
    if not isinstance(value, dict):
        raise ValueError(f"Expected a saved {name} object")  # noqa: TRY004
    return value


def _identity(value):
    if not isinstance(value, str) or not re.fullmatch(r"CHEMBL[1-9][0-9]*", value):
        raise ValueError(f"Expected a positive ChEMBL ID: {value!r}")
    return value


def _reject_constant(value):
    raise ValueError(f"Nonstandard JSON number: {value}")


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"Nonfinite JSON number: {value}")
    return number


def _records(payload, path):
    """Check completeness and source identity without interpreting assay outcomes."""
    bundle = _object(payload, "snapshot")
    if bundle.get("source") != "ChEMBL":
        raise ValueError("Expected ChEMBL snapshot source")
    status = _object(bundle.get("status"), "version status")
    if not isinstance(status.get("chembl_db_version"), str) or not status["chembl_db_version"].strip():
        raise ValueError("Missing ChEMBL database version")
    try:
        stamp = datetime.fromisoformat(bundle["retrieved_at"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Snapshot requires a UTC retrieval timestamp") from error
    if stamp.utcoffset() != timedelta(0):
        raise ValueError("Snapshot retrieval timestamp must be aware UTC")
    assay = _object(bundle.get("assay"), "assay")
    if _identity(assay.get("assay_chembl_id")) != path.stem:
        raise ValueError("Snapshot filename does not match assay identity")
    document = _object(bundle.get("document"), "document")
    document_id = _identity(assay.get("document_chembl_id"))
    if document.get("document_chembl_id") != document_id:
        raise ValueError("Snapshot document identity mismatch")
    count, pages = bundle.get("activity_count"), bundle.get("activity_pages")
    if type(count) is not int or count < 0:
        raise ValueError("Invalid snapshot activity count")
    if not isinstance(pages, list) or not pages:
        raise ValueError("Snapshot requires complete activity pages")
    rows, seen = [], set()
    for page in pages:
        page = _object(page, "page")
        meta = _object(page.get("page_meta"), "page metadata")
        if type(meta.get("total_count")) is not int or meta["total_count"] != count:
            raise ValueError("Snapshot page count mismatch")
        if type(meta.get("offset")) is not int or meta["offset"] != len(rows):
            raise ValueError("Snapshot page offset mismatch")
        records = page.get("activities")
        if not isinstance(records, list) or not records and (count != 0 or len(pages) != 1):
            raise ValueError("Incomplete snapshot activity page")
        for record in records:
            record = _object(record, "activity")
            identity = record.get("activity_id")
            if type(identity) is not int or identity <= 0 or identity in seen:
                raise ValueError("Invalid or duplicate activity_id")
            if record.get("assay_chembl_id") != path.stem:
                raise ValueError("Activity assay identity mismatch")
            if record.get("document_chembl_id") != document_id:
                raise ValueError("Activity document identity mismatch")
            _identity(record.get("molecule_chembl_id"))
            smiles = record.get("canonical_smiles")
            if smiles is not None and not isinstance(smiles, str):
                raise ValueError("Source SMILES must be text or null")
            for key in ACTIVITY_FIELDS:
                if isinstance(record.get(key), (list, dict)):
                    raise ValueError(f"Expected a scalar review field: {key}")  # noqa: TRY004
            seen.add(identity)
            rows.append(record)
    if len(rows) != count:
        raise ValueError("Snapshot activity count does not match saved pages")
    return rows


def run(snapshots, output):
    """Validate frozen snapshots before exporting evidence and unknown labels."""
    snapshots, output = Path(snapshots).resolve(), Path(output).resolve()
    if snapshots.is_relative_to(output) or output.is_relative_to(snapshots):
        raise ValueError("Output and snapshot roots must be separate")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use an empty output directory")
    paths = sorted((snapshots / "raw" / "chembl").glob("*.json"))
    if not paths:
        raise ValueError("No ChEMBL snapshots found under raw/chembl")
    review, candidates, inputs, seen, versions = [], {}, {}, set(), set()
    for path in paths:
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        try:
            bundle = json.loads(data, parse_constant = _reject_constant, parse_float = _finite_float)
        except (UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(f"Invalid JSON snapshot {path}: {error}") from error
        records = _records(bundle, path)
        inputs[str(path.resolve())] = digest
        version = bundle["status"]["chembl_db_version"]
        versions.add(version)
        if len(versions) > 1:
            raise ValueError("Use one ChEMBL database version per review export")
        assay, document = bundle["assay"], bundle["document"]
        for record in records:
            identity = record["activity_id"]
            if identity in seen:
                raise ValueError("Duplicate activity_id across snapshots")
            seen.add(identity)
            compound = record["molecule_chembl_id"]
            smiles = record.get("canonical_smiles") or None
            if smiles is not None and not smiles.strip():
                smiles = None
            previous = candidates.get(compound)
            if previous and smiles and previous != smiles:
                raise ValueError(f"Conflicting source SMILES for {compound}")
            candidates[compound] = previous or smiles
            review.append({
                **{key: record.get(key) for key in ACTIVITY_FIELDS},
                "assay_description": assay.get("description"),
                "assay_organism": assay.get("assay_organism"), "doi": document.get("doi"),
                "document_title": document.get("title"), "document_year": document.get("year"),
                "chembl_db_version": version, "retrieved_at": bundle["retrieved_at"],
                "snapshot_path": str(path.resolve()), "snapshot_sha256": digest,
                "raw_activity_json": json.dumps(record, ensure_ascii = False, sort_keys = True,
                                                 allow_nan = False),
            })
    compounds = [{"compound_id": identity, "canonical_smiles": candidates[identity]}
                 for identity in sorted(candidates)]
    labels = [{"compound_id": row["compound_id"], "natural_origin": "unknown",
               "herbicidal_activity": "unknown"} for row in compounds]
    output.mkdir(parents = True, exist_ok = True)
    write_csv(output / "activity_review.csv", sorted(review, key = lambda r: r["activity_id"]),
              REVIEW_FIELDS)
    write_csv(output / "candidates.csv", compounds, ["compound_id", "canonical_smiles"])
    write_csv(output / "label_review_template.csv", labels,
              ["compound_id"] + sorted(LABEL_FIELDS - {"compound_id"}))
    manifest = {
        "input_hashes": inputs, "code_hashes": hashes(list(HERE.glob("*.py"))),
        "lock_hashes": hashes([HERE / "uv.lock", HERE / "pyproject.toml"]),
        "output_hashes": hashes(list(output.iterdir())), "assays": len(paths),
        "activity_records": len(review), "compounds": len(compounds),
        "missing_structures": sum(row["canonical_smiles"] is None for row in compounds),
        "database_version": next(iter(versions)),
        "scope": "Unreviewed assay evidence; activity and natural-origin labels remain unknown.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent = 2, allow_nan = False) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument("--snapshots", type = Path, required = True)
    parser.add_argument("--output", type = Path, required = True)
    args = parser.parse_args()
    manifest = run(args.snapshots, args.output)
    print(f"Wrote {manifest['activity_records']} review rows and {manifest['compounds']} candidates")


if __name__ == "__main__":
    main()
