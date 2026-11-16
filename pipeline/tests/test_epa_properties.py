"""EPA chemical properties, with measured and calculated values kept apart."""

import json

import polars as pl
import pytest

from agrotox.epa_properties import (
    CALCULATED,
    MEASURED,
    fetch_properties,
    parse_properties,
    property_coverage,
    property_table,
)
from agrotox.storage import epa_property_path

MEASURED_RECORD = {
    "dtxsid": "DTXSID7020182",
    "propName": "Log Kow",
    "dataset": "DMS",
    "propValue": -0.31,
    "propUnit": "",
    "propValueOriginal": -0.31,
    "propValueText": "-0.31",
    "expDetailsSpeciesLatin": "Rattus norvegicus",
    "sourceName": "DMS",
    "sourceDescription": "DMS data",
    "publicSourceUrl": "https://example.org/dms",
}
PREDICTED_RECORD = {
    "dtxsid": "DTXSID7020182",
    "propName": "Log Kow",
    "propCategory": "Physicochemical",
    "propDescription": "Octanol water partition coefficient",
    "modelName": "TEST",
    "modelId": 100,
    "sourceName": "TEST",
    "sourceDescription": "TEST predictions",
    "propValue": -0.28,
    "propValueString": "-0.28",
    "propUnit": "",
    "adMethod": "Consensus",
    "adValue": 0.9,
    "adConclusion": "Inside",
    "adReasoning": "The compound is inside the domain",
    "hasQmrf": True,
    "qmrfUrl": "https://example.org/qmrf",
}
OTHER_MODEL_RECORD = {**PREDICTED_RECORD, "modelName": "OPERA", "modelId": 7}


def crosswalk(*rows):
    return pl.DataFrame(list(rows), schema = {
        "compound_id": pl.String, "dtxsid": pl.String, "status": pl.String,
    })


class FakeClient:
    def __init__(self, experimental = None, predicted = None):
        self.experimental = experimental if experimental is not None else [MEASURED_RECORD]
        self.predicted = predicted if predicted is not None else [PREDICTED_RECORD]
        self.calls = []

    def property_experimental(self, dtxsid):
        self.calls.append(("experimental", dtxsid))
        return self.experimental

    def property_predicted(self, dtxsid):
        self.calls.append(("predicted", dtxsid))
        return self.predicted


def test_a_measured_property_keeps_its_source():
    rows = parse_properties([MEASURED_RECORD], "PUBCHEM:1", MEASURED, "now")
    row = rows[0]
    assert row["property_name"] == "Log Kow"
    assert row["property_value"] == -0.31
    assert row["property_origin"] == MEASURED
    assert row["source_name"] == "DMS"
    assert row["public_source_url"] == "https://example.org/dms"


def test_a_calculated_property_keeps_its_model():
    rows = parse_properties([PREDICTED_RECORD], "PUBCHEM:1", CALCULATED, "now")
    row = rows[0]
    assert row["property_origin"] == CALCULATED
    assert row["model_name"] == "TEST"
    assert row["model_id"] == 100
    assert row["ad_conclusion"] == "Inside"


def test_a_missing_optional_trait_is_null():
    rows = parse_properties([{**MEASURED_RECORD, "propValue": None}], "PUBCHEM:1",
                            MEASURED, "now")
    assert rows[0]["property_value"] is None
    assert rows[0]["property_value_text"] == "-0.31"


def test_a_malformed_record_is_rejected():
    with pytest.raises(TypeError):
        parse_properties(["not a record"], "PUBCHEM:1", MEASURED, "now")


def test_two_sources_keep_both_values():
    properties = property_table([
        *parse_properties([MEASURED_RECORD], "PUBCHEM:1", MEASURED, "now"),
        *parse_properties([{**PREDICTED_RECORD, "propValue": -0.28}], "PUBCHEM:1",
                          CALCULATED, "now"),
    ])
    assert properties.height == 2
    assert set(properties["property_origin"].to_list()) == {MEASURED, CALCULATED}
    coverage = property_coverage(properties)
    assert coverage["properties"].to_list() == [2]
    assert coverage["measured_properties"].to_list() == [1]
    assert coverage["calculated_properties"].to_list() == [1]


def test_only_approved_compounds_are_requested(tmp_path):
    client = FakeClient()
    approved = crosswalk(
        {"compound_id": "PUBCHEM:1", "dtxsid": "DTXSID1", "status": "approved"},
        {"compound_id": "PUBCHEM:2", "dtxsid": "DTXSID2", "status": "unresolved"},
    )
    properties, coverage = fetch_properties(tmp_path, approved, client)
    assert [call[1] for call in client.calls] == ["DTXSID1", "DTXSID1"]
    assert properties.height == 2
    assert coverage["compound_id"].to_list() == ["PUBCHEM:1"]


def test_cached_property_responses_are_reused(tmp_path):
    client = FakeClient()
    approved = crosswalk({"compound_id": "PUBCHEM:1", "dtxsid": "DTXSID1",
                          "status": "approved"})
    fetch_properties(tmp_path, approved, client)
    stored = json.loads(
        epa_property_path(tmp_path, "experimental", "DTXSID1").read_text(encoding = "utf-8")
    )
    assert stored["dtxsid"] == "DTXSID1"
    assert "api_key" not in json.dumps(stored)
    calls = len(client.calls)
    fetch_properties(tmp_path, approved, client)
    assert len(client.calls) == calls


def test_a_compound_with_no_property_data_is_empty(tmp_path):
    client = FakeClient(experimental = [], predicted = [])
    approved = crosswalk({"compound_id": "PUBCHEM:1", "dtxsid": "DTXSID1",
                          "status": "approved"})
    properties, coverage = fetch_properties(tmp_path, approved, client)
    assert properties.is_empty()
    assert coverage.is_empty()
    assert properties.schema["property_value"] == pl.Float64


