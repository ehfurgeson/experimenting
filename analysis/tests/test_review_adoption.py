"""Human approval adoption preserves bounded labels, explicit holds and source bytes."""
import copy
import csv
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from review_adoption import (
    K1998,
    blank_label,
    legacy_decisions,
    workbook_decisions,
    workbook_tables,
)


def fixture_rows():
    original = [{'compound_id': 'x', 'name': 'Example', 'axis': 'origin',
                 'proposed_policy': 'PROPOSED-EXACT-NATURAL-OCCURRENCE-v1', 'proposed_decision': 'unknown'},
                {'compound_id': 'x', 'name': 'Example', 'axis': 'activity',
                 'proposed_policy': 'PROPOSED-K1998-LETTUCE-1MM-6D-v1', 'proposed_decision': 'low_response'}]
    rows = [{**r, 'approval_state': 'approved', 'reviewer': 'Human reviewer',
             'review_date': '2026-11-11', 'source_locator': 'paper Table 1',
             'scientific_approval_reference': 'doi:example', 'rationale': 'exact context',
             'identity_status': 'source_structure_checked_matches',
             'proposed_decision': 'natural' if r['axis'] == 'origin' else 'active'} for r in original]
    return original, rows


def test_workbook_revised_decisions_override_original_and_axes_are_independent():
    original, rows = fixture_rows()
    rows[1].update(proposed_decision = 'unknown', approval_state = 'unreviewed')
    batches, origin, ledger = workbook_decisions({'Reviewed Worksheet': rows}, original,
        [{'compound_id': 'x', 'name': 'Example'}], {'approval_id': 'human-session'})
    assert origin[0]['natural_origin'] == 'natural'
    assert batches[K1998][0]['natural_origin'] == 'natural'
    assert batches[K1998][0]['herbicidal_activity'] == 'unknown'
    assert ledger[1]['prior_proposed_decision'] == 'low_response'
    assert ledger[1]['adopted_decision'] == 'unknown'
    assert set(origin[0]) == set(blank_label('x'))


@pytest.mark.parametrize('field,value', [('identity_status', 'identity_hold'), ('reviewer', ''),
    ('scientific_approval_reference', ''), ('source_locator', ''), ('review_date', ''),
    ('approval_state', 'automatic'), ('proposed_decision', 'safe'), ('name', 'Wrong')])
def test_incomplete_conflicting_or_invalid_approvals_fail(field, value):
    original, rows = fixture_rows()
    rows[0][field] = value
    with pytest.raises(ValueError):
        workbook_decisions({'Reviewed Worksheet': rows}, original,
            [{'compound_id': 'x', 'name': 'Example'}], {'approval_id': 'session'})


@pytest.mark.parametrize('mutation', ['missing', 'duplicate'])
def test_exact_workbook_coverage_required(mutation):
    original, rows = fixture_rows()
    rows = rows[:1] if mutation == 'missing' else rows+[copy.deepcopy(rows[0])]
    with pytest.raises(ValueError, match = 'exactly once'):
        workbook_decisions({'Reviewed Worksheet': rows}, original,
            [{'compound_id': 'x', 'name': 'Example'}], {'approval_id': 'session'})


def tiny_xlsx(path, formula = False):
    base = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    row = '<row r="1"><c r="A1" t="inlineStr"><is><t>decision</t></is></c></row>'
    row += '<row r="2"><c r="A2" t="inlineStr">'+ ('<f>1+1</f>' if formula else '')
    row += '<is><t>'+escape('active & bounded')+'</t></is></c></row>'
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('xl/workbook.xml', f'<workbook xmlns="{base}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Review" sheetId="1" r:id="r1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels', '<Relationships><Relationship Id="r1" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr('xl/worksheets/sheet1.xml', f'<worksheet xmlns="{base}"><sheetData>{row}</sheetData></worksheet>')


def test_literal_workbook_read_preserves_bytes_and_row_locator(tmp_path):
    path = tmp_path/'review.xlsx'
    tiny_xlsx(path)
    before = path.read_bytes()
    assert workbook_tables(path)['Review'] == [{'decision': 'active & bounded', '_xlsx_row': '2'}]
    assert path.read_bytes() == before
    tiny_xlsx(path, formula = True)
    with pytest.raises(ValueError, match = 'not formulas'):
        workbook_tables(path)


def write(path, rows):
    with path.open('w', newline = '') as f:
        w = csv.DictWriter(f, fieldnames = list(rows[0])); w.writeheader(); w.writerows(rows)


def test_legacy_assertion_does_not_resolve_explicit_conflicts_or_create_synthetic_truth(tmp_path):
    release = tmp_path/'release';release.mkdir()
    audit = tmp_path/'audit';audit.mkdir()
    from review_adoption import CONSISTENT
    ids = ['good', 'hold', 'stereo', 'gray']
    conditional = [{'compound_id': cid, 'scenario_policy_UNAPPROVED': 'PROPOSED-LI2006-test',
                    'source_doi': 'doi:primary', 'assay_id': 'source-assay',
                    'interpretation': 'band', 'original_frozen_outcomes': '>80',
                    'structure_to_source_verified': 'historical pending'} for cid in ids]
    write(release/'conditional_assay_screen_NOT_FOR_TRAINING.csv', conditional)
    write(audit/'effective_conditional_screen.csv', [{'compound_id': cid,
          'effective_conditional_NOT_LABEL': 'unknown' if cid == 'gray' else 'active'} for cid in ids])
    write(audit/'identity_holds.csv', [{'compound_id': 'hold'}])
    write(release/'li_2006_24_compound_source_crosswalk.csv', [
        {'compound_id': cid, 'crosswalk_status': CONSISTENT if cid != 'stereo' else 'UNRESOLVED_STEREO'} for cid in ids])
    write(release/'PROPOSED_ORIGIN_FULL_STRUCTURE_MATCHES_NOT_FOR_TRAINING.csv', [
        {'compound_id': 'good', 'proposed_origin': 'synthetic_provenance_documented',
         'external_stereo_structure_match': 'exact', 'independent_origin_evidence': 'manufacturing'}])
    batches, origins, _, ledger = legacy_decisions(release, audit, {c: {} for c in ids}, {'approval_id': 'session'})
    labels = {r['compound_id']: r for r in batches['HUMAN-LI2006-test']}
    assert labels['good']['herbicidal_activity'] == 'active'
    assert all(labels[c]['herbicidal_activity'] == 'unknown' for c in ids[1:])
    assert all(r['natural_origin'] == 'unknown' for r in origins)
    assert sum(r['status'] == 'explicit_identity_gap' for r in ledger) == 2
