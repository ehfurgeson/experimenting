from natural_rescreen import endpoint_flags, oral_scores


def test_flags_keep_observations_separate_from_model_agreement():
    rows = [
        {'endpoint': name, 'unit': unit, 'observed': observed,
         'descriptor_score': a, 'morgan_score': b, 'max_training_morgan_tanimoto': similarity}
        for name, unit, observed, a, b, similarity in [
            ('measured_negative', 'binary', 0, .9, .9, .7),
            ('measured_positive', 'binary', 1, .1, .1, .7),
            ('both_positive', 'binary', '', .8, .6, .2),
            ('discordant', 'binary', '', .2, .7, .6),
            ('quantitative', 'mg/L', '', .8, .6, .2),
        ]
    ]
    assert endpoint_flags(rows) == {
        'observed_positive_endpoints': 'measured_positive',
        'both_forests_positive_endpoints': 'both_positive',
        'both_positive_below_point30_similarity': 'both_positive',
        'forest_disagreement_endpoints': 'discordant',
    }


def test_oral_screen_uses_held_scores_and_leaves_unvalidated_training_rows_blank():
    held = {'measured': {'predicted': '1'}}
    scores = oral_scores(['measured', 'added'], {}, {'measured': {}, 'added': {}}, held)
    assert scores == {'measured': (held['measured'], 'scaffold_held_out')}
