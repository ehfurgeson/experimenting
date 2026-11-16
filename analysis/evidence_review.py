"""Source-checked proposals and per-policy readiness, never scientific approval or fitting."""
import argparse
import json
import time
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

import polars as pl
import requests
from rdkit import Chem
from rdkit.Chem import Draw

from labels import LABEL_FIELDS, attach_labels
from screen import HERE, hashes, write_csv
from structure import structure_features
from weekly_report import verify_manifest

RESOURCE = HERE / 'resources/expansion_review.json'


def validate_resource(data, names):
    if set(data['origin_leads']) != set(names):
        raise ValueError('Preserve all literature leads exactly once in origin review')
    ids = {r['source_id'] for r in data['sources']}
    for lead in data['origin_leads'].values():
        if lead['proposal'] not in {'natural', 'unknown'} or not set(lead['sources']) <= ids:
            raise ValueError('Origin proposal requires known source references')
    named = data.get('named_structure_reconstructions', {})
    if named and set(named) != set(names):
        raise ValueError('Named structure reconstructions must cover the exact review cohort')
    for row in data['observations']:
        if row['study'] not in ids:
            raise ValueError('Every study observation requires a declared source')
        if row['name'] not in names or row['approval_state'] != 'unreviewed':
            raise ValueError('This workflow accepts unreviewed source observations only')
        if row['proposed_activity'] not in {'active', 'low_response', 'unknown'}:
            raise ValueError('Unknown proposed activity')
        policy = row['activity_policy']
        if policy and policy not in data['policies']:
            raise ValueError('Observation policy must be declared')
        if row['proposed_activity'] != 'unknown' and not policy:
            raise ValueError('Known proposal requires a bounded policy')
    if any(r['approval_state'] != 'unapproved' for r in data['policies'].values()):
        raise ValueError('Scientific approval cannot be assigned by this workflow')


def fetch(resource, output):
    resource, output = Path(resource).resolve(), Path(output).resolve()
    if output.exists() or resource.is_relative_to(output):
        raise ValueError('Use a new source directory separate from resource')
    data = json.loads(resource.read_text())
    output.mkdir(parents = True)
    (output / 'acquisition_resource.json').write_bytes(resource.read_bytes())
    requests_log = []
    for source in data['sources']:
        path = output / (source['source_id'] + '.' + source['kind'])
        url = source['url']
        try:
            response = requests.get(url, timeout = (10, 40))
            body = response.content
            if len(body) > 20_000_000:
                raise ValueError('Source exceeds bounded acquisition size')
            path.write_bytes(body)
            status = 'available' if response.status_code == 200 else 'http_access_gap'
            if source['kind'] == 'pdf' and not body.startswith(b'%PDF'):
                status = 'not_pdf_or_access_gap'
            if b'Checking your browser' in body[:30000]:
                status = 'browser_challenge'
            requests_log.append({'source_id': source['source_id'], 'url': url,
                                 'status': status, 'http_status': response.status_code,
                                 'file': path.name, 'retrieved_at': datetime.now(UTC).isoformat()})
        except (requests.RequestException, ValueError) as error:
            requests_log.append({'source_id': source['source_id'], 'url': url,
                                 'status': type(error).__name__, 'retrieved_at': datetime.now(UTC).isoformat()})
        time.sleep(.3)
    manifest = {'input_hashes': hashes([output / 'acquisition_resource.json']),
                'output_hashes': hashes(list(output.iterdir())), 'requests': requests_log,
                'scope': 'Public primary-source acquisition; access gaps are not evidence absence.'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2) + '\n')
    return manifest


def build(resource, literature, sources, output, holds = None):
    resource, literature, sources, output = [Path(p).resolve() for p in (resource, literature, sources, output)]
    if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output)
                              for p in (resource, literature, sources)):
        raise ValueError('Use a new output directory separate from source bundles')
    verify_manifest(literature / 'manifest.json')
    source_manifest = verify_manifest(sources / 'manifest.json')
    data = json.loads(resource.read_text())
    leads = pl.read_csv(literature / 'literature_evidence.csv').to_dicts()
    validate_resource(data, [r['name'] for r in leads])
    by_name = {r['name']: r for r in leads}
    features = {r['name']: structure_features(r['smiles']) for r in leads}
    source_index = {r['source_id']: r for r in data['sources']}
    source_status = {r['source_id']: r['status'] for r in source_manifest['requests']}
    observations = []
    for i, row in enumerate(data['observations']):
        observations.append({'observation_id': f'REVIEW20261111:{i+1:03d}',
                             'compound_id': by_name[row['name']]['compound_id'], **row})
    worksheets, packets = [], []
    for lead in leads:
        name = lead['name']
        origin = data['origin_leads'][name]
        chemistry = features[name]
        named = data.get('named_structure_reconstructions', {}).get(name, {})
        named_features = structure_features(named.get('smiles'))
        named_key = named_features.get('structure_inchikey')
        named_status = ('unavailable' if named_key is None else 'name_reconstruction_matches_database'
                        if named_key == lead['pubchem_inchikey'] else 'name_structure_identity_hold')
        worksheets.append({'compound_id': lead['compound_id'], 'name': name, 'axis': 'origin',
                           'proposed_policy': 'PROPOSED-EXACT-NATURAL-OCCURRENCE-v1',
                           'proposed_decision': origin['proposal'] if named_status != 'name_structure_identity_hold' else 'unknown', 'rationale': origin['reason'],
                           'source_locator': '; '.join(f'{s}: {source_index[s]["locator"]}' for s in origin['sources']),
                           'approval_state': 'unreviewed', 'reviewer': '', 'review_date': '',
                           'scientific_approval_reference': '', 'identity_status': named_status if named_status == 'name_structure_identity_hold' else 'source_structure_review_pending'})
        packets.append({'compound_id': lead['compound_id'], 'name': name,
                        'database_smiles': lead['smiles'], 'database_inchikey': lead['pubchem_inchikey'],
                        'stereochemistry': 'Specified E geometry requires source confirmation' if name in
                                           {'Sarmentine','trans-Cinnamic acid','trans-Cinnamaldehyde'}
                                           else 'No specified stereocenters in database identity; source form still pending',
                        'chemical_form': 'Database single-component form; tested free acid/ester/salt/formulation must be checked',
                        'source_structure_status': 'unapproved; original drawings/spectra not adjudicated',
                        'source_named_structure_smiles': named.get('smiles'),
                        'source_literal_name': named.get('source_name'),
                        'source_name_locator': named.get('locator'),
                        'named_structure_inchikey': named_key, 'named_structure_check': named_status,
                        'origin_proposal': origin['proposal'] if named_status != 'name_structure_identity_hold' else 'unknown', 'origin_rationale': origin['reason'],
                        'origin_sources': ';'.join(origin['sources']),
                        'source_access': ';'.join(s + '=' + source_status.get(s, 'not_acquired') for s in origin['sources']),
                        'structure_status': chemistry['structure_status'], 'scaffold': chemistry['scaffold'],
                        'accepted_natural_origin': 'unknown', 'accepted_activity': 'unknown'})
    grouped = defaultdict(list)
    for row in observations:
        if row['activity_policy']:
            grouped[row['compound_id'], row['activity_policy']].append(row)
    for (cid, policy), rows in sorted(grouped.items()):
        proposals = {r['proposed_activity'] for r in rows} - {'unknown'}
        proposed = next(iter(proposals)) if len(proposals) == 1 else 'unknown'
        held = any(p['name'] == rows[0]['name'] and p['named_structure_check'] == 'name_structure_identity_hold' for p in packets)
        if held:
            proposed = 'unknown'
        worksheets.append({'compound_id': cid, 'name': rows[0]['name'], 'axis': 'activity',
                           'proposed_policy': policy, 'proposed_decision': proposed,
                           'rationale': data['policies'][policy]['scope'],
                           'source_locator': ';'.join(sorted({r['study'] + ': ' + r['locator'] for r in rows})),
                           'approval_state': 'unreviewed', 'reviewer': '', 'review_date': '',
                           'scientific_approval_reference': '', 'identity_status': 'name_structure_identity_hold' if held else 'source_structure_review_pending'})
    readiness = []
    for policy in data['policies']:
        proposed = [r for r in worksheets if r['axis'] == 'activity' and r['proposed_policy'] == policy]
        counts = Counter(r['proposed_decision'] for r in proposed)
        scaffolds = {label: {features[r['name']]['scaffold'] for r in proposed if
                            r['proposed_decision'] == label} for label in ('active','low_response')}
        readiness.append({'policy': policy, 'accepted_active': 0, 'accepted_low_response': 0,
                          'proposed_active': counts['active'], 'proposed_low_response': counts['low_response'],
                          'proposed_unknown': counts['unknown'], 'active_scaffolds': len(scaffolds['active']),
                          'low_response_scaffolds': len(scaffolds['low_response']),
                          'five_fold_proposed_support': min(counts['active'], counts['low_response'],
                              len(scaffolds['active']),len(scaffolds['low_response'])) >= 5,
                          'status': 'unapproved_labels_no_models_fitted'})
    labels = [{'compound_id': r['compound_id'], 'natural_origin': 'unknown', 'origin_reference': '',
               'herbicidal_activity': 'unknown', 'activity_reference': '', 'activity_context': '',
               'activity_policy': ''} for r in leads]
    attach_labels([{'compound_id': r['compound_id']} for r in leads], labels)
    output.mkdir(parents = True)
    write_csv(output / 'compound_packets.csv', packets, list(packets[0]))
    write_csv(output / 'study_observations.csv', observations, list(observations[0]))
    write_csv(output / 'approval_worksheet.csv', worksheets, list(worksheets[0]))
    write_csv(output / 'reviewed_labels.csv', labels, ['compound_id', *sorted(LABEL_FIELDS-{'compound_id'})])
    pl.DataFrame(readiness).write_csv(output / 'policy_readiness.csv')
    (output / 'policy_proposals.json').write_text(json.dumps(data['policies'], indent = 2) + '\n')
    (output / 'source_index.json').write_text(json.dumps(data['sources'], indent = 2) + '\n')
    if holds:
        holds = Path(holds).resolve()
        # Copy the exact immutable hold evidence; never rewrite historical labels.
        (output / 'preserved_identity_holds.csv').write_bytes(holds.read_bytes())
    mols = [Chem.MolFromSmiles(r['smiles']) for r in leads]
    drawing = Draw.MolsToGridImage(mols, molsPerRow = 3, subImgSize = (300,200),
                                  legends = [r['name'] for r in leads], useSVG = True)
    (output / 'database_structure_reference.svg').write_text(str(drawing))
    (output / 'README.md').write_text(
        '# Compound evidence review\n\nAll 15 leads and all proposed policies remain unapproved. '
        'The 81 extracted study/condition observations are not interchangeable activity labels.\n\n'
        'Start with `approval_worksheet.csv`, consult `compound_packets.csv`, `study_observations.csv`, '
        '`source_index.json` and `policy_proposals.json`. Structure drawings depict database SMILES, '
        'not verified paper structures. All seven-column accepted labels remain unknown.\n\n'
        'Priority checks: sarmentine 10/20 mg/mL conflict; source free acid versus ester; '
        'ortho/para and beta-resorcylic isomer mapping; source melting-point/spectral consistency; '
        '2020 water-control mortality; 2024 formulation/site/dose dependence. No fitting is performed.\n')
    inputs = [resource, literature / 'manifest.json', sources / 'manifest.json', *([holds] if holds else [])]
    manifest = {'input_hashes': hashes(inputs), 'code_hashes': hashes([Path(__file__), HERE / 'labels.py', HERE / 'structure.py']),
                'lock_hashes': hashes([HERE / 'uv.lock']), 'output_hashes': hashes(list(output.iterdir())),
                'counts': {'compounds': len(packets), 'observations': len(observations), 'worksheet_rows': len(worksheets),
                           'named_structure_matches': sum(r['named_structure_check'] == 'name_reconstruction_matches_database' for r in packets)},
                'accepted_origin_labels': 0, 'accepted_activity_labels': 0, 'models_fitted': 0,
                'policy_support': readiness}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--resource', type = Path, default = RESOURCE)
    commands = parser.add_subparsers(dest = 'command', required = True)
    acquire = commands.add_parser('fetch')
    acquire.add_argument('--output', type = Path, required = True)
    prepare = commands.add_parser('build')
    for key in ('literature','sources','output'):
        prepare.add_argument('--' + key, type = Path, required = True)
    prepare.add_argument('--holds', type = Path)
    args = parser.parse_args()
    result = fetch(args.resource, args.output) if args.command == 'fetch' else build(
        args.resource, args.literature, args.sources, args.output, args.holds)
    print(json.dumps(result.get('counts', result.get('requests')), indent = 2))
