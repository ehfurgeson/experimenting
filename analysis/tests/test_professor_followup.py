"""Halogen removal, matched folds, held-out attribution and export contracts."""
import copy
import json
import sys
from pathlib import Path

import numpy as np
import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_ablations import records

import professor_followup as followup
from formula import formula_features


def examples():
    rows = records()
    for i, row in enumerate(rows):
        row.update(formula_features('C2H5Cl' if i % 2 else 'C4H10O2'))
    return rows


def test_halogen_removal_recomputes_indirect_features():
    a, b = formula_features('C2H6Cl2'), formula_features('C2H6F')
    assert np.array_equal(followup.matrix([a], 'composition_without_halogens'),
                          followup.matrix([b], 'composition_without_halogens'))
    assert not np.array_equal(followup.matrix([a], 'formula_drop_halogen_columns'),
                              followup.matrix([b], 'formula_drop_halogen_columns'))


def test_shared_folds_order_independence_and_no_source_mutation():
    rows = examples()
    before = copy.deepcopy(rows)
    result = followup.diagnose(rows, permutation_repeats = 1)
    assert rows == before
    assert result == followup.diagnose(list(reversed(rows)), permutation_repeats = 1)
    assert len(result['reports']) == 8
    assert {r['status'] for r in result['reports']} == {'evaluated'}
    assignments, scaffolds = {}, {}
    for r in result['oof']:
        assert assignments.setdefault(r['compound_id'], r['fold']) == r['fold']
        assert scaffolds.setdefault(r['scaffold'], r['fold']) == r['fold']
    assert len(result['oof']) == 8 * 30
    assert len(result['permutations']) == 5 * 28
    assert len(result['coefficients']) == 5 * 27


def test_formula_preprocessing_and_permutation_use_disjoint_training_test_rows(monkeypatch):
    from sklearn.preprocessing import StandardScaler
    original_fit, original_transform = StandardScaler.fit, StandardScaler.transform
    training, transformed = [], []

    def fit(self, x, *args, **kwargs):
        training.append(len(x))
        return original_fit(self, x, *args, **kwargs)

    def transform(self, x, *args, **kwargs):
        transformed.append(len(x))
        return original_transform(self, x, *args, **kwargs)

    monkeypatch.setattr(StandardScaler, 'fit', fit)
    monkeypatch.setattr(StandardScaler, 'transform', transform)
    followup.diagnose(examples(), permutation_repeats = 1)
    assert set(training) == {24}
    assert 6 in transformed


def test_unknown_labels_and_support_failures_never_emit_partial_predictions():
    rows = examples()
    for r in rows:
        r['selection_target'] = None
    result = followup.diagnose(rows)
    assert {r['status'] for r in result['reports']} == {'insufficient_class_support'}
    assert not result['oof'] and not result['coefficients'] and not result['permutations']
    rows = examples()
    for r in rows:
        r['scaffold'] = 'single'
    assert {r['status'] for r in followup.diagnose(rows)['reports']} == {
        'insufficient_scaffold_support'}


def test_exports_and_input_failures(tmp_path):
    source = tmp_path / 'features.parquet'
    pl.DataFrame(examples()).write_parquet(source)
    output = tmp_path / 'result'
    manifest = followup.run(source, output, permutation_repeats = 0)
    assert json.loads((output / 'manifest.json').read_text()) == manifest
    assert pl.read_csv(output / 'permutations.csv').height == 0
    with pytest.raises(ValueError, match = 'empty output'):
        followup.run(source, output)
    with pytest.raises(ValueError, match = 'outside'):
        followup.run(source, tmp_path)
    rows = examples()
    rows[0]['formula_C_count'] = np.nan
    with pytest.raises(ValueError, match = 'finite'):
        followup.diagnose(rows)
    with pytest.raises(ValueError, match = 'integer'):
        followup.diagnose(examples(), permutation_repeats = True)


def test_f1_is_from_scaffold_held_out_predictions():
    from sklearn.metrics import f1_score
    result = followup.diagnose(examples(), permutation_repeats = 0)
    for report in result['reports']:
        predictions = [r for r in result['oof'] if r['profile'] == report['profile']]
        assert report['f1'] == f1_score([r['label'] for r in predictions],
                                      [r['probability'] >= .5 for r in predictions])


def test_reviewed_cohort_target_is_explicit_and_does_not_use_other_labels():
    rows = examples()
    for r in rows:
        r['provenance_comparator_target'] = r['selection_target']
        r['contrast_group'] = ('documented_commercial_herbicide_comparator'
                               if r['selection_target'] else 'reviewed_natural_occurrence')
        r['selection_target'] = None
        r['activity_target'] = None
        r['origin_target'] = None
    result = followup.diagnose(rows, target = 'provenance_comparator_target', permutation_repeats = 0)
    assert {r['status'] for r in result['reports']} == {'evaluated'}
    assert {r['target'] for r in result['reports']} == {'provenance_comparator_target'}
    rows[0]['contrast_group'] = 'unreviewed_natural_product_selection'
    with pytest.raises(ValueError, match = 'target/group disagreement'):
        followup.diagnose(rows, target = 'provenance_comparator_target')
