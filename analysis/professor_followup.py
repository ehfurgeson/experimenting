"""Matched scaffold diagnostics for halogen attribution and raw fingerprint classifiers."""

import argparse
import json
from importlib.metadata import version
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ablations import _cohort, _splits
from formula import ELEMENTS, FORMULA_FEATURES
from oob import oob_permutation
from screen import HERE, hashes, write_csv
from structure_models import SEED, feature_matrix, make_estimator

HALOGENS = ('F', 'Cl', 'Br', 'I')
HALOGEN_COLUMNS = [f'formula_{e}_{kind}' for e in HALOGENS for kind in ('count', 'fraction')]
PROFILES = ('formula_pca', 'formula_raw', 'halogens_only', 'halogen_presence',
            'formula_drop_halogen_columns', 'composition_without_halogens',
            'morgan_logistic', 'morgan_forest')


def composition_without_halogens(row):
    """Recompute totals/fractions after removing halogens, including indirect proxies."""
    counts = {e: row[f'formula_{e}_count'] for e in ELEMENTS if e not in HALOGENS}
    other = row['other_atom_count']
    total = sum(counts.values()) + other
    # The stored complete composition retains any elements outside the predictor allowlist.
    composition = row.get('formula_composition')
    if not isinstance(composition, str):
        raise TypeError('Complete formula_composition is required for halogen removal')
    distinct = sum(float(part.split(':')[1]) > 0 for part in composition.split(';')
                   if part.split(':')[0] not in HALOGENS)
    return [distinct, total, other] + [v for n in counts.values()
                                                  for v in (n, n / total if total else 0)]


def matrix(rows, profile):
    if profile == 'composition_without_halogens':
        return np.array([composition_without_halogens(r) for r in rows], dtype = float)
    if profile.startswith('morgan_'):
        return feature_matrix(rows, 'morgan')
    if profile == 'halogen_presence':
        return np.array([[int(any(r[f'formula_{e}_count'] for e in HALOGENS))] for r in rows])
    columns = (HALOGEN_COLUMNS if profile == 'halogens_only' else
               [c for c in FORMULA_FEATURES if c not in HALOGEN_COLUMNS]
               if profile == 'formula_drop_halogen_columns' else FORMULA_FEATURES)
    return np.array([[r[c] for c in columns] for r in rows], dtype = float)


def estimator(profile):
    if profile == 'formula_pca':
        return make_estimator()
    if profile == 'morgan_forest':
        return RandomForestClassifier(n_estimators = 500, min_samples_leaf = 2,
                                      class_weight = 'balanced', random_state = SEED, n_jobs = 1)
    classifier = LogisticRegression(C = 1, class_weight = 'balanced', max_iter = 5000,
                                    random_state = SEED)
    # Binary fingerprints remain unscaled, with no PCA; formula inputs are scaled in-fold.
    return classifier if profile == 'morgan_logistic' else make_pipeline(StandardScaler(), classifier)


def diagnose(rows, target = 'selection_target', permutation_repeats = 10):
    if type(permutation_repeats) is not int or not 0 <= permutation_repeats <= 100:
        raise ValueError('permutation_repeats must be an integer in 0..100')
    cohort = _cohort(rows, target)
    y = np.array([r[target] for r in cohort], dtype = int)
    groups = np.array([r['scaffold'] for r in cohort])
    # Validate all inputs before fitting or exporting any partial products.
    matrices = {p: matrix(cohort, p) for p in PROFILES}
    if any(not np.isfinite(x).all() for x in matrices.values()):
        raise ValueError('Complete finite chemistry required')
    status, splits = _splits(np.zeros((len(y), 1)), y, groups, 5)
    result = {'reports': [], 'oof': [], 'coefficients': [], 'permutations': [], 'cohort': []}
    for row in cohort:
        result['cohort'].append({k: row.get(k) for k in
                                 ('compound_id', 'canonical_structure', 'scaffold', 'query')} | {
                                     'label': row[target], 'halogen_present': int(any(
                                         row[f'formula_{e}_count'] for e in HALOGENS))})
    for profile, x in matrices.items():
        report = {'profile': profile, 'target': target, 'n': len(y), 'positives': int(y.sum()),
                      'negatives': int(len(y) - y.sum()), 'status': status,
                      'roc_auc': None, 'balanced_accuracy': None, 'tn': None, 'fp': None,
                      'fn': None, 'tp': None, 'precision': None, 'recall': None, 'f1': None}
        result['reports'].append(report)
        if not splits:
            continue
        # Constants are allowed for raw estimators; PCA requires training variation.
        if profile == 'formula_pca' and any(not np.any(np.ptp(x[a], axis = 0)) for a, _ in splits):
            report['status'] = 'no_training_variation'
            continue
        probabilities = np.zeros(len(y))
        for fold, (train, test) in enumerate(splits):
            model = estimator(profile).fit(x[train], y[train])
            probabilities[test] = model.predict_proba(x[test])[:, 1]
            result['oof'] += [{'profile': profile, 'compound_id': cohort[i]['compound_id'],
                                   'scaffold': str(groups[i]), 'fold': fold, 'label': int(y[i]),
                                   'probability': float(p)}
                              for i, p in zip(test, probabilities[test], strict = True)]
            if profile != 'formula_raw':
                continue
            coefficients = model.named_steps['logisticregression'].coef_[0]
            result['coefficients'] += [{'fold': fold, 'feature': c, 'coefficient': float(v),
                                       'scale': 'training-fold standard deviation',
                                       'positive_class': 'target=1'}
                                       for c, v in zip(FORMULA_FEATURES, coefficients, strict = True)]
            baseline = roc_auc_score(y[test], probabilities[test])
            blocks = {c: [i] for i, c in enumerate(FORMULA_FEATURES)}
            blocks['halogens_joint'] = [FORMULA_FEATURES.index(c) for c in HALOGEN_COLUMNS]
            for block, columns in blocks.items():
                rng = np.random.default_rng(SEED + fold)
                for repeat in range(permutation_repeats):
                    permuted = x[test].copy()
                    order = rng.permutation(len(test))
                    permuted[:, columns] = x[test][order][:, columns]
                    score = roc_auc_score(y[test], model.predict_proba(permuted)[:, 1])
                    result['permutations'].append({'fold': fold, 'feature': block,
                                                       'repeat': repeat, 'auc_drop': float(baseline - score)})
        tn, fp, fn, tp = confusion_matrix(y, probabilities >= .5, labels = [0, 1]).ravel()
        report.update(precision = float(precision_score(y, probabilities >= .5, zero_division = 0)),
                      recall = float(recall_score(y, probabilities >= .5, zero_division = 0)),
                      f1 = float(f1_score(y, probabilities >= .5, zero_division = 0)),
                      roc_auc = float(roc_auc_score(y, probabilities)),
                      balanced_accuracy = float(balanced_accuracy_score(y, probabilities >= .5)),
                      tn = int(tn), fp = int(fp), fn = int(fn), tp = int(tp))
    return result


def run(features, output, target = 'selection_target', permutation_repeats = 10, oob_repeats = 10):
    features, output = Path(features).resolve(), Path(output).resolve()
    if features.is_relative_to(output):
        raise ValueError('Output must be outside input paths')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use an empty output directory')
    result = diagnose(pl.read_parquet(features).to_dicts(), target, permutation_repeats)
    if type(oob_repeats) is not int or oob_repeats < 0:
        raise ValueError('oob_repeats must be a nonnegative integer')
    result['oob_importance'] = []
    if oob_repeats and result['reports'][-1]['status'] == 'evaluated':
        cohort = _cohort(pl.read_parquet(features).to_dicts(), target)
        x = matrix(cohort, 'morgan_forest')
        y = np.array([r[target] for r in cohort])
        forest = estimator('morgan_forest').fit(x, y)
        result['oob_importance'] = oob_permutation(
            forest, x, y, [f'morgan_bit_{i}' for i in range(x.shape[1])],
            repeats = oob_repeats, seed = SEED)
    output.mkdir(parents = True, exist_ok = True)
    schemas = {'reports': ['profile', 'target', 'n', 'positives', 'negatives', 'status', 'roc_auc',
                           'balanced_accuracy', 'tn', 'fp', 'fn', 'tp', 'precision', 'recall', 'f1'],
               'oof': ['profile', 'compound_id', 'scaffold', 'fold', 'label', 'probability'],
               'coefficients': ['fold', 'feature', 'coefficient', 'scale', 'positive_class'],
               'oob_importance': ['feature', 'mean_f1_drop', 'std_f1_drop', 'repeats',
                                  'baseline_oob_f1', 'n', 'min_oob_votes'],
               'permutations': ['fold', 'feature', 'repeat', 'auc_drop'],
               'cohort': ['compound_id', 'canonical_structure', 'scaffold', 'query', 'label',
                          'halogen_present']}
    for key, columns in schemas.items():
        write_csv(output / f'{key}.csv', result[key], columns)
    manifest = {'input_hashes': hashes([features]), 'code_hashes': hashes(list(HERE.glob('*.py'))),
                    'lock_hashes': hashes([HERE / 'uv.lock', HERE / 'pyproject.toml']),
                    'output_hashes': hashes(list(output.iterdir())), 'seed': SEED, 'folds': 5,
                    'target': target, 'permutation_repeats': permutation_repeats,
                    'oob_repeats': oob_repeats, 'threshold': .5,
                    'oob_scope': 'Exploratory full-cohort tree-specific OOB F1 permutation; '
                                 'repeat SD is not a significance test or scaffold validation.',
                    'versions': {n: version(n) for n in ('rdkit', 'numpy', 'scikit-learn', 'polars')},
                    'profiles': list(PROFILES), 'reports': result['reports'],
                    'forest': {'n_estimators': 500, 'min_samples_leaf': 2, 'max_features': 'sqrt'},
                    'scope': 'Exploratory cohort diagnostics; no toxicity/activity labels inferred.',
                    'class_meanings': ({'0': 'reviewed natural-occurrence cohort',
                                        '1': 'documented commercial-herbicide comparator cohort'}
                                       if target == 'provenance_comparator_target' else
                                       {'0': 'target=0', '1': 'target=1'})}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2, allow_nan = False) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--features', type = Path, required = True)
    parser.add_argument('--output', type = Path, required = True)
    parser.add_argument('--target', default = 'selection_target')
    parser.add_argument('--oob-repeats', type = int, default = 10)
    parser.add_argument('--permutation-repeats', type = int, default = 10)
    args = parser.parse_args()
    print(json.dumps(run(args.features, args.output, args.target, args.permutation_repeats,
                             args.oob_repeats)['reports'],
                     indent = 2))
