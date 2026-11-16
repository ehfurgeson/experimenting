"""Acquire PubChem identities and build an unlabelled dietary-comparator review bundle."""

import argparse
import csv
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

import polars as pl
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from screen import HERE, hashes, write_csv
from structure import structure_features

DEFAULT_SEEDS = HERE / 'resources/dietary_candidate_seeds.tsv'


def seeds_from(path):
    with Path(path).open(newline = '') as stream:
        rows = list(csv.DictReader(stream, delimiter = '\t'))
    names = [r.get('name') for r in rows]
    if not rows or any(not n for n in names) or len(names) != len(set(names)):
        raise ValueError('Seed names must be nonempty and unique')
    if any(not r.get('family') or not r.get('food_source_url', '').startswith('https://')
           or not r.get('review_caveat') for r in rows):
        raise ValueError('Each seed requires family, food source URL and review caveat')
    return rows


def fetch(seeds, snapshots):
    """Explicit online step; preserve each successful response even if a later request fails."""
    rows = seeds_from(seeds)
    snapshots = Path(snapshots)
    if snapshots.exists() and any(snapshots.iterdir()):
        raise ValueError('Use an empty snapshot directory')
    snapshots.mkdir(parents = True, exist_ok = True)
    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries = Retry(
        total = 3, backoff_factor = 1, status_forcelist = [429, 500, 502, 503, 504])))
    for i, row in enumerate(rows):
        url = ('https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/' +
               quote(row['name'], safe = '') + '/property/IsomericSMILES,InChIKey/JSON')
        response = session.get(url, timeout = 60)
        response.raise_for_status()
        snapshot = {'query': row['name'], 'url': url,
                    'retrieved_at': datetime.now(UTC).isoformat(), 'response': response.json()}
        (snapshots / f'{i:03d}.json').write_text(json.dumps(snapshot, indent = 2) + '\n')
        print(f"{i + 1}/{len(rows)} {row['name']}", flush = True)
        time.sleep(.25)
    return snapshots


def build(seeds, snapshots, features, output):
    seeds, snapshots, features, output = [Path(p).resolve()
                                           for p in (seeds, snapshots, features, output)]
    if any(p.is_relative_to(output) for p in (seeds, snapshots, features)):
        raise ValueError('Output must be outside input paths')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use an empty output directory')
    rows = seeds_from(seeds)
    raw_paths = sorted(snapshots.glob('*.json'))
    saved = {}
    for path in raw_paths:
        snapshot = json.loads(path.read_text())
        name = snapshot['query']
        if name in saved:
            raise ValueError('Duplicate snapshot query')
        saved[name] = snapshot
    if set(saved) != {r['name'] for r in rows}:
        raise ValueError('Snapshots must match all seed names exactly')
    known = pl.read_parquet(features).to_dicts()
    reviews, four_columns, chemistry, overlaps = [], [], [], []
    for row in rows:
        snapshot = saved[row['name']]
        properties = snapshot['response']['PropertyTable']['Properties']
        if len(properties) != 1:
            raise ValueError(f"Ambiguous PubChem result: {row['name']}")
        prop = properties[0]
        cid, key = prop['CID'], prop['InChIKey']
        smiles = prop.get('SMILES') or prop.get('IsomericSMILES')
        computed = structure_features(smiles)
        if type(cid) is not int or cid <= 0 or computed['structure_status'] != 'valid':
            raise ValueError(f"Invalid identity: {row['name']}")
        if computed['structure_inchikey'] != key:
            raise ValueError(f"PubChem/RDKit InChIKey mismatch: {row['name']}")
        four_columns.append({'name': row['name'], 'pubchem_cid': cid, 'smiles': smiles,
                             'inchikey': key})
        compound_id = f'pubchem:{cid}'
        chemistry.append({'compound_id': compound_id, 'query': row['name'],
                          'selection_target': None, 'activity_target': None,
                          'origin_target': None, **computed})
        matches = []
        for r in known:
            known_key = r.get('structure_inchikey') or r.get('inchikey') or ''
            kind = ('exact_structure' if computed['canonical_structure'] == r.get('canonical_structure')
                    else 'connectivity_inchikey' if key.split('-')[0] == known_key.split('-')[0]
                    else None)
            if kind:
                matches.append(r['compound_id'])
                overlaps.append({'candidate_id': compound_id, 'candidate_name': row['name'],
                                 'existing_id': r['compound_id'], 'existing_name': r.get('query'),
                                 'match': kind, 'existing_selection_target': r.get('selection_target')})
        reviews.append({**four_columns[-1], 'compound_id': compound_id, 'family': row['family'],
                        'food_source_url': row['food_source_url'], 'review_caveat': row['review_caveat'],
                        'caution_source_url': row.get('caution_source_url', ''),
                        'identity_status': 'pubchem_rdkit_agree', 'pubchem_url': snapshot['url'],
                        'retrieved_at': snapshot['retrieved_at'], 'scaffold': computed['scaffold'],
                        'existing_matches': ';'.join(matches),
                        'review_status': 'hold' if row['review_caveat'].startswith('HOLD:')
                                         else 'pending_human_review',
                        'high_dose_safety': 'unknown', 'plant_activity': 'unknown',
                        'natural_occurrence_reference': '', 'dose_value': '', 'dose_unit': '',
                        'population_species': '', 'route_duration': '', 'reviewer': '',
                        'decision_reference': '', 'decision': ''})
    if len({r['inchikey'] for r in four_columns}) != len(rows):
        raise ValueError('Duplicate candidate identity; review seeds before export')
    output.mkdir(parents = True, exist_ok = True)
    with (output / 'candidates.tsv').open('w', newline = '') as stream:
        writer = csv.DictWriter(stream, fieldnames = list(four_columns[0]), delimiter = '\t')
        writer.writeheader()
        writer.writerows(four_columns)
    write_csv(output / 'review.csv', reviews, list(reviews[0]))
    write_csv(output / 'overlaps.csv', overlaps, ['candidate_id', 'candidate_name', 'existing_id',
                                                'existing_name', 'match', 'existing_selection_target'])
    pl.DataFrame(chemistry).write_parquet(output / 'features.parquet')
    manifest = {'input_hashes': hashes([seeds, features, *raw_paths]),
                'code_hashes': hashes([Path(__file__), HERE / 'structure.py', HERE / 'formula.py']),
                'lock_hashes': hashes([HERE / 'uv.lock', HERE / 'pyproject.toml']),
                'output_hashes': hashes(list(output.iterdir())), 'n': len(rows),
                'holds': sum(r['review_status'] == 'hold' for r in reviews),
                'overlap_rows': len(overlaps),
                'scope': 'Dietary-source candidates only; no accepted high-dose or plant-negative labels.'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--seeds', type = Path, default = DEFAULT_SEEDS)
    parser.add_argument('--snapshots', type = Path, required = True)
    parser.add_argument('--fetch', action = 'store_true', help = 'Explicit online acquisition only')
    parser.add_argument('--features', type = Path)
    parser.add_argument('--output', type = Path)
    args = parser.parse_args()
    if args.fetch:
        fetch(args.seeds, args.snapshots)
    else:
        if args.features is None or args.output is None:
            parser.error('Offline build requires --features and --output')
        print(json.dumps(build(args.seeds, args.snapshots, args.features, args.output), indent = 2))
