import pytest

from parthenium_panel import compare_cell


def test_reported_and_recomputed_bands_must_agree():
    assert compare_cell('2.74 ± 0.035 aA(0)', '1.49 ± 0.015 bG(45.62)')[
        'context_response'] == 'high'
    assert compare_cell('94.44 ± 1.92 aA(0)', '92.21 ± 5.09 aA(2.36)')[
        'context_response'] == 'low'
    assert compare_cell('94.44 ± 1.92 aA(0)', '93.33 ± 3.84 aA(2.35)')[
        'context_response'] == 'review_discrepancy'
    assert compare_cell('1.00 aA(0)', '0.80 aA(20.20)')[
        'context_response'] == 'review_discrepancy'


def test_zero_treatment_and_missing_sem_are_preserved():
    point = compare_cell('2.74 ± 0.035 aA(0)', '0.00eG(100)')
    assert point['treated_mean'] == 0
    assert point['treated_sem'] == ''
    assert point['reported_inhibition_percent'] == point['derived_inhibition_percent'] == 100
    with pytest.raises(ValueError, match='Invalid control'):
        compare_cell('0.00 aA(0)', '0.00 aA(0)')
