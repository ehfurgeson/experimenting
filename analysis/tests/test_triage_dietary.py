"""Triage separates handling, dietary concerns, plant-negative exclusions and missingness."""
import csv
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import triage_dietary as triage


def row():
    return {'compound_id': 'pubchem:5950', 'pubchem_cid': '5950', 'name': 'L-Alanine',
            'inchikey': 'fixture', 'family': 'amino_acid',
            'food_source_url': 'https://www.ecfr.gov/current/title-21/section-172.320',
            'identity_status': 'pubchem_rdkit_agree', 'review_status': 'pending_human_review'}


def snapshot(cid = 5950, codes = 'Not Classified'):
    return {'status': 200, 'url': 'https://example.org/pubchem', 'retrieved_at': 'fixture',
            'body': json.dumps({'Record': {'RecordNumber': cid, 'RecordType': 'CID',
                'Reference': [{'ReferenceNumber': 7, 'SourceName': 'contributor',
                               'URL': 'https://example.org/source'}],
                'Section': [{'TOCHeading': 'Safety and Hazards', 'Information': [
                    {'Name': 'GHS Hazard Statements', 'ReferenceNumber': 7,
                     'Value': {'StringWithMarkup': [{'String': codes}]}},
                    {'Name': 'Unrelated prose', 'Value': {'StringWithMarkup': [
                        {'String': 'Example code H300 is not a classification field'}]}}]}]}})}


def test_handling_only_is_distinct_from_systemic_and_no_code_is_not_a_safety_label():
    status, evidence = triage.pubchem_evidence(snapshot(codes = 'H315; H319'), 5950)
    assert len(evidence) == 1 and evidence[0]['source_name'] == 'contributor'
    result = triage.classify(row(), 'named_food_use_lead', status, evidence, [])
    assert result['triage'] == 'provisional_dietary_shortlist'
    assert result['ghs_handling_codes'] == 'H315;H319'
    assert result['ghs_systemic_codes'] == ''
    assert result['high_dose_safety'] == result['plant_activity'] == 'unknown'


def test_reproductive_suffix_and_conflicting_classifications_trigger_review():
    status, evidence = triage.pubchem_evidence(snapshot(codes = 'Not Classified; H302; H360FD'), 5950)
    result = triage.classify(row(), 'named_food_use_lead', status, evidence, [])
    assert result['triage'] == 'priority_review'
    assert result['ghs_systemic_codes'] == 'H302;H360FD'
    assert 'ghs_systemic_hazard_lead' in result['flags']


@pytest.mark.parametrize('food,hazard,evidence', [('unavailable', 'retrieved', [{'field':
    'GHS Hazard Statements', 'codes': ''}]), ('named_food_use_lead', 'unavailable', []),
    ('named_food_use_lead', 'retrieved', [])])
def test_missing_evidence_never_becomes_provisional_shortlist(food, hazard, evidence):
    result = triage.classify(row(), food, hazard, evidence, [])
    assert result['triage'] == 'evidence_gap' and result['evidence_gaps']


def test_positive_known_warning_overrides_an_evidence_gap():
    lead = {'flag': 'registered_herbicide_active'}
    result = triage.classify(row(), 'unavailable', 'unavailable', [], [lead])
    assert result['triage'] == 'exclude_presumed_plant_negative'
    assert result['plant_comparator_status'] == 'exclude_presumed_negative'
    assert result['plant_activity'] == 'unknown'
    assert result['evidence_gaps']


def test_overlap_and_prior_hold_cannot_be_automatically_cleared():
    r = {**row(), 'existing_matches': 'old', 'review_status': 'hold'}
    result = triage.classify(r, 'named_food_use_lead', 'retrieved', [], [])
    assert result['triage'] == 'priority_review'
    assert 'prior_hold' in result['flags'] and 'existing_selection_overlap' in result['flags']


def test_food_document_challenge_pages_and_mixture_scope():
    r = row()
    url, kind = triage.food_request(r)
    assert 'CFR-2025' in url and 'sec172-320.xml' in url
    s = {'status': 200, 'kind': kind, 'body': '<html>Request Access</html>'}
    assert triage.food_support(s, r)[0] == 'unrecognized_document'
    s['body'] = '<CFRGRANULE><P>L-Alanine may be used under conditions</P></CFRGRANULE>'
    assert triage.food_support(s, r)[0] == 'named_food_use_lead'
    assert triage.food_support(s, {**r, 'name': 'Maltose'})[0] == 'mixture_scope'
    s['body'] = '<CFRGRANULE><P>unrelated</P></CFRGRANULE>'
    assert triage.food_support(s, r)[0] == 'name_not_confirmed'


def inputs(tmp_path):
    r = {**row(), 'decision': 'retained human decision', 'reviewer': 'researcher',
         'decision_reference': 'https://example.org/decision'}
    source = tmp_path / 'review.csv'
    with source.open('w', newline = '') as f:
        writer = csv.DictWriter(f, fieldnames = list(r))
        writer.writeheader()
        writer.writerow(r)
    raw = tmp_path / 'raw'
    raw.mkdir()
    for i, (key, (url, kind)) in enumerate(triage.requests_for([r]).items()):
        s = snapshot()
        s.update(key = key, url = url, kind = kind)
        if kind == 'annual_cfr_2025_xml':
            s['body'] = '<CFRGRANULE><P>L-Alanine nutrient use</P></CFRGRANULE>'
        (raw / f'{i}.json').write_text(json.dumps(s))
    return source, raw, tmp_path / 'output'


def test_offline_exports_preserve_human_decisions_and_source_bytes(tmp_path):
    source, raw, output = inputs(tmp_path)
    before = source.read_bytes()
    manifest = triage.run(source, raw, output)
    assert source.read_bytes() == before
    assert manifest['counts']['provisional_dietary_shortlist'] == 1
    with (output / 'triage.csv').open() as f:
        result = next(csv.DictReader(f))
    assert result['researcher_decision'] == 'retained human decision'
    assert result['reviewer'] == 'researcher' and result['plant_activity'] == 'unknown'
    with pytest.raises(ValueError, match = 'empty output'):
        triage.run(source, raw, output)
    with pytest.raises(ValueError, match = 'outside'):
        triage.run(source, raw, tmp_path)


def test_wrong_cid_and_incomplete_snapshots_fail_before_export(tmp_path):
    source, raw, output = inputs(tmp_path)
    p = raw / '0.json'
    s = json.loads(p.read_text())
    d = json.loads(s['body'])
    d['Record']['RecordNumber'] = 999
    s['body'] = json.dumps(d)
    p.write_text(json.dumps(s))
    with pytest.raises(ValueError, match = 'CID'):
        triage.run(source, raw, output)
    assert not output.exists()
    p.unlink()
    with pytest.raises(ValueError, match = 'every request'):
        triage.run(source, raw, output)
    assert not output.exists()


def test_text_hits_are_review_leads_even_for_null_findings_not_toxicity_labels():
    policy = json.loads(triage.POLICY.read_text())
    evidence = [{'section': 'Toxicity > Human Toxicity Excerpts',
                 'text': 'No significant effect on homocysteine was observed.', 'codes': '',
                 'field': '', 'source_url': 'https://example.org/paper'}]
    signals = triage.scan_toxicity(evidence, policy)
    assert [s['signal'] for s in signals] == ['methionine_homocysteine']
    assert signals[0]['interpretation'] == 'unadjudicated_text_match'
    result = triage.classify(row(), 'named_food_use_lead', 'retrieved', [], [], signals)
    assert result['triage'] == 'priority_review'
    assert result['plant_activity'] == result['high_dose_safety'] == 'unknown'
    evidence[0]['section'] = 'Non-Human Toxicity Excerpts'
    assert not triage.scan_toxicity(evidence, policy)


def test_toxicity_retrieval_gap_blocks_shortlist_even_with_a_ghs_record():
    result = triage.classify(row(), 'named_food_use_lead', 'retrieved',
                            [{'field': 'GHS Hazard Statements', 'codes': ''}], [],
                            toxicity_status = 'unavailable')
    assert result['triage'] == 'evidence_gap'
    assert 'toxicity_retrieval_gap' in result['evidence_gaps']
