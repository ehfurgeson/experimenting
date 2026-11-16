"""EPA TEST predictions, read from the stored provider predictions."""

import json

import polars as pl
import pytest

from agrotox.epa_test import (
    fetch_test_predictions,
    is_test_model,
    parse_test_predictions,
    prediction_coverage,
    prediction_table,
)
from agrotox.storage import epa_property_path

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
    def __init__(self, predicted = None):
        self.predicted = predicted if predicted is not None else [PREDICTED_RECORD]
        self.calls = []

    def property_predicted(self, dtxsid):
        self.calls.append(dtxsid)
        return self.predicted


def test_only_test_models_become_predictions():
    rows = parse_test_predictions([PREDICTED_RECORD, OTHER_MODEL_RECORD], "PUBCHEM:1", "now")
    assert len(rows) == 1
    assert rows[0]["model_name"] == "TEST"
    assert rows[0]["evidence_class"] == "predicted"
    assert rows[0]["ad_value"] == 0.9
    assert rows[0]["has_qmrf"] is True


def test_a_non_test_model_is_not_a_test_prediction():
    assert is_test_model("TEST") is True
    assert is_test_model("OPERA") is False
    assert is_test_model(None) is False


def test_an_unavailable_prediction_is_absent_not_zero(tmp_path):
    client = FakeClient(predicted = [])
    approved = crosswalk({"compound_id": "PUBCHEM:1", "dtxsid": "DTXSID1",
                          "status": "approved"})
    predictions, coverage = fetch_test_predictions(tmp_path, approved, client)
    assert predictions.is_empty()
    assert coverage.is_empty()
    assert predictions.schema["predicted_value"] == pl.Float64


def test_predictions_stay_out_of_the_measured_tables():
    predictions = prediction_table(parse_test_predictions([PREDICTED_RECORD],
                                                           "PUBCHEM:1", "now"))
    assert "property_origin" not in predictions.columns
    assert set(predictions["evidence_class"].to_list()) == {"predicted"}


def test_the_prediction_coverage_counts_models():
    predictions = prediction_table(parse_test_predictions(
        [PREDICTED_RECORD, {**PREDICTED_RECORD, "adConclusion": "Outside"}],
        "PUBCHEM:1", "now",
    ))
    coverage = prediction_coverage(predictions)
    assert coverage["predictions"].to_list() == [2]
    assert coverage["models"].to_list() == [1]
    assert coverage["outside_applicability_domain"].to_list() == [1]


def test_only_approved_compounds_are_requested(tmp_path):
    client = FakeClient()
    approved = crosswalk(
        {"compound_id": "PUBCHEM:1", "dtxsid": "DTXSID1", "status": "approved"},
        {"compound_id": "PUBCHEM:2", "dtxsid": "DTXSID2", "status": "needs_review"},
    )
    _predictions, coverage = fetch_test_predictions(tmp_path, approved, client)
    assert client.calls == ["DTXSID1"]
    assert coverage["compound_id"].to_list() == ["PUBCHEM:1"]


def test_the_cached_predicted_response_is_reused(tmp_path):
    client = FakeClient()
    approved = crosswalk({"compound_id": "PUBCHEM:1", "dtxsid": "DTXSID1",
                          "status": "approved"})
    fetch_test_predictions(tmp_path, approved, client)
    stored = json.loads(
        epa_property_path(tmp_path, "predicted", "DTXSID1").read_text(encoding = "utf-8")
    )
    assert "api_key" not in json.dumps(stored)
    calls = len(client.calls)
    fetch_test_predictions(tmp_path, approved, client)
    assert len(client.calls) == calls


def test_a_malformed_record_is_rejected():
    with pytest.raises(TypeError):
        parse_test_predictions(["not a record"], "PUBCHEM:1", "now")


def test_raw_lineage_and_embedded_comparator_are_preserved_without_admission():
    record = {**PREDICTED_RECORD, 'id': 123, 'sourceName': 'TEST5.1.3',
              'smiles': 'CCO', 'canonQsarSmiles': 'CCO',
              'propValueExperimental': 42, 'propValueExperimentalString': '>42',
              'propValueError': 'not calculable', 'newProviderField': {'unknown': True}}
    table = prediction_table(parse_test_predictions([record], 'PUBCHEM:1', 'now'))
    row = table.to_dicts()[0]
    assert row['source_name'] == 'TEST5.1.3'
    assert row['provider_record_id'] == '123'
    assert row['provider_experimental_value'] == 42
    assert row['provider_experimental_text'] == '>42'
    assert row['provider_error'] == 'not calculable'
    assert json.loads(row['source_record_json']) == record
    assert row['evidence_class'] == 'predicted'
    assert row['predicted_value'] == PREDICTED_RECORD['propValue']


def test_older_records_leave_new_provenance_nullable():
    row = prediction_table(parse_test_predictions(
        [PREDICTED_RECORD], 'PUBCHEM:1', 'now')).to_dicts()[0]
    assert row['provider_record_id'] is None
    assert row['provider_experimental_value'] is None
    assert row['smiles'] is None
