"""Identity approval cannot change scientific fields, pool contexts or impute bounds."""
import json
import sys
from pathlib import Path

import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ecotox_comparison import (
    documented_context,
    group_for,
    identity_only_accounting,
    overlap_scenarios,
    rat_review,
    summarize_strata,
)


def observation(**changes):
    return {'measurement_id':'slot1','source_result_id':'result1','test_id':'test1',
            'reference_number':'ref1','policy':'trout','compound_id':'compound1','name':'Example',
            'group':'natural_activity_unknown','chemical_analysis':'U','concentration_type':'A',
            'formulation_code':'PU','exposure_type':'S','medium':'FW','exposure_hours':96.,
            'duration_hours':96.,'qualifier':'=','value':10.,'reported_context_complete':True,
            **changes}


def test_native_and_measurement_grains_unchanged_after_identity_attachment():
    native = pl.DataFrame({'source_result_id':['result1'],'result_json':['raw source']})
    before = pl.DataFrame({'measurement_id':['slot1'],'value':[10.],'compound_id':[None],
                           'identity_status':['candidate']})
    after = before.with_columns(pl.lit('compound1').alias('compound_id'),pl.lit('approved').alias('identity_status'))
    assert all(r['scientific_fields_unchanged'] for r in identity_only_accounting(native,native,before,after))
    with pytest.raises(ValueError,match = 'Scientific measurements changed'):
        identity_only_accounting(native,native,before,after.with_columns(pl.lit(20.).alias('value')))
    with pytest.raises(ValueError,match = 'Native source results changed'):
        identity_only_accounting(native,native.with_columns(pl.lit('changed').alias('result_json')),before,after)
    with pytest.raises(ValueError,match = 'explicitly approved'):
        identity_only_accounting(native,native,before,before)


def test_summaries_keep_bounds_and_contexts_distinct_and_do_not_collapse_equal_results():
    rows = [observation(),observation(measurement_id='slot2',source_result_id='result2',qualifier='>',value=100.),
            observation(measurement_id='slot3',source_result_id='result3',chemical_analysis='M',value=1.),
            observation(measurement_id='slot4',source_result_id='result4',formulation_code='AI',value=2.),
            observation(measurement_id='slot5',source_result_id='result5',exposure_hours=48.,value=3.),
            observation(measurement_id='slot6',source_result_id='result6',value=10.)]
    summaries = summarize_strata(rows)
    assert len(summaries) == 4
    unmeasured_pure = next(r for r in summaries if r['chemical_analysis']=='U' and r['formulation_code']=='PU' and r['exposure_hours']==96.)
    assert unmeasured_pure['slots'] == unmeasured_pure['distinct_results'] == 3
    assert unmeasured_pure['exact_slots'] == 2 and unmeasured_pure['bounded_or_range_slots'] == 1
    assert unmeasured_pure['exact_record_median_mg_l'] == 10.
    only_bound = summarize_strata([rows[1]])[0]
    assert only_bound['exact_record_median_mg_l'] is None
    assert not summarize_strata([rows[0]],excluded={'slot1'})


def test_missing_context_remains_reviewable_and_sensitivity_does_not_impute_it():
    row = observation(exposure_hours=None)
    gaps = documented_context(row,{'control_type':'NR'})
    assert set(gaps) == {'exposure_duration_not_reported','control_type_not_reported'}
    assert 'exposure_and_observation_duration_differ' in documented_context(observation(exposure_hours=48.),{'control_type':'C'})
    row['reported_context_complete'] = False
    assert len(summarize_strata([row])) == 1
    assert summarize_strata([row],documented_only=True) == []


def test_identity_does_not_establish_natural_origin_or_plant_inactivity():
    ledger = {'compound1':{'inchikey':'key'}}
    assert group_for('compound1',ledger,{'key':{'activity':'unknown'}},{}) == 'natural_activity_unknown'
    assert group_for('compound1',ledger,{'key':{'activity':'active'}},{}) == 'natural_active_K1998'
    assert group_for('compound1',ledger,{}, {'compound1':{'chemical_group':'herbicide'}}) == 'selected_herbicide_comparator'
    assert group_for('compound1',ledger,{}, {'compound1':{'chemical_group':'natural_product'}}) == 'unreviewed_natural_product_selection'
    assert group_for('compound1',ledger,{}, {}) == 'unreviewed_source_chemical'


def test_rat_identity_approval_does_not_solve_unit_or_acute_context():
    row = observation(source_chemical_id='ECOTOX:chemical:50',species='rattus norvegicus',
        slot=1,exposure_type='DT',unit_raw='g/kg bdwt',unit_standardized=None,parse_status='review',
        effect_code='MOR',measurement_code='MORT')
    source = {'test_json':json.dumps({'test_type':'NC'}),
              'result_json':json.dumps({'conc1_mean':'4.44'}), 'reference_number':'r1',
              'reference_json':json.dumps({'title':'An acute study title is not context approval'})}
    result = rat_review(row,source)
    assert result['raw_value'] == '4.44' and result['unit_raw'] == 'g/kg bdwt'
    assert 'acute_test_type_not_explicit' in result['reasons']
    assert 'not_explicit_gavage_or_oral_capsule' in result['reasons']
    assert 'not_added_to_historical_baseline' in result['status']


def test_adopted_duplicate_queue_roundtrip_changes_only_reviewed_summaries(tmp_path):
    from expansion_toxicity import adopt_duplicate_decisions
    from review_adoption import read_csv
    from screen import write_csv

    queue = [{'pair_id': 'EPA:a|slot1', 'left_id': 'EPA:a', 'right_id': 'slot1',
              'identity_link_status': 'approved', 'decision': 'unreviewed',
              'retain_id': '', 'reviewer': '', 'review_date': '', 'decision_reference': ''},
             {'pair_id': 'EPA:b|slot2', 'left_id': 'EPA:b', 'right_id': 'slot2',
              'identity_link_status': 'approved', 'decision': 'unresolved',
              'retain_id': '', 'reviewer': '', 'review_date': '', 'decision_reference': ''}]
    decision = {'pair_id': 'EPA:a|slot1', 'decision': 'same_observation', 'retain_id': 'EPA:a',
                'reviewer': 'Fixture reviewer', 'review_date': '2026-11-12',
                'decision_reference': 'Fixture paper table/result'}
    adopted = adopt_duplicate_decisions(queue, [decision])
    assert queue[0]['decision'] == 'unreviewed'  # never mutate frozen source queues
    path = tmp_path / 'study_overlap_review.csv'
    write_csv(path, adopted, list(adopted[0]))
    rows = [observation(), observation(measurement_id = 'slot2', value = 30.)]
    strata, sensitivity, excluded = overlap_scenarios(rows, read_csv(path), ['trout'])
    assert excluded == {'slot1'}
    counts = {r['scenario']: r['slots'] for r in sensitivity}
    assert counts == {'all_core_policy_admitted': 2, 'reviewed_duplicate_decisions': 1,
                      'exclude_unresolved_overlap_candidates': 0, 'reported_context_only': 1,
                      'reported_context_exclude_overlap': 0}
    reviewed = next(r for r in strata if r['scenario'] == 'reviewed_duplicate_decisions')
    assert reviewed['exact_record_median_mg_l'] == 30.
    assert rows[0]['measurement_id'] == 'slot1'  # observation archive remains intact
    adopted[0]['reviewer'] = ''
    with pytest.raises(ValueError, match = 'signed'):
        overlap_scenarios(rows, adopted, ['trout'])


def test_distinct_observation_decision_resolves_pending_without_dropping():
    queue = [{'pair_id': 'EPA:a|slot1', 'left_id': 'EPA:a', 'right_id': 'slot1',
              'identity_link_status': 'approved', 'decision': 'different_observation',
              'reviewer': 'Fixture reviewer', 'review_date': '2026-11-12',
              'decision_reference': 'Different primary treatments'}]
    _, sensitivity, excluded = overlap_scenarios([observation()], queue, ['trout'])
    assert not excluded
    assert all(r['slots'] == 1 for r in sensitivity)
