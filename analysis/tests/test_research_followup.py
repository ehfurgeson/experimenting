import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence_release import structure
from research_followup import (
    GENERATOR,
    analogue_queue,
    assert_partition,
    evidence_band,
    paired_bootstrap,
    representations,
)


def test_chemistry_captures_halogens_and_rejects_structure_key_conflicts():
    row = structure('CC(Cl)F')
    matrix, _ = representations([row])
    assert matrix['chemistry'][0, 8:12].tolist() == [1, 1, 0, 0]
    assert matrix['morgan'].shape == (1, 2048)
    with pytest.raises(ValueError, match = 'conflicting'):
        representations([{**row, 'full_key': 'wrong'}])


def test_holdouts_prohibit_leakage_on_the_declared_axis():
    rows = [{'reference_id': 'a'}, {'reference_id': 'a'}]
    with pytest.raises(ValueError, match = 'Reference'):
        assert_partition(rows, [0], [1], 'publication', np.array(['a', 'b']))
    with pytest.raises(ValueError, match = 'Chemical'):
        assert_partition(rows, [0], [1], 'chemical_group', np.array(['a', 'a']))


def test_paired_bootstrap_identical_models_have_zero_difference():
    result = paired_bootstrap(np.array([0, 1, 1, 0]), np.array([0, 0, 1, 0]),
        np.array([0, 0, 1, 0]), np.array(['a', 'a', 'b', 'b']), np.ones(4), [0, 1], repeats = 40)
    assert result['difference'] == result['conditional_lower95'] == result['conditional_upper95'] == 0


def test_analogue_search_excludes_same_connectivity_and_lower_ld50():
    from rdkit import Chem
    query = structure('CCO')
    pool = [structure(s) for s in ['CCO', 'CCCO', 'CCCCO']]
    for r, dose in zip(pool, [4., 2., 4.], strict = True):
        r['target_log10_mg_kg'] = dose
    fps = [GENERATOR.GetFingerprint(Chem.MolFromSmiles(r['smiles'])) for r in pool]
    results = analogue_queue([{'original_structure': query['smiles'],
        'full_inchikey': query['full_key'], 'compound_id': 'q'}], pool, fps)
    assert [r['analogue_full_key'] for r in results] == [pool[2]['full_key']]


def test_unknown_and_conflicting_plant_outcomes_never_become_benign():
    assert evidence_band([]) == 'no_plant_observations'
    assert evidence_band([0, 1]) == 'mixed_context_response'
    assert evidence_band([0, 0]) == 'tested_low_response_only'
