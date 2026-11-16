"""Literature names remain provisional even when database keys agree."""
import json
import sys
from pathlib import Path

import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from structure import structure_features
from weekly_literature import build_rows, resource_from, run


def inputs(tmp_path):
    resource = tmp_path / 'resource.json'
    data = {'sources': [{'source_id': 'paper', 'url': 'https://example.org/paper'}],
            'compounds': [{'name': 'ethanol', 'source_id': 'paper'}]}
    resource.write_text(json.dumps(data))
    snapshots = tmp_path / 'snapshots'
    snapshots.mkdir()
    key = structure_features('CCO')['structure_inchikey']
    (snapshots / 'identity_00.json').write_text(json.dumps({
        'name': 'ethanol', 'payload': {'PropertyTable': {'Properties': [
            {'CID': 702, 'SMILES': 'CCO', 'InChIKey': key}]}}}))
    return resource, data, snapshots


def test_database_match_does_not_assign_activity_or_origin(tmp_path):
    resource, data, snapshots = inputs(tmp_path)
    rows, features = build_rows(data, snapshots)
    assert len(features) == 1
    assert rows[0]['natural_origin'] == rows[0]['herbicidal_activity'] == 'unknown'
    assert rows[0]['identity_status'] == 'database_key_agrees_source_unverified'
    assert resource_from(resource) == data
    path = snapshots / 'identity_00.json'
    saved = json.loads(path.read_text())
    saved['payload']['PropertyTable']['Properties'][0]['InChIKey'] = 'wrong'
    path.write_text(json.dumps(saved))
    assert build_rows(data, snapshots)[1] == []


def test_missing_or_duplicate_identity_snapshots_fail(tmp_path):
    _, data, snapshots = inputs(tmp_path)
    path = snapshots / 'identity_00.json'
    (snapshots / 'identity_01.json').write_bytes(path.read_bytes())
    with pytest.raises(ValueError, match = 'exactly one'):
        build_rows(data, snapshots)


def test_exports_remove_exact_selection_overlap_and_preserve_inputs(tmp_path):
    resource, _, snapshots = inputs(tmp_path)
    selection = tmp_path / 'selection.parquet'
    pl.DataFrame([{'compound_id': 'PUBCHEM:702', 'selection_target': 1,
                   **structure_features('CCO')}]).write_parquet(selection)
    before = selection.read_bytes()
    output = tmp_path / 'output'
    manifest = run(resource, snapshots, selection, output)
    assert manifest['excluded_selection_overlaps'] == ['PUBCHEM:702']
    assert manifest['accepted_activity_labels'] == 0
    assert manifest['counts']['selected_herbicides'] == 0
    assert selection.read_bytes() == before
    assert (output / 'descriptors.svg').exists()
    assert (output / 'source_packets.json').exists()
    with pytest.raises(ValueError, match = 'empty output'):
        run(resource, snapshots, selection, output)
    with pytest.raises(ValueError, match = 'separate'):
        run(resource, snapshots, selection, snapshots)


def test_acquisition_preserves_the_exact_resource_before_later_annotations(tmp_path, monkeypatch):
    import weekly_literature as literature
    resource, _, _ = inputs(tmp_path)
    original = resource.read_bytes()

    class Client:
        def __init__(self, **kwargs):
            pass

        def resolve(self, name):
            return 702

        def properties(self, cid):
            return {'PropertyTable': {'Properties': []}}

    class Response:
        status_code = 403
        content = b'Publisher denied automated access'

    monkeypatch.setattr(literature, 'PubChemClient', Client)
    monkeypatch.setattr(literature.requests, 'get', lambda *a, **k: Response())
    snapshots = tmp_path / 'acquired'
    manifest = literature.fetch(resource, snapshots)
    resource.write_text('later annotations')
    assert (snapshots / 'acquisition_resource.json').read_bytes() == original
    assert list(manifest['input_hashes']) == [str(snapshots / 'acquisition_resource.json')]
    assert manifest['requests'][-1]['status'] == 403
