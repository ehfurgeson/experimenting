"""Offline EPA-first acute rat oral LD50 pilot with explicit sampling limits."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

import altair as alt
import numpy as np
from agrotox.epa_hazard import hazard_table, normalize_hazards

from labels import attach_labels
from screen import HERE, hashes, read_records, write_csv


def text(value):
    value = str(value or '').strip().casefold()
    return '' if value in {'-', 'nr', 'unknown', 'not specified'} else value


def summarize(hazards, crosswalk, traits, labels = ()):
    """Inventory source chemicals first, then attach approved identities and groups."""
    metadata = {r['compound_id']: r for r in attach_labels(traits, labels)}
    approved = {(r['compound_id'], r['dtxsid']) for r in crosswalk if r['status'] == 'approved'}
    normalized = normalize_hazards(hazard_table(hazards)).to_dicts()
    inventory, evidence, values, bounds, seen = {}, [], defaultdict(list), Counter(), set()
    for raw, row in zip(hazards, normalized, strict = True):
        cid = raw['compound_id']
        info = metadata.get(cid, {})
        key = (cid, raw.get('dtxsid'))
        item = inventory.setdefault(key, {
            'compound_id': cid, 'dtxsid': raw.get('dtxsid'), 'query': info.get('query'),
            'identity_approved': key in approved, 'in_selection': cid in metadata,
            'selection_group': info.get('chemical_group'), 'source_records': 0,
            'natural_origin': info.get('natural_origin') or 'unknown',
            'herbicidal_activity': info.get('herbicidal_activity') or 'unknown'})
        item['source_records'] += 1
        reasons = []
        if key not in approved:
            reasons.append('identity_not_approved')
        if row['endpoint'] != 'LD50':
            reasons.append('not_ld50')
        if row['species'] not in {'rattus norvegicus', 'rat', 'rats'}:
            reasons.append('not_explicit_rat')
        if row['exposure_route'] != 'oral':
            reasons.append('not_oral')
        if row['study_type'] != 'acute':
            reasons.append('not_explicit_acute')
        if row['parse_status'] != 'complete' or row['unit_standardized'] != 'mg/kg':
            reasons.append('not_eligible_measured_dose')
        reference = text(raw.get('doi')).removeprefix('https://doi.org/').removeprefix('doi:')
        reference = reference or text(raw.get('reference'))
        # Same reference, exposure context and result are duplicate reports, not new votes.
        # Without a reference, collapse only exact records within a named source.
        locator = reference or (text(raw.get('source')), text(raw.get('source_hash')),
                                text(raw.get('external_source_id')),
                                json.dumps(raw, sort_keys = True, default = str))
        study = (cid, str(locator), row['species'], row['exposure_route'],
                 row['study_type'], row['duration_hours'], text(raw.get('strain')),
                 text(raw.get('sex')), text(raw.get('lifestage')),
                 text(raw.get('exposure_method')), text(raw.get('exposure_form')),
                 row['qualifier'], row['value_standardized'])
        status = 'excluded' if reasons else 'duplicate' if study in seen else (
            'exact' if row['qualifier'] == '=' else 'censored')
        if not reasons:
            seen.add(study)
        if status == 'exact':
            values[cid].append(row['value_standardized'])
        elif status == 'censored':
            bounds[cid] += 1
        evidence.append({
            'compound_id': cid, 'annotation_id': row['annotation_id'], 'status': status,
            'reasons': ';'.join(reasons), 'species': row['species'],
            'route': row['exposure_route'], 'study_type': row['study_type'],
            'qualifier': row['qualifier'], 'value_mg_kg': row['value_standardized'],
            'reference': raw.get('reference'), 'doi': raw.get('doi'),
            'source': raw.get('source'), 'source_url': raw.get('source_url'),
            'source_hash': raw.get('source_hash'), 'dtxsid': raw.get('dtxsid'),
            'reference_missing': not bool(reference),
            'context_json': json.dumps(raw, sort_keys = True, default = str)})
    summaries = []
    for cid in sorted(set(values) | set(bounds)):
        info = metadata.get(cid, {})
        origin, activity = info.get('natural_origin'), info.get('herbicidal_activity')
        group = ('natural_active' if origin == 'natural' and activity == 'active' else
                 'natural_tested_low_response' if origin == 'natural' and activity == 'inactive'
                 else 'selected_herbicide' if info.get('chemical_group') == 'herbicide'
                 else 'unreviewed_natural_product_selection'
                 if info.get('chemical_group') == 'natural_product' else 'unreviewed_source_chemical')
        exact = values[cid]
        summaries.append({'compound_id': cid, 'query': info.get('query'), 'group': group,
                          'exact_records': len(exact), 'censored_records': bounds[cid],
                          'median_mg_kg': median(exact) if exact else None,
                          'min_mg_kg': min(exact) if exact else None,
                          'max_mg_kg': max(exact) if exact else None,
                          'discordant_exact_values': len(set(exact)) > 1,
                          'ld50_bin': None})
    medians = [r['median_mg_kg'] for r in summaries if r['median_mg_kg'] is not None]
    cutoffs = [float(v) for v in np.quantile(medians, [1 / 3, 2 / 3], method = 'linear')] if medians else []
    for row in summaries:
        value = row['median_mg_kg']
        if value is not None:
            row['ld50_bin'] = 'low' if value <= cutoffs[0] else 'medium' if value <= cutoffs[1] else 'high'
    bin_counts = Counter((r['group'], r['ld50_bin']) for r in summaries if r['ld50_bin'])
    groups = []
    for group in sorted({r['group'] for r in summaries}):
        denominator = sum(n for (g, b), n in bin_counts.items() if g == group)
        for bucket in ('low', 'medium', 'high'):
            count = bin_counts[group, bucket]
            groups.append({'group': group, 'ld50_bin': bucket, 'compounds': count,
                           'exact_compound_denominator': denominator,
                           'proportion': count / denominator if denominator else None})
    return {'inventory': sorted(inventory.values(), key = lambda r: (r['compound_id'], r['dtxsid'] or '')),
            'evidence': evidence, 'compounds': summaries, 'groups': groups,
            'policy': {'endpoint': 'acute rat oral LD50', 'unit': 'mg/kg',
                       'cutoffs': cutoffs, 'quantile_method': 'linear',
                       'collapsed_cutoffs': bool(cutoffs and cutoffs[0] == cutoffs[1]),
                       'bin_status': 'available' if medians else 'no_exact_compounds',
                       'lower_ld50': 'greater toxicity',
                       'deduplication': 'same reference, compound, context, qualifier and value; '
                                        'missing references only exact same-source records',
                       'limits': 'Purposive cached selection, not population discovery. Compound '
                                 'medians summarize retained acute contexts, not a pooled risk estimate. '
                                 'Potential study duplicates with different references remain unresolved.'}}


def run(hazards, crosswalk, traits, output, labels = None):
    inputs = [Path(p).resolve() for p in (hazards, crosswalk, traits)]
    if labels:
        inputs.append(Path(labels).resolve())
    output = Path(output).resolve()
    if any(p.is_relative_to(output) or output.is_relative_to(p.parent) for p in inputs):
        raise ValueError('Output must be separate from input directories')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use an empty output directory')
    result = summarize(*(read_records(p) for p in inputs[:3]),
                       labels = read_records(inputs[3]) if labels else [])
    output.mkdir(parents = True, exist_ok = True)
    columns = {
        'inventory': ['compound_id', 'dtxsid', 'query', 'identity_approved', 'in_selection',
                      'selection_group', 'source_records', 'natural_origin', 'herbicidal_activity'],
        'evidence': ['compound_id', 'annotation_id', 'status', 'reasons', 'species', 'route',
                     'study_type', 'qualifier', 'value_mg_kg', 'reference', 'doi', 'source',
                     'source_url', 'source_hash', 'dtxsid', 'reference_missing', 'context_json'],
        'compounds': ['compound_id', 'query', 'group', 'exact_records', 'censored_records',
                      'median_mg_kg', 'min_mg_kg', 'max_mg_kg', 'discordant_exact_values', 'ld50_bin'],
        'groups': ['group', 'ld50_bin', 'compounds', 'exact_compound_denominator', 'proportion']}
    for key, fields in columns.items():
        write_csv(output / f'{key}.csv', result[key], fields)
    plotted = [r for r in result['compounds'] if r['median_mg_kg'] is not None]
    if plotted:
        chart = alt.Chart(alt.Data(values = plotted)).mark_circle(size = 70).encode(
            x = alt.X('median_mg_kg:Q', scale = alt.Scale(type = 'log'),
                      title = 'Acute rat oral LD50 (mg/kg); lower = greater toxicity'),
            y = alt.Y('group:N', title = 'Evidence / selection group'),
            tooltip = ['query:N', 'median_mg_kg:Q', 'exact_records:Q', 'censored_records:Q'],
            color = 'ld50_bin:N').properties(width = 650, height = 180,
                                             title = 'Exploratory cached EPA comparison')
        chart.save(output / 'ld50_distribution.html')
        chart.save(output / 'ld50_distribution.svg')
        bins = alt.Chart(alt.Data(values = result['groups'])).mark_bar().encode(
            x = alt.X('proportion:Q', title = 'Proportion of compounds with exact values'),
            y = 'group:N', color = alt.Color('ld50_bin:N', sort = ['low', 'medium', 'high']),
            tooltip = ['group:N', 'ld50_bin:N', 'compounds:Q', 'exact_compound_denominator:Q'])
        bins.properties(width = 650, height = 180, title = 'Pooled exploratory LD50 tertiles').save(
            output / 'ld50_bins.svg')
    manifest = {'input_hashes': hashes(inputs),
                'code_hashes': hashes([Path(__file__), HERE / 'labels.py']),
                'lock_hashes': hashes([HERE / 'uv.lock', HERE / 'pyproject.toml']),
                'output_hashes': hashes(list(output.iterdir())), 'policy': result['policy'],
                'counts': {k: len(result[k]) for k in columns},
                'record_status': dict(Counter(r['status'] for r in result['evidence'])),
                'outside_selection': sum(not r['in_selection'] for r in result['inventory'])}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2, allow_nan = False) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for name in ('hazards', 'crosswalk', 'traits', 'output'):
        parser.add_argument(f'--{name}', type = Path, required = True)
    parser.add_argument('--labels', type = Path)
    args = parser.parse_args()
    print(json.dumps(run(args.hazards, args.crosswalk, args.traits, args.output, args.labels), indent = 2))
