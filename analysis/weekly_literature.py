"""Acquire identity leads explicitly, then build an offline literature pilot."""
import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import altair as alt
import numpy as np
import requests
from agrotox.sources.pubchem import PubChemClient

from screen import HERE, hashes, read_records, write_csv
from structure import structure_features

DEFAULT_RESOURCE = HERE / 'resources/weekly_literature.json'
DESCRIPTORS = ['mw', 'logp', 'tpsa', 'hbd', 'hba', 'halogen_present']


def resource_from(path):
    data = json.loads(Path(path).read_text())
    sources = {r['source_id'] for r in data['sources']}
    names = [r['name'] for r in data['compounds']]
    if len(names) != len(set(names)) or any(not n for n in names):
        raise ValueError('Compound names must be nonempty and unique')
    if any(r['source_id'] not in sources for r in data['compounds']):
        raise ValueError('Every compound requires a known source')
    return data


def fetch(resource, snapshots):
    data = resource_from(resource)
    snapshots = Path(snapshots).resolve()
    if snapshots.exists() and any(snapshots.iterdir()):
        raise ValueError('Use an empty snapshots directory')
    snapshots.mkdir(parents = True, exist_ok = True)
    resource_copy = snapshots / 'acquisition_resource.json'
    resource_copy.write_bytes(Path(resource).read_bytes())
    client = PubChemClient(retries = 1)
    inventory = []
    for i, row in enumerate(data['compounds']):
        try:
            payload = client.properties(client.resolve(row['name']))
            status = 'resolved' if payload else 'not_found'
        except (requests.RequestException, ValueError, LookupError) as error:
            payload, status = None, type(error).__name__
        record = {'name': row['name'], 'retrieved_at': datetime.now(UTC).isoformat(),
                  'status': status, 'payload': payload}
        path = snapshots / f'identity_{i:02d}.json'
        path.write_text(json.dumps(record, indent = 2) + '\n')
        inventory.append({'file': path.name, 'name': row['name'], 'status': status})
    for source in data['sources']:
        # Preserve response status and bytes even when a publisher denies automated retrieval.
        try:
            response = requests.get(source['url'], timeout = (10, 40))
            path = snapshots / f"{source['source_id']}.html"
            path.write_bytes(response.content)
            inventory.append({'file': path.name, 'url': source['url'],
                              'status': response.status_code,
                              'retrieved_at': datetime.now(UTC).isoformat()})
        except requests.RequestException as error:
            inventory.append({'url': source['url'], 'status': type(error).__name__})
    manifest = {'input_hashes': hashes([resource_copy]), 'requests': inventory,
                'output_hashes': hashes(list(snapshots.iterdir()))}
    (snapshots / 'manifest.json').write_text(json.dumps(manifest, indent = 2) + '\n')
    return manifest


def build_rows(data, snapshots):
    candidates = {r['name']: r for r in data['compounds']}
    rows, features = [], []
    for path in sorted(Path(snapshots).glob('identity_*.json')):
        saved = json.loads(path.read_text())
        if saved['name'] not in candidates:
            raise ValueError('Snapshot is outside the supplied literature resource')
        seed = candidates[saved['name']]
        payload = saved['payload'] or {}
        properties = payload.get('PropertyTable', {}).get('Properties', [])
        prop = properties[0] if len(properties) == 1 else {}
        chemistry = structure_features(prop.get('SMILES'))
        key_match = bool(prop.get('InChIKey') and
                         prop['InChIKey'] == chemistry.get('structure_inchikey'))
        cid = prop.get('CID')
        row = {**seed, 'compound_id': f'PUBCHEM:{cid}' if cid else None,
               'pubchem_inchikey': prop.get('InChIKey'), 'smiles': prop.get('SMILES'),
               'identity_status': 'database_key_agrees_source_unverified' if key_match
                                  else 'unresolved_or_key_mismatch',
               'natural_origin': 'unknown', 'herbicidal_activity': 'unknown',
               'review_status': 'unapproved_primary_source_screen'}
        rows.append(row)
        if key_match and chemistry['structure_status'] == 'valid':
            features.append({**row, **chemistry,
                             'halogen_present': int(any(chemistry.get(f'formula_{e}_count', 0)
                                                        for e in ('F', 'Cl', 'Br', 'I'))),
                             'group': 'literature_lead_unapproved'})
    if Counter(r['name'] for r in rows) != Counter(candidates.keys()):
        raise ValueError('Require exactly one snapshot per literature compound')
    return rows, features


def run(resource, snapshots, selection, output):
    resource, snapshots, selection, output = [Path(p).resolve() for p in
                                            (resource, snapshots, selection, output)]
    if output == snapshots or output.is_relative_to(snapshots) or snapshots.is_relative_to(output):
        raise ValueError('Output must be separate from snapshots')
    if any(p.is_relative_to(output) for p in (resource, selection)):
        raise ValueError('Output must be separate from inputs')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use an empty output directory')
    data = resource_from(resource)
    rows, leads = build_rows(data, snapshots)
    lead_keys = {r['structure_inchikey'] for r in leads}
    comparators, seen, overlap = [], set(), []
    for record in read_records(selection):
        if record.get('selection_target') != 1 or record.get('structure_status') != 'valid':
            continue
        key = record['structure_inchikey']
        if key in lead_keys:
            overlap.append(record['compound_id'])
            continue
        if key not in seen:
            comparators.append({**record, 'name': record.get('query'),
                                'group': 'selected_herbicide',
                                'halogen_present': int(any(record.get(f'formula_{e}_count', 0)
                                                           for e in ('F', 'Cl', 'Br', 'I')))})
            seen.add(key)
    # One structure per descriptive group, even if source names alias.
    unique_leads = {r['structure_inchikey']: r for r in leads}
    features = list(unique_leads.values()) + comparators
    summaries, points = [], []
    for group in ('literature_lead_unapproved', 'selected_herbicide'):
        for feature in DESCRIPTORS:
            values = [r[feature] for r in features if r['group'] == group and
                      isinstance(r.get(feature), (int, float)) and np.isfinite(r[feature])]
            quantiles = np.quantile(values, [.25, .5, .75]) if values else [None] * 3
            summaries.append({'group': group, 'feature': feature, 'n': len(values),
                              'q1': quantiles[0], 'median': quantiles[1], 'q3': quantiles[2],
                              'prevalence': float(np.mean(values)) if values and
                                            feature == 'halogen_present' else None})
    for row in features:
        for feature in DESCRIPTORS:
            points.append({'compound_id': row['compound_id'], 'name': row.get('name'),
                           'group': row['group'], 'feature': feature, 'value': row.get(feature)})
    output.mkdir(parents = True, exist_ok = True)
    write_csv(output / 'literature_evidence.csv', rows, list(rows[0]))
    write_csv(output / 'descriptor_summary.csv', summaries, list(summaries[0]))
    write_csv(output / 'descriptor_points.csv', points,
              ['compound_id', 'name', 'group', 'feature', 'value'])
    (output / 'source_packets.json').write_text(json.dumps(data['sources'], indent = 2) + '\n')
    chart = alt.Chart(alt.Data(values = points)).mark_circle(opacity = .6).encode(
        x = alt.X('value:Q', title = 'Descriptor value (units differ by panel)'),
        y = alt.Y('group:N', title = None), tooltip = ['name:N', 'value:Q'], color = 'group:N')
    figure = chart.properties(width = 520, height = 70).facet(row = 'feature:N').resolve_scale(
        x = 'independent').properties(title = 'Provisional literature identities versus herbicide selection')
    figure.save(output / 'descriptors.svg')
    figure.save(output / 'descriptors.html')
    manifest = {'input_hashes': hashes([resource, selection, *snapshots.glob('*.json')]),
                'code_hashes': hashes([Path(__file__), HERE / 'structure.py', HERE / 'formula.py']),
                'lock_hashes': hashes([HERE / 'uv.lock', HERE / 'pyproject.toml']),
                'output_hashes': hashes(list(output.iterdir())),
                'counts': {'literature_names': len(rows), 'supported_unique_leads': len(unique_leads),
                           'selected_herbicides': len(comparators), 'sources': len(data['sources'])},
                'excluded_selection_overlaps': overlap, 'accepted_activity_labels': 0,
                'natural_negative_group': 'not_established',
                'model_readiness': 'No accepted activity/origin labels; no biological models fitted.',
                'scope': 'AI-assisted source screen and provisional database identities. '
                         'Descriptor groups do not establish accepted natural origin or activity.'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2, allow_nan = False) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--resource', type = Path, default = DEFAULT_RESOURCE)
    sub = parser.add_subparsers(dest = 'command', required = True)
    acquire = sub.add_parser('fetch')
    acquire.add_argument('--snapshots', type = Path, required = True)
    build = sub.add_parser('build')
    for name in ('snapshots', 'selection', 'output'):
        build.add_argument(f'--{name}', type = Path, required = True)
    args = parser.parse_args()
    result = fetch(args.resource, args.snapshots) if args.command == 'fetch' else run(
        args.resource, args.snapshots, args.selection, args.output)
    print(json.dumps(result, indent = 2, default = str))
