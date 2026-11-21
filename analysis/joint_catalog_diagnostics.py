"""Reconstruct model diagnostics for the completed joint catalog screen."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.metrics import f1_score, mean_absolute_error
from sklearn.model_selection import GroupKFold

from accepted_plant_models import chemical_weights, metrics, partitions
from data_sprint import read_csv, sha256
from evidence_models import merged_groups, toxicity_forest
from evidence_release import FEATURES
from nice_endpoint_models import feature_arrays, models, read_observations
from plant_assay_regression import assay_forest
from research_followup import estimator, fit
from sprint_report import verify_bundle


def oob_importance(model, x, y, names, task, repeats=3):
    """Permute within each tree's unsampled rows and reassemble forest votes."""
    x = np.asarray(x, dtype=np.float32)
    n = len(y)
    classifier = task == 'classification'
    n_classes = len(model.classes_) if classifier else 1
    blocks = [(name, slice(i, i+1)) for i, name in enumerate(names) if name != 'morgan']
    if 'morgan' in names:
        blocks.append(('morgan', slice(len(names)-1, None)))
    counts = np.zeros(n, dtype=np.int32)
    baseline = np.zeros((n, n_classes))
    changes = np.zeros((len(blocks), repeats, n, n_classes))
    rng = np.random.default_rng(20261117)
    for tree, sample in zip(model.estimators_, model.estimators_samples_, strict=True):
        mask = np.ones(n, dtype=bool)
        mask[sample] = False
        indices = np.flatnonzero(mask)
        if not indices.size:
            continue
        features = x[indices]
        predict = tree.predict_proba if classifier else tree.predict
        votes = predict(features).reshape(-1, n_classes)
        counts[indices] += 1
        baseline[indices] += votes
        split_features = tree.tree_.feature
        orders = [rng.permutation(len(indices)) for _ in range(repeats)]
        for i, (_, block) in enumerate(blocks):
            if not ((split_features >= block.start) & (split_features < (block.stop or x.shape[1]))).any():
                continue
            permuted = features.copy()
            for r, order in enumerate(orders):
                permuted[:, block] = features[order, block]
                changes[i, r, indices] += predict(permuted).reshape(-1, n_classes) - votes
    covered = counts > 0
    if not covered.any():
        raise ValueError('The diagnostic fit has no unsampled observations')

    def loss(votes):
        if classifier:
            probabilities = votes[covered] / counts[covered, None]
            predicted = (model.classes_[(probabilities[:, 1] >= .5).astype(int)] if n_classes == 2
                         else model.classes_[probabilities.argmax(axis=1)])
            return 1 - f1_score(y[covered], predicted, labels=model.classes_, average='macro', zero_division=0)
        return mean_absolute_error(y[covered], votes[covered, 0] / counts[covered])

    baseline_loss = loss(baseline)
    for (name, _), replicates in zip(blocks, changes, strict=True):
        deltas = [loss(baseline + delta) - baseline_loss for delta in replicates]
        yield {'feature': name, 'mean_performance_loss': float(np.mean(deltas)),
               'shuffle_sd': float(np.std(deltas)), 'baseline': 1-baseline_loss if classifier else baseline_loss,
               'metric': 'Macro-F1 drop' if classifier else 'MAE increase', 'repeats': repeats,
               'training_rows': n, 'rows_with_oob_votes': int(covered.sum())}


def matrix(rows):
    return np.array([[float(r[f]) for f in FEATURES] for r in rows])


def run(root, training, nice, output):
    joint, plant, tox, ice, npass, endpoints = (root / name for name in (
        'catalog-joint-screen-v2', 'catalog-plant-activity-v3', 'catalog-bulk-public-v1',
        'public-cohorts-v2', 'npass-label-trusted-v2', 'other-toxicity-endpoints-v2'))
    summary = verify_bundle(joint)['counts']
    for folder in (plant, tox, ice, npass, endpoints):
        verify_bundle(folder)
    training_manifest = training.with_name('manifest.json')
    if sha256(training) != json.loads(training_manifest.read_text())['products'][training.name]:
        raise ValueError('Plant training release checksum mismatch')
    oob, plant_validation, weights, panel_validation = [], [], [], []

    def diagnose(name, model, x, y, names, task='classification', fit_weights=None):
        model.fit(x, y, sample_weight=fit_weights)
        oob.extend({'model': name, **row} for row in oob_importance(model, x, y, names, task))
        print(name, 'OOB complete', flush=True)

    a = read_csv(ice / 'A_compounds.csv')
    oral_cohorts = {'Oral · ICE': a, 'Oral · CATMoS': read_csv(ice / 'B_compounds.csv'),
                    'Oral · ICE + NPASS': a + read_csv(npass / 'candidate_labels.csv')}
    for name, rows in oral_cohorts.items():
        diagnose(name, toxicity_forest(), matrix(rows), np.array([int(r['ld50_bin']) for r in rows]), FEATURES)

    pooled = read_csv(training)
    x, y = matrix(pooled), np.array([int(r['label']) for r in pooled])
    diagnose('Plant · pooled response', estimator('descriptor7_forest'), x, y, FEATURES,
             fit_weights=chemical_weights(pooled))
    for protocol in ('random_row', 'publication', 'chemical_group'):
        for profile in ('descriptor7_forest', 'descriptor7_logistic'):
            pred = np.empty(len(y))
            for fold, (train, test) in enumerate(partitions(pooled, protocol)):
                model = fit(estimator(profile), x[train], y[train], chemical_weights([pooled[i] for i in train]), profile)
                pred[test] = model.predict_proba(x[test])[:, 1]
                if profile.endswith('logistic'):
                    weights.extend({'protocol': protocol, 'fold': fold, 'feature': name, 'weight': float(value)}
                                   for name, value in zip(FEATURES, model[-1].coef_[0], strict=True))
            plant_validation.append({'split': protocol, 'profile': profile, 'observations': len(y),
                                     **metrics(y, pred, chemical_weights(pooled))})

    assay_rows = read_csv(plant / 'assay_training_observations.csv')
    for species, endpoint in sorted({(r['species'], r['endpoint']) for r in assay_rows}):
        rows = [r for r in assay_rows if (r['species'], r['endpoint']) == (species, endpoint)]
        x = np.column_stack((matrix(rows), np.log10([float(r['dose_um']) for r in rows])))
        y = np.array([float(r['inhibition_percent']) for r in rows])
        name = f'Plant · {species} {endpoint.replace("_", " ")}'
        diagnose(name, assay_forest(), x, y, [*FEATURES, 'log10_dose'], 'regression')
        pred, median = np.empty(len(y)), np.empty(len(y))
        for train, test in GroupKFold(5).split(x, groups=merged_groups(rows)):
            pred[test] = assay_forest().fit(x[train], y[train]).predict(x[test])
            median[test] = np.median(y[train])
        known = (y >= 40) | (y <= 20)
        panel_validation.append({'model': name, 'observations': len(y), 'high_observations': int((y >= 40).sum()),
                                 'mae_points': mean_absolute_error(y, pred), 'median_mae_points': mean_absolute_error(y, median),
                                 'band_macro_f1': f1_score(y[known] >= 40, pred[known] >= 40, average='macro',
                                                          zero_division=0) if (y >= 40).any() else None})

    identities = {r['full_key']: r for r in read_csv(ice / 'chemical_identity.csv') if r['identity_status'] == 'valid'}
    for _ in read_observations(nice, identities, defaultdict(Counter)):
        pass
    cohorts = defaultdict(list)
    target_file = endpoints / 'targets.csv'
    for row in read_csv(target_file):
        cohorts[row['endpoint']].append(row)
    for row in read_csv(tox / 'endpoint_summary.csv'):
        name, profile, binary = row['endpoint'], row['profile'], row['task'] == 'binary'
        rows = cohorts[name]
        x, fingerprints, _ = feature_arrays([r['full_key'] for r in rows], identities)
        with_morgan = profile == 'descriptors_morgan'
        diagnose(name, models(binary)[profile], fingerprints if with_morgan else x,
                 np.array([float(r['target']) for r in rows]), [*FEATURES, 'morgan'] if with_morgan else FEATURES,
                 'classification' if binary else 'log10 regression')

    output.mkdir(parents=True, exist_ok=False)
    for name, rows in [('oob_importance', oob), ('pooled_plant_validation', plant_validation),
                       ('plant_logistic_weights', weights), ('plant_assay_validation', panel_validation)]:
        pl.DataFrame(rows).write_csv(output / f'{name}.csv')
    inputs = [folder / 'manifest.json' for folder in (joint, plant, tox, ice, npass, endpoints)]
    inputs.extend([training, training_manifest])
    manifest = {'screen_counts': summary, 'models_with_oob': len({r['model'] for r in oob}),
                'inputs': {str(p): sha256(p) for p in inputs},
                'products': {p.name: sha256(p) for p in output.iterdir()}}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'training', 'nice', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    run(**vars(parser.parse_args()))
