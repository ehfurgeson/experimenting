"""Synthesize qualified sprint products without adopting new labels or fitting models."""

import argparse
import csv
import gzip
import json
import shutil
from collections import Counter, defaultdict
from importlib.metadata import version
from pathlib import Path

import altair as alt
import polars as pl

from data_sprint import read_csv, sha256, write_csv


def compressed_rows(path):
    with gzip.open(path, 'rt', newline = '') as stream:
        yield from csv.DictReader(stream)


def verify_bundle(path):
    path = Path(path)
    manifest = json.loads((path / 'manifest.json').read_text())
    for name, digest in manifest['products'].items():
        if sha256(path / name) != digest:
            raise ValueError(f'Product hash mismatch: {path / name}')
    for name, digest in manifest['inputs'].items():
        if sha256(name) != digest:
            raise ValueError(f'Upstream input hash mismatch: {name}')
    return manifest


def summarize_overlap(rows):
    summary = []
    for cohort in sorted({r['cohort'] for r in rows}):
        members = [r for r in rows if r['cohort'] == cohort]
        for field in ['coconut_exact', 'npass_exact', 'either_catalog_exact',
                      'taxon_publication_linked_unreviewed', 'adopted_occurrence',
                      'measured_a', 'adopted_plant_response', 'catalog_measured_plant',
                      'linked_occurrence_measured_plant', 'adopted_occurrence_measured_plant',
                      'chembl_plant_review_candidate']:
            summary.append({'cohort': cohort, 'metric': field,
                            'rows_with_evidence': sum(bool(r.get(field)) for r in members),
                            'cohort_rows': len(members),
                            'unique_full_structures': len({r['full_inchikey'] for r in members
                                                           if r.get(field) and r['full_inchikey']})})
    return summary


def run(paths, output):
    output = Path(output)
    manifests = {name: verify_bundle(paths[name])
                 for name in ['baseline', 'npass', 'coconut', 'context', 'toxval', 'plant']}
    if 'chembl' in paths:
        manifests['chembl'] = verify_bundle(paths['chembl'])
    adoption = paths['adoption']
    adoption_manifest = json.loads((adoption / 'manifest.json').read_text())
    for name, digest in adoption_manifest['output_hashes'].items():
        if sha256(name) != digest:
            raise ValueError(f'Adopted bundle hash mismatch: {name}')
    inputs = [paths[name] / 'manifest.json' for name in manifests]
    inputs += [adoption / p for p in ['manifest.json', 'origin_labels.csv',
                                      'accepted_activity_features.csv', 'contrast_features.parquet']]
    before = {str(p): sha256(p) for p in inputs}
    baseline = read_csv(paths['baseline'] / 'cohort_membership.csv')
    if Counter(r['cohort'] for r in baseline) != {'A': 4234, 'B': 43128, 'selection': 176}:
        raise ValueError('This dated synthesis requires the frozen 2026-11-12 cohorts')
    selection_paths = [Path(p) for p in manifests['baseline']['inputs'] if p.endswith('.parquet')]
    if len(selection_paths) != 1:
        raise ValueError('One frozen selection source required for compound names')
    selection_names = {r['compound_id']: r['query']
                       for r in pl.read_parquet(selection_paths[0]).to_dicts()}
    catalog = {}
    for name in ('npass', 'coconut'):
        catalog[name] = {(r['cohort'], r['compound_id']): r
                         for r in read_csv(paths[name] / f'{name}_overlap.csv')}
    occurrences, occurrence_refs = set(), defaultdict(set)
    for row in compressed_rows(paths['context'] / 'npass_occurrences.csv.gz'):
        if row['occurrence_evidence_type'] == 'taxon_and_publication_linked_unreviewed':
            occurrences.add(row['full_inchikey'])
            occurrence_refs[row['full_inchikey']].add(row['citation'])
    activity = [r for r in read_csv(adoption / 'accepted_activity_features.csv')
                if r['structure_status'] == 'valid' and r['activity_target'] in {'0', '1', '0.0', '1.0'}]
    activity_keys = {r['structure_inchikey'] for r in activity}
    native_keys = {r['compound_id']: r['full_inchikey'] for r in baseline
                   if r['cohort'] == 'selection' and r['identity_status'] == 'valid'}
    for row in pl.read_parquet(adoption / 'contrast_features.parquet').to_dicts():
        if row['structure_status'] == 'valid':
            native_keys[row['compound_id']] = row['structure_inchikey']
    adopted_occurrences = {native_keys[r['compound_id']] for r in read_csv(adoption / 'origin_labels.csv')
                           if r['natural_origin'] == 'natural' and r['compound_id'] in native_keys}
    a_keys = {r['full_inchikey'] for r in baseline if r['cohort'] == 'A'}
    b_keys = {r['full_inchikey'] for r in baseline if r['cohort'] == 'B'}
    chembl_keys = set()
    if 'chembl' in paths:
        chembl_keys = {r['full_inchikey']
                       for r in read_csv(paths['chembl'] / 'plant_activity_observations.csv')
                       if r['identity_status'] == 'valid' and
                       'Logran_formulated_control' not in r['hold_reasons']}
    rows, queue = [], []
    for row in baseline:
        key = row['full_inchikey']
        item = {k: row[k] for k in ['cohort', 'compound_id', 'full_inchikey', 'selection_group',
                                    'identity_status', 'target_log10_mg_kg']}
        for name in ('npass', 'coconut'):
            match = catalog[name][(row['cohort'], row['compound_id'])]
            item[name + '_exact'] = match['match_tier'] == 'exact_full_key'
            item[name + '_match_tier'] = match['match_tier']
            item[name + '_catalog_ids'] = match['catalog_ids']
        item.update(either_catalog_exact = item['npass_exact'] or item['coconut_exact'],
                    taxon_publication_linked_unreviewed = key in occurrences,
                    adopted_occurrence = key in adopted_occurrences,
                    measured_a = key in a_keys, teacher_b_screening_only = key in b_keys,
                    adopted_plant_response = key in activity_keys,
                    chembl_plant_review_candidate = key in chembl_keys,
                    occurrence_citations = ';'.join(sorted(occurrence_refs[key])))
        item['catalog_measured_plant'] = (item['either_catalog_exact'] and item['measured_a'] and
                                          item['adopted_plant_response'])
        item['linked_occurrence_measured_plant'] = (
            item['taxon_publication_linked_unreviewed'] and item['measured_a'] and
            item['adopted_plant_response'])
        item['adopted_occurrence_measured_plant'] = (
            item['adopted_occurrence'] and item['measured_a'] and item['adopted_plant_response'])
        rows.append(item)
        if row['cohort'] == 'selection':
            missing = []
            if row['identity_status'] != 'valid':
                missing.append('resolve_full_structure')
            if not item['adopted_occurrence']:
                missing.append('verify_taxon_reference_occurrence')
            if not item['measured_a']:
                missing.append('obtain_measured_acute_rat_oral_ld50')
            if not item['adopted_plant_response']:
                missing.append('recover_compatible_plant_high_low_response')
            queue.append({'compound_id': row['compound_id'], 'full_inchikey': key,
                          'compound_name': selection_names.get(row['compound_id'], ''),
                          'selection_group': row['selection_group'],
                          'priority_score': int(item['either_catalog_exact']) + int(item['measured_a'])
                                            + int(item['adopted_plant_response'])
                                            + int(item['taxon_publication_linked_unreviewed']),
                          'missing_evidence': ';'.join(missing),
                          'occurrence_citations': item['occurrence_citations'],
                          'measured_a': item['measured_a'],
                          'adopted_plant_response': item['adopted_plant_response'],
                          'coconut_match_tier': item['coconut_match_tier'],
                          'npass_match_tier': item['npass_match_tier'],
                          'teacher_b_screening_only': item['teacher_b_screening_only'],
                          'review_status': 'research_queue_not_safety_ranking'})
    queue.sort(key = lambda r: (-r['priority_score'], r['compound_id']))
    output.mkdir(parents = True, exist_ok = False)
    with gzip.open(output / 'cohort_overlap.csv.gz', 'wt', newline = '') as stream:
        writer = csv.DictWriter(stream, fieldnames = list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = summarize_overlap(rows)
    write_csv(output / 'cohort_overlap_counts.csv', summary, list(summary[0]))
    write_csv(output / 'candidate_evidence_queue.csv', queue, list(queue[0]))
    # One descriptive source waterfall. Rows and structures have distinct units.
    waterfall = []
    for name in ('npass', 'coconut'):
        m = manifests[name]
        for stage, value in [('acquired_structure_records', m.get('source_structure_records',
                                                                 m.get('source_records'))),
                             ('valid_identity_records', m['identity_status']['valid']),
                             ('unique_valid_full_keys', m['unique_valid_full_keys']),
                             ('A_exact_full_key_matches', m['overlap']['A']['exact_full_key'])]:
            waterfall.append({'source': name, 'stage': stage, 'count': value})
    for source, counts in manifests['toxval']['tables'].items():
        for stage, value in counts.items():
            waterfall.append({'source': source, 'stage': stage, 'count': value})
    waterfall += [{'source': 'toxval', 'stage': name, 'count': manifests['toxval'][name]}
                  for name in ['candidate_net_new_exact_full_structures',
                               'candidate_net_new_censored_only_full_structures',
                               'net_new_eligible_full_structures']]
    write_csv(output / 'source_waterfall.csv', waterfall, ['source', 'stage', 'count'])
    # Stratified computational audit samples; independent human review remains pending.
    audit = []
    for name in ('npass', 'coconut'):
        for tier in ('exact_full_key', 'connectivity_only_review', 'unresolved'):
            examples = [r for r in rows if r['cohort'] == 'A' and r[name + '_match_tier'] == tier]
            for r in examples[:4]:
                audit.append({'source': name, 'stratum': tier, 'full_inchikey': r['full_inchikey'],
                              'catalog_ids': r[name + '_catalog_ids'],
                              'review_status': 'computational_checks_passed_human_review_pending'})
    a_by_dose = sorted((r for r in rows if r['cohort'] == 'A'),
                       key = lambda r: float(r['target_log10_mg_kg']))
    for label, examples in [('low_ld50', a_by_dose[:2]), ('high_ld50', a_by_dose[-2:])]:
        for r in examples:
            audit.append({'source': 'frozen_A', 'stratum': label, 'full_inchikey': r['full_inchikey'],
                          'catalog_ids': r['coconut_catalog_ids'],
                          'review_status': 'computational_checks_passed_human_review_pending'})
    write_csv(output / 'identity_audit_sample.csv', audit, list(audit[0]))
    figures = output / 'figures'
    figures.mkdir()
    a_rows = [r for r in rows if r['cohort'] == 'A']
    coverage = Counter(('Both catalogs' if r['npass_exact'] and r['coconut_exact'] else
                        'NPASS only' if r['npass_exact'] else 'COCONUT only' if r['coconut_exact'] else
                        'Neither exact catalog') for r in a_rows)
    plot = alt.Chart(alt.Data(values = [{'coverage': k, 'structures': v} for k, v in coverage.items()]))
    plot = plot.mark_bar(color = '#267888').encode(
        y = alt.Y('coverage:N', title = None), x = alt.X('structures:Q', title = 'A full structures'),
        tooltip = ['coverage:N', 'structures:Q']).properties(
            width = 520, height = 180, title = 'Frozen A catalog coverage (n=4,234); occurrence unverified')
    plot.save(figures / 'a_catalog_coverage.png')
    plot.save(figures / 'a_catalog_coverage.svg')
    distributions = []
    matched_n = sum(r['either_catalog_exact'] for r in a_rows)
    for r in a_rows:
        distributions.append({'group': f'Exact catalog match (n={matched_n:,})'
                              if r['either_catalog_exact'] else
                              f'No exact catalog match (n={len(a_rows) - matched_n:,})',
                              'log10_mg_kg': float(r['target_log10_mg_kg'])})
    plot = alt.Chart(alt.Data(values = distributions)).mark_bar(opacity = .7).encode(
        x = alt.X('log10_mg_kg:Q', bin = alt.Bin(step = .25), title = 'Measured log10(LD50, mg/kg)'),
        y = alt.Y('count():Q', title = 'A full structures'),
        color = alt.Color('group:N', title = None), row = alt.Row('group:N', title = None)
    ).properties(width = 520, height = 130, title = 'Descriptive source-selected LD50 distributions')
    plot.save(figures / 'a_ld50_catalog_distribution.png')
    plot.save(figures / 'a_ld50_catalog_distribution.svg')
    metrics = {r['metric']: r['rows_with_evidence'] for r in summary if r['cohort'] == 'A'}
    metrics.update(net_new_eligible_full_structures = 0, net_new_independent_studies = None,
                   candidate_new_exact_structures = manifests['toxval'][
                       'candidate_net_new_exact_full_structures'],
                   candidate_new_censored_only_structures = manifests['toxval'][
                       'candidate_net_new_censored_only_full_structures'],
                   adopted_occurrence_structures_resolved = len(adopted_occurrences))
    chembl_text = ''
    if 'chembl' in manifests:
        c = manifests['chembl']
        chembl_text = f'''
Targeted ChEMBL searches found 184 lettuce functional assays and 15 Arabidopsis
root-description assays. Six complete selected assays provide {c['activity_observations']}
observations from {c['source_publications']} publications, all review-only. Two
lettuce cultivars each contain 12 tested materials in the podolactone series.
Parsed primary text flags a formulated Logran control mapped to a single chemical
and an across-dose qualitative summary not clearly assignable to the database dose.
Primary PDF downloads returned 403 and screenshots failed; visual verification is
unavailable. These source-form/dose holds prevent new labels. Complete raw assay
rows, descriptions, bound qualifiers, molecule identities and hold reasons are
retained in the separate ChEMBL review bundle. No response bound is turned into an
exact effect. {metrics['chembl_plant_review_candidate']} A structures match the
provider-verified ChEMBL candidate identities after excluding the Logran form hold;
these remain distinct from adopted plant responses.
'''
    text = f'''# Data yield report — 17 November 2026

AI experimental source audit; new source evidence has not received independent scientific review.

The sprint adds a usable natural-catalog overlay and a bounded validation queue.
Frozen A remains 4,234 experimental full structures and B remains 43,128 teacher
structures. There are 176 prepared selection rows, including 116 selected natural
products. Source membership does not establish herbicidal activity or safety.

## Evidence gained

COCONUT has {manifests['coconut']['source_records']:,} source rows and
{manifests['coconut']['unique_valid_full_keys']:,} valid unique full keys after checking
every structure. A has **{metrics['coconut_exact']:,} exact COCONUT matches
({100 * metrics['coconut_exact'] / 4234:.1f}%)** and {metrics['npass_exact']:,} exact NPASS matches;
{metrics['either_catalog_exact']:,} match either catalog. These are catalog assertions.
NPASS taxon-plus-publication links cover {metrics['taxon_publication_linked_unreviewed']:,}
A structures, awaiting primary-source review. {metrics['adopted_occurrence']:,} A structures
map to already adopted occurrence evidence. Unknown origin remains unknown.

NPASS toxicity retains all 34,975 source rows, including 4,179 rat LD50 rows, but its
actual export omits route, acute context and experimental status. Zero rows pass
the complete endpoint contract. ToxValDB's selected TEST/ChemIDplus/ECHA workbooks
contain 116,596 rows. It supplies **{metrics['candidate_new_exact_structures']} candidate
new exact-value structures** and **{metrics['candidate_new_censored_only_structures']}
additional censored-only structures** through local unambiguous DTXSID links.
These are provisional identifier links, with tested-material and study-lineage holds.
**Confirmed net-new eligible structures: 0; net-new independent studies: unknown.**
Same-reference/value flags identify possible mirrors, not duplicate adjudications.
ChemIDplus experimental status is undetermined and is excluded from eligibility.

The local ECOTOX snapshot provides {manifests['plant']['growth_germination_biomass_results']:,}
non-algal plant growth/germination/biomass review records. Aquatic vascular plants
remain included and require habitat review. NPASS adds organism/protein/tissue
leads without enough protocol, dose, duration or control metadata to adopt labels.
No missing value, NOEC or publication omission becomes a tested low-response label.
{chembl_text}

## Integration and next decisions

Within A, catalog membership + measured toxicity + already adopted plant response
intersect in {metrics['catalog_measured_plant']} structures. Using NPASS unreviewed
taxon/publication links instead gives {metrics['linked_occurrence_measured_plant']};
using already adopted occurrence evidence gives
{metrics['adopted_occurrence_measured_plant']}. These tiers must remain separate.
The complete cohort/combination counts and the 176-row selection evidence queue
are companion CSV products. Queue scores prioritize closing evidence gaps; they
are not efficacy, safety or novelty predictions. B appears only as teacher screening.

The four accepted policies were rerun through existing activity preflight: K1998
5 high/0 low, Okamoto 4/0, Li 11/10, He 29/21. K1998/Okamoto lack both-class support;
Li/He lack sufficient class-bearing scaffolds. Li 7b's identity hold persists.
No new classifier or pooled plant model was fitted. The highest-value follow-up
is compatible primary plant-assay recovery with explicit highs/lows, alongside
targeted ToxValDB tested-form and source-reference review; broad extra downloads
would currently add less value than these audits.

## Methods, quality and limits

All joins use recomputed full InChIKeys and single-component structures. Source-key
conflicts, unresolved identities and connectivity-only candidates stay in review.
NPASS has 10,160 provider-key conflicts, 2,167 multicomponent forms, 1,418 invalid
structures, one missing key and one identical repeated compound-ID row. COCONUT
has 20 key conflicts, 4,247 multicomponent and four invalid structures. No salts or
stereoisomers were merged. Unspecified atom stereocenters are recorded, not resolved.

Raw exports, source versions/URLs/timestamps/licenses, native/stored hashes and
failed attempts remain local. Compressed text avoids filling the local disk.
Preliminary/aborted runs remain identified separately; canonical input paths are
listed in this report's manifest. Original frozen bundles were verified and preserved.
The 28-row stratified identity/extreme-dose audit is computational and awaits human review.
Plots compare source-selected groups with all denominators; unmatched origin is
unknown, naturalness is not safety and the LD50 distributions have no causal or
population interpretation. Exact medians use existing A context, not new pooling.
Source studies, tested forms, duration, controls and publication independence remain
the main scientific limitations. No retraining or source refresh is justified yet.
'''
    (output / 'DATA_YIELD_REPORT.md').write_text(text)
    (output / 'summary.json').write_text(json.dumps(metrics, indent = 2) + '\n')
    if before != {str(p): sha256(p) for p in inputs}:
        raise ValueError('Inputs changed during report')
    reproduction = output / 'reproduction'
    reproduction.mkdir()
    for p in [Path(__file__), Path(__file__).with_name('data_sprint.py')]:
        shutil.copyfile(p, reproduction / p.name)
    manifest = {'inputs': before, 'canonical_bundles': {k: str(v) for k, v in paths.items()},
                'versions': {p: version(p) for p in ['rdkit', 'polars', 'altair', 'vl-convert-python']},
                'locks': {str(p): sha256(p) for p in [Path('analysis/uv.lock'),
                                                       Path('pipeline/uv.lock')]},
                'products': {str(p.relative_to(output)): sha256(p)
                             for p in output.rglob('*') if p.is_file()}}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2) + '\n')
    return metrics


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    names = ['baseline', 'npass', 'coconut', 'context', 'toxval', 'plant', 'adoption']
    for name in [*names, 'output']:
        parser.add_argument('--' + name, type = Path, required = True)
    parser.add_argument('--chembl', type = Path)
    args = parser.parse_args()
    paths = {k: getattr(args, k) for k in names}
    if args.chembl:
        paths['chembl'] = args.chembl
    print(json.dumps(run(paths, args.output), indent = 2))
