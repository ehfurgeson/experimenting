"""Compare paired scaffold-held-out forests with and without NICE cHTS calls."""

import argparse
import json
import math
from collections import Counter, defaultdict
from contextlib import contextmanager
from pathlib import Path
from shutil import copyfileobj
from statistics import median
from tempfile import SpooledTemporaryFile
from zipfile import ZipFile

import numpy as np

from accepted_uncertainty import paired_intervals
from data_sprint import read_csv, sha256
from evidence_models import classification_metrics, toxicity_forest
from evidence_release import FEATURES, number, write_csv
from nice_archive_coverage import tsv
from sprint_report import verify_bundle


@contextmanager
def nested_tsv(archive, name):
    with archive.open(name) as raw, SpooledTemporaryFile(max_size=8 << 20) as temp:
        copyfileobj(raw, temp)
        with ZipFile(temp) as nested:
            member, = [name for name in nested.namelist() if 'readme' not in name.casefold()]
            yield tsv(nested, member)


def assay_calls(archive, known, potency=None):
    flagged = set()
    counts = Counter()
    with nested_tsv(archive, 'cHTS_InterferenceFlags.zip') as rows:
        for row in rows:
            if row['DTXSID'] in known and not row['Interference Flags'].startswith('No flag:'):
                flagged.add((row['DTXSID'], row['Assay']))
    pairs = defaultdict(set)
    active_records, ac50 = {}, {}
    with nested_tsv(archive, 'cHTS_DataDownload.zip') as rows:
        for row in rows:
            sid, assay = row['DTXSID'], row['Assay']
            endpoint = row['Endpoint']
            if sid not in known or (endpoint != 'Call' and not (potency is not None and endpoint == 'AC50')):
                continue
            if (sid, assay) in flagged:
                if endpoint == 'Call':
                    counts['interference_omitted_rows'] += 1
                continue
            pair = known[sid], assay
            if endpoint == 'AC50':
                value = number(row['Response'])
                if row['ResponseUnit'] in {'uM', 'µM', 'μM'} and value is not None and value > 0:
                    ac50[sid, assay, row['RecordID']] = 6 - math.log10(value)
                continue
            call = row['Response']
            counts['source_call_' + call] += 1
            pairs[pair].add(call)
            if potency is not None and call == 'Active':
                active_records[sid, assay, row['RecordID']] = pair
    usable = {pair: int(calls == {'Active'}) for pair, calls in pairs.items()
              if calls in ({'Active'}, {'Inactive'})}
    counts['omitted_structure_assay_pairs'] = len(pairs) - len(usable)
    counts['usable_structure_assay_pairs'] = len(usable)
    if potency is not None:
        points = defaultdict(list)
        for record, pair in active_records.items():
            if usable.get(pair) == 1 and record in ac50:
                points[pair].append(ac50[record])
        potency.update({pair: median(values) for pair, values in points.items()})
        counts['active_pairs_with_ac50'] = len(potency)
    return usable, dict(counts)


def training_assays(values, assays):
    active = (values == 1).sum(axis=0)
    inactive = (values == 0).sum(axis=0)
    eligible = np.flatnonzero((active >= 10) & (inactive >= 10)
                              & (active + inactive >= .7 * len(values)))
    return sorted(eligible, key=lambda i: (-int(active[i] + inactive[i]), assays[i]))[:128]


def evaluate(cohort, folds, calls, potency=None):
    keys = sorted({key for key, _ in calls})
    assays = sorted({assay for _, assay in calls})
    indexes = {key: i for i, key in enumerate(keys)}
    columns = {assay: i for i, assay in enumerate(assays)}
    values = np.full((len(keys), len(assays)), np.nan)
    for (key, assay), value in calls.items():
        values[indexes[key], columns[assay]] = value
    if potency is not None:
        potency_values = np.full_like(values, np.nan)
        for (key, assay), value in potency.items():
            potency_values[indexes[key], columns[assay]] = value
    x = np.array([[float(cohort[key][f]) for f in FEATURES] for key in keys])
    y = np.array([int(cohort[key]['ld50_bin']) for key in keys])
    membership = np.array([int(folds[key]['fold']) for key in keys])
    groups = np.array([folds[key]['group'] for key in keys])
    profiles = ('structure', 'structure_and_assay_coverage', 'structure_and_assay_calls')
    if potency is not None:
        profiles += ('structure_assay_calls_and_ac50',)
    held = {profile: np.full((len(keys), 3), np.nan) for profile in profiles}
    selected = []
    for fold in sorted(set(membership)):
        train, test = membership != fold, membership == fold
        if set(groups[train]) & set(groups[test]) or set(y[train]) != {0, 1, 2}:
            raise ValueError('Invalid scaffold split or training-class coverage')
        columns = training_assays(values[train], assays)
        if not columns:
            raise ValueError('No assays meet training-only coverage criteria')
        selected.extend({'fold': int(fold), 'assay': assays[i]} for i in columns)
        available = np.isfinite(values[:, columns])
        calls_with_neutral_missing = np.where(available, values[:, columns], .5)
        features_by_profile = [x, np.column_stack((x, available)),
                               np.column_stack((x, calls_with_neutral_missing))]
        if potency is not None:
            observed = potency_values[:, columns]
            features_by_profile.append(np.column_stack(
                (features_by_profile[-1], np.nan_to_num(observed, nan=0.), np.isfinite(observed))))
        for profile, features in zip(profiles, features_by_profile, strict=True):
            model = toxicity_forest().fit(features[train], y[train])
            held[profile][test] = model.predict_proba(features[test])
        print(f'NICE fold {fold}: {len(columns)} assays; {int(test.sum())} test structures', flush=True)
    preds = {profile: prob.argmax(axis=1) for profile, prob in held.items()}
    if any(not np.isfinite(prob).all() for prob in held.values()):
        raise ValueError('Incomplete paired predictions')
    metrics = [{'profile': profile, 'structures': len(keys),
                **classification_metrics(y, preds[profile], held[profile])} for profile in profiles]
    intervals = [{'profile': profile, **r} for profile in profiles[1:]
                 for r in paired_intervals(y, preds['structure'], preds[profile], groups, 'classification')]
    if potency is not None:
        intervals.extend({'profile': 'ac50_increment_over_assay_calls', **r} for r in paired_intervals(
            y, preds['structure_and_assay_calls'], preds['structure_assay_calls_and_ac50'],
            groups, 'classification'))
    predictions = [{'full_key': key, 'group': groups[i], 'fold': int(membership[i]),
                    'profile': profile, 'observed': int(y[i]),
                    'predicted': int(preds[profile][i]),
                    **{f'probability_{c}': float(held[profile][i, c]) for c in (0, 1, 2)}}
                   for i, key in enumerate(keys) for profile in profiles]
    return {'metrics.csv': metrics, 'paired_intervals.csv': intervals,
            'held_out_predictions.csv': predictions, 'training_assays.csv': selected}


def compare_structure_fallback(baseline_rows, assay_rows, folds, profile='structure_and_assay_calls'):
    baseline = {r['full_key']: r for r in baseline_rows
                if (r['pathway'], r['profile'], r['task']) == ('A', 'forest', 'classification')}
    enriched = {r['full_key']: r for r in assay_rows if r['profile'] == profile}
    if set(baseline) != folds.keys() or not set(enriched) <= baseline.keys():
        raise ValueError('Published baseline predictions do not match split membership')
    for key, row in baseline.items():
        if (int(row['fold']) != int(folds[key]['fold']) or
                (key in enriched and (int(row['observed']) != enriched[key]['observed']
                                      or int(row['fold']) != enriched[key]['fold']))):
            raise ValueError('Outcomes or fold membership differ between assay and published baseline')
    results = []
    for stratum, keys in [('with_usable_assays', sorted(enriched)), ('all_measured', sorted(baseline))]:
        results.extend({'stratum': stratum, **row} for row in paired_intervals(
            [int(baseline[key]['observed']) for key in keys],
            [int(baseline[key]['predicted']) for key in keys],
            [int(enriched.get(key, baseline[key])['predicted']) for key in keys],
            [folds[key]['group'] for key in keys], 'classification'))
    return results


def run(archive, release, models, output, include_potency=False):
    archive, release, models, output = map(Path, (archive, release, models, output))
    verify_bundle(release)
    metadata = json.loads((models / 'manifest.json').read_text())
    split_path, prediction_path = models / 'splits.csv', models / 'predictions.csv'
    if (metadata['release_manifest_sha256'] != sha256(release / 'manifest.json')
            or any(metadata['outputs'][p.name] != sha256(p) for p in (split_path, prediction_path))):
        raise ValueError('Model splits do not match release')
    cohort = {row['full_key']: row for row in read_csv(release / 'A_compounds.csv')}
    folds = {row['full_key']: row for row in read_csv(split_path)
             if row['pathway'] == 'A' and row['role'] == 'test'}
    mappings = defaultdict(set)
    for row in read_csv(release / 'A_observations.csv'):
        if row['status'] in {'exact', 'censored'} and row['full_key'] and row['dtxsid']:
            mappings[row['dtxsid']].add(row['full_key'])
    known = {sid: next(iter(keys)) for sid, keys in mappings.items()
             if len(keys) == 1 and keys <= cohort.keys()}
    potency = {} if include_potency else None
    with ZipFile(archive) as source:
        calls, counts = assay_calls(source, known, potency)
    if include_potency and not potency:
        raise ValueError('No usable AC50 records on quality-filtered active calls')
    print(f'Curated NICE calls: {counts}', flush=True)
    products = evaluate(cohort, folds, calls, potency)
    baseline_rows = read_csv(prediction_path)
    products['structure_fallback_intervals.csv'] = compare_structure_fallback(
        baseline_rows, products['held_out_predictions.csv'], folds)
    if include_potency:
        products['ac50_fallback_intervals.csv'] = compare_structure_fallback(
            baseline_rows, products['held_out_predictions.csv'], folds, 'structure_assay_calls_and_ac50')
    output.mkdir(parents=True, exist_ok=False)
    for name, rows in products.items():
        write_csv(output / name, rows)
    inputs = (archive, release / 'manifest.json', models / 'manifest.json', split_path, prediction_path)
    summary = {'inputs': {str(p): sha256(p) for p in inputs},
               'products': {name: sha256(output / name) for name in products}, 'calls': counts}
    (output / 'manifest.json').write_text(json.dumps(summary, indent=2) + '\n')
    return products['metrics.csv']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('archive', 'release', 'models', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--include-potency', action='store_true')
    print(json.dumps(run(**vars(parser.parse_args())), indent=2))
