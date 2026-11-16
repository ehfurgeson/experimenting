"""Bounded ECOTOX import with separate source results, slots and identity decisions."""
import argparse
import json
import math
import os
import re
import tempfile
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

import polars as pl
import yaml

from .ecotox_inventory import REQUIRED, digest, keyed, members, rows
from .units import duration_hours, normalize_unit

SENTINELS = {'', '--', '-', 'NC', 'NR', 'NA', 'UKN'}
DICTIONARIES = ('endpoint', 'effect', 'measurement', 'duration_unit', 'media_type',
                'concentration_unit', 'concentration_type', 'chemical_formulation',
                'chemical_grade', 'chemical_analysis', 'exposure_type', 'test_type')
NATIVE_SCHEMA = dict.fromkeys(('snapshot_id', 'source_result_id', 'source_chemical_id', 'result_id',
                              'test_id', 'reference_number', 'species_number', 'result_member',
                              'test_member', 'result_json', 'test_json', 'reference_json',
                              'species_json', 'chemical_json'), pl.String)
NATIVE_SCHEMA.update(result_record = pl.Int64, test_record = pl.Int64)
MEASUREMENT_SCHEMA = dict.fromkeys((
    'measurement_id', 'source_result_id', 'source_chemical_id', 'compound_id', 'identity_status',
    'endpoint', 'endpoint_description', 'effect_code', 'effect_description', 'measurement_code',
    'measurement_description', 'species', 'medium', 'medium_description', 'exposure_type',
    'exposure_description', 'test_type', 'formulation_code', 'formulation_description',
    'concentration_type', 'concentration_description', 'chemical_analysis', 'analysis_description',
    'qualifier', 'unit_raw', 'unit_standardized', 'parse_status', 'review_reasons'), pl.String)
MEASUREMENT_SCHEMA.update(slot = pl.Int64, value = pl.Float64, lower = pl.Float64, upper = pl.Float64,
                          duration_hours = pl.Float64, exposure_hours = pl.Float64)
DECISION_FIELDS = {'source_chemical_id', 'compound_id', 'status', 'match_type',
                   'source_identity_reference', 'reviewer', 'review_date'}


def number(value):
    if not isinstance(value, str) or not re.fullmatch(r'\+?\d*\.?\d+(?:[Ee][+-]?\d+)?', value.strip()):
        return None
    result = float(value)
    return result if math.isfinite(result) and result > 0 else None


def known(value):
    return (value or '').strip() not in SENTINELS


def identities(decisions, selected):
    found, attached = {}, {}
    for row in decisions:
        source = row.get('source_chemical_id')
        if source not in selected or source in found:
            raise ValueError('Identity decisions require unique selected source IDs')
        status = row.get('status')
        if status not in {'candidate', 'unknown', 'approved', 'rejected', 'conflict'}:
            raise ValueError('Unknown identity decision status')
        found[source] = row
        if status == 'approved':
            if row.get('match_type') != 'exact_structure' or any(not row.get(k, '').strip()
                    for k in DECISION_FIELDS - {'source_chemical_id', 'status', 'match_type'}):
                raise ValueError('Approved identity requires exact structure and signed source evidence')
            attached[source] = row['compound_id']
    return found, attached


def policies_from(path):
    data = yaml.safe_load(Path(path).read_text())
    required = {'endpoint', 'species', 'effect_code', 'measurement_code', 'duration_hours', 'medium',
                'standard_unit', 'concentration_types', 'formulations', 'analysis_codes'}
    if not isinstance(data, dict) or not data:
        raise ValueError('Policies must be a nonempty mapping')
    for name, rule in data.items():
        if not isinstance(name, str) or not isinstance(rule, dict) or set(rule) != required:
            raise ValueError('Each policy requires the exact explicit context fields')
        if rule['endpoint'] not in {'LD50', 'LC50', 'EC50'}:
            raise ValueError('Unsupported policy endpoint')
        for field in ('species', 'medium', 'concentration_types', 'formulations', 'analysis_codes'):
            if not isinstance(rule[field], list) or not rule[field] or any(
                    not isinstance(v, str) or not v.strip() for v in rule[field]):
                raise ValueError('Policy context lists must contain nonempty strings')
        if (type(rule['duration_hours']) not in (float, int) or
                not math.isfinite(rule['duration_hours']) or rule['duration_hours'] <= 0):
            raise ValueError('Explicit positive duration required')
        expected = 'mg/kg' if rule['endpoint'] == 'LD50' else 'mg/L'
        if rule['standard_unit'] != expected or any(not isinstance(rule[k], str) or not rule[k]
                for k in ('effect_code', 'measurement_code')):
            raise ValueError('Invalid endpoint unit or effect/measurement context')
    return data


def normalize(native, dictionaries, compound_id = None, identity_status = 'unknown'):
    result, test, species = [json.loads(native[k]) for k in ('result_json', 'test_json', 'species_json')]
    common, reasons = {}, []
    fields = {'endpoint': ('endpoint', result.get('endpoint')),
              'effect': ('effect', result.get('effect')), 'measurement': ('measurement', result.get('measurement')),
              'medium': ('media_type', test.get('media_type')),
              'exposure': ('exposure_type', test.get('exposure_type')),
              'formulation': ('chemical_formulation', test.get('test_formulation')),
              'analysis': ('chemical_analysis', result.get('chem_analysis_method')),
              'test_type': ('test_type', test.get('test_type'))}
    for target, (dictionary, code) in fields.items():
        code = (code or '').strip()
        common[target] = code
        common[target + '_description'] = dictionaries[dictionary].get(code)
        if known(code) and code not in dictionaries[dictionary]:
            reasons.append('unknown_' + dictionary + '_code')
    endpoint = common['endpoint']
    if endpoint not in {'LD50', 'LC50', 'EC50'}:
        reasons.append('unsupported_endpoint')

    def hours(prefix, data):
        raw = data.get(prefix + '_mean', '')
        unit = data.get(prefix + '_unit', '')
        operator = data.get(prefix + '_mean_op', '')
        value = number(raw)
        if unit not in dictionaries['duration_unit'] or operator not in {'', '='} or value is None:
            return None
        # hph, dph and other event-relative times must never become elapsed duration.
        return duration_hours(value, unit) if unit in {'h', 'd', 'wk'} else None

    output = []
    slots = [i for i in (1, 2, 3) if any(known(result.get(f'conc{i}_{part}'))
             for part in ('mean', 'min', 'max', 'unit', 'type'))] or [1]
    for slot in slots:
        prefix = f'conc{slot}_'
        notes = reasons.copy()
        raw_unit, concentration = result.get(prefix + 'unit', ''), result.get(prefix + 'type', '')
        description = dictionaries['concentration_type'].get(concentration)
        if known(concentration) and description is None:
            notes.append('unknown_concentration_type_code')
        if known(raw_unit) and raw_unit not in dictionaries['concentration_unit']:
            notes.append('unknown_concentration_unit_code')
        medium = 'water' if common['medium'] in {'FW', 'SW', 'AQU'} else None
        unit, factor = normalize_unit(raw_unit, endpoint, medium)
        if factor is None:
            notes.append('incompatible_or_unsupported_unit')
        value = number(result.get(prefix + 'mean'))
        lower, upper, qualifier = None, None, result.get(prefix + 'mean_op', '') or '='
        if value is None:
            lower, upper = number(result.get(prefix + 'min')), number(result.get(prefix + 'max'))
            if lower is not None and upper is not None and lower <= upper and all(
                    result.get(prefix + field, '') in {'', '='} for field in ('min_op', 'max_op')):
                qualifier = 'range'
            else:
                lower, upper = None, None
                notes.append('missing_or_unsupported_numeric_value')
        elif qualifier not in {'=', '<', '<=', '>', '>='}:
            notes.append('unsupported_qualifier')
        if factor is not None:
            value, lower, upper = [n * factor if n is not None else None for n in (value, lower, upper)]
            if any(n is not None and not math.isfinite(n) for n in (value, lower, upper)):
                value, lower, upper = None, None, None
                notes.append('nonfinite_converted_value')
        else:
            value, lower, upper = None, None, None
        output.append({
            'measurement_id': f"{native['source_result_id']}:conc{slot}",
            'source_result_id': native['source_result_id'], 'source_chemical_id': native['source_chemical_id'],
            'compound_id': compound_id, 'identity_status': identity_status, 'slot': slot,
            'endpoint': endpoint, 'endpoint_description': common['endpoint_description'],
            'effect_code': common['effect'], 'effect_description': common['effect_description'],
            'measurement_code': common['measurement'], 'measurement_description': common['measurement_description'],
            'species': species.get('latin_name', '').strip().casefold(),
            'medium': common['medium'], 'medium_description': common['medium_description'],
            'exposure_type': common['exposure'], 'exposure_description': common['exposure_description'],
            'test_type': common['test_type'], 'formulation_code': common['formulation'],
            'formulation_description': common['formulation_description'],
            'concentration_type': concentration, 'concentration_description': description,
            'chemical_analysis': common['analysis'], 'analysis_description': common['analysis_description'],
            'duration_hours': hours('obs_duration', result), 'exposure_hours': hours('exposure_duration', test),
            'qualifier': qualifier, 'unit_raw': raw_unit, 'unit_standardized': unit,
            'value': value, 'lower': lower, 'upper': upper,
            'parse_status': 'complete' if not notes else 'review', 'review_reasons': ';'.join(sorted(set(notes)))})
    return output


def policy_reasons(row, rule):
    checks = {'endpoint': row['endpoint'] == rule['endpoint'],
              'species': row['species'] in rule['species'], 'effect': row['effect_code'] == rule['effect_code'],
              'measurement': row['measurement_code'] == rule['measurement_code'],
              'duration': row['duration_hours'] == rule['duration_hours'],
              'medium': row['medium'] in rule['medium'], 'unit': row['unit_standardized'] == rule['standard_unit'],
              'concentration_basis': row['concentration_type'] in rule['concentration_types'],
              'formulation': row['formulation_code'] in rule['formulations'],
              'exposure_analysis': row['chemical_analysis'] in rule['analysis_codes'],
              'parsed_measurement': row['parse_status'] == 'complete'}
    return [key for key, value in checks.items() if not value]


def import_selected(source, selected, decisions, policies):
    """One native row per result; one measurement per occupied concentration slot."""
    selected = list(selected)
    if not selected or len(selected) != len(set(selected)) or any(
            not re.fullmatch(r'ECOTOX:chemical:[^:]+', s) for s in selected):
        raise ValueError('Require unique namespaced source chemical IDs')
    decision_rows, attached = identities(decisions, set(selected))
    snapshot = digest(source)
    with ZipFile(source) as archive:
        mapping = members(archive)
        root = mapping['tests.txt'].rsplit('/', 1)[0]
        chemicals = keyed(archive, mapping['validation/chemicals.txt'], REQUIRED['validation/chemicals.txt'], 'cas_number')
        requested = {s.split(':')[-1] for s in selected}
        if not requested <= set(chemicals):
            raise ValueError('Requested chemical is absent from source snapshot')
        dictionaries = {}
        for name in DICTIONARIES:
            entry = f'{root}/validation/{name}_codes.txt'
            dictionaries[name] = {r['code'].strip(): r['description'] for _, r in rows(
                archive, entry, {'code', 'description'})}
        references = keyed(archive, mapping['validation/references.txt'], REQUIRED['validation/references.txt'], 'reference_number')
        species = keyed(archive, mapping['validation/species.txt'], REQUIRED['validation/species.txt'], 'species_number')
        tests, all_tests = {}, set()
        for line, test in rows(archive, mapping['tests.txt'], REQUIRED['tests.txt']):
            key = test['test_id']
            if not key or key in all_tests:
                raise ValueError('Missing or duplicate source test key')
            all_tests.add(key)
            if test['test_cas'] in requested:
                if test['reference_number'] not in references or test['species_number'] not in species:
                    raise ValueError('Dangling selected test relationship')
                tests[key] = (line, test)
        native, measurements, all_results = [], [], set()
        for line, result in rows(archive, mapping['results.txt'], REQUIRED['results.txt']):
            key = result['result_id']
            if not key or key in all_results:
                raise ValueError('Missing or duplicate source result key')
            all_results.add(key)
            if result['test_id'] not in all_tests:
                raise ValueError('Dangling result/test relationship')
            if result['test_id'] not in tests:
                continue
            test_line, test = tests[result['test_id']]
            source_id = 'ECOTOX:chemical:' + test['test_cas']
            row = {'snapshot_id': snapshot, 'source_result_id': f'ECOTOX:{snapshot}:result:{key}',
                   'source_chemical_id': source_id, 'result_id': key, 'test_id': test['test_id'],
                   'reference_number': test['reference_number'], 'species_number': test['species_number'],
                   'result_member': mapping['results.txt'], 'test_member': mapping['tests.txt'],
                   'result_record': line, 'test_record': test_line,
                   **{name + '_json': json.dumps(value, sort_keys = True) for name, value in {
                       'result': result, 'test': test, 'chemical': chemicals[test['test_cas']],
                       'reference': references[test['reference_number']], 'species': species[test['species_number']]}.items()}}
            native.append(row)
            measurements.extend(normalize(row, dictionaries, attached.get(source_id),
                                           decision_rows.get(source_id, {}).get('status', 'unknown')))
    counts = Counter(r['source_chemical_id'] for r in native)
    coverage, admission = [], []
    for source_id in selected:
        for policy, rule in policies.items():
            compatible = []
            for row in measurements:
                if row['source_chemical_id'] != source_id:
                    continue
                excluded = policy_reasons(row, rule)
                if not excluded:
                    compatible.append(row)
                # Emit only target endpoint/species candidates, plus coverage for all selected IDs.
                if row['endpoint'] == rule['endpoint'] and row['species'] in rule['species']:
                    admission.append({'measurement_id': row['measurement_id'], 'policy': policy,
                                      'source_chemical_id': source_id, 'compound_id': row['compound_id'],
                                      'source_context_eligible': not excluded,
                                      'canonical_comparison_eligible': not excluded and row['compound_id'] is not None,
                                      'reasons': ';'.join(excluded + ([] if row['compound_id'] else ['identity_not_approved']))})
            coverage.append({'source_chemical_id': source_id, 'policy': policy,
                             'source_results': counts[source_id], 'eligible_slots': len(compatible),
                             'eligible_results': len({r['source_result_id'] for r in compatible}),
                             'identity_status': decision_rows.get(source_id, {}).get('status', 'unknown'),
                             'compound_id': attached.get(source_id),
                             'canonical_coverage': int(bool(compatible)) if source_id in attached else None})
    return native, measurements, coverage, admission, dictionaries, len(tests)


def run(source, chemical_ids, crosswalk, policies, output):
    paths = [Path(p).resolve() for p in (source, chemical_ids, crosswalk, policies)]
    output = Path(output).resolve()
    if output.exists() or any(p.is_relative_to(output) or output.is_relative_to(p) for p in paths):
        raise ValueError('Use a new output directory separate from inputs')
    initial_hashes = {str(p): digest(p) for p in paths}
    selected = pl.read_csv(paths[1], infer_schema = False)['source_chemical_id'].to_list()
    decisions = pl.read_csv(paths[2], infer_schema = False).fill_null('').to_dicts()
    rules = policies_from(paths[3])
    native, measurements, coverage, admission, dictionaries, tests = import_selected(paths[0], selected, decisions, rules)
    if {str(p): digest(p) for p in paths} != initial_hashes:
        raise ValueError('Source inputs changed during import')
    output.parent.mkdir(parents = True, exist_ok = True)
    with tempfile.TemporaryDirectory(prefix = '.ecotox-stage-', dir = output.parent) as staging:
        stage = Path(staging)
        products = {'native_observations': pl.DataFrame(native, schema = NATIVE_SCHEMA),
                    'measurements': pl.DataFrame(measurements, schema = MEASUREMENT_SCHEMA),
                    'coverage': pl.DataFrame(coverage, schema = {
                        'source_chemical_id': pl.String, 'policy': pl.String, 'source_results': pl.Int64,
                        'eligible_slots': pl.Int64, 'eligible_results': pl.Int64, 'identity_status': pl.String,
                        'compound_id': pl.String, 'canonical_coverage': pl.Int64}),
                    'admission': pl.DataFrame(admission, schema = {
                        'measurement_id': pl.String, 'policy': pl.String, 'source_chemical_id': pl.String,
                        'compound_id': pl.String, 'source_context_eligible': pl.Boolean,
                        'canonical_comparison_eligible': pl.Boolean, 'reasons': pl.String})}
        for name, frame in products.items():
            frame.write_parquet(stage / (name + '.parquet'))
            frame.write_csv(stage / (name + '.csv'))
        (stage / 'dictionaries.json').write_text(json.dumps(dictionaries, indent = 2) + '\n')
        manifest = {'input_hashes': initial_hashes,
                    'code_hashes': {str(p): digest(p) for p in Path(__file__).parent.glob('*.py')},
                    'lock_hashes': {str(p): digest(p) for p in (Path(__file__).parents[2] / 'uv.lock',)},
                    'output_hashes': {str(output / p.name): digest(p) for p in stage.iterdir()},
                    'counts': {name: frame.height for name, frame in products.items()},
                    'selected_chemicals': len(selected), 'selected_tests': tests,
                    'parse_status': dict(Counter(r['parse_status'] for r in measurements)),
                    'approved_source_identities': sum(r['status'] == 'approved' for r in decisions),
                    'scope': 'Complete selected-cohort results; slot records are not independent studies. '
                             'Identity candidates and experimental effect estimates are not approved biological labels.'}
        (stage / 'manifest.json').write_text(json.dumps(manifest, indent = 2) + '\n')
        os.rename(stage, output)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for key in ('source', 'chemical-ids', 'crosswalk', 'policies', 'output'):
        parser.add_argument('--' + key, type = Path, required = True)
    args = parser.parse_args()
    manifest = run(args.source, args.chemical_ids, args.crosswalk, args.policies, args.output)
    print(json.dumps({k: manifest[k] for k in ('counts', 'selected_chemicals', 'selected_tests', 'parse_status')}, indent = 2))
