"""Evaluate and screen chemically distinct NICE toxicity endpoints."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from math import log10
from pathlib import Path
from statistics import median

import numpy as np
from rdkit import Chem, DataStructs
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold, StratifiedGroupKFold

from data_sprint import read_csv, sha256
from evidence_models import SEED, merged_groups, regression_metrics, toxicity_forest
from evidence_release import FEATURES, number, structure, workbook_rows, write_csv
from research_followup import GENERATOR
from sprint_report import compressed_rows, verify_bundle

CALL = {'Active': 1, 'Inactive': 0}
POS_NEG = {'Positive': 1, 'Negative': 0}
NICE_ENDPOINTS = {
    'rat_inhalation_lc50_4h': (
        'acute_inhalation', 'Data', {'Assay': 'Rat Acute Inhalation Toxicity', 'Duration': '4 hr',
                                    'Endpoint': 'LC50', 'Response_Unit': 'mg/L'}, 'mg/L', None),
    'rabbit_eye_irritation': (
        'eye_irritation', 'Data', {'Species': 'Rabbit', 'Assay': 'Draize Eye Irritation/Corrosion Test',
                                   'Endpoint': 'GHS Classification'}, 'binary',
        {'1': 1, '2': 1, '2A': 1, '2B': 1, 'Not classified': 0}),
    'epiderm_skin_irritation': (
        'skin_irritation', 'Data_invitro', {'Assay': 'EpiDerm Irritation', 'Endpoint': 'Call'}, 'binary', CALL),
    'human_maximization_sensitization': (
        'skin_sensitization', 'Data_invivo',
        {'Species': 'Human', 'Assay': 'Human Maximization Test', 'Endpoint': 'Call'}, 'binary', CALL),
    'human_repeat_patch_sensitization': (
        'skin_sensitization', 'Data_invivo',
        {'Species': 'Human', 'Assay': 'Human Repeat Insult Patch Test', 'Endpoint': 'Call'}, 'binary', CALL),
    'mouse_llna_ec3': (
        'skin_sensitization', 'Data_invivo',
        {'Species': 'Mouse', 'Assay': 'LLNA', 'Endpoint': 'EC3', 'Response_Unit': '%'}, '%', None),
    'bacterial_mutagenicity': (
        'cancer', 'Data', {'Assay': 'In Vitro Genotoxicity', 'Endpoint': 'Bacterial mutagenicity'},
        'binary', POS_NEG),
    'rat_feed_carcinogenic_activity': (
        'cancer', 'Data', {'Assay': 'NTP Carcinogenicity', 'Species': 'Rat', 'Route': 'Dosed feed',
                           'Endpoint': 'Level of evidence of carcinogenic activity'}, 'binary',
        {'Clear evidence': 1, 'Some evidence': 1, 'No evidence': 0}),
    'ar_agonist_transactivation': (
        'endocrine', 'Data_invitro', {'Assay': 'AR Transactivation-Agonist', 'Endpoint': 'Call'},
        'binary', CALL),
    'rat_hershberger_antagonism': (
        'endocrine', 'Data_invivo', {'Species': 'Rat', 'Route': 'Oral',
                                     'Assay': 'Hershberger-Antagonist', 'Endpoint': 'Call'}, 'binary', CALL),
    **{f'{species.casefold()}_fetal_malformation_loel': (
        'dart', 'Data', {'Species': species, 'Route': 'Oral', 'Life_Stage': 'Fetal',
                         'Assay': 'DART, Developmental malformation', 'Critical_Effect': 'Yes',
                         'Endpoint': 'LOEL', 'Response_Unit': 'mg/kg/day'}, 'mg/kg/day', None)
       for species in ('Rat', 'Rabbit')},
}
DERMAL = 'rat_dermal_ld50'


def target_value(row, unit, mapping):
    if row.get('Response_Modifier') not in (None, '', '='):
        return None
    if mapping is not None:
        parts = str(row.get('Response') or '').split(';')
        values = {mapping.get(part.strip()) for part in parts}
        return next(iter(values)) if None not in values and len(values) == 1 else None
    value = number(row.get('Response'))
    return value if value is not None and value > 0 and (unit != '%' or value <= 100) else None


def read_observations(nice, identities, counts):
    tables = defaultdict(list)
    for endpoint, (file, sheet, filters, unit, mapping) in NICE_ENDPOINTS.items():
        tables[file, sheet].append((endpoint, filters, unit, mapping))
    cache = {}
    for (file, sheet), endpoints in tables.items():
        path = nice / (file + '.xlsx')
        for ordinal, row in workbook_rows(path, sheet, descriptive=True):
            for endpoint, filters, unit, mapping in endpoints:
                if any(row.get(k) != v for k, v in filters.items()):
                    continue
                counts[endpoint]['selected_endpoint_rows'] += 1
                value = target_value(row, unit, mapping)
                smiles = row.get('SMILES')
                single_chemical = row.get('Mixture') == 'Chemical' or (
                    file == 'dart' and 'Mixture' not in row and bool(row.get('DTXSID')))
                if not single_chemical or not isinstance(smiles, str) or not smiles.strip():
                    counts[endpoint]['mixture_or_missing_structure'] += 1
                    continue
                if value is None:
                    counts[endpoint]['unsupported_response'] += 1
                    continue
                if smiles not in cache:
                    cache[smiles] = structure(smiles)
                identity = cache[smiles]
                if identity['identity_status'] != 'valid':
                    counts[endpoint]['invalid_or_multicomponent_structure'] += 1
                    continue
                key = identity['full_key']
                identities[key] = identity
                counts[endpoint]['usable_records'] += 1
                yield {'endpoint': endpoint, 'full_key': key, 'value': value, 'unit': unit,
                       'source_file': path.name, 'source_locator': f'{sheet}!row{ordinal}',
                       'source_record_id': row.get('Record_ID'), 'chemical_name': row.get('Chemical_Name'),
                       'sex': row.get('Sex'), 'source_measurement_type': row.get('Data_Type'),
                       'reference': row.get('Reference') or row.get('URL') or ''}


def dermal_observations(folders, identities, counts):
    for folder in folders:
        for row in compressed_rows(folder / 'toxval_observations_all.csv.gz'):
            if (row['test_species'].casefold(), row['test_route'].casefold(), row['endpoint']) != (
                    'rat', 'dermal', 'LD50'):
                continue
            counts[DERMAL]['selected_endpoint_rows'] += 1
            key = row['full_inchikey']
            raw = json.loads(row['source_record_json'])['toxval']
            study_type = str(raw.get('STUDY_TYPE') or '').casefold()
            value = number(row['value'])
            if (key not in identities or row['unit'] != 'mg/kg' or row['qualifier'] != '='
                    or row['source_table'] not in {'toxval-echa', 'toxval-chemid', 'toxval-hpvis', 'toxval-tsca8e'}
                    or row['measurement_type'] not in {'experimental', 'undetermined'}
                    or raw.get('QC_STATUS') not in {'pass', 'not determined'}
                    or 'acute' not in study_type or value is None or value <= 0):
                counts[DERMAL]['unsupported_or_unlinked_record'] += 1
                continue
            counts[DERMAL]['usable_records'] += 1
            yield {'endpoint': DERMAL, 'full_key': key, 'value': value, 'unit': 'mg/kg',
                   'source_file': folder.name, 'source_locator': row['source_locator'],
                   'source_record_id': row['source_record_id'], 'chemical_name': row['source_chemical_name'],
                   'sex': raw.get('SEX'), 'source_measurement_type': row['measurement_type'],
                   'reference': row['source_url'] or row['citation']}


def aggregate(observations):
    by_key = defaultdict(list)
    for row in observations:
        by_key[row['endpoint'], row['full_key']].append(row)
    cohorts, conflicts = defaultdict(list), []
    for (endpoint, key), records in sorted(by_key.items()):
        values = {r['value'] for r in records}
        unit = records[0]['unit']
        row = {'endpoint': endpoint, 'full_key': key, 'unit': unit, 'records': len(records),
               'distinct_values': len(values), 'minimum': min(values), 'maximum': max(values)}
        if unit == 'binary' and len(values) > 1:
            conflicts.append(row)
            continue
        target = next(iter(values)) if unit == 'binary' else median(map(log10, values))
        cohorts[endpoint].append({**row, 'target': target})
    return cohorts, conflicts


def feature_arrays(keys, identities):
    x = np.array([[float(identities[key][name]) for name in FEATURES] for key in keys])
    fps = [GENERATOR.GetFingerprint(Chem.MolFromSmiles(identities[key]['smiles'])) for key in keys]
    return x, np.column_stack((x, np.asarray([bytes_to_bits(fp) for fp in fps]))), fps


def bytes_to_bits(fp):
    return np.unpackbits(np.frombuffer(DataStructs.BitVectToBinaryText(fp), dtype='uint8'), bitorder='little')


def models(binary):
    if binary:
        return {'dummy': DummyClassifier(strategy='prior'), 'descriptors': toxicity_forest(),
                'descriptors_morgan': toxicity_forest().set_params(max_features='sqrt')}
    forest = RandomForestRegressor(n_estimators=200, min_samples_leaf=5, random_state=SEED, n_jobs=2)
    return {'dummy': DummyRegressor(strategy='median'), 'descriptors': forest,
            'descriptors_morgan': RandomForestRegressor(n_estimators=200, min_samples_leaf=5,
                max_features='sqrt', random_state=SEED, n_jobs=2)}


def scores(y, pred, binary):
    if not binary:
        return regression_metrics(y, pred)
    labels = np.asarray(pred) >= .5
    return {'macro_f1': f1_score(y, labels, average='macro', zero_division=0),
            'balanced_accuracy': balanced_accuracy_score(y, labels),
            'positive_precision': precision_score(y, labels, zero_division=0),
            'positive_recall': recall_score(y, labels, zero_division=0),
            'auroc': roc_auc_score(y, pred), 'average_precision': average_precision_score(y, pred)}


def fit_endpoint(endpoint, targets, identities, panel_keys):
    keys = [r['full_key'] for r in targets]
    groups = merged_groups([identities[key] for key in keys])
    binary = targets[0]['unit'] == 'binary'
    y = np.array([row['target'] for row in targets])
    if len(y) < 60 or len(set(groups)) < 5 or (binary and min(sum(y == 0), sum(y == 1)) < 15):
        return None
    x, mx, fps = feature_arrays(keys, identities)
    splits = (StratifiedGroupKFold(5, shuffle=True, random_state=SEED) if binary else GroupKFold(5))
    profiles = models(binary)
    features = {'dummy': x, 'descriptors': x, 'descriptors_morgan': mx}
    held = {name: np.full(len(keys), np.nan) for name in profiles}
    membership = np.full(len(keys), -1)
    for fold, (train, test) in enumerate(splits.split(x, y, groups)):
        if set(groups[train]) & set(groups[test]) or (binary and len(set(y[train])) < 2):
            return None
        membership[test] = fold
        for name, model in profiles.items():
            xf = features[name]
            fitted = model.fit(xf[train], y[train])
            held[name][test] = fitted.predict_proba(xf[test])[:, 1] if binary else fitted.predict(xf[test])
    if any(not np.isfinite(pred).all() for pred in held.values()):
        raise ValueError(f'Incomplete held-out predictions for {endpoint}')
    stats = [{'endpoint': endpoint, 'profile': name, 'structures': len(keys), 'groups': len(set(groups)),
              'task': 'binary' if binary else 'log10_regression', 'positive_n': int(y.sum()) if binary else '',
              **scores(y, pred, binary)} for name, pred in held.items()]
    predictions = [{'endpoint': endpoint, 'profile': name, 'full_key': key, 'fold': int(membership[i]),
                    'scaffold_group': groups[i], 'observed': y[i], 'prediction': pred[i]}
                   for name, pred in held.items() for i, key in enumerate(keys)]
    seen = {key: i for i, key in enumerate(keys)}
    outside = sorted(set(panel_keys) - seen.keys())
    outside_scores = {}
    if outside:
        sx, smx, sfps = feature_arrays(outside, identities)
        for name, xf in [('descriptors', sx), ('descriptors_morgan', smx)]:
            fitted = profiles[name].fit(features[name], y)
            outside_scores[name] = fitted.predict_proba(xf)[:, 1] if binary else fitted.predict(xf)
        outside_scores = {key: (outside_scores['descriptors'][i], outside_scores['descriptors_morgan'][i],
                                max(DataStructs.BulkTanimotoSimilarity(sfps[i], fps)))
                          for i, key in enumerate(outside)}
    screened = {}
    for key in panel_keys:
        if key in seen:
            i = seen[key]
            train_fps = [fp for j, fp in enumerate(fps) if membership[j] != membership[i]]
            d, m = held['descriptors'][i], held['descriptors_morgan'][i]
            proximity = max(DataStructs.BulkTanimotoSimilarity(fps[i], train_fps))
            mode, observed = 'scaffold_held_out', y[i] if binary else 10 ** y[i]
        else:
            d, m, proximity = outside_scores[key]
            mode, observed = 'exploratory_full_fit', ''
        screened[key] = {'score_mode': mode, 'observed': observed,
                         'descriptor_score': d if binary else 10 ** d,
                         'morgan_score': m if binary else 10 ** m,
                         'max_training_morgan_tanimoto': proximity}
    return stats, predictions, screened


def run(nice, release, panel, output, toxval=(), dermal_evidence=None):
    nice, release, output = map(Path, (nice, release, output))
    panel = Path(panel) if panel is not None else None
    toxval = list(map(Path, toxval))
    if toxval and dermal_evidence:
        raise ValueError('Choose one dermal evidence input')
    bundles = [release, *([panel] if panel else []), *toxval]
    for bundle in bundles:
        verify_bundle(bundle)
    identities = {}
    for row in read_csv(release / 'chemical_identity.csv'):
        if row['identity_status'] == 'valid':
            identities.setdefault(row['full_key'], row)
    counts = defaultdict(Counter)
    observations = list(read_observations(nice, identities, counts))
    if toxval:
        csv.field_size_limit(max(csv.field_size_limit(), 1 << 25))
        observations.extend(dermal_observations(toxval, identities, counts))
    elif dermal_evidence:
        for row in read_csv(dermal_evidence):
            value = number(row['value'])
            if (row['endpoint'] != DERMAL or row['unit'] != 'mg/kg' or row['full_key'] not in identities
                    or value is None or value <= 0):
                raise ValueError('Invalid frozen dermal observation')
            observations.append({**row, 'value': value})
            counts[DERMAL]['usable_records'] += 1
    cohorts, conflicts = aggregate(observations)
    panel_rows = read_csv(panel / 'panel.csv') if panel else []
    panel_keys = set()
    for row in panel_rows:
        key = row['full_key']
        if key and key not in identities:
            identity = structure(row['canonical_smiles'])
            if identity.get('full_key') == key and identity['identity_status'] == 'valid':
                identities[key] = identity
        if key in identities:
            panel_keys.add(key)
    metrics, predictions, screen, coverage = [], [], [], []
    for endpoint in (*NICE_ENDPOINTS, *((DERMAL,) if toxval or dermal_evidence else ())):
        cohort = cohorts.get(endpoint, [])
        result = fit_endpoint(endpoint, cohort, identities, panel_keys) if cohort else None
        coverage.append({'endpoint': endpoint, **counts[endpoint], 'target_structures': len(cohort),
                         'status': 'modeled' if result else 'insufficient_grouped_endpoint_data'})
        if result is None:
            print(f'{endpoint}: {len(cohort)} targets, insufficient for grouped evaluation', flush=True)
            continue
        stats, held, screened = result
        metrics.extend(stats)
        predictions.extend(held)
        for row in panel_rows:
            context = {k: row[k] for k in ('panel', 'compound_name', 'source_locator', 'full_key')}
            screen.append({'endpoint': endpoint, 'unit': cohort[0]['unit'], **context,
                           **screened.get(row['full_key'], {'score_mode': 'unscored_identity'})})
        print(f'{endpoint}: {len(cohort)} targets; scored {len(screened)} distinct panel structures', flush=True)
    products = {'observations.csv': observations, 'targets.csv': [r for c in cohorts.values() for r in c],
                'binary_conflicts.csv': conflicts, 'coverage.csv': coverage, 'metrics.csv': metrics,
                'held_out_predictions.csv': predictions, 'panel_screen.csv': screen,
                'reviewed_panel_screen.csv': [r for r in screen if r['panel'].startswith('reviewed_selection_')]}
    inputs = [nice / (name + '.xlsx') for name in sorted({row[0] for row in NICE_ENDPOINTS.values()})]
    inputs.extend(b / 'manifest.json' for b in bundles)
    if dermal_evidence:
        inputs.append(dermal_evidence)
    output.mkdir(parents=True, exist_ok=False)
    for name, rows in products.items():
        write_csv(output / name, rows)
    summary = {'inputs': {str(p): sha256(p) for p in inputs},
               'products': {name: sha256(output / name) for name in products}, 'coverage': coverage}
    (output / 'manifest.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('nice', 'release', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--panel', type=Path)
    parser.add_argument('--dermal-evidence', type=Path)
    parser.add_argument('--toxval', type=Path, action='append', default=[])
    print(json.dumps(run(**vars(parser.parse_args())), indent=2))
