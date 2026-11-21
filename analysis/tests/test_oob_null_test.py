from collections import Counter

import numpy as np

from oob_null_test import block_strata, permute_labels, randomization_pvalue


def test_only_whole_equal_size_blocks_can_move():
    groups = ['A', 'B', 'A', 'B', 'C', 'C', 'C', 'D', 'E']
    labels = np.array([1, 0, 1, 0, 1, 1, 0, 0, 1])
    rng = np.random.default_rng(17)
    strata = block_strata(groups)
    assert {size: len(blocks) for size, blocks in strata.items()} == {1: 2, 2: 2, 3: 1}
    draws = [permute_labels(labels, strata, rng) for _ in range(12)]
    assert any(not np.array_equal(draw, labels) for draw in draws)
    for draw in draws:
        assert list(draw[4:7]) == list(labels[4:7])
        assert Counter((tuple(draw[[0, 2]]), tuple(draw[[1, 3]]))) == Counter(((1, 1), (0, 0)))
        assert Counter(draw) == Counter(labels)


def test_monte_carlo_test_adds_one_and_includes_ties():
    assert randomization_pvalue(.80, [.20, .79, .80, .81]) == .60
    assert randomization_pvalue(.90, [.20, .79, .80, .81]) == .20
