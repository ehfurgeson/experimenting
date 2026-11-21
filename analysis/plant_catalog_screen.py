"""Score the toxicity catalog with the existing plant response models."""

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import polars as pl
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold

from accepted_plant_models import SEED, chemical_weights, partitions
from catalog_bulk_screen import descriptor_range, predict_batches
from data_sprint import read_csv, sha256, write_csv
from evidence_models import merged_groups
from evidence_release import FEATURES, structure
from plant_assay_regression import assay_forest

DOSES = (1, 10, 100)
SPECIES = ('radish', 'cress')
COMPOUND_NAMES = (
    'flavone', '7-hydroxyflavone', '7-methoxyflavone', 'chrysin', '5,7-dimethoxyflavone',
    "3',4'-dimethoxyflavone", 'luteolin', 'luteolin tetramethyl ether', '3-hydroxyflavone',
    '3-methoxyflavone', 'morin', 'quercetin', 'rutin', 'beta-naphthoflavone', 'genistein',
    'flavanone', '7-hydroxyflavanone', '7-methoxyflavanone', 'pinocembrin',
    '5,7-dimethoxyflavanone', '(2S)-naringenin', 'naringin', 'hesperetin', 'hesperidin',
    '(+)-catechin', 'catechol', 'phloridzin',
)


def table_cells(table):
    return [[(''.join(cell.itertext())).strip() for cell in row] for row in table.findall('.//tbody/tr')]


def assay_observations(xml_path, compounds_path):
    source = ET.parse(xml_path)
    records = json.loads(compounds_path.read_text())
    tables = {t.findtext('label'): t for t in source.iter('table-wrap')}
    normalize = lambda text: re.sub(r'[^\w]', '', text.casefold())
    names = [normalize(r[0]) for r in table_cells(tables['Table 1'])]
    for number, endpoint in ((1, 'germination'), (2, 'root_length')):
        rows = table_cells(tables[f'Table {number}'])
        if (len(rows) != 1 + len(COMPOUND_NAMES) or any(len(row) != 7 for row in rows)
                or [normalize(row[0]) for row in rows] != names):
            raise ValueError('Unexpected assay table shape or compound order')
        control = rows[0][1:]
        for name, row in zip(COMPOUND_NAMES, rows[1:], strict=True):
            record, = records[name]
            identity = structure(record['SMILES'])
            if identity.get('full_key') != record['InChIKey']:
                raise ValueError(f'Invalid PubChem structure for {name}')
            for i, (reported, control_value) in enumerate(zip(row[1:], control, strict=True)):
                value = float(reported.split('±')[0])
                baseline = float(control_value.split('±')[0])
                yield {'endpoint': endpoint, 'species': SPECIES[i // 3],
                       'dose_um': DOSES[i % 3], 'duration_h': 120, 'compound': row[0],
                       'cid': record['CID'], 'source_table': f'Table {number}',
                       'treated_cell': reported, 'control_cell': control_value,
                       'inhibition_percent': 100 * (1 - value / baseline),
                       **{k: identity[k] for k in ('full_key', 'connectivity', 'scaffold', *FEATURES)}}


def assay_scores(rows, x, positions):
    columns, metrics = {}, []
    for species in SPECIES:
        for endpoint in ('germination', 'root_length'):
            panel = [r for r in rows if r['species'] == species and r['endpoint'] == endpoint]
            key = f'{species}_{endpoint}'
            training = np.array([[r[name] for name in FEATURES] + [np.log10(r['dose_um'])] for r in panel])
            target = np.array([r['inhibition_percent'] for r in panel])
            model = assay_forest()
            held = np.empty(len(panel))
            for train, test in GroupKFold(5).split(training, groups=merged_groups(panel)):
                held[test] = assay_forest().fit(training[train], target[train]).predict(training[test])
            model.fit(training, target)
            columns[f'{key}__outside_descriptor_ranges'] = descriptor_range(x, training[:, :-1])
            for dose in DOSES:
                features = np.column_stack((x, np.full(len(x), np.log10(dose))))
                prediction = predict_batches(model, features)
                observed = np.full(len(x), np.nan, dtype=np.float32)
                for i, r in enumerate(panel):
                    if r['dose_um'] == dose and r['full_key'] in positions:
                        pos = positions[r['full_key']]
                        observed[pos] = target[i]
                        prediction[pos] = held[i]
                prefix = f'{key}_{dose}um'
                columns[f'{prefix}__inhibition_pct'] = prediction
                columns[f'{prefix}__observed_inhibition_pct'] = observed
            metrics.append({'species': species, 'endpoint': endpoint, 'observations': len(panel),
                            'scaffold_holdout_mae_pct_points': float(np.mean(abs(held - target)))})
    return columns, metrics


def pooled_scores(path, x, positions):
    rows = read_csv(path)
    if len(rows) != 733 or len({r['full_key'] for r in rows}) != 211 or Counter(
            int(r['label']) for r in rows) != {0: 526, 1: 207}:
        raise ValueError('Training input does not match documented plant-v5 counts')
    train_x = np.array([[float(r[name]) for name in FEATURES] for r in rows])
    y = np.array([int(r['label']) for r in rows])
    model = RandomForestClassifier(n_estimators=200, min_samples_leaf=5, max_features=1.,
                                   class_weight='balanced', random_state=SEED, n_jobs=2)
    held = {}
    for train, test in partitions(rows, 'chemical_group'):
        model.fit(train_x[train], y[train], sample_weight=chemical_weights([rows[i] for i in train]))
        held.update(zip((rows[i]['full_key'] for i in test), model.predict_proba(train_x[test])[:, 1], strict=True))
    model.fit(train_x, y, sample_weight=chemical_weights(rows))
    predictions = predict_batches(model, x, task='binary')
    known = np.zeros(len(x), dtype=np.uint16)
    for key, n in Counter(r['full_key'] for r in rows).items():
        if key in positions:
            known[positions[key]] = n
            predictions[positions[key]] = held[key]
    return {'pooled_high_response_score': predictions, 'pooled_training_observations': known,
            'pooled_outside_descriptor_ranges': descriptor_range(x, train_x)}


def run(catalog, xml, compounds, output, pooled=None):
    catalog_manifest = catalog.parent / 'manifest.json'
    if sha256(catalog) != json.loads(catalog_manifest.read_text())['products'][catalog.name]:
        raise ValueError('Catalog differs from the verified toxicity run')
    table = pl.read_parquet(catalog, columns=['full_key', 'name', *FEATURES])
    x = table.select(FEATURES).to_numpy()
    positions = {key: i for i, key in enumerate(table['full_key'])}
    rows = list(assay_observations(xml, compounds))
    training_keys = {r['full_key'] for r in rows}
    if len(rows) != 324 or len(training_keys) != len(COMPOUND_NAMES):
        raise ValueError('Assay observations do not match the original study design')
    columns, metrics = assay_scores(rows, x, positions)
    if pooled:
        columns.update(pooled_scores(pooled, x, positions))
    output.mkdir(parents=True, exist_ok=False)
    table.select('full_key', 'name').hstack(pl.DataFrame(columns)).fill_nan(None).write_parquet(
        output / 'plant_scores.parquet')
    write_csv(output / 'assay_training_observations.csv', rows, list(rows[0]))
    write_csv(output / 'assay_validation.csv', metrics, list(metrics[0]))
    manifest = {'structures_scored': table.height, 'pooled_plant_v5': bool(pooled),
                'assay_training_structures': len(training_keys),
                'assay_training_structures_in_catalog': len(training_keys & positions.keys()),
                'assay_conditions': {'doses_um': DOSES, 'duration_h': 120, 'species': SPECIES},
                'inputs': {str(p): sha256(p) for p in (catalog, catalog_manifest, xml, compounds, pooled) if p},
                'products': {p.name: sha256(p) for p in output.iterdir()}}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest['assay_conditions']), f'{table.height:,} structures scored')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ('catalog', 'xml', 'compounds', 'output'):
        parser.add_argument('--' + option, required=True, type=Path)
    parser.add_argument('--pooled', type=Path)
    run(**vars(parser.parse_args()))
