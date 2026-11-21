import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sprint_chembl_review import PODOLACTONE_DOI, holds, source_bound


def test_reported_inequality_bounds_are_not_exact_responses():
    raw = {'standard_type': 'Inhibition', 'standard_units': '%',
           'standard_value': '40', 'standard_relation': '>'}
    assert source_bound(raw) == 'reported_inhibition_over_40_percent'
    assert source_bound(raw | {'standard_relation': '='}) == 'other_reported_response'
    assert source_bound(raw | {'standard_value': '20', 'standard_relation': '<'}) == (
        'reported_inhibition_under_20_percent')
    assert source_bound(raw | {'standard_value': None}) == 'unknown'
    assert source_bound(raw | {'standard_units': 'mm'}) == 'not_compatible_inhibition_bound'


def test_formulated_positive_control_is_held_even_with_valid_single_chemical_identity():
    result = holds({'molecule_chembl_id': 'CHEMBL1896787'}, PODOLACTONE_DOI)
    assert 'Logran_formulated_control_not_single_ingredient' in result
    assert 'qualitative_summary_not_resolved_to_single_dose' in result
    ordinary = holds({'molecule_chembl_id': 'CHEMBL2269810'}, PODOLACTONE_DOI)
    assert 'Logran_formulated_control_not_single_ingredient' not in ordinary
    assert 'qualitative_summary_not_resolved_to_single_dose' in ordinary
