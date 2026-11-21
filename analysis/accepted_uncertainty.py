"""Paired chemical-cluster bootstrap for fixed held-out A expansion comparisons."""

import argparse
import json
import shutil
from pathlib import Path

import numpy as np

from data_sprint import read_csv, sha256, write_csv
from sprint_report import verify_bundle


def confusion_scores(confusion):
    support = confusion.sum(axis = 1)
    predicted = confusion.sum(axis = 0)
    tp = np.diag(confusion)
    denom = support + predicted
    f1 = np.divide(2 * tp, denom, out = np.zeros(3), where = denom > 0)
    return {'macro_f1': float(f1.mean()),
            'low_ld50_recall': float(tp[0] / support[0]) if support[0] else None}


def paired_intervals(y, baseline, expanded, groups, task, repeats = 2000):
    y, baseline, expanded = map(np.asarray, [y, baseline, expanded])
    labels, inverse = np.unique(groups, return_inverse = True)
    rng = np.random.default_rng(20261117)
    if task == 'classification':
        cells = np.zeros((len(labels), 2, 3, 3))
        for i, group in enumerate(inverse):
            cells[group, 0, int(y[i]), int(baseline[i])] += 1
            cells[group, 1, int(y[i]), int(expanded[i])] += 1

        def score(weights):
            totals = np.einsum('g,gijk->ijk', weights, cells)
            return confusion_scores(totals[0]), confusion_scores(totals[1])
    else:
        counts = np.bincount(inverse)
        errors = np.column_stack([np.bincount(inverse, weights = np.abs(y - baseline)),
                                  np.bincount(inverse, weights = np.abs(y - expanded))])

        def score(weights):
            totals = (weights @ errors) / (weights @ counts)
            return {'mae_log10': float(totals[0])}, {'mae_log10': float(totals[1])}
    base, updated = score(np.ones(len(labels)))
    draws = {metric: [] for metric in base}
    for _ in range(repeats):
        weights = rng.multinomial(len(labels), np.full(len(labels), 1 / len(labels)))
        b, u = score(weights)
        for metric, values in draws.items():
            if b[metric] is not None and u[metric] is not None:
                values.append(u[metric] - b[metric])
    return [{'metric': metric, 'baseline': base[metric], 'expanded': updated[metric],
             'difference_expanded_minus_baseline': updated[metric] - base[metric],
             'conditional_bootstrap_lower95': float(np.quantile(values, .025)),
             'conditional_bootstrap_upper95': float(np.quantile(values, .975)),
             'structures': len(y), 'chemical_clusters': len(labels), 'repeats': repeats}
            for metric, values in draws.items()]


def run(models, output):
    models, output = Path(models), Path(output)
    verify_bundle(models)
    inputs = [models / 'predictions.csv', models / 'split_membership.csv']
    before = {str(p): sha256(p) for p in inputs}
    groups = {r['full_key']: r['group'] for r in read_csv(inputs[1])}
    predictions = read_csv(inputs[0])
    results = []
    for task in ['classification', 'regression']:
        base = {r['full_key']: r for r in predictions if r['task'] == task and
                r['profile'] == 'forest' and r['scenario'] == 'frozen_A' and
                r['evaluation_stratum'] == 'frozen_A'}
        keys = sorted(base)
        for scenario in ['source_asserted', 'all_accepted']:
            updated = {r['full_key']: r for r in predictions if r['task'] == task and
                       r['profile'] == 'forest' and r['scenario'] == scenario and
                       r['evaluation_stratum'] == 'frozen_A'}
            if set(base) != set(updated) or any(base[k]['observed'] != updated[k]['observed'] for k in keys):
                raise ValueError('Paired outcomes differ')
            statistics = paired_intervals(
                [float(base[k]['observed']) for k in keys],
                [float(base[k]['predicted']) for k in keys],
                [float(updated[k]['predicted']) for k in keys], [groups[k] for k in keys], task)
            results.extend({'scenario': scenario, 'task': task, **r} for r in statistics)
    output.mkdir(parents = True, exist_ok = False)
    write_csv(output / 'paired_cluster_intervals.csv', results, list(results[0]))
    rep = output / 'reproduction'
    rep.mkdir()
    shutil.copyfile(__file__, rep / Path(__file__).name)
    result = {'inputs': before,
              'method': 'Paired percentile bootstrap resampling joint scaffold/connectivity clusters '
                        'of fixed held-out predictions; 2,000 draws, seed 20261117.',
              'limits': 'Conditional on these fitted models and folds. No retraining, model-selection '
                        'uncertainty, study-independence correction or multiplicity-adjusted claim.',
              'products': {str(p.relative_to(output)): sha256(p)
                           for p in output.rglob('*') if p.is_file()}}
    (output / 'manifest.json').write_text(json.dumps(result, indent = 2) + '\n')
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--models', type = Path, required = True)
    parser.add_argument('--output', type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(run(args.models, args.output), indent = 2))
