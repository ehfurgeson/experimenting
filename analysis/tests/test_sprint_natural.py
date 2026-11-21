import json
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sprint_natural import catalog_matches, identity, npass_toxicity, run_coconut, sha256, tab_rows


def test_identity_keeps_salts_and_provider_conflicts_out_of_exact_matches():
    valid = identity('CCO', 'LFQSCWFLJHTTHZ-UHFFFAOYSA-N')
    assert valid['identity_status'] == 'valid'
    assert identity('CCO', 'WRONG')['identity_status'] == 'provider_key_conflict'
    assert identity('CCO.[Na+]', 'WRONG')['identity_status'] == 'multiple_components'
    assert identity('', '')['identity_status'] == 'invalid_or_missing_structure'
    baseline = [{'full_inchikey': valid['full_inchikey'], 'identity_status': 'valid',
                 'cohort': 'A', 'compound_id': '1', 'selection_group': ''}]
    matches = catalog_matches([valid | {'source_compound_id': 'CAT1'}], baseline, 'catalog')
    assert matches[0]['match_tier'] == 'exact_full_key'
    assert matches[0]['verified_taxon_reference_occurrence'] == 'unknown'


def test_connectivity_match_cannot_promote_stereo_or_held_identity():
    catalog = identity('C[C@H](O)C(=O)O', 'JVTAAEKCZFNVCJ-REOHCLBHSA-N')
    assert catalog['identity_status'] == 'valid'
    baseline = [{'full_inchikey': 'JVTAAEKCZFNVCJ-UHFFFAOYSA-N', 'identity_status': 'valid',
                 'cohort': 'A', 'compound_id': '1', 'selection_group': ''}]
    result = catalog_matches([catalog | {'source_compound_id': 'CAT1'}], baseline, 'catalog')
    assert result[0]['match_tier'] == 'connectivity_only_review'
    baseline[0]['full_inchikey'] = catalog['full_inchikey']
    baseline[0]['identity_status'] = 'identity_hold'
    assert catalog_matches([catalog | {'source_compound_id': 'CAT1'}], baseline,
                           'catalog')[0]['match_tier'] != 'exact_full_key'


def test_npass_ld50_without_context_never_becomes_training_label():
    raw = {'np_id': 'NPC1', 'activity_value': '100', 'activity_type': 'LD50',
           'assay_organism': 'Rattus norvegicus', 'activity_units': 'mg/kg',
           'activity_relation': '>', 'ref_id': '12345', 'ref_id_type': 'PMID'}
    compound = identity('CCO', 'LFQSCWFLJHTTHZ-UHFFFAOYSA-N')
    row = npass_toxicity(raw, compound, 7, {compound['full_inchikey']})
    assert row['status'] == 'review_only'
    assert row['is_experimental'] == 'unknown'
    assert row['qualifier'] == '>'
    assert row['is_existing_a_structure']
    assert row['exclusion_reason'].split(';') == [
        'route_not_reported', 'acute_context_not_reported', 'experimental_status_not_reported']


def test_delimiter_only_separators_are_not_records_but_truncated_rows_fail(tmp_path):
    path = tmp_path / 'source.tsv'
    path.write_text('id\tname\textra\n1\tone\tok\n\t\n2\ttwo\tok\n')
    assert [r['id'] for _, r in tab_rows(path)] == ['1', '2']
    path.write_text('id\tname\textra\n1\tone\n')
    with pytest.raises(ValueError, match = 'Malformed source row'):
        list(tab_rows(path))


def test_coconut_cohort_index_requalifies_keys_inside_the_block(tmp_path):
    exact = 'LFQSCWFLJHTTHZ-UHFFFAOYSA-N'
    other = 'VNWKTOKETHGBQD-UHFFFAOYSA-N'
    source = tmp_path / 'source.zip'
    with ZipFile(source, 'w') as archive:
        archive.writestr('catalog.csv', 'identifier,canonical_smiles,standard_inchi_key\n'
                         f'exact,CCO,{exact}\nwrong,CC,{exact}\noutside,C,{other}\n')
    registry = tmp_path / 'sources.json'
    registry.write_text(json.dumps([{'source_id': 'coconut-lite', 'status': 'downloaded',
                                     'file': source.name, 'sha256': sha256(source)}]))
    baseline = tmp_path / 'baseline.csv'
    baseline.write_text('full_inchikey,identity_status,cohort,compound_id,selection_group\n'
                        f'{exact},valid,A,1,\n')
    (tmp_path / 'manifest.json').write_text(json.dumps({
        'products': {baseline.name: sha256(baseline)},
    }))
    full = run_coconut(registry, baseline, tmp_path / 'full')
    targeted = run_coconut(registry, baseline, tmp_path / 'targeted', cohort_only=True)
    assert full['overlap'] == targeted['overlap'] == {'A': {'exact_full_key': 1}}
    assert targeted['identity_status'] == {
        'valid': 1, 'provider_key_conflict': 1, 'outside_provider_connectivity_index': 1,
    }
