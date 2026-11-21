import inspect
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from accepted_screen import (
    admits_exact_catalog_identity,
    argument_parser,
    displayed_ld50_qualifier,
    measured_ld50,
    pareto_front,
    run,
)


def test_default_entry_point_uses_corrected_bundles():
    signature = inspect.signature(run)
    assert signature.parameters['plant_bundle'].default == 'plant-v5'
    assert signature.parameters['plant_models'].default == 'plant-models-v5'
    assert signature.parameters['toxicity_bundle'].default == 'toxicity-v2'
    assert signature.parameters['toxicity_models'].default == 'toxicity-models-v2'
    assert signature.parameters['uncertainty_bundle'].default == 'uncertainty-v2'
    args = argument_parser().parse_args(['--accepted', 'a', '--sprint', 'b', '--output', 'c'])
    assert args.plant_bundle == 'plant-v5'
    assert args.plant_models == 'plant-models-v5'
    assert args.toxicity_bundle == 'toxicity-v2'
    assert args.toxicity_models == 'toxicity-models-v2'
    assert args.uncertainty_bundle == 'uncertainty-v2'


def test_provider_key_conflict_is_not_an_exact_catalog_hit():
    assert admits_exact_catalog_identity('valid')
    assert not admits_exact_catalog_identity('provider_key_conflict')
    assert not admits_exact_catalog_identity('invalid_or_missing_structure')


def test_measured_ld50_uses_a_connectivity_sibling_and_labels_a_limit():
    unspecified = 'DTGKSKDOIYIVQL-UHFFFAOYSA-N'
    isoborneol = {'full_key': 'DTGKSKDOIYIVQL-MRTMQBJTSA-N', 'connectivity': 'DTGKSKDOIYIVQL',
                  'target_log10_mg_kg': '3.716003343634799', 'deduplicated_values': '1',
                  'new_source_records': '2', 'source_record_ids': '["other"]'}
    endo = {'full_key': 'DTGKSKDOIYIVQL-QXFUBDJGSA-N', 'connectivity': 'DTGKSKDOIYIVQL',
            'target_log10_mg_kg': '3.7634279935629373', 'deduplicated_values': '1',
            'new_source_records': '2', 'source_record_ids': '["other"]'}
    by_connectivity = {'DTGKSKDOIYIVQL': [isoborneol, endo]}
    rows, scope = measured_ld50(unspecified, by_connectivity)
    assert scope == 'same_connectivity'
    assert {r['full_key'] for r in rows} == {isoborneol['full_key'], endo['full_key']}
    own, own_scope = measured_ld50(isoborneol['full_key'], by_connectivity)
    assert own_scope == 'same_full_key' and own[0]['target_log10_mg_kg'].startswith('3.716')
    limit = {'source_record_ids': '["acute_oral_1852"]', 'deduplicated_values': '1',
             'new_source_records': '3'}
    assert displayed_ld50_qualifier(limit) == '>'
    assert displayed_ld50_qualifier(isoborneol) == '='


def test_pareto_front_preserves_ties_and_different_tradeoffs():
    assert pareto_front([[1, 3], [2, 2], [3, 1], [1, 1], [2, 2]]) == [True, True, True, False, True]
    assert pareto_front([[1, 1], [1, 2]]) == [False, True]
    with pytest.raises(ValueError, match = 'finite'):
        pareto_front([[float('nan'), 1]])
