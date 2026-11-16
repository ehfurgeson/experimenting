"""Validate expanded single-policy activity cohorts and inspect support without fitting."""

import argparse
import csv
import json
from collections import Counter
from importlib.metadata import version
from pathlib import Path

import numpy as np

from ablations import _splits
from labels import LABEL_FIELDS, attach_labels
from screen import HERE, hashes, prepare, read_records, write_csv
from structure_models import REPRESENTATIONS, SEED, eligible
from verification_release import reject_held_activity


def inspect(compounds, labels, hold_ids):
    """Check proposed evidence, retaining exclusions and canonical aliases for audit."""
    rows = attach_labels(prepare(compounds), labels)
    reject_held_activity(labels, hold_ids)
    held_structures = {r['canonical_structure'] for r in rows
                       if r['compound_id'] in hold_ids and r['canonical_structure']}
    for row in rows:
        if row['canonical_structure'] in held_structures and row['activity_target'] is not None:
            raise ValueError(f"Activity assignment blocked by held structure: {row['compound_id']}")
    reports, members, assignments = [], [], []
    for representation in REPRESENTATIONS:
        unique = {}
        for row in sorted(rows, key = lambda r: r['compound_id']):
            if row['activity_target'] is not None and eligible(row, representation):
                unique.setdefault(row['canonical_structure'], row)
        cohort = [unique[key] for key in sorted(unique)]
        y = np.array([r['activity_target'] for r in cohort], dtype = int)
        groups = np.array([r['scaffold'] for r in cohort])
        status, splits = _splits(np.zeros((len(cohort), 1)), y, groups, 5)
        counts = [int(np.sum(y == value)) for value in (0, 1)]
        scaffolds = [len(set(groups[y == value])) for value in (0, 1)]
        reports.append({
            'representation': representation, 'n': len(cohort),
            'inactive': counts[0], 'active': counts[1],
            'inactive_scaffolds': scaffolds[0], 'active_scaffolds': scaffolds[1],
            'inactive_compound_deficit': max(0, 5 - counts[0]),
            'active_compound_deficit': max(0, 5 - counts[1]),
            'inactive_scaffold_deficit': max(0, 5 - scaffolds[0]),
            'active_scaffold_deficit': max(0, 5 - scaffolds[1]),
            'status': 'supported' if status == 'evaluated' else status,
            'folds': len(splits),
        })
        for row in rows:
            reason = ('unknown_activity' if row['activity_target'] is None else
                      row['structure_status'] if row['structure_status'] != 'valid' else
                      'unsupported_formula' if not eligible(row, representation) else
                      'included' if unique[row['canonical_structure']]['compound_id'] ==
                      row['compound_id'] else 'canonical_alias')
            members.append({
                'representation': representation, 'compound_id': row['compound_id'],
                'canonical_structure': row['canonical_structure'], 'scaffold': row['scaffold'],
                'activity_target': row['activity_target'], 'status': reason,
                'representative_id': (unique[row['canonical_structure']]['compound_id']
                                      if row['canonical_structure'] in unique else None),
            })
        for fold, (train, test) in enumerate(splits):
            for partition, indices in [('train', train), ('test', test)]:
                for i in indices:
                    assignments.append({
                        'representation': representation, 'fold': fold, 'partition': partition,
                        'compound_id': cohort[i]['compound_id'], 'label': int(y[i]),
                        'scaffold': cohort[i]['scaffold'],
                    })
    return {'reports': reports, 'members': members, 'assignments': assignments,
            'structure_statuses': dict(Counter(r['structure_status'] for r in rows)),
            'activity_policies': sorted({r['activity_policy'] for r in rows
                                         if r['activity_target'] is not None}),
            'identity_holds': sorted(hold_ids),
            'holds_outside_cohort': sorted(hold_ids - {r['compound_id'] for r in rows}),
            'scientific_approval_verified': False, 'models_fitted': 0}


def run(compounds, labels, holds, output):
    """Require explicit hold inputs; hash inputs and write only into a fresh directory."""
    if not holds:
        raise ValueError('Supply at least one hold CSV, even if it has no rows')
    inputs = [Path(p).resolve() for p in [compounds, labels, *holds]]
    output = Path(output).resolve()
    if any(path.is_relative_to(output) for path in inputs):
        raise ValueError('Output must be outside input paths')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use an empty output directory')
    before = hashes(inputs)
    with inputs[1].open(encoding = 'utf-8-sig', newline = '') as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        if len(fields) != len(LABEL_FIELDS) or set(fields) != LABEL_FIELDS:
            raise ValueError('Preserve exactly the seven label columns')
        proposed = list(reader)
    hold_ids = set()
    for path in inputs[2:]:
        with path.open(encoding = 'utf-8-sig', newline = '') as stream:
            reader = csv.DictReader(stream)
            if 'compound_id' not in (reader.fieldnames or []):
                raise ValueError('Hold CSV requires compound_id')
            for row in reader:
                identity = row['compound_id']
                if not identity or not identity.strip():
                    raise ValueError('Hold compound_id must be nonempty')
                hold_ids.add(identity)
    result = inspect(read_records(inputs[0]), proposed, hold_ids)
    if hashes(inputs) != before:
        raise ValueError('Inputs changed during activity preflight')
    output.mkdir(parents = True, exist_ok = True)
    write_csv(output / 'support.csv', result['reports'], list(result['reports'][0]))
    write_csv(output / 'members.csv', result['members'], [
        'representation', 'compound_id', 'canonical_structure', 'scaffold',
        'activity_target', 'status', 'representative_id'])
    write_csv(output / 'folds.csv', result['assignments'], [
        'representation', 'fold', 'partition', 'compound_id', 'label', 'scaffold'])
    manifest = {key: value for key, value in result.items() if key not in {'members', 'assignments'}}
    manifest.update(
        input_hashes = before, code_hashes = hashes(list(HERE.glob('*.py'))),
        lock_hashes = hashes([HERE / 'uv.lock', HERE / 'pyproject.toml']),
        output_hashes = hashes(list(output.iterdir())), seed = SEED, requested_folds = 5,
        versions = {name: version(name) for name in ('rdkit', 'scikit-learn', 'numpy', 'polars')},
        scope = 'Computational support only; no scientific approval, feature-variation check or fit. '
                'Deficits are lower bounds, not sufficient additions. Holds are supplied by caller.',
    )
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2, allow_nan = False) + '\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--compounds', type = Path, required = True)
    parser.add_argument('--labels', type = Path, required = True)
    parser.add_argument('--holds', type = Path, action = 'append', required = True)
    parser.add_argument('--output', type = Path, required = True)
    args = parser.parse_args()
    manifest = run(args.compounds, args.labels, args.holds, args.output)
    for report in manifest['reports']:
        print(report['representation'], report['status'], 'n=', report['n'])


if __name__ == '__main__':
    main()
