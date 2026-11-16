"""Frozen structural audit of user-reported benign food compounds; no biological labels assigned."""
import csv
import json
import sys
from collections import Counter
from importlib.metadata import version
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'analysis'))
from screen import hashes, write_csv
from structure import structure_features

OUT = Path(__file__).resolve().parent
if set(p.name for p in OUT.iterdir()) != {'audit.py'}:
    raise ValueError('Use a fresh audit directory')
source = ROOT / 'notes/plant_animal_food_compounds_200.tsv'
with source.open(newline = '') as stream:
    reader = csv.DictReader(stream, delimiter = '\t')
    assert reader.fieldnames == ['Name', 'PubChem CID', 'SMILES', 'InChIKey']
    rows = list(reader)
assert len(rows) == 200
for field in ('Name', 'PubChem CID', 'InChIKey'):
    assert len({r[field] for r in rows}) == 200
    assert all(r[field].strip() for r in rows)
features, identities = [], []
for line, row in enumerate(rows, 2):
    c = structure_features(row['SMILES'])
    assert c['structure_status'] == 'valid', row['Name']
    assert c['structure_inchikey'] == row['InChIKey'], row['Name']
    assert int(row['PubChem CID']) > 0
    identity = f"food200:{line - 1:03d}"
    features.append({'compound_id': identity, 'query': row['Name'],
                     'selection_target': None, 'activity_target': None, 'origin_target': None, **c})
    identities.append({'compound_id': identity, 'source_line': line, 'name': row['Name'],
                       'supplied_cid': row['PubChem CID'], 'supplied_smiles': row['SMILES'],
                       'supplied_inchikey': row['InChIKey'], 'computed_inchikey': c['structure_inchikey'],
                       'key_agrees': True, 'formula_status': c['formula_status'], 'scaffold': c['scaffold'],
                       'benignity_provenance': 'user_reports_verified; supporting records not in this TSV',
                       'pubchem_cid_crosscheck': 'not_independently_checked',
                       'plant_activity': 'unknown'})
paths = {
    'original_selection': ROOT / 'analysis/outputs/structure-2026-10-28-stress-baseline/structural_features.parquet',
    'dietary40': ROOT / 'analysis/outputs/dietary-review-2026-11-04-final/features.parquet',
    'assay154': ROOT / 'analysis/outputs/chembl-review-screen-2026-10-29-final/structural_features.parquet',
}
overlaps, overlap_counts = [], {}
for label, path in paths.items():
    known = pl.read_parquet(path).to_dicts()
    matches = []
    for r in features:
        key = r['structure_inchikey']
        for k in known:
            previous = k.get('structure_inchikey') or ''
            if not previous or key.split('-')[0] != previous.split('-')[0]:
                continue
            kind = 'full_key' if key == previous else 'connectivity_only'
            matches.append({'source_cohort': label, 'compound_id': r['compound_id'], 'name': r['query'],
                            'existing_id': k['compound_id'], 'existing_name': k.get('query'),
                            'match': kind})
    overlaps.extend(matches)
    overlap_counts[label] = {
        'full_key_candidates': len({r['compound_id'] for r in matches if r['match'] == 'full_key'}),
        'connectivity_candidates_including_full': len({r['compound_id'] for r in matches}),
    }
scaffolds = Counter(r['scaffold'] for r in features)
summary = {
    'n': len(rows), 'unique_names_cids_and_keys': 200, 'parseable_structures': len(features),
    'matching_computed_keys': len(features), 'fingerprints': sum(r['fingerprint'] is not None for r in features),
    'formula_eligible': sum(r['formula_status'] == 'valid' for r in features),
    'scaffold_groups': len(scaffolds), 'acyclic': scaffolds['ACYCLIC'], 'overlaps': overlap_counts,
    'benignity_status': 'user_reports_verified; scope and supporting evidence not in four-column TSV',
    'plant_inactivity_established_by_this_audit': False, 'independent_cid_validation': False,
    'models_fitted': 0, 'biological_targets_assigned': 0,
}
assert summary['fingerprints'] == 200
assert overlap_counts['dietary40']['full_key_candidates'] == 40
write_csv(OUT / 'identity_checks.csv', identities, list(identities[0]))
write_csv(OUT / 'overlaps.csv', overlaps, list(overlaps[0]))
pl.DataFrame(features).write_parquet(OUT / 'features.parquet')
(OUT / 'audit.json').write_text(json.dumps(summary, indent = 2) + '\n')
manifest = {
    'input_hashes': hashes([source, *paths.values()]),
    'code_hashes': hashes([Path(__file__), ROOT / 'analysis/structure.py', ROOT / 'analysis/formula.py']),
    'versions': {n: version(n) for n in ('rdkit', 'polars')},
    'output_hashes': hashes(sorted(OUT.iterdir())), 'scope': __doc__,
}
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent = 2) + '\n')
print(json.dumps(summary, indent = 2))
