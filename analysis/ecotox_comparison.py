"""Identity-approved aquatic comparisons with separate contexts, bounds and rat review."""
import argparse
import html
import json
import shutil
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

import altair as alt
import polars as pl

from expansion_toxicity import duplicate_exclusions
from review_adoption import K1998, read_csv
from screen import HERE, hashes, write_csv
from weekly_report import verify_manifest

STRATA = ('policy', 'compound_id', 'chemical_analysis', 'concentration_type',
          'formulation_code', 'exposure_type', 'medium', 'exposure_hours')
MISSING = {'', 'NC', 'NR', 'NA', 'UKN', '--', '-'}


def identity_only_accounting(previous_native, native, previous_measures, measures):
    """Require identical scientific records; only identity attachment may change."""
    if not previous_native.equals(native):
        raise ValueError('Native source results changed during identity-only reimport')
    if not previous_measures.drop('compound_id', 'identity_status').equals(
            measures.drop('compound_id', 'identity_status')):
        raise ValueError('Scientific measurements changed during identity-only reimport')
    if measures['measurement_id'].n_unique() != measures.height or native['source_result_id'].n_unique() != native.height:
        raise ValueError('Unique result and slot identifiers required')
    if measures.filter(pl.col('compound_id').is_null() | (pl.col('identity_status') != 'approved')).height:
        raise ValueError('All selected mappings must be explicitly approved')
    return [{'grain': 'native_results', 'previous_rows': previous_native.height, 'approved_rows': native.height,
             'scientific_fields_unchanged': True},
            {'grain': 'concentration_slots', 'previous_rows': previous_measures.height,
             'approved_rows': measures.height, 'scientific_fields_unchanged': True}]


def group_for(cid, ledger, natural, selection):
    key = ledger[cid]['inchikey']
    label = natural.get(key)
    if label:
        return ('natural_active_K1998' if label['activity'] == 'active' else
                'natural_tested_low_response_K1998' if label['activity'] == 'inactive' else
                'natural_activity_unknown')
    group = selection.get(cid, {}).get('chemical_group')
    return ('selected_herbicide_comparator' if group == 'herbicide' else
            'unreviewed_natural_product_selection' if group == 'natural_product' else 'unreviewed_source_chemical')


def documented_context(row, test):
    gaps = []
    if row['exposure_type'] in MISSING:
        gaps.append('exposure_type_not_reported')
    if row['exposure_hours'] is None:
        gaps.append('exposure_duration_not_reported')
    elif row['exposure_hours'] != row['duration_hours']:
        gaps.append('exposure_and_observation_duration_differ')
    if (test.get('control_type') or '').strip() in MISSING:
        gaps.append('control_type_not_reported')
    return gaps


def summarize_strata(observations, excluded = (), documented_only = False):
    buckets = defaultdict(list)
    for row in observations:
        if row['measurement_id'] in excluded or documented_only and not row['reported_context_complete']:
            continue
        buckets[tuple(row[k] for k in STRATA)].append(row)
    summaries = []
    for key, rows in buckets.items():
        exact = [r['value'] for r in rows if r['qualifier'] == '=' and r['value'] is not None]
        summaries.append({**dict(zip(STRATA, key, strict = True)), 'name': rows[0]['name'],
            'group': rows[0]['group'], 'slots': len(rows),
            'distinct_results': len({r['source_result_id'] for r in rows}),
            'distinct_tests': len({r['test_id'] for r in rows}),
            'distinct_references': len({r['reference_number'] for r in rows}),
            'exact_slots': len(exact), 'bounded_or_range_slots': len(rows)-len(exact),
            'exact_record_median_mg_l': median(exact) if exact else None,
            'exact_record_min_mg_l': min(exact) if exact else None,
            'exact_record_max_mg_l': max(exact) if exact else None})
    return sorted(summaries, key = lambda r: tuple(str(r[k]) for k in STRATA))


def rat_review(row, source):
    test, result = json.loads(source['test_json']), json.loads(source['result_json'])
    prefix = f"conc{row['slot']}_"
    reasons = []
    if row['exposure_type'] not in {'GV', 'OR'}:
        reasons.append('not_explicit_gavage_or_oral_capsule')
    if test.get('test_type') != 'ACUTE':
        reasons.append('acute_test_type_not_explicit')
    if row['unit_standardized'] != 'mg/kg' or row['parse_status'] != 'complete':
        reasons.append('incomplete_or_unsupported_dose_parse')
    if row['concentration_type'] != 'A':
        reasons.append('not_active_ingredient_dose_basis')
    if row['duration_hours'] is None:
        reasons.append('elapsed_observation_duration_missing')
    if row['effect_code'] != 'MOR' or row['measurement_code'] != 'MORT':
        reasons.append('not_explicit_mortality')
    # This export is a context-review queue; no record enters the historical baseline.
    return {'measurement_id': row['measurement_id'], 'source_result_id': row['source_result_id'],
            'source_chemical_id': row['source_chemical_id'], 'compound_id': row['compound_id'],
            'species': row['species'], 'exposure_type': row['exposure_type'],
            'test_type': test.get('test_type'), 'unit_raw': row['unit_raw'],
            'raw_value': result.get(prefix+'mean'), 'qualifier': row['qualifier'],
            'normalized_value': row['value'], 'normalized_unit': row['unit_standardized'],
            'concentration_type': row['concentration_type'], 'formulation': row['formulation_code'],
            'duration_hours': row['duration_hours'], 'reference_number': source['reference_number'],
            'reference_title': json.loads(source['reference_json']).get('title'),
            'status': 'review_required_not_added_to_historical_baseline',
            'reasons': ';'.join(reasons) or 'explicit_primary_study_context_adjudication_required'}


def overlap_scenarios(observations, queue, policies):
    """Carry adopted pair decisions into explicit aquatic sensitivity summaries."""
    if len({r['pair_id'] for r in queue}) != len(queue):
        raise ValueError('Overlap queue requires unique pair IDs')
    dropped = duplicate_exclusions(queue, queue)
    pending = {r[k] for r in queue if r['decision'] in {'unreviewed', 'unresolved'}
               for k in ('left_id', 'right_id')}
    strata, sensitivity = [], []
    for scenario, excluded, documented in [
        ('all_core_policy_admitted', set(), False),
        ('reviewed_duplicate_decisions', dropped, False),
        ('exclude_unresolved_overlap_candidates', pending | dropped, False),
        ('reported_context_only', dropped, True),
        ('reported_context_exclude_overlap', pending | dropped, True),
    ]:
        records = summarize_strata(observations, excluded, documented)
        strata.extend({**r, 'scenario': scenario} for r in records)
        for policy in sorted(policies):
            chosen = [r for r in observations if r['policy'] == policy and
                      r['measurement_id'] not in excluded and
                      (not documented or r['reported_context_complete'])]
            sensitivity.append({'scenario': scenario, 'policy': policy, 'slots': len(chosen),
                'distinct_results': len({r['source_result_id'] for r in chosen}),
                'distinct_compounds': len({r['compound_id'] for r in chosen}),
                'exact_slots': sum(r['qualifier'] == '=' for r in chosen),
                'bounded_or_range_slots': sum(r['qualifier'] != '=' for r in chosen)})
    return strata, sensitivity, dropped


def run(ecotox, previous, identities, adoption, selection_path, reconciliation, output):
    ecotox, previous, identities, adoption, selection_path, reconciliation, output = [Path(p).resolve() for p in
        (ecotox, previous, identities, adoption, selection_path, reconciliation, output)]
    roots = (ecotox, previous, identities, adoption, reconciliation)
    if output.exists() or any(p.is_relative_to(output) or output.is_relative_to(p) for p in (*roots, selection_path)):
        raise ValueError('Use a fresh output directory separate from inputs')
    manifests = {p: verify_manifest(p/'manifest.json') for p in roots}
    inputs = [p/'manifest.json' for p in roots]+[selection_path]
    before = hashes(inputs)
    if manifests[identities]['approved_source_identities'] != manifests[ecotox]['selected_chemicals']:
        raise ValueError('Identity approval must cover the selected cohort')
    native = pl.read_parquet(ecotox/'native_observations.parquet')
    measures = pl.read_parquet(ecotox/'measurements.parquet')
    accounting = identity_only_accounting(pl.read_parquet(previous/'native_observations.parquet'), native,
        pl.read_parquet(previous/'measurements.parquet'), measures)
    ledger = {r['compound_id']: r for r in read_csv(identities/'identity_approval_ledger.csv')}
    crosswalk = {r['source_chemical_id']: r['compound_id'] for r in read_csv(identities/'approved_crosswalk.csv')}
    if any(r['compound_id'] != crosswalk.get(r['source_chemical_id']) for r in measures.select(
            'source_chemical_id', 'compound_id').unique().to_dicts()):
        raise ValueError('Attached identities disagree with approved crosswalk')
    selection = {r['compound_id']: r for r in pl.read_parquet(selection_path).to_dicts()}
    natural_features = pl.read_parquet(adoption/'contrast_features.parquet').filter(
        pl.col('contrast_group') == 'reviewed_natural_occurrence').to_dicts()
    k_labels = {r['compound_id']: r for r in read_csv(adoption/(K1998+'.csv'))}
    natural = {r['structure_inchikey']: {'activity': k_labels.get(r['compound_id'], {}).get('herbicidal_activity', 'unknown')}
               for r in natural_features}
    admission = pl.read_parquet(ecotox/'admission.parquet')
    admitted = admission.filter(pl.col('canonical_comparison_eligible'))
    if admitted['measurement_id'].n_unique() != admitted.height:
        raise ValueError('Each admitted slot requires one policy; prevent policy join fan-out')
    selected = measures.join(admitted.select('measurement_id','policy'), on = 'measurement_id', validate = '1:1')
    by_native = {r['source_result_id']: r for r in native.to_dicts()}
    observations = []
    for row in selected.to_dicts():
        source = by_native[row['source_result_id']]
        test, reference = json.loads(source['test_json']), json.loads(source['reference_json'])
        gaps = documented_context(row, test)
        observations.append({**row, 'name': ledger[row['compound_id']]['name'],
            'group': group_for(row['compound_id'], ledger, natural, selection),
            'test_id': source['test_id'], 'reference_number': source['reference_number'],
            'reference_title': reference.get('title'), 'reference_doi': reference.get('doi'),
            'source_record': source['result_record'], 'source_member': source['result_member'],
            'control_type_raw': test.get('control_type'),
            'reported_context_complete': not gaps, 'context_gaps': ';'.join(gaps)})
    queue = read_csv(reconciliation/'study_overlap_review.csv')
    strata, sensitivity, dropped = overlap_scenarios(observations, queue, admission['policy'].unique().to_list())
    aquatic_dropped = sorted(dropped & {r['measurement_id'] for r in observations})
    rats = [rat_review(r, by_native[r['source_result_id']]) for r in measures.filter(
        pl.col('species').str.starts_with('rattus ') & (pl.col('endpoint') == 'LD50')).to_dicts()]
    policy_rows = []
    for policy in sorted(admission['policy'].unique().to_list()):
        obs = [r for r in observations if r['policy'] == policy]
        policy_rows.append({'policy': policy, 'approved_slots': len(obs),
            'distinct_results': len({r['source_result_id'] for r in obs}),
            'distinct_tests': len({r['test_id'] for r in obs}),
            'distinct_compounds': len({r['compound_id'] for r in obs}),
            'measured_slots': sum(r['chemical_analysis'] == 'M' for r in obs),
            'unmeasured_slots': sum(r['chemical_analysis'] == 'U' for r in obs),
            'reported_context_complete_slots': sum(r['reported_context_complete'] for r in obs),
            'observation_duration_hours': obs[0]['duration_hours'] if obs else None,
            'natural_active_slots': sum(r['group'] == 'natural_active_K1998' for r in obs),
            'natural_activity_unknown_slots': sum(r['group'] == 'natural_activity_unknown' for r in obs)})
    output.parent.mkdir(parents = True, exist_ok = True)
    stage = Path(tempfile.mkdtemp(prefix = '.ecotox-comparison-', dir = output.parent))
    try:
        for name, records in [('row_accounting', accounting), ('aquatic_observations', observations),
                              ('compound_context_summaries', strata), ('sensitivity', sensitivity),
                              ('rat_ld50_review', rats), ('policy_coverage', policy_rows)]:
            write_csv(stage/(name+'.csv'), records, list(records[0]))
        exposure_counts = Counter((r['policy'],r['chemical_analysis'],r['concentration_type'],r['formulation_code'],r['exposure_type']) for r in observations)
        context_rows = [{'policy':p,'analysis':a,'basis':b,'formulation':f,'exposure_type':e,'slots':n}
                        for (p,a,b,f,e),n in sorted(exposure_counts.items())]
        write_csv(stage/'exposure_contexts.csv',context_rows,list(context_rows[0]))
        group_labels = {'natural_active_K1998':'Natural active (K1998)', 'natural_activity_unknown':'Natural, activity unknown',
                        'natural_tested_low_response_K1998':'Natural low response (K1998)',
                        'selected_herbicide_comparator':'Selected herbicide comparator',
                        'unreviewed_natural_product_selection':'Unreviewed natural-product selection',
                        'unreviewed_source_chemical':'Unreviewed source chemical'}
        points = [{**r,'group_label':group_labels[r['group']], 'policy_label': 'Trout 96 h observation LC50' if r['endpoint']=='LC50' else 'Daphnia 48 h observation EC50'} for r in observations]
        chart = alt.Chart(alt.Data(values = points)).mark_point(size = 85).encode(
            x = alt.X('value:Q', scale = alt.Scale(type = 'log'), title = 'Concentration or censored bound (mg/L); lower = greater potency'),
            y = alt.Y('name:N', title = None), color = alt.Color('group_label:N', title = 'Reviewed evidence group', legend = alt.Legend(labelLimit = 350)),
            shape = alt.Shape('qualifier:N', title = 'Reported qualifier', scale = alt.Scale(
                domain = ['=','>'], range = ['circle','triangle-right'])),
            tooltip = ['name:N','group:N','qualifier:N','value:Q','chemical_analysis:N','formulation_code:N',
                       'exposure_type:N','exposure_hours:Q','reference_number:N','context_gaps:N']
        ).properties(width = 600, height = 220).facet(row = alt.Row('policy_label:N',title = None)).resolve_scale(y = 'independent', x = 'independent')
        chart.save(stage/'aquatic_observations.svg')
        context_chart = alt.Chart(alt.Data(values = context_rows)).mark_bar().encode(
            x = alt.X('sum(slots):Q',title = 'Admitted concentration slots'),
            y = alt.Y('policy:N',title = None), color = alt.Color('analysis:N',title = 'M measured / U unmeasured')
        ).properties(width = 600, height = 100)
        context_chart.save(stage/'exposure_coverage.svg')
        links = ''.join('<li><a href="'+p.name+'">'+html.escape(p.name)+'</a></li>' for p in sorted(stage.glob('*.csv')))
        counts = '; '.join(f"{r['policy']}: {r['approved_slots']} slots across {r['distinct_compounds']} compounds" for r in policy_rows)
        body = f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>Approved ECOTOX comparisons</title>
<style>body{{font:17px/1.5 system-ui;max-width:1100px;margin:40px auto;padding:0 24px}}img{{max-width:100%;height:auto}}</style><body>
<h1>Identity-approved ECOTOX comparisons</h1><p>All {manifests[identities]['approved_source_identities']} frozen mappings are approved by the research lead. Source records, values, units and policies are unchanged: {native.height:,} native results and {measures.height:,} concentration slots.</p>
<p>{html.escape(counts)}. The 96/48-hour policy screen uses reported observation duration; exposure duration is a separate field and is often missing. These are ecological endpoints, separate from rat oral LD50. Each observation retains its source, qualifier and exposure context. Slots are not independent experiments.</p>
<img src="aquatic_observations.svg" alt="Individual trout and Daphnia concentrations with qualifiers">
<h2>Exposure and documentation</h2><img src="exposure_coverage.svg" alt="Measured and unmeasured exposure coverage">
<p>Compound summaries stay within policy, measured/unmeasured analysis, concentration basis, formulation, exposure type, medium and exposure duration. Only exact observations enter a record median. Bounds remain separate. These strata do not harmonize all study conditions such as pH, temperature or organism age; record medians are descriptive, not pooled effect estimates. Source observations and the chart above preserve all admitted slots. Reviewed duplicate decisions exclude {len(aquatic_dropped)} aquatic slot(s) in separately named sensitivity summaries.</p>
<p>The original reported exposure/control subset contains {sum(r['reported_context_complete_slots'] for r in policy_rows)} observation(s). Reported context does not establish study quality, and missing exposure duration prevents treating the core-policy screen as fully verified continuous 96/48-hour exposure.</p>
<p>The all-core scenario preserves the original admission. All other sensitivity scenarios apply signed duplicate exclusions; conservative scenarios additionally exclude unresolved overlap candidates and/or require reported control type, exposure type and matching exposure/observation duration. Reported fields do not establish study quality. Empty subsets remain empty.</p>
<h2>Rat oral comparison</h2><p>{len(rats)} rat LD50 records remain in a source-context review queue. Identity approval does not establish acute-study context or resolve body-weight/acid-equivalent unit semantics. No records are added to the historical 43 exact / 25 censored observations or 34 compound medians; 1,080/3,400 mg/kg cutoffs stay frozen.</p>
<h2>Files</h2><ul>{links}</ul></body></html>'''
        (stage/'walkthrough.html').write_text(body)
        if hashes(inputs) != before:
            raise ValueError('Inputs changed during comparison')
        manifest = {'input_hashes':before, 'output_hashes':{str(output/Path(k).name):v for k,v in hashes(list(stage.iterdir())).items()},
            'code_hashes':hashes([Path(__file__),HERE/'ecotox_approved.py',HERE/'expansion_toxicity.py']),
            'lock_hashes':hashes([HERE/'uv.lock',HERE/'pyproject.toml']),
            'identity_approvals':manifests[identities]['approved_source_identities'],
            'policy_coverage':policy_rows,'rat_ld50_review_records':len(rats),
            'new_rat_baseline_observations':0,'duplicate_observations_collapsed':len(aquatic_dropped),
            'aquatic_duplicate_exclusions':aquatic_dropped,
            'scope':'Identity-approved ecological context comparisons; no endpoint pooling, inferred biological labels or new model fitting.'}
        (stage/'manifest.json').write_text(json.dumps(manifest,indent = 2,allow_nan = False)+'\n')
        if output.exists():
            raise ValueError('Output appeared before publication')
        stage.rename(output)
        return manifest
    finally:
        if stage.exists():
            shutil.rmtree(stage)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for key in ('ecotox','previous','identities','adoption','selection','reconciliation','output'):
        parser.add_argument('--'+key,type = Path,required = True)
    args = parser.parse_args()
    result = run(args.ecotox,args.previous,args.identities,args.adoption,args.selection,args.reconciliation,args.output)
    print(json.dumps({'policy_coverage':result['policy_coverage'], 'rat_ld50_review_records':result['rat_ld50_review_records']},indent = 2))
