import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from accepted_plant import ecotox_basis, ecotox_response, inhibition_label
from accepted_plant_models import chemical_weights, partitions


def test_accepted_missing_and_cross_threshold_responses_remain_unknown():
    assert inhibition_label(None) is None
    assert inhibition_label('nan') is None
    assert inhibition_label(30) is None
    assert inhibition_label(40, '>') == 1
    assert inhibition_label(40, '<') is None
    assert inhibition_label(20, '<') == 0
    assert inhibition_label(20, '>') is None
    assert inhibition_label(-60) == 0


def test_direction_and_endpoint_do_not_invent_numeric_no_effect():
    row = {'observed_response': 'NR', 'effect_direction': 'NEF', 'qualifier': '',
           'response_basis': 'percent_change'}
    assert ecotox_response(row) == (None, None)
    assert ecotox_response(row | {'observed_response': '118', 'effect_direction': 'INC'}) == (-118, 0)
    assert ecotox_response(row | {'observed_response': '80', 'effect_direction': 'DEC'}) == (80, 1)
    assert ecotox_response(row | {'observed_response': '80', 'effect_direction': 'NR'}) == (None, None)


def test_percent_control_is_converted_before_response_classification():
    row = {'observed_response': '70', 'effect_direction': 'DEC', 'qualifier': '',
           'response_basis': 'percent_control'}
    assert ecotox_response(row) == (30, None)
    assert ecotox_response(row | {'observed_response': '95'}) == (5, 0)
    assert ecotox_response(row | {'observed_response': '40'}) == (60, 1)
    assert ecotox_response(row | {'observed_response': '120', 'effect_direction': 'INC'}) == (-20, 0)
    assert ecotox_response(row | {'observed_response': '80', 'qualifier': '>='}) == (20, 0)
    assert ecotox_response(row | {'observed_response': '60', 'qualifier': '<='}) == (40, 1)
    assert ecotox_response(row | {'response_basis': 'unknown'}) == (None, None)


@pytest.mark.parametrize('comment,basis', [
    ('PERCENT OF CONTROL', 'percent_control'), ('OF CONTROL, FROM GRAPH', 'percent_control'),
    ('PERCENT CONTROL', 'percent_control'), ('PERCENTAGE OF CONTROL', 'percent_control'),
    ('PERCENT REDUCTION', 'percent_change'), ('PERCENT INCREASE OVER CONTROL', 'percent_change'),
    ('FROM GRAPH', 'unknown'), ('', 'unknown'),
])
def test_response_scale_requires_explicit_native_documentation(comment, basis):
    assert ecotox_basis({'effect_pct_comments': comment}) == basis


def test_cl20_increase_over_control_is_low_not_high_inhibition():
    """Rocheleau et al. 2008: CL-20 had no adverse effect on ryegrass growth."""
    comment = 'OF CONTROL, FROM GRAPH, SIGNIFICANT INCREASE OVER CONTROL'
    assert ecotox_basis({'effect_pct_comments': comment}) == 'percent_control'
    row = {'observed_response': '20', 'effect_direction': 'INC', 'qualifier': '~',
           'response_basis': 'percent_control', 'effect_pct_comments': comment}
    assert ecotox_response(row) == (-20, 0)
    # 8% of control is 92% inhibition. Direction INC does not override a bare scale comment.
    lemna = row | {'observed_response': '8', 'qualifier': '',
                   'effect_pct_comments': 'PERCENT OF CONTROL'}
    assert ecotox_response(lemna) == (92, 1)
    documented_decrease = row | {'observed_response': '40', 'qualifier': '',
                                 'effect_pct_comments': 'PERCENT OF CONTROL, DECREASE'}
    assert ecotox_response(documented_decrease) == (60, 1)
    # Extra wording that is neither increase nor a bare scale stays unlabeled.
    ambiguous = row | {'observed_response': '20', 'qualifier': '',
                       'effect_pct_comments': 'OF CONTROL, FROM GRAPH'}
    assert ecotox_response(ambiguous) == (None, None)


def test_training_weights_give_equal_total_mass_to_repeated_structures():
    rows = [{'full_key': 'a'}, {'full_key': 'a'}, {'full_key': 'b'}]
    w = chemical_weights(rows)
    assert w[0] + w[1] == pytest.approx(w[2])
    assert w.sum() == pytest.approx(3)


def test_publication_and_chemical_splits_protect_the_declared_axis():
    rows = [{'label': (ref + compound) % 2, 'reference_id': f'R{ref}',
             'full_key': f'K{compound}', 'connectivity': f'C{compound}', 'scaffold': f'S{compound}'}
            for ref in range(6) for compound in range(6)]
    for protocol, field in [('publication', 'reference_id'), ('chemical_group', 'full_key')]:
        splits = partitions(rows, protocol)
        assert len(splits) == 5
        for train, test in splits:
            assert not {rows[i][field] for i in train} & {rows[i][field] for i in test}
