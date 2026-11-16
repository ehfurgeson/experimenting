"""Offline structural screening from CSV/Parquet compounds and reviewed labels."""
import argparse
import csv
import hashlib
import json
from importlib.metadata import version
from pathlib import Path

import polars as pl

from formula import formula_features
from labels import LABEL_FIELDS, attach_labels, selection_target
from structure import structure_features
from structure_models import REPRESENTATIONS, SEED, eligible, evaluate, feature_matrix

HERE = Path(__file__).resolve().parent
OOF_COLUMNS = ["compound_id", "target", "representation", "label", "fold", "scaffold",
               "probability", "baseline_prediction"]
SCORE_COLUMNS = ["compound_id", "representation", "status", "probability",
                 "nearest_training_tanimoto", "scaffold_seen"]


def prepare(records):
    """Retain failures and cross-check supplied formula/InChIKey against SMILES."""
    rows = []
    for record in records:
        smiles = next((record[key] for key in ("canonical_smiles", "smiles", "connectivity_smiles")
                       if record.get(key)), None)
        chemistry = structure_features(smiles)
        cached = formula_features(record.get("molecular_formula"))
        comparison = "unavailable"
        if cached["formula_status"] == chemistry["formula_status"] == "valid":
            comparison = ("match" if cached["formula_composition"] == chemistry["formula_composition"]
                          else "mismatch")
        key = record.get("inchikey")
        key_conflict = bool(key and chemistry["structure_inchikey"]
                            and key != chemistry["structure_inchikey"])
        if comparison == "mismatch" or key_conflict:
            chemistry["structure_status"] = "identity_mismatch"
        rows.append({
            **{key: record.get(key) for key in ("compound_id", "query", "chemical_group",
                                               "molecular_formula", "inchikey")},
            "input_smiles": smiles, "input_formula_status": cached["formula_status"],
            "formula_comparison": comparison, "inchikey_conflict": key_conflict,
            **chemistry, "selection_target": selection_target(record),
        })
    return attach_labels(rows, [])  # validate unique nonempty IDs even without reviews


def score_candidates(result, candidates):
    """Score only reviewed activity models; attach simple structural-domain context."""
    if result["report"]["target"] != "activity_target":
        raise ValueError("Candidate screening requires an activity_target model")
    representation = result["report"]["representation"]
    training = result["training"]
    identities = {row["canonical_structure"] for row in training}
    scaffolds = {row["scaffold"] for row in training}
    scores = []
    for row in candidates:
        score = {"compound_id": row["compound_id"], "representation": representation,
                 "status": "activity_model_unavailable", "probability": None,
                 "nearest_training_tanimoto": None, "scaffold_seen": None}
        if not eligible(row, representation):
            score["status"] = (row["structure_status"] if row["structure_status"] != "valid"
                               else "unsupported_formula")
        elif row["canonical_structure"] in identities:
            score["status"] = "already_labeled_structure"
        elif result["estimator"] is not None:
            similarities = []
            for known in training:
                pairs = list(zip(row["fingerprint"], known["fingerprint"], strict = True))
                intersection = sum(a and b for a, b in pairs)
                union = sum(a or b for a, b in pairs)
                similarities.append(intersection / union if union else 1.0)
            score.update(
                status = "scored_exploratory",
                probability = float(result["estimator"].predict_proba(
                    feature_matrix([row], representation))[0, 1]),
                nearest_training_tanimoto = max(similarities),
                scaffold_seen = row["scaffold"] in scaffolds,
            )
        scores.append(score)
    return scores


def read_records(path):
    if path.suffix == ".parquet":
        return pl.read_parquet(path).to_dicts()
    if path.suffix == ".csv":
        with path.open(encoding = "utf-8-sig", newline = "") as stream:
            return list(csv.DictReader(stream))
    raise ValueError("Inputs must be .csv or .parquet")


def write_csv(path, rows, columns):
    with path.open("w", encoding = "utf-8", newline = "") as stream:
        writer = csv.DictWriter(stream, fieldnames = columns)
        writer.writeheader()
        writer.writerows(rows)


def hashes(paths):
    return {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}


def run(compounds, output, labels = None, candidates = None):
    """Write an independent product directory without changing any inputs."""
    inputs = [Path(p).resolve() for p in (compounds, labels, candidates) if p is not None]
    output = Path(output).resolve()
    if any(path.is_relative_to(output) for path in inputs):
        raise ValueError("Output must be outside input paths")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use an empty output directory")
    rows = prepare(read_records(inputs[0]))
    if not rows:
        raise ValueError("No compound rows")
    if labels is not None:
        rows = attach_labels(rows, read_records(Path(labels)))
    new = prepare(read_records(Path(candidates))) if candidates is not None else []
    if {row["compound_id"] for row in rows} & {row["compound_id"] for row in new}:
        raise ValueError("Training and candidate compound_id values overlap")
    results = [evaluate(rows, target, representation)
               for target in ("selection_target", "activity_target", "origin_target")
               for representation in REPRESENTATIONS]
    scores = [score for result in results if result["report"]["target"] == "activity_target"
              for score in score_candidates(result, new)]
    output.mkdir(parents = True, exist_ok = True)
    frame = pl.DataFrame(rows, infer_schema_length = None,
                         schema_overrides = {"fingerprint": pl.List(pl.Int8)})
    frame.write_parquet(output / "structural_features.parquet")
    frame.drop("fingerprint").write_csv(output / "structural_features.csv")
    reports = [result["report"] for result in results]
    write_csv(output / "structure_models.csv", reports, list(reports[0]))
    write_csv(output / "out_of_fold.csv", [r for result in results for r in result["oof"]],
              OOF_COLUMNS)
    write_csv(output / "candidate_scores.csv", scores, SCORE_COLUMNS)
    if new:
        pl.DataFrame(new, infer_schema_length = None,
                     schema_overrides = {"fingerprint": pl.List(pl.Int8)}).write_parquet(
                         output / "candidate_features.parquet")
    template = [{"compound_id": row["compound_id"], "natural_origin": "unknown",
                 "herbicidal_activity": "unknown"} for row in rows]
    write_csv(output / "label_review_template.csv", template, ["compound_id"] + sorted(
        LABEL_FIELDS - {"compound_id"}))
    manifest = {
        "input_hashes": hashes(inputs), "code_hashes": hashes(list(HERE.glob("*.py"))),
        "lock_hashes": hashes([HERE / "uv.lock", HERE / "pyproject.toml"]),
        "output_hashes": hashes(list(output.iterdir())),
        "versions": {name: version(name) for name in ("rdkit", "scikit-learn", "numpy", "polars")},
        "seed": SEED, "folds": 5, "pca_training_variance": .95,
        "scope": "exploratory; selection membership is not herbicidal activity",
        "reports": reports,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent = 2, allow_nan = False) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument("--compounds", type = Path, default = HERE / "data/compound_traits.parquet")
    parser.add_argument("--labels", type = Path)
    parser.add_argument("--candidates", type = Path)
    parser.add_argument("--output", type = Path, default = HERE / "outputs/structure")
    args = parser.parse_args()
    manifest = run(args.compounds, args.output, args.labels, args.candidates)
    for report in manifest["reports"]:
        print(report["target"], report["representation"], report["status"],
              "n=", report["n"], "balanced_accuracy=", report["balanced_accuracy"])
    print(f"Products: {args.output}")


if __name__ == "__main__":
    main()
