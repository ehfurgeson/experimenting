import polars as pl

from joint_catalog_screen import screening_flags


def test_joint_flags_distinguish_observed_outcomes_and_missing_model_scores():
    source = pl.DataFrame({
        'ice_oral_bin': [2, None, 2, None], 'pooled_high_response_score': [0.5, 0.8, 0.8, 0.8],
        'ice_reviewed_lower_bound_mg_kg': [None, None, 32_000, None],
        'oral_A__high': [0.6, 0.6, 0.6, 0.6], 'oral_B__high': [0.6, 0.6, 0.6, 0.6],
        'oral_augmented__high': [0.6, None, 0.6, 0.6],
        'radish_root_length_100um__inhibition_pct': [40., 20., 20., 20.],
        'cress_root_length_100um__inhibition_pct': [20., 20., 20., 20.],
        'assay__observed': [0, None, 1, None], 'assay__score': [0.8, 0.8, 0.1, 0.1],
    })
    results = source.select(screening_flags([{'endpoint': 'assay', 'task': 'binary'}]))
    assert results['measured_oral_high'].to_list() == [True, False, False, False]
    assert results['joint_model_ab'].to_list() == [False, True, False, True]
    assert results['joint_model_all_three'].to_list() == [False, False, False, True]
    assert results['root_inhibition_ge_40_at_100um'].to_list() == [True, False, False, False]
    assert results['observed_positive_binary_endpoints'].to_list() == [0, 0, 1, 0]
    assert results['unmeasured_binary_model_flags'].to_list() == [0, 1, 0, 0]
