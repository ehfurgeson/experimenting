"""Inventory accepted plant policies and unadopted non-algal ECOTOX growth leads."""

import argparse
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile

from agrotox.ecotox_inventory import keyed, members, rows

from data_sprint import read_csv, sha256, write_csv


def plant_candidate(species, result):
    """A bounded discovery filter; non-algal does not necessarily mean terrestrial."""
    return (species['kingdom'] == 'Plantae' and
            'Algae' not in species['ecotox_group'] and
            (result['effect'].lstrip('~') == 'GRO' or
             result['measurement'].lstrip('~') in {'GERM', 'GMEN', 'BMAS', 'DBMS'}))


def accepted_inventory(adoption):
    policies = json.loads((adoption / 'policies.json').read_text())
    features = read_csv(adoption / 'accepted_activity_features.csv')
    reports = []
    for policy, definition in policies.items():
        unique = {r['structure_inchikey']: r for r in features
                  if r['policy'] == policy and r['structure_status'] == 'valid' and
                  r['activity_target'] in {'0', '1', '0.0', '1.0'}}
        high = [r for r in unique.values() if float(r['activity_target']) == 1]
        low = [r for r in unique.values() if float(r['activity_target']) == 0]
        reports.append({'source_assay_id': policy, 'source': 'human_adopted_bundle',
                        'review_status': definition['status'], 'context': definition['context'],
                        'high_structures': len(high), 'low_structures': len(low),
                        'high_scaffolds': len({r['scaffold'] for r in high}),
                        'low_scaffolds': len({r['scaffold'] for r in low}),
                        'activity_reference': '; '.join(sorted({r['activity_reference']
                                                               for r in unique.values()})),
                        'hold_reason': 'No pooling; run activity_preflight for actual fold support'})
    return reports


def run(adoption, source, output):
    source, output = Path(source), Path(output)
    inputs = [source]
    if adoption is not None:
        adoption = Path(adoption)
        inputs.extend(adoption / name for name in (
            'policies.json', 'accepted_activity_features.csv', 'identity_holds.csv',
            'activity_observations.csv'))
    before = {str(p): sha256(p) for p in inputs}
    output.mkdir(parents = True, exist_ok = False)
    if adoption is not None:
        accepted = accepted_inventory(adoption)
        write_csv(output / 'accepted_policy_inventory.csv', accepted, list(accepted[0]))
        observations = read_csv(adoption / 'activity_observations.csv')
        write_csv(output / 'accepted_source_observations.csv', observations, list(observations[0]))
    with ZipFile(source) as archive:
        mapping = members(archive)
        species = keyed(archive, mapping['validation/species.txt'], {'species_number', 'kingdom'},
                        'species_number')
        references = keyed(archive, mapping['validation/references.txt'], {'reference_number'},
                           'reference_number')
        chemicals = keyed(archive, mapping['validation/chemicals.txt'], {'cas_number'}, 'cas_number')
        tests = {}
        for line, test in rows(archive, mapping['tests.txt'], {'test_id', 'species_number'}):
            organism = species[test['species_number']]
            if organism['kingdom'] == 'Plantae' and 'Algae' not in organism['ecotox_group']:
                if test['test_id'] in tests:
                    raise ValueError('Duplicate ECOTOX plant test ID')
                tests[test['test_id']] = (line, test)
        groups = defaultdict(list)
        fields = ['source', 'source_assay_id', 'source_record_id', 'doi', 'plant_species',
                  'plant_taxon_id', 'source_chemical_id', 'chemical_name', 'dtxsid',
                  'full_inchikey', 'identity_status', 'endpoint', 'measurement', 'response_site',
                  'observed_response', 'qualifier', 'effect_direction', 'concentration',
                  'concentration_unit', 'duration', 'duration_unit', 'exposure_duration',
                  'exposure_duration_unit', 'control_context', 'organism_habitat', 'media_type',
                  'review_status', 'activity_label', 'source_locator', 'source_record_json']
        seen, counts = set(), Counter()
        with gzip.open(output / 'plant_activity_observations.csv.gz', 'wt', newline = '') as stream:
            import csv
            writer = csv.DictWriter(stream, fieldnames = fields)
            writer.writeheader()
            for line, result in rows(archive, mapping['results.txt'], {'result_id', 'test_id'}):
                if result['test_id'] not in tests:
                    continue
                test_line, test = tests[result['test_id']]
                organism = species[test['species_number']]
                if not plant_candidate(organism, result):
                    continue
                if result['result_id'] in seen:
                    raise ValueError('Duplicate ECOTOX plant result ID')
                seen.add(result['result_id'])
                reference = references[test['reference_number']]
                chemical = chemicals[test['test_cas']]
                row = dict(zip(fields, [''] * len(fields), strict = True))
                row.update(source = 'ECOTOX_2026-09-15', source_assay_id = test['test_id'],
                           source_record_id = result['result_id'], doi = reference['doi'],
                           plant_species = organism['latin_name'],
                           plant_taxon_id = organism['ncbi_taxid'],
                           source_chemical_id = test['test_cas'],
                           chemical_name = chemical['chemical_name'], dtxsid = chemical['dtxsid'],
                           identity_status = 'source_identifier_only_not_structure_resolved',
                           endpoint = result['endpoint'], measurement = result['measurement'],
                           response_site = result['response_site'],
                           observed_response = result['effect_pct_mean'],
                           qualifier = result['effect_pct_mean_op'], effect_direction = result['trend'],
                           concentration = result['conc1_mean'],
                           concentration_unit = result['conc1_unit'],
                           duration = result['obs_duration_mean'],
                           duration_unit = result['obs_duration_unit'],
                           exposure_duration = test['exposure_duration_mean'],
                           exposure_duration_unit = test['exposure_duration_unit'],
                           control_context = test['control_type'],
                           organism_habitat = test['organism_habitat'], media_type = test['media_type'],
                           review_status = 'review_only', activity_label = 'unknown',
                           source_locator = f"results.txt:{line};tests.txt:{test_line}",
                           source_record_json = json.dumps({'result': result, 'test': test,
                                                            'species': organism,
                                                            'reference': reference}, sort_keys = True))
                writer.writerow(row)
                # Context key is a discovery stratum, not an assertion of comparability.
                group = (test['reference_number'], organism['latin_name'], result['endpoint'],
                         result['measurement'], result['conc1_unit'], result['obs_duration_mean'],
                         result['obs_duration_unit'], test['media_type'])
                groups[group].append((test['test_cas'], test['test_id'], result['effect_pct_mean']))
                counts[result['endpoint']] += 1
    registry = []
    for group, values in sorted(groups.items()):
        registry.append(dict(zip(['reference_number', 'plant_species', 'endpoint', 'measurement',
                                  'concentration_unit', 'duration', 'duration_unit', 'media_type'],
                                 group, strict = True)) | {
            'observations': len(values), 'source_chemicals': len({v[0] for v in values}),
            'source_tests': len({v[1] for v in values}),
            'review_status': 'review_only_context_not_harmonized',
            'high_labels': 0, 'low_labels': 0})
    fields = ['reference_number', 'plant_species', 'endpoint', 'measurement', 'concentration_unit',
              'duration', 'duration_unit', 'media_type', 'observations', 'source_chemicals',
              'source_tests', 'review_status', 'high_labels', 'low_labels']
    write_csv(output / 'plant_assay_registry.csv', registry, fields)
    summary = {'inputs': before, 'nonalgal_plant_tests': len(tests),
               'includes_adopted_inputs': adoption is not None,
               'growth_germination_biomass_results': len(seen), 'discovery_strata': len(groups),
               'endpoints': dict(counts), 'new_adopted_labels': 0, 'models_fitted': 0,
               'limits': 'Non-algal includes aquatic vascular plants. No effect/NOEC is not '
                         'an adopted low-response label. Source structures and primary study '
                         'methods require review; no universal plant classifier.'}
    if before != {str(p): sha256(p) for p in inputs}:
        raise ValueError('Inputs changed during inventory')
    summary['products'] = {p.name: sha256(p) for p in output.iterdir()}
    (output / 'manifest.json').write_text(json.dumps(summary, indent = 2) + '\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--adoption', type = Path,
                        help = 'Optional reviewed activity bundle to inventory alongside ECOTOX')
    parser.add_argument('--ecotox', type = Path, required = True)
    parser.add_argument('--output', type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(run(args.adoption, args.ecotox, args.output), indent = 2))
