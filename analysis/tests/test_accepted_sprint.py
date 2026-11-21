import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from accepted_sprint import aggregate, bound_class, log_median, mass_dose
from evidence_release import ld50_bin, structure


def test_acceptance_does_not_convert_bounds_or_incompatible_units_to_points():
    assert mass_dose('2', 'g/Kg') == 2000
    assert mass_dose('2', 'mg.kg-1') == 2
    assert mass_dose('nan', 'mg/kg') is None
    assert mass_dose('2', 'mL/kg') is None
    assert mass_dose('2', 'mg/kg-day') is None
    assert bound_class(3400, '>') == 2
    assert bound_class(3400, '>=') is None
    assert bound_class(1080, '<=') == 0
    assert bound_class(2000, '>') is None


def test_frozen_targets_remain_fixed_and_assumptions_define_separate_cohorts():
    eth = structure('CCO')
    met = structure('CO')
    identities = {r['full_key']: r for r in [eth, met]}
    base = {eth['full_key']: eth | {'target_log10_mg_kg': 3., 'ld50_bin': 0}}
    common = {'eligible': True, 'source': 'NPASS', 'source_asserted': False,
              'assumptions': 'oral_route_assumed', 'class_from_interval': 2}
    obs = [common | {'full_key': eth['full_key'], 'value_mg_kg': 10000., 'qualifier': '='},
           common | {'full_key': met['full_key'], 'value_mg_kg': 5000., 'qualifier': '>'}]
    exact, classes, conflicts = aggregate(base, obs, identities, 'all_accepted')
    assert len(exact) == 1 and exact[0]['target_log10_mg_kg'] == 3.
    assert len(classes) == 2
    censored = next(r for r in classes if r['full_key'] == met['full_key'])
    assert censored['ld50_bin'] == 2 and censored['target_log10_mg_kg'] is None
    assert conflicts[0]['status'] == 'exact_vs_source_class_disagreement'
    assert len(aggregate(base, obs, identities, 'source_asserted')[1]) == 1


def test_repeated_source_doses_do_not_reweight_new_structure_medians():
    met = structure('CO')
    common = {'eligible': True, 'source': 'ToxValDB', 'source_asserted': True,
              'assumptions': '', 'class_from_interval': None, 'full_key': met['full_key'],
              'qualifier': '=', 'reference': 'study'}
    obs = [common | {'value_mg_kg': v} for v in [10., 10., 10., 1000.]]
    exact, _, conflicts = aggregate({}, obs, {met['full_key']: met}, 'source_asserted')
    assert conflicts == []
    assert exact[0]['target_log10_mg_kg'] == pytest.approx(2)
    assert round(10 ** exact[0]['target_log10_mg_kg']) == 100


def test_log_median_of_280_and_10000_stays_in_the_middle_tertile():
    met = structure('CO')
    common = {'eligible': True, 'source': 'ToxValDB', 'source_asserted': True,
              'assumptions': '', 'class_from_interval': None, 'full_key': met['full_key'],
              'qualifier': '=', 'reference': 'study'}
    obs = [common | {'value_mg_kg': v} for v in [280., 10000.]]
    exact, _, _ = aggregate({}, obs, {met['full_key']: met}, 'source_asserted')
    target_log = log_median([280., 10000.])
    assert exact[0]['target_log10_mg_kg'] == pytest.approx(target_log)
    assert 10 ** target_log == pytest.approx(1673, rel = 0.01)
    assert exact[0]['ld50_bin'] == 1
    assert ld50_bin(math.log10(5140)) == 2


def test_wide_dose_span_withholds_the_exact_target_and_frozen_a_stays_fixed():
    eth, met = structure('CCO'), structure('CO')
    identities = {r['full_key']: r for r in [eth, met]}
    base = {eth['full_key']: eth | {'target_log10_mg_kg': 3., 'ld50_bin': 1}}
    common = {'eligible': True, 'source': 'ToxValDB', 'source_asserted': True,
              'assumptions': '', 'class_from_interval': None, 'qualifier': '=', 'reference': 'study'}
    obs = [common | {'full_key': eth['full_key'], 'value_mg_kg': v} for v in [1., 5000.]]
    obs += [common | {'full_key': met['full_key'], 'value_mg_kg': v} for v in [1., 5000.]]
    exact, classes, conflicts = aggregate(base, obs, identities, 'all_accepted')
    frozen = next(r for r in exact if r['full_key'] == eth['full_key'])
    assert frozen['target_log10_mg_kg'] == 3. and frozen['ld50_bin'] == 1
    assert all(r['full_key'] != met['full_key'] for r in exact)
    assert all(r['full_key'] != met['full_key'] for r in classes)
    withheld = next(r for r in conflicts if r['full_key'] == met['full_key'])
    assert withheld['status'] == 'wide_exact_dose_span'


def test_lone_assumed_implausible_dose_is_withheld_without_a_chemical_name():
    met = structure('CO')
    assumed = {'eligible': True, 'source': 'ToxValDB', 'source_asserted': False,
               'assumptions': 'experimental_status_assumed', 'class_from_interval': 0,
               'full_key': met['full_key'], 'qualifier': '=', 'reference': 'secondary 1958',
               'value_mg_kg': 0.012}
    exact, _, conflicts = aggregate({}, [assumed], {met['full_key']: met}, 'all_accepted')
    assert exact == []
    assert conflicts[0]['status'] == 'single_implausible_assumed_dose'
    asserted = assumed | {'source_asserted': True, 'assumptions': ''}
    kept, _, kept_conflicts = aggregate({}, [asserted], {met['full_key']: met}, 'source_asserted')
    assert kept_conflicts == []
    assert kept[0]['target_log10_mg_kg'] == pytest.approx(math.log10(0.012))
