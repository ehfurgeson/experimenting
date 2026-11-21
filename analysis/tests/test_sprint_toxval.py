import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sprint_toxval import run, screen_row


def source_row():
    return {'SOURCE_HASH': 'native1', 'DTXSID': 'DTXSID1', 'NAME': 'Test compound',
            'SUBSOURCE_URL': 'https://example.test/dossier/1', 'EXPERIMENTAL_RECORD': 'experimental',
            'SPECIES_COMMON': 'Rat', 'EXPOSURE_ROUTE': 'oral', 'STUDY_TYPE': 'acute',
            'TOXVAL_TYPE': 'LD50', 'TOXVAL_UNITS': 'mg/kg', 'TOXVAL_NUMERIC': '100',
            'QUALIFIER': '>', 'QC_STATUS': 'not determined', 'STUDY_DURATION_VALUE': '-999',
            'STUDY_DURATION_UNITS': '-', 'EXPOSURE_FORM': '-', 'STUDY_GROUP': 'provider_group'}


def test_endpoint_eligible_censor_retains_form_and_independence_holds():
    row = screen_row(source_row(), [], {'DTXSID1': {'KEY'}}, {'KEY'}, 'echa', 3)
    assert row['status'] == 'endpoint_eligible_censored'
    assert row['value'] == '100' and row['qualifier'] == '>'
    assert row['is_existing_a_structure'] is True
    assert 'tested_material_form_not_verified' in row['admission_holds']
    assert 'source_study_independence_unresolved' in row['admission_holds']


@pytest.mark.parametrize('field,value,reason', [
    ('EXPERIMENTAL_RECORD', 'undetermined', 'not_explicit_experimental'),
    ('EXPERIMENTAL_RECORD', 'predicted', 'not_explicit_experimental'),
    ('EXPOSURE_ROUTE', 'dermal', 'not_oral'),
    ('TOXVAL_NUMERIC', 'nan', 'nonpositive_or_nonfinite_value'),
    ('QUALIFIER', '~', 'unsupported_qualifier'),
    ('QC_STATUS', 'fail', 'source_qc_fail'),
])
def test_context_failures_are_excluded(field, value, reason):
    raw = source_row() | {field: value}
    row = screen_row(raw, [], {}, set(), 'echa', 2)
    assert row['status'] == 'excluded'
    assert reason in row['exclusion_reason']


def test_ambiguous_dtxsid_is_never_resolved_by_first_hit():
    row = screen_row(source_row(), [], {'DTXSID1': {'KEY1', 'KEY2'}}, set(), 'echa', 2)
    assert row['full_inchikey'] == ''
    assert row['candidate_full_inchikeys'] == 'KEY1;KEY2'
    assert row['is_existing_a_structure'] == 'unknown'
    assert 'ambiguous_dtxsid_structure' in row['admission_holds']


def test_audit_rejects_duplicate_source_ids_before_creating_output(tmp_path):
    output = tmp_path / 'output'
    with pytest.raises(ValueError, match='at least one unique ToxValDB source'):
        run(tmp_path / 'missing.json', tmp_path, tmp_path / 'missing.csv', output,
            source_ids=['toxval-opp', 'toxval-opp'])
    assert not output.exists()
