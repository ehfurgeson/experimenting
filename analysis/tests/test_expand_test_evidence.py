"""Expansion retains ambiguous identities and failures without exposing secrets."""
import json
import sys
from pathlib import Path

import polars as pl
import pytest
from agrotox.sources.comptox import SearchResult

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence_release import structure
from expand_test_evidence import expand


class Client:
    def __init__(self, fail = False, ambiguous = False):
        self.fail, self.ambiguous = fail, ambiguous
        self.calls = []

    def search_equal(self, term):
        return SearchResult([{'dtxsid': 'DTXSID1', 'rank': 1}], [])

    def details(self, sid):
        return {'inchikey': structure('CC' if self.ambiguous else 'CCO')['full_key']}

    def property_predicted(self, sid):
        self.calls.append(sid)
        if self.fail:
            raise RuntimeError('credential-like-content-must-not-appear')
        return []


def inputs(tmp_path):
    path = tmp_path / 'features.parquet'
    pl.DataFrame([{'compound_id': 'pubchem:1', 'query': 'ethanol',
                   'canonical_structure': 'CCO',
                   'structure_inchikey': structure('CCO')['full_key']}]).write_parquet(path)
    return path


def test_empty_prediction_is_logged_as_absence_not_zero(tmp_path):
    output = tmp_path / 'release'
    result = expand(inputs(tmp_path), output, Client())
    assert result['states'] == {'no_stored_output': 1}
    assert pl.read_parquet(output / 'B_TEST_predictions.parquet').is_empty()
    assert (output / 'reproduction' / 'pipeline__src__agrotox__epa_identity.py').is_file()
    assert json.loads((output / 'manifest.json').read_text())['prediction_rows'] == 0
    with pytest.raises(FileExistsError):
        expand(tmp_path / 'features.parquet', output, Client())


def test_failure_log_omits_exception_text_and_preserves_identity(tmp_path):
    output = tmp_path / 'release'
    result = expand(inputs(tmp_path), output, Client(fail = True))
    assert result['states'] == {'failed': 1}
    assert 'RuntimeError' in (output / 'collection_log.csv').read_text()
    assert 'credential-like-content' not in (output / 'collection_log.csv').read_text()
    assert (output / 'identity_crosswalk.csv').is_file()


def test_identity_mismatch_never_fetches_predictions(tmp_path):
    client = Client(ambiguous = True)
    result = expand(inputs(tmp_path), tmp_path / 'release', client)
    assert client.calls == []
    assert result['states'] == {'identity_unresolved': 1}
