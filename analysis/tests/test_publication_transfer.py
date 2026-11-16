"""Source holdout must include alias provenance and expose shared scaffold families."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from publication_transfer import transfer
from screen import prepare


def fixtures():
    compounds = [
        ('a', 'c1ccccc1', 0, 'paper1'), ('b', 'Cc1ccccc1', 1, 'paper2'),
        ('c', 'C1CCCCC1', 1, 'paper1'), ('d', 'C1CCCC1', 0, 'paper2'),
        ('e', 'c1ccncc1', 0, 'paper2'), ('f', 'c1ccoc1', 1, 'paper2'),
    ]
    rows = prepare([{'compound_id': cid, 'smiles': smiles} for cid, smiles, _, _ in compounds])
    for row, (_, _, target, _) in zip(rows, compounds, strict = True):
        row['activity_target'] = target
    lineage = [{'compound_id': cid, 'publication': publication} for cid, _, _, publication in compounds]
    return rows, lineage


def test_publication_and_scaffold_holdout_are_distinct_and_alias_safe(monkeypatch):
    # Use the fixed raw-logistic profile to keep the regression fast.
    monkeypatch.setattr('publication_transfer.PROFILES', ('formula_raw',))
    rows, lineage = fixtures()
    alias = dict(rows[1], compound_id = 'alias-b')
    rows.append(alias)
    lineage.append({'compound_id': 'alias-b', 'publication': 'paper1'})
    result = transfer(rows, lineage)
    assert len(result['reports']) == 4
    for scenario in ('publication_only', 'publication_and_scaffold'):
        members = [r for r in result['membership'] if r['publication'] == 'paper1'
                   and r['scenario'] == scenario]
        # Lexically smallest alias represents b; provenance from both aliases is retained.
        assert 'alias-b' in {r['compound_id'] for r in members if r['partition'] == 'test'}
        assert 'alias-b' not in {r['compound_id'] for r in members if r['partition'] == 'train'}
    purged = [r for r in result['reports'] if r['scenario'] == 'publication_and_scaffold']
    assert all(r['shared_scaffolds'] == 0 for r in purged)
    assert {r['publication']: r['status'] for r in purged} == {
        'paper1': 'evaluated', 'paper2': 'insufficient_training_classes'}
    expected = {(r['publication'], r['scenario'], r['compound_id']): r['probability']
                for r in result['predictions']}
    repeated = transfer(list(reversed(rows)), list(reversed(lineage)))
    actual = {(r['publication'], r['scenario'], r['compound_id']): r['probability']
              for r in repeated['predictions']}
    assert actual == expected


def test_shared_scaffolds_are_purged_before_fitting(monkeypatch):
    monkeypatch.setattr('publication_transfer.PROFILES', ('formula_raw',))
    rows, lineage = fixtures()
    result = transfer(rows, lineage)
    reports = {(r['publication'], r['scenario']): r for r in result['reports']}
    assert reports['paper1', 'publication_only']['shared_scaffolds'] == 1
    assert reports['paper1', 'publication_and_scaffold']['purged_training_compounds'] == 1
    assert reports['paper1', 'publication_and_scaffold']['shared_scaffolds'] == 0


@pytest.mark.parametrize('case', ['missing', 'orphan', 'blank', 'duplicate', 'conflict', 'mixed_policy'])
def test_invalid_lineage_or_targets_fail_before_model_fit(monkeypatch, case):
    rows, lineage = fixtures()
    if case == 'missing':
        lineage.pop()
    elif case == 'orphan':
        lineage.append({'compound_id': 'orphan', 'publication': 'paper'})
    elif case == 'blank':
        lineage[0]['publication'] = ' '
    elif case == 'duplicate':
        lineage.append(dict(lineage[0]))
    elif case == 'conflict':
        rows.append(dict(rows[0], compound_id = 'conflict', activity_target = 1))
        lineage.append({'compound_id': 'conflict', 'publication': 'paper1'})
    else:
        rows[0]['activity_policy'], rows[1]['activity_policy'] = 'one', 'two'
    def no_fit(*args, **kwargs):
        pytest.fail('Invalid inputs reached estimator.fit')
    monkeypatch.setattr('sklearn.pipeline.Pipeline.fit', no_fit)
    with pytest.raises(ValueError):
        transfer(rows, lineage)


def test_single_source_or_single_class_test_returns_null_metrics_without_fitting(monkeypatch):
    rows, _ = fixtures()
    def no_fit(*args, **kwargs):
        pytest.fail('Unsupported split reached estimator.fit')
    monkeypatch.setattr('sklearn.pipeline.Pipeline.fit', no_fit)
    one_source = [{'compound_id': r['compound_id'], 'publication': 'only'} for r in rows]
    result = transfer(rows, one_source)
    assert {r['status'] for r in result['reports']} == {'insufficient_training_classes'}
    assert all(r['f1'] is None for r in result['reports'])
    assert not result['predictions']
    assert transfer([], []) == {'reports': [], 'predictions': [], 'membership': []}
    # A source with only one class must not produce an apparently perfect F1/AUC.
    rows = rows[:3]
    lineage = [{'compound_id': row['compound_id'], 'publication': 'test' if i == 0 else 'train'}
               for i, row in enumerate(rows)]
    rows[2]['activity_target'] = 0
    result = transfer(rows, lineage)
    assert all(r['status'] != 'evaluated' for r in result['reports'])


def test_command_products_hashes_and_source_protection(tmp_path, monkeypatch):
    import csv
    import json

    import polars as pl

    from publication_transfer import run

    monkeypatch.setattr('publication_transfer.PROFILES', ('formula_raw',))
    rows, lineage = fixtures()
    features = tmp_path / 'features.parquet'
    pl.DataFrame(rows, infer_schema_length = None).write_parquet(features)
    sources = tmp_path / 'lineage.csv'
    with sources.open('w', newline = '') as stream:
        writer = csv.DictWriter(stream, fieldnames = ['compound_id', 'publication'])
        writer.writeheader()
        writer.writerows(lineage)
    before = features.read_bytes(), sources.read_bytes()
    output = tmp_path / 'output'
    manifest = run(features, sources, output)
    assert len(manifest['output_hashes']) == 3
    assert json.loads((output / 'manifest.json').read_text())['threshold'] == .5
    assert (features.read_bytes(), sources.read_bytes()) == before
    with pytest.raises(ValueError, match = 'empty output'):
        run(features, sources, output)
    with pytest.raises(ValueError, match = 'outside input'):
        run(features, sources, tmp_path)
