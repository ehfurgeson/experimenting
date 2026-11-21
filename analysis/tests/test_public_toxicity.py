import evidence_release


def test_ice_compounds_keep_reference_votes_and_exclude_censored_targets():
    identity = evidence_release.structure('CCO')
    key = identity['full_key']
    base = {'full_key': key, 'reference': 'study1', 'sex': 'Male', 'status': 'exact'}
    observations = [
        {**base, 'source_record_id': 'a', 'value_mg_kg': 1000},
        {**base, 'source_record_id': 'b', 'value_mg_kg': 1000},
        {**base, 'source_record_id': 'c', 'reference': 'study2', 'value_mg_kg': 2000},
        {**base, 'source_record_id': 'd', 'status': 'censored', 'value_mg_kg': 50},
    ]
    [target] = evidence_release.ice_compounds(observations, {key: identity})
    assert target['ld50_bin'] == 1
    assert target['deduplicated_values'] == 2
    assert target['source_record_ids'] == '["a", "b", "c"]'
