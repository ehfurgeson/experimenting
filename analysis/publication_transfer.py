"""Fixed-model publication transfer diagnostics with explicit scaffold purging."""

import argparse
import json
from collections import defaultdict
from importlib.metadata import version
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from ablations import _cohort
from professor_followup import estimator, matrix
from screen import HERE, hashes, read_records, write_csv
from structure_models import SEED

PROFILES = ('formula_raw', 'morgan_logistic', 'morgan_forest')


def transfer(rows, lineage, target = 'activity_target'):
    """Leave each publication out, merging alias provenance before any split or fit."""
    policies = {r.get('activity_policy') for r in rows
                if r.get(target) is not None and r.get('activity_policy')}
    if target == 'activity_target' and len(policies) > 1:
        raise ValueError('Use one activity_policy per transfer dataset')
    cohort = _cohort(rows, target)
    by_id = {r['compound_id']: r for r in rows}
    publications, seen = defaultdict(set), set()
    for item in lineage:
        cid, publication = item.get('compound_id'), item.get('publication')
        if cid not in by_id or not isinstance(publication, str) or not publication.strip():
            raise ValueError('Lineage requires known compound IDs and nonempty publications')
        publication = publication.strip()
        if (cid, publication) in seen:
            raise ValueError('Duplicate compound/publication lineage pair')
        seen.add((cid, publication))
        publications[cid].add(publication)
    if any(r.get(target) is not None and not publications[r['compound_id']] for r in rows):
        raise ValueError('Every labeled compound requires publication lineage, including aliases')
    by_structure = defaultdict(set)
    for row in rows:
        if row.get(target) is not None and row.get('canonical_structure'):
            by_structure[row['canonical_structure']].update(publications[row['compound_id']])
    source_sets = [by_structure[r['canonical_structure']] for r in cohort]
    y = np.array([r[target] for r in cohort], dtype = int)
    matrices = {p: matrix(cohort, p) for p in PROFILES} if cohort else {}
    if any(not np.isfinite(x).all() for x in matrices.values()):
        raise ValueError('Complete finite chemistry required')
    reports, predictions, membership = [], [], []
    for publication in sorted(set().union(*source_sets) if source_sets else set()):
        test = np.array([i for i, sources in enumerate(source_sets) if publication in sources])
        other = np.array([i for i, sources in enumerate(source_sets) if publication not in sources], dtype = int)
        test_scaffolds = {cohort[i]['scaffold'] for i in test}
        for scenario in ('publication_only', 'publication_and_scaffold'):
            train = np.array([i for i in other if scenario == 'publication_only' or
                              cohort[i]['scaffold'] not in test_scaffolds], dtype = int)
            status = ('insufficient_training_classes' if len(set(y[train])) < 2 else
                      'insufficient_test_classes' if len(set(y[test])) < 2 else 'evaluated')
            for partition, indices in [('train', train), ('test', test)]:
                membership.extend({'publication': publication, 'scenario': scenario,
                    'partition': partition, 'compound_id': cohort[i]['compound_id'],
                    'scaffold': cohort[i]['scaffold'], 'label': int(y[i])} for i in indices)
            for profile in PROFILES:
                report = {'publication': publication, 'scenario': scenario, 'profile': profile,
                    'status': status, 'train_n': len(train), 'test_n': len(test),
                    'train_active': int(y[train].sum()), 'test_active': int(y[test].sum()),
                    'purged_training_compounds': len(other) - len(train),
                    'shared_scaffolds': len({cohort[i]['scaffold'] for i in train} & test_scaffolds),
                    **dict.fromkeys(['f1', 'precision', 'recall', 'balanced_accuracy', 'roc_auc',
                                     'baseline_f1', 'baseline_balanced_accuracy', 'tn', 'fp', 'fn', 'tp'])}
                reports.append(report)
                if status != 'evaluated':
                    continue
                model = estimator(profile).fit(matrices[profile][train], y[train])
                probability = model.predict_proba(matrices[profile][test])[:, 1]
                predicted = probability >= .5
                baseline = np.full(len(test), int(y[train].sum() > len(train) / 2))
                tn, fp, fn, tp = confusion_matrix(y[test], predicted, labels = [0, 1]).ravel()
                report.update(
                    f1 = float(f1_score(y[test], predicted, zero_division = 0)),
                    precision = float(precision_score(y[test], predicted, zero_division = 0)),
                    recall = float(recall_score(y[test], predicted, zero_division = 0)),
                    balanced_accuracy = float(balanced_accuracy_score(y[test], predicted)),
                    roc_auc = float(roc_auc_score(y[test], probability)),
                    baseline_f1 = float(f1_score(y[test], baseline, zero_division = 0)),
                    baseline_balanced_accuracy = float(balanced_accuracy_score(y[test], baseline)),
                    tn = int(tn), fp = int(fp), fn = int(fn), tp = int(tp))
                predictions.extend({'publication': publication, 'scenario': scenario,
                    'profile': profile, 'compound_id': cohort[i]['compound_id'], 'label': int(y[i]),
                    'probability': float(p), 'baseline_prediction': int(b)}
                    for i, p, b in zip(test, probability, baseline, strict = True))
    return {'reports': reports, 'predictions': predictions, 'membership': membership}


def run(features, lineage, output, target = 'activity_target'):
    inputs = [Path(p).resolve() for p in (features, lineage)]
    output = Path(output).resolve()
    if any(path.is_relative_to(output) for path in inputs):
        raise ValueError('Output must be outside input paths')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use an empty output directory')
    before = hashes(inputs)
    result = transfer(read_records(inputs[0]), read_records(inputs[1]), target)
    if hashes(inputs) != before:
        raise ValueError('Inputs changed during transfer diagnostics')
    output.mkdir(parents = True, exist_ok = True)
    schemas = {
        'reports': ['publication', 'scenario', 'profile', 'status', 'train_n', 'test_n',
                    'train_active', 'test_active', 'purged_training_compounds', 'shared_scaffolds',
                    'f1', 'precision', 'recall', 'balanced_accuracy', 'roc_auc', 'baseline_f1',
                    'baseline_balanced_accuracy', 'tn', 'fp', 'fn', 'tp'],
        'predictions': ['publication', 'scenario', 'profile', 'compound_id', 'label', 'probability',
                        'baseline_prediction'],
        'membership': ['publication', 'scenario', 'partition', 'compound_id', 'scaffold', 'label'],
    }
    for name, columns in schemas.items():
        write_csv(output / f'{name}.csv', result[name], columns)
    manifest = {'input_hashes': before, 'output_hashes': hashes(list(output.iterdir())),
        'code_hashes': hashes(list(HERE.glob('*.py'))),
        'lock_hashes': hashes([HERE / 'uv.lock', HERE / 'pyproject.toml']),
        'versions': {name: version(name)
                     for name in ('rdkit', 'scikit-learn', 'numpy', 'polars')},
        'target': target, 'seed': SEED, 'threshold': .5, 'profiles': list(PROFILES),
        'scope': 'Exploratory transfer diagnostic, not scientific approval or evidence that '
                 'publication-specific assay labels measure a common estimand. No model selection. '
                 'Test sets may overlap across publications when structures have multiple sources.',
        'reports': result['reports']}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2, allow_nan = False) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--features', type = Path, required = True)
    parser.add_argument('--lineage', type = Path, required = True)
    parser.add_argument('--output', type = Path, required = True)
    parser.add_argument('--target', default = 'activity_target')
    args = parser.parse_args()
    print(json.dumps(run(args.features, args.lineage, args.output, args.target)['reports'], indent = 2))
