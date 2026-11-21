"""Build a traceable evidence review for low-LD50 catalog matches."""

import argparse
import csv
import gzip
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from data_sprint import read_csv, sha256
from evidence_release import ld50_bin
from research_followup import lotus_overlay
from sprint_report import verify_bundle

BINS = ('low', 'medium', 'high')
REVIEW_STATUSES = {'primary_biosynthesis_supported', 'documented_pesticide_use_origin_unverified'}
OCCURRENCE_FIELDS = ('taxon_name', 'citation', 'source_record_id', 'occurrence_evidence_type')


def ld50_support(observations):
    exact = [r for r in observations if r['status'] == 'exact']
    values = {float(r['value_mg_kg']) for r in exact}
    if not values or any(not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError('Expected finite positive exact LD50 evidence')
    bins = sorted({ld50_bin(math.log10(v)) for v in values})
    return {'exact_point_records': len(exact), 'distinct_exact_values': len(values),
            'distinct_exact_reference_strings': len({r['reference'] for r in exact if r['reference']}),
            'censored_records': sum(r['status'] == 'censored' for r in observations),
            'min_exact_mg_kg': min(values), 'max_exact_mg_kg': max(values),
            'exact_report_bins': ';'.join(BINS[i] for i in bins)}


def summarize_catalog(measured, observations, review):
    evidence = ld50_support(observations)
    row = {field: measured[field] for field in (
        'full_key', 'coconut_exact', 'npass_exact', 'npass_taxon_reference_lead', 'hrac_name_lead',
    )}
    row.update(evidence)
    row['low_bin_report_agreement'] = ('all_exact_reports_low'
                                       if evidence['exact_report_bins'] == 'low'
                                       else 'exact_reports_cross_low_boundary')
    row['origin_review'] = review['origin_review'] if review else 'unreviewed'
    for field in ('reviewed_compound', 'reviewed_context', 'review_source'):
        row[field] = review[field] if review else ''
    row['screen_disposition'] = 'exclude_from_low_acute_lethality_shortlist'
    return row


def write_rows(path, records, fields):
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def comparison_rows(leads, triplets):
    by_key = defaultdict(list)
    for record in triplets:
        by_key[record['structure_inchikey']].append(record)
    for lead in leads:
        key = lead['full_key']
        found = by_key[key]
        yield {
            'full_key': key,
            'npass_taxon_reference_lead': lead['npass_taxon_reference_lead'] == 'True',
            'lotus_links': len(found),
            'lotus_rows_with_doi': sum(bool(r['reference_doi'].strip()) for r in found),
            'lotus_manual_validation_rows': sum(r['manual_validation'] == 'Y' for r in found),
        }


def compare_lotus(lotus, leads, output):
    triplets, fields, summary = lotus_overlay(lotus, {row['full_key'] for row in leads})
    rows = list(comparison_rows(leads, triplets))
    write_rows(output / 'lotus_source_links.csv', triplets, fields)
    write_rows(output / 'lotus_npass_coverage.csv', rows, rows[0])
    categories = {(True, True): 'both', (True, False): 'npass_only',
                  (False, True): 'lotus_only', (False, False): 'neither'}
    groups = Counter(categories[row['npass_taxon_reference_lead'], row['lotus_rows_with_doi'] > 0]
                     for row in rows)
    return {**summary, 'provider_record': 'https://zenodo.org/records/19360665',
            'provider_version': 'v11', 'doi_linkage_comparison': dict(groups),
            'matched_manual_validation_rows': sum(r['lotus_manual_validation_rows'] for r in rows)}


def run(root, integrated, review, output, lotus=None):
    root, integrated, review, output = map(Path, (root, integrated, review, output))
    cohort, occurrence = root / 'public-cohorts', root / 'npass-context-v2'
    for bundle in (cohort, occurrence, integrated):
        verify_bundle(bundle)
    measured_path = integrated / 'measured_context.csv'
    observations_path = cohort / 'A_observations.csv'
    occurrences_path = occurrence / 'npass_occurrences.csv.gz'
    selection = {
        row['full_key']: row for row in read_csv(measured_path)
        if row['ld50_bin'] == '0' and 'True' in (row['coconut_exact'], row['npass_exact'])
    }
    if not selection:
        raise ValueError('Integrated bundle contains no low-bin catalog structures')
    reviews = {}
    for row in read_csv(review):
        key = row['full_key']
        if key not in selection or key in reviews or row['origin_review'] not in REVIEW_STATUSES:
            raise ValueError(f'Unexpected or duplicate reviewed structure: {key}')
        if not all(row[field] for field in ('reviewed_compound', 'reviewed_context', 'review_source')):
            raise ValueError(f'Incomplete primary or regulatory review for {key}')
        reviews[key] = row
    by_key = defaultdict(list)
    measurement_fields = ('full_key', 'source_record_id', 'source_locator', 'dtxsid',
                          'value_mg_kg', 'qualifier', 'status', 'sex', 'reference')
    for row in read_csv(observations_path):
        if row['full_key'] in selection and row['status'] in {'exact', 'censored'}:
            by_key[row['full_key']].append({field: row[field] for field in measurement_fields})
    leads = [summarize_catalog(row, by_key[key], reviews.get(key))
             for key, row in sorted(selection.items())]
    output.mkdir(parents=True, exist_ok=False)
    write_rows(output / 'catalog_low_structures.csv', leads, leads[0])
    write_rows(output / 'ice_support.csv',
               (row for key in sorted(by_key) for row in by_key[key]), measurement_fields)

    with gzip.open(occurrences_path, 'rt', encoding='utf-8', newline='') as stream:
        linked = [
            {'full_key': r['full_inchikey'], **{field: r[field] for field in OCCURRENCE_FIELDS}}
            for r in csv.DictReader(stream) if r['full_inchikey'] in selection
        ]
    write_rows(output / 'npass_source_links.csv', linked, ('full_key', *OCCURRENCE_FIELDS))
    lotus_summary = compare_lotus(lotus, leads, output) if lotus is not None else None
    manifest = {
        'inputs': {str(path): sha256(path) for path in (
            measured_path, observations_path, occurrences_path, review,
            *(bundle / 'manifest.json' for bundle in (cohort, occurrence, integrated)),
        )},
        'products': {path.name: sha256(path) for path in output.iterdir()},
        'structures': len(leads),
        'ice_observation_rows': sum(map(len, by_key.values())),
        'npass_source_links': len(linked),
        'npass_taxon_publication_structure_leads': sum(
            row['npass_taxon_reference_lead'] == 'True' for row in leads),
        'dose_agreement': dict(Counter(r['low_bin_report_agreement'] for r in leads)),
        'origin_review': dict(Counter(r['origin_review'] for r in leads)),
    }
    if lotus_summary is not None:
        manifest['inputs'][str(lotus)] = sha256(lotus)
        manifest['lotus'] = lotus_summary
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'integrated', 'review', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--lotus', type=Path)
    print(json.dumps(run(**vars(parser.parse_args())), indent=2))
