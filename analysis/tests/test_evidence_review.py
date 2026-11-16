"""Proposal packets cannot silently acquire approval or discard identity holds."""
import copy
import json
import sys
from pathlib import Path

import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence_review import RESOURCE, build, validate_resource
from screen import hashes


def test_resource_all_fifteen_and_dose_conflict_are_explicit():
    data = json.loads(RESOURCE.read_text())
    validate_resource(data, list(data['origin_leads']))
    assert len(data['origin_leads']) == 15 and len(data['observations']) == 81
    sarmentine = [r for r in data['observations'] if r['name'] == 'Sarmentine']
    assert all(r['proposed_activity'] == 'unknown' for r in sarmentine)
    assert '10' in sarmentine[0]['conflicts'] and '20' in sarmentine[0]['conflicts']
    changed = copy.deepcopy(data)
    changed['observations'][0]['approval_state'] = 'approved'
    with pytest.raises(ValueError, match = 'unreviewed'):
        validate_resource(changed, list(data['origin_leads']))
    changed = copy.deepcopy(data)
    changed['policies'][next(iter(changed['policies']))]['approval_state'] = 'approved'
    with pytest.raises(ValueError, match = 'Scientific approval'):
        validate_resource(changed, list(data['origin_leads']))


def test_build_keeps_seven_column_labels_unknown_and_copies_hold_bytes(tmp_path):
    data = json.loads(RESOURCE.read_text())
    data.pop('named_structure_reconstructions', None)
    data['origin_leads'] = {'Ethanol': {'proposal': 'unknown', 'sources': [], 'reason': 'No reviewed source'}}
    data['observations'] = [{**data['observations'][0], 'name': 'Ethanol',
                             'activity_policy': 'PROPOSED-K1998-LETTUCE-1MM-6D-v1'}]
    resource = tmp_path / 'resource.json';resource.write_text(json.dumps(data))
    literature = tmp_path / 'literature';literature.mkdir()
    pl.DataFrame([{'name': 'Ethanol', 'compound_id': 'PUBCHEM:702', 'smiles': 'CCO',
                   'pubchem_inchikey': 'LFQSCWFLJHTTHZ-UHFFFAOYSA-N'}]).write_csv(literature / 'literature_evidence.csv')
    (literature / 'manifest.json').write_text(json.dumps({'output_hashes': hashes([literature / 'literature_evidence.csv'])}))
    sources = tmp_path / 'sources';sources.mkdir()
    (sources / 'manifest.json').write_text(json.dumps({'requests': [], 'output_hashes': {}}))
    holds = tmp_path / 'holds.csv';holds.write_text('compound_id\nCHEMBL2253255\n')
    output = tmp_path / 'output'
    manifest = build(resource, literature, sources, output, holds)
    assert manifest['accepted_activity_labels'] == manifest['models_fitted'] == 0
    labels = pl.read_csv(output / 'reviewed_labels.csv')
    assert labels.width == 7 and set(labels['herbicidal_activity']) == {'unknown'}
    assert (output / 'preserved_identity_holds.csv').read_bytes() == holds.read_bytes()
    assert not pl.read_csv(output / 'policy_readiness.csv')['five_fold_proposed_support'].any()
    with pytest.raises(ValueError, match = 'new output'):
        build(resource, literature, sources, output, holds)
    data['origin_leads']['Ethanol']['proposal'] = 'natural'
    data['named_structure_reconstructions'] = {'Ethanol': {'smiles': 'CCC', 'source_name': 'wrong source structure'}}
    resource.write_text(json.dumps(data))
    mismatch_output = tmp_path / 'mismatch'
    build(resource, literature, sources, mismatch_output, holds)
    worksheet = pl.read_csv(mismatch_output / 'approval_worksheet.csv')
    assert set(worksheet['proposed_decision']) == {'unknown'}
    assert set(worksheet['identity_status']) == {'name_structure_identity_hold'}
