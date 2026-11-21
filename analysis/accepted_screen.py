"""Experimental evidence integration and model screens under the user's acceptance scope."""

import argparse
import csv
import io
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import polars as pl
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

from accepted_plant_models import chemical_weights
from accepted_sprint import rows
from data_sprint import read_csv, sha256, write_csv
from evidence_release import FEATURES, structure
from sprint_report import verify_bundle


def pareto_front(points):
    """Maximize two explicit objectives; equal points do not dominate one another."""
    points = np.asarray(points, dtype = float)
    if points.ndim != 2 or points.shape[1] != 2 or not np.isfinite(points).all():
        raise ValueError('Two finite objectives required')
    return [not np.any(np.all(points >= p, axis = 1) & np.any(points > p, axis = 1)) for p in points]


def admits_exact_catalog_identity(status):
    """An exact catalog hit requires a valid full-key match. Provider conflicts are not hits."""
    return status == 'valid'


def measured_ld50(full_key, by_connectivity):
    """Measured log10 LD50 on this full key, otherwise on the same connectivity key."""
    rows = [r for r in by_connectivity.get(full_key.split('-')[0], [])
            if r.get('target_log10_mg_kg') not in ('', None)]
    own = [r for r in rows if r['full_key'] == full_key]
    if own:
        return own, 'same_full_key'
    siblings = [r for r in rows if r['full_key'] != full_key]
    if siblings:
        return siblings, 'same_connectivity'
    return [], 'absent'


def displayed_ld50_qualifier(exact_row):
    """Keep the stored number. A limit-test source is relation '>', not a new LD50."""
    if not exact_row:
        return ''
    text = ' '.join(str(exact_row.get(name) or '') for name in (
        'source_record_ids', 'source_record_json', 'reference'))
    if re.search(r'\b(?:no deaths|no mortality|all (?:rats|animals) survived|limit test)\b', text, re.IGNORECASE):
        return '>'
    # ICE/HSDB acute_oral_1852 stores 32,000 mg/kg with qualifier '='.
    # PPDB records >32,000 and the HSDB narrative is survival at 32 g/kg.
    if 'acute_oral_1852' in text:
        return '>'
    return '='


def measured_support(exact_row):
    """Repeated copies of one value are one reported dose, not multiple studies."""
    if not exact_row:
        return ''
    try:
        distinct = int(float(exact_row.get('deduplicated_values') or 0))
        records = int(float(exact_row.get('new_source_records') or 0))
    except (TypeError, ValueError):
        return ''
    if distinct == 1 and records > 1:
        return 'one_reported_value_repeated_across_sources'
    return ''


def run(accepted, sprint, output, plant_bundle = 'plant-v5', plant_models = 'plant-models-v5',
        toxicity_bundle = 'toxicity-v2', toxicity_models = 'toxicity-models-v2',
        uncertainty_bundle = 'uncertainty-v2'):
    accepted, sprint, output = Path(accepted), Path(sprint), Path(output)
    for name in [toxicity_bundle, toxicity_models, uncertainty_bundle, plant_bundle, plant_models]:
        verify_bundle(accepted / name)
    for name in ['npass-v3', 'coconut-v2', 'baseline', 'npass-context-v1']:
        verify_bundle(sprint / name)
    paths = [accepted / toxicity_bundle / 'all_accepted_exact_compounds.csv',
             accepted / toxicity_bundle / 'all_accepted_classification_compounds.csv',
             accepted / plant_bundle / 'plant_training_observations.csv',
             sprint / 'baseline/cohort_membership.csv', sprint / 'npass-v3/npass_identity.csv.gz',
             sprint / 'npass-context-v1/npass_plant_assay_leads.csv.gz']
    baseline_manifest = json.loads((sprint / 'baseline/manifest.json').read_text())
    selection_path = next(Path(p) for p in baseline_manifest['inputs'] if p.endswith('.parquet'))
    paths.append(selection_path)
    cmanifest_path = sprint / 'coconut-v2/manifest.json'
    cmanifest = json.loads(cmanifest_path.read_text())
    archives = [Path(p) for p in cmanifest['inputs'] if Path(p).name == 'coconut-lite']
    paths += [cmanifest_path, archives[0], sprint / 'coconut-v2/coconut_identity_conflicts.csv.gz']
    toxicity_manifest = json.loads((accepted / toxicity_bundle / 'manifest.json').read_text())
    a_observations = next(Path(p).with_name('A_observations.csv')
                          for p in toxicity_manifest['inputs'] if p.endswith('/A_compounds.csv'))
    paths.append(a_observations)
    before = {str(p): sha256(p) for p in paths}
    exact, classification, plant = [read_csv(p) for p in paths[:3]]
    structure_index = {r['full_key']: r for r in [*classification, *plant]}
    selection = [r for r in read_csv(paths[3]) if r['cohort'] == 'selection']
    for r in selection:
        parsed = structure(r['original_structure'])
        if parsed['identity_status'] == 'valid':
            structure_index.setdefault(parsed['full_key'], parsed)
    wanted = set(structure_index)
    names = {r['structure_inchikey']: r['query'] for r in pl.read_parquet(selection_path).to_dicts()
             if r['structure_inchikey']}
    for r in rows(a_observations):
        if r['full_key'] in wanted and r['full_key'] not in names:
            native = json.loads(r['source_record_json'])
            label = native.get('Preferred_Name') or native.get('Chemical_Name')
            if label:
                names[r['full_key']] = label
    catalog = defaultdict(set)
    for r in rows(paths[4]):
        # Match catalog_matches: provider_key_conflict is not an exact catalog hit.
        if r['full_inchikey'] in wanted and admits_exact_catalog_identity(r['identity_status']):
            catalog[r['full_inchikey']].add('NPASS:' + r['source_compound_id'])
    # Reuse the prior complete structure verification. COCONUT conflict IDs stay out.
    # No connectivity-only catalog labels are created. A catalog hit is not an origin claim.
    conflict_ids = {r['source_compound_id'] for r in rows(sprint / 'coconut-v2/coconut_identity_conflicts.csv.gz')}
    with ZipFile(archives[0]) as archive:
        member = next(n for n in archive.namelist() if n.endswith('.csv'))
        with archive.open(member) as raw, io.TextIOWrapper(raw, encoding = 'utf-8-sig', newline = '') as stream:
            for r in csv.DictReader(stream):
                if r['standard_inchi_key'] in wanted and r['identifier'] not in conflict_ids:
                    catalog[r['standard_inchi_key']].add('COCONUT:' + r['identifier'])
    mechanisms, bykey_mechanism = [], defaultdict(list)
    for r in rows(paths[5]):
        if r['evidence_channel'] != 'plant_protein_mechanism':
            continue
        raw = json.loads(r['source_record_json'])
        target = raw['target']
        record = {'full_key': r['full_inchikey'], 'source_compound_id': r['source_compound_id'],
                  'source_record_id': r['source_record_id'], 'target_id': r['source_target_id'],
                  'target_name': r['target_name'], 'target_organism': target.get('target_organism', ''),
                  'uniprot_id': target.get('uniprot_id', ''), 'endpoint': r['endpoint'],
                  'value': r['reported_value'], 'unit': r['reported_unit'], 'qualifier': r['qualifier'],
                  'citation': r['citation'],
                  'evidence_channel': 'affinity_endpoint' if r['endpoint'] in {'Kd', 'Ki'} else
                                      'target_annotated_bioactivity'}
        mechanisms.append(record)
        bykey_mechanism[record['full_key']].append(record)
    exact_bykey = {r['full_key']: r for r in exact}
    by_connectivity = defaultdict(list)
    for r in exact:
        by_connectivity[r['connectivity']].append(r)
    class_bykey = {r['full_key']: r for r in classification}
    plant_bykey = defaultdict(list)
    for r in plant:
        plant_bykey[r['full_key']].append(r)
    selection_ids = defaultdict(list)
    selected_herbicides, selected_natural_products = set(), set()
    for r in selection:
        selection_ids[r['full_inchikey']].append(r['compound_id'])
        if r.get('selection_group') == 'herbicide' and r['full_inchikey']:
            selected_herbicides.add(r['full_inchikey'])
        if r.get('selection_group') == 'natural_product' and r['full_inchikey']:
            selected_natural_products.add(r['full_inchikey'])
    # Selected herbicides stay in the screen. They are not labeled as catalog-accepted
    # natural products when a COCONUT or NPASS row collides with them.
    catalog_keys = {key for key, identifiers in catalog.items() if identifiers}
    accepted_catalog = catalog_keys - selected_herbicides
    pool = sorted({r['full_inchikey'] for r in selection if r['identity_status'] == 'valid'} |
                  set(plant_bykey) | (set(exact_bykey) & catalog_keys))
    pool = [key for key in pool if key in structure_index]
    matrices = [np.array([[float(r[f]) for f in FEATURES] for r in data])
                for data in [exact, classification, plant]]
    x = np.array([[float(structure_index[key][f]) for f in FEATURES] for key in pool])
    reg = RandomForestRegressor(n_estimators = 200, min_samples_leaf = 5, max_features = 1.,
                                random_state = 20261117, n_jobs = 2).fit(
        matrices[0], [float(r['target_log10_mg_kg']) for r in exact])
    tox = RandomForestClassifier(n_estimators = 200, min_samples_leaf = 5, max_features = 1.,
                                 class_weight = 'balanced', random_state = 20261117, n_jobs = 2).fit(
        matrices[1], [int(r['ld50_bin']) for r in classification])
    activity = RandomForestClassifier(n_estimators = 200, min_samples_leaf = 5, max_features = 1.,
                                      class_weight = 'balanced', random_state = 20261117, n_jobs = 2).fit(
        matrices[2], [int(r['label']) for r in plant], sample_weight = chemical_weights(plant))
    dose_prediction, toxicity_probability = reg.predict(x), tox.predict_proba(x)
    activity_probability = activity.predict_proba(x)[:, 1]
    # Distances are descriptor-space coverage diagnostics, not chemical similarity.
    distances = []
    for train in [matrices[0], matrices[2]]:
        scaler = StandardScaler().fit(train)
        neighbor = NearestNeighbors(n_neighbors = 1, algorithm = 'ball_tree').fit(scaler.transform(train))
        distances.append(neighbor.kneighbors(scaler.transform(x))[0][:, 0])
    front = pareto_front(np.column_stack([dose_prediction, activity_probability]))
    candidates = []
    for i, key in enumerate(pool):
        responses = plant_bykey.get(key, [])
        measured_rows, measured_scope = measured_ld50(key, by_connectivity)
        candidates.append({'full_key': key, 'compound_name': names.get(key, key),
                           'selection_ids': ';'.join(sorted(selection_ids[key])),
                           'exact_catalog_hit': key in accepted_catalog,
                           'selected_herbicide': key in selected_herbicides,
                           'selected_natural_product': key in selected_natural_products,
                           'catalog_ids': ';'.join(sorted(catalog.get(key, set()))),
                           'accepted_exact_log10_ld50': exact_bykey.get(key, {}).get('target_log10_mg_kg', ''),
                           'measured_log10_ld50': ';'.join(str(r['target_log10_mg_kg']) for r in measured_rows),
                           'measured_ld50_scope': measured_scope,
                           'measured_ld50_qualifier': ';'.join(
                               displayed_ld50_qualifier(r) for r in measured_rows),
                           'measured_ld50_support': ';'.join(
                               note for r in measured_rows if (note := measured_support(r))),
                           'accepted_ld50_class': class_bykey.get(key, {}).get('ld50_bin', ''),
                           'plant_observations': len(responses),
                           'observed_high_response_fraction': np.mean([int(r['label']) for r in responses])
                                                               if responses else '',
                           'plant_references': len({r['reference_id'] for r in responses}),
                           'plant_protein_records': len(bykey_mechanism[key]),
                           'plant_protein_targets': ';'.join(sorted({r['target_name'] for r in bykey_mechanism[key]})),
                           'predicted_log10_ld50': float(dose_prediction[i]),
                           'predicted_low_ld50_probability': float(toxicity_probability[i, 0]),
                           'predicted_high_plant_response_probability': float(activity_probability[i]),
                           'toxicity_descriptor_distance': float(distances[0][i]),
                           'plant_descriptor_distance': float(distances[1][i]),
                           'exploratory_prediction_pareto_front': bool(front[i]),
                           'screen_status': 'full_fit_exploratory_not_held_out_candidate_validation'})
    candidates.sort(key = lambda r: (-r['exploratory_prediction_pareto_front'],
                                     -r['predicted_high_plant_response_probability'], r['full_key']))
    coverage = []
    for label, keys in [('accepted_exact_toxicity', set(exact_bykey)), ('plant_response', set(plant_bykey)),
                        ('original_selection', {r['full_inchikey'] for r in selection if r['full_inchikey']})]:
        for catalog_hit in [False, True]:
            for measured in [False, True]:
                for response in [False, True]:
                    matched = [k for k in keys if (k in catalog_keys) == catalog_hit and
                               (k in exact_bykey) == measured and (k in plant_bykey) == response]
                    coverage.append({'cohort': label, 'exact_catalog_hit': catalog_hit,
                                     'exact_toxicity': measured, 'plant_response': response,
                                     'full_structures': len(matched)})
    output.mkdir(parents = True, exist_ok = False)
    write_csv(output / 'candidate_screen.csv', candidates, list(candidates[0]))
    unscorable = [r for r in selection if r['full_inchikey'] not in pool]
    write_csv(output / 'unscorable_selection.csv', unscorable, list(selection[0]))
    write_csv(output / 'evidence_combinations.csv', coverage, list(coverage[0]))
    write_csv(output / 'plant_protein_evidence.csv', mechanisms, list(mechanisms[0]))
    three = catalog_keys & set(exact_bykey) & set(plant_bykey)
    summaries = []
    for group, keys in [
            ('exact_catalog_hit_excluding_selected_herbicides', accepted_catalog & set(exact_bykey)),
            ('selected_herbicide', selected_herbicides & set(exact_bykey)),
            ('no_exact_catalog_hit', set(exact_bykey) - catalog_keys - selected_herbicides)]:
        values = [float(exact_bykey[k]['target_log10_mg_kg']) for k in keys]
        summaries.append({'group': group, 'structures': len(keys),
                          'median_log10_ld50': float(np.median(values)) if values else None,
                          'q25_log10_ld50': float(np.quantile(values, .25)) if values else None,
                          'q75_log10_ld50': float(np.quantile(values, .75)) if values else None,
                          'class_counts': json.dumps(dict(Counter(int(exact_bykey[k]['ld50_bin']) for k in keys))),
                          'interpretation': 'catalog_or_cohort_membership_not_an_origin_effect'})
    write_csv(output / 'catalog_toxicity_summary.csv', summaries, list(summaries[0]))
    result = {'inputs': before, 'candidate_structures': len(candidates),
              'toxicity_bundle': toxicity_bundle,
              'toxicity_models': toxicity_models,
              'uncertainty_bundle': uncertainty_bundle,
              'plant_bundle': plant_bundle, 'plant_models': plant_models,
              'unscorable_selection_rows': len(unscorable),
              'pareto_prediction_front': sum(front),
              'exact_catalog_and_exact_toxicity': len(catalog_keys & set(exact_bykey)),
              'catalog_hit_excluding_selected_herbicides_and_exact_toxicity': len(
                  accepted_catalog & set(exact_bykey)),
              'plant_with_exact_toxicity': len(set(plant_bykey) & set(exact_bykey)),
              'all_three_structures': len(three),
              'all_three_selected_herbicides': len(three & selected_herbicides),
              'all_three_selected_natural_products': len(three & selected_natural_products),
              'plant_protein_records': len(mechanisms),
              'affinity_endpoint_records': sum(r['evidence_channel'] == 'affinity_endpoint' for r in mechanisms),
              'plant_protein_reference_count': len({r['citation'] for r in mechanisms}),
              'policy': 'Exact catalog hit means a valid COCONUT or NPASS full key. Provider-key '
                        'conflicts are excluded. Selected herbicides are not given that flag. '
                        'A catalog hit is not an origin claim. The prediction Pareto front maximizes '
                        'predicted LD50 and predicted high-response probability. It is a mathematical '
                        'front, not a safer-herbicide or natural-product shortlist. Measured LD50 is '
                        'separate from the model prediction; a connectivity sibling can supply the '
                        'measured value. Full-data scores are not held-out validation.',
              'limits': 'Catalog absence is unknown origin, not proof of synthetic origin. '
                        'Pooled plant transfer is weak under chemical holdout. Project LD50 bins at '
                        '1,080 and 3,400 mg/kg are tertiles, not EPA or GHS categories. Source IC50 '
                        'and other target bioactivities do not become binding affinities.'}
    if before != {str(p): sha256(p) for p in paths}:
        raise ValueError('Screen input changed')
    rep = output / 'reproduction'
    rep.mkdir()
    shutil.copyfile(__file__, rep / Path(__file__).name)
    result['products'] = {str(p.relative_to(output)): sha256(p)
                          for p in output.rglob('*') if p.is_file()}
    (output / 'manifest.json').write_text(json.dumps(result, indent = 2) + '\n')
    return {k: v for k, v in result.items() if k not in {'inputs', 'products'}}


def argument_parser():
    parser = argparse.ArgumentParser(description = __doc__)
    for name in ['accepted', 'sprint', 'output']:
        parser.add_argument('--' + name, type = Path, required = True)
    parser.add_argument('--plant-bundle', default = 'plant-v5')
    parser.add_argument('--plant-models', default = 'plant-models-v5')
    parser.add_argument('--toxicity-bundle', default = 'toxicity-v2')
    parser.add_argument('--toxicity-models', default = 'toxicity-models-v2')
    parser.add_argument('--uncertainty-bundle', default = 'uncertainty-v2')
    return parser


if __name__ == '__main__':
    args = argument_parser().parse_args()
    print(json.dumps(run(args.accepted, args.sprint, args.output,
                         args.plant_bundle, args.plant_models, args.toxicity_bundle,
                         args.toxicity_models, args.uncertainty_bundle), indent = 2))
