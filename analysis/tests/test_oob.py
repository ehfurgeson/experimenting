"""OOB scores agree with independent unsampled-tree predictions."""
import sys
from pathlib import Path

import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from oob import oob_permutation


def test_oob_votes_and_unused_features_are_exact_and_reproducible():
    rng = np.random.default_rng(8)
    x = np.column_stack([rng.normal(size = 80), np.zeros(80)])
    y = (x[:, 0] > 0).astype(int)
    forest = RandomForestClassifier(n_estimators = 50, random_state = 4,
                                    oob_score = True).fit(x, y)
    result = oob_permutation(forest, x, y, ['signal', 'constant'], repeats = 3)
    assert result == oob_permutation(forest, x, y, ['signal', 'constant'], repeats = 3)
    assert result[0]['baseline_oob_f1'] == f1_score(
        y, forest.oob_decision_function_[:, 1] >= .5)
    assert result[0]['mean_f1_drop'] > .2
    assert result[1]['mean_f1_drop'] == result[1]['std_f1_drop'] == 0
    for tree, sampled in zip(forest.estimators_, forest.estimators_samples_, strict = True):
        oob = np.setdiff1d(np.arange(len(y)), sampled)
        assert not np.intersect1d(sampled, oob).size
        assert len(tree.predict_proba(x[oob])) == len(oob)
    with pytest.raises(ValueError, match = 'positive integer'):
        oob_permutation(forest, x, y, ['signal', 'constant'], repeats = True)


def test_missing_oob_votes_are_unsupported():
    x = np.arange(20).reshape(-1, 1)
    y = np.arange(20) % 2
    forest = RandomForestClassifier(n_estimators = 1, random_state = 0).fit(x, y)
    with pytest.raises(ValueError, match = 'Every row'):
        oob_permutation(forest, x, y, ['x'])


def test_vectorized_permutations_match_independent_tree_reference():
    rng = np.random.default_rng(7)
    x = rng.normal(size = (24, 3)).astype(np.float32)
    y = (x[:, 0] + x[:, 1] > 0).astype(int)
    original = x.copy()
    forest = RandomForestClassifier(n_estimators = 30, random_state = 3).fit(x, y)
    actual = oob_permutation(forest, x, y, ['a', 'b', 'c'], repeats = 2, seed = 10)
    baseline, counts = np.zeros(len(y)), np.zeros(len(y), dtype = int)
    changed_totals = np.zeros((3, 2, len(y)))
    random = np.random.default_rng(10)
    for tree, sampled in zip(forest.estimators_, forest.estimators_samples_, strict = True):
        unsampled = np.setdiff1d(np.arange(len(y)), sampled)
        probabilities = tree.predict_proba(x[unsampled])[:, 1]
        baseline[unsampled] += probabilities
        counts[unsampled] += 1
        used = np.unique(tree.tree_.feature[tree.tree_.feature >= 0])
        for repeat in range(2):
            order = random.permutation(len(unsampled)) if len(used) else None
            for feature in range(3):
                modified = x[unsampled].copy()
                if feature in used:
                    modified[:, feature] = x[unsampled][order, feature]
                changed_totals[feature, repeat, unsampled] += tree.predict_proba(modified)[:, 1]
    score = f1_score(y, baseline / counts >= .5, zero_division = 0)
    for feature, row in enumerate(actual):
        drops = [score - f1_score(y, votes / counts >= .5, zero_division = 0)
                 for votes in changed_totals[feature]]
        assert row['mean_f1_drop'] == pytest.approx(np.mean(drops))
        assert row['std_f1_drop'] == pytest.approx(np.std(drops))
    assert np.array_equal(original, x)
