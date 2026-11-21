"""Matched held-out experiments for frozen A and two accepted source expansions."""

import argparse
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from data_sprint import read_csv, sha256, write_csv
from evidence_models import classification_metrics, merged_groups, regression_metrics
from evidence_release import FEATURES
from oob import oob_permutation
from sprint_report import verify_bundle

SEED = 20261117


def fixed_partitions(rows, folds = 5):
    groups = merged_groups(rows)
    if len(set(groups)) < folds:
        raise ValueError('Insufficient joint scaffold/connectivity groups')
    assignments = np.full(len(rows), -1)
    for fold, (train, test) in enumerate(GroupKFold(folds).split(np.zeros(len(rows)), groups = groups)):
        if set(groups[train]) & set(groups[test]):
            raise AssertionError('Chemical group leakage')
        assignments[test] = fold
    return groups, assignments


def run(release, output):
    release, output = Path(release), Path(output)
    verify_bundle(release)
    scenarios = ['frozen_A', 'source_asserted', 'all_accepted']
    files = {'frozen_A': release / 'frozen_A_compounds.csv',
             **{s: release / f'{s}_classification_compounds.csv' for s in scenarios[1:]}}
    inputs = [release / 'manifest.json', *files.values()]
    before = {str(p): sha256(p) for p in inputs}
    cohorts = {s: {r['full_key']: r for r in read_csv(path)} for s, path in files.items()}
    universe = [cohorts['all_accepted'][k] for k in sorted(cohorts['all_accepted'])]
    x = np.array([[float(r[f]) for f in FEATURES] for r in universe])
    labels = np.array([int(r['ld50_bin']) for r in universe])
    targets = np.array([float(r['target_log10_mg_kg']) if r['target_log10_mg_kg'] else np.nan
                        for r in universe])
    groups, assignment = fixed_partitions(universe)
    keys = [r['full_key'] for r in universe]
    output.mkdir(parents = True, exist_ok = False)
    predictions, weights, support = [], [], []
    splits = [{'full_key': key, 'fold': int(assignment[i]), 'group': groups[i],
               'evaluation_stratum': ('frozen_A' if key in cohorts['frozen_A'] else
                                      'new_source_asserted' if key in cohorts['source_asserted'] else
                                      'additional_all_accepted'),
               'target_kind': universe[i]['target_kind']}
              for i, key in enumerate(keys)]
    for fold in range(5):
        test = np.flatnonzero(assignment == fold)
        for scenario in scenarios:
            train = np.array([i for i, key in enumerate(keys)
                              if assignment[i] != fold and key in cohorts[scenario]], dtype = int)
            if set(groups[train]) & set(groups[test]):
                raise AssertionError('Train/test scaffold or connectivity overlap')
            for task in ['classification', 'regression']:
                tr = train if task == 'classification' else train[[
                    bool(cohorts[scenario][keys[i]]['target_log10_mg_kg']) for i in train]]
                te = test if task == 'classification' else test[np.isfinite(targets[test])]
                ytrain = np.array([int(cohorts[scenario][keys[i]]['ld50_bin']) if task == 'classification'
                                   else float(cohorts[scenario][keys[i]]['target_log10_mg_kg'])
                                   for i in tr])
                support.append({'fold': fold, 'scenario': scenario, 'task': task,
                                'training_n': len(tr), 'test_n': len(te),
                                'training_groups': len(set(groups[tr])),
                                'training_classes': json.dumps(dict(Counter(map(int, ytrain))))
                                if task == 'classification' else ''})
                if task == 'classification':
                    models = {
                        'majority': DummyClassifier(strategy = 'most_frequent'),
                        'logistic': make_pipeline(StandardScaler(), LogisticRegression(
                            class_weight = 'balanced', max_iter = 3000, random_state = SEED)),
                        'forest': RandomForestClassifier(n_estimators = 200, min_samples_leaf = 5,
                            class_weight = 'balanced', max_features = 1., random_state = SEED, n_jobs = 2)}
                else:
                    models = {
                        'median': DummyRegressor(strategy = 'median'),
                        'ridge': make_pipeline(StandardScaler(), Ridge(alpha = 1)),
                        'forest': RandomForestRegressor(n_estimators = 200, min_samples_leaf = 5,
                            max_features = 1., random_state = SEED, n_jobs = 2)}
                for name, model in models.items():
                    model.fit(x[tr], ytrain)
                    pred = model.predict(x[te])
                    proba = model.predict_proba(x[te]) if task == 'classification' else None
                    for j, i in enumerate(te):
                        item = {'scenario': scenario, 'fold': fold, 'task': task, 'profile': name,
                                'full_key': keys[i], 'evaluation_stratum': splits[i]['evaluation_stratum'],
                                'target_kind': universe[i]['target_kind'],
                                'observed': int(labels[i]) if task == 'classification' else targets[i],
                                'predicted': float(pred[j])}
                        if proba is not None:
                            item.update({f'probability_{c}': float(proba[j, list(model.classes_).index(c)])
                                         if c in model.classes_ else 0. for c in [0, 1, 2]})
                        predictions.append(item)
                    if name == 'logistic':
                        fitted = model[-1]
                        weights.extend({'scenario': scenario, 'fold': fold, 'class': int(cls),
                                        'feature': feature, 'standardized_weight': float(weight)}
                                       for cls, coefficients in zip(fitted.classes_, fitted.coef_, strict = True)
                                       for feature, weight in zip(FEATURES, coefficients, strict = True))
        print('Accepted toxicity fold', fold, 'complete', flush = True)
    strata = defaultdict(list)
    for r in predictions:
        strata[(r['scenario'], r['task'], r['profile'], r['evaluation_stratum'])].append(r)
        strata[(r['scenario'], r['task'], r['profile'], 'all_accepted_targets')].append(r)
    metrics = []
    for (scenario, task, profile, stratum), rs in strata.items():
        y = np.array([r['observed'] for r in rs])
        pred = np.array([r['predicted'] for r in rs])
        calculated = (regression_metrics(y, pred) if task == 'regression' else
                      classification_metrics(y, pred, np.array([[r[f'probability_{c}'] for c in [0, 1, 2]]
                                                               for r in rs])))
        metrics.append({'scenario': scenario, 'task': task, 'profile': profile,
                        'evaluation_stratum': stratum, 'n': len(rs), **calculated})
    oob = []
    for scenario in scenarios:
        indices = [i for i, key in enumerate(keys) if key in cohorts[scenario]]
        y = np.array([int(cohorts[scenario][keys[i]]['ld50_bin']) == 0 for i in indices], dtype = int)
        forest = RandomForestClassifier(n_estimators = 200, min_samples_leaf = 5,
            class_weight = 'balanced', max_features = 1., random_state = SEED, n_jobs = 2).fit(x[indices], y)
        oob.extend({'scenario': scenario, **r} for r in oob_permutation(
            forest, x[indices], y, FEATURES, repeats = 5, seed = SEED))
    for name, data in [('metrics', metrics), ('predictions', predictions), ('weights', weights),
                       ('support', support), ('split_membership', splits), ('oob', oob)]:
        write_csv(output / f'{name}.csv', data, list(dict.fromkeys(k for r in data for k in r)))
    result = {'inputs': before, 'seed': SEED, 'folds': 5,
              'cohort_sizes': {s: len(c) for s, c in cohorts.items()},
              'evaluation_policy': 'Same five joint scaffold/connectivity partitions on the '
                                   'widest accepted cohort. Frozen A outcomes never change. '
                                   'External evaluation uses all-accepted targets; source-asserted '
                                   'training targets can differ as more source values enter.',
              'limits': 'User-accepted experimental evidence; grouped chemical validation, not '
                        'untouched publication validation. OOB uses low-LD50 binary target and '
                        'repeat SD is stability, not a significance test.'}
    if before != {str(p): sha256(p) for p in inputs}:
        raise ValueError('Inputs changed during evaluation')
    rep = output / 'reproduction'
    rep.mkdir()
    for p in [Path(__file__), Path('analysis/evidence_models.py'), Path('analysis/oob.py')]:
        shutil.copyfile(p, rep / p.name)
    result['products'] = {str(p.relative_to(output)): sha256(p)
                          for p in output.rglob('*') if p.is_file()}
    (output / 'manifest.json').write_text(json.dumps(result, indent = 2) + '\n')
    return result['cohort_sizes']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--release', type = Path, required = True)
    parser.add_argument('--output', type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(run(args.release, args.output), indent = 2))
