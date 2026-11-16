"""Rebuild source-specific endpoint evidence from selected raw caches."""

from pathlib import Path

from agrotox import __version__
from agrotox.coverage import load_definitions
from agrotox.epa_workflow import build_epa_hazard_offline
from agrotox.inputs import load_queries
from agrotox.storage import save_table
from agrotox.workflow import build_offline


def build_sources(data: Path, definitions_path: Path):
    """Return current PubChem and optional EPA analyses on the same selection.

    A missing crosswalk means EPA was not run; a missing approved hazard cache
    remains an error. Processed legacy experiment products are never consumed.
    """
    queries = load_queries(data / "compounds.csv")
    definitions = load_definitions(definitions_path)
    pubchem = build_offline(data, queries, definitions)
    epa = None
    if (data / "epa_identity_crosswalk.parquet").exists():
        epa = build_epa_hazard_offline(data, queries, definitions)
    return definitions, pubchem, epa


def export_epa(analysis, data: Path, definitions_path: Path, *, output_data: Path | None = None):
    """Save normalized EPA evidence, reviews, and context-aware summaries."""
    import agrotox

    package = Path(agrotox.__file__).resolve().parent
    sources = [*(Path(path) for path in analysis.dependencies),
               data / "compounds.csv", definitions_path, Path(__file__),
               *sorted(package.rglob("*.py"))]
    destination = output_data if output_data is not None else data
    for name, frame in analysis.tables.items():
        save_table(destination / "epa_analysis" / f"{name}.parquet", frame, sources,
                   code_version = __version__)


def add_endpoint_traits(rows, definitions, pubchem, epa):
    """Attach source flags and their union, preserving unassessed states as null.

    A union is positive when either source has evidence, zero when both were
    assessed without a match, and otherwise unknown. No potency is inferred.
    """
    pubchem_by_id = {row["compound_id"]: row for row in pubchem["coverage"].to_dicts()}
    epa_by_id = {row["compound_id"]: row for row in epa["coverage"].to_dicts()} if epa else {}
    epa_assessed = {row["compound_id"]: row["epa_identity_status"] == "approved"
                    for row in epa["audit"].to_dicts()} if epa else {}
    for row in rows:
        compound_id = row["compound_id"]
        pubchem_assessed = (row["resolution_status"] == "resolved"
                            and row["toxicity_status"] in {"found", "missing"})
        for name in definitions:
            pc = pubchem_by_id[compound_id][name] if pubchem_assessed else None
            ep = epa_by_id[compound_id][name] if epa_assessed.get(compound_id) else None
            row[f"has_pubchem_{name}"] = pc
            row[f"has_epa_{name}"] = ep
            row[f"has_{name}"] = 1 if pc == 1 or ep == 1 else 0 if pc == ep == 0 else None
    return rows


def numeric_traits(frame):
    """Include numeric traits and all-null endpoint flags, excluding identifiers."""
    return [name for name, dtype in frame.schema.items()
            if name not in {"pubchem_cid", "hrac_group"}
            and (dtype.is_numeric() or name.startswith("has_"))]


def trait_kind(name):
    """Separate chemistry, evidence availability, and assay activity."""
    if name.startswith("has_"):
        return "endpoint_availability"
    if name == "toxcast_inactive_fraction":
        return "assay_activity"
    if name.startswith(("epa_", "toxcast_", "distinct_")) or name in {
        "annotation_count", "complete_count", "partial_count", "failed_count",
    }:
        return "study_coverage"
    return "molecular_property"


def display_number(value):
    return "NA" if value is None else f"{value:.4g}"
