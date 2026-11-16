"""Critical identity conflicts override historical scenarios without creating model labels."""
import copy
import json
import sys
from pathlib import Path

import pytest
from rdkit import Chem

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verification_release as release
from structure import structure_features

SMILES = 'COc1cc(OC)nc(Oc2cccc3c(C)nn(C4CC4)c(=O)c23)n1'


def example():
    data = {'manifest': {'training_use_approved': False}, 'matrix': [], 'labels': [],
            'log': [], 'crosswalk': [], 'conditional': [], 'references': []}
    features = []
    for i, (cid, smiles) in enumerate([('CHEMBL2253255', SMILES), ('LOW', 'CCO'), ('HIGH', 'CCN')]):
        chemistry = structure_features(smiles)
        key = chemistry['structure_inchikey']
        critical = cid == 'CHEMBL2253255'
        features.append({'compound_id': cid, **chemistry})
        data['matrix'].append({'compound_id': cid, 'canonical_smiles': smiles,
            'rdkit_inchikey': key, 'critical_hold': 'YES' if critical else 'NO',
            'approved_herbicidal_activity': 'unknown', 'approved_natural_origin': 'unknown',
            'full_inchikey_external_match': 'NOT_INDEPENDENTLY_STRUCTURE_MATCHED' if critical else release.EXACT,
            'primary_paper_crosswalk_state': 'pending', 'remaining_required_verification': 'review source'})
        data['labels'].append({'compound_id': cid, 'herbicidal_activity': 'unknown', 'natural_origin': 'unknown'})
        low = cid == 'LOW'
        observation = dict.fromkeys(release.SOURCE_FIELDS, '')
        observation.update(compound_id = cid, activity_id = str(i), assay_chembl_id = 'CHEMBL3066645',
                           canonical_smiles = smiles, standard_relation = '<' if low else '>',
                           standard_value = '50.0' if low else '80.0', standard_units = '%')
        data['log'].append(observation)
        data['crosswalk'].append({'compound_id': cid, 'source_compound': f'7{i}',
            'crosswalk_status': 'CLEAR_STRUCTURE_CONFLICT' if critical else release.CONSISTENT,
            'frozen_smiles': smiles, 'frozen_inchikey': key,
            'chEMBL_frozen_recorded_band': 'under_50_band' if low else 'over_80_band',
            'source_paper_reported_A_retroflexus_post_emergence': 'under_50_band' if low else 'over_80_band',
            'reported_response_band_agrees_with_paper_narrative': 'YES'})
        data['conditional'].append({'compound_id': cid, 'conditional_activity_NOT_A_LABEL':
                                    'inactive' if low else 'active'})
        if not critical:
            data['references'].append({'compound_id': cid, 'frozen_smiles': smiles,
                'frozen_inchikey': key, 'reference_inchikey': key, 'comparison': release.EXACT,
                'claimed_name': cid, 'claimed_origin': 'natural' if cid == 'HIGH' else 'synthetic',
                'reference_url': 'https://example.org/' + cid})
    return data, copy.deepcopy(data['log']), features


def test_critical_hold_overrides_old_active_and_all_labels_stay_unknown():
    data, prior, features = example()
    before = copy.deepcopy(data)
    result = release.audit(data, prior, features)
    held = next(r for r in result['effective'] if r['compound_id'] == 'CHEMBL2253255')
    assert held['historical_conditional_NOT_LABEL'] == 'active'
    assert held['effective_conditional_NOT_LABEL'] == 'identity_hold'
    assert held['approved_activity'] == 'unknown'
    assert result['summary']['approved_activity_labels'] == result['summary']['model_fits'] == 0
    assert result['summary']['activity_model_status'] == 'blocked_unapproved_labels'
    assert all(not r['model_fitted'] for r in result['support'])
    assert result['support'][1]['n'] == 2
    assert data == before


@pytest.mark.parametrize('change,message', [('source', 'observation fields'), ('key', 'computed identity'),
    ('hold', 'hold flags disagree'), ('approval', 'explicitly unapproved'),
    ('matrix_claim', 'comparison disagree'), ('band', 'band differs'), ('ids', 'feature IDs')])
def test_inconsistent_release_fails_instead_of_reclassifying(change, message):
    data, prior, features = example()
    if change == 'source': data['log'][0]['standard_value'] = '0.0'
    elif change == 'key': data['matrix'][0]['rdkit_inchikey'] = 'WRONG'
    elif change == 'hold': data['matrix'][0]['critical_hold'] = 'NO'
    elif change == 'approval': data['manifest']['training_use_approved'] = True
    elif change == 'matrix_claim': data['matrix'][1]['full_inchikey_external_match'] = 'unknown'
    elif change == 'band': data['crosswalk'][0]['chEMBL_frozen_recorded_band'] = 'under_50_band'
    else: features.pop()
    with pytest.raises(ValueError, match = message):
        release.audit(data, prior, features)


def test_live_reference_failure_is_missingness_not_confirmation():
    data, prior, features = example()
    snapshot = {'key': 'reference:LOW', 'reference_url': 'https://example.org/LOW',
                'status': 403, 'kind': 'ppdb_html', 'body': 'blocked'}
    result = release.audit(data, prior, features, [snapshot])
    row = next(r for r in result['references'] if r['compound_id'] == 'LOW')
    assert row['released_comparison'] == release.EXACT
    assert row['source_status'] == 'source_unavailable'
    assert row['independently_retrieved_comparison'] == 'not_verified'
    assert row['origin_approved'] is False


def test_illustrative_isomers_share_formula_but_not_identity_or_fingerprint():
    result, svg = release.allyl_hypothesis(SMILES)
    assert result['formula'] == 'C18H18N4O4'
    assert result['different_full_inchikey']
    assert 0 < result['morgan_tanimoto'] < 1
    assert result['different_morgan_bits'] > 0
    assert result['activity_transfer_approved'] is False
    assert '<svg' in svg
    assert result['status'] == 'hypothetical_representation_demo_not_an_approved_correction'
    assert Chem.MolFromSmiles(result['hypothetical_allyl_smiles']) is not None
    with pytest.raises(ValueError, match = 'exactly one'):
        release.allyl_hypothesis('CCO')


def test_name_lookup_candidates_remain_unlabelled_and_missing_rows_remain_present():
    leads = [{'name': n, 'source_reference': 'https://example.org/paper',
              'reported_evidence': 'unverified lead'} for n in ('available', 'missing')]
    key = structure_features('CCO')['structure_inchikey']
    snapshots = [{'key': 'lead:available', 'status': 200, 'url': 'https://example.org/available',
                  'body': json.dumps({'PropertyTable': {'Properties': [
                      {'CID': 702, 'SMILES': 'CCO', 'InChIKey': key}]}})},
                 {'key': 'lead:missing', 'status': 404, 'url': 'https://example.org/missing'}]
    identities, features = release.lead_candidates(leads, snapshots, [])
    assert len(identities) == len(features) == 2
    assert identities[1]['status'] == 'name_not_resolved'
    assert features[1]['fingerprint'] is None
    assert all(r['activity_target'] is None and r['origin_target'] is None for r in features)
    assert identities[0]['source_structure_match'] == 'not_reviewed'


def test_schema_valid_known_label_cannot_override_identity_hold():
    release.reject_held_activity([{'compound_id': 'held', 'herbicidal_activity': 'unknown'}], {'held'})
    with pytest.raises(ValueError, match = 'identity hold'):
        release.reject_held_activity([{'compound_id': 'held', 'herbicidal_activity': 'active'}], {'held'})


def test_proposal_cli_checks_frozen_holds_and_preserves_working_labels(tmp_path):
    import csv
    import hashlib

    import polars as pl

    from labels import LABEL_FIELDS
    from validate_activity_proposal import validate

    _, _, features = example()
    audit = tmp_path / 'audit'
    audit.mkdir()
    holds = audit / 'identity_holds.csv'
    holds.write_text('compound_id\nCHEMBL2253255\n')
    (audit / 'manifest.json').write_text(json.dumps({'output_hashes': {
        str(holds): hashlib.sha256(holds.read_bytes()).hexdigest()}}))
    parquet = tmp_path / 'features.parquet'
    pl.DataFrame(features).write_parquet(parquet)
    labels = tmp_path / 'labels.csv'
    rows = [{'compound_id': r['compound_id'], 'herbicidal_activity': 'unknown'} for r in features]

    def save():
        with labels.open('w', newline = '') as stream:
            writer = csv.DictWriter(stream, fieldnames = sorted(LABEL_FIELDS))
            writer.writeheader()
            writer.writerows(rows)

    save()
    before = labels.read_bytes()
    result = validate(labels, parquet, audit)
    assert result['scientific_approval_verified'] is False
    assert result['models_fitted'] == 0
    assert labels.read_bytes() == before
    rows[0].update(herbicidal_activity = 'active', activity_reference = 'paper',
                   activity_context = 'bounded conditions', activity_policy = 'proposed')
    save()
    with pytest.raises(ValueError, match = 'identity hold'):
        validate(labels, parquet, audit)
    holds.write_text('compound_id\n')
    with pytest.raises(ValueError, match = 'hash mismatch'):
        validate(labels, parquet, audit)
