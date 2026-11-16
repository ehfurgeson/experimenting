"""Collect every trait the pipeline and PubChem can supply for the curated list.

Reads the validated PubChem snapshots through the pipeline's own storage and
analysis stages, adds the computed PubChem descriptors, and writes one
long-form trait table plus one wide compound table. The EPA columns are filled
only when the optional EPA step has been run.

    uv run --project pipeline python analysis/build_traits.py
"""

import csv
import json
from pathlib import Path

import polars as pl
from agrotox.epa_hazard import hazard_coverage

from endpoint_analysis import add_endpoint_traits, build_sources, export_epa

HERE = Path(__file__).resolve().parent
DATA_ROOT = HERE / "data"
SELECTION = DATA_ROOT / "compounds.csv"
CLASSES = DATA_ROOT / "compound_classes.csv"
DEFINITIONS = HERE.parent / "pipeline" / "examples" / "endpoints.yaml"
EXTRA = DATA_ROOT / "raw" / "pubchem_computed"
TRAITS = DATA_ROOT / "traits.parquet"
COMPOUNDS = DATA_ROOT / "compound_traits.parquet"
COMPOUNDS_CSV = DATA_ROOT / "compound_traits.csv"

NUMERIC_COMPUTED = {
    "MolecularWeight": "molecular_weight",
    "XLogP": "xlogp",
    "TPSA": "tpsa",
    "HBondDonorCount": "hbond_donor_count",
    "HBondAcceptorCount": "hbond_acceptor_count",
    "RotatableBondCount": "rotatable_bond_count",
    "HeavyAtomCount": "heavy_atom_count",
    "Complexity": "complexity",
    "Charge": "formal_charge",
    "ExactMass": "exact_mass",
    "MonoisotopicMass": "monoisotopic_mass",
    "DefinedAtomStereoCount": "defined_atom_stereo_count",
    "CovalentUnitCount": "covalent_unit_count",
    "IsotopeAtomCount": "isotope_atom_count",
}
TEXT_COMPUTED = {
    "MolecularFormula": "molecular_formula",
    "SMILES": "canonical_smiles",
    "ConnectivitySMILES": "connectivity_smiles",
    "InChI": "inchi",
    "InChIKey": "inchikey",
    "IUPACName": "iupac_name",
    "Title": "pubchem_title",
}


def as_number(value):
    """Return a numeric value, accepting the numeric strings PubChem returns."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def computed_properties(cid):
    """Read cached descriptors only; absent descriptors remain missing."""
    path = EXTRA / f"{cid}.json"
    if not path.exists():
        print(f"no cached computed descriptors for CID {cid}")
        return {}
    return json.loads(path.read_text(encoding = "utf-8"))


def add_epa_traits(rows, epa):
    """Add the EPA traits to the compound rows, when the EPA step has been run.

    The EPA evidence is optional. A compound without it keeps the PubChem
    traits, and the EPA columns are null rather than zero.
    """
    crosswalk_path = DATA_ROOT / "epa_identity_crosswalk.parquet"
    if epa is None:
        print("no EPA identity crosswalk found; run 03_fetch_epa.py first")
        return rows
    crosswalk = pl.read_parquet(crosswalk_path)
    by_compound = {
        row["compound_id"]: row for row in crosswalk.iter_rows(named = True)
    }
    toxcast_path = DATA_ROOT / "toxcast_coverage.parquet"
    toxcast = (
        pl.read_parquet(toxcast_path) if toxcast_path.exists() else pl.DataFrame()
    )
    toxcast_by_compound = (
        {row["compound_id"]: row for row in toxcast.iter_rows(named = True)}
        if toxcast.height else {}
    )
    hazard = hazard_coverage(epa["hazards"])
    hazard_by_compound = (
        {row["compound_id"]: row for row in hazard.iter_rows(named = True)}
        if hazard.height else {}
    )
    comparison = epa["comparison_records"]
    comparison_counts = (
        {row["compound_id"]: row["len"] for row in comparison.group_by("compound_id").len()
         .iter_rows(named = True)} if comparison.height else {}
    )
    property_path = DATA_ROOT / "epa_property_coverage.parquet"
    properties = pl.read_parquet(property_path) if property_path.exists() else pl.DataFrame()
    property_by_compound = (
        {row["compound_id"]: row for row in properties.iter_rows(named = True)}
        if properties.height else {}
    )
    for row in rows:
        compound_id = row["compound_id"]
        identity = by_compound.get(compound_id, {})
        row["dtxsid"] = identity.get("dtxsid")
        row["epa_identity_status"] = identity.get("status")
        row["epa_match_strength"] = identity.get("match_strength")
        toxcast_row = toxcast_by_compound.get(compound_id, {})
        row["toxcast_assays"] = toxcast_row.get("assays_with_result")
        row["toxcast_hits"] = toxcast_row.get("assays_with_hit")
        row["toxcast_inactive"] = toxcast_row.get("assays_inactive")
        row["toxcast_targets"] = toxcast_row.get("distinct_targets")
        with_result = toxcast_row.get("assays_with_result")
        inactive = toxcast_row.get("assays_inactive")
        row["toxcast_inactive_fraction"] = (
            round(inactive / with_result, 4)
            if with_result and inactive is not None else None
        )
        hazard_row = hazard_by_compound.get(compound_id, {})
        row["epa_hazard_records"] = hazard_row.get("records")
        row["epa_hazard_endpoints"] = hazard_row.get("distinct_endpoints")
        row["epa_hazard_species"] = hazard_row.get("distinct_species")
        row["epa_hazard_experimental_records"] = hazard_row.get("experimental_records")
        property_row = property_by_compound.get(compound_id, {})
        row["epa_comparison_records"] = (
            comparison_counts.get(compound_id, 0) if identity.get("status") == "approved" else None
        )
        row["epa_properties"] = property_row.get("properties")
        row["epa_measured_properties"] = property_row.get("measured_properties")
        row["epa_calculated_properties"] = property_row.get("calculated_properties")
    return rows


def main() -> None:
    classes = {
        row["query"]: row["compound_class"]
        for row in csv.DictReader(CLASSES.open(encoding = "utf-8"))
    }
    definitions, analysis, epa = build_sources(DATA_ROOT, DEFINITIONS)
    if epa is not None:
        export_epa(epa, DATA_ROOT, DEFINITIONS, output_data = COMPOUNDS.parent)
    compounds = analysis["compounds"]
    measurements = analysis["measurements"]
    annotations = analysis["annotations"]

    rows = []
    for compound in compounds.iter_rows(named = True):
        cid = compound["pubchem_cid"]
        properties = computed_properties(cid) if cid is not None else {}
        record = {
            "compound_id": compound["compound_id"],
            "pubchem_cid": cid,
            "query": compound["input_queries"][0],
            "chemical_group": compound["chemical_group"],
            "subgroup": compound["subgroup"],
            "hrac_group": compound["hrac_group"],
            "compound_class": classes.get(compound["input_queries"][0]),
            "resolution_status": compound["resolution_status"],
            "toxicity_status": compound["toxicity_status"],
        }
        for source, target in NUMERIC_COMPUTED.items():
            record[target] = as_number(properties.get(source))
        for source, target in TEXT_COMPUTED.items():
            value = properties.get(source)
            record[target] = value if isinstance(value, str) else None
        subset = measurements.filter(pl.col("compound_id") == compound["compound_id"])
        record["annotation_count"] = annotations.filter(
            pl.col("compound_id") == compound["compound_id"]
        ).height
        record["complete_count"] = subset.filter(pl.col("parse_status") == "complete").height
        record["partial_count"] = subset.filter(pl.col("parse_status") == "partial").height
        record["failed_count"] = subset.filter(pl.col("parse_status") == "failed").height
        record["distinct_endpoints"] = subset["endpoint"].drop_nulls().n_unique()
        record["distinct_species"] = subset["species"].drop_nulls().n_unique()
        record["distinct_routes"] = subset["exposure_route"].drop_nulls().n_unique()
        record["distinct_units"] = subset["unit_standardized"].drop_nulls().n_unique()
        rows.append(record)
    rows = add_epa_traits(rows, epa)
    rows = add_endpoint_traits(rows, definitions, analysis, epa)

    frame = pl.DataFrame(rows, schema_overrides = {
        f"{prefix}{name}": pl.Int64 for name in definitions
        for prefix in ("has_", "has_pubchem_", "has_epa_")
    })
    frame.write_parquet(TRAITS)
    frame.write_parquet(COMPOUNDS)
    frame.write_csv(COMPOUNDS_CSV)

    long_rows = []
    for record in rows:
        for trait, value in record.items():
            if trait in {"compound_id", "pubchem_cid", "query"}:
                continue
            if value is None:
                continue
            long_rows.append({
                "compound_id": record["compound_id"],
                "chemical_group": record["chemical_group"],
                "compound_class": record["compound_class"],
                "trait": trait,
                "value": value,
                "is_numeric": isinstance(value, (int, float)) and not isinstance(value, bool),
            })
    pl.DataFrame(long_rows).write_parquet(COMPOUNDS.parent / "traits_long.parquet")
    print(f"compounds with traits: {frame.height}")
    print(f"long-form trait rows: {len(long_rows)}")
    print("traits per compound:")
    print(frame.select(
        pl.col("annotation_count"), pl.col("complete_count"), pl.col("xlogp"),
    ).describe())


if __name__ == "__main__":
    main()
