"""Offline full-structure catalog overlays and conservative NPASS toxicity audit."""

import argparse
import csv
import gzip
import io
import json
import math
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile

from rdkit import Chem, RDLogger

from data_sprint import read_csv, sha256, write_csv

RDLogger.DisableLog('rdApp.warning')
RDLogger.DisableLog('rdApp.error')


def source_file(registry, source_id):
    registry = Path(registry)
    entries = [r for r in json.loads(registry.read_text()) if r['source_id'] == source_id]
    if len(entries) != 1 or entries[0]['status'] != 'downloaded':
        raise ValueError(f'One successfully downloaded source required: {source_id}')
    path = registry.parent / entries[0]['file']
    if sha256(path) != entries[0]['sha256']:
        raise ValueError(f'Source hash mismatch: {source_id}')
    return path


def tab_rows(path):
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding = 'utf-8-sig', newline = '') as stream:
        reader = csv.DictReader(stream, delimiter = '\t')
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError('Missing or duplicate source headers')
        for ordinal, row in enumerate(reader, 1):
            if all(value in ('', None) for value in row.values()):
                continue  # NPASS general export includes a delimiter-only separator record.
            if None in row or None in row.values():
                raise ValueError(f'Malformed source row {ordinal}')
            yield ordinal, row


def identity(smiles, provider_key):
    mol = Chem.MolFromSmiles(smiles or '')
    result = {'original_structure': smiles, 'provider_full_inchikey': provider_key,
              'full_inchikey': '', 'identity_status': 'invalid_or_missing_structure',
              'unspecified_atom_stereocenters': ''}
    if mol is None or not mol.GetNumAtoms():
        return result
    key = Chem.MolToInchiKey(mol)
    result.update(full_inchikey = key, unspecified_atom_stereocenters = sum(
        label == '?' for _, label in Chem.FindMolChiralCenters(mol, includeUnassigned = True)))
    result['identity_status'] = (
        'multiple_components' if len(Chem.GetMolFrags(mol)) != 1 else
        'missing_full_key' if not key else
        'missing_provider_key' if not provider_key else
        'provider_key_conflict' if key != provider_key else 'valid')
    return result


def baseline_members(path):
    path = Path(path)
    manifest = json.loads((path.parent / 'manifest.json').read_text())
    if sha256(path) != manifest['products'][path.name]:
        raise ValueError('Baseline membership hash mismatch')
    return read_csv(path)


def catalog_matches(identities, baseline, source):
    exact, connected = defaultdict(list), defaultdict(list)
    for row in identities:
        if row['identity_status'] == 'valid':
            exact[row['full_inchikey']].append(row['source_compound_id'])
            connected[row['full_inchikey'].split('-')[0]].append(row['source_compound_id'])
    result = []
    for row in baseline:
        key = row['full_inchikey']
        full = exact.get(key, []) if row['identity_status'] == 'valid' else []
        maybe = connected.get(key.split('-')[0], []) if key else []
        result.append({'source': source, 'cohort': row['cohort'], 'compound_id': row['compound_id'],
                       'full_inchikey': key, 'selection_group': row['selection_group'],
                       'match_tier': 'exact_full_key' if full else
                                     'connectivity_only_review' if maybe else 'unresolved',
                       'catalog_ids': ';'.join(sorted(full or maybe)),
                       'occurrence_evidence_type': 'catalog_membership_only',
                       'verified_taxon_reference_occurrence': 'unknown'})
    return result


def npass_toxicity(raw, compound, ordinal, a_keys):
    reasons = []
    try:
        value = float(raw['activity_value'])
        valid_value = math.isfinite(value) and value > 0
    except (ValueError, TypeError):
        valid_value = False
    for okay, reason in [
        (raw['activity_type'] == 'LD50', 'not_ld50'),
        (raw['assay_organism'].lower() in {'rattus norvegicus', 'rat'}, 'not_explicit_rat'),
        (raw['activity_units'] == 'mg/kg', 'not_mg_kg'),
        (valid_value, 'nonpositive_or_nonfinite_value'),
        (raw['activity_relation'] in {'=', '<', '>', '<=', '>='}, 'unknown_qualifier'),
        (bool(raw['ref_id']) and raw['ref_id'] not in {'n.a.', '-'}, 'missing_reference'),
        (compound.get('identity_status') == 'valid', 'unqualified_structure'),
    ]:
        if not okay:
            reasons.append(reason)
    # The actual NPASS 3.0 export has no route, acute-duration or experimental-status field.
    # Even mammalian LD50 rows cannot be admitted by assuming those missing contexts.
    reasons.extend(['route_not_reported', 'acute_context_not_reported',
                    'experimental_status_not_reported'])
    return {'source': 'NPASS_3.0', 'source_record_id': f'toxicity:record{ordinal}',
            'source_compound_id': raw['np_id'], 'full_inchikey': compound.get('full_inchikey', ''),
            'test_species': raw['assay_organism'], 'test_route': '', 'exposure_duration': '',
            'endpoint': raw['activity_type'], 'measurement_type': 'unknown',
            'value': raw['activity_value'], 'unit': raw['activity_units'],
            'qualifier': raw['activity_relation'], 'tested_form': '',
            'citation': raw['ref_id_type'] + ':' + raw['ref_id'], 'is_experimental': 'unknown',
            'status': 'review_only', 'exclusion_reason': ';'.join(reasons),
            'is_existing_a_structure': compound.get('full_inchikey') in a_keys,
            'duplicate_group': 'unresolved', 'source_record_json': json.dumps(raw, sort_keys = True)}


def run_npass(structure_registry, toxicity_registry, baseline_path, output):
    structures = source_file(structure_registry, 'npass-structure')
    toxicity = source_file(toxicity_registry, 'npass-toxicity')
    inputs = [structures, toxicity, Path(baseline_path)]
    before = {str(p): sha256(p) for p in inputs}
    baseline = baseline_members(baseline_path)
    a_keys = {r['full_inchikey'] for r in baseline if r['cohort'] == 'A'}
    output = Path(output)
    output.mkdir(parents = True, exist_ok = False)
    identities, originals, duplicates = {}, {}, []
    source_count = 0
    for ordinal, raw in tab_rows(structures):
        source_count += 1
        native = raw['np_id']
        if not native:
            raise ValueError('Missing NPASS compound ID')
        if native in identities:
            same = raw == originals[native]
            duplicates.append({'source_compound_id': native, 'source_record_ordinal': ordinal,
                               'duplicate_status': 'identical_source_repeat' if same else
                                                   'conflicting_source_identity_hold',
                               'source_record_json': json.dumps(raw, sort_keys = True)})
            if not same:
                identities[native]['identity_status'] = 'source_id_structure_conflict'
            continue
        originals[native] = raw
        identities[native] = {'source_compound_id': native,
                              **identity(raw['SMILES'], raw['InChIKey']),
                              'original_inchi': raw['InChI']}
        if ordinal % 50000 == 0:
            print('NPASS structures checked:', ordinal, flush = True)
    write_csv(output / 'npass_duplicate_identity_records.csv', duplicates,
              ['source_compound_id', 'source_record_ordinal', 'duplicate_status', 'source_record_json'])
    with gzip.open(output / 'npass_identity.csv.gz', 'wt', newline = '') as stream:
        writer = csv.DictWriter(stream, fieldnames = list(next(iter(identities.values()))))
        writer.writeheader()
        writer.writerows(identities.values())
    matches = catalog_matches(identities.values(), baseline, 'NPASS_3.0')
    write_csv(output / 'npass_overlap.csv', matches, list(matches[0]))
    observations = [npass_toxicity(raw, identities.get(raw['np_id'], {}), n, a_keys)
                    for n, raw in tab_rows(toxicity)]
    with gzip.open(output / 'npass_toxicity_all.csv.gz', 'wt', newline = '') as stream:
        writer = csv.DictWriter(stream, fieldnames = list(observations[0]))
        writer.writeheader()
        writer.writerows(observations)
    write_csv(output / 'npass_rat_oral_ld50_eligible.csv', [], list(observations[0]))
    summary = {'source_structure_records': source_count, 'identity_records': len(identities),
        'duplicate_identity_records': len(duplicates), 'identity_status': dict(Counter(
        r['identity_status'] for r in identities.values())),
        'unique_valid_full_keys': len({r['full_inchikey'] for r in identities.values()
                                      if r['identity_status'] == 'valid'}),
        'toxicity_records': len(observations), 'toxicity_endpoints': dict(Counter(
            r['endpoint'] for r in observations)),
        'rat_ld50_rows_before_context_filter': sum(
            r['endpoint'] == 'LD50' and r['test_species'].lower() in {'rat', 'rattus norvegicus'}
            for r in observations), 'eligible_exact': 0, 'eligible_censored': 0,
        'net_new_eligible_full_structures': 0, 'net_new_independent_studies': None,
        'exclusion_reasons': dict(Counter(reason for r in observations
                                         for reason in r['exclusion_reason'].split(';'))),
        'overlap': {cohort: dict(Counter(r['match_tier'] for r in matches if r['cohort'] == cohort))
                    for cohort in ('A', 'B', 'selection')},
        'limits': 'Catalog membership is not verified occurrence. Missing route, acute context '
                  'and experimental status block all NPASS toxicity admissions.'}
    return finish(output, inputs, before, summary)


def finish(output, inputs, before, summary):
    if before != {str(p): sha256(p) for p in inputs}:
        raise ValueError('Inputs changed during normalization')
    code = [Path(__file__), Path(__file__).with_name('data_sprint.py'),
            Path(__file__).with_name('sprint_toxval.py'),
            Path(__file__).with_name('evidence_release.py')]
    reproduction = output / 'reproduction'
    reproduction.mkdir()
    for path in code:
        shutil.copyfile(path, reproduction / path.name)
    summary.update(inputs = before, code_hashes = {str(p): sha256(p) for p in code},
                   products = {str(p.relative_to(output)): sha256(p)
                               for p in output.rglob('*') if p.is_file()})
    (output / 'manifest.json').write_text(json.dumps(summary, indent = 2) + '\n')
    return summary


def run_coconut(registry, baseline_path, output, *, cohort_only=False):
    source = source_file(registry, 'coconut-lite')
    inputs = [source, Path(baseline_path)]
    before = {str(p): sha256(p) for p in inputs}
    baseline = baseline_members(baseline_path)
    output = Path(output)
    output.mkdir(parents = True, exist_ok = False)
    statuses, source_keys, ids = Counter(), set(), set()
    # Only catalog identities relevant to the supplied cohorts need a persistent overlay.
    wanted = {r['full_inchikey'].split('-')[0] for r in baseline if r['full_inchikey']}
    matched, conflicts = [], []
    with ZipFile(source) as archive:
        csv_members = [n for n in archive.namelist() if n.lower().endswith('.csv')]
        if len(csv_members) != 1:
            raise ValueError('Expected one COCONUT CSV member')
        with archive.open(csv_members[0]) as raw, io.TextIOWrapper(raw, encoding = 'utf-8-sig',
                                                                 newline = '') as stream:
            reader = csv.DictReader(stream)
            # Explicit schema selected after inspecting the real source header.
            required = {'identifier', 'canonical_smiles', 'standard_inchi_key'}
            if not required <= set(reader.fieldnames or []):
                raise ValueError(f'Unrecognized COCONUT headers: {reader.fieldnames}')
            for n, row in enumerate(reader, 1):
                native = row['identifier']
                if native in ids or not native:
                    raise ValueError('Missing or duplicate COCONUT ID')
                ids.add(native)
                if cohort_only and row['standard_inchi_key'].split('-')[0] not in wanted:
                    statuses['outside_provider_connectivity_index'] += 1
                    continue
                item = {'source_compound_id': native,
                        **identity(row['canonical_smiles'], row['standard_inchi_key'])}
                statuses[item['identity_status']] += 1
                key = item['full_inchikey']
                if item['identity_status'] == 'valid':
                    source_keys.add(key)
                    if key.split('-')[0] in wanted:
                        matched.append(item)
                else:
                    conflicts.append(item)
                if n % 100000 == 0:
                    print('COCONUT structures checked:', n, flush = True)
    matches = catalog_matches(matched, baseline, 'COCONUT_2026-11')
    write_csv(output / 'coconut_overlap.csv', matches, list(matches[0]))
    fields = ['source_compound_id', 'original_structure', 'provider_full_inchikey', 'full_inchikey',
              'identity_status', 'unspecified_atom_stereocenters']
    with gzip.open(output / 'coconut_identity_conflicts.csv.gz', 'wt', newline = '') as stream:
        writer = csv.DictWriter(stream, fieldnames = fields)
        writer.writeheader()
        writer.writerows(conflicts)
    write_csv(output / 'coconut_matched_identity.csv', matched, fields)
    summary = {'source_records': len(ids), 'identity_status': dict(statuses),
               'qualification_scope': 'cohort_provider_connectivity' if cohort_only else 'full',
               'unique_valid_full_keys': len(source_keys),
               'overlap': {cohort: dict(Counter(r['match_tier'] for r in matches
                                               if r['cohort'] == cohort))
                           for cohort in sorted({r['cohort'] for r in baseline})},
               'new_toxicity_observations': 0,
               'limits': 'Catalog membership only. Connectivity is review-only; source/derived '
                         'key disagreements are excluded. No unmatched synthetic-origin labels.'}
    return finish(output, inputs, before, summary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    sub = parser.add_subparsers(dest = 'command', required = True)
    npass = sub.add_parser('npass')
    npass.add_argument('--structures', type = Path, required = True)
    npass.add_argument('--toxicity', type = Path, required = True)
    coconut = sub.add_parser('coconut')
    coconut.add_argument('--registry', type = Path, required = True)
    coconut.add_argument('--cohort-only', action='store_true',
                         help='Recompute keys within the cohort provider-connectivity index')
    for child in (npass, coconut):
        child.add_argument('--baseline', type = Path, required = True)
        child.add_argument('--output', type = Path, required = True)
    args = parser.parse_args()
    result = (run_npass(args.structures, args.toxicity, args.baseline, args.output)
              if args.command == 'npass' else
              run_coconut(args.registry, args.baseline, args.output, cohort_only=args.cohort_only))
    print(json.dumps(result, indent = 2))
