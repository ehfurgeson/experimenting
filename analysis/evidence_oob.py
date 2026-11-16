"""Same-target multiclass OOB macro-F1 diagnostics for frozen A/B cohorts."""
import argparse
import json
import shutil
from collections import Counter
from importlib.metadata import version
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

from evidence_models import SEED, read
from evidence_release import FEATURES, sha, write_csv


def macro_oob(forest, x, y, names, repeats = 10, seed = SEED):
    """Permute within each tree's OOB rows and aggregate class probability votes."""
    x, y = np.asarray(x, dtype = np.float32), np.asarray(y)
    if type(repeats) is not int or repeats < 1:
        raise ValueError('repeats must be a positive integer')
    if x.ndim != 2 or x.shape != (len(y), len(names)) or not np.isfinite(x).all():
        raise ValueError('Require aligned finite features and labels')
    classes = np.unique(y)
    if len(classes) < 2 or not np.array_equal(classes, np.arange(len(classes))):
        raise ValueError('Require contiguous class labels starting at zero')
    if not forest.bootstrap or not np.array_equal(forest.classes_, classes):
        raise ValueError('Require a bootstrap forest fitted on these classes')
    totals = np.zeros((len(y), len(classes)))
    counts = np.zeros(len(y), dtype = int)
    cache = []
    for tree, sampled in zip(forest.estimators_, forest.estimators_samples_, strict = True):
        mask = np.ones(len(y), dtype = bool)
        mask[np.unique(sampled)] = False
        indices = np.flatnonzero(mask)
        base = tree.predict_proba(x[indices]) if len(indices) else np.empty((0, len(classes)))
        totals[indices] += base
        counts[indices] += 1
        cache.append((tree, indices, base))
    if not np.all(counts > 0):
        raise ValueError('Every row requires at least one OOB vote')
    probabilities = totals / counts[:, None]
    prediction = probabilities.argmax(axis = 1)
    baseline = f1_score(y, prediction, average = 'macro', labels = classes, zero_division = 0)
    deltas = np.zeros((len(names), repeats, len(y), len(classes)))
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
            changed = tree.predict_proba(batch).reshape(len(used), len(indices), len(classes))
            for j, feature in enumerate(used):
                deltas[feature, repeat, indices] += changed[j] - base
    importance, repeat_rows = [], []
    for feature, name in enumerate(names):
        drops = []
        for repeat in range(repeats):
            changed = (totals + deltas[feature, repeat]).argmax(axis = 1)
            score = f1_score(y, changed, average = 'macro', labels = classes, zero_division = 0)
            drop = float(baseline - score)
            drops.append(drop)
            repeat_rows.append({'feature': name, 'repeat': repeat, 'macro_f1_drop': drop})
        importance.append({'feature': name, 'mean_macro_f1_drop': float(np.mean(drops)),
                           'sd_macro_f1_drop': float(np.std(drops)), 'repeats': repeats,
                           'baseline_oob_macro_f1': float(baseline), 'n': len(y),
                           'min_oob_votes': int(counts.min())})
    return {'importance': importance, 'repeats': repeat_rows,
            'probabilities': probabilities, 'predicted': prediction, 'votes': counts,
            'baseline_oob_macro_f1': float(baseline)}


def run(release, models, output, repeats = 10):
    release, models, output = map(Path, (release, models, output))
    if output.exists() or any(output.resolve().is_relative_to(p.resolve())
                              for p in (release, models)):
        raise ValueError('Choose a fresh separate output directory')
    for root in (release, models):
        manifest = json.loads((root / 'manifest.json').read_text())
        for name, expected in manifest['outputs'].items():
            if sha(root / name) != expected:
                raise ValueError('Frozen input hash mismatch: ' + name)
    if json.loads((models / 'manifest.json').read_text())['release_manifest_sha256'] != sha(
            release / 'manifest.json'):
        raise ValueError('Models used a different release')
    output.mkdir(parents = True)
    profile = {'n_estimators': 200, 'min_samples_leaf': 5, 'max_features': 1.0,
               'class_weight': 'balanced', 'random_state': SEED, 'n_jobs': 2}
    importance, repeat_rows, predictions, summary = [], [], [], []
    for pathway in ('A', 'B'):
        rows = read(release / f'{pathway}_compounds.csv')
        x = np.array([[float(r[f]) for f in FEATURES] for r in rows])
        y = np.array([int(r['ld50_bin']) for r in rows])
        forest = RandomForestClassifier(**profile).fit(x, y)
        result = macro_oob(forest, x, y, FEATURES, repeats = repeats)
        importance.extend({'pathway': pathway, **r} for r in result['importance'])
        repeat_rows.extend({'pathway': pathway, **r} for r in result['repeats'])
        predictions.extend({'pathway': pathway, 'full_key': r['full_key'], 'observed': int(y[i]),
                            'predicted': int(result['predicted'][i]),
                            'oob_votes': int(result['votes'][i]),
                            **{f'probability_{c}': float(result['probabilities'][i, c])
                               for c in range(3)}} for i, r in enumerate(rows))
        summary.append({'pathway': pathway, 'n': len(y),
                        'class_counts': dict(Counter(map(int, y))),
                        'oob_macro_f1': result['baseline_oob_macro_f1'],
                        'interpretation': 'whole_cohort_OOB_not_scaffold_held_out'})
        print(pathway, summary[-1]['oob_macro_f1'], flush = True)
    for name, rows in [('importance', importance), ('repeats', repeat_rows),
                       ('oob_predictions', predictions)]:
        write_csv(output / (name + '.csv'), rows)
    (output / 'summary.json').write_text(json.dumps(summary, indent = 2) + '\n')
    (output / 'reproduction').mkdir()
    code = [Path(__file__), Path(__file__).parent / 'evidence_models.py',
            Path(__file__).parent / 'evidence_release.py']
    for path in code:
        shutil.copyfile(path, output / 'reproduction' / path.name)
    manifest = {'inputs': {str(root / 'manifest.json'): sha(root / 'manifest.json')
                           for root in (release, models)}, 'profile': profile, 'repeats': repeats,
                'runtime': {name: version(name) for name in ['numpy', 'scikit-learn', 'polars', 'rdkit']},
                'code': {str(p): sha(p) for p in code},
                'outputs': {str(p.relative_to(output)): sha(p) for p in sorted(output.rglob('*'))
                            if p.is_file()},
                'limits': 'No null-hypothesis significance test; repeat SD is stability. '
                          'OOB is not scaffold validation; B reproduces external estimates.'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2) + '\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for name in ('release', 'models', 'output'):
        parser.add_argument('--' + name, type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(run(args.release, args.models, args.output), indent = 2))
