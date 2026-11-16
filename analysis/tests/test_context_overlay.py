"""Source-context recovery must remain traceable and separate from raw toxicity values."""
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from context_overlay import apply_overlays, load_sources, run
from ecotox_comparison import summarize_strata
from screen import hashes, write_csv
from weekly_report import verify_manifest


def observation(**changes):
    return {'measurement_id': 'm1', 'test_id': 't1', 'source_result_id': 'r1',
            'reference_number': '990', 'policy': 'trout', 'compound_id': 'c1', 'name': 'Example',
            'group': 'natural_active_K1998', 'chemical_analysis': 'U', 'concentration_type': 'A',
            'formulation_code': 'PU', 'exposure_type': 'NR', 'medium': 'FW',
            'exposure_hours': None, 'duration_hours': 96., 'control_type_raw': 'NR',
            'qualifier': '>', 'value': .1, 'reported_context_complete': False,
            'context_gaps': 'exposure_duration_not_reported', **changes}


def source(**changes):
    return {'source_id': 'paper', 'kind': 'primary_fulltext', 'reference_number': '990',
            'sha256': 'a' * 64, **changes}


def decision(field = 'exposure_hours', proposed = 96., original = None, **changes):
    return {'measurement_id': 'm1', 'field': field, 'original': original, 'proposed': proposed,
            'source_id': 'paper', 'status': 'verified_from_primary_source',
            'review_level': 'scientific_review', 'reviewer': 'Fixture reviewer',
            'review_date': '2026-11-12', 'source_locator': 'Methods; specific treatment cell',
            'rationale': 'Fixture source supports this test field', **changes}


def test_recovery_changes_documentation_without_changing_values_bounds_or_native_rows():
    raw = observation()
    decisions = [decision(), decision('exposure_type', 'S', 'NR'),
                 decision('control_type_raw', 'C', 'NR')]
    updated, audit = apply_overlays([raw], decisions, {'paper': source()})
    assert not raw['reported_context_complete'] and raw['exposure_hours'] is None
    assert updated[0]['reported_context_complete']
    assert all(row['applied'] for row in audit)
    assert updated[0]['value'] == .1 and updated[0]['qualifier'] == '>'
    assert json.loads(updated[0]['original_context_json'])['exposure_hours'] is None
    assert summarize_strata(updated, documented_only = True)[0]['exact_record_median_mg_l'] is None


def test_experimental_primary_abstract_is_separate_from_reviewed_adoption():
    d = decision(status = 'provisional', review_level = 'AI_experimental')
    sources = {'paper': source(kind = 'primary_abstract')}
    reviewed, audit = apply_overlays([observation()], [d], sources)
    assert reviewed[0]['exposure_hours'] is None and not audit[0]['applied']
    experimental, audit = apply_overlays([observation()], [d], sources, 'experimental')
    assert experimental[0]['exposure_hours'] == 96 and audit[0]['applied']
    assert experimental[0]['context_overlay_mode'] == 'experimental'
    assert not experimental[0]['reported_context_complete']  # other missing fields survive
    d['status'] = 'verified_from_primary_source'
    with pytest.raises(ValueError, match = 'primary full text'):
        apply_overlays([observation()], [d], sources, 'experimental')


def test_contradictions_are_exposed_without_overriding_native_context():
    raw = observation(exposure_hours = 24.)
    with pytest.raises(ValueError, match = 'contradiction'):
        apply_overlays([raw], [decision(original = 24.)], {'paper': source()}, 'experimental')
    changed, audit = apply_overlays([raw], [decision(original = 24., status = 'contradiction')],
                                    {'paper': source()}, 'experimental')
    assert changed[0]['exposure_hours'] == 24.
    assert audit[0]['native_disagreement'] and not audit[0]['applied']
    with pytest.raises(ValueError, match = 'numeric context'):
        apply_overlays([raw], [decision(original = 24., proposed = float('nan'),
                                       status = 'contradiction')], {'paper': source()})


def test_shared_test_slots_require_complete_consistent_explicit_decisions():
    rows = [observation(), observation(measurement_id = 'm2', source_result_id = 'r2')]
    with pytest.raises(ValueError, match = 'sibling'):
        apply_overlays(rows, [decision()], {'paper': source()})
    with pytest.raises(ValueError, match = 'sibling'):
        apply_overlays(rows, [decision(), decision(measurement_id = 'm2', proposed = 48.)],
                       {'paper': source()})
    changed, _ = apply_overlays(rows, [decision(), decision(measurement_id = 'm2')], {'paper': source()})
    assert [row['exposure_hours'] for row in changed] == [96., 96.]


@pytest.mark.parametrize('changes', [
    {'measurement_id': 'orphan'}, {'field': 'value'}, {'original': 20.},
    {'proposed': float('nan')}, {'proposed': True}, {'proposed': -1},
    {'source_id': 'missing'}, {'reviewer': ''}, {'review_date': '2026-1-1'},
    {'status': 'approved'}, {'review_level': 'automatic'},
])
def test_invalid_or_stale_decisions_fail(changes):
    with pytest.raises(ValueError):
        apply_overlays([observation()], [decision(**changes)], {'paper': source()})


def test_duplicate_source_mismatch_and_secondary_claims_are_rejected():
    with pytest.raises(ValueError, match = 'unique'):
        apply_overlays([observation()], [decision(), decision()], {'paper': source()})
    with pytest.raises(ValueError, match = 'reference'):
        apply_overlays([observation()], [decision()], {'paper': source(reference_number = '80404')})
    changed, audit = apply_overlays([observation()], [decision(status = 'provisional')],
                                    {'paper': source(kind = 'secondary')}, 'experimental')
    assert not audit[0]['applied'] and changed[0]['exposure_hours'] is None


def test_registry_hashes_paths_and_versioned_command_products(tmp_path):
    evidence = tmp_path / 'sources'
    evidence.mkdir()
    paper = evidence / 'paper.txt'
    paper.write_text('Synthetic primary-text fixture, not a real paper')
    record = source(file = paper.name, sha256 = hashlib.sha256(paper.read_bytes()).hexdigest())
    registry = evidence / 'sources.json'
    registry.write_text(json.dumps([record]))
    loaded, _ = load_sources(evidence)
    assert loaded['paper']['sha256'] == record['sha256']
    comparison = tmp_path / 'comparison'
    comparison.mkdir()
    rows = [observation(), observation(measurement_id = 'm2', test_id = 't2', source_result_id = 'r2')]
    write_csv(comparison / 'aquatic_observations.csv', rows, list(rows[0]))
    (comparison / 'manifest.json').write_text(json.dumps({'output_hashes': hashes([
        comparison / 'aquatic_observations.csv'])}))
    overlays = tmp_path / 'overlays.json'
    # A new metadata field only in the second row must survive CSV export.
    overlays.write_text(json.dumps([decision('initial_ph', 7.45, measurement_id = 'm2')]))
    out = tmp_path / 'out'
    manifest = run(comparison, overlays, evidence, out)
    assert manifest['applied_field_decisions'] == 1
    assert manifest['new_rat_admissions'] == 0
    assert (out / 'original_aquatic_observations.csv').read_bytes() == (comparison / 'aquatic_observations.csv').read_bytes()
    assert 'initial_ph' in (out / 'source_adjudicated_observations.csv').read_text().splitlines()[0]
    verify_manifest(out / 'manifest.json')
    with pytest.raises(ValueError, match = 'new output'):
        run(comparison, overlays, evidence, out)
    with pytest.raises(ValueError, match = 'new output'):
        run(comparison, overlays, evidence, comparison / 'nested')
    paper.write_text('Changed bytes')
    with pytest.raises(ValueError, match = 'hash mismatch'):
        load_sources(evidence)
    record['file'] = '../outside.txt'
    (tmp_path / 'outside.txt').write_text('Outside')
    registry.write_text(json.dumps([record]))
    with pytest.raises(ValueError, match = 'inside'):
        load_sources(evidence)
