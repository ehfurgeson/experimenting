"""Offline ECOTOX bulk preflight: source inventory and unnormalized evidence sample."""
import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

import polars as pl

REQUIRED = {'validation/chemicals.txt': {'cas_number', 'chemical_name', 'dtxsid'},
            'tests.txt': {'test_id', 'test_cas', 'reference_number', 'species_number'},
            'results.txt': {'result_id', 'test_id', 'endpoint'},
            'validation/references.txt': {'reference_number'},
            'validation/species.txt': {'species_number', 'kingdom'}}


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def members(archive):
    """Require one bulk root and the actual core schema; never extract ZIP paths."""
    names = [r.filename for r in archive.infolist() if not r.is_dir()]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate ZIP member')
    if any(PurePosixPath(n).is_absolute() or '..' in PurePosixPath(n).parts for n in names):
        raise ValueError('Unsafe ZIP member path')
    roots = {n.split('/')[0] for n in names}
    if len(roots) != 1:
        raise ValueError('Expected one official bulk root directory')
    root = next(iter(roots))
    mapping = {key: f'{root}/{key}' for key in REQUIRED}
    if not set(mapping.values()) <= set(names):
        raise ValueError('Missing required ECOTOX bulk tables')
    return mapping


def rows(archive, member, required):
    with archive.open(member) as raw, io.TextIOWrapper(raw, encoding = 'ascii', newline = '') as stream:
        reader = csv.reader(stream, delimiter = '|', strict = True)
        header = next(reader)
        if len(header) != len(set(header)) or not required <= set(header):
            raise ValueError(f'Invalid bulk header: {member}')
        for line, values in enumerate(reader, 2):
            if len(values) != len(header):
                raise ValueError(f'Wrong field count: {member}:{line}')
            yield line, dict(zip(header, values, strict = True))


def keyed(archive, member, required, key):
    result = {}
    for line, row in rows(archive, member, required):
        if not row[key] or row[key] in result:
            raise ValueError(f'Missing or duplicate primary key: {member}:{line}')
        result[row[key]] = row
    return result


def inspect(source, crosswalk = (), sample_per_kind = 25):
    if type(sample_per_kind) is not int or not 0 <= sample_per_kind <= 1000:
        raise ValueError('sample_per_kind must be an integer in 0..1000')
    candidates = defaultdict(set)
    for row in crosswalk:
        if row.get('status') == 'approved' and row.get('dtxsid'):
            candidates[row['dtxsid']].add(row['compound_id'])
    with ZipFile(source) as archive:
        mapping = members(archive)
        chemicals = keyed(archive, mapping['validation/chemicals.txt'],
                          REQUIRED['validation/chemicals.txt'], 'cas_number')
        references = keyed(archive, mapping['validation/references.txt'],
                           REQUIRED['validation/references.txt'], 'reference_number')
        species = keyed(archive, mapping['validation/species.txt'],
                        REQUIRED['validation/species.txt'], 'species_number')
        tests, test_counts, result_counts = {}, Counter(), Counter()
        # Store full test rows only when sampled, avoiding a large in-memory database.
        for line, row in rows(archive, mapping['tests.txt'], REQUIRED['tests.txt']):
            key = row['test_id']
            if not key or key in tests:
                raise ValueError(f'Missing or duplicate test_id at line {line}')
            if row['test_cas'] not in chemicals or row['reference_number'] not in references or row['species_number'] not in species:
                raise ValueError(f'Unresolved test foreign key at line {line}')
            tests[key] = (row['test_cas'], row['reference_number'], row['species_number'], line)
            test_counts[row['test_cas']] += 1
        samples, endpoints, sample_counts, ids = [], Counter(), Counter(), set()
        wanted_tests = set()
        for line, row in rows(archive, mapping['results.txt'], REQUIRED['results.txt']):
            if not row['result_id'] or row['result_id'] in ids:
                raise ValueError(f'Missing or duplicate result_id at line {line}')
            ids.add(row['result_id'])
            if row['test_id'] not in tests:
                raise ValueError(f'Unresolved result test_id at line {line}')
            cas, reference, organism, test_line = tests[row['test_id']]
            endpoint = row['endpoint']
            result_counts[cas] += 1
            endpoints[endpoint] += 1
            kind = endpoint if endpoint in {'LD50', 'LC50', 'EC50'} else (
                'plant_other' if species[organism]['kingdom'] == 'Plantae' else None)
            if kind and sample_counts[kind] < sample_per_kind:
                samples.append({'source_chemical_id': f'ECOTOX:chemical:{cas}',
                                'result_id': row['result_id'], 'test_id': row['test_id'],
                                'reference_number': reference, 'species_number': organism,
                                'sample_kind': kind, 'result_line': line, 'test_line': test_line,
                                'result_json': json.dumps(row, sort_keys = True),
                                'reference_json': json.dumps(references[reference], sort_keys = True),
                                'species_json': json.dumps(species[organism], sort_keys = True)})
                wanted_tests.add(row['test_id'])
                sample_counts[kind] += 1
        test_rows = {row['test_id']: json.dumps(row, sort_keys = True)
                     for _, row in rows(archive, mapping['tests.txt'], REQUIRED['tests.txt'])
                     if row['test_id'] in wanted_tests}
        for sample in samples:
            sample['test_json'] = test_rows[sample['test_id']]
        inventory = []
        for cas, chemical in sorted(chemicals.items()):
            matches = sorted(candidates.get(chemical['dtxsid'], []))
            inventory.append({'source_chemical_id': f'ECOTOX:chemical:{cas}', **chemical,
                              'test_records': test_counts[cas], 'result_records': result_counts[cas],
                              'candidate_existing_ids': ';'.join(matches),
                              'identity_status': 'candidate_dtxsid_overlap' if matches else 'unresolved',
                              'natural_origin': 'unknown', 'herbicidal_activity': 'unknown'})
        details = [{'member': f.filename, 'bytes': f.file_size, 'compressed_bytes': f.compress_size,
                    'crc32': f'{f.CRC:08x}'} for f in archive.infolist() if not f.is_dir()]
        release_files = [n for n in archive.namelist() if '/release_notes_' in n]
        releases = {n: archive.read(n).decode('ascii') for n in release_files}
        return {'chemicals': inventory, 'samples': samples, 'members': details,
                'manifest': {'counts': {'chemicals': len(chemicals), 'tests': len(tests),
                                        'results': len(ids), 'references': len(references),
                                        'species': len(species)},
                             'endpoint_counts': dict(sorted(endpoints.items())),
                             'sample_counts': dict(sample_counts), 'release_notes': releases,
                             'candidate_selection_overlap': sum(bool(r['candidate_existing_ids'])
                                                                for r in inventory),
                             'with_results': sum(r['result_records'] > 0 for r in inventory),
                             'relationship_checks': 'Core primary keys and test/result foreign keys passed',
                             'encoding': 'ascii', 'separator': '|',
                             'scope': 'Bulk inventory and bounded raw sample only. DTXSID overlap is '
                                      'a candidate match, not identity approval or biological labeling. '
                                      'No measurement normalization or LD50 potency inference.'}}


def run(source, output, crosswalk = None, sample_per_kind = 25):
    source, output = Path(source).resolve(), Path(output).resolve()
    crosswalk = Path(crosswalk).resolve() if crosswalk else None
    if source.is_relative_to(output) or output.is_relative_to(source.parent):
        raise ValueError('Output must be separate from archive directory')
    if crosswalk and crosswalk.is_relative_to(output):
        raise ValueError('Output must be separate from crosswalk')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use an empty output directory')
    crosswalk_rows = pl.read_parquet(crosswalk).to_dicts() if crosswalk else []
    result = inspect(source, crosswalk_rows, sample_per_kind)
    output.mkdir(parents = True, exist_ok = True)
    for key in ('chemicals', 'samples', 'members'):
        # Explicit empty sample schema keeps zero-sample runs readable.
        data = result[key]
        frame = pl.DataFrame(data) if data else pl.DataFrame(schema = {'sample_kind': pl.String})
        frame.write_parquet(output / f'{key}.parquet')
        frame.write_csv(output / f'{key}.csv')
    inputs = [source, *([crosswalk] if crosswalk else [])]
    manifest = {**result['manifest'], 'input_hashes': {str(p): digest(p) for p in inputs},
                'code_hashes': {str(Path(__file__)): digest(__file__)},
                'lock_hashes': {str(p): digest(p) for p in
                                (Path(__file__).parents[2] / 'uv.lock',
                                 Path(__file__).parents[2] / 'pyproject.toml')},
                'sample_per_kind': sample_per_kind,
                'output_hashes': {str(p): digest(p) for p in output.iterdir()}}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--source', type = Path, required = True)
    parser.add_argument('--output', type = Path, required = True)
    parser.add_argument('--crosswalk', type = Path)
    parser.add_argument('--sample-per-kind', type = int, default = 25)
    args = parser.parse_args()
    manifest = run(args.source, args.output, args.crosswalk, args.sample_per_kind)
    print(json.dumps({key: manifest[key] for key in ('counts', 'sample_counts',
                                                   'candidate_selection_overlap')}, indent = 2))
