"""Explicit identity signoff is bound to source pairs, not other scientific decisions."""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ecotox_approved import approve_pairs, canonical_index


def declaration():
    return {'approval_id': 'human-review', 'reviewer': 'Research lead', 'review_date': '2026-11-11',
            'statement': 'All selected source identity mappings reviewed and approved.',
            'scope': 'all_selected_ecotox_identity_mappings', 'snapshot_sha256': 'snapshot'}


def candidates():
    return [{'source_chemical_id': 'ECOTOX:chemical:50', 'compound_id': '', 'status': 'candidate',
             'match_type': 'dtxsid_only', 'candidate_compound_ids': 'KNOWN:1'}]


def canonical():
    return {'KNOWN:1': {'compound_id': 'KNOWN:1', 'name': 'Example',
                       'canonical_smiles': 'CCO', 'inchikey': 'LFQSCWFLJHTTHZ-UHFFFAOYSA-N',
                       'structure_model_status': 'valid'}}


def test_identity_approval_preserves_original_candidates_and_signoff_basis():
    rows = candidates();before = copy.deepcopy(rows)
    decisions, ledger = approve_pairs(rows, ['ECOTOX:chemical:50'], canonical(), declaration(), 'snapshot')
    assert rows == before
    assert decisions[0]['compound_id'] == 'KNOWN:1'
    assert decisions[0]['status'] == 'approved' and decisions[0]['match_type'] == 'exact_structure'
    assert ledger[0]['previous_status'] == 'candidate'
    assert ledger[0]['evidence_basis'].startswith('User assertion')
    assert 'activity_target' not in decisions[0]


@pytest.mark.parametrize('change', ['snapshot', 'scope', 'reviewer', 'date', 'ambiguous', 'missing', 'conflict', 'duplicate', 'wrong_id'])
def test_approval_rejects_unbound_incomplete_or_conflicting_mappings(change):
    rows, d, sources = candidates(), declaration(), ['ECOTOX:chemical:50']
    if change == 'snapshot': d['snapshot_sha256'] = 'another'
    elif change == 'scope': d['scope'] = 'biological_labels'
    elif change == 'reviewer': d['reviewer'] = ''
    elif change == 'date': d['review_date'] = 'not-a-date'
    elif change == 'ambiguous': rows[0]['candidate_compound_ids'] = 'KNOWN:1;KNOWN:2'
    elif change == 'missing': rows[0]['candidate_compound_ids'] = ''
    elif change == 'conflict': rows[0]['status'] = 'conflict'
    elif change == 'duplicate': rows += copy.deepcopy(rows)
    else: rows[0]['compound_id'] = 'OTHER:1'
    with pytest.raises(ValueError):
        approve_pairs(rows, sources, canonical(), d, 'snapshot')


def test_multicomponent_model_exclusion_is_distinct_from_approved_identity():
    data = canonical_index([{'compound_id': 'salt', 'input_smiles': '[Na+].CC(=O)[O-]',
                             'inchikey': 'VMHLLURERBWHNL-UHFFFAOYSA-M',
                             'structure_status': 'multicomponent'}], [])
    assert data['salt']['structure_model_status'] == 'multicomponent'
    rows = candidates();rows[0]['candidate_compound_ids'] = 'salt'
    assert approve_pairs(rows,['ECOTOX:chemical:50'],data,declaration(),'snapshot')[0][0]['compound_id'] == 'salt'
    with pytest.raises(ValueError, match = 'SMILES/key disagreement'):
        canonical_index([{'compound_id':'bad','input_smiles':'CCO','inchikey':'WRONG'}], [])
