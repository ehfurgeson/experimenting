"""Bounded ToxValDB workbook screen; endpoint eligibility is separate from admission."""

import argparse
import csv
import gzip
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from data_sprint import sha256, write_csv
from evidence_release import workbook_rows
from sprint_natural import baseline_members, finish, source_file


def csv_rows(path):
    with Path(path).open(newline = '') as stream:
        yield from csv.DictReader(stream)


def identifier_crosswalk(release):
    """Retain ambiguous DTXSID mappings; never pick the first structure or strip salts."""
    mappings = defaultdict(set)
    ice_identity = {r['native_id']: r for r in csv_rows(release / 'chemical_identity.csv')
                    if r['source_cohort'] == 'ICE' and r['identity_status'] == 'valid'}
    for row in csv_rows(release / 'A_observations.csv'):
        identity = ice_identity.get(row['source_record_id'])
        if identity and row['dtxsid']:
            mappings[row['dtxsid']].add(identity['full_key'])
    for row in csv_rows(release / 'B_predictions.csv'):
        if row['status'] == 'eligible' and row['dtxsid'] and row['full_key']:
            mappings[row['dtxsid']].add(row['full_key'])
    return mappings


def populated(value):
    return bool(value and value.strip() not in {'-', '-999', 'n.a.', 'not specified'})


def screen_row(raw, references, mappings, a_keys, source_id, ordinal):
    reasons = []
    try:
        value = float(raw['TOXVAL_NUMERIC'])
        valid_value = math.isfinite(value) and value > 0
    except (ValueError, TypeError):
        valid_value = False
    citation = '; '.join(sorted({r.get('DOI', '') for r in references
                                if populated(r.get('DOI'))} |
                               {r.get('LONG_REF', '') for r in references
                                if populated(r.get('LONG_REF'))}))
    source_url = raw['SUBSOURCE_URL'] if populated(raw['SUBSOURCE_URL']) else ''
    for okay, reason in [
        (raw['EXPERIMENTAL_RECORD'] == 'experimental', 'not_explicit_experimental'),
        (raw['SPECIES_COMMON'] == 'Rat', 'not_rat'),
        (raw['EXPOSURE_ROUTE'] == 'oral', 'not_oral'),
        (raw['STUDY_TYPE'] == 'acute', 'not_acute'),
        (raw['TOXVAL_TYPE'] == 'LD50', 'not_ld50'),
        (raw['TOXVAL_UNITS'] == 'mg/kg', 'not_mg_kg'),
        (valid_value, 'nonpositive_or_nonfinite_value'),
        (raw['QUALIFIER'] in {'=', '<', '>', '<=', '>='}, 'unsupported_qualifier'),
        (bool(citation or source_url), 'no_record_level_reference'),
        (raw['QC_STATUS'] != 'fail', 'source_qc_fail'),
    ]:
        if not okay:
            reasons.append(reason)
    keys = mappings.get(raw['DTXSID'], set())
    key = next(iter(keys)) if len(keys) == 1 else ''
    status = 'excluded' if reasons else 'endpoint_eligible_exact' if raw['QUALIFIER'] == '=' else (
        'endpoint_eligible_censored')
    holds = ['source_study_independence_unresolved', 'tested_material_form_not_verified']
    if len(keys) != 1:
        holds.append('ambiguous_dtxsid_structure' if keys else 'unresolved_dtxsid_structure')
    if not citation:
        holds.append('dossier_reference_only')
    return {'source': 'ToxValDB_v9.7.0', 'source_table': source_id,
            'source_record_id': raw['SOURCE_HASH'], 'source_locator': f'{source_id}:toxval!row{ordinal}',
            'original_compound_id': raw['DTXSID'], 'source_chemical_name': raw['NAME'],
            'full_inchikey': key, 'candidate_full_inchikeys': ';'.join(sorted(keys)),
            'identity_status': 'unambiguous_local_dtxsid_link' if key else 'review_required',
            'test_species': raw['SPECIES_COMMON'], 'test_route': raw['EXPOSURE_ROUTE'],
            'exposure_duration': raw['STUDY_DURATION_VALUE'],
            'exposure_duration_unit': raw['STUDY_DURATION_UNITS'],
            'endpoint': raw['TOXVAL_TYPE'], 'measurement_type': raw['EXPERIMENTAL_RECORD'],
            'value': raw['TOXVAL_NUMERIC'], 'unit': raw['TOXVAL_UNITS'],
            'qualifier': raw['QUALIFIER'], 'tested_form': raw['EXPOSURE_FORM'],
            'source_study_id': raw['STUDY_GROUP'], 'citation': citation, 'source_url': source_url,
            'is_experimental': raw['EXPERIMENTAL_RECORD'], 'status': status,
            'exclusion_reason': ';'.join(reasons), 'admission_holds': ';'.join(holds),
            'is_existing_a_structure': key in a_keys if key else 'unknown',
            'duplicate_group': 'unresolved',
            'source_record_json': json.dumps({'toxval': raw, 'record_source': references},
                                             sort_keys = True)}


def reference_token(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())


DEFAULT_SOURCES = ('toxval-test', 'toxval-chemid', 'toxval-echa')


def run(registry, release, baseline_path, output, *, source_ids=DEFAULT_SOURCES):
    release, output = Path(release), Path(output)
    if not source_ids or len(source_ids) != len(set(source_ids)):
        raise ValueError('Select at least one unique ToxValDB source')
    sources = {name: source_file(registry, name) for name in source_ids}
    inputs = [*sources.values(), Path(baseline_path), release / 'chemical_identity.csv',
              release / 'A_observations.csv', release / 'B_predictions.csv']
    before = {str(p): sha256(p) for p in inputs}
    baseline = baseline_members(baseline_path)
    a_keys = {r['full_inchikey'] for r in baseline if r['cohort'] == 'A'}
    mappings = identifier_crosswalk(release)
    a_refs, a_values = defaultdict(set), defaultdict(set)
    for row in csv_rows(release / 'A_observations.csv'):
        if row['status'] in {'exact', 'censored'}:
            a_refs[row['full_key']].add(reference_token(row['reference']))
            a_values[row['full_key']].add((float(row['value_mg_kg']), row['qualifier']))
    output.mkdir(parents = True, exist_ok = False)
    counts, exclusions, candidates, duplicates, all_fields = {}, Counter(), [], [], None
    with gzip.open(output / 'toxval_observations_all.csv.gz', 'wt', newline = '') as stream:
        writer = None
        for source_id, path in sources.items():
            references = defaultdict(list)
            for _, raw in workbook_rows(path, 'record_source'):
                references[raw['SOURCE_HASH']].append(raw)
            counter = Counter()
            for ordinal, raw in workbook_rows(path, 'toxval'):
                row = screen_row(raw, references.get(raw['SOURCE_HASH'], []), mappings,
                                 a_keys, source_id, ordinal)
                if writer is None:
                    all_fields = list(row)
                    writer = csv.DictWriter(stream, fieldnames = all_fields)
                    writer.writeheader()
                writer.writerow(row)
                counter['acquired_rows'] += 1
                counter[row['status']] += 1
                exclusions.update(row['exclusion_reason'].split(';') if row['exclusion_reason'] else [])
                if row['status'].startswith('endpoint_eligible'):
                    counter['unambiguous_structure_rows'] += bool(row['full_inchikey'])
                    candidates.append(row)
                    key = row['full_inchikey']
                    if key and key in a_keys:
                        reference_match = reference_token(row['citation']) in a_refs[key]
                        dose_match = (float(row['value']), row['qualifier']) in a_values[key]
                        duplicates.append({
                            'source_record_id': row['source_record_id'], 'full_inchikey': key,
                            'source_table': source_id, 'same_normalized_reference': reference_match,
                            'same_value_qualifier_in_a': dose_match,
                            'overlap_status': 'possible_mirror_review' if reference_match or dose_match
                                              else 'existing_structure_study_unresolved',
                            'citation': row['citation'], 'source_study_id': row['source_study_id']})
            counts[source_id] = dict(counter)
            print(source_id, counts[source_id], flush = True)
    with gzip.open(output / 'toxval_candidate_rat_oral.csv.gz', 'wt', newline = '') as stream:
        writer = csv.DictWriter(stream, fieldnames = all_fields)
        writer.writeheader()
        writer.writerows(candidates)
    write_csv(output / 'toxval_possible_duplicate_studies.csv', duplicates,
              ['source_record_id', 'full_inchikey', 'source_table', 'same_normalized_reference',
               'same_value_qualifier_in_a', 'overlap_status', 'citation', 'source_study_id'])
    exact = {r['full_inchikey'] for r in candidates
             if r['status'] == 'endpoint_eligible_exact' and r['full_inchikey']}
    censored = {r['full_inchikey'] for r in candidates
                if r['status'] == 'endpoint_eligible_censored' and r['full_inchikey']}
    summary = {'tables': counts, 'exclusion_reasons': dict(exclusions),
               'endpoint_eligible_mapped_exact_structures': len(exact),
               'endpoint_eligible_mapped_censored_structures': len(censored),
               'candidate_net_new_exact_full_structures': len(exact - a_keys),
               'candidate_net_new_censored_only_full_structures': len(censored - exact - a_keys),
               'net_new_eligible_full_structures': 0,
               'net_new_independent_studies': None,
               'possible_mirror_rows_against_a': sum(
                   r['overlap_status'] == 'possible_mirror_review' for r in duplicates),
               'limits': 'Endpoint-eligible candidates are not admitted labels. DTXSID links do '
                         'not verify tested material or source study independence. All candidates '
                         'retain form/lineage holds. ChemIDplus experimental status is undetermined; '
                         'TEST experimental rows are not assumed predictions or independent of ICE.'}
    return finish(output, inputs, before, summary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for name in ('registry', 'release', 'baseline', 'output'):
        parser.add_argument('--' + name, type = Path, required = True)
    parser.add_argument('--only', nargs='+', default=DEFAULT_SOURCES,
                        help='Registered source IDs to audit with the same endpoint policy')
    args = parser.parse_args()
    print(json.dumps(run(args.registry, args.release, args.baseline, args.output,
                         source_ids=args.only), indent = 2))
