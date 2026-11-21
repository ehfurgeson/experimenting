"""Apply the frozen toxicity models to complete bulk catalog feature inventories."""

import argparse
import csv
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import polars as pl

from data_sprint import read_csv, sha256
from evidence_models import toxicity_forest
from evidence_release import FEATURES, write_csv
from nice_endpoint_models import feature_arrays, models, read_observations
from sprint_report import verify_bundle

BATCH_SIZE = 16384
CLASSES = ('low', 'medium', 'high')


def load_catalog(folder, manifest, prefix):
    table = pl.read_parquet([folder / name for name in manifest['feature_parts']])
    if table.height != manifest['unique_valid_keys']:
        raise ValueError(f'The feature count differs from the inventory for {prefix}')
    return table.rename({'native_id': prefix + '_identifier'})


def predict_batches(model, x, packed=None, task='regression'):
    columns = 3 if task == 'multiclass' else 1
    result = np.empty((len(x), columns), dtype=np.float32)
    for start in range(0, len(x), BATCH_SIZE):
        end = min(start + BATCH_SIZE, len(x))
        values = x[start:end]
        if packed is not None:
            bits = np.unpackbits(packed[start:end], axis=1, bitorder='little')
            values = np.column_stack((values, bits))
        if task == 'multiclass':
            result[start:end] = model.predict_proba(values)
        else:
            result[start:end, 0] = model.predict_proba(values)[:, 1] if task == 'binary' else model.predict(values)
    return result if task == 'multiclass' else result[:, 0]


def numeric_column(values, positions, cast=float):
    output = np.full(len(positions), np.nan, dtype=np.float32)
    for key, value in values.items():
        if key in positions and value not in ('', None):
            output[positions[key]] = cast(value)
    return output


def descriptor_range(x, train):
    return ((x < train.min(axis=0)) | (x > train.max(axis=0))).sum(axis=1).astype(np.uint8)


def endpoint_results(directory, identities, positions, x, packed, threads):
    cohorts, held, benchmarks = defaultdict(list), defaultdict(dict), defaultdict(list)
    for row in read_csv(directory / 'targets.csv'):
        cohorts[row['endpoint']].append(row)
    for row in read_csv(directory / 'held_out_predictions.csv'):
        held[row['endpoint'], row['profile']][row['full_key']] = row['prediction']
    for row in read_csv(directory / 'metrics.csv'):
        if row['profile'] != 'dummy':
            benchmarks[row['endpoint']].append(row)
    columns, meta = {}, []
    for endpoint, choices in sorted(benchmarks.items()):
        binary = choices[0]['task'] == 'binary'
        selected = (max(choices, key=lambda r: float(r['macro_f1'])) if binary else
                    min(choices, key=lambda r: float(r['mae_log10'])))
        profile = selected['profile']
        training = cohorts[endpoint]
        tx, tm, _ = feature_arrays([r['full_key'] for r in training], identities)
        model = models(binary)[profile].set_params(n_jobs=threads)
        morgan = profile == 'descriptors_morgan'
        model.fit(tm if morgan else tx, [float(r['target']) for r in training])
        predictions = predict_batches(model, x, packed if morgan else None, 'binary' if binary else 'regression')
        held_positions = np.zeros(len(x), dtype=bool)
        for key, prediction in held[endpoint, profile].items():
            if key in positions:
                predictions[positions[key]] = float(prediction)
                held_positions[positions[key]] = True
        if not binary:
            predictions = np.power(10., predictions)
        outside_range = descriptor_range(x, tx)
        columns[endpoint + '__score'] = predictions
        columns[endpoint + '__held_out'] = held_positions
        columns[endpoint + '__observed'] = numeric_column(
            {r['full_key']: r['target'] for r in training}, positions,
            float if binary else lambda value: 10 ** float(value))
        columns[endpoint + '__outside_descriptor_ranges'] = outside_range
        meta.append({**selected, 'output_unit': training[0]['unit'],
                     'catalog_held_out': int(held_positions.sum()),
                     'catalog_exploratory': len(x) - int(held_positions.sum()),
                     'catalog_outside_any_descriptor_range': int((outside_range > 0).sum())})
        print(f'{endpoint}: {len(x):,} scores using {profile}', flush=True)
    return columns, meta


def oral_results(root, positions, x, threads):
    release = root / 'public-cohorts-v2'
    held, catalogs = defaultdict(dict), {}
    for row in read_csv(root / 'public-models-v2' / 'predictions.csv'):
        if row['task'] == 'classification' and row['profile'] == 'forest':
            held[row['pathway']][row['full_key']] = row
    for path in ('A', 'B'):
        catalogs[path] = read_csv(release / f'{path}_compounds.csv')
    npass_dir = root / 'npass-label-trusted-v2'
    npass = read_csv(npass_dir / 'candidate_labels.csv')
    held['augmented'] = {r['full_key']: r for r in read_csv(npass_dir / 'held_out_predictions.csv')
                         if r['profile'] == 'trusted_npass_exact_and_bounds'}
    catalogs['augmented'] = catalogs['A'] + npass
    columns, summary = {}, []
    for name, cohort in catalogs.items():
        train = np.array([[float(r[f]) for f in FEATURES] for r in cohort], dtype=np.float32)
        model = toxicity_forest().set_params(n_jobs=threads).fit(train, [int(r['ld50_bin']) for r in cohort])
        prob = predict_batches(model, x, task='multiclass')
        status = np.zeros(len(x), dtype=np.uint8)
        for row in cohort:
            key = row['full_key']
            if key in positions:
                i = positions[key]
                scored = held[name].get(key)
                if scored:
                    prob[i] = [float(scored[f'probability_{j}']) for j in range(3)]
                    status[i] = 1
                else:
                    status[i] = 2
        for i, band in enumerate(CLASSES):
            columns[f'oral_{name}__{band}'] = np.where(status == 2, np.nan, prob[:, i])
        columns[f'oral_{name}__mode'] = status
        columns[f'oral_{name}__outside_descriptor_ranges'] = descriptor_range(x, train)
        summary.append({'profile': name, 'held_out': int((status == 1).sum()),
                        'exploratory': int((status == 0).sum()), 'training_only_no_score': int((status == 2).sum())})
        print(f'oral {name}: {len(x):,} structures processed', flush=True)
    columns['ice_oral_ld50_mg_kg'] = numeric_column(
        {r['full_key']: r['target_log10_mg_kg'] for r in catalogs['A']}, positions,
        lambda n: 10 ** float(n))
    columns['ice_oral_bin'] = numeric_column({r['full_key']: r['ld50_bin'] for r in catalogs['A']}, positions)
    columns['catmos_teacher_bin'] = numeric_column({r['full_key']: r['ld50_bin'] for r in catalogs['B']}, positions)
    columns['npass_assumed_oral_bin'] = numeric_column({r['full_key']: r['ld50_bin'] for r in npass}, positions)
    return columns, summary


def merge_catalog(structures, additional, identifier):
    # Earlier inventories take display precedence for exact cross-catalog matches.
    new_structures = additional.join(structures.select('full_key'), on='full_key', how='anti',
                                     maintain_order='left')
    return (pl.concat([structures, new_structures], how='diagonal').drop(identifier)
            .join(additional.select('full_key', identifier, pl.col('name').alias('additional_name')),
                  on='full_key', how='left', maintain_order='left')
            .with_columns(pl.coalesce(pl.col('name').replace('', None), pl.col('additional_name')).alias('name'))
            .drop('additional_name'))


def run(root, nice, coconut, lotus_triplets, output, lotus=(), npass_catalog=None, existing=None, threads=6):
    root, nice, coconut, lotus_triplets, output = map(Path, (root, nice, coconut, lotus_triplets, output))
    cm = verify_bundle(coconut)
    all_structures = load_catalog(coconut, cm, 'coconut')
    lotus_count = 0
    lotus = tuple(map(Path, lotus))
    if lotus:
        l = pl.concat([load_catalog(folder, verify_bundle(folder), 'lotus') for folder in lotus]).unique(
            'full_key', keep='first', maintain_order=True)
        lotus_count = l.height
        all_structures = merge_catalog(all_structures, l, 'lotus_identifier')
        del l
    else:
        all_structures = all_structures.with_columns(pl.lit(None, dtype=pl.String).alias('lotus_identifier'))
    coconut_lotus_count = all_structures.height
    npass_count = 0
    if npass_catalog is not None:
        npass_catalog = Path(npass_catalog)
        n = load_catalog(npass_catalog, verify_bundle(npass_catalog), 'npass')
        npass_count = n.height
        all_structures = merge_catalog(all_structures, n, 'npass_identifier')
        del n
    release, endpoints, npass = (root / name for name in (
        'public-cohorts-v2', 'other-toxicity-endpoints-v2', 'npass-label-trusted-v2'))
    for directory in (release, endpoints, npass):
        verify_bundle(directory)
    model_dir = root / 'public-models-v2'
    model_manifest = json.loads((model_dir / 'manifest.json').read_text())
    model_predictions = model_dir / 'predictions.csv'
    if (model_manifest['release_manifest_sha256'] != sha256(release / 'manifest.json')
            or model_manifest['outputs'][model_predictions.name] != sha256(model_predictions)):
        raise ValueError('Frozen oral predictions failed input fingerprint verification')
    pinned_models = {str(p): sha256(p) for p in
                     (release / 'manifest.json', endpoints / 'manifest.json', npass / 'manifest.json',
                      model_dir / 'manifest.json', model_predictions)}
    nice_inputs = [nice / name for name in ('acute_inhalation.xlsx', 'cancer.xlsx', 'dart.xlsx', 'endocrine.xlsx',
                                            'eye_irritation.xlsx', 'skin_irritation.xlsx', 'skin_sensitization.xlsx')]
    apply = all_structures
    if existing is not None:
        existing = Path(existing)
        earlier = verify_bundle(existing)
        if earlier.get('pinned_models') != pinned_models:
            raise ValueError('Earlier results use different toxicity model inputs')
        if (earlier['counts']['lotus_metadata_structures'] or earlier['counts'].get('npass_structures', 0)
                or any(earlier['inputs'].get(str(p)) != sha256(p) for p in
                       (coconut / 'manifest.json', *nice_inputs))):
            raise ValueError('Earlier results must be the COCONUT-only run with the same inputs')
        schema = pl.read_parquet_schema(existing / 'catalog_scores.parquet')
        old = pl.read_parquet(existing / 'catalog_scores.parquet',
                              columns=[k for k in schema if k == 'full_key' or '__' in k or k in (
                                  'ice_oral_bin', 'ice_oral_ld50_mg_kg', 'catmos_teacher_bin',
                                  'npass_assumed_oral_bin')])
        apply = all_structures.join(old.select('full_key'), on='full_key', how='anti', maintain_order='left')
    keys = apply['full_key'].to_list()
    positions = {key: i for i, key in enumerate(keys)}
    packed = np.frombuffer(b''.join(apply['fingerprint']), dtype=np.uint8).reshape(len(keys), 256)
    x = apply.select(FEATURES).to_numpy().astype(np.float32)
    identities = {r['full_key']: r for r in read_csv(release / 'chemical_identity.csv')
                  if r['identity_status'] == 'valid'}
    for _ in read_observations(nice, identities, defaultdict(Counter)):
        pass
    columns, endpoint_meta = endpoint_results(endpoints, identities, positions, x, packed, threads)
    oral, oral_meta = oral_results(root, positions, x, threads)
    columns.update(oral)
    scores = pl.DataFrame({'full_key': keys, **columns}).fill_nan(None)
    if existing is not None:
        scores = pl.concat([old, scores.select(old.columns)])
        old_endpoints = {r['endpoint']: r for r in read_csv(existing / 'endpoint_summary.csv')}
        old_orals = {r['profile']: r for r in read_csv(existing / 'oral_summary.csv')}
        for row in endpoint_meta:
            for field in ('catalog_held_out', 'catalog_exploratory', 'catalog_outside_any_descriptor_range'):
                row[field] += int(old_endpoints[row['endpoint']][field])
        for row in oral_meta:
            for field in ('held_out', 'exploratory', 'training_only_no_score'):
                row[field] += int(old_orals[row['profile']][field])
    table = all_structures.drop('fingerprint').join(scores, on='full_key', how='left', validate='1:1',
                                                  maintain_order='left')
    keys = table['full_key'].to_list()
    key_set = set(keys)
    occurrences, cited, manual, lotus_keys = Counter(), Counter(), Counter(), set()
    with gzip.open(lotus_triplets, 'rt', encoding='utf-8', newline='') as stream:
        for row in csv.DictReader(stream):
            key = row['structure_inchikey']
            if not key:
                continue
            lotus_keys.add(key)
            if key in key_set:
                occurrences[key] += 1
                cited[key] += bool(row['reference_doi'])
                manual[key] += row['manual_validation'] == 'Y'
    table = table.with_columns(
        pl.Series('lotus_occurrence_rows', [occurrences[key] for key in keys], dtype=pl.UInt32),
        pl.Series('lotus_rows_with_doi', [cited[key] for key in keys], dtype=pl.UInt32),
        pl.Series('lotus_manual_rows', [manual[key] for key in keys], dtype=pl.UInt32)).fill_nan(None)
    output.mkdir(parents=True, exist_ok=False)
    table.write_parquet(output / 'catalog_scores.parquet')
    measured = table.filter(pl.col('ice_oral_ld50_mg_kg').is_not_null())
    measured.write_csv(output / 'measured_ice_catalog.csv')
    measured.filter(pl.col('ice_oral_bin') == 0).sort('ice_oral_ld50_mg_kg', 'full_key').write_csv(
        output / 'measured_low_ld50.csv')
    unresolved = lotus_keys - key_set
    hold_reasons = defaultdict(set)
    for folder in lotus:
        for row in read_csv(folder / 'identity_holds.csv'):
            hold_reasons[row['provider_full_key']].add(row['reason'])
    write_csv(output / 'lotus_core_unscored.csv', [
        {'full_key': key, 'reason': ';'.join(sorted(hold_reasons[key])) or
         ('no_exact_structure_in_metadata' if lotus else 'absent_from_coconut')}
        for key in sorted(unresolved)], ['full_key', 'reason'])
    write_csv(output / 'endpoint_summary.csv', endpoint_meta)
    write_csv(output / 'oral_summary.csv', oral_meta)
    counts = {'structures_scored': table.height, 'coconut_structures': cm['unique_valid_keys'],
              'lotus_metadata_structures': lotus_count,
              'both_structure_inventories': cm['unique_valid_keys'] + lotus_count - coconut_lotus_count,
              'npass_structures': npass_count, 'npass_additional_structures': table.height - coconut_lotus_count,
              'lotus_core_keys': len(lotus_keys), 'lotus_core_keys_scored': len(lotus_keys & key_set),
              'lotus_core_keys_unscored': len(unresolved),
              'ice_measured_keys': table.height - table['ice_oral_ld50_mg_kg'].null_count(),
              'ice_measured_low_keys': int((table['ice_oral_bin'] == 0).sum()),
              'other_endpoint_scores': int(table.height * len(endpoint_meta))}
    inputs = [folder / 'manifest.json' for folder in
              (coconut, *lotus, npass_catalog, release, endpoints, npass, model_dir, existing)
              if folder is not None]
    inputs.extend((lotus_triplets, model_predictions))
    inputs.extend(nice_inputs)
    summary = {'inputs': {str(p): sha256(p) for p in inputs},
               'products': {p.name: sha256(p) for p in output.iterdir()},
               'counts': counts, 'pinned_models': pinned_models,
               'oral_modes': {'0': 'exploratory_full_fit', '1': 'scaffold_held_out',
                                                 '2': 'training_structure_without_held_out_prediction'}}
    (output / 'manifest.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(counts, indent=2))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'nice', 'coconut', 'lotus-triplets', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--lotus', type=Path, nargs='+', default=())
    parser.add_argument('--npass-catalog', type=Path)
    parser.add_argument('--existing', type=Path)
    parser.add_argument('--threads', type=int, default=6)
    run(**vars(parser.parse_args()))
