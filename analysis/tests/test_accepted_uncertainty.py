import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from accepted_uncertainty import confusion_scores, paired_intervals


def test_confusion_scores_use_all_fixed_classes_and_correct_low_recall():
    scores = confusion_scores(np.array([[4, 1, 0], [1, 4, 0], [0, 0, 0]]))
    assert scores['macro_f1'] == pytest.approx(1.6 / 3)
    assert scores['low_ld50_recall'] == pytest.approx(.8)


def test_paired_cluster_intervals_preserve_direction_for_constant_improvements():
    groups = ['a', 'a', 'b', 'b', 'c', 'c']
    y = np.array([1., 2., 3., 4., 5., 6.])
    r = paired_intervals(y, y + 1, y + .5, groups, 'regression', repeats = 30)[0]
    assert r['difference_expanded_minus_baseline'] == pytest.approx(-.5)
    assert r['conditional_bootstrap_lower95'] == pytest.approx(-.5)
    assert r['conditional_bootstrap_upper95'] == pytest.approx(-.5)
    y = np.array([0, 1, 2] * 3)
    r = paired_intervals(y, (y + 1) % 3, y, ['a'] * 3 + ['b'] * 3 + ['c'] * 3,
                         'classification', repeats = 30)
    macro = next(row for row in r if row['metric'] == 'macro_f1')
    assert macro['chemical_clusters'] == 3
    assert macro['difference_expanded_minus_baseline'] == 1
    assert macro['conditional_bootstrap_lower95'] == 1
