"""Actual compound/scaffold boundaries and teacher-agreement interpretation."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence_models import (
    classification_metrics,
    merged_groups,
    paired_agreement,
    regression_metrics,
    run,
)


def test_connectivity_bridges_merge_scaffolds_transitively():
    rows = [{'connectivity': 'a', 'scaffold': 'x'},
            {'connectivity': 'a', 'scaffold': 'y'},
            {'connectivity': 'b', 'scaffold': 'y'},
            {'connectivity': 'c', 'scaffold': 'z'}]
    groups = merged_groups(rows)
    assert groups[0] == groups[1] == groups[2]
    assert groups[3] != groups[0]


def test_agreement_joins_exact_full_keys_only_and_does_not_validate():
    a = [{'full_key': 'KEY-A', 'target_log10_mg_kg': '2', 'ld50_bin': '0',
          'source_record_ids': '["a"]'}]
    b = [{'full_key': 'KEY-B', 'target_log10_mg_kg': '4', 'ld50_bin': '2',
          'training_membership': 'Tr', 'ad_conclusion': 'Inside', 'source_record_ids': '["b"]'}]
    assert paired_agreement(a, b) == ([], [])
    b[0]['full_key'] = 'KEY-A'
    pairs, summaries = paired_agreement(a, b)
    assert pairs[0]['difference_B_minus_A'] == 2
    assert summaries[0]['mae_log10'] == 2
    assert summaries[0]['same_bin_fraction'] == 0
    assert summaries[0]['interpretation'] == 'agreement_only_not_independent_validation'


def test_metrics_expose_majority_failure_and_constant_rank():
    y = np.array([0, 0, 0, 1, 2])
    pred = np.zeros(5, dtype = int)
    metrics = classification_metrics(y, pred, np.tile([1., 0., 0.], (5, 1)))
    assert metrics['class_1_recall'] == 0
    assert metrics['balanced_accuracy'] == pytest.approx(1 / 3)
    assert metrics['confusion'][2] == [1, 0, 0]
    assert regression_metrics(np.array([1., 2.]), np.array([1., 1.]))['spearman'] is None


def test_model_run_refuses_mutated_frozen_input(tmp_path):
    import json
    release = tmp_path / 'release'
    release.mkdir()
    (release / 'A_compounds.csv').write_text('mutated')
    (release / 'manifest.json').write_text(json.dumps({'outputs': {'A_compounds.csv': 'wrong'}}))
    with pytest.raises(ValueError, match = 'hash mismatch'):
        run(release, tmp_path / 'evaluation')
    assert not (tmp_path / 'evaluation').exists()


def test_sparse_class_support_retains_regression_and_explicit_OOB_status():
    from evidence_models import evaluate
    from evidence_release import FEATURES
    rows = [{'full_key': f'key{i}', 'connectivity': f'c{i}', 'scaffold': f's{i}',
             'target_log10_mg_kg': '4', 'ld50_bin': '2',
             **{f: i + 1 for f in FEATURES}} for i in range(10)]
    result = evaluate(rows, 'A')
    assert result['oob'] == []
    assert result['predictions']
    assert all(r['task'] == 'regression' for r in result['predictions'])
    assert any(r['status'] == 'OOB_unsupported_binary_class_support' for r in result['status'])
