"""Describe adopted biological groups, fixed-cutoff toxicity and a distinct cohort model."""
import argparse
import html
import json
import shutil
import tempfile
from pathlib import Path

import altair as alt
import numpy as np
import polars as pl
from sklearn.metrics import balanced_accuracy_score, f1_score, roc_auc_score

from review_adoption import K1998, read_csv
from screen import HERE, hashes, write_csv
from weekly_report import verify_manifest

GROUPS = ('natural_active_K1998', 'natural_activity_unknown',
          'natural_tested_low_response_K1998', 'selected_herbicide_comparator')
MEASURES = ('mw', 'logp', 'tpsa', 'hbd', 'hba', 'sa_score', 'halogen_present')


def natural_group(label):
    if label.get('natural_origin') != 'natural':
        return None
    return {'active': GROUPS[0], 'inactive': GROUPS[2]}.get(label.get('herbicidal_activity'), GROUPS[1])


def membership(adoption, selection):
    contrast = pl.read_parquet(adoption / 'contrast_features.parquet').to_dicts()
    origin = {r['compound_id']: r for r in read_csv(adoption / 'origin_labels.csv')}
    k_labels = {r['compound_id']: r for r in read_csv(adoption / (K1998+'.csv'))}
    natural, keys = [], set()
    for row in contrast:
        label = k_labels.get(row['compound_id'], origin[row['compound_id']])
        group = natural_group(label)
        if group:
            key = row['structure_inchikey']
            if key in keys:
                raise ValueError('Natural membership requires unique full structures')
            keys.add(key)
            natural.append({**row, 'group': group, 'natural_origin': 'natural',
                            'herbicidal_activity': label['herbicidal_activity'],
                            'activity_policy': label['activity_policy'],
                            'origin_reference': label['origin_reference']})
    comparators = []
    seen = set(keys)
    overlaps = []
    for row in sorted(selection, key = lambda r: r['compound_id']):
        if row.get('chemical_group') != 'herbicide' or row.get('structure_status') != 'valid':
            continue
        key = row['structure_inchikey']
        if key in seen:
            overlaps.append({'compound_id': row['compound_id'], 'structure_inchikey': key,
                             'reason': 'duplicate_structure_or_reviewed_natural_overlap'})
            continue
        seen.add(key)
        comparators.append({**row, 'group': GROUPS[3], 'natural_origin': 'unknown',
                            'herbicidal_activity': 'unknown', 'activity_policy': '',
                            'origin_reference': ''})
    return natural+comparators, overlaps


def describe(rows):
    summary = []
    for group in GROUPS:
        members = [r for r in rows if r['group'] == group]
        for measure in MEASURES:
            values = [r.get(measure) for r in members]
            values = [float(v) for v in values if v is not None and np.isfinite(v)]
            quartiles = np.quantile(values, [.25, .5, .75], method = 'linear') if values else [None]*3
            summary.append({'group': group, 'feature': measure, 'group_compounds': len(members),
                            'n': len(values), 'q1': quartiles[0], 'median': quartiles[1],
                            'q3': quartiles[2],
                            'prevalence': float(np.mean(values)) if measure == 'halogen_present' and values else None})
    return summary


def reclassify_ld50(baseline, selection, members):
    selected = {r['compound_id']: r for r in selection}
    reviewed = {r['structure_inchikey']: r for r in members if r['natural_origin'] == 'natural'}
    result = []
    for row in baseline:
        key = selected.get(row['compound_id'], {}).get('structure_inchikey')
        match = reviewed.get(key)
        group = match['group'] if match else (
            GROUPS[3] if row['group'] == 'selected_herbicide' else 'unreviewed_natural_product_selection')
        value = float(row['median_mg_kg']) if row['median_mg_kg'] else None
        expected = 'low' if value is not None and value <= 1080 else 'medium' if value is not None and value <= 3400 else 'high' if value is not None else ''
        if row['ld50_bin'] != expected:
            raise ValueError('Historical LD50 bins/cutoffs must remain 1080/3400 mg/kg')
        result.append({**row, 'historical_group': row['group'], 'group': group,
                       'reviewed_compound_id': match['compound_id'] if match else '',
                       'activity_policy': match['activity_policy'] if match else '',
                       'natural_origin': 'natural' if match else 'unknown'})
    return result


def verify_model_predictions(models):
    reports = read_csv(models / 'reports.csv')
    oof = read_csv(models / 'oof.csv')
    canonical_assignments, scaffold_assignments, labels_by_id = {}, {}, {}
    expected_ids = None
    for report in reports:
        rows = [r for r in oof if r['profile'] == report['profile']]
        if report['target'] != 'provenance_comparator_target':
            raise ValueError('Incorrect model target')
        if report['status'] != 'evaluated':
            raise ValueError('Reviewed-cohort comparison requires supported held-out models')
        if len(rows) != int(report['n']) or len({r['compound_id'] for r in rows}) != len(rows):
            raise ValueError('One held-out prediction per compound/profile required')
        row_ids = {r['compound_id'] for r in rows}
        if expected_ids is None:
            expected_ids = row_ids
        if expected_ids != row_ids:
            raise ValueError('Model profiles must share the exact compound cohort')
        for row in rows:
            if labels_by_id.setdefault(row['compound_id'], row['label']) != row['label']:
                raise ValueError('Model profiles must share target labels')
            if canonical_assignments.setdefault(row['compound_id'], row['fold']) != row['fold']:
                raise ValueError('Model profiles must use identical held-out assignments')
            if scaffold_assignments.setdefault(row['scaffold'], row['fold']) != row['fold']:
                raise ValueError('Scaffold leakage')
        y = [int(r['label']) for r in rows]
        p = [float(r['probability']) for r in rows]
        hard = [v >= .5 for v in p]
        for metric, value in [('f1', f1_score(y, hard)), ('roc_auc', roc_auc_score(y, p)),
                              ('balanced_accuracy', balanced_accuracy_score(y, hard))]:
            if abs(float(report[metric])-value) > 1e-12:
                raise ValueError('Reported model metrics disagree with held-out predictions')
    return reports


def run(adoption, models, baseline, selection_path, output):
    adoption, models, baseline, selection_path, output = [Path(p).resolve() for p in
        (adoption, models, baseline, selection_path, output)]
    if output.exists() or any(p.is_relative_to(output) or output.is_relative_to(p)
                              for p in (adoption, models, baseline, selection_path)):
        raise ValueError('Use a fresh output directory separate from inputs')
    adoption_manifest, model_manifest, baseline_manifest = [verify_manifest(p/'manifest.json')
                                                           for p in (adoption, models, baseline)]
    if model_manifest['target'] != 'provenance_comparator_target':
        raise ValueError('Model must use the reviewed cohort-membership target')
    if baseline_manifest['policy']['cutoffs'] != [1080, 3400]:
        raise ValueError('Preserve frozen historical LD50 cutoffs')
    inputs = [p/'manifest.json' for p in (adoption, models, baseline)] + [selection_path]
    before = hashes(inputs)
    selection = pl.read_parquet(selection_path).to_dicts()
    members, overlaps = membership(adoption, selection)
    for row in members:
        row['halogen_present'] = int(any(row.get('formula_'+e+'_count', 0) for e in ('F','Cl','Br','I')))
    summary = describe(members)
    ld50 = reclassify_ld50(read_csv(baseline / 'compounds.csv'), selection, members)
    model_reports = verify_model_predictions(models)
    group_counts = [{'group': g, 'compounds': sum(r['group'] == g for r in members),
                     'scaffolds': len({r['scaffold'] for r in members if r['group'] == g}),
                     'activity_scope': K1998 if g in (GROUPS[0], GROUPS[2]) else 'not shared activity labels'}
                    for g in GROUPS]
    toxicity_counts = []
    for group in sorted({r['group'] for r in ld50}):
        rows = [r for r in ld50 if r['group'] == group]
        exact = [r for r in rows if r['median_mg_kg']]
        for bucket in ('low', 'medium', 'high'):
            count = sum(r['ld50_bin'] == bucket for r in exact)
            toxicity_counts.append({'group': group, 'ld50_bin': bucket, 'count': count,
                'exact_compound_denominator': len(exact),
                'censored_only_compounds': len(rows)-len(exact),
                'proportion': count/len(exact) if exact else None})
    output.parent.mkdir(parents = True, exist_ok = True)
    stage = Path(tempfile.mkdtemp(prefix = '.'+output.name+'-', dir = output.parent))
    try:
        columns = ['compound_id','query','structure_inchikey','canonical_structure','scaffold','group',
                   'natural_origin','herbicidal_activity','activity_policy','origin_reference', *MEASURES]
        write_csv(stage/'group_membership.csv', [{k:r.get(k) for k in columns} for r in members], columns)
        write_csv(stage/'group_counts.csv', group_counts, list(group_counts[0]))
        write_csv(stage/'descriptor_summary.csv', summary, list(summary[0]))
        write_csv(stage/'selection_overlaps.csv', overlaps,
                  ['compound_id','structure_inchikey','reason'])
        write_csv(stage/'ld50_reclassified_compounds.csv', ld50, list(ld50[0]))
        write_csv(stage/'ld50_group_bins.csv', toxicity_counts, list(toxicity_counts[0]))
        write_csv(stage/'model_metrics.csv', model_reports, list(model_reports[0]))
        plotted = [{'group':r['group'], 'compound':r['query'] or r['compound_id'],
                    'feature':m, 'value':float(r[m])} for r in members for m in ('mw','logp','tpsa')]
        chart = alt.Chart(alt.Data(values = plotted)).mark_circle(size = 45, opacity = .65).encode(
            x = alt.X('value:Q', title = 'Descriptor value (MW g/mol; logP calculated; TPSA Å²)'),
            y = alt.Y('group:N', title = None),
            color = alt.Color('group:N', legend = None), tooltip = ['compound:N','feature:N','value:Q']
        ).properties(width = 570, height = 100).facet(row = alt.Row('feature:N', title = None)).resolve_scale(x = 'independent')
        chart.save(stage/'reviewed_descriptors.svg')
        model_plot = alt.Chart(alt.Data(values = [{**r, 'f1':float(r['f1'])} for r in model_reports])).mark_bar().encode(
            x = alt.X('f1:Q', scale = alt.Scale(domain = [0,1]), axis = alt.Axis(tickCount = 6),
                        title = 'Held-out F1; commercial comparator is positive'),
            y = alt.Y('profile:N', title = 'Reviewed cohort model', sort = '-x'), tooltip = ['profile:N','f1:Q']
        ).properties(width = 600, height = 260)
        model_plot.save(stage/'reviewed_models.svg')
        ldpoints = [{**r, 'median_mg_kg':float(r['median_mg_kg'])} for r in ld50 if r['median_mg_kg']]
        alt.Chart(alt.Data(values = ldpoints)).mark_circle(size = 80).encode(
            x = alt.X('median_mg_kg:Q', scale = alt.Scale(type = 'log'),
                      axis = alt.Axis(values = [10,100,1000,10000]),
                      title = 'Rat oral LD50 (mg/kg); lower means greater acute toxicity'),
            y = alt.Y('group:N', title = None),
            color = 'ld50_bin:N', tooltip = ['query:N','median_mg_kg:Q','exact_records:N','censored_records:N']
        ).properties(width = 600, height = 170).save(stage/'reviewed_ld50.svg')
        body = ['<h1>Human-reviewed research progress — 11 November 2026</h1>',
                '<p>Human adoption establishes 19 natural-occurrence labels and 80 bounded activity decisions across four supported policies. Source gaps and unknowns remain. No supported assay-specific activity model is available.</p>',
                '<h2>Biological groups and chemical description</h2>',
                '<p>Five natural compounds meet the 1998 authors’ very-active category; fourteen approved natural compounds have unknown activity under that policy. There are zero low-response examples under that policy. The 58 selected herbicides are a separate purposive comparator, not an assay-matched activity class.</p>',
                '<img src="reviewed_descriptors.svg" alt="Individual descriptor values by reviewed group">',
                '<h2>New structural cohort comparison</h2>',
                '<p>The 30-compound contrast contains 19 natural-occurrence examples and 11 documented commercial-herbicide manufacturing comparators. It predicts membership in these two groups, not natural origin, herbicidal activity, safety or protein binding. Natural occurrence and commercial manufacture can coexist. Five scaffold folds have very small test partitions. These scores do not represent improvement over the historical 171-compound task.</p>',
                '<img src="reviewed_models.svg" alt="Held-out F1 for the separate reviewed cohort contrast">',
                '<h2>EPA rat oral LD50</h2>',
                '<p>The historical 43 exact observations, 34 exact compound medians, 25 bounds and 1,080/3,400 mg/kg cutoffs are preserved. Only evidence-group annotation changes. Low LD50 means greater acute toxicity; these are not regulatory risk bins. Source ECOTOX candidate overlaps are not automatically source-identity approval.</p>',
                '<img src="reviewed_ld50.svg" alt="Rat oral LD50 with reviewed group annotations">',
                '<h2>Inspect the results</h2>']
        for filename in ('group_counts.csv','group_membership.csv','descriptor_summary.csv',
                         'ld50_group_bins.csv','ld50_reclassified_compounds.csv','model_metrics.csv'):
            body.append('<p><a href="'+filename+'">'+html.escape(filename)+'</a></p>')
        (stage/'walkthrough.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Reviewed research progress</title><style>body{font:17px/1.5 system-ui;max-width:1100px;margin:40px auto;padding:0 24px}img{max-width:100%;height:auto}h2{margin-top:2em}</style><body>'+''.join(body)+'</body></html>')
        if hashes(inputs) != before:
            raise ValueError('Inputs changed during analysis')
        manifest = {'input_hashes': before, 'output_hashes': {str(output/Path(k).name):v for k,v in hashes(list(stage.iterdir())).items()},
                    'code_hashes': hashes([Path(__file__)]), 'lock_hashes': hashes([HERE/'uv.lock',HERE/'pyproject.toml']),
                    'group_counts': group_counts, 'adopted_origin': adoption_manifest['accepted_origin'],
                    'model_target': model_manifest['target'], 'ld50_cutoffs': [1080,3400],
                    'ld50_exact_compounds': len(ldpoints), 'activity_models_fitted': adoption_manifest['activity_models_fitted'],
                    'cohort_models': len(model_reports), 'scope': 'Descriptive biological groups plus separate purposive cohort models; no assay pooling or biological activity model.'}
        (stage/'manifest.json').write_text(json.dumps(manifest, indent = 2, allow_nan = False)+'\n')
        if output.exists():
            raise ValueError('Output appeared before publication')
        stage.rename(output)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for name in ('adoption','models','baseline','selection','output'):
        parser.add_argument('--'+name, type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(run(args.adoption,args.models,args.baseline,args.selection,args.output),indent = 2))
