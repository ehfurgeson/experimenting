"""Attach descriptive NICE workbook context to measured ICE structures."""

import argparse
import csv
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from data_sprint import sha256
from evidence_release import NS, structure, workbook_rows


def match(row, mappings, wanted, cache):
    dtxsid = row.get('DTXSID')
    linked = mappings.get(dtxsid, set()) if isinstance(dtxsid, str) else set()
    source_smiles = row.get('SMILES')
    smiles = source_smiles.strip() if isinstance(source_smiles, str) else ''
    has_formula = isinstance(source_smiles, dict)
    has_smiles = smiles.casefold() not in {'', '-', 'na', 'n/a', 'null', 'not available'}
    if has_smiles and smiles not in cache:
        identity = structure(smiles)
        cache[smiles] = identity.get('full_key') if identity['identity_status'] == 'valid' else None
    key = cache.get(smiles)
    candidates = linked | ({key} if key else set())
    if not candidates & wanted:
        return None
    if row.get('Mixture') == 'Mixture' or has_formula or (has_smiles and not key):
        return 'identity_hold', candidates
    if key and (not linked or linked == {key}):
        return 'exact_structure', {key}
    if not has_smiles and len(linked) == 1:
        return 'identifier_only', linked
    return 'identity_hold', candidates


def data_sheets(path):
    with ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
    for sheet in workbook.find('m:sheets', NS):
        name = sheet.attrib['name']
        if name.casefold().startswith(('data', 'integrated')):
            yield name


def run(nice, release, output):
    nice, release, output = map(Path, (nice, release, output))
    workbooks = sorted(path for path in nice.glob('*.xlsx') if path.name != 'acute_oral.xlsx')
    cohort = release / 'A_compounds.csv'
    observations = release / 'A_observations.csv'
    upstream = json.loads((release / 'manifest.json').read_text())['outputs']
    for path in (cohort, observations):
        if sha256(path) != upstream[path.name]:
            raise ValueError(f'Upstream hash mismatch: {path}')
    with cohort.open(encoding='utf-8', newline='') as stream:
        wanted = {row['full_key'] for row in csv.DictReader(stream)}
    mappings = defaultdict(set)
    with observations.open(encoding='utf-8', newline='') as stream:
        for row in csv.DictReader(stream):
            if row['status'] in {'exact', 'censored'} and row['full_key'] and row['dtxsid']:
                mappings[row['dtxsid']].add(row['full_key'])
    output.mkdir(parents=True, exist_ok=False)
    inputs = {str(path): sha256(path) for path in [cohort, observations, *workbooks]}
    cache, inventory = {}, {}
    product = output / 'nice_context.jsonl.gz'
    with gzip.open(product, 'wt', encoding='utf-8') as stream:
        for path in workbooks:
            for sheet in data_sheets(path):
                tally, covered = Counter(), defaultdict(set)
                for ordinal, row in workbook_rows(path, sheet, descriptive=True):
                    tally['source_rows'] += 1
                    if 'DTXSID' not in row:
                        raise ValueError(f'Unrecognized DTXSID column in {path.name}!{sheet}')
                    found = match(row, mappings, wanted, cache)
                    if not found:
                        continue
                    tier, keys = found
                    tally[tier] += 1
                    covered[tier].update(keys & wanted)
                    record = {'source_file': path.name, 'sheet': sheet, 'source_row': ordinal,
                              'identity_tier': tier, 'candidate_full_keys': sorted(keys),
                              'source_record': row}
                    stream.write(json.dumps(record) + '\n')
                inventory[f'{path.name}!{sheet}'] = {
                    'rows': dict(tally), 'cohort_keys': {k: len(v) for k, v in covered.items()}}
                print(path.name, sheet, dict(tally), flush=True)
    manifest = {'inputs': inputs, 'products': {product.name: sha256(product)},
                'sheets': inventory, 'target_scope': 'descriptive_context_only'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('nice', 'release', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    run(args.nice, args.release, args.output)
