import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from plant_evidence_experiments import (
    NUMERIC,
    chembl_rows,
    curve_analysis,
    dose_in_description,
    duration_hours,
    exposure_features,
    model,
)


def test_dose_ranges_and_bounds_do_not_become_scalar_exposures():
    assert dose_in_description('inhibition at 1 mM after 7 days') == ('1', 'mM')
    for description in ['at 1 to 10 uM', 'at 1 mM or 10 mM', 'at > 10 uM', 'up to 100 uM']:
        assert dose_in_description(description) == ('', '')


def test_exposure_conversion_keeps_incompatible_dose_axes_separate():
    molar = exposure_features(10, 'uM', 200)
    mass = exposure_features(2, 'mg/L', 200)
    assert molar['log_molar'] == pytest.approx(mass['log_molar'])
    assert exposure_features(1000, 'g/ha', 200)['log_kg_ha'] == 0
    assert np.isnan(exposure_features(2, 'ppm', 200)['log_molar'])
    assert exposure_features(2, 'ppm', 200)['dose_family'] == 'reported_ppm_unresolved_basis'
    assert np.isnan(duration_hours(1, 'mo'))
    assert duration_hours(1, 'd') == duration_hours(24, 'h')


def test_curves_score_only_interior_doses_and_retain_unreached_crossings():
    rows = [{'compound_id': 'a', 'species': 'x', 'endpoint': 'root', 'dose_unit': 'uM',
             'concentration': dose, 'derived_inhibition_percent': response}
            for dose, response in [(1, 0), (10, 10), (100, 20)]]
    summaries, predictions = curve_analysis(rows)
    assert summaries[0]['ec50_status'] == 'above_tested_range_under_monotone_assumption'
    assert summaries[0]['descriptive_50pct_crossing'] == ''
    assert {r['dose'] for r in predictions} == {10}
    assert [r['prediction'] for r in predictions] == pytest.approx([10] * 3)


def test_context_encoder_accepts_unseen_species_without_looking_at_test_set():
    rows = np.array([[float(i)] * len(NUMERIC) + ['s1', 'root', 'molar', 'study1'] for i in range(6)], object)
    fitted = model('chemistry_context_study').fit(rows, [0, 0, 0, 1, 1, 1])
    test = rows[:1].copy()
    test[0, -4:] = ['unseen_species', 'root', 'molar', 'unseen_study']
    probability = fitted.predict_proba(test)
    assert probability.shape == (1, 2)
    assert np.isfinite(probability).all()


def test_complete_series_does_not_turn_unknown_scale_or_missing_values_into_negatives(tmp_path):
    doc = {'document_chembl_id': 'CHEMBL1', 'doi': '10.example/source', 'title': 'Example'}
    (tmp_path / 'CHEMBL1-document.json').write_text(json.dumps(doc))
    base = {'activity_id': 1, 'target_organism': 'Lactuca sativa', 'standard_value': '0',
        'assay_description': 'Inhibition of root length at 10 uM after 7 days',
        'canonical_smiles': 'CCO', 'standard_type': 'Inhibition', 'standard_units': '%',
        'standard_relation': '=', 'data_validity_comment': None, 'assay_chembl_id': 'CHEMBL2'}
    rows = [base, {**base, 'activity_id': 2, 'standard_type': 'Activity'},
            {**base, 'activity_id': 3, 'standard_value': None}]
    page = {'page_meta': {'total_count': 3}, 'activities': rows}
    path = tmp_path / 'CHEMBL1-activities-0.json'
    path.write_text(json.dumps(page))
    observations, audit, _, _ = chembl_rows(tmp_path)
    assert len(observations) == 1 and observations[0]['label'] == 0
    assert {r['status'] for r in audit} == {'experimental_database_response',
        'missing_numeric_response', 'response_basis_or_endpoint_unresolved'}
    page['page_meta']['total_count'] = 4
    path.write_text(json.dumps(page))
    with pytest.raises(ValueError, match = 'Incomplete'):
        chembl_rows(tmp_path)
