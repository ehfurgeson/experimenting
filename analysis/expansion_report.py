"""Verified evidence/ECOTOX expansion walkthrough without fitting biological models."""
import argparse
import html
import json
from pathlib import Path

import altair as alt
import polars as pl

from screen import HERE, hashes
from weekly_report import table, verify_manifest


def build(ecotox, toxicity, review, sources, cohort, output):
    roots = {name: Path(p).resolve() for name,p in
             {'ecotox':ecotox, 'toxicity':toxicity, 'review':review, 'sources':sources, 'cohort':cohort}.items()}
    output = Path(output).resolve()
    if output.exists() or any(p.is_relative_to(output) or output.is_relative_to(p) for p in roots.values()):
        raise ValueError('Use a new output directory separate from inputs')
    manifests = {key: verify_manifest(root / 'manifest.json') for key,root in roots.items()}
    ec, tx, rv = [manifests[k] for k in ('ecotox','toxicity','review')]
    if rv['accepted_activity_labels'] or rv['accepted_origin_labels'] or rv['models_fitted']:
        raise ValueError('This report requires unapproved evidence and no biological model fitting')
    packets = pl.read_csv(roots['review'] / 'compound_packets.csv')
    readiness = pl.read_csv(roots['review'] / 'policy_readiness.csv')
    admission = pl.read_parquet(roots['ecotox'] / 'admission.parquet')
    measurements = pl.read_parquet(roots['ecotox'] / 'measurements.parquet')
    selected = pl.read_csv(roots['cohort'] / 'chemical_ids.csv')
    aq = pl.read_csv(roots['toxicity'] / 'aquatic_policy_summary.csv')
    strata = pl.read_csv(roots['toxicity'] / 'aquatic_exposure_strata.csv')
    queue = pl.read_csv(roots['toxicity'] / 'study_overlap_review.csv', infer_schema_length = None)
    quality = pl.read_csv(roots['toxicity'] / 'context_missingness.csv')
    policies = json.loads((roots['review'] / 'policy_proposals.json').read_text())
    source_index = json.loads((roots['review'] / 'source_index.json').read_text())
    cases = admission.filter(pl.col('source_context_eligible')).join(
        measurements, on = 'measurement_id', suffix = '_measurement').join(
            selected.select('source_chemical_id','chemical_name'), on = 'source_chemical_id')
    points = cases.select('policy','chemical_name','source_chemical_id','value','qualifier',
                          'chemical_analysis','concentration_type').to_dicts()
    output.mkdir(parents = True)
    for source in roots['toxicity'].glob('*.svg'):
        (output / source.name).write_bytes(source.read_bytes())
    if points:
        chart = alt.Chart(alt.Data(values = points)).mark_point(size = 60).encode(
            x = alt.X('value:Q', scale = alt.Scale(type = 'log'), title = 'Effect concentration/bound (mg/L)'),
            y = alt.Y('chemical_name:N', title = 'Source chemical; identity approval pending'),
            color = alt.Color('chemical_analysis:N', title = 'M measured / U unmeasured'),
            shape = 'qualifier:N', tooltip = ['chemical_name:N','value:Q','qualifier:N','chemical_analysis:N'])
        chart.properties(width = 650,height = 220).facet(row = 'policy:N').resolve_scale(
            x = 'independent',y = 'independent').properties(
                title = 'Source-context matches only; no canonical identity approval or pooled potency').save(
                    output / 'aquatic_context.svg')
    source_text = ''.join('<li><a href="' + html.escape(s['url'],quote = True) + '">' +
                          html.escape(s['source_id']) + '</a> — ' + html.escape(s['locator']) +
                          '. ' + html.escape(s['finding']) + '</li>' for s in source_index)
    scenarios = [{**r, 'fixed_cutoffs': ', '.join(str(x) for x in r['fixed_cutoffs']),
                  'cohort_tertiles': ', '.join(str(x) for x in r['cohort_tertiles'])} for r in tx['scenarios']]
    scene = pl.DataFrame(scenarios)
    requests = pl.DataFrame(manifests['sources']['requests']).select('source_id','http_status','status')
    # Browser-accessible CSV links remain relative to neighboring frozen bundles.
    links = []
    for label,path in [('Approval worksheet',roots['review']/'approval_worksheet.csv'),
                       ('Study/condition evidence',roots['review']/'study_observations.csv'),
                       ('Compound packets',roots['review']/'compound_packets.csv'),
                       ('All study-overlap candidates',roots['toxicity']/'study_overlap_review.csv'),
                       ('Censored-compatible bins',roots['toxicity']/'censored_bins.csv')]:
        import os
        target = os.path.relpath(path, output)
        links.append('<a href="' + html.escape(target,quote = True) + '">' + html.escape(label) + '</a>')
    ec_summary = (f"{ec['selected_chemicals']} source chemicals, {ec['selected_tests']:,} tests, "
                  f"{ec['counts']['native_observations']:,} native results and "
                  f"{ec['counts']['measurements']:,} concentration-slot records. "
                  f"{manifests['cohort']['priority']} literature overlaps prioritized. "
                  f"{rv['counts']['compounds']} compounds, {rv['counts']['observations']} study/condition observations, "
                  f"{rv['counts']['worksheet_rows']} approval worksheet rows.")
    parts = ['<h1>Stronger evidence and comparable toxicity</h1>',
             '<p class="date">11 November 2026 · Local expansion checkpoint</p>',
             '<p class="lead">' + html.escape(ec_summary) + '</p>',
             ('<p class="notice"><strong>Review status:</strong> no scientific origin/activity labels or '
             'source-specific canonical identities are approved. No biological model was fitted.</p>'),
             '<nav>' + ' · '.join(links) + '</nav>',
             '<h2>Decisions ready for scientific review</h2>',
             ('<p>Every packet distinguishes primary isolation/characterization leads from exact structure, '
             'stereochemistry and chemical-form approval. Some primary full texts remain inaccessible. '
             'Natural occurrence is a separate decision from plant response, manufacturing and safety.</p>'),
             table(packets, ['name','origin_proposal','origin_rationale','named_structure_check','source_access']),
             '<h3>Activity policy proposals</h3><ul>' + ''.join(
                 '<li><strong>' + html.escape(k) + '</strong>: ' + html.escape(v['scope']) + '</li>'
                 for k,v in policies.items()) + '</ul>',
             ('<p>Do not pool species, soil versus solution, field site, application rate or formulation. '
             'The 1998 paper has full methods and figures; numerical graph values were not invented. '
             'Sarmentine methods report 10 mg/mL while weed-spectrum tables report 20 mg/mL: '
             'that dose conflict keeps its activity proposal unknown. 2020 controls show mortality '
             'and 2024 responses depend on site/dose/formulation. The Li 7b hold is preserved byte-for-byte.</p>'),
             '<h2>Comparable aquatic source contexts</h2>',table(aq,aq.columns),table(strata,strata.columns),
             ('<p>Trout: 96-hour mortality LC50. Daphnia: 48-hour ITX/IMBL immobilization EC50. '
             'Unknown effect, duration, medium, form, exposure basis or units exclude admission. '
             'M and U strata remain separate. Slot counts do not represent independent studies; '
             'canonical coverage remains unknown until source identity approval.</p>'),
             (output/'aquatic_context.svg').read_text() if points else '<p>No source-context matches.</p>',
             '<h2>Rat oral LD50 sensitivity</h2>',table(scene,scene.columns),
             ('<p>The 34-compound historical exact-value baseline remains unchanged. Fixed exploratory '
             'boundaries stay 1,080/3,400 mg/kg. Scenario tertiles are separate, and lower LD50 means '
             'greater toxicity. Individual censored bounds are not substituted for point estimates '
             'or assigned to compound medians. No approved new ECOTOX rat oral data were added.</p>'),
             (output/'study_values.svg').read_text(),
             '<h3>Missingness and disagreement</h3>',table(quality,quality.columns),
             (output/'missingness.svg').read_text(),
             ('<p>The documented-context subset requires reference, sex, strain and an explicit elapsed '
             'duration. It is empty here; that is an insufficiency finding rather than evidence of '
             'safety or a justification to loosen eligibility. Per-compound minimum/maximum study '
             'values accompany medians in the sensitivity export.</p>'),
             '<h2>Study-overlap adjudication</h2>',
             '<p>' + str(queue.height) + ' publication/chemical-hint pairs are ranked by context-field '
             'agreement. This count is not a count of duplicates. Missing duration and candidate '
             'identity remain explicit. No observations were collapsed. A signed same-observation '
             'decision and source-specific identity approval are required for cross-source exclusion.</p>',
             table(queue.head(12),['compound_id_hint','identity_link_status','species_match','endpoint_match',
                                  'route_match','duration_match','result_match','match_count']),
             '<h2>Model readiness</h2>',table(readiness,readiness.columns),
             ('<p>All accepted labels remain unknown. Hypothetical proposal counts are displayed per '
             'policy and are not evaluation results. No proposed policy has both-class five-fold '
             'scaffold support. The existing 154-compound validator and frozen label worksheets '
             'remain unchanged; the separate 15-row seven-column label file remains unknown.</p>'),
             ('<h2>Remaining review work</h2><ol><li>Confirm primary source structures, spectral '
             'consistency, regioisomers, stereochemistry and exact tested chemical forms.</li>'
             '<li>Resolve the sarmentine dose conflict, treatment control adequacy and source-access gaps.</li>'
             '<li>Review the source-specific identity worksheet before attaching ecological results.</li>'
             '<li>Approve one bounded biological policy at a time; acquire independent negative-bearing '
             'chemistry before model fitting.</li></ol>'),
             '<h2>Primary source access and citations</h2>',table(requests,requests.columns),
             '<ul>' + source_text + '</ul>',
             ('<p>Input/output hashes of all five upstream bundles were verified before synthesis. '
             'Source byte verification does not constitute scientific approval.</p>')]
    css = ('body{font:16px/1.55 system-ui,sans-serif;color:#1d3440;max-width:1150px;margin:40px auto;padding:0 28px}'
           'h1{font-size:36px}h2{margin-top:38px;border-bottom:2px solid #d6e5df;padding-bottom:8px}'
           '.lead{font-size:20px}.date{color:#526b77}.notice{background:#edf4f1;padding:16px}'
           'table{border-collapse:collapse;display:block;overflow:auto;font-size:13px;margin:20px 0}'
           'th,td{text-align:left;vertical-align:top;padding:9px 12px;border-bottom:1px solid #d6e1e4}'
           'th{background:#eef4f2}svg{max-width:100%;height:auto}li{margin:10px 0}a{color:#08664f}')
    (output/'walkthrough.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1"><title>Evidence expansion</title>'
        '<style>'+css+'</style></head><body>'+''.join(parts)+'</body></html>')
    (output/'README.md').write_text('# Evidence and toxicity expansion — 11 November 2026\n\n'+ec_summary+
        '\n\nOpen `walkthrough.html` and follow its approval/evidence CSV links. All proposals remain '
        'unapproved. No biological models fitted. Primary source access, source identity and assay '
        'policy decisions remain explicit review work.\n')
    manifest = {'input_hashes':hashes([p/'manifest.json' for p in roots.values()]),
                'code_hashes':hashes([Path(__file__),HERE/'weekly_report.py']),
                'lock_hashes':hashes([HERE/'uv.lock']), 'output_hashes':hashes(list(output.iterdir())),
                'upstream_bundles_verified':list(roots), 'accepted_labels':0,'biological_models_fitted':0}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for key in ('ecotox','toxicity','review','sources','cohort','output'):
        parser.add_argument('--'+key,type = Path,required = True)
    args = parser.parse_args()
    result = build(args.ecotox,args.toxicity,args.review,args.sources,args.cohort,args.output)
    print(json.dumps(result,indent=2))
