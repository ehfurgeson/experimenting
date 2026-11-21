"""Screen reviewed and previously toxicity-linked natural-product structures."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from rdkit import DataStructs

from catalog_hazard_review import ld50_support
from data_sprint import read_csv, sha256
from evidence_models import toxicity_forest
from evidence_release import FEATURES, structure, write_csv
from nice_endpoint_models import feature_arrays, models, read_observations
from sprint_report import compressed_rows, verify_bundle

BINS = ('low', 'medium', 'high')


def index(rows, field='full_key'):
    return {r[field]: r for r in rows}


def oral_scores(keys, identities, cohort, held):
    mode = 'exploratory_full_fit'
    scores = {key: (held[key], 'scaffold_held_out') for key in keys if key in held}
    remaining = sorted(set(keys) - scores.keys() - cohort.keys())
    if remaining:
        def features(rows):
            return np.array([[float(r[f]) for f in FEATURES] for r in rows])

        train = list(cohort.values())
        labels = np.array([int(r['ld50_bin']) for r in train])
        forest = toxicity_forest().fit(features(train), labels)
        predicted = forest.predict_proba(features(identities[key] for key in remaining))
        scores.update({key: ({'predicted': int(p.argmax()),
                              **{f'probability_{i}': p[i] for i in range(3)}}, mode)
                       for key, p in zip(remaining, predicted, strict=True)})
    return scores


def endpoint_scores(bundle, keys, identities):
    measured = defaultdict(list)
    for row in read_csv(bundle / 'targets.csv'):
        measured[row['endpoint']].append(row)
    held, known = defaultdict(dict), defaultdict(dict)
    for row in read_csv(bundle / 'held_out_predictions.csv'):
        if row['profile'] != 'dummy':
            held[row['endpoint']][row['full_key'], row['profile']] = row
    for row in read_csv(bundle / 'panel_screen.csv'):
        if row['full_key'] and row['score_mode'] != 'unscored_identity':
            known[row['endpoint']][row['full_key']] = row
    x, mx, fps = feature_arrays(keys, identities)
    positions = {key: i for i, key in enumerate(keys)}
    result = []
    metrics = [row for row in read_csv(bundle / 'metrics.csv') if row['profile'] != 'dummy']
    for endpoint, answers in sorted(held.items()):
        records = measured[endpoint]
        binary = records[0]['unit'] == 'binary'
        unit = records[0]['unit']
        training_keys = [row['full_key'] for row in records]
        tx, tmx, tfps = feature_arrays(training_keys, identities)
        by_key = index(records)
        cached = known[endpoint]
        for key in keys:
            if key in cached:
                result.append({f: cached[key][f] for f in (
                    'endpoint', 'unit', 'full_key', 'score_mode', 'observed',
                    'descriptor_score', 'morgan_score', 'max_training_morgan_tanimoto')})
        outside = [key for key in keys if key not in by_key and key not in cached]
        positions_outside = [positions[key] for key in outside]
        assignments = {key: answers[key, 'descriptors']['fold'] for key in training_keys}
        fold_fps = {fold: [fp for key, fp in zip(training_keys, tfps, strict=True)
                           if assignments[key] != fold] for fold in set(assignments.values())}
        fitted = models(binary)
        y = np.array([float(row['target']) for row in records])
        outside_results = {}
        if outside:
            for profile, train, apply in [('descriptors', tx, x), ('descriptors_morgan', tmx, mx)]:
                model = fitted[profile].fit(train, y)
                inputs = apply[positions_outside]
                outside_results[profile] = iter(model.predict_proba(inputs)[:, 1] if binary else model.predict(inputs))
        for key in keys:
            if key in cached:
                continue
            observed = ''
            if key in by_key:
                a, b = (answers[key, profile]['prediction'] for profile in ('descriptors', 'descriptors_morgan'))
                available = fold_fps[assignments[key]]
                point = float(by_key[key]['target'])
                observed = int(point) if binary else 10 ** point
                mode = 'scaffold_held_out'
            else:
                a, b = (next(outside_results[profile]) for profile in ('descriptors', 'descriptors_morgan'))
                available = tfps
                mode = 'exploratory_full_fit'
            result.append({'endpoint': endpoint, 'unit': unit, 'full_key': key, 'score_mode': mode,
                           'observed': observed, 'descriptor_score': float(a) if binary else 10 ** float(a),
                           'morgan_score': float(b) if binary else 10 ** float(b),
                           'max_training_morgan_tanimoto': max(
                               DataStructs.BulkTanimotoSimilarity(fps[positions[key]], available))})
        print(f'{endpoint}: {len(keys)} structures screened', flush=True)
    return result, metrics


def endpoint_flags(rows):
    flags = defaultdict(list)
    for row in rows:
        if row['unit'] != 'binary':
            continue
        endpoint = row['endpoint']
        if row['observed'] not in ('', None):
            if float(row['observed']) == 1:
                flags['observed_positive_endpoints'].append(endpoint)
            continue
        a, b = float(row['descriptor_score']), float(row['morgan_score'])
        if a >= .5 and b >= .5:
            flags['both_forests_positive_endpoints'].append(endpoint)
            if float(row['max_training_morgan_tanimoto']) < .30:
                flags['both_positive_below_point30_similarity'].append(endpoint)
        elif (a >= .5) != (b >= .5):
            flags['forest_disagreement_endpoints'].append(endpoint)
    return {name: ';'.join(sorted(values)) for name, values in flags.items()}


def run(root, nice, review, output):
    root, nice, review, output = map(Path, (root, nice, review, output))
    directories = ('public-cohorts-v2', 'public-panel-reviewed-v1', 'other-toxicity-endpoints-v2',
                   'npass-label-trusted-v2', 'nice-assay-model-v2', 'coconut', 'npass',
                   'npass-context-v2', 'integrated-reviewed-v1', 'parthenium-review-v2')
    for directory in directories:
        verify_bundle(root / directory)
    release, panel_bundle, endpoints, trusted_dir, assay_dir = (root / name for name in directories[:5])
    model_dir = root / 'public-models-v2'
    model_manifest = json.loads((model_dir / 'manifest.json').read_text())
    model_predictions = model_dir / 'predictions.csv'
    if (model_manifest['release_manifest_sha256'] != sha256(release / 'manifest.json')
            or model_manifest['outputs'][model_predictions.name] != sha256(model_predictions)):
        raise ValueError('Published oral model does not match the measured release')
    a, b = (index(read_csv(release / f'{path}_compounds.csv')) for path in ('A', 'B'))
    trusted = index(read_csv(trusted_dir / 'candidate_labels.csv'))
    panel = read_csv(panel_bundle / 'panel.csv')
    explicit = [r for r in panel if r['panel'] == 'reviewed_selection_natural_product'
                or r['source_kind'] == 'plant_literature']
    panel_keys = {r['full_key'] for r in explicit if r['full_key']}
    herbicide_keys = {r['full_key'] for r in panel if r['panel'] in (
        'HRAC_2026', 'reviewed_selection_herbicide') and r['full_key']}
    toxicity_keys = a.keys() | b.keys()
    catalog = {name: {r['full_inchikey'] for r in read_csv(root / name / f'{name}_overlap.csv')
                      if r['match_tier'] == 'exact_full_key' and r['full_inchikey'] in toxicity_keys}
               for name in ('coconut', 'npass')}
    keys = sorted(panel_keys | catalog['coconut'] | catalog['npass'] | trusted.keys())
    wanted = set(keys)
    identities = index(r for r in read_csv(release / 'chemical_identity.csv') if r['identity_status'] == 'valid')
    identities.update(trusted)
    for row in explicit:
        if row['full_key']:
            item = structure(row['canonical_smiles'])
            if item.get('full_key') != row['full_key'] or item['identity_status'] != 'valid':
                raise ValueError('Reviewed panel structure identity differs from its key')
            identities[row['full_key']] = item
    for _ in read_observations(nice, identities, defaultdict(Counter)):
        pass
    scored_endpoints, metrics = endpoint_scores(endpoints, keys, identities)
    by_structure = defaultdict(list)
    for row in scored_endpoints:
        by_structure[row['full_key']].append(row)
    oral_held = defaultdict(dict)
    for row in read_csv(model_predictions):
        if row['task'] == 'classification' and row['profile'] == 'forest':
            oral_held[row['pathway']][row['full_key']] = row
    oral = {'ICE_forest': oral_scores(keys, identities, a, oral_held['A']),
            'CATMoS_forest': oral_scores(keys, identities, b, oral_held['B'])}
    augmented = index(r for r in read_csv(trusted_dir / 'held_out_predictions.csv')
                      if r['profile'] == 'trusted_npass_exact_and_bounds')
    oral['ICE_NPASS_forest'] = oral_scores(keys, identities, a | trusted, augmented)
    assay = index(r for r in read_csv(assay_dir / 'held_out_predictions.csv')
                  if r['profile'] == 'structure_and_assay_calls')
    oral['ICE_NICE_assay_forest'] = {key: (assay[key], 'scaffold_held_out') for key in wanted & assay.keys()}
    oral_rows = []
    for profile, scores in oral.items():
        for key, (row, mode) in scores.items():
            oral_rows.append({'full_key': key, 'profile': profile, 'score_mode': mode,
                              'predicted_bin': BINS[int(row['predicted'])],
                              **{f'probability_{band}': row[f'probability_{i}'] for i, band in enumerate(BINS)}})
    names, support = {}, defaultdict(list)
    for row in read_csv(release / 'B_predictions.csv'):
        if row['full_key'] in wanted:
            names.setdefault(row['full_key'], json.loads(row['source_record_json']).get('Name') or '')
    for row in read_csv(release / 'A_observations.csv'):
        key = row['full_key']
        if key in wanted and row['status'] in {'exact', 'censored'}:
            info = json.loads(row['source_record_json'])
            names[key] = info.get('Preferred_Name') or info.get('Chemical_Name') or names.get(key, '')
            support[key].append(row)
    occurrence = {r['full_inchikey'] for r in compressed_rows(
        root / 'npass-context-v2' / 'npass_occurrences.csv.gz')
        if r['occurrence_evidence_type'] == 'taxon_and_publication_linked_unreviewed'}
    plant, sources = defaultdict(list), defaultdict(set)
    for row in explicit:
        if row['full_key']:
            key = row['full_key']
            sources[key].add(row['panel'])
            names[key] = row['compound_name']
    for row in read_csv(review):
        if row['full_key'] in wanted:
            plant[row['full_key']].append({'evidence_kind': 'literature_review', **row})
            names[row['full_key']] = row['compound']
    parthenium = {r['compound_name']: r['full_key'] for r in explicit
                  if r['panel'] == 'Parthenium_hysterophorus' and r['full_key']}
    for row in read_csv(root / 'parthenium-review-v2' / 'observations.csv'):
        if row['compound_name'] in parthenium and row['context_response'] == 'high':
            key = parthenium[row['compound_name']]
            plant[key].append({'evidence_kind': 'high_inhibition_dose_point', 'full_key': key,
                               'compound': row['compound_name'],
                               **{name: row[name] for name in ('doi', 'source_locator', 'test_species',
                                                              'endpoint', 'nominal_concentration_uM',
                                                              'derived_inhibition_percent')}})
    for row in read_csv(root / 'integrated-reviewed-v1' / 'plant_response_leads.csv'):
        if row['full_inchikey'] in wanted:
            plant[row['full_inchikey']].append({'evidence_kind': 'ecotox_identity_and_form_review',
                'full_key': row['full_inchikey'], 'compound': row['chemical_name'],
                **{k: row[k] for k in ('doi', 'source_locator', 'plant_species', 'concentration',
                                      'concentration_unit', 'signed_inhibition_percent')}})
    summaries = []
    for key in keys:
        row = {'full_key': key, 'compound_name': names.get(key, ''), 'smiles': identities[key]['smiles'],
               'panel_membership': ';'.join(sorted(sources[key])),
               'coconut_exact_cohort_link': key in catalog['coconut'], 'npass_exact_cohort_link': key in catalog['npass'],
               'npass_taxon_reference_lead': key in occurrence, 'herbicide_panel_overlap': key in herbicide_keys,
               'ice_measured_bin': BINS[int(a[key]['ld50_bin'])] if key in a else '',
               'ice_measured_mg_kg': 10 ** float(a[key]['target_log10_mg_kg']) if key in a else '',
               'npass_assumed_oral_bin': BINS[int(trusted[key]['ld50_bin'])] if key in trusted else '',
               'npass_assumed_label_kind': trusted.get(key, {}).get('disposition', ''),
               'npass_assumed_exact_mg_kg': trusted.get(key, {}).get('dose_mg_kg', ''),
               'catmos_teacher_bin': BINS[int(b[key]['ld50_bin'])] if key in b else '',
               'plant_evidence_records': sum(r.get('evidence_kind') != 'literature_review' or
                                             bool(r.get('plant_evidence')) for r in plant[key]),
               'other_evidence_notes': '; '.join(r['other_evidence'] for r in plant[key] if r.get('other_evidence'))}
        if key in a:
            row.update(ld50_support(support[key]))
        for profile, scores in oral.items():
            row[profile + '_bin'] = BINS[int(scores[key][0]['predicted'])] if key in scores else ''
        row.update(endpoint_flags(by_structure[key]))
        summaries.append(row)
    products = {'compound_summary.csv': summaries, 'endpoint_screen.csv': scored_endpoints,
                'oral_scores.csv': oral_rows, 'plant_and_other_evidence.csv': [r for v in plant.values() for r in v],
                'reviewed_natural_products.csv': [r for r in summaries
                                                  if 'reviewed_selection_natural_product' in r['panel_membership']],
                'plant_evidence_followup.csv': [r for r in summaries if r['plant_evidence_records']],
                'identity_holds.csv': [r for r in explicit if not r['full_key']], 'endpoint_metrics.csv': metrics}
    inputs = [root / name / 'manifest.json' for name in directories]
    inputs.extend((model_dir / 'manifest.json', model_predictions, review))
    inputs.extend(nice / name for name in ('acute_inhalation.xlsx', 'cancer.xlsx', 'dart.xlsx', 'endocrine.xlsx',
                                           'eye_irritation.xlsx', 'skin_irritation.xlsx', 'skin_sensitization.xlsx'))
    output.mkdir(parents=True, exist_ok=False)
    for name, rows in products.items():
        write_csv(output / name, rows)
    manifest = {'inputs': {str(p): sha256(p) for p in inputs},
                'products': {name: sha256(output / name) for name in products},
                'catalog_links': len(catalog['coconut'] | catalog['npass']), 'structures': len(keys),
                'endpoint_pairs': len(scored_endpoints), 'plant_evidence_kinds': dict(
                    Counter(r['evidence_kind'] for rows in plant.values() for r in rows))}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'nice', 'review', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    print(json.dumps(run(**vars(parser.parse_args())), indent=2))
