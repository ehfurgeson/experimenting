"""Expanded-cohort preflight guards evidence boundaries without fitting models."""

import csv
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from activity_preflight import inspect, run
from labels import LABEL_FIELDS
from structure_models import evaluate


def label(identity, activity = 'active', policy = 'EXPERIMENT-v1'):
    return {'compound_id': identity, 'natural_origin': 'unknown', 'origin_reference': '',
            'herbicidal_activity': activity, 'activity_reference': 'fixture study',
            'activity_context': 'fixture species/dose/time/endpoint', 'activity_policy': policy}


def test_new_ids_aliases_unknowns_and_invalid_chemistry_are_auditable():
    result = inspect([
        {'compound_id': 'new', 'smiles': 'CCO'},
        {'compound_id': 'alias', 'smiles': 'OCC'},
        {'compound_id': 'unknown', 'smiles': 'c1ccccc1'},
        {'compound_id': 'bad', 'smiles': 'CC.Cl'},
    ], [label('new'), label('alias'), label('bad', 'inactive')], set())
    assert result['models_fitted'] == 0
    assert result['reports'][0]['n'] == 1
    assert result['reports'][0]['inactive_scaffold_deficit'] == 5
    members = {r['compound_id']: r for r in result['members'] if r['representation'] == 'formula'}
    assert members['new']['status'] == 'canonical_alias'
    assert members['new']['representative_id'] == 'alias'
    assert members['unknown']['status'] == 'unknown_activity'
    assert members['bad']['status'] == 'multicomponent'


@pytest.mark.parametrize('case', ['conflict', 'orphan', 'duplicate', 'mixed_policy', 'hold', 'alias_hold'])
def test_ambiguous_or_held_labels_fail(case):
    compounds = [{'compound_id': 'a', 'smiles': 'CCO'}, {'compound_id': 'b', 'smiles': 'OCC'}]
    labels, holds = [label('a')], set()
    if case == 'conflict':
        labels.append(label('b', 'inactive'))
    elif case == 'orphan':
        labels.append(label('missing'))
    elif case == 'duplicate':
        labels.append(label('a'))
    elif case == 'mixed_policy':
        labels.append(label('b', policy = 'OTHER'))
    elif case == 'hold':
        holds.add('a')
    else:
        holds.add('b')
    with pytest.raises(ValueError):
        inspect(compounds, labels, holds)


def test_supported_folds_match_model_and_never_fit(monkeypatch):
    # Each scaffold bears both classes; no canonical structure has conflicting labels.
    smiles = ['c1ccccc1', 'C1CCCCC1', 'c1ccncc1', 'C1CCCC1', 'c1ccoc1', 'C1CCC1']
    compounds, labels = [], []
    for i, core in enumerate(smiles):
        for target in (0, 1):
            identity = f'{i}-{target}'
            compounds.append({'compound_id': identity, 'smiles': ('C' if target else '') + core})
            labels.append(label(identity, 'active' if target else 'inactive'))
    from labels import attach_labels
    from screen import prepare
    reference = evaluate(attach_labels(prepare(compounds), labels), 'activity_target', 'formula')
    assert reference['report']['status'] == 'evaluated'

    def no_fit(*args, **kwargs):
        pytest.fail('Preflight attempted model fitting')

    monkeypatch.setattr('sklearn.pipeline.Pipeline.fit', no_fit)
    result = inspect(compounds, labels, set())
    report = result['reports'][0]
    assert report['status'] == 'supported'
    expected = {r['compound_id']: r['fold'] for r in reference['oof']}
    actual = {r['compound_id']: r['fold'] for r in result['assignments']
              if r['representation'] == 'formula' and r['partition'] == 'test'}
    assert actual == expected
    assert inspect(list(reversed(compounds)), labels, set())['assignments'] == result['assignments']
    for fold in range(5):
        rows = [r for r in result['assignments'] if r['representation'] == 'formula' and r['fold'] == fold]
        train = {r['scaffold'] for r in rows if r['partition'] == 'train'}
        test = {r['scaffold'] for r in rows if r['partition'] == 'test'}
        assert train.isdisjoint(test)
        assert {r['label'] for r in rows if r['partition'] == 'test'} == {0, 1}


def test_run_hashes_preserves_sources_and_requires_fresh_output(tmp_path):
    compounds = tmp_path / 'compounds.csv'
    compounds.write_text('compound_id,smiles\nnew,CCO\n')
    labels = tmp_path / 'labels.csv'
    with labels.open('w', newline = '') as stream:
        writer = csv.DictWriter(stream, fieldnames = sorted(LABEL_FIELDS))
        writer.writeheader()
        writer.writerow(label('new'))
    holds = tmp_path / 'holds.csv'
    holds.write_text('compound_id,reason\noutside,identity unresolved\n')
    before = [p.read_bytes() for p in (compounds, labels, holds)]
    output = tmp_path / 'output'
    manifest = run(compounds, labels, [holds], output)
    assert manifest['holds_outside_cohort'] == ['outside']
    assert len(manifest['input_hashes']) == 3
    assert len(manifest['output_hashes']) == 3
    assert json.loads((output / 'manifest.json').read_text())['models_fitted'] == 0
    assert [p.read_bytes() for p in (compounds, labels, holds)] == before
    with pytest.raises(ValueError, match = 'empty output'):
        run(compounds, labels, [holds], output)
    with pytest.raises(ValueError, match = 'outside input'):
        run(compounds, labels, [holds], tmp_path)
    with pytest.raises(ValueError, match = 'hold CSV'):
        run(compounds, labels, [], tmp_path / 'unused')
    labels.write_text('compound_id,herbicidal_activity\nnew,active\n')
    with pytest.raises(ValueError, match = 'seven label'):
        run(compounds, labels, [holds], tmp_path / 'invalid')
    assert not (tmp_path / 'invalid').exists()


def test_input_change_during_inspection_is_rejected_before_output(tmp_path, monkeypatch):
    compounds = tmp_path / 'compounds.csv'
    compounds.write_text('compound_id,smiles\na,CCO\n')
    labels = tmp_path / 'labels.csv'
    with labels.open('w', newline = '') as stream:
        writer = csv.DictWriter(stream, fieldnames = sorted(LABEL_FIELDS))
        writer.writeheader()
        writer.writerow(label('a'))
    holds = tmp_path / 'holds.csv'
    holds.write_text('compound_id\n')
    original = inspect

    def changed_input(*args):
        result = original(*args)
        holds.write_text('compound_id\na\n')
        return result

    monkeypatch.setattr('activity_preflight.inspect', changed_input)
    output = tmp_path / 'output'
    with pytest.raises(ValueError, match = 'Inputs changed'):
        run(compounds, labels, [holds], output)
    assert not output.exists()
