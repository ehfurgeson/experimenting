"""Evidence-type, identity, units and immutable-source release boundaries."""
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence_release import (
    catmos_prediction,
    freeze,
    ice_observation,
    ld50_bin,
    number,
    sdf_properties,
    structure,
    workbook_rows,
)


def measured(**changes):
    return {'Record_ID': 'a', 'Data_Type': 'In Vivo', 'Species': 'Rat',
            'Mixture': 'Chemical', 'Assay': 'Rat Acute Oral Toxicity', 'Endpoint': 'LD50',
            'Response_Unit': 'mg/kg', 'Response': '100', 'Reference': 'Primary A', **changes}


def test_censored_measured_doses_are_not_exact_outcomes():
    row = ice_observation(measured(Response_Modifier = '>'), 2, structure('CCO'))
    assert row['status'] == 'censored'
    assert row['value_mg_kg'] == 100
    assert row['source_locator'] == 'Data!row2'


@pytest.mark.parametrize('change,reason', [
    ({'Data_Type': 'In Silico'}, 'not_explicit_in_vivo'),
    ({'Mixture': 'Mixture'}, 'mixture_or_unknown'),
    ({'Response': '0'}, 'missing_nonpositive_or_nonfinite'),
    ({'Response': 'NaN'}, 'missing_nonpositive_or_nonfinite'),
    ({'Response_Unit': 'mg/kg-day'}, 'not_mg_kg'),
    ({'Reference': None}, 'missing_reference'),
])
def test_incompatible_records_are_retained_but_excluded(change, reason):
    row = ice_observation(measured(**change), 2, structure('CCO'))
    assert row['status'] == 'excluded'
    assert reason in row['reasons']
    assert row['source_record_json']
    if change.get('Data_Type') == 'In Silico':
        assert row['evidence_class'] == 'predicted'


def test_catmos_uses_prediction_not_experimental_or_consensus_field():
    raw = {'CATMoS_LD50_pred': '3', 'CATMoS_LD50_mgkg': '7',
           'consensus_LD50': '1', 'AD_CATMoS': '1', 'CATMoS_Tr_Tst': 'Tr'}
    row = catmos_prediction(raw, 1, structure('CCO'))
    assert row['status'] == 'eligible'
    assert row['value_log10_mg_kg'] == 3
    assert row['unit'] == 'log10(mg/kg)'
    assert row['evidence_class'] == 'predicted'
    assert row['training_membership'] == 'Tr'
    raw['AD_CATMoS'] = ''
    assert catmos_prediction(raw, 1, structure('CCO'))['status'] == 'excluded'


def test_structure_keeps_stereo_and_multicomponent_boundaries():
    left, right = structure('C[C@H](O)C(=O)O'), structure('C[C@@H](O)C(=O)O')
    assert left['full_key'] != right['full_key']
    assert left['connectivity'] == right['connectivity']
    assert structure('CCO.[Na+]')['identity_status'] == 'multiple_components'
    assert structure(None)['identity_status'] == 'invalid_or_missing_structure'


def test_sdf_retains_blank_multiline_and_truncation(tmp_path):
    path = tmp_path / 'data.zip'
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('CATMoS_QR50k.sdf', 'M  END\n> <ID>\n1\n\n> <empty>\n\n$$$$\n')
    assert list(sdf_properties(path)) == [(1, {'ID': '1', 'empty': ''})]
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('CATMoS_QR50k.sdf', '> <ID>\n1\n')
    with pytest.raises(ValueError, match = 'Truncated'):
        list(sdf_properties(path))


def test_workbook_preserves_sparse_cell_positions(tmp_path):
    path = tmp_path / 'book.xlsx'
    ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('xl/workbook.xml', f'<workbook xmlns="{ns}" '
                         'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                         '<sheets><sheet name="Data" r:id="r1"/></sheets></workbook>')
        archive.writestr('xl/_rels/workbook.xml.rels',
                         '<Relationships><Relationship Id="r1" Target="worksheets/sheet1.xml"/>'
                         '</Relationships>')
        archive.writestr('xl/worksheets/sheet1.xml', f'<worksheet xmlns="{ns}"><sheetData>'
                         '<row r="1"><c r="A1" t="inlineStr"><is><t>ID</t></is></c>'
                         '<c r="B1" t="inlineStr"><is><t>value</t></is></c></row>'
                         '<row r="3"><c r="B3"><v>0</v></c></row></sheetData></worksheet>')
    assert list(workbook_rows(path, 'Data')) == [(3, {'ID': None, 'value': '0'})]


def test_immutable_release_and_fixed_cutoffs(tmp_path):
    with pytest.raises(FileExistsError):
        freeze(tmp_path, tmp_path, tmp_path)
    import math
    assert ld50_bin(math.log10(1080)) == 0
    assert ld50_bin(math.log10(3400)) == 1
    assert ld50_bin(4) == 2
    assert number('inf') is None


def test_provider_key_mismatch_is_retained_but_cannot_enter_B():
    row = catmos_prediction({'CATMoS_LD50_pred': '3', 'AD_CATMoS': '1',
                             'InChI Key_QSARr': 'WRONG'}, 1, structure('CCO'))
    assert row['status'] == 'excluded'
    assert 'provider_full_key_mismatch' in row['reasons']
