"""Read-only integration audit of the 29 October source-review package; no model fits."""
import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import polars as pl


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def write(path, rows, fields):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run(root, output):
    root, output = root.resolve(), output.resolve()
    source = root / 'notes/compound_review_deeper_2026-10-29'
    assert not output.exists(), 'Use a new audit directory'
    assert not source.is_relative_to(output) and not output.is_relative_to(source)
    sys.path.insert(0, str(root / 'analysis'))
    from ablations import _splits
    from labels import attach_labels
    inputs = list(sorted(source.iterdir()))
    assert all(p.is_file() for p in inputs) and len(inputs) == 16
    release = json.loads((source / 'release_manifest.json').read_text())
    inventory = []
    for path in inputs:
        expected = release['source_hashes_sha256'].get(path.name)
        assert expected is None or expected == digest(path), path
        rows = read(path) if path.suffix == '.csv' else None
        inventory.append({'file': path.name, 'bytes': path.stat().st_size,
                          'csv_rows': len(rows) if rows is not None else '',
                          'release_hash': 'verified' if expected else 'manifest itself',
                          'sha256': digest(path)})
    tables = {p.name: read(p) for p in inputs if p.suffix == '.csv'}
    index = tables['compound_index.csv']
    ids = {r['compound_id'] for r in index}
    assert len(index) == len(ids) == 154
    for name, rows in tables.items():
        if name != 'study_source_index.csv':
            assert {r['compound_id'] for r in rows} == ids, name
    log = tables['evidence_log.csv']
    assert len(log) == len({r['activity_id'] for r in log}) == 157
    handoff = root / 'analysis/outputs/chembl-researcher-handoff-2026-10-29'
    original = read(handoff / 'evidence_log.csv')
    inputs.append(handoff / 'evidence_log.csv')
    by_activity = {r['activity_id']: r for r in original}
    immutable = list(log[0])[:16]
    assert {r['activity_id'] for r in log} == set(by_activity)
    assert all(r[k] == by_activity[r['activity_id']][k] for r in log for k in immutable)
    for aid in {r['assay_chembl_id'] for r in log}:
        path = root / f'analysis/outputs/chembl-2026-10-28/raw/chembl/{aid}.json'
        assert all(r['source_snapshot_sha256'] == digest(path) for r in log if r['assay_chembl_id'] == aid)
        inputs.append(path)
    packet = (source / 'compound_evidence_packets.md').read_text()
    sections = dict(re.findall(r'^## (CHEMBL\d+)\n(.*?)(?=^## CHEMBL\d+|\Z)', packet, re.M | re.S))
    assert set(sections) == ids
    for row in index:
        block = sections[row['compound_id']]
        assert row['canonical_smiles'] in block
        assert all('| ' + r['activity_id'] + ' |' in block for r in log if r['compound_id'] == row['compound_id'])
    by_id = {r['compound_id']: r for r in index}
    assert all(r['frozen_canonical_smiles'] == by_id[r['compound_id']]['canonical_smiles']
               for r in tables['compound_by_compound_deep_audit.csv'])
    identical_handoff = {}
    for name in ('compound_index.csv', 'compound_evidence_packets.md'):
        path = handoff / name
        inputs.append(path)
        identical_handoff[name] = path.read_bytes() == (source / name).read_bytes()
        assert identical_handoff[name]
    features = root / 'analysis/outputs/chembl-review-screen-2026-10-29-final/structural_features.parquet'
    inputs.append(features)
    structures = pl.read_parquet(features).to_dicts()
    by_structure_id = {r['compound_id']: r for r in structures}
    assert set(by_structure_id) == ids
    assert all(by_structure_id[r['compound_id']]['input_smiles'] == r['canonical_smiles'] for r in index)
    working = attach_labels(structures, tables['reviewed_labels.csv'])
    assert all(r['activity_target'] is None and r['origin_target'] is None for r in working)
    counts = Counter(r['conditional_activity_NOT_A_LABEL'] for r in tables['conditional_assay_screen_NOT_FOR_TRAINING.csv'])
    assert counts == {'not_assessed': 68, 'active': 47, 'inactive': 31, 'unknown': 8}
    studies = []
    for study in tables['study_source_index.csv']:
        rows = [r for r in log if r['assay_chembl_id'] == study['assay_id']]
        assert len(rows) == int(study['observations'])
        studies.append({**study, 'unique_compounds': len({r['compound_id'] for r in rows})})
    support = []
    for name in ('PROVISIONAL_LI2006_NOT_FOR_TRAINING.csv', 'PROVISIONAL_HE2011_NOT_FOR_TRAINING.csv',
                 'PROVISIONAL_labels_NOT_FOR_TRAINING.csv'):
        attached = attach_labels(structures, tables[name])  # Schema audit only; NOT scientific approval.
        chosen = [r for r in attached if r['activity_target'] is not None]
        y = np.array([r['activity_target'] for r in chosen])
        groups = np.array([r['scaffold'] for r in chosen])
        x = np.zeros((len(chosen), 1))
        support.append({'file': name, 'hypothetical_labeled_n': len(chosen),
                        'proposed_active': int(y.sum()), 'proposed_low_response': int(len(y)-y.sum()),
                        'scaffolds': len(set(groups)),
                        'active_scaffolds': len(set(groups[y == 1])),
                        'low_response_scaffolds': len(set(groups[y == 0])),
                        'three_fold_support': _splits(x, y, groups, 3)[0],
                        'five_fold_support': _splits(x, y, groups, 5)[0],
                        'schema_parseable': True, 'scientifically_approved': False})
    overlaps = []
    for cohort, path in [('original_selection', root / 'analysis/outputs/structure-2026-10-28-stress-baseline/structural_features.parquet'),
                         ('dietary_candidates', root / 'analysis/outputs/dietary-review-2026-11-04-final/features.parquet')]:
        inputs.append(path)
        for r in structures:
            for q in pl.read_parquet(path).to_dicts():
                exact = r.get('canonical_structure') and r['canonical_structure'] == q.get('canonical_structure')
                connectivity = (r.get('structure_inchikey') and q.get('structure_inchikey') and
                    r['structure_inchikey'].split('-')[0] == q['structure_inchikey'].split('-')[0])
                if exact or connectivity:
                    overlaps.append({'cohort': cohort, 'review_id': r['compound_id'],
                                     'other_id': q['compound_id'], 'name': q.get('query'),
                                     'match': 'exact' if exact else 'connectivity_only'})
    links = []
    for path in source.glob('*.md'):
        text = path.read_text().replace('\\', '')
        text = re.sub(r'```.*?```', '', text, flags=re.S)
        for target in sorted(set(re.findall(r'\]\(([^)]+)\)', text))):
            if '://' in target or target.startswith('#'):
                continue
            relative = target.split('#')[0]
            if relative and not (path.parent / relative).exists():
                links.append({'file': path.name, 'broken_relative_target': target})
    result = {'source_files': len(inputs[:16]), 'release_hashes_verified': 15,
              'compounds': len(ids), 'observations': len(log), 'studies': len(studies),
              'original_source_columns_preserved': len(immutable), 'source_field_changes': 0,
              'packets_verified': len(sections), 'identical_to_original_handoff': identical_handoff,
              'approved_activity_labels': 0, 'approved_origin_labels': 0,
              'conditional_counts_NOT_APPROVED': dict(counts),
              'exact_original_overlap': sum(r['cohort']=='original_selection' and r['match']=='exact' for r in overlaps),
              'dietary_overlap': sum(r['cohort']=='dietary_candidates' for r in overlaps),
              'model_fits': 0, 'label_changes': 0, 'scope': 'Input/lineage/scaffold-support audit, not source-table or biological approval.'}
    output.mkdir(parents=True)
    shutil.copyfile(__file__, output / 'audit.py')
    for name, rows, fields in [('file_inventory.csv', inventory, list(inventory[0])),
                               ('study_inventory.csv', studies, list(studies[0])),
                               ('hypothetical_support_NOT_APPROVED.csv', support, list(support[0])),
                               ('identity_overlaps.csv', overlaps, ['cohort','review_id','other_id','name','match']),
                               ('broken_links.csv', links, ['file','broken_relative_target'])]:
        write(output / name, rows, fields)
    (output / 'audit.json').write_text(json.dumps(result, indent=2)+'\n')
    manifest = {'input_hashes': {str(p): digest(p) for p in sorted(set(inputs))},
                'code_hashes': {str(root/'analysis'/n):digest(root/'analysis'/n) for n in
                                ('labels.py','ablations.py','structure_models.py')},
                'output_hashes': {str(p):digest(p) for p in sorted(output.iterdir())},
                'audit_date': '2026-11-05', 'scope': result['scope']}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    print(json.dumps(support, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.root, args.output)
