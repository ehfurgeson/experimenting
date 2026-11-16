"""Analysis consumers of the current seven-endpoint cached workflow."""

import runpy
from pathlib import Path

import polars as pl
import pytest
import yaml

from agrotox.storage import epa_hazard_path, write_json
from agrotox.tables import EPA_IDENTITY_CROSSWALK_SCHEMA, frame_from_rows

ANALYSIS = Path(__file__).resolve().parents[2] / "analysis"


@pytest.fixture
def experiment_cache(snapshot_cache):
    crosswalk = frame_from_rows([
        {"compound_id": "PUBCHEM:101", "dtxsid": "DTXSID1", "status": "approved"},
        {"compound_id": "PUBCHEM:102", "dtxsid": "DTXSID2", "status": "approved"},
        {"compound_id": "PUBCHEM:103", "dtxsid": None, "status": "needs_review"},
    ], EPA_IDENTITY_CROSSWALK_SCHEMA)
    crosswalk.write_parquet(snapshot_cache / "epa_identity_crosswalk.parquet")
    records = [{
        "dtxsid": "DTXSID1", "toxvalType": endpoint, "toxvalNumeric": 10.0,
        "toxvalUnits": "mg/L" if endpoint in {"LC50", "EC50"} else
        "mg/kg" if endpoint == "LD50" else "mg/kg-day",
        "experimentalRecord": "experimental", "speciesSupercategory": "Mammals",
        "speciesCommon": "Rat", "exposureRoute": "oral",
    } for endpoint in ["LD50", "LC50", "EC50", "NOAEL", "LOAEL", "BMD", "BMDL (10)"]]
    records.append({**records[3], "experimentalRecord": "not experimental"})
    for dtxsid, response in [("DTXSID1", records), ("DTXSID2", [])]:
        write_json(epa_hazard_path(snapshot_cache, dtxsid), {
            "dtxsid": dtxsid, "retrieved_at": "2026-01-01T00:00:00Z",
            "status": 200, "response": response,
        })
    rules = {endpoint: {"endpoint": endpoint,
                       **({"standard_unit": "mg/kg-day"} if endpoint in
                          {"NOAEL", "LOAEL", "BMD", "BMDL"} else {})}
             for endpoint in ["LD50", "LC50", "EC50", "NOAEL", "LOAEL", "BMD", "BMDL"]}
    definitions = snapshot_cache / "endpoints.yaml"
    definitions.write_text(yaml.safe_dump(rules))
    (snapshot_cache / "compounds.csv").write_text(
        "query,chemical_group\nalpha,herbicide\nbeta,natural_product\n"
        "gamma,natural_product\nunknown,natural_product\n"
    )
    return snapshot_cache, definitions


def script(name, monkeypatch, **settings):
    monkeypatch.syspath_prepend(str(ANALYSIS))
    namespace = runpy.run_path(str(ANALYSIS / name))
    namespace["main"].__globals__.update(settings)
    return namespace


def test_coverage_rebuilds_raw_evidence_with_equal_denominators(experiment_cache, monkeypatch):
    root, definitions = experiment_cache
    output = root / "coverage.csv"
    module = script("endpoint_coverage.py", monkeypatch, DATA = root,
                    DEFINITIONS = definitions, OUTPUT = output)
    module["main"]()
    coverage = pl.read_csv(output)
    assert coverage.height == 28
    assert set(coverage["source"]) == {"pubchem", "epa_hazard"}
    for row in coverage.to_dicts():
        assert row["total_compounds"] == (1 if row["chemical_group"] == "herbicide" else 3)
    epa = coverage.filter(pl.col("source") == "epa_hazard")
    assert epa.filter(pl.col("chemical_group") == "herbicide")["compounds_with_data"].to_list() == [1] * 7
    summaries = pl.read_parquet(root / "epa_analysis" / "compound_summary.parquet")
    chronic = summaries.filter(pl.col("comparison").is_in(["NOAEL", "LOAEL", "BMD", "BMDL"]))
    assert chronic["exact_median"].null_count() == 4
    measurements = pl.read_parquet(root / "epa_analysis" / "measurements.parquet")
    assert measurements.height == 8
    assert (root / "epa_analysis" / "coverage.metadata.json").exists()


def test_traits_include_source_specific_chronic_availability(experiment_cache, monkeypatch):
    root, definitions = experiment_cache
    (root / "compound_classes.csv").write_text("query,compound_class\nalpha,synthetic\n")
    module = script("build_traits.py", monkeypatch, DATA_ROOT = root,
                    SELECTION = root / "compounds.csv", CLASSES = root / "compound_classes.csv",
                    DEFINITIONS = definitions, TRAITS = root / "traits.parquet",
                    COMPOUNDS = root / "compound_traits.parquet",
                    COMPOUNDS_CSV = root / "compound_traits.csv",
                    computed_properties = lambda cid: {"MolecularWeight": 100.0, "XLogP": 1.0})
    module["main"]()
    traits = pl.read_parquet(root / "compound_traits.parquet")
    assert traits.height == 4  # unresolved selections retain their denominator
    alpha = traits.filter(pl.col("compound_id") == "PUBCHEM:101").row(0, named = True)
    beta = traits.filter(pl.col("compound_id") == "PUBCHEM:102").row(0, named = True)
    gamma = traits.filter(pl.col("compound_id") == "PUBCHEM:103").row(0, named = True)
    for endpoint in ["NOAEL", "LOAEL", "BMD", "BMDL"]:
        assert alpha[f"has_epa_{endpoint}"] == 1
        assert alpha[f"has_pubchem_{endpoint}"] == 0
        assert alpha[f"has_{endpoint}"] == 1
        assert beta[f"has_epa_{endpoint}"] == 0  # retrieved empty response
        assert gamma[f"has_epa_{endpoint}"] is None  # identity not approved
        assert gamma[f"has_{endpoint}"] is None  # neither positive nor fully assessed
    assert alpha["epa_comparison_records"] == 7
    assert beta["epa_comparison_records"] == 0
    assert gamma["epa_comparison_records"] is None
    assert "NOAEL_median" not in traits.columns


def test_source_flags_preserve_missing_epa_and_positive_pubchem(experiment_cache, monkeypatch):
    root, definitions = experiment_cache
    (root / "epa_identity_crosswalk.parquet").unlink()
    monkeypatch.syspath_prepend(str(ANALYSIS))
    from endpoint_analysis import add_endpoint_traits, build_sources

    rules, pubchem, epa = build_sources(root, definitions)
    assert epa is None
    rows = pubchem["compounds"].to_dicts()
    augmented = add_endpoint_traits(rows, rules, pubchem, epa)
    for row in augmented:
        assert row["has_epa_NOAEL"] is None
        assert row["has_NOAEL"] is None
        assert row["has_LD50"] == (1 if row["has_pubchem_LD50"] == 1 else None)


def test_missing_approved_hazard_cache_is_not_zero_coverage(experiment_cache, monkeypatch):
    root, definitions = experiment_cache
    epa_hazard_path(root, "DTXSID1").unlink()
    monkeypatch.syspath_prepend(str(ANALYSIS))
    from endpoint_analysis import build_sources

    with pytest.raises(FileNotFoundError):
        build_sources(root, definitions)
