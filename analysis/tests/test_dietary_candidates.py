"""Candidate identities, source overlap and unknown labels remain explicit offline."""
import csv
import json
import sys
from pathlib import Path

import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dietary_candidates as dietary
from structure import structure_features


def inputs(tmp_path):
    seeds = tmp_path / 'seeds.tsv'
    with seeds.open('w', newline = '') as stream:
        writer = csv.DictWriter(stream, fieldnames = ['name', 'family', 'food_source_url',
                                                       'review_caveat'], delimiter = '\t')
        writer.writeheader()
        writer.writerow({'name': 'example', 'family': 'fixture',
                         'food_source_url': 'https://example.org/source',
                         'review_caveat': 'HOLD: fixture only'})
    snapshots = tmp_path / 'raw'
    snapshots.mkdir()
    chemistry = structure_features('CCO')
    prop = {'CID': 702, 'SMILES': 'CCO', 'InChIKey': chemistry['structure_inchikey']}
    snapshot = {'query': 'example', 'url': 'https://example.org/identity',
                'retrieved_at': '2026-11-04T00:00:00+00:00',
                'response': {'PropertyTable': {'Properties': [prop]}}}
    (snapshots / '000.json').write_text(json.dumps(snapshot))
    known = tmp_path / 'known.parquet'
    pl.DataFrame([{'compound_id': 'known', 'query': 'known', 'selection_target': 0,
                   **chemistry}]).write_parquet(known)
    return seeds, snapshots, known, tmp_path / 'output'


def test_identity_checked_four_column_export_retains_unknown_labels_and_overlap(tmp_path):
    paths = inputs(tmp_path)
    manifest = dietary.build(*paths)
    assert manifest['n'] == manifest['holds'] == manifest['overlap_rows'] == 1
    output = paths[-1]
    frame = pl.read_csv(output / 'candidates.tsv', separator = '\t')
    assert frame.columns == ['name', 'pubchem_cid', 'smiles', 'inchikey']
    assert pl.read_parquet(output / 'features.parquet')['activity_target'].to_list() == [None]
    review = pl.read_csv(output / 'review.csv').row(0, named = True)
    assert review['review_status'] == 'hold'
    assert review['high_dose_safety'] == review['plant_activity'] == 'unknown'
    assert review['existing_matches'] == 'known'
    with pytest.raises(ValueError, match = 'empty output'):
        dietary.build(*paths)


@pytest.mark.parametrize('change,message', [('mismatch', 'InChIKey mismatch'),
                                           ('ambiguous', 'Ambiguous'),
                                           ('missing', 'match all seed')])
def test_bad_identity_never_creates_a_partial_bundle(tmp_path, change, message):
    paths = inputs(tmp_path)
    raw = paths[1] / '000.json'
    snapshot = json.loads(raw.read_text())
    if change == 'mismatch':
        snapshot['response']['PropertyTable']['Properties'][0]['InChIKey'] = 'bad'
    elif change == 'ambiguous':
        snapshot['response']['PropertyTable']['Properties'] *= 2
    else:
        snapshot['query'] = 'unmatched'
    raw.write_text(json.dumps(snapshot))
    with pytest.raises(ValueError, match = message):
        dietary.build(*paths)
    assert not paths[-1].exists()


def test_seed_policy_requires_traceable_unique_names(tmp_path):
    assert len(dietary.seeds_from(dietary.DEFAULT_SEEDS)) == 40
    seeds = inputs(tmp_path)[0]
    seeds.write_text(seeds.read_text() + seeds.read_text().splitlines()[1] + '\n')
    with pytest.raises(ValueError, match = 'unique'):
        dietary.seeds_from(seeds)
