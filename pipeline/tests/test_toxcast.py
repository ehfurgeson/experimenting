"""ToxCast assay evidence ingestion, kept apart from acute toxicity endpoints."""

import json

import polars as pl
import pytest

from agrotox.storage import epa_bioactivity_path
from agrotox.toxcast import (
    ASSAY_FIT,
    INACTIVE,
    SOURCE_RELEASE,
    fetch_toxcast,
    parse_bioactivity,
    toxcast_assays,
    toxcast_coverage,
)

ANNOTATION = {
    "aeid": 12345,
    "aid": 7,
    "assayComponentEndpointName": "ATG_NRF2_CIS_up",
    "assayFunctionType": "gene expression",
    "intendedTargetType": "cellular target",
    "intendedTargetFamily": "transcription factor",
    "biologicalProcessTarget": "oxidative stress response",
    "detectionTechnology": "luminescence",
    "assayFormatType": "cell-based",
    "organism": "Homo sapiens",
    "taxonName": "Homo sapiens",
    "tissue": "liver",
    "cellFormat": "2-D plate",
    "timepointHr": 24.0,
}


def record(aeid = 12345, hitc = 1, **overrides):
    row = {
        "dtxsid": "DTXSID7020182",
        "aeid": aeid,
        "aid": 7,
        "hitc": hitc,
        "actp": -4.5,
        "bmad": 0.3,
        "concMin": 1.0,
        "concMax": 92.0,
        "testedConcUnit": "uM",
        "respMin": -20.0,
        "respMax": 80.0,
        "modl": "logistic",
        "fitc": 1,
        "nconc": 12,
        "nrep": 2.0,
        "npts": 12,
    }
    row.update(overrides)
    return row


def crosswalk(*rows):
    return pl.DataFrame(list(rows), schema = {
        "compound_id": pl.String, "dtxsid": pl.String, "status": pl.String,
    })


class FakeClient:
    def __init__(self, records = None, annotation = None):
        self.records = records if records is not None else [record()]
        self.annotation = annotation if annotation is not None else ANNOTATION
        self.calls = []

    def bioactivity(self, dtxsid):
        self.calls.append(("bioactivity", dtxsid))
        return self.records

    def assay(self, aeid):
        self.calls.append(("assay", aeid))
        return self.annotation


def test_assay_evidence_keeps_the_source_fields():
    rows = parse_bioactivity([record()], "PUBCHEM:1", "DTXSID7020182",
                              {12345: ANNOTATION}, "2026-01-01T00:00:00Z")
    assert len(rows) == 1
    row = rows[0]
    assert row["assay_component_endpoint_name"] == "ATG_NRF2_CIS_up"
    assert row["intended_target_family"] == "transcription factor"
    assert row["organism"] == "Homo sapiens"
    assert row["hit_call"] == 1
    assert row["activity_value"] == -4.5
    assert row["concentration_unit"] == "uM"
    assert row["measurement_kind"] == ASSAY_FIT
    assert row["evidence_class"] == "experimental"
    assert row["source_release"] == SOURCE_RELEASE


def test_an_inactive_result_is_kept_and_marked():
    # The hit call is continuous: a negative call is an inactive curve.
    rows = parse_bioactivity([record(hitc = -0.87, actp = None)], "PUBCHEM:1",
                              "DTXSID7020182", {12345: ANNOTATION}, "2026-01-01T00:00:00Z")
    assert rows[0]["measurement_kind"] == INACTIVE
    assert rows[0]["activity_value"] is None
    assert rows[0]["hit_call"] == -0.87


def test_a_zero_hit_call_is_neither_active_nor_inactive():
    rows = parse_bioactivity([record(hitc = 0.0)], "PUBCHEM:1", "DTXSID7020182",
                              {12345: ANNOTATION}, "2026-01-01T00:00:00Z")
    assert rows[0]["measurement_kind"] != INACTIVE


def test_missing_and_nonfinite_metrics_become_null():
    rows = parse_bioactivity([record(concMin = None, concMax = float("nan"), respMax = None)],
                              "PUBCHEM:1", "DTXSID7020182", {12345: ANNOTATION},
                              "2026-01-01T00:00:00Z")
    assert rows[0]["concentration_min"] is None
    assert rows[0]["concentration_max"] is None
    assert rows[0]["response_max"] is None


def test_several_assays_for_one_chemical_are_kept():
    rows = parse_bioactivity([record(aeid = 1), record(aeid = 2)], "PUBCHEM:1",
                              "DTXSID7020182", {1: ANNOTATION, 2: ANNOTATION},
                              "2026-01-01T00:00:00Z")
    assert len(rows) == 2
    assays = toxcast_assays(rows)
    coverage = toxcast_coverage(assays)
    assert coverage["assays_with_result"].to_list() == [2]
    assert coverage["assays_with_hit"].to_list() == [2]
    assert coverage["assays_inactive"].to_list() == [0]


def test_the_coverage_separates_active_inactive_and_inconclusive():
    rows = parse_bioactivity([
        record(aeid = 1, hitc = 3.4),
        record(aeid = 2, hitc = -0.87),
        record(aeid = 3, hitc = 0.0),
    ], "PUBCHEM:1", "DTXSID7020182", {1: ANNOTATION, 2: ANNOTATION, 3: ANNOTATION},
        "2026-01-01T00:00:00Z")
    coverage = toxcast_coverage(toxcast_assays(rows))
    assert coverage["assays_with_result"].to_list() == [3]
    assert coverage["assays_with_hit"].to_list() == [1]
    assert coverage["assays_inactive"].to_list() == [1]
    assert coverage["assays_inconclusive"].to_list() == [1]


def test_an_untested_assay_is_absent_rather_than_inactive():
    rows = parse_bioactivity([record(hitc = 1)], "PUBCHEM:1", "DTXSID7020182",
                              {12345: ANNOTATION}, "2026-01-01T00:00:00Z")
    coverage = toxcast_coverage(toxcast_assays(rows))
    assert coverage["assays_inactive"].to_list() == [0]


def test_the_client_unwraps_the_assay_annotation_list():
    from agrotox.sources.comptox import ComptoxClient

    class Response:
        status_code = 200

        def __init__(self):
            self.headers = {}

        def raise_for_status(self):
            return None

        def json(self):
            return [ANNOTATION]

    class HTTP:
        def get(self, url, *, params, headers, timeout, allow_redirects):
            return Response()

    annotation = ComptoxClient(HTTP(), api_key = "secret-key").assay(12345)
    assert annotation["aeid"] == 12345


def test_the_evidence_table_has_no_acute_toxicity_endpoint():
    schema = toxcast_assays([]).schema
    for forbidden in ("ld50", "lc50", "ec50", "endpoint"):
        assert forbidden not in schema


def test_only_approved_compounds_are_requested(tmp_path):
    client = FakeClient()
    approved = crosswalk(
        {"compound_id": "PUBCHEM:1", "dtxsid": "DTXSID1", "status": "approved"},
        {"compound_id": "PUBCHEM:2", "dtxsid": "DTXSID2", "status": "needs_review"},
        {"compound_id": "PUBCHEM:3", "dtxsid": "DTXSID3", "status": "unresolved"},
    )
    assays, coverage = fetch_toxcast(tmp_path, approved, client)
    assert [call for call in client.calls if call[0] == "bioactivity"] == [
        ("bioactivity", "DTXSID1"),
    ]
    assert assays.height == 1
    assert coverage["compound_id"].to_list() == ["PUBCHEM:1"]


def test_cached_responses_are_reused_and_reparsed(tmp_path):
    client = FakeClient()
    approved = crosswalk({"compound_id": "PUBCHEM:1", "dtxsid": "DTXSID1",
                          "status": "approved"})
    first, _ = fetch_toxcast(tmp_path, approved, client)
    stored = json.loads(epa_bioactivity_path(tmp_path, "DTXSID1").read_text(encoding = "utf-8"))
    assert stored["dtxsid"] == "DTXSID1"
    assert "api_key" not in json.dumps(stored)
    calls = len(client.calls)
    second, _ = fetch_toxcast(tmp_path, approved, client)
    assert len(client.calls) == calls
    assert first.to_dicts() == second.to_dicts()


def test_an_empty_selection_gives_typed_empty_evidence(tmp_path):
    assays, coverage = fetch_toxcast(tmp_path, crosswalk(), FakeClient())
    assert assays.is_empty()
    assert coverage.is_empty()
    assert assays.schema["aeid"] == pl.Int64
    assert assays.schema["measurement_kind"] == pl.String
    assert coverage.schema["assays_with_result"] == pl.Int64


def test_malformed_records_are_rejected():
    with pytest.raises(TypeError):
        parse_bioactivity(["not a record"], "PUBCHEM:1", "DTXSID1", {}, "now")
