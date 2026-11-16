"""Cross-source coverage and group descriptions after separate A/B evaluation."""
import argparse
import csv
import html
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

import polars as pl
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator

from evidence_models import residual_plot, svg
from evidence_release import number, sha, structure, write_csv


def read(path):
    with Path(path).open() as stream:
        return list(csv.DictReader(stream))


def verify(root):
    manifest = json.loads((root / 'manifest.json').read_text())
    for name, expected in manifest['outputs'].items():
        if sha(root / name) != expected:
            raise ValueError('Frozen hash mismatch: ' + name)
    return manifest


def reconcile_test_rows(rows):
    """Collapse repeated exact structure/model outputs; retain conflicts for review."""
    byrecord = defaultdict(list)
    for r in rows:
        key = (r.get('full_key') or r['compound_id'], r['source_name'], r['model_name'], r['endpoint'], r['predicted_unit'])
        byrecord[key].append(r)
    merged, duplicate_audit = [], []
    for key, records in sorted(byrecord.items()):
        values = {(r['predicted_value'], r['ad_conclusion']) for r in records}
        if len(records) > 1:
            duplicate_audit.append({'key': json.dumps(key), 'records': len(records),
                                    'distinct_value_domain_pairs': len(values),
                                    'status': 'same_output_collapsed' if len(values) == 1
                                    else 'conflict_no_primary_value'})
        if len(values) == 1:
            merged.append(records[0])
    return merged, duplicate_audit


def run(release, models, dietary, traits, output):
    release, models, dietary, traits, output = map(Path, (release, models, dietary, traits, output))
    if output.exists() or any(output.resolve().is_relative_to(p.resolve())
                              for p in (release, models, dietary)):
        raise ValueError('Choose a separate new output root')
    manifests = [verify(p) for p in (release, models, dietary)]
    if manifests[1]['release_manifest_sha256'] != sha(release / 'manifest.json'):
        raise ValueError('Evaluation used a different release')
    expected_traits = next((v for k, v in manifests[0]['inputs'].items()
                            if Path(k).resolve() == traits.resolve()), None)
    if expected_traits != sha(traits):
        raise ValueError('Group metadata must match the frozen release input')
    output.mkdir(parents = True)
    metadata, memberships = defaultdict(set), []
    for r in pl.read_parquet(traits).to_dicts():
        identity = structure(r.get('canonical_smiles'))
        if identity.get('full_key'):
            group = 'selected_' + r['chemical_group']
            metadata[identity['full_key']].add(group)
            memberships.append({'full_key': identity['full_key'], 'compound_id': r['compound_id'],
                                'source_cohort': 'original_selection', 'selection_group': group,
                                'origin_activity_inference': 'none'})
    feature_path = Path(next(iter(manifests[2]['input'])))
    if sha(feature_path) != manifests[2]['input'][str(feature_path)]:
        raise ValueError('Dietary input changed')
    for r in pl.read_parquet(feature_path).to_dicts():
        metadata[r['structure_inchikey']].add('dietary_inventory')
        memberships.append({'full_key': r['structure_inchikey'], 'compound_id': r['compound_id'],
                            'source_cohort': 'dietary_inventory', 'selection_group': None,
                            'origin_activity_inference': 'none'})
    write_csv(output / 'cohort_memberships.csv', memberships)

    def group(key):
        labels = sorted(v for v in metadata[key] if v.startswith('selected_'))
        return ';'.join(labels) if labels else 'dietary_inventory_only' if metadata[key] else (
            'source_inventory_unknown_group')

    descriptive = []
    for pathway in ('A', 'B'):
        bygroup = defaultdict(list)
        for r in read(release / f'{pathway}_compounds.csv'):
            bygroup[group(r['full_key'])].append(r)
        for name, rows in sorted(bygroup.items()):
            counts = Counter(r['ld50_bin'] for r in rows)
            descriptive.append({'pathway': pathway, 'group': name, 'compounds': len(rows),
                                'median_log10_mg_kg': median(float(r['target_log10_mg_kg'])
                                                           for r in rows),
                                **{f'bin_{k}_n': counts[str(k)] for k in range(3)},
                                'interpretation': 'selection_membership_not_activity_or_safety'})
    write_csv(output / 'descriptive_groups.csv', descriptive)
    identity_bycid = {r['compound_id'].upper(): r['full_key'] for r in memberships}
    original = read(release / 'B_TEST_cache.csv')
    additional = read(dietary / 'B_TEST_predictions.csv')
    rows = [{**r, 'batch': batch, 'full_key': identity_bycid.get(r['compound_id']),
             'group': group(identity_bycid.get(r['compound_id']))}
            for batch, records in [('original_cache', original), ('dietary_expansion', additional)]
            for r in records]
    write_csv(output / 'B_TEST_all_batches.csv', rows)
    merged, duplicate_audit = reconcile_test_rows(rows)
    write_csv(output / 'TEST_duplicate_audit.csv', duplicate_audit)
    endpoint_groups = defaultdict(list)
    for r in merged:
        endpoint_groups[(r['endpoint'], r['source_name'], r['predicted_unit'], r['group'],
                         r['ad_conclusion'])].append(r)
    write_csv(output / 'TEST_group_coverage.csv', [
        {'endpoint': k[0], 'version': k[1], 'unit': k[2], 'group': k[3], 'domain': k[4],
         'compounds': len(rs), 'finite': sum(number(r['predicted_value']) is not None for r in rs),
         'median_original_scale': median(vals) if (vals := [number(r['predicted_value'])
              for r in rs if number(r['predicted_value']) is not None]) else None,
         'normalization': 'raw_provider_scale_retained_no_molar_conversion'}
        for k, rs in sorted(endpoint_groups.items())])
    pairs = read(models / 'paired_agreement.csv')
    # Identity/scaffold similarity to the archived known-training chemical inventory.
    # It cannot establish exact-study overlap or absence from later teacher training.
    trained = {r['full_key'] for r in read(release / 'B_predictions.csv') if
               r['training_membership'] == 'Tr' and r['full_key'] and
               'provider_full_key_mismatch' not in r['reasons'] and
               'invalid_or_missing_structure' not in r['reasons']}
    identities = {r['full_key']: r for r in read(release / 'chemical_identity.csv')
                  if r['source_cohort'] == 'CATMoS' and r['identity_status'] == 'valid'}
    generator = rdFingerprintGenerator.GetMorganGenerator(radius = 2, fpSize = 1024)
    references = [generator.GetFingerprint(Chem.MolFromSmiles(identities[k]['smiles']))
                  for k in sorted(trained) if k in identities]
    for r in pairs:
        key = r['full_key']
        r['group'] = group(key)
        r['known_teacher_training_compound'] = key in trained
        r['max_morgan_similarity_to_archived_training'] = 1.0 if key in trained else max(
            DataStructs.BulkTanimotoSimilarity(generator.GetFingerprint(
                Chem.MolFromSmiles(identities[key]['smiles'])), references), default = None)
        r['independence'] = 'known_training_compound_overlap' if key in trained else (
            'unknown_shared_source_lineage')
    write_csv(output / 'paired_lineage_group_similarity.csv', pairs)
    bygroup = defaultdict(list)
    for r in pairs:
        bygroup[(r['group'], r['independence'])].append(r)
    write_csv(output / 'paired_group_summary.csv', [
        {'group': k[0], 'independence': k[1], 'n': len(rs),
         'median_B_minus_A_log10': median(float(r['difference_B_minus_A']) for r in rs),
         'same_bin_fraction': sum(r['A_bin'] == r['B_bin'] for r in rs) / len(rs)}
        for k, rs in sorted(bygroup.items())])
    oldids, newids = {r['compound_id'] for r in original}, {r['compound_id'] for r in additional}
    summary = {
        'original_TEST_compounds': len(oldids), 'dietary_TEST_compounds': len(newids),
        'additional_TEST_compounds': len(newids - oldids), 'union_TEST_compounds': len(oldids | newids),
        'unique_TEST_full_structures': len({r['full_key'] for r in rows if r['full_key']}),
        'TEST_records_without_structure_membership': sum(not r['full_key'] for r in rows),
        'raw_TEST_batch_rows': len(rows), 'deduplicated_TEST_endpoint_rows': len(merged),
        'dietary_acquisition_states': manifests[2]['states'],
        'paired_compounds': len(pairs),
        'paired_known_teacher_training_compounds': sum(r['known_teacher_training_compound']
                                                       for r in pairs),
        'C': 'defer', 'TEST_numeric_model_status': 'not_fitted_pending_API_scale_and_form_audit',
        'plant_activity_external_model': 'no_fit_for_purpose_model_qualified',
        'source_backlog': [
            'Resolve remaining 160 dietary names with primary identity/occurrence review',
            'Review two dietary EPA identity ambiguities; preserve Li identity holds',
            'Qualify local TEST installation and CTX unit scale; do not infer transforms from range',
            'Qualify VEGA endpoint/version/AD batch execution',
            'Qualify GenRA analogues and OECD Toolbox workflow; no predictions yet acquired',
            'Original-study/tested-form review for ICE and shared teacher sources',
            'Zenodo pLD50 scale/source reconciliation before normalization',
            'Kuehn Daphnia transcription and benzoic-acid fulltext access gap',
            'Further documented natural-product inventories with exact forms and source cohorts'],
        'limits': 'Source membership is not natural origin, inactivity or safety. '
                  'No count of independent measured studies is established. '
                  'Source tags and similarity are not proof of exact-study independence.'}
    (output / 'summary.json').write_text(json.dumps(summary, indent = 2) + '\n')
    metrics = read(models / 'pooled_metrics.csv')
    def cells(record):
        values = []
        for key in ('pathway', 'task', 'profile', 'n', 'mae_log10', 'macro_f1'):
            value = record.get(key, '')
            if key in {'mae_log10', 'macro_f1'} and value:
                value = f'{float(value):.3f}'
            values.append('<td>' + html.escape(str(value)) + '</td>')
        return '<tr>' + ''.join(values) + '</tr>'
    table = ''.join(cells(r) for r in metrics)
    charts = []
    for name in ('paired_agreement.svg', 'residuals.svg'):
        if name == 'residuals.svg':
            histogram = read(models / 'residual_histogram.csv')
            for r in histogram:
                for key in ('left', 'right', 'count'):
                    r[key] = float(r[key])
            content = svg(residual_plot(histogram))
        else:
            content = (models / name).read_text()
        (output / name).write_text(content)
        charts.append(content)
    backlog = ''.join('<li>' + html.escape(r) + '</li>' for r in summary['source_backlog'])
    counts = manifests[0]['counts']
    report = f'''<!doctype html><html lang="en"><meta charset="utf-8">
    <title>Measured and modeled evidence: first release</title>
    <style>body{{font:17px system-ui;line-height:1.5;max-width:1040px;margin:40px auto;
    padding:0 24px;color:#203239}}h1,h2{{color:#174b47}}table{{border-collapse:collapse}}
    td,th{{padding:8px 12px;text-align:left;border-bottom:1px solid #ddd}}
    svg{{max-width:100%;height:auto}}a{{color:#175d78}}</style>
    <h1>Measured outcomes and outside-model estimates</h1>
    <p>First collection release · 12 November 2026 · AI experimental.</p>
    <h2>Completed</h2><p>The provisional A cohort has {counts['A_compounds']:,} full structures
    with exact experimental compound medians. B has {counts['B_compounds']:,} structures with
    eligible Inside-domain CATMoS estimates. TEST coverage grew from 136 to
    {summary['unique_TEST_full_structures']} full structures after an exact-identity dietary batch.
    Two dietary EPA identities remain under review. Censored records, mixtures, missing outputs,
    domain exclusions and conflicting predictions remain in separate audit tables.</p>
    <p>Five outer folds keep scaffolds and connectivity together. Seven features are calculated
    from structures. A targets experimental outcomes; B targets a teacher estimate. Source
    membership supplies no natural-origin, plant-inactivity or safety label. Repeated records
    are not independent studies.</p>
    <table><tr><th>Pathway</th><th>Task</th><th>Profile</th><th>Held-out n</th>
    <th>MAE log10 dose</th><th>Macro-F1</th></tr>{table}</table>
    <p>Fixed historical cohort cutoffs are 1,080 and 3,400 mg/kg. These are low/medium/high
    LD50 bins, not regulatory categories. Lower LD50 means greater acute hazard. A log10 dose
    error of one means a tenfold dose difference. The A forest's MAE improvement is small.</p>
    <h2>Provisional agreement</h2><p>Of {summary['paired_compounds']:,} exact-key pairs,
    {summary['paired_known_teacher_training_compounds']:,} are known teacher-training compounds.
    Agreement is dominated by overlap and cannot establish independent validation.</p>{charts[0]}
    <p>The plot displays a deterministic sample of up to 1,000 pairs. Full tables retain every
    pair, training tag, group membership and similarity. Actual tested forms, original studies,
    purity and dose context need further review. TEST molar outputs have not been converted.</p>
    <h2>Held-out residuals</h2>{charts[1]}<p>Panels separate pathways and profiles, with
    independent count scales. Complete unbinned predictions remain in the model bundle.</p>
    <h2>Decision: defer combined pathway C</h2><p>Original-study and teacher-training
    independence are insufficient for an untouched experimental evaluation. No combined fit
    was run. B scores measure teacher reproduction, not experimental accuracy.</p>
    <p>Per-fold logistic weights and OOB permutation diagnostics are retained. The binary
    whole-cohort OOB diagnostic is separate from scaffold validation. Its repeat SD is
    stability, not a p-value. No calibrated intervals, original-publication/provider holdouts,
    measured-feature cohort or qualified external plant-activity model are available.</p>
    <h2>Planned source work</h2><ul>{backlog}</ul>
    <p>See <a href="summary.json">source/status summary</a>,
    <a href="descriptive_groups.csv">group distributions</a> and
    <a href="paired_group_summary.csv">paired group/lineage summary</a>.
    Raw scientific assets remain local. This release does not establish safer candidates
    or field efficacy.</p></html>'''
    (output / 'walkthrough.html').write_text(report)
    (output / 'reproduction').mkdir()
    code = [Path(__file__), Path(__file__).parent / 'evidence_models.py',
            Path(__file__).parent / 'evidence_release.py']
    for p in code:
        (output / 'reproduction' / p.name).write_bytes(p.read_bytes())
    manifest = {'inputs': {str(p / 'manifest.json'): sha(p / 'manifest.json')
                           for p in (release, models, dietary)},
                'traits_input': {str(traits): sha(traits)},
                'code': {str(p): sha(p) for p in code},
                'outputs': {str(p.relative_to(output)): sha(p) for p in sorted(output.rglob('*'))
                            if p.is_file()}}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2) + '\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for name in ('release', 'models', 'dietary', 'traits', 'output'):
        parser.add_argument('--' + name, type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(run(args.release, args.models, args.dietary, args.traits, args.output), indent = 2))
