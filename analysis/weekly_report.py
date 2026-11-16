"""Verify frozen pilot products and assemble a readable cross-track walkthrough."""
import argparse
import hashlib
import html
import json
from pathlib import Path

import altair as alt
import polars as pl

from screen import HERE, hashes


def verify_manifest(path, archived_inputs = None, resolutions = None):
    """Verify recorded research input/output bytes, separately from historical code."""
    data = json.loads(Path(path).read_text())
    for key in ('input_hashes', 'output_hashes', 'hashes'):
        for filename, expected in data.get(key, {}).items():
            source = Path(filename)
            actual = None
            if source.is_file():
                with source.open('rb') as stream:
                    actual = hashlib.file_digest(stream, 'sha256').hexdigest()
            if actual != expected and key == 'input_hashes' and archived_inputs:
                replacement = archived_inputs.get(expected)
                if replacement is not None:
                    with Path(replacement).open('rb') as stream:
                        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
                    if actual == expected and resolutions is not None:
                        resolutions[str(source)] = str(replacement)
            if actual != expected:
                raise ValueError(f'Hash mismatch: {source}')
    return data


def table(frame, columns):
    headers = ''.join(f'<th>{html.escape(c)}</th>' for c in columns)
    lines = []
    for row in frame.to_dicts():
        values = [f'{row[c]:.3f}' if isinstance(row[c], float) else str(row[c]) for c in columns]
        lines.append('<tr>' + ''.join(f'<td>{html.escape(v)}</td>' for v in values) + '</tr>')
    return '<table><thead><tr>' + headers + '</tr></thead><tbody>' + ''.join(lines) + '</tbody></table>'


def run(toxicity, literature, models, ecotox, output, evidence = ()):
    roots = {k: Path(v).resolve() for k, v in
             {'toxicity': toxicity, 'literature': literature, 'models': models, 'ecotox': ecotox}.items()}
    output = Path(output).resolve()
    evidence = [Path(p).resolve() for p in evidence]
    if any(output.is_relative_to(p) or p.is_relative_to(output) for p in [*roots.values(), *evidence]):
        raise ValueError('Output must be separate from source bundles')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use an empty output directory')
    archived, resolutions = {}, {}
    for root in evidence:
        saved = json.loads((root / 'manifest.json').read_text())
        archived.update({value: Path(key) for key, value in saved.get('output_hashes', {}).items()})
    manifests = {key: verify_manifest(root / 'manifest.json', archived, resolutions)
                 for key, root in roots.items()}
    for root in evidence:
        verify_manifest(root / 'manifest.json', archived, resolutions)
    report = pl.read_csv(roots['models'] / 'reports.csv')
    coefficients = pl.read_csv(roots['models'] / 'coefficients.csv')
    weights = coefficients.group_by('feature').agg(
        pl.col('coefficient').mean().alias('mean_coefficient'),
        pl.col('coefficient').std().alias('fold_sd'), pl.len().alias('folds'),
        (pl.col('coefficient') > 0).sum().alias('positive_folds')).sort(
            pl.col('mean_coefficient').abs(), descending = True)
    oob = pl.read_csv(roots['models'] / 'oob_importance.csv').sort('mean_f1_drop', descending = True)
    compounds = pl.read_csv(roots['toxicity'] / 'compounds.csv')
    group_summary = compounds.group_by('group').agg(
        pl.len().alias('eligible_compounds'), pl.col('median_mg_kg').count().alias('exact_compounds'),
        pl.col('median_mg_kg').median().alias('median_of_compound_medians_mg_kg')).sort('group')
    descriptors = pl.read_csv(roots['literature'] / 'descriptor_summary.csv')
    leads = pl.read_csv(roots['literature'] / 'literature_evidence.csv')
    overlap = leads.join(compounds, on = 'compound_id', how = 'inner').select(
        'compound_id', 'name', 'source_id', 'median_mg_kg', 'ld50_bin',
        'natural_origin', 'herbicidal_activity')
    source_chemicals = pl.read_parquet(roots['ecotox'] / 'chemicals.parquet')
    source_overlap = source_chemicals.filter(pl.col('candidate_existing_ids') != '').with_columns(
        pl.col('candidate_existing_ids').str.split(';').alias('compound_id')).explode('compound_id').join(
            leads, on = 'compound_id', how = 'inner').select(
                'source_chemical_id', 'chemical_name', 'dtxsid', 'compound_id', 'name',
                'source_id', 'test_records', 'result_records', 'identity_status')
    ec = manifests['ecotox']
    tox = manifests['toxicity']
    lit = manifests['literature']
    cutoffs = ', '.join(f'{v:g}' for v in tox['policy']['cutoffs'])
    overview = (
        f"EPA rat oral pilot: {tox['counts']['inventory']} cached source chemicals; "
        f"{sum(group_summary['exact_compounds'])} compounds with exact medians; "
        f"{tox['record_status'].get('censored', 0)} censored records kept separate. "
        f"Pooled exploratory cutoffs: {cutoffs} mg/kg. "
        f"Literature: {lit['counts']['supported_unique_leads']} provisional structures from "
        f"{lit['counts']['sources']} publications versus {lit['counts']['selected_herbicides']} "
        f"selected-herbicide structures. ECOTOX: {ec['counts']['chemicals']:,} source chemicals, "
        f"{ec['counts']['tests']:,} tests, {ec['counts']['results']:,} results; "
        f"{ec['candidate_selection_overlap']} candidate selection overlaps.")
    gaps = [
        ('The three biological groups are not established. All literature origin/activity labels remain '
        'unknown pending source structure, isolation, assay-policy and scientific review. Dietary '
        'comparators cannot supply tested-negative labels.'),
        ('Source screening is AI-assisted. The 1998 phenolic paper was screened at publisher-abstract '
        'level; full methods/figures remain pending. For 2020/2024, PDF treatment tables were checked '
        'but compound-level source identities and response labels were not adjudicated.'),
        ('The LD50 pilot is restricted to the existing purposive EPA cache, not the ECOTOX discovery '
        'population. Qualifiers, heterogeneous acute contexts and possible cross-reference duplicate '
        'studies limit interpretation; lower LD50 means greater toxicity.'),
        ('ECOTOX preflight preserves raw source keys and samples. Full endpoint decoding, normalization, '
        'source-specific identity approval, origin annotation and cross-source study reconciliation '
        'remain follow-up work.'),
        ('Current models predict selection membership. Five-fold scaffold support remains required for '
        'a reviewed activity model; no biological model was fitted. OOB repeat SD is not a statistical '
        'significance test and OOB predictions do not provide scaffold independence.')]
    next_steps = [
        ('Review the source structures and primary isolation references for the 15 leads; then review '
        'the 2024 low-response conditions and the 1998 full paper. Keep field performance separate '
        'from broad plant inactivity.'),
        ('Agree one assay-specific activity policy and record human scientific approvals before '
        'transferring any labels. Preserve Li 7b identity hold and all earlier frozen worksheets.'),
        ('Use the ECOTOX chemical inventory to prioritize DTXSID/source-identity review and natural '
        'occurrence searches. Implement conservative endpoint normalization as a separate increment.'),
        ('Reassess both-class scaffold support after approved labels exist; reserve independent '
        'publication evidence before activity-model selection or candidate scoring.')]
    output.mkdir(parents = True, exist_ok = True)
    weights.write_csv(output / 'logistic_weight_summary.csv')
    overlap.write_csv(output / 'literature_ld50_overlap.csv')
    source_overlap.write_csv(output / 'ecotox_literature_candidates.csv')
    figure = alt.Chart(alt.Data(values = report.to_dicts())).mark_bar().encode(
        x = alt.X('f1:Q', scale = alt.Scale(domain = [0, 1]), title = 'Scaffold-held-out F1'),
        y = alt.Y('profile:N', sort = '-x', title = None),
        tooltip = ['profile:N', 'f1:Q', 'precision:Q', 'recall:Q']).properties(
            width = 620, height = 240)
    # Cohort size comes from the verified report rather than a display-only constant.
    figure = figure.properties(title = f'Selection classification; threshold 0.5, n={report["n"][0]}')
    figure.save(output / 'model_f1.svg')
    source_packets = json.loads((roots['literature'] / 'source_packets.json').read_text())
    sources = ''.join('<li><a href="' + html.escape(s['url'], quote = True) + '">' +
                      html.escape(s['doi']) + '</a>: ' + html.escape(s['locator']) + '</li>'
                      for s in source_packets)
    parts = [
        '<h1>Weekly research pilots</h1><p class="date">10 November 2026 · Local research checkpoint</p>',
        '<p class="lead">' + html.escape(overview) + '</p>',
        '<p><strong>Status:</strong> pilot workflows verified; biological labels remain unapproved.</p>',
        '<h2>Track 1: measured acute rat oral toxicity</h2>',
        table(group_summary, group_summary.columns),
        ('<p>One compound median per exact-value compound. Censored bounds do not estimate tertiles. '
        'Source selection groups are explicitly unreviewed for biological activity.</p>'),
        (roots['toxicity'] / 'ld50_distribution.svg').read_text(),
        (roots['toxicity'] / 'ld50_bins.svg').read_text(),
        '<h2>Track 2: what the literature leads look like</h2>',
        ('<p>Provisional full-key database identities; single structures, no accepted training labels. '
        'MW: g/mol; TPSA: Å²; logP: calculated; HBD/HBA: counts. '
        'Tables report individual-descriptor denominators.</p>'),
        table(descriptors, descriptors.columns),
        (roots['literature'] / 'descriptors.svg').read_text(),
        '<h3>Literature leads with cached rat oral evidence</h3>', table(overlap, overlap.columns),
        '<h3>ECOTOX source chemicals overlapping literature leads</h3>',
        ('<p>DTXSID overlaps are identity-review candidates only. Source observations and natural '
        'occurrence require review before any biological grouping.</p>'),
        table(source_overlap, source_overlap.columns),
        '<h2>Model diagnostics</h2>',
        (output / 'model_f1.svg').read_text(),
        table(report, ['profile', 'n', 'precision', 'recall', 'f1', 'roc_auc', 'balanced_accuracy']),
        ('<h3>Formula logistic weights</h3><p>Target=1: selected herbicide. Coefficients are log-odds '
        'per training-fold standard deviation; summaries span five folds. Correlated features prevent '
        'causal interpretation. PCA loadings are not substituted for these raw-feature weights.</p>'),
        table(weights.head(10), weights.columns),
        ('<h3>Forest OOB permutation importance</h3><p>Top ten Morgan bits by mean OOB F1 decrease; '
        '10 seeded repeats. Bits require substructure inspection before chemical interpretation.</p>'),
        table(oob.head(10), oob.columns),
        '<h2>Evidence gaps</h2><ul>' + ''.join('<li>' + html.escape(v) + '</li>' for v in gaps) + '</ul>',
        '<h2>Next research steps</h2><ol>' + ''.join('<li>' + html.escape(v) + '</li>' for v in next_steps) + '</ol>',
        '<h2>Primary publications</h2><ul>' + sources + '</ul>',
        ('<p>All upstream research input/output hashes were verified before this report was written. '
        'Historical code hashes are preserved separately; the report does not rewrite old bundles.</p>')]
    style = ('body{font:16px/1.55 system-ui,sans-serif;color:#19303c;max-width:1100px;margin:40px auto;'
             'padding:0 28px}h1{font-size:36px}h2{margin-top:40px;border-bottom:2px solid #d9e8e3;'
             'padding-bottom:8px}.date{color:#60727b}.lead{font-size:19px}table{border-collapse:collapse;'
             'font-size:13px;display:block;overflow:auto;margin:20px 0}th,td{padding:8px 12px;'
             'border-bottom:1px solid #dce5e8;text-align:left}th{background:#edf4f2}svg{max-width:100%;'
             'height:auto;margin:18px 0}li{margin:10px 0}a{color:#116d58}')
    (output / 'walkthrough.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8">'
                                            '<meta name="viewport" content="width=device-width,initial-scale=1">'
                                            '<title>Weekly research pilots</title><style>' + style + '</style>'
                                            '<body>' + ''.join(parts) + '</body></html>')
    markdown = '# Weekly research pilots — 10 November 2026\n\n' + overview + '\n\n'
    markdown += 'Open `walkthrough.html` for figures, metrics, weights, sources and the cross-track overlap.\n\n'
    markdown += '## Evidence gaps\n\n' + '\n'.join('- ' + v for v in gaps) + '\n\n'
    markdown += '## Next steps\n\n' + '\n'.join(f'{i}. {v}' for i, v in enumerate(next_steps, 1)) + '\n'
    (output / 'README.md').write_text(markdown)
    inputs = [r / 'manifest.json' for r in roots.values()] + [r / 'manifest.json' for r in evidence]
    manifest = {'input_hashes': hashes(inputs), 'code_hashes': hashes([Path(__file__)]),
                'lock_hashes': hashes([HERE / 'uv.lock', HERE / 'pyproject.toml']),
                'output_hashes': hashes(list(output.iterdir())),
                'verified_upstream_bundles': [str(p.parent) for p in inputs],
                'archived_input_resolutions': resolutions,
                'activity_model': 'unavailable_unapproved_labels',
                'literature_ld50_overlap': overlap.height,
                'ecotox_literature_candidates': source_overlap.height}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for name in ('toxicity', 'literature', 'models', 'ecotox', 'output'):
        parser.add_argument(f'--{name}', type = Path, required = True)
    parser.add_argument('--evidence', type = Path, action = 'append', default = [])
    args = parser.parse_args()
    print(json.dumps(run(args.toxicity, args.literature, args.models, args.ecotox, args.output,
                         args.evidence), indent = 2))
