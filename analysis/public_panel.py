"""Screen a public herbicide benchmark and reviewed plant-assay structures."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import polars as pl

from data_sprint import read_csv, sha256
from evidence_models import toxicity_forest
from evidence_release import FEATURES, structure, workbook_rows, write_csv
from sprint_report import verify_bundle


def normalize_name(name):
    return ' '.join((name or '').casefold().split())


def resolve_name(name, index):
    return set().union(*(index.get(normalize_name(alias), set()) for alias in name.split('=')))


def name_index(release, wanted_names):
    index = defaultdict(set)
    identities = {}

    def add(name, smiles):
        identity = structure(smiles)
        if identity['identity_status'] == 'valid':
            key = identity['full_key']
            index[name].add(key)
            identities[key] = identity

    for item in read_csv(release / 'A_observations.csv'):
        raw = json.loads(item['source_record_json'])
        if raw['Mixture'] != 'Chemical' or not item['full_key']:
            continue
        for field in ('Chemical_Name', 'Preferred_Name'):
            name = normalize_name(raw[field])
            if name in wanted_names:
                add(name, raw.get('SMILES'))
    for item in read_csv(release / 'B_predictions.csv'):
        raw = json.loads(item['source_record_json'])
        name = normalize_name(raw.get('Name'))
        if name not in wanted_names:
            continue
        # The original form has priority over the potentially stripped QSAR form.
        add(name, item['original_smiles'])
    return index, identities


def benchmark_panel(hrac, index):
    for ordinal, row in hrac:
        name = row['ACTIVE']
        if not isinstance(name, str) or not name.strip():
            continue
        candidates = resolve_name(name, index)
        key, = candidates if len(candidates) == 1 else ['']
        yield {'panel': 'HRAC_2026', 'compound_name': name.strip(), 'source_locator': f'row {ordinal}',
               'hrac_group': row['HRAC GLOBAL'], 'full_key': key,
               'identity_status': ('unambiguous_source_name_lead' if key else
                                   'ambiguous_name' if candidates else 'unresolved_name'),
               'candidate_full_keys': ';'.join(sorted(candidates))}


def reviewed_panel(rows, structures):
    for row in rows:
        key = row['structure_inchikey']
        status = row['structure_status']
        if status == 'valid':
            identity = structure(row['input_smiles'])
            if identity.get('full_key') == key and identity['identity_status'] == 'valid':
                structures[key] = identity
            else:
                status = 'structure_key_conflict'
        yield {'panel': 'reviewed_selection_' + row['chemical_group'],
               'compound_name': row.get('query') or row['compound_id'],
               'source_locator': row['compound_id'], 'hrac_group': '',
               'full_key': key if status == 'valid' else '',
               'identity_status': status, 'candidate_full_keys': key or ''}


def literature_panel(rows, structures):
    studies = defaultdict(list)
    for row in rows:
        studies[row.get('panel') or 'Annona_reticulata', row['compound_name']].append(row)
    for (study, name), records in studies.items():
        variants = {(r['smiles'], r['identity_status']) for r in records}
        smiles, status = next(iter(variants)) if len(variants) == 1 else ('', 'source_identity_conflict')
        key = ''
        if status == 'structure_supported':
            identity = structure(smiles)
            if identity['identity_status'] == 'valid':
                key = identity['full_key']
                structures[key] = identity
            else:
                status = identity['identity_status']
        locators = sorted({r['doi'] + ' ' + r['source_locator'] for r in records})
        yield {'panel': study, 'compound_name': name, 'source_locator': '; '.join(locators),
               'hrac_group': '', 'full_key': key, 'identity_status': status,
               'candidate_full_keys': key, 'source_kind': 'plant_literature'}


def features(row):
    return [float(row[field]) for field in FEATURES]


def run(release, models, hrac, literature, output, selection=None, extra_literature=()):
    release, models, hrac, literature, output = map(Path, (release, models, hrac, literature, output))
    verify_bundle(release)
    model_manifest = json.loads((models / 'manifest.json').read_text())
    prediction_file = models / 'predictions.csv'
    if (model_manifest['release_manifest_sha256'] != sha256(release / 'manifest.json')
            or model_manifest['outputs'][prediction_file.name] != sha256(prediction_file)):
        raise ValueError('Model predictions do not match the public cohort and model manifest')
    raw_panel = list(workbook_rows(hrac, 'Master List', descriptive=True))
    names = {normalize_name(alias) for _, r in raw_panel if isinstance(r['ACTIVE'], str)
             for alias in r['ACTIVE'].split('=')}
    index, structures = name_index(release, names)
    panel = list(benchmark_panel(raw_panel, index))
    if selection is not None:
        selection = Path(selection)
        panel.extend(reviewed_panel(pl.read_parquet(selection).to_dicts(), structures))
    cohorts = {c: {row['full_key']: row for row in read_csv(release / f'{c}_compounds.csv')}
               for c in ('A', 'B')}
    scores = {}
    for row in read_csv(prediction_file):
        if row['profile'] == 'forest' and row['task'] == 'classification':
            scores[row['pathway'], row['full_key']] = row
    literature_sources = [literature, *map(Path, extra_literature)]
    panel.extend(literature_panel((r for path in literature_sources for r in read_csv(path)),
                                  structures))
    fitted = {}
    for row in panel:
        key = row['full_key']
        item = structures.get(key)
        row.setdefault('source_kind', '')
        row['canonical_smiles'] = item['smiles'] if item else ''
        measured = cohorts['A'].get(key)
        row['ice_mg_kg'] = 10 ** float(measured['target_log10_mg_kg']) if measured else None
        row['ice_bin'] = measured['ld50_bin'] if measured else None
        row['catmos_teacher_bin'] = cohorts['B'].get(key, {}).get('ld50_bin')
        for channel, cohort in cohorts.items():
            held = scores.get((channel, key))
            probabilities, mode = [None] * 3, 'unscored'
            if held is not None:
                probabilities = [float(held[f'probability_{i}']) for i in range(3)]
                mode = 'group_held_out'
            elif item is not None and key not in cohort:
                if channel not in fitted:
                    fitted[channel] = toxicity_forest().fit(
                        np.array([features(v) for v in cohort.values()]),
                        [int(v['ld50_bin']) for v in cohort.values()])
                probabilities = list(map(float, fitted[channel].predict_proba([features(item)])[0]))
                mode = 'full_fit_outside_target_cohort'
            row[f'{channel}_score_mode'] = mode
            row[f'{channel}_predicted_bin'] = int(np.argmax(probabilities)) if mode != 'unscored' else ''
            for i, probability in enumerate(probabilities):
                row[f'{channel}_probability_{i}'] = probability
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output / 'panel.csv', panel)
    tally = Counter((r['panel'], r['A_score_mode'], r['B_score_mode']) for r in panel)
    counts = [{'panel': p, 'A_mode': a, 'B_mode': b, 'rows': n} for (p, a, b), n in sorted(tally.items())]
    write_csv(output / 'coverage.csv', counts)
    inputs = [hrac, *literature_sources, prediction_file, models / 'manifest.json', release / 'manifest.json',
              *(release / f'{name}.csv' for name in [
                  'A_compounds', 'B_compounds', 'A_observations', 'B_predictions'])]
    if selection is not None:
        inputs.append(selection)
    manifest = {'inputs': {str(path): sha256(path) for path in inputs},
                'products': {path.name: sha256(path) for path in output.iterdir()},
                'includes_reviewed_selection': selection is not None,
                'limits': 'HRAC source-name matches require tested-form review.'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return counts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('release', 'models', 'hrac', 'literature', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--selection', type=Path, help='Optional original structural_features.parquet')
    parser.add_argument('--extra-literature', type=Path, action='append', default=[])
    print(json.dumps(run(**vars(parser.parse_args())), indent=2))
