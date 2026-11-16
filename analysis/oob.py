"""Tree-specific OOB permutation diagnostics, separate from scaffold validation."""
import numpy as np
from sklearn.metrics import f1_score


def oob_permutation(forest, x, y, names, repeats = 10, seed = 20261027):
    """Shuffle only each tree's unsampled rows; reuse their vote denominators.

    Features absent from a tree cannot affect its predictions. Skipping them is
    exact, and makes bit-level Morgan diagnostics practical without impurity ranks.
    """
    if type(repeats) is not int or repeats < 1:
        raise ValueError('repeats must be a positive integer')
    x, y = np.asarray(x, dtype = np.float32), np.asarray(y)
    if x.ndim != 2 or x.shape[1] != len(names) or len(x) != len(y):
        raise ValueError('Feature names, matrix and labels must align')
    if set(np.unique(y)) != {0, 1} or not np.isfinite(x).all():
        raise ValueError('Finite features and both binary classes required')
    if not forest.bootstrap or not np.array_equal(forest.classes_, [0, 1]):
        raise ValueError('A bootstrap forest with classes [0, 1] is required')
    totals, counts = np.zeros(len(y)), np.zeros(len(y), dtype = int)
    cache = []
    for tree, sampled in zip(forest.estimators_, forest.estimators_samples_, strict = True):
        mask = np.ones(len(y), dtype = bool)
        mask[np.unique(sampled)] = False
        indices = np.flatnonzero(mask)
        base = tree.predict_proba(x[indices])[:, 1] if len(indices) else np.array([])
        totals[indices] += base
        counts[indices] += 1
        cache.append((tree, indices, base))
    valid = counts > 0
    if not valid.all():
        raise ValueError('Every row requires at least one OOB vote; increase tree count')
    baseline = f1_score(y, totals / counts >= .5, zero_division = 0)
    # Sum only changed votes; unused tree features leave the baseline intact.
    deltas = np.zeros((len(names), repeats, len(y)))
    rng = np.random.default_rng(seed)
    for tree, indices, base in cache:
        used = np.unique(tree.tree_.feature[tree.tree_.feature >= 0])
        if not len(indices) or not len(used):
            continue
        original = x[indices]
        for repeat in range(repeats):
            order = rng.permutation(len(indices))
            batch = np.tile(original, (len(used), 1))
            for j, feature in enumerate(used):
                batch[j * len(indices):(j + 1) * len(indices), feature] = original[order, feature]
            changed = tree.predict_proba(batch)[:, 1].reshape(len(used), len(indices))
            for j, feature in enumerate(used):
                deltas[feature, repeat, indices] += changed[j] - base
    rows = []
    for feature, name in enumerate(names):
        drops = [float(baseline - f1_score(y, (totals + delta) / counts >= .5,
                                          zero_division = 0)) for delta in deltas[feature]]
        rows.append({'feature': name, 'mean_f1_drop': float(np.mean(drops)),
                     'std_f1_drop': float(np.std(drops)), 'repeats': repeats,
                     'baseline_oob_f1': float(baseline), 'n': len(y),
                     'min_oob_votes': int(counts.min())})
    return rows
