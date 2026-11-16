"""Evidence-backed preliminary dietary-candidate triage, with explicit unknowns."""

import argparse
import csv
import json
import re
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from html.parser import HTMLParser
from importlib.metadata import version
from pathlib import Path
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from screen import HERE, hashes, write_csv

POLICY = HERE / 'resources/dietary_triage_policy.json'
HEADINGS = ('Safety and Hazards', 'Toxicity')
# Handling-only irritant codes and aquatic hazards are recorded on separate axes.
SYSTEMIC = re.compile(r'H(?:30[0-5]|3[13][0-3]|3[45][01]|36[012]|37[0123])\b')
HANDLING = re.compile(r'H(?:31[45789]|33[456])\b')
AQUATIC = re.compile(r'H4[01][0123]\b')
TRIAGE_ORDER = ('exclude_presumed_plant_negative', 'priority_review',
                'evidence_gap', 'provisional_dietary_shortlist')


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def read_review(path):
    with Path(path).open(newline = '') as stream:
        rows = list(csv.DictReader(stream))
    required = ('compound_id', 'name', 'pubchem_cid', 'inchikey', 'family',
                'identity_status', 'food_source_url', 'review_status')
    if not rows or any(not r.get(k) for r in rows for k in required):
        raise ValueError('Review rows require complete identity and source fields')
    ids = [r['compound_id'] for r in rows]
    cids = [int(r['pubchem_cid']) for r in rows]
    if len(set(ids)) != len(ids) or len(set(cids)) != len(cids) or any(c <= 0 for c in cids):
        raise ValueError('Review IDs and positive CIDs must be unique')
    return rows


def food_request(row):
    """Use dated official annual XML, not a silently substituted current regulation."""
    match = re.search(r'/section-(\d+)\.(\d+)$', row['food_source_url'])
    if match:
        part, section = match.groups()
        vol = 2 if int(part) < 170 else 3
        url = (f'https://www.govinfo.gov/content/pkg/CFR-2025-title21-vol{vol}/xml/'
               f'CFR-2025-title21-vol{vol}-sec{part}-{section}.xml')
        return url, 'annual_cfr_2025_xml'
    return row['food_source_url'], 'fda_gras_html'


def requests_for(rows):
    requests_map = {}
    for row in rows:
        cid = int(row['pubchem_cid'])
        for heading in HEADINGS:
            url = (f'https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON'
                   f'?heading={quote(heading)}')
            requests_map[f'pubchem:{cid}:{heading}'] = (url, 'pubchem_json')
        url, kind = food_request(row)
        requests_map['food:' + row['food_source_url']] = (url, kind)
    return requests_map


def fetch(review, snapshots):
    rows = read_review(review)
    snapshots = Path(snapshots)
    if snapshots.exists() and any(snapshots.iterdir()):
        raise ValueError('Use an empty snapshot directory')
    snapshots.mkdir(parents = True, exist_ok = True)
    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries = Retry(
        total = 3, backoff_factor = 1, status_forcelist = [429, 500, 502, 503, 504])))
    jobs = requests_for(rows)
    for i, (key, (url, kind)) in enumerate(jobs.items()):
        snapshot = {'key': key, 'url': url, 'kind': kind,
                    'retrieved_at': datetime.now(UTC).isoformat(), 'status': None,
                    'body': None, 'error': None}
        try:
            response = session.get(url, timeout = 45)
            snapshot.update(status = response.status_code, body = response.text)
        except requests.RequestException as exc:
            snapshot['error'] = type(exc).__name__
        (snapshots / f'{i:03d}.json').write_text(json.dumps(snapshot, indent = 2) + '\n')
        print(f'{i + 1}/{len(jobs)} {key}: {snapshot["status"]}', flush = True)
        time.sleep(.25)
    return snapshots


def food_support(snapshot, row):
    if snapshot['status'] != 200:
        return 'unavailable', ''
    try:
        if snapshot['kind'] == 'annual_cfr_2025_xml':
            tree = ET.fromstring(snapshot['body'])
            if tree.tag != 'CFRGRANULE':
                return 'unrecognized_document', ''
            text = ' '.join(tree.itertext())
        else:
            parser = Text()
            parser.feed(snapshot['body'])
            text = ' '.join(parser.parts)
            if 'GRN No.' not in text:
                return 'unrecognized_document', ''
    except (ET.ParseError, TypeError):
        return 'malformed_document', ''
    # Confirm a named food-use lead, without claiming dose/identity adjudication.
    names = {'D-Glucose': ['D-glucose', 'dextrose'], 'Glycerol': ['glycerin'],
             'L-Malic acid': ['L-malic acid', 'malic acid']}.get(row['name'], [row['name']])
    normalized = re.sub('[^a-z]', '', text.casefold())
    matched = any(re.sub('[^a-z]', '', name.casefold()) in normalized for name in names)
    if row['name'] in ('D-Fructose', 'Maltose'):
        return 'mixture_scope', 'Reference concerns HFCS or malt syrup, not an isolated-compound dose.'
    return ('named_food_use_lead' if matched else 'name_not_confirmed'), snapshot['kind']


def sections(record, path = ()):
    for section in record.get('Section', []):
        heading = (*path, section.get('TOCHeading', ''))
        for info in section.get('Information', []):
            yield heading, info
        yield from sections(section, heading)


def pubchem_evidence(snapshot, cid):
    """Only explicit GHS statement fields supply codes; other toxicity text is a review lead."""
    if snapshot['status'] != 200:
        return 'unavailable', []
    try:
        record = json.loads(snapshot['body'])['Record']
    except (json.JSONDecodeError, KeyError, TypeError):
        return 'malformed_record', []
    if record.get('RecordType') != 'CID' or record.get('RecordNumber') != cid:
        raise ValueError('PubChem snapshot CID does not match candidate')
    references = {r['ReferenceNumber']: r for r in record.get('Reference', [])}
    result = []
    for path, info in sections(record):
        name = info.get('Name', '')
        # Keep exact source text and contributor references for reviewer inspection.
        if name != 'GHS Hazard Statements' and not any(
            'Toxicity' in p or 'Toxic' in p or 'Effects' in p for p in path
        ):
            continue
        strings = [v['String'] for v in info.get('Value', {}).get('StringWithMarkup', [])
                   if isinstance(v.get('String'), str)]
        for text in strings:
            reference = references.get(info.get('ReferenceNumber'), {})
            result.append({'section': ' > '.join(path), 'field': name, 'text': text,
                           'codes': ';'.join(sorted(set(re.findall(r'\bH\d{3}(?:[A-Za-z]{1,2})?\b', text))))
                                    if name == 'GHS Hazard Statements' else '',
                           'reference_number': info.get('ReferenceNumber'),
                           'source_name': reference.get('SourceName', ''),
                           'source_url': reference.get('URL', ''),
                           'snapshot_url': snapshot['url'], 'retrieved_at': snapshot['retrieved_at']})
    return 'retrieved', result


def scan_toxicity(evidence, policy):
    """Find review passages; no polarity, causality, dose or species inference is made."""
    result = []
    for e in evidence:
        if not set(e['section'].split(' > ')).intersection(policy['text_signal_sections']):
            continue
        for signal, pattern in policy['text_signals'].items():
            if re.search(pattern, e['text'], re.IGNORECASE):
                result.append({'signal': signal, 'interpretation': 'unadjudicated_text_match', **e})
    return result


def classify(row, food_status, hazard_status, evidence, leads, text_signals = (),
             toxicity_status = 'retrieved', toxicity_available = True):
    flags = []
    if row['identity_status'] != 'pubchem_rdkit_agree':
        flags.append('identity_not_verified')
    if row.get('existing_matches'):
        flags.append('existing_selection_overlap')
    if row['review_status'] == 'hold':
        flags.append('prior_hold')
    if food_status == 'mixture_scope':
        flags.append('food_reference_is_mixture')
    if row['family'] == 'fatty_acid':
        flags.append('free_acid_vs_food_fat_exposure')
    if row['family'] == 'organic_acid':
        flags.append('pH_and_concentration_review')
    if row['family'] == 'sugar':
        flags.append('sugar_dose_and_anomer_review')
    if row['family'] == 'polyol' and row['name'] != 'Glycerol':
        flags.append('polyol_dose_tolerance_review')
    flags += [lead['flag'] for lead in leads]
    flags += ['text_' + e['signal'] for e in text_signals]
    codes = sorted({c for e in evidence for c in e['codes'].split(';') if c})
    systemic = [c for c in codes if SYSTEMIC.fullmatch(c[:4])]
    if systemic:
        flags.append('ghs_systemic_hazard_lead')
    gaps = []
    if toxicity_status != 'retrieved':
        gaps.append('toxicity_retrieval_gap')
    elif not toxicity_available:
        gaps.append('no_toxicity_text_extracted')
    if food_status != 'named_food_use_lead':
        gaps.append('specific_food_use_not_confirmed')
    if hazard_status != 'retrieved':
        gaps.append('hazard_retrieval_gap')
    elif not any(e['field'] == 'GHS Hazard Statements' for e in evidence):
        gaps.append('no_ghs_statement_field')
    if 'registered_herbicide_active' in flags:
        triage = 'exclude_presumed_plant_negative'
    elif flags:
        triage = 'priority_review'
    elif gaps:
        triage = 'evidence_gap'
    else:
        triage = 'provisional_dietary_shortlist'
    return {'triage': triage, 'flags': ';'.join(sorted(set(flags))),
            'evidence_gaps': ';'.join(gaps), 'ghs_systemic_codes': ';'.join(systemic),
            'ghs_handling_codes': ';'.join(c for c in codes if HANDLING.fullmatch(c)),
            'ghs_aquatic_codes': ';'.join(c for c in codes if AQUATIC.fullmatch(c)),
            'ghs_all_codes': ';'.join(codes), 'food_support': food_status,
            'hazard_status': hazard_status,
            'plant_comparator_status': 'exclude_presumed_negative' if
                'registered_herbicide_active' in flags else 'unknown_requires_plant_assay',
            'high_dose_safety': 'unknown', 'plant_activity': 'unknown'}


def run(review, snapshots, output, policy = POLICY):
    review, snapshots, output, policy = [Path(p).resolve() for p in
                                         (review, snapshots, output, policy)]
    if any(p.is_relative_to(output) for p in (review, snapshots, policy)):
        raise ValueError('Output must be outside input paths')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use an empty output directory')
    rows = read_review(review)
    rules = json.loads(policy.read_text())
    paths = sorted(snapshots.glob('*.json'))
    saved = {}
    expected = requests_for(rows)
    for path in paths:
        s = json.loads(path.read_text())
        key = s['key']
        if key in saved or key not in expected:
            raise ValueError('Unexpected or duplicate snapshot key')
        if (s['url'], s['kind']) != expected[key]:
            raise ValueError('Snapshot URL/kind does not match acquisition request')
        saved[key] = s
    if set(saved) != set(expected):
        raise ValueError('A snapshot, including explicit failures, is required for every request')
    triage, extracts, ledger, text_hits = [], [], [], []
    for row in rows:
        cid, identity = int(row['pubchem_cid']), row['compound_id']
        fs = saved['food:' + row['food_source_url']]
        food_status, scope = food_support(fs, row)
        hazard_status, evidence = pubchem_evidence(saved[f'pubchem:{cid}:Safety and Hazards'], cid)
        toxicity_status, toxicity = pubchem_evidence(saved[f'pubchem:{cid}:Toxicity'], cid)
        signals = scan_toxicity(toxicity, rules)
        for signal in signals:
            text_hits.append({'compound_id': identity, 'name': row['name'], **signal})
        for e in [*evidence, *toxicity]:
            extracts.append({'compound_id': identity, 'name': row['name'], **e})
        leads = [lead for lead in rules['curated_leads'] if cid in lead['cids']]
        for lead in leads:
            ledger.append({'compound_id': identity, 'name': row['name'],
                           'flag': lead['flag'], 'summary': lead['summary'], 'source_url': lead['url'],
                           'evidence_type': 'curated_primary_source_lead',
                           'checked_date': rules['checked_date'],
                           **{k: lead.get(k, '') for k in ('quantity', 'unit', 'quantity_type', 'context')}})
        classification = classify(row, food_status, hazard_status, evidence, leads, signals,
                                  toxicity_status, bool(toxicity))
        if classification['triage'] == TRIAGE_ORDER[-1]:
            reason = 'Named conditional food-use lead and identity agreement; no policy trigger found.'
            action = 'Review actual dietary dose, population, source conditions and natural occurrence.'
        else:
            reason = '; '.join([*(lead['summary'] for lead in leads),
                                *(('Text review lead: ' + e['signal']) for e in signals)])
            if not reason:
                reason = classification['flags'] or classification['evidence_gaps']
            action = ('Resolve flags/gaps using source passages; specify dose, population and species. '
                      'Keep separate from any accepted plant-negative group.')
        triage.append({'compound_id': identity, 'name': row['name'], 'pubchem_cid': cid,
                       'family': row['family'], **classification,
                       'preliminary_reason': reason, 'next_review_action': action,
                       'food_scope': scope, 'food_snapshot_url': fs['url'],
                       'food_retrieved_at': fs['retrieved_at'], 'toxicity_status': toxicity_status,
                       'toxicity_extract_count': len(toxicity), 'policy_id': rules['policy_id'],
                       'review_caveat': row.get('review_caveat', ''),
                       'researcher_decision': row.get('decision', ''),
                       'reviewer': row.get('reviewer', ''),
                       'decision_reference': row.get('decision_reference', '')})
    triage.sort(key = lambda r: (TRIAGE_ORDER.index(r['triage']), r['name']))
    output.mkdir(parents = True, exist_ok = True)
    write_csv(output / 'triage.csv', triage, list(triage[0]))
    write_csv(output / 'pubchem_extracts.csv', extracts, list(extracts[0]) if extracts else
              ['compound_id', 'name', 'section', 'field', 'text', 'codes', 'reference_number',
               'source_name', 'source_url', 'snapshot_url', 'retrieved_at'])
    write_csv(output / 'curated_leads.csv', ledger, list(ledger[0]) if ledger else
              ['compound_id', 'name', 'flag', 'summary', 'source_url', 'evidence_type',
               'checked_date', 'quantity', 'unit', 'quantity_type', 'context'])
    write_csv(output / 'text_flags.csv', text_hits, list(text_hits[0]) if text_hits else
              ['compound_id', 'name', 'signal', 'interpretation', 'section', 'field', 'text', 'codes',
               'reference_number', 'source_name', 'source_url', 'snapshot_url', 'retrieved_at'])
    counts = {t: sum(r['triage'] == t for r in triage) for t in TRIAGE_ORDER}
    summary = ['# Preliminary dietary-candidate triage', '',
               'Rule-based research screening; not a safety or plant-activity assessment.', '',
               '| Triage | Count |', '| --- | ---: |']
    summary += [f'| {t} | {n} |' for t, n in counts.items()]
    summary += ['', '## Provisional shortlist', '',
                ', '.join(r['name'] for r in triage if r['triage'] == TRIAGE_ORDER[-1]) or 'None', '',
                'Lower review burden under this bounded policy, not proven benign at high doses.',
                'All high-dose and plant-activity labels remain unknown. A missing signal is not safety.',
                'CFR food checks use the 2025 edition; verify current text before acceptance.',
                'GHS codes are supplier/contributor handling leads, not dietary dose-response evidence.',
                'Text hits are unadjudicated: null findings, other exposures and historical contamination can match.',
                'See triage.csv, curated_leads.csv, text_flags.csv and pubchem_extracts.csv for context.', '',
                '## Review queue', '', '| Candidate | Triage | Flags / gaps |', '| --- | --- | --- |']
    summary += [f"| {r['name']} | {r['triage']} | {r['flags']} {r['evidence_gaps']} |" for r in triage]
    summary.append('')
    (output / 'README.md').write_text('\n'.join(summary))
    manifest = {'policy_id': rules['policy_id'], 'counts': counts, 'n': len(rows),
                'request_count': len(saved),
                'http_status_counts': {str(k): sum(s['status'] == k for s in saved.values())
                                       for k in sorted({s['status'] for s in saved.values()}, key = str)},
                'rows_with_gaps': sum(bool(r['evidence_gaps']) for r in triage),
                'text_flagged_candidates': len({r['compound_id'] for r in text_hits}),
                'input_hashes': hashes([review, policy, *paths]),
                'code_hashes': hashes([Path(__file__), HERE / 'screen.py']),
                'lock_hashes': hashes([HERE / 'uv.lock', HERE / 'pyproject.toml']),
                'output_hashes': hashes(list(output.iterdir())),
                'versions': {n: version(n) for n in ('requests', 'polars')},
                'scope': rules['scope']}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--review', type = Path, required = True)
    parser.add_argument('--snapshots', type = Path, required = True)
    parser.add_argument('--fetch', action = 'store_true')
    parser.add_argument('--output', type = Path)
    parser.add_argument('--policy', type = Path, default = POLICY)
    args = parser.parse_args()
    if args.fetch:
        fetch(args.review, args.snapshots)
    else:
        if args.output is None:
            parser.error('Offline triage requires --output')
        result = run(args.review, args.snapshots, args.output, args.policy)
        print(json.dumps(result['counts'], indent = 2))
