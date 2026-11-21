"""Validate bulk natural product structures and cache model features in batches."""

import argparse
import csv
import gzip
import io
import json
import tarfile
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from itertools import batched
from pathlib import Path
from zipfile import ZipFile

import polars as pl
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import Descriptors, Lipinski, rdMolDescriptors
from rdkit.Chem.rdFingerprintGenerator import GetMorganGenerator

from data_sprint import sha256
from evidence_release import FEATURES, write_csv

GENERATOR = GetMorganGenerator(radius=2, fpSize=2048, includeChirality=True)


def input_records(source, path):
    if source == 'coconut':
        with ZipFile(path) as archive:
            member, = [n for n in archive.namelist() if n.endswith('.csv')]
            with archive.open(member) as raw, io.TextIOWrapper(raw, encoding='utf-8-sig', newline='') as stream:
                for row in csv.DictReader(stream):
                    yield (row['identifier'], row['standard_inchi_key'], row['canonical_smiles'], row['name'])
    elif source == 'lotus':
        with gzip.open(path, 'rt', encoding='utf-8', newline='') as stream:
            reader = csv.DictReader(stream)
            for row in reader:
                smiles = row['structure_smiles']
                if not smiles and row.get('structure_inchi'):
                    molecule = Chem.MolFromInchi(row['structure_inchi'])
                    smiles = Chem.MolToSmiles(molecule) if molecule is not None else ''
                yield (row['structure_wikidata'], row['structure_inchikey'], smiles,
                       row.get('structure_nameTraditional') or row.get('structure_nameIupac') or '')
    elif source == 'lotus-wikidata':
        with (tarfile.open(path, 'r:gz') as archive,
              archive.extractfile('lotus-wikidata-smiles.csv') as raw,
              io.TextIOWrapper(raw, encoding='utf-8', newline='') as stream):
            for row in csv.DictReader(stream):
                yield (row['wikidata_id'], row['inchi_key'], row['smiles'], '')
    else:
        with gzip.open(path, 'rt', encoding='utf-8', newline='') as stream:
            for row in csv.DictReader(stream):
                record = (row['source_compound_id'], row['provider_full_inchikey'], row['original_structure'], '')
                if row['identity_status'] == 'source_id_structure_conflict':
                    yield (*record, 'source_id_structure_conflict')
                else:
                    yield record


def featured(record):
    native, provider_key, smiles, name, *holds = record
    if holds:
        return None, holds[0]
    mol = Chem.MolFromSmiles(smiles or '')
    if mol is None or not mol.GetNumAtoms():
        return None, 'invalid_or_missing_structure'
    if len(Chem.GetMolFrags(mol)) != 1:
        return None, 'multiple_components'
    key = Chem.MolToInchiKey(mol)
    if not key or not provider_key or key != provider_key:
        return None, 'missing_or_conflicting_full_key'
    features = (Descriptors.MolWt(mol), rdMolDescriptors.CalcTPSA(mol), Lipinski.NumHDonors(mol),
                Lipinski.NumHAcceptors(mol), Lipinski.NumRotatableBonds(mol), Lipinski.RingCount(mol),
                rdMolDescriptors.CalcFractionCSP3(mol))
    return {'full_key': key, 'native_id': native, 'smiles': smiles, 'name': name,
            **dict(zip(FEATURES, features, strict=True)),
            'fingerprint': DataStructs.BitVectToBinaryText(GENERATOR.GetFingerprint(mol))}, 'valid'


def process_batch(records):
    RDLogger.DisableLog('rdApp.*')
    return [featured(record) for record in records]


def run(source, path, output, workers=6):
    path, output = Path(path), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    checks = Counter()
    seen, seen_records = set(), set()
    holds, parts = [], []

    def source_rows():
        for record in input_records(source, path):
            checks['source_rows'] += 1
            if source == 'lotus':
                # Triplet metadata repeats the same structure for multiple occurrence reports.
                signature = record[:3]
                if signature in seen_records:
                    checks['repeated_lotus_structure_rows'] += 1
                    continue
                seen_records.add(signature)
            yield record

    with ProcessPoolExecutor(max_workers=workers) as executor:
        for sequence, batches in enumerate(batched(batched(source_rows(), 1024), workers * 2)):
            kept = []
            for batch, results in zip(batches, executor.map(process_batch, batches), strict=True):
                for record, (row, status) in zip(batch, results, strict=True):
                    checks[status] += 1
                    if row is None:
                        native, key, smiles, _ = record[:4]
                        holds.append({'native_id': native, 'provider_full_key': key,
                                      'source_smiles': smiles, 'reason': status})
                    elif row['full_key'] not in seen:
                        seen.add(row['full_key'])
                        kept.append(row)
            if kept:
                part = output / f'features-{sequence:04d}.parquet'
                pl.DataFrame(kept).write_parquet(part)
                parts.append(part)
            if sequence % 5 == 0:
                print(f'{source}: {checks["source_rows"]:,} source rows, {len(seen):,} unique valid keys',
                      flush=True)
    hold_path = output / 'identity_holds.csv'
    write_csv(hold_path, holds, ['native_id', 'provider_full_key', 'source_smiles', 'reason'])
    result = {'source': source, 'counts': dict(checks), 'unique_valid_keys': len(seen),
              'feature_parts': [part.name for part in parts], 'inputs': {str(path): sha256(path)},
              'products': {p.name: sha256(p) for p in (*parts, hold_path)}}
    (output / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', choices=('coconut', 'lotus', 'lotus-wikidata', 'npass'), required=True)
    for name in ('path', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--workers', type=int, default=6)
    result = run(**vars(parser.parse_args()))
    print(json.dumps({k: result[k] for k in ('source', 'counts', 'unique_valid_keys')}, indent=2))
