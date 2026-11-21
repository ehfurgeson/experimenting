"""Cached EPA hazard analysis across selected compounds and all seven endpoints."""

import json
import runpy
from pathlib import Path

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from agrotox.epa_workflow import build_epa_hazard_offline
from agrotox.storage import epa_hazard_path, write_json
from agrotox.tables import EPA_IDENTITY_CROSSWALK_SCHEMA, frame_from_rows
from agrotox.workflow import TABLE_NAMES

RULES = {
    **{name: {"endpoint": name, "standard_unit": "mg/kg-day"}
       for name in ["NOAEL", "LOAEL", "BMD", "BMDL"]},
    "LD50": {"endpoint": "LD50"},
    "LC50": {"endpoint": "LC50"},
    "EC50": {"endpoint": "EC50"},
}


@pytest.fixture
def hazard_cache(snapshot_cache):
    crosswalk = frame_from_rows([
        {"compound_id": "PUBCHEM:101", "dtxsid": "DTXSID1", "status": "approved"},
        {"compound_id": "PUBCHEM:102", "dtxsid": "DTXSID2", "status": "approved"},
        {"compound_id": "PUBCHEM:103", "dtxsid": "DTXSID3", "status": "needs_review"},
        {"compound_id": "UNSELECTED", "dtxsid": "DTXSID4", "status": "approved"},
    ], EPA_IDENTITY_CROSSWALK_SCHEMA)
    crosswalk.write_parquet(snapshot_cache / "epa_identity_crosswalk.parquet")
    records = [{
        "dtxsid": "DTXSID1", "toxvalType": label, "toxvalNumeric": 100.0,
        "toxvalUnits": "mg/L" if label in {"LC50", "EC50"} else
        "mg/kg" if label == "LD50" else "mg/kg-day",
        "qualifier": "=", "experimentalRecord": "experimental",
        "source": "Synthetic", "longRef": "Synthetic study", "speciesCommon": "Rat",
        "speciesSupercategory": "Mammals", "exposureRoute": "oral",
        "studyType": "chronic", "studyDurationClass": "chronic",
        "studyDurationValue": 90.0, "studyDurationUnits": "day",
        "toxicologicalEffect": "body weight",
    } for label in ["LD50", "NOAEL", "LOAEL", "BMD", "BMDL (10)", "LC50", "EC50"]]
    records.append({**records[1], "toxvalUnits": "ppm"})
    for dtxsid, response in [("DTXSID1", records), ("DTXSID2", [])]:
        write_json(epa_hazard_path(snapshot_cache, dtxsid), {
            "dtxsid": dtxsid, "retrieved_at": "2026-01-01T00:00:00Z",
            "status": 200, "response": response,
        })
    return snapshot_cache


def test_offline_hazard_tables_preserve_context_and_selected_denominators(hazard_cache, curated_queries):
    analysis = build_epa_hazard_offline(hazard_cache, curated_queries, RULES)
    assert set(analysis.tables) == {*TABLE_NAMES, "hazards"}
    assert analysis["compounds"].height == 4
    assert analysis["measurements"].height == 8
    assert analysis["comparison_records"].height == 7
    assert analysis["review_queue"].height == 1
    assert analysis["coverage"].select(*RULES).sum().row(0) == (1, 1, 1, 1, 1, 1, 1)
    groups = analysis["group_summary"]
    assert groups.filter(pl.col("chemical_group") == "herbicide")["total_compounds"].to_list() == [1] * 7
    assert groups.filter(pl.col("chemical_group") == "natural_product")["total_compounds"].to_list() == [3] * 7
    chronic = analysis["compound_summary"].filter(pl.col("comparison").is_in(["NOAEL", "LOAEL", "BMD", "BMDL"]))
    assert chronic["exact_median"].null_count() == 4
    acute = analysis["compound_summary"].filter(pl.col("comparison") == "LD50")
    assert acute["exact_median"].to_list() == [100.0]
    assert analysis["audit"]["availability_reason"].to_list() == [
        "comparison_data_available", "no_hazard_records_in_saved_response",
        "identity_not_approved", "identity_not_in_crosswalk",
    ]
    paths = analysis["measurements"]["raw_file"].unique().to_list()
    assert paths == [str(epa_hazard_path(hazard_cache, "DTXSID1"))]
    assert len([p for p in analysis.dependencies if "hazard" in Path(p).parts]) == 2
    assert str(hazard_cache / "epa_identity_crosswalk.parquet") in analysis.dependencies


def test_selected_caches_are_read_only_and_reruns_identical(hazard_cache, curated_queries):
    before = {p: p.read_bytes() for p in hazard_cache.rglob("*") if p.is_file()}
    first = build_epa_hazard_offline(hazard_cache, curated_queries, RULES)
    second = build_epa_hazard_offline(hazard_cache, curated_queries, RULES)
    for name in first.tables:
        assert_frame_equal(first[name], second[name])
    assert first.dependencies == second.dependencies
    assert {p: p.read_bytes() for p in before} == before


def test_missing_approved_cache_is_an_error(hazard_cache, curated_queries):
    epa_hazard_path(hazard_cache, "DTXSID2").unlink()
    with pytest.raises(FileNotFoundError):
        build_epa_hazard_offline(hazard_cache, curated_queries, RULES)


@pytest.mark.parametrize("mutation", ["envelope_identity", "record_identity", "response_shape"])
def test_invalid_selected_cache_is_rejected(hazard_cache, curated_queries, mutation):
    path = epa_hazard_path(hazard_cache, "DTXSID1")
    payload = json.loads(path.read_text())
    if mutation == "envelope_identity":
        payload["dtxsid"] = "DTXSID99"
    elif mutation == "record_identity":
        payload["response"][0]["dtxsid"] = "DTXSID99"
    else:
        payload["response"] = None
    write_json(path, payload)
    with pytest.raises(ValueError, match = "hazard cache"):
        build_epa_hazard_offline(hazard_cache, curated_queries, RULES)


def test_unapproved_and_unselected_cache_is_not_read(hazard_cache, curated_queries):
    for dtxsid in ["DTXSID3", "DTXSID4"]:
        path = epa_hazard_path(hazard_cache, dtxsid)
        path.parent.mkdir(parents = True, exist_ok = True)
        path.write_text("corrupt and unselected")
    analysis = build_epa_hazard_offline(hazard_cache, curated_queries, RULES)
    assert analysis["hazards"].height == 8


def test_empty_selection_keeps_typed_tables(hazard_cache):
    analysis = build_epa_hazard_offline(hazard_cache, [], RULES)
    assert set(analysis.tables) == {*TABLE_NAMES, "hazards"}
    assert all(table.is_empty() for table in analysis.tables.values())
    assert analysis["audit"].schema["records"] == pl.Int64


def test_example_writes_offline_products_and_dependency_sidecars(hazard_cache, tmp_path, monkeypatch):
    selection = tmp_path / "selected.txt"
    selection.write_text("alpha\nbeta\ngamma\nunknown\n")
    output = tmp_path / "output"
    example = Path(__file__).parents[1] / "examples" / "analyze_epa_hazards.py"
    monkeypatch.setattr("sys.argv", [str(example), "--data", str(hazard_cache),
                                   "--input", str(selection), "--output", str(output)])
    runpy.run_path(str(example), run_name = "__main__")
    assert pl.read_parquet(output / "measurements.parquet").height == 8
    metadata = json.loads((output / "measurements.metadata.json").read_text())
    assert metadata["row_count"] == 8
    assert str(selection) in metadata["input_hashes"]
    assert str(epa_hazard_path(hazard_cache, "DTXSID1")) in metadata["input_hashes"]


def test_stale_processed_hazard_products_are_not_consumed(hazard_cache, curated_queries):
    for name in ["epa_hazard.parquet", "epa_hazard_comparison.parquet"]:
        (hazard_cache / name).write_text("stale processed output")
    analysis = build_epa_hazard_offline(hazard_cache, curated_queries, RULES)
    assert analysis["comparison_records"].height == 7
    assert not any(Path(path).name == "epa_hazard_comparison.parquet" for path in analysis.dependencies)
