"""Pooled accepted plant-response experiments with visible row/study/chemical leakage."""

import argparse
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold, StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from data_sprint import read_csv, sha256, write_csv
from evidence_models import merged_groups
from evidence_release import FEATURES
from oob import oob_permutation
from sprint_report import verify_bundle

SEED = 20261117


def chemical_weights(rows):
    counts = Counter(r['full_key'] for r in rows)
    return np.array([len(rows) / len(counts) / counts[r['full_key']] for r in rows])


def metrics(y, probability, weight = None):
    pred = probability >= .5
    return {'macro_f1': float(f1_score(y, pred, labels = [0, 1], average = 'macro',
                                      sample_weight = weight, zero_division = 0)),
            'high_response_f1': float(f1_score(y, pred, sample_weight = weight, zero_division = 0)),
            'precision': float(precision_score(y, pred, sample_weight = weight, zero_division = 0)),
            'recall': float(recall_score(y, pred, sample_weight = weight, zero_division = 0)),
            'balanced_accuracy': float(balanced_accuracy_score(y, pred, sample_weight = weight)),
            'auroc': float(roc_auc_score(y, probability, sample_weight = weight))
                     if len(set(y)) == 2 else None}


def partitions(rows, protocol):
    y = np.array([int(r['label']) for r in rows])
    x = np.zeros((len(rows), 1))
    if protocol == 'random_row':
        return list(StratifiedKFold(5, shuffle = True, random_state = SEED).split(x, y))
    groups = merged_groups(rows) if protocol == 'chemical_group' else np.array([
        r['reference_id'] for r in rows])
    if len(set(groups)) < 5:
        return []
    return list(GroupKFold(5).split(x, y, groups))


def run(release, output):
    release, output = Path(release), Path(output)
    verify_bundle(release)
    path = release / 'plant_training_observations.csv'
    before = {str(path): sha256(path), str(release / 'manifest.json'): sha256(release / 'manifest.json')}
    all_rows = read_csv(path)
    output.mkdir(parents = True, exist_ok = False)
    predictions, support, splits, weights, oob = [], [], [], [], []
    for scenario in ['quantitative_only', 'with_accepted_categories']:
        rows = [r for r in all_rows if scenario != 'quantitative_only' or r['label_kind'] == 'quantitative']
        x = np.array([[float(r[f]) for f in FEATURES] for r in rows])
        y = np.array([int(r['label']) for r in rows])
        for protocol in ['random_row', 'publication', 'chemical_group']:
            for fold, (train, test) in enumerate(partitions(rows, protocol)):
                train_rows, test_rows = [rows[i] for i in train], [rows[i] for i in test]
                key_overlap = {r['full_key'] for r in train_rows} & {r['full_key'] for r in test_rows}
                ref_overlap = {r['reference_id'] for r in train_rows} & {r['reference_id'] for r in test_rows}
                if protocol == 'chemical_group' and key_overlap or protocol == 'publication' and ref_overlap:
                    raise AssertionError('Declared holdout leakage')
                base = {'scenario': scenario, 'protocol': protocol, 'fold': fold}
                support.append({**base, 'training_n': len(train), 'test_n': len(test),
                                'training_structures': len({r['full_key'] for r in train_rows}),
                                'test_structures': len({r['full_key'] for r in test_rows}),
                                'overlapping_structures': len(key_overlap),
                                'overlapping_references': len(ref_overlap),
                                'test_seen_structure_fraction': float(np.mean([
                                    r['full_key'] in key_overlap for r in test_rows])),
                                'status': 'evaluated' if len(set(y[train])) == 2 else 'one_training_class'})
                if len(set(y[train])) != 2:
                    continue
                splits.extend({**base, 'observation_id': rows[i]['observation_id'],
                               'full_key': rows[i]['full_key'], 'reference_id': rows[i]['reference_id'],
                               'role': role} for role, indices in [('train', train), ('test', test)]
                              for i in indices)
                sample_weights = chemical_weights(train_rows)
                models = {
                    'majority': DummyClassifier(strategy = 'most_frequent'),
                    'logistic': make_pipeline(StandardScaler(), LogisticRegression(
                        class_weight = 'balanced', max_iter = 3000, random_state = SEED)),
                    'forest': RandomForestClassifier(n_estimators = 200, min_samples_leaf = 5,
                        max_features = 1., class_weight = 'balanced', random_state = SEED, n_jobs = 2)}
                for name, model in models.items():
                    params = {'logisticregression__sample_weight': sample_weights} if name == 'logistic' else {
                        'sample_weight': sample_weights}
                    model.fit(x[train], y[train], **params)
                    probabilities = model.predict_proba(x[test])[:, list(model.classes_).index(1)]
                    predictions.extend({**base, 'profile': name, 'observation_id': rows[i]['observation_id'],
                                        'full_key': rows[i]['full_key'],
                                        'reference_id': rows[i]['reference_id'], 'source': rows[i]['source'],
                                        'label': int(y[i]), 'probability': float(p)}
                                       for i, p in zip(test, probabilities, strict = True))
                    if name == 'logistic':
                        weights.extend({**base, 'feature': feature, 'standardized_weight': float(w)}
                                       for feature, w in zip(FEATURES, model[-1].coef_[0], strict = True))
            print('Accepted plant', scenario, protocol, 'complete', flush = True)
        forest = RandomForestClassifier(n_estimators = 200, min_samples_leaf = 5,
            max_features = 1., class_weight = 'balanced', random_state = SEED, n_jobs = 2).fit(
                x, y)
        # sklearn can use sample_weight as bootstrap sampling probabilities. Strong
        # inverse-frequency weights can then give rare rows no OOB votes at all.
        # Keep this explicitly separate, observation-weighted OOB diagnostic.
        oob.extend({'scenario': scenario, 'training_weighting': 'unweighted_observations', **r}
                   for r in oob_permutation(
            forest, x, y, FEATURES, repeats = 5, seed = SEED))
    grouped = defaultdict(list)
    for r in predictions:
        grouped[(r['scenario'], r['protocol'], r['profile'], 'all_sources')].append(r)
        grouped[(r['scenario'], r['protocol'], r['profile'], r['source'])].append(r)
    results = []
    for (scenario, protocol, profile, source), rs in grouped.items():
        y = np.array([r['label'] for r in rs])
        probability = np.array([r['probability'] for r in rs])
        for weighting in ['observation', 'equal_structure']:
            w = chemical_weights(rs) if weighting == 'equal_structure' else None
            results.append({'scenario': scenario, 'protocol': protocol, 'profile': profile,
                            'source': source, 'weighting': weighting, 'n': len(rs),
                            'structures': len({r['full_key'] for r in rs}), **metrics(y, probability, w)})
    for name, data in [('metrics', results), ('predictions', predictions), ('support', support),
                       ('splits', splits), ('weights', weights), ('oob', oob)]:
        write_csv(output / f'{name}.csv', data, list(dict.fromkeys(k for r in data for k in r)))
    summary = {'inputs': before, 'seed': SEED, 'folds': 5,
               'training_policy': 'Inverse observation count per structure within each training fold; '
                                  'fixed balanced logistic and forest, seven descriptors.',
               'evaluation_policy': 'Compare random rows (repeat overlap expected), held-out references '
                                    '(chemical overlap allowed and reported), and joint scaffold/'
                                    'connectivity groups (chemical overlap prohibited). Metrics are '
                                    'both observation-weighted and equal-structure-weighted.',
               'limits': 'Accepted retrospective heterogeneous response-band labels, with different '
                         'endpoints/doses/species. No universal plant inhibition or safety claim. '
                         'The separate OOB forest omits inverse-frequency sample weights to '
                         'retain OOB vote coverage, and can share repeated chemicals and studies.'}
    if before != {str(p): sha256(p) for p in before}:
        raise ValueError('Inputs changed during plant experiment')
    rep = output / 'reproduction'
    rep.mkdir()
    for p in [Path(__file__), Path('analysis/evidence_models.py'), Path('analysis/oob.py')]:
        shutil.copyfile(p, rep / p.name)
    summary['products'] = {str(p.relative_to(output)): sha256(p)
                           for p in output.rglob('*') if p.is_file()}
    (output / 'manifest.json').write_text(json.dumps(summary, indent = 2) + '\n')
    return {'predictions': len(predictions), 'metric_rows': len(results)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--release', type = Path, required = True)
    parser.add_argument('--output', type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(run(args.release, args.output), indent = 2))
