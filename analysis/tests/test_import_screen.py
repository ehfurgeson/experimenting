from import_screen import high_ld50_support, point_response, structure_profile


def test_control_response_normalizes_only_explicit_dose_points():
    row = {'endpoint': 'NR', 'qualifier': '=', 'concentration': '10',
           'concentration_unit': 'mg/L', 'control_context': 'C',
           'observed_response': '45', 'effect_direction': 'DEC'}
    result = {'effect_pct_comments': '% of control', 'conc1_mean_op': '='}
    assert point_response(row, result) == ('percent_control', 55, 1)
    assert point_response(row | {'endpoint': 'NOEC'}, result) is None
    assert point_response(row, result | {'conc1_mean_op': '>'}) is None
    assert point_response(row | {'control_context': 'NR'}, result) is None


def test_structure_profile_counts_presence_per_structure():
    rows = [
        {'smiles': 'FC(F)Cl', 'molecular_weight': '86', 'tpsa': '0'},
        {'smiles': 'CO', 'molecular_weight': '32', 'tpsa': '20'},
    ]
    profile = structure_profile('reference', rows)
    assert profile['with_F'] == profile['with_Cl'] == profile['with_any'] == 1
    assert profile['structures'] == 2
    assert profile['median_tpsa'] == 10


def test_high_ld50_support_flags_disagreement_without_using_bounds_as_points():
    observations = [
        {'full_key': key, 'status': status, 'value_mg_kg': str(value), 'reference': 'source'}
        for key, status, value in (
            ('conflict', 'exact', 3400), ('conflict', 'exact', 9000),
            ('single', 'exact', 3500), ('single', 'censored', 500),
            ('other', 'exact', 9000),
        )
    ]
    support = high_ld50_support({'conflict', 'single'}, observations)
    assert support['conflict']['exact_report_bins'] == 'medium;high'
    assert support['single']['exact_report_bins'] == 'high'
    assert support['single']['distinct_exact_reference_strings'] == 1
    assert 'other' not in support
