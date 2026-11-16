"""Repeated retrievals, model versions and disagreements are not extra votes."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence_comparison import reconcile_test_rows, verify


def row(**changes):
    return {'compound_id': 'a', 'full_key': 'EXACT-KEY', 'source_name': 'TEST5.1.3',
            'model_name': 'TEST_Rat', 'endpoint': 'Oral Rat LD50', 'predicted_unit': 'mol/kg',
            'predicted_value': '.01', 'ad_conclusion': 'Inside', **changes}


def test_aliases_and_repeated_queries_are_one_output_not_votes():
    merged, audit = reconcile_test_rows([row(), row(compound_id = 'alias')])
    assert len(merged) == 1
    assert audit[0]['status'] == 'same_output_collapsed'


def test_conflicts_cannot_supply_a_primary_value_and_versions_stay_separate():
    merged, audit = reconcile_test_rows([row(), row(predicted_value = '.02')])
    assert merged == []
    assert audit[0]['status'] == 'conflict_no_primary_value'
    merged, _ = reconcile_test_rows([row(), row(source_name = 'TEST4.2')])
    assert len(merged) == 2


def test_source_manifest_tamper_rejection(tmp_path):
    (tmp_path / 'manifest.json').write_text('{"outputs":{"data.csv":"wrong"}}')
    (tmp_path / 'data.csv').write_text('bad')
    with pytest.raises(ValueError, match = 'Frozen hash mismatch'):
        verify(tmp_path)
