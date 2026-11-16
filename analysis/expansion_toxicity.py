"""Cross-source study review and conservative LD50 sensitivity; no inferred duplicates."""
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

import altair as alt
import numpy as np
import polars as pl

from screen import HERE, hashes, write_csv
from weekly_report import verify_manifest
from weekly_toxicity import text


def compatible_bins(value, qualifier, cutoffs = (1080., 3400.)):
    if value is None or not np.isfinite(value) or value <= 0:
        raise ValueError('Positive finite bound required')
    a, b = cutoffs
    if not 0 < a < b:
        raise ValueError('Require ordered positive cutoffs')
    if qualifier == '=':
        return ['low' if value <= a else 'medium' if value <= b else 'high']
    if qualifier in {'>', '>='}:
        low = value < a if qualifier == '>' else value <= a
        middle = value < b if qualifier == '>' else value <= b
        return (['low'] if low else []) + (['medium'] if middle else []) + ['high']
    if qualifier in {'<', '<='}:
        return ['low'] + (['medium'] if value > a else []) + (['high'] if value > b else [])
    raise ValueError('Unsupported inequality')


def publication(doi, title):
    doi = (doi or '').strip().casefold()
    match = re.search(r'10\.\d{4,9}/[^\s]+', doi)
    if match:
        return 'doi:' + match[0].rstrip('.,;')
    title = re.sub(r'\W+', ' ', (title or '').casefold()).strip()
    return 'title:' + title if len(title) >= 20 else None


def overlap_queue(epa, native, measurements, candidates):
    index, candidate_ids = defaultdict(list), {}
    for row in epa:
        raw = json.loads(row['context_json'])
        key = publication(row['doi'], raw.get('title'))
        if key:
            index[row['compound_id'], key].append(row)
    for row in candidates:
        candidate_ids[row['source_chemical_id']] = row.get('candidate_compound_ids', '').split(';')
    by_result = {r['source_result_id']: r for r in native}
    queue = []
    for row in measurements:
        source = by_result[row['source_result_id']]
        ref = json.loads(source['reference_json'])
        key = publication(ref.get('doi'), ref.get('title'))
        if not key:
            continue
        for cid in candidate_ids.get(row['source_chemical_id'], []):
            for other in index.get((cid, key), []):
                raw = json.loads(other['context_json'])
                match = {'species_match': other['species'] == row['species'],
                         'endpoint_match': raw.get('toxval_type') == row['endpoint'],
                         'route_match': (other['route'] == 'oral' and row['exposure_type'] in {'OR', 'UN'}),
                         'duration_match': False,
                         'result_match': other['value_mg_kg'] is not None and row['value'] is not None and
                                         other['value_mg_kg'] == row['value'] and
                                         other['qualifier'] == row['qualifier'] and
                                         row['unit_standardized'] == 'mg/kg'}
                # Missing duration cannot establish equality; keep an explicit unknown flag.
                duration = raw.get('study_duration_value')
                if isinstance(duration, (int, float)) and duration > 0 and raw.get('study_duration_units') in {'h', 'd'}:
                    hours = duration * (24 if raw['study_duration_units'] == 'd' else 1)
                    match['duration_match'] = hours == row['duration_hours']
                queue.append({'pair_id': other['annotation_id'] + '|' + row['measurement_id'],
                              'left_id': other['annotation_id'], 'right_id': row['measurement_id'],
                              'compound_id_hint': cid, 'identity_link_status': row['identity_status'],
                              'publication_key': key, **match, 'decision': 'unreviewed',
                              'retain_id': '', 'reviewer': '', 'review_date': '', 'decision_reference': ''})
    # Within-source same-publication/context/result pairs also require adjudication.
    seen = defaultdict(list)
    for row in epa:
        raw = json.loads(row['context_json'])
        pub = publication(row['doi'], raw.get('title'))
        if not pub:
            continue
        key = (row['compound_id'], pub, row['species'], row['route'], raw.get('toxval_type'),
               row['qualifier'], row['value_mg_kg'])
        for other in seen[key]:
            if other['annotation_id'] == row['annotation_id']:
                continue
            queue.append({'pair_id': other['annotation_id'] + '|' + row['annotation_id'],
                          'left_id': other['annotation_id'], 'right_id': row['annotation_id'],
                          'compound_id_hint': row['compound_id'], 'identity_link_status': 'existing_epa_approved',
                          'publication_key': pub, 'species_match': True, 'endpoint_match': True,
                          'route_match': True, 'duration_match': False, 'result_match': True,
                          'decision': 'unreviewed', 'retain_id': '', 'reviewer': '', 'review_date': '',
                          'decision_reference': ''})
        seen[key].append(row)
    for row in queue:
        row['match_count'] = sum(row[k] for k in ('species_match', 'endpoint_match', 'route_match', 'duration_match', 'result_match'))
    return sorted({r['pair_id']: r for r in queue}.values(),
                  key = lambda r: (-r['match_count'], r['pair_id']))


def duplicate_exclusions(queue, decisions):
    pairs = {r['pair_id']: r for r in queue}
    dropped, retained, seen = set(), set(), set()
    for decision in decisions:
        key = decision.get('pair_id')
        if key not in pairs or key in seen:
            raise ValueError('Duplicate decisions require known unique pair IDs')
        seen.add(key)
        state = decision.get('decision')
        if state not in {'unreviewed', 'same_observation', 'different_observation', 'unresolved'}:
            raise ValueError('Unknown duplicate decision')
        if state in {'same_observation', 'different_observation'} and any(
                not decision.get(k, '').strip() for k in ('reviewer', 'review_date', 'decision_reference')):
            raise ValueError('Reviewed duplicate decisions require signed supporting evidence')
        if state == 'same_observation':
            pair = pairs[key]
            if pair['identity_link_status'] not in {'approved', 'existing_epa_approved'}:
                raise ValueError('Source identity approval required before cross-source collapse')
            keep = decision.get('retain_id')
            if keep not in {pair['left_id'], pair['right_id']}:
                raise ValueError('Retain an explicitly named pair member')
            dropped.add(pair['right_id'] if keep == pair['left_id'] else pair['left_id'])
            retained.add(keep)
    if retained & dropped:
        raise ValueError('Conflicting duplicate retention decisions')
    return dropped


def adopt_duplicate_decisions(queue, decisions):
    """Validate decisions before copying signed review fields into the exported queue."""
    if len({r['pair_id'] for r in queue}) != len(queue):
        raise ValueError('Overlap queue requires unique pair IDs')
    duplicate_exclusions(queue, decisions)
    by_id = {r['pair_id']: r for r in decisions}
    fields = ('decision', 'retain_id', 'reviewer', 'review_date', 'decision_reference')
    return [{**row, **{key: by_id[row['pair_id']].get(key, '') for key in fields}}
            if row['pair_id'] in by_id else dict(row) for row in queue]


def scenario(rows, name, cutoffs):
    grouped = defaultdict(list)
    for row in rows:
        if row['status'] == 'exact':
            grouped[row['compound_id']].append(row['value_mg_kg'])
    compounds = [{'scenario': name, 'compound_id': cid, 'exact_records': len(vals),
                  'median_mg_kg': median(vals), 'study_value_min': min(vals), 'study_value_max': max(vals),
                  'fixed_bin': compatible_bins(median(vals), '=', cutoffs)[0]}
                 for cid, vals in sorted(grouped.items())]
    medians = [r['median_mg_kg'] for r in compounds]
    return compounds, {'scenario': name, 'exact_records': sum(len(v) for v in grouped.values()),
                       'compounds': len(compounds), 'fixed_cutoffs': list(cutoffs),
                       'cohort_tertiles': [float(v) for v in np.quantile(medians, [1/3, 2/3])]
                                         if medians else [],
                       'status': 'descriptive' if medians else 'insufficient_documented_context'}


def run(baseline, ecotox, crosswalk, output, decisions = None):
    baseline, ecotox, crosswalk, output = [Path(p).resolve() for p in (baseline, ecotox, crosswalk, output)]
    if output.exists() or any(p.is_relative_to(output) or output.is_relative_to(p) for p in (baseline, ecotox, crosswalk)):
        raise ValueError('Use a new output directory separate from inputs')
    base = verify_manifest(baseline / 'manifest.json')
    verify_manifest(ecotox / 'manifest.json')
    cutoffs = base['policy']['cutoffs']
    if cutoffs != [1080., 3400.]:
        raise ValueError('Historical cutoffs must remain 1080/3400 mg/kg')
    evidence = pl.read_csv(baseline / 'evidence.csv', infer_schema_length = None).to_dicts()
    native = pl.read_parquet(ecotox / 'native_observations.parquet').to_dicts()
    measures = pl.read_parquet(ecotox / 'measurements.parquet').to_dicts()
    candidates = pl.read_csv(crosswalk, infer_schema = False).fill_null('').to_dicts()
    queue = overlap_queue(evidence, native, measures, candidates)
    review = pl.read_csv(decisions, infer_schema = False).fill_null('').to_dicts() if decisions else []
    queue = adopt_duplicate_decisions(queue, review)
    dropped = duplicate_exclusions(queue, review)
    resolved = {r['pair_id'] for r in review if r['decision'] in {'same_observation', 'different_observation'}}
    pending = {r[k] for r in queue if r['pair_id'] not in resolved for k in ('left_id', 'right_id')} - dropped
    eligible = [r for r in evidence if r['status'] in {'exact', 'censored'}]
    missingness, documented = Counter(), []
    for row in eligible:
        raw = json.loads(row['context_json'])
        missing = [k for k in ('reference', 'strain', 'sex') if not text(raw.get(k))]
        if not isinstance(raw.get('study_duration_value'), (int, float)) or raw['study_duration_value'] <= 0 or raw.get('study_duration_units') not in {'h', 'd'}:
            missing.append('explicit_elapsed_duration')
        missingness.update(missing)
        if not missing:
            documented.append(row)
    all_compounds, scenarios = [], []
    for name, rows in [('historical_exact', eligible),
                       ('reviewed_duplicate_decisions', [r for r in eligible if r['annotation_id'] not in dropped]),
                       ('exclude_unresolved_overlap_candidates', [r for r in eligible if r['annotation_id'] not in pending | dropped]),
                       ('documented_context_only', [r for r in documented if r['annotation_id'] not in dropped])]:
        compounds, summary = scenario(rows, name, cutoffs)
        all_compounds.extend(compounds)
        scenarios.append(summary)
    bounds = [{'annotation_id': r['annotation_id'], 'compound_id': r['compound_id'],
               'qualifier': r['qualifier'], 'bound_mg_kg': r['value_mg_kg'],
               'compatible_bins': ';'.join(compatible_bins(r['value_mg_kg'], r['qualifier'], cutoffs)),
               'scope': 'individual study observation; not compound-median assignment'}
              for r in eligible if r['status'] == 'censored']
    output.mkdir(parents = True)
    queue_columns = ['pair_id', 'left_id', 'right_id', 'compound_id_hint', 'identity_link_status',
                     'publication_key', 'species_match', 'endpoint_match', 'route_match', 'duration_match',
                     'result_match', 'match_count', 'decision', 'retain_id', 'reviewer', 'review_date', 'decision_reference']
    write_csv(output / 'study_overlap_review.csv', queue, queue_columns)
    write_csv(output / 'censored_bins.csv', bounds, ['annotation_id', 'compound_id', 'qualifier',
              'bound_mg_kg', 'compatible_bins', 'scope'])
    pl.DataFrame(all_compounds).write_csv(output / 'sensitivity_compounds.csv')
    pl.DataFrame([{'field': k, 'missing_records': v, 'eligible_records': len(eligible)}
                  for k, v in sorted(missingness.items())]).write_csv(output / 'context_missingness.csv')
    points = [{'compound_id': r['compound_id'], 'value_mg_kg': r['value_mg_kg'],
               'qualifier': r['qualifier'], 'status': r['status']} for r in eligible]
    figure = alt.Chart(alt.Data(values = points)).mark_point(size = 65).encode(
        x = alt.X('value_mg_kg:Q', scale = alt.Scale(type = 'log'), title = 'Rat oral LD50 or bound (mg/kg)'),
        y = alt.Y('compound_id:N', title = 'Compound'), color = 'status:N', shape = 'qualifier:N',
        tooltip = ['compound_id:N', 'qualifier:N', 'value_mg_kg:Q']).properties(
            width = 720, height = 650, title = 'Individual observations; inequalities are bounds, not point estimates')
    figure.save(output / 'study_values.svg')
    chart = alt.Chart(alt.Data(values = [{'field': k, 'missing': v} for k,v in missingness.items()])).mark_bar().encode(
        x = 'missing:Q', y = 'field:N').properties(width = 550, title = 'Missing context among eligible rat oral observations')
    chart.save(output / 'missingness.svg')
    admission = pl.read_parquet(ecotox / 'admission.parquet')
    summary = admission.group_by('policy').agg(pl.len().alias('candidate_slots'),
        pl.col('source_context_eligible').sum().alias('source_context_eligible_slots'),
        pl.col('canonical_comparison_eligible').sum().alias('approved_identity_slots'))
    summary.write_csv(output / 'aquatic_policy_summary.csv')
    # Preserve exposure basis strata; no potency pooling across slots or nominal/measured exposure.
    m = pl.read_parquet(ecotox / 'measurements.parquet')
    strata = admission.filter(pl.col('source_context_eligible')).join(m, on = 'measurement_id', suffix = '_measurement').group_by(
        'policy', 'chemical_analysis', 'concentration_type').agg(
            pl.len().alias('slots'), pl.col('source_result_id').n_unique().alias('distinct_results'))
    strata.write_csv(output / 'aquatic_exposure_strata.csv')
    inputs = [baseline / 'manifest.json', ecotox / 'manifest.json', crosswalk,
              *([Path(decisions).resolve()] if decisions else [])]
    manifest = {'input_hashes': hashes(inputs),
                'code_hashes': hashes([Path(__file__), HERE / 'weekly_toxicity.py', HERE / 'weekly_report.py']),
                'lock_hashes': hashes([HERE / 'uv.lock']), 'output_hashes': hashes(list(output.iterdir())),
                'scenarios': scenarios, 'overlap_pairs': len(queue), 'documented_duplicate_exclusions': sorted(dropped),
                'censored_observations': len(bounds), 'approved_ecotox_identities': 0 if not any(r['compound_id'] for r in measures) else len({r['compound_id'] for r in measures if r['compound_id']}),
                'limits': 'Overlap is a review lead, not duplicate proof. No automatic merging. '
                          'Rat oral cutoffs stay frozen; new-cohort tertiles are separate. '
                          'Aquatic context eligibility is not canonical identity approval or a safety claim.'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for key in ('baseline', 'ecotox', 'crosswalk', 'output'):
        parser.add_argument('--' + key, type = Path, required = True)
    parser.add_argument('--decisions', type = Path)
    args = parser.parse_args()
    result = run(args.baseline, args.ecotox, args.crosswalk, args.output, args.decisions)
    print(json.dumps({k: result[k] for k in ('scenarios','overlap_pairs','censored_observations')}, indent = 2))
