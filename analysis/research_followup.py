"""Protected representation pilots and evidence-first natural-product analogue queues.

Fixed exploratory profiles, no tuning or automatic model promotion. Uses corrected
plant-v5 labels and toxicity-models-v2 fold memberships from the log10-median
cohort. All products are new. A catalog hit is a database key match with selected
herbicides removed, not an origin claim.
"""

import argparse
import csv
import gzip
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import Crippen, rdFingerprintGenerator
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_fscore_support
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from accepted_plant_models import chemical_weights, partitions
from data_sprint import read_csv, sha256, write_csv
from evidence_release import FEATURES, structure
from oob import oob_permutation
from sprint_report import verify_bundle

SEED = 20261117
CHEMISTRY = FEATURES + ['logp', 'fluorines', 'chlorines', 'bromines', 'iodines', 'formal_charge']
GENERATOR = rdFingerprintGenerator.GetMorganGenerator(radius = 2, fpSize = 2048,
                                                      includeChirality = True)
PROFILES = ['descriptor7_logistic', 'descriptor7_forest', 'chemistry_logistic',
            'chemistry_forest', 'morgan_logistic']


def representations(rows):
    descriptors, chemistry, fingerprints, bits = [], [], [], []
    for row in rows:
        mol = Chem.MolFromSmiles(row['smiles'])
        if mol is None or Chem.MolToInchiKey(mol) != row['full_key']:
            raise ValueError('Invalid or conflicting full-key structure')
        d = [float(row[f]) for f in FEATURES]
        descriptors.append(d)
        numbers = Counter(atom.GetAtomicNum() for atom in mol.GetAtoms())
        chemistry.append(d + [Crippen.MolLogP(mol), *[numbers[n] for n in [9, 17, 35, 53]],
                              Chem.GetFormalCharge(mol)])
        fp = GENERATOR.GetFingerprint(mol)
        fingerprints.append(fp)
        bits.append(np.asarray(fp, dtype = np.float64))
    return {'descriptor7': np.asarray(descriptors), 'chemistry': np.asarray(chemistry),
            'morgan': np.asarray(bits)}, fingerprints


def estimator(profile):
    if profile.endswith('forest'):
        return RandomForestClassifier(n_estimators = 200, min_samples_leaf = 5,
            max_features = 1., class_weight = 'balanced', random_state = SEED, n_jobs = 2)
    logistic = LogisticRegression(C = 1, class_weight = 'balanced', max_iter = 3000,
                                  random_state = SEED)
    return logistic if profile.startswith('morgan') else make_pipeline(StandardScaler(), logistic)


def fit(model, x, y, weights, profile):
    params = {'logisticregression__sample_weight': weights} if hasattr(model, 'steps') else {
        'sample_weight': weights}
    model.fit(x, y, **params)
    if profile.endswith('logistic'):
        fitted = model[-1] if hasattr(model, 'steps') else model
        if np.any(fitted.n_iter_ >= fitted.max_iter):
            raise ValueError('Logistic convergence failed')
    return model


def paired_bootstrap(y, baseline, candidate, groups, weights, classes, repeats = 2000):
    """Resample held-out clusters jointly; conditional on fixed fits and outcomes."""
    unique, inverse = np.unique(groups, return_inverse = True)
    cells = np.zeros((len(unique), 2, len(classes), len(classes)))
    for i, group in enumerate(inverse):
        cells[group, 0, y[i], baseline[i]] += weights[i]
        cells[group, 1, y[i], candidate[i]] += weights[i]

    def scores(counts):
        den = counts.sum(axis = 1) + counts.sum(axis = 2)
        return np.divide(2 * np.diagonal(counts, axis1 = 1, axis2 = 2), den,
                         out = np.zeros_like(den), where = den > 0).mean(axis = 1)

    point = scores(cells.sum(axis = 0))
    rng = np.random.default_rng(SEED)
    differences = []
    for _ in range(repeats):
        draw = rng.multinomial(len(unique), np.full(len(unique), 1 / len(unique)))
        score = scores(np.einsum('g,gijk->ijk', draw, cells))
        differences.append(score[1] - score[0])
    return {'baseline_macro_f1': float(point[0]), 'candidate_macro_f1': float(point[1]),
            'difference': float(point[1] - point[0]),
            'conditional_lower95': float(np.quantile(differences, .025)),
            'conditional_upper95': float(np.quantile(differences, .975)),
            'clusters': len(unique), 'bootstrap_draws': repeats}


def assert_partition(rows, train, test, protocol, groups):
    if set(train) & set(test):
        raise ValueError('Row leakage')
    if protocol == 'publication':
        if {rows[i]['reference_id'] for i in train} & {rows[i]['reference_id'] for i in test}:
            raise ValueError('Reference leakage')
    elif set(groups[train]) & set(groups[test]):
        raise ValueError('Chemical group leakage')


def benchmark(rows, matrices, task, protocol, folds, groups, frozen_keys):
    labels = np.array([int(r['ld50_bin'] if task == 'toxicity' else r['label']) for r in rows])
    classes = list(range(3 if task == 'toxicity' else 2))
    predicted = {name: np.full(len(rows), -1, dtype = int) for name in PROFILES}
    predictions, coefficients, membership = [], [], []
    for fold, (train, test) in enumerate(folds):
        assert_partition(rows, train, test, protocol, groups)
        if set(labels[train]) != set(classes):
            raise ValueError('Insufficient training class support')
        sample_weights = chemical_weights([rows[i] for i in train]) if task == 'plant' else None
        membership.extend({'task': task, 'protocol': protocol, 'fold': fold,
                           'row_id': rows[i].get('observation_id', rows[i]['full_key']),
                           'full_key': rows[i]['full_key'], 'group': str(groups[i])}
                          for i in test)
        for profile in PROFILES:
            representation = profile.rsplit('_', 1)[0]
            x = matrices[representation]
            model = fit(estimator(profile), x[train], labels[train], sample_weights, profile)
            probability = model.predict_proba(x[test])
            pred = model.classes_[probability.argmax(axis = 1)].astype(int)
            predicted[profile][test] = pred
            for j, i in enumerate(test):
                predictions.append({'task': task, 'protocol': protocol, 'fold': fold,
                    'profile': profile, 'row_id': rows[i].get('observation_id', rows[i]['full_key']),
                    'full_key': rows[i]['full_key'], 'observed': int(labels[i]),
                    'predicted': int(pred[j]), **{f'probability_{c}': float(probability[j, k])
                    for k, c in enumerate(model.classes_)}})
            if profile.endswith('logistic') and representation != 'morgan':
                fitted = model[-1]
                coef_classes = fitted.classes_[1:] if len(classes) == 2 else fitted.classes_
                for cls, coefs in zip(coef_classes, fitted.coef_, strict = True):
                    coefficients.extend({'task': task, 'protocol': protocol, 'fold': fold,
                        'profile': profile, 'class': int(cls), 'feature': feature,
                        'standardized_weight': float(w)} for feature, w in zip(
                            FEATURES if representation == 'descriptor7' else CHEMISTRY,
                            coefs, strict = True))
        print(task, protocol, 'fold', fold, 'complete', flush = True)
    if any(np.any(p < 0) for p in predicted.values()):
        raise ValueError('Each row needs exactly one held-out prediction')
    evaluation = np.array([r['full_key'] in frozen_keys for r in rows]) if task == 'toxicity' else np.ones(len(rows), bool)
    y = labels[evaluation]
    weight = chemical_weights([r for r, keep in zip(rows, evaluation, strict = True) if keep]) if task == 'plant' else np.ones(len(y))
    results, intervals = [], []
    for profile in PROFILES:
        p = predicted[profile][evaluation]
        precision, recall, f1, support = precision_recall_fscore_support(
            y, p, labels = classes, sample_weight = weight, zero_division = 0)
        results.append({'task': task, 'protocol': protocol, 'profile': profile,
            'evaluation': 'unchanged_frozen_A' if task == 'toxicity' else 'quantitative_equal_structure',
            'n': len(y), 'macro_f1': float(f1_score(y, p, labels = classes,
                average = 'macro', sample_weight = weight, zero_division = 0)),
            'confusion': json.dumps(confusion_matrix(y, p, labels = classes, sample_weight = weight).tolist()),
            **{f'class_{c}_{metric}': float(values[k]) for metric, values in [
                ('precision', precision), ('recall', recall), ('f1', f1), ('support', support)]
                for k, c in enumerate(classes)}})
        if profile != 'descriptor7_forest':
            intervals.append({'task': task, 'protocol': protocol, 'profile': profile,
                'baseline': 'descriptor7_forest', **paired_bootstrap(y,
                    predicted['descriptor7_forest'][evaluation], p, groups[evaluation], weight, classes)})
    return predictions, coefficients, membership, results, intervals


def catalog_exact_hit(row):
    """A catalog hit is a valid full-key match. Selected herbicides are not hits."""
    if 'exact_catalog_hit' in row:
        return row['exact_catalog_hit'] == 'True' and row.get('selected_herbicide') != 'True'
    return row.get('natural_catalog_accepted') == 'True' and row.get('selected_herbicide') != 'True'


def evidence_band(labels):
    values = set(labels)
    return 'mixed_context_response' if values == {0, 1} else 'tested_high_response' if values == {1} else 'tested_low_response_only' if values == {0} else 'no_plant_observations'


def analogue_queue(queries, pool, fps, minimum = 3400., top_k = 5):
    result = []
    for query in queries:
        mol = Chem.MolFromSmiles(query['original_structure'])
        if mol is None or Chem.MolToInchiKey(mol) != query['full_inchikey']:
            continue
        similarities = DataStructs.BulkTanimotoSimilarity(GENERATOR.GetFingerprint(mol), fps)
        eligible = [i for i, r in enumerate(pool) if r['connectivity'] != query['full_inchikey'][:14]
                    and float(r['target_log10_mg_kg']) >= np.log10(minimum)]
        indices = sorted(eligible, key = lambda i: (-similarities[i], pool[i]['full_key']))[:top_k]
        result.extend({'query_id': query['compound_id'], 'query_full_key': query['full_inchikey'],
                       'analogue_full_key': pool[i]['full_key'], 'rank': rank,
                       'morgan_tanimoto': float(similarities[i]),
                       'accepted_ld50_mg_kg': 10 ** float(pool[i]['target_log10_mg_kg']),
                       'evidence': 'catalog_match_and_accepted_toxicity; plant_effect_requires_review'}
                      for rank, i in enumerate(indices, 1))
    return result


def lotus_overlay(path, wanted):
    """Retain native triplets; a DOI/catalog link does not become reviewed occurrence."""
    expected = 'cf0cf2afa2ca4d758b68f2e39d466f5d'
    if hashlib.md5(Path(path).read_bytes()).hexdigest() != expected:
        raise ValueError('LOTUS v11 archive does not match publisher MD5')
    selected, fields, total = [], None, 0
    with gzip.open(path, 'rt', encoding = 'utf-8', newline = '') as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        key_columns = [f for f in fields if f.lower() in {'structure_inchikey', 'inchikey'}]
        if len(key_columns) != 1:
            raise ValueError('Inspect LOTUS headers before mapping: ' + repr(fields))
        for r in reader:
            total += 1
            if r[key_columns[0]] in wanted:
                selected.append(r)
    return selected, fields, {'source_rows': total, 'matched_rows': len(selected),
                             'matched_full_keys': len({r[key_columns[0]] for r in selected})}


def run(accepted, sprint, output, lotus = None):
    accepted, sprint, output = map(Path, [accepted, sprint, output])
    manifests = [accepted / name / 'manifest.json' for name in [
        'toxicity-v2', 'toxicity-models-v2', 'plant-v5', 'plant-models-v5', 'integrated-screen-v5']]
    manifests += [sprint / 'baseline/manifest.json']
    for manifest in manifests:
        verify_bundle(manifest.parent)
    sources = [accepted / 'toxicity-v2/all_accepted_classification_compounds.csv',
               accepted / 'toxicity-v2/frozen_A_compounds.csv',
               accepted / 'toxicity-models-v2/split_membership.csv',
               accepted / 'plant-v5/plant_training_observations.csv',
               accepted / 'integrated-screen-v5/candidate_screen.csv',
               sprint / 'baseline/cohort_membership.csv',
               accepted / 'toxicity-v2/all_accepted_exact_compounds.csv']
    if lotus:
        sources.append(Path(lotus))
    before = {str(p): sha256(p) for p in [*manifests, *sources]}
    output.mkdir(parents = True, exist_ok = False)
    toxicity, frozen, toxicity_split, plants, candidates, baseline, exact = map(read_csv, sources[:7])
    # Match accepted_toxicity_models: training rows follow sorted full keys.
    toxicity.sort(key = lambda r: r['full_key'])
    selection = [r for r in baseline if r['cohort'] == 'selection']
    plant = [r for r in plants if r['label_kind'] == 'quantitative']
    tox_matrices, _ = representations(toxicity)
    plant_matrices, _ = representations(plant)
    memberships = {r['full_key']: r for r in toxicity_split}
    assigned = np.array([int(memberships[r['full_key']]['fold']) for r in toxicity])
    tox_groups = np.array([memberships[r['full_key']]['group'] for r in toxicity])
    jobs = [('toxicity', 'chemical_group', toxicity, tox_matrices,
             [(np.flatnonzero(assigned != f), np.flatnonzero(assigned == f)) for f in range(5)], tox_groups)]
    from evidence_models import merged_groups
    for protocol in ['publication', 'chemical_group']:
        groups = np.array([r['reference_id'] for r in plant]) if protocol == 'publication' else merged_groups(plant)
        jobs.append(('plant', protocol, plant, plant_matrices, partitions(plant, protocol), groups))
    products = defaultdict(list)
    for task, protocol, rows, matrices, folds, groups in jobs:
        for name, values in zip(['predictions', 'coefficients', 'split_membership', 'metrics', 'paired_intervals'],
            benchmark(rows, matrices, task, protocol, folds, groups, {r['full_key'] for r in frozen}), strict = True):
            products[name].extend(values)
    # Apply prespecified logistic alternatives to the prepared selection. These
    # full-data fits are explicitly distinct from the protected evaluations above.
    scorable = []
    for r in selection:
        parsed = structure(r['original_structure'])
        if parsed['identity_status'] == 'valid' and parsed['full_key'] == r['full_inchikey']:
            scorable.append({**r, **parsed})
    selection_matrices, _ = representations(scorable)
    for task, rows, matrices in [('toxicity', toxicity, tox_matrices), ('plant', plant, plant_matrices)]:
        y = np.array([int(r['ld50_bin'] if task == 'toxicity' else r['label']) for r in rows])
        training_keys = {r['full_key'] for r in rows}
        weights = chemical_weights(rows) if task == 'plant' else None
        for profile in [p for p in PROFILES if p.endswith('logistic')]:
            representation = profile.rsplit('_', 1)[0]
            model = fit(estimator(profile), matrices[representation], y, weights, profile)
            probability = model.predict_proba(selection_matrices[representation])
            for j, r in enumerate(scorable):
                products['selection_model_comparison'].append({'compound_id': r['compound_id'],
                    'full_key': r['full_key'], 'selection_group': r['selection_group'],
                    'task': task, 'profile': profile, 'in_training': r['full_key'] in training_keys,
                    'status': 'full_fit_exploratory_uncalibrated',
                    **{f'probability_{c}': float(probability[j, k]) for k, c in enumerate(model.classes_)}})
    # Separately labelled unweighted OOB forests; tree OOB is not a study/scaffold holdout.
    for task, rows, matrices in [('toxicity', toxicity, tox_matrices), ('plant', plant, plant_matrices)]:
        y = np.array([int(r['ld50_bin']) == 0 if task == 'toxicity' else int(r['label']) for r in rows], int)
        forest = estimator('chemistry_forest').fit(matrices['chemistry'], y)
        products['oob'].extend({'task': task, 'target': 'low_ld50_vs_rest' if task == 'toxicity' else 'high_plant_response',
            'weighting': 'unweighted_observations', **r} for r in oob_permutation(
                forest, matrices['chemistry'], y, CHEMISTRY, repeats = 5, seed = SEED))
    bykey = {r['full_key']: r for r in candidates}
    exact_bykey = {r['full_key']: r for r in exact}
    for row in selection:
        candidate = bykey.get(row['full_inchikey'], {})
        products['selection_screen'].append({**row, **candidate,
            'screen_coverage': 'scored' if candidate else 'unscorable_identity',
            'scope': '116 prepared natural-product rows; 60 herbicide rows; not asserted to be 120'})
    # exact_catalog_hit already excludes selected herbicides. Older screens used
    # natural_catalog_accepted, which is a key match and not an origin claim.
    natural_pool = [exact_bykey[r['full_key']] for r in candidates if catalog_exact_hit(r)
                    and r['full_key'] in exact_bykey]
    _, natural_fps = representations(natural_pool)
    products['analogues'] = analogue_queue([r for r in selection if r['selection_group'] == 'natural_product'],
                                         natural_pool, natural_fps)
    response = defaultdict(list)
    for r in plants:
        response[r['full_key']].append(int(r['label']))
    for r in natural_pool:
        products['natural_toxicity'].append({**r, 'compound_name': bykey[r['full_key']]['compound_name'],
            'accepted_ld50_mg_kg': 10 ** float(r['target_log10_mg_kg']),
            'plant_evidence_band': evidence_band(response[r['full_key']]),
            'catalog_ids': bykey[r['full_key']]['catalog_ids'],
            'origin_tier': 'catalog_membership_not_independently_verified_occurrence'})
    contrasts = defaultdict(list)
    for r in natural_pool:
        contrasts['natural_catalog_' + evidence_band(response[r['full_key']])].append(r)
    herbicide_keys = {r['full_inchikey'] for r in selection if r['selection_group'] == 'herbicide'}
    contrasts['selected_herbicide_with_accepted_exact_toxicity'] = [exact_bykey[k] for k in sorted(herbicide_keys & set(exact_bykey))]
    for group, rs in contrasts.items():
        matrix, _ = representations(rs)
        for j, feature in enumerate(CHEMISTRY):
            products['group_contrasts'].append({'group': group, 'structures': len(rs), 'feature': feature,
                'median': float(np.median(matrix['chemistry'][:, j])),
                'q25': float(np.quantile(matrix['chemistry'][:, j], .25)),
                'q75': float(np.quantile(matrix['chemistry'][:, j], .75)),
                'interpretation': 'descriptive_source_selected_contextual_groups; no_universal_benign_label'})
    lotus_summary = {'status': 'not_downloaded'}
    if lotus:
        triplets, fields, lotus_summary = lotus_overlay(lotus, set(bykey))
        write_csv(output / 'lotus_occurrence_links.csv', triplets, fields)
    for name, values in products.items():
        write_csv(output / f'{name}.csv', values, list(dict.fromkeys(k for r in values for k in r)))
    if before != {p: sha256(p) for p in before}:
        raise ValueError('Inputs changed')
    rep = output / 'reproduction'
    rep.mkdir()
    for name in ['research_followup.py', 'accepted_plant_models.py', 'evidence_models.py',
                 'evidence_release.py', 'oob.py', 'data_sprint.py', 'sprint_report.py']:
        shutil.copyfile(Path(__file__).parent / name, rep / name)
    manifest = {'created_at': datetime.now(UTC).isoformat(), 'inputs': before,
        'seed': SEED, 'profiles': PROFILES, 'lotus': {**lotus_summary,
            'source_url': 'https://zenodo.org/records/19360665', 'release': 'v11, 2026-04-13',
            'license': 'CC BY 4.0', 'evidence_tier': 'database_occurrence_links_unreviewed'},
        'selection_rows': dict(Counter(r['selection_group'] for r in selection)),
        'natural_catalog_exact_toxicity_structures': len(natural_pool),
        'natural_class_counts': dict(Counter(r['ld50_bin'] for r in natural_pool)),
        'features': {'descriptor7': FEATURES, 'chemistry': CHEMISTRY,
                     'morgan': '2048 bits, radius 2, chirality enabled; unscaled binary logistic C=1'},
        'runtime': {p: version(p) for p in ['rdkit', 'numpy', 'scikit-learn']},
        'policy': 'Fixed exploratory profiles, no hyperparameter search. Existing chemical toxicity folds; '
                  'unchanged frozen A evaluation. Quantitative corrected plant responses, equal-structure '
                  'evaluation, inverse-frequency training weights. Publication and chemical holdouts are '
                  'separate, not simultaneous. Full-data existing candidate predictions remain exploratory.',
        'limits': 'No universal natural-benign class, no human-safety label, no dose-matched selectivity. '
                  'Higher LD50 analogue threshold is project-defined 3400 mg/kg; low-class <=1080. '
                  'Analogue search covers catalog-matched accepted exact-toxicity structures, not full COCONUT. '
                  'OOB repeated permutations measure descriptive model reliance/stability, not significance. '
                  'Bootstrap intervals condition on fixed folds/predictions, without refitting or multiplicity correction.',
        'products': {str(p.relative_to(output)): sha256(p) for p in output.rglob('*') if p.is_file()}}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2) + '\n')
    return {k: manifest[k] for k in ['lotus', 'selection_rows', 'natural_catalog_exact_toxicity_structures', 'natural_class_counts']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for name in ['accepted', 'sprint', 'output']:
        parser.add_argument('--' + name, type = Path, required = True)
    parser.add_argument('--lotus', type = Path)
    args = parser.parse_args()
    print(json.dumps(run(args.accepted, args.sprint, args.output, args.lotus), indent = 2))
