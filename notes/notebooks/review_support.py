"""Read-only helpers for the local professor review; no fitting or acquisition."""
import hashlib
import json
from pathlib import Path

import polars as pl
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    roc_auc_score,
)

BUNDLES = {
    "baseline": "structure-2026-10-28-stress-baseline",
    "stress": "stress-2026-10-28",
    "fixed": "ablations-fixed-2026-10-29-final",
    "nested": "ablations-nested-2026-10-29-final",
    "review": "chembl-review-2026-10-29-final",
    "review_screen": "chembl-review-screen-2026-10-29-final",
}
PROFILES = {
    "formula": "Formula · PCA",
    "descriptors": "Descriptors · PCA",
    "morgan": "Morgan · PCA",
    "combined": "All features · joint PCA",
    "formula_descriptors": "Formula + descriptors · PCA",
    "formula_morgan": "Formula + Morgan · PCA",
    "combined_formula_outside_pca": "All · formula preserved",
    "combined_morgan_pca": "All · only Morgan PCA",
    "formula_morgan_pca": "Formula + Morgan · only Morgan PCA",
}
FEATURES = {
    "Distinct elements": "element_count",
    "Nitrogen atoms": "formula_N_count",
    "Chlorine atoms": "formula_Cl_count",
    "Molecular weight": "mw",
    "RDKit logP": "logp",
    "Polar surface area": "tpsa",
    "Synthetic accessibility (1 easy → 10 difficult)": "sa_score",
    "Lipinski violations": "lipinski_violations",
    "Tice-inspired proxy violations": "tice_proxy_violations",
    "Rotatable bonds": "rotatable_bonds",
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def resolve_recorded(root, bundle, recorded, section):
    """Map project-relative dependencies without rewriting historical manifests."""
    path = Path(recorded)
    if section == "output_hashes":
        return bundle / path.name
    parts = path.parts
    for marker in ("analysis", "pipeline", "notes", "experiments"):
        if marker in parts:
            return root.joinpath(*parts[parts.index(marker):])
    return path if path.is_absolute() else root / path


def load_review(root):
    root = Path(root).resolve()
    frames, audit = {}, []
    for key, name in BUNDLES.items():
        bundle = root / "analysis/outputs" / name
        manifest_path = bundle / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        for section in ("output_hashes", "input_hashes", "code_hashes", "lock_hashes"):
            for recorded, expected in manifest.get(section, {}).items():
                path = resolve_recorded(root, bundle, recorded, section)
                status = "missing" if not path.exists() else (
                    "matches" if digest(path) == expected else "changed"
                )
                audit.append({"bundle": key, "kind": section, "path": str(path.relative_to(root)),
                              "status": status, "recorded_sha256": expected})
                if section == "output_hashes" and status != "matches":
                    raise ValueError(f"Frozen product {status}: {path}")
        for path in sorted(bundle.glob("*.csv")):
            if path.name not in {Path(p).name for p in manifest["output_hashes"]}:
                continue
            frames[f"{key}/{path.stem}"] = pl.read_csv(
                path, infer_schema_length = None, null_values = "",
            )
    prepared = root / "analysis/data/compound_traits.csv"
    prepared_manifest = root / "analysis/data/manifest.json"
    if prepared.exists() and prepared_manifest.exists():
        metadata = json.loads(prepared_manifest.read_text())
        expected = next((value for key, value in metadata["output_hashes"].items()
                         if Path(key).name == prepared.name), None)
        if expected is None or digest(prepared) != expected:
            raise ValueError("Prepared trait CSV does not match its saved manifest.")
        frames["presentation/traits"] = pl.read_csv(prepared, infer_schema_length = None)
        audit.append({"bundle": "presentation", "kind": "output_hashes",
                      "path": str(prepared.relative_to(root)), "status": "matches",
                      "recorded_sha256": expected})
    working = root / "analysis/outputs/chembl-researcher-handoff-2026-10-29/reviewed_labels.csv"
    label_path = working if working.exists() else (
        root / "analysis/outputs" / BUNDLES["review"] / "label_review_template.csv"
    )
    frames["working_labels"] = pl.read_csv(label_path)
    fixed_cohort = frames["fixed/cohort"].sort("compound_id")
    if not fixed_cohort.equals(frames["nested/cohort"].sort("compound_id")):
        raise ValueError("Fixed and nested cohorts differ; do not compare as matched runs.")
    assignments = None
    for mode in ("fixed", "nested"):
        for profile in PROFILES:
            oof = frames[f"{mode}/out_of_fold"].filter(pl.col("profile") == profile)
            if oof.height != fixed_cohort.height or oof["compound_id"].n_unique() != oof.height:
                raise ValueError(f"Incomplete/duplicate held-out predictions: {mode}/{profile}")
            if set(oof["compound_id"]) != set(fixed_cohort["compound_id"]):
                raise ValueError("Held-out prediction identities differ from the declared cohort.")
            assignment = oof.select("compound_id", "label", "scaffold", "fold").sort("compound_id")
            if assignments is None:
                assignments = assignment
            elif not assignments.equals(assignment):
                raise ValueError("Profile/mode folds or labels differ; matched comparison unavailable.")
            if oof.group_by("scaffold").agg(pl.col("fold").n_unique()).filter(
                pl.col("fold") > 1
            ).height:
                raise ValueError("Scaffold crosses outer folds.")
            report = frames[f"{mode}/ablation_models"].filter(pl.col("profile") == profile).to_dicts()[0]
            metric = oof_metrics(oof, 0.5)
            for field in ("balanced_accuracy", "roc_auc", "average_precision", "tn", "fp", "fn", "tp"):
                if abs(metric[field] - report[field]) > 1e-10:
                    raise ValueError(f"Saved report disagrees with held-out predictions: {mode}/{profile}/{field}")
    return frames, pl.DataFrame(audit), str(label_path.relative_to(root))


def cohort_features(frames, common = True):
    features = frames["baseline/structural_features"]
    if common:
        return features.join(frames["fixed/cohort"].select("compound_id"), on = "compound_id", how = "inner")
    return features.filter(pl.col("structure_status") == "valid")


def oof_metrics(rows, threshold):
    if rows.is_empty():
        raise ValueError("No held-out predictions for the selected model.")
    y, probabilities = rows["label"].to_numpy(), rows["probability"].to_numpy()
    tn, fp, fn, tp = confusion_matrix(y, probabilities >= threshold, labels = [0, 1]).ravel()
    return {"balanced_accuracy": float(balanced_accuracy_score(y, probabilities >= threshold)),
            "roc_auc": float(roc_auc_score(y, probabilities)),
            "average_precision": float(average_precision_score(y, probabilities)),
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}


def comparison_rows(frames):
    rows = []
    for mode in ("fixed", "nested"):
        for row in frames[f"{mode}/ablation_models"].to_dicts():
            rows.append({**row, "mode": mode, "profile_label": PROFILES[row["profile"]]})
    return pl.DataFrame(rows)


def ecdf_rows(features, key):
    rows = []
    for group in ("herbicide", "natural_product"):
        subset = features.filter(pl.col("chemical_group") == group).filter(pl.col(key).is_not_null())
        values = sorted(subset[key].to_list())
        for i, value in enumerate(values):
            rows.append({"group": group, "value": float(value), "fraction": (i + 1) / len(values),
                         "n": len(values)})
    return rows
