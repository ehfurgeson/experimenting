"""Multiclass tree-specific OOB diagnostics against independent reference votes."""
import sys
from pathlib import Path

import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence_oob import macro_oob


def test_macro_OOB_matches_sklearn_and_constant_feature_has_zero_importance():
    rng = np.random.default_rng(22)
    x = np.column_stack([np.linspace(-2, 2, 90), np.zeros(90), rng.normal(size = 90)])
    y = np.repeat([0, 1, 2], 30)
    forest = RandomForestClassifier(n_estimators = 70, random_state = 4,
                                    oob_score = True).fit(x, y)
    result = macro_oob(forest, x, y, ['signal', 'constant', 'noise'], repeats = 3)
    assert np.allclose(result['probabilities'], forest.oob_decision_function_)
    assert result['baseline_oob_macro_f1'] == pytest.approx(f1_score(
        y, forest.oob_decision_function_.argmax(axis = 1), average = 'macro'))
    assert result['importance'][0]['mean_macro_f1_drop'] > .2
    assert result['importance'][1]['mean_macro_f1_drop'] == 0
    assert result['importance'][1]['sd_macro_f1_drop'] == 0
    again = macro_oob(forest, x, y, ['signal', 'constant', 'noise'], repeats = 3)
    assert result['repeats'] == again['repeats']


def test_permuted_votes_match_independent_per_tree_reference_and_do_not_mutate_X():
    rng = np.random.default_rng(5)
    x = rng.normal(size = (36, 2)).astype(np.float32)
    y = np.arange(36) % 3
    original = x.copy()
    forest = RandomForestClassifier(n_estimators = 40, random_state = 7).fit(x, y)
    result = macro_oob(forest, x, y, ['a', 'b'], repeats = 2, seed = 12)
    totals, counts = np.zeros((len(y), 3)), np.zeros(len(y))
    changed = np.zeros((2, 2, len(y), 3))
    random = np.random.default_rng(12)
    for tree, sampled in zip(forest.estimators_, forest.estimators_samples_, strict = True):
        indices = np.setdiff1d(np.arange(len(y)), sampled)
        totals[indices] += tree.predict_proba(x[indices])
        counts[indices] += 1
        used = set(tree.tree_.feature[tree.tree_.feature >= 0])
        for repeat in range(2):
            order = random.permutation(len(indices)) if len(used) and len(indices) else None
            for feature in range(2):
                altered = x[indices].copy()
                if feature in used:
                    altered[:, feature] = x[indices][order, feature]
                changed[feature, repeat, indices] += tree.predict_proba(altered)
    baseline = f1_score(y, totals.argmax(axis = 1), average = 'macro')
    for r in result['repeats']:
        feature = ['a', 'b'].index(r['feature'])
        expected = baseline - f1_score(y, changed[feature, r['repeat']].argmax(axis = 1),
                                       average = 'macro')
        assert r['macro_f1_drop'] == pytest.approx(expected)
    assert np.array_equal(x, original)
    assert np.array_equal(result['votes'], counts)


def test_missing_votes_and_invalid_class_semantics_are_explicit():
    x, y = np.arange(24).reshape(-1, 1), np.arange(24) % 3
    forest = RandomForestClassifier(n_estimators = 1, random_state = 0).fit(x, y)
    with pytest.raises(ValueError, match = 'Every row'):
        macro_oob(forest, x, y, ['x'])
    with pytest.raises(ValueError, match = 'positive integer'):
        macro_oob(forest, x, y, ['x'], repeats = True)
    with pytest.raises(ValueError, match = 'contiguous'):
        macro_oob(forest, x, y + 1, ['x'])
