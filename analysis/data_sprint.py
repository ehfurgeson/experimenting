"""Small, offline evidence-sprint helpers; scientific products stay in fresh local runs."""

import argparse
import csv
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import polars as pl


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path):
    with Path(path).open(newline = '', encoding = 'utf-8-sig') as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows, fields):
    with Path(path).open('w', newline = '') as stream:
        writer = csv.DictWriter(stream, fieldnames = fields)
        writer.writeheader()
        writer.writerows(rows)


def freeze_baseline(release, selection, output):
    """Freeze full-key memberships with upstream hashes, refusing any prior output."""
    release, selection, output = Path(release), Path(selection), Path(output)
    inputs = [release / 'manifest.json', release / 'A_compounds.csv',
              release / 'B_compounds.csv', selection]
    hashes = {str(path): sha256(path) for path in inputs}
    manifest = json.loads(inputs[0].read_text())
    products = manifest['outputs']
    for path in inputs[1:3]:
        expected = products.get(path.name)
        if isinstance(expected, dict):
            expected = expected['sha256']
        if expected != hashes[str(path)]:
            raise ValueError(f'Frozen release hash mismatch: {path}')
    rows = []
    for cohort in ('A', 'B'):
        source = release / f'{cohort}_compounds.csv'
        members = read_csv(source)
        keys = [r['full_key'] for r in members]
        if len(keys) != len(set(keys)) or not all(keys):
            raise ValueError(f'Nonunique or missing {cohort} full keys')
        for row in members:
            rows.append({'cohort': cohort, 'compound_id': row['full_key'],
                         'full_inchikey': row['full_key'], 'original_structure': row['smiles'],
                         'identity_status': 'valid', 'selection_group': '',
                         'target_log10_mg_kg': row['target_log10_mg_kg'],
                         'upstream_path': str(source), 'upstream_sha256': hashes[str(source)]})
    for row in pl.read_parquet(selection).to_dicts():
        rows.append({'cohort': 'selection', 'compound_id': row['compound_id'],
                     'full_inchikey': row['structure_inchikey'],
                     'original_structure': row['input_smiles'],
                     'identity_status': row['structure_status'],
                     'selection_group': row['chemical_group'], 'target_log10_mg_kg': '',
                     'upstream_path': str(selection), 'upstream_sha256': hashes[str(selection)]})
    output.mkdir(parents = True, exist_ok = False)
    write_csv(output / 'cohort_membership.csv', rows, list(rows[0]))
    counts = {c: sum(r['cohort'] == c for r in rows) for c in ('A', 'B', 'selection')}
    result = {'created_at': datetime.now(UTC).isoformat(),
              'upstream_commit': subprocess.check_output(
                  ['git', 'rev-parse', 'HEAD'], text = True).strip(),
              'inputs': hashes, 'counts': counts,
              'products': {'cohort_membership.csv': sha256(output / 'cohort_membership.csv')},
              'selection_scope': 'All prepared selection rows; natural-product membership is not '
                                 'verified occurrence or plant activity.',
              'independent_study_count': None}
    if hashes != {str(path): sha256(path) for path in inputs}:
        raise ValueError('Inputs changed during freeze')
    (output / 'manifest.json').write_text(json.dumps(result, indent = 2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--release', type = Path, required = True)
    parser.add_argument('--selection', type = Path, required = True)
    parser.add_argument('--output', type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(freeze_baseline(args.release, args.selection, args.output), indent = 2))
