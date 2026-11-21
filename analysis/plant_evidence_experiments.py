"""Plant evidence recovery, protected context pilots, curves and validation design.

New source rows remain experimental assertions; canonical adopted labels are never
modified. Complete publications include missing outcomes in a separate audit.
"""

import argparse
import json
import math
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
from scipy.stats import spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, mean_absolute_error, precision_recall_fscore_support
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from accepted_plant import finite, inhibition_label
from accepted_plant_models import chemical_weights
from data_sprint import read_csv, sha256, write_csv
from evidence_models import merged_groups
from evidence_release import FEATURES, structure
from research_followup import paired_bootstrap
from sprint_report import verify_bundle

SEED = 20261117
PLANTS = {'Lactuca sativa', 'Avena sativa', 'Lolium multiflorum', 'Trifolium pratense',
          'Raphanus sativus', 'Echinochloa crus-galli', 'Monochoria vaginalis'}
NUMBER = r'(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?'


def dose_in_description(text):
    """Only one explicit scalar; ranges, bounds, and alternate doses remain unresolved."""
    match = re.search(r'\bat (' + NUMBER + r') (uM|mM|nM|M|mg/L|ug/ml|ug/mL|ppm)\b', text)
    if not match:
        return '', ''
    tail = text[match.end():]
    if re.match(r'\s*(?:to|or|[-–])\s*\d', tail):
        return '', ''
    return match[1], match[2]


def exposure_features(value, unit, mw):
    """Keep aqueous molarity, application rate, soil dose and unresolved ppm separate."""
    result = {'log_molar': np.nan, 'log_kg_ha': np.nan, 'log_soil_mg_kg': np.nan,
              'log_reported_ppm': np.nan, 'dose_family': 'missing_or_unresolved'}
    dose = finite(value)
    if dose is None or dose <= 0:
        return result
    unit = (unit or '').replace('µ', 'u').strip()
    molar = {'M': 1., 'mol/L': 1., 'mM': 1e-3, 'uM': 1e-6, 'umol/L': 1e-6, 'nM': 1e-9}
    mass = {'mg/L': 1e-3, 'ug/L': 1e-6, 'g/L': 1., 'ug/ml': 1e-3, 'ug/mL': 1e-3}
    area = {'kg/ha': 1., 'AI kg/ha': 1., 'g/ha': 1e-3, 'AI g/ha': 1e-3,
            'lb/acre': 1.12085116}
    if unit in molar:
        result.update(log_molar = math.log10(dose * molar[unit]), dose_family = 'molar')
    elif unit in mass and mw > 0:
        result.update(log_molar = math.log10(dose * mass[unit] / mw), dose_family = 'molar')
    elif unit in area:
        result.update(log_kg_ha = math.log10(dose * area[unit]), dose_family = 'area_mass')
    elif unit in {'AI mg/kg soil', 'mg/kg dry soil'}:
        result.update(log_soil_mg_kg = math.log10(dose), dose_family = 'soil_mass')
    elif unit == 'ppm':
        result.update(log_reported_ppm = math.log10(dose), dose_family = 'reported_ppm_unresolved_basis')
    return result


def duration_hours(value, unit):
    factor = {'h': 1., 'hr': 1., 'hrs': 1., 'd': 24., 'day': 24., 'days': 24., 'wk': 168.}.get(unit)
    v = finite(value)
    return math.log10(v * factor) if factor and v is not None and v > 0 else np.nan


def endpoint_family(value):
    text = value.lower().strip('~/')
    if text in {'germ', 'gmen', 'germinated_seed_count'} or 'germination' in text:
        return 'germination'
    if 'root' in text or 'radicle' in text:
        return 'root_length'
    if text in {'bmas', 'dbms', 'wght'} or 'biomass' in text:
        return 'biomass'
    if text in {'hght'} or 'shoot' in text or 'hypocotyl' in text:
        return 'shoot_length'
    return text


def chembl_rows(sources):
    audit, observations, registry, potency = [], [], [], []
    for docfile in sorted(sources.glob('*-document.json')):
        doc = json.loads(docfile.read_text())
        docid, doi = doc['document_chembl_id'], doc.get('doi') or doc['document_chembl_id']
        files = sorted(sources.glob(docid + '-activities-*.json'))
        pages = [json.loads(p.read_text()) for p in files]
        raw = [r for page in pages for r in page['activities']]
        if not pages or len(raw) != pages[0]['page_meta']['total_count'] or len({r['activity_id'] for r in raw}) != len(raw):
            raise ValueError('Incomplete publication series')
        statuses = Counter()
        for r in raw:
            plant = r.get('target_organism') in PLANTS
            value = finite(r.get('standard_value'))
            description = r['assay_description']
            dose, unit = dose_in_description(description)
            parsed = structure(r.get('canonical_smiles') or '')
            explicit = r['standard_type'] == 'Inhibition' and r['standard_units'] == '%' and 'inhibit' in description.lower()
            status = 'nonplant_endpoint' if not plant else 'missing_numeric_response' if value is None else 'response_basis_or_endpoint_unresolved'
            if plant and r['standard_type'] in {'IC50', 'EC50'} and value is not None:
                potency.append({'source_activity_id': r['activity_id'], 'doi': doi,
                    'species': r['target_organism'], 'endpoint': r['standard_type'],
                    'value': value, 'unit': r['standard_units'], 'qualifier': r['standard_relation'],
                    'full_key': parsed.get('full_key', ''), 'assay_description': description,
                    'status': 'separate_plant_potency_not_response_percent'})
            if plant and explicit and value is not None:
                if r['standard_relation'] != '=':
                    status = 'censored_not_continuous_target'
                elif parsed['identity_status'] != 'valid':
                    status = 'unresolved_structure'
                elif not dose:
                    status = 'unresolved_dose'
                elif not -1000 <= value <= 100:
                    status = 'invalid_inhibition_range'
                elif r.get('data_validity_comment'):
                    status = 'provider_validity_hold'
                else:
                    status = 'experimental_database_response'
                    duration = re.search(r'(?:after|measured) (\d+(?:\.\d+)?) (days|day|hr|hrs)', description)
                    # The recovered Kava primary methods explicitly specify seven days.
                    days = '7' if doi.lower() == '10.1021/jf0519461' else ''
                    observations.append({'observation_id': 'ChEMBL:' + str(r['activity_id']),
                        'source': 'ChEMBL_complete_series', 'source_assay_id': r['assay_chembl_id'],
                        'reference_id': doi.lower(), 'plant_species': r['target_organism'],
                        'endpoint': endpoint_family(description), 'dose': dose, 'dose_unit': unit,
                        'duration': duration[1] if duration else days,
                        'duration_unit': duration[2] if duration else 'd' if days else '',
                        'signed_inhibition_percent': value, 'qualifier': '=',
                        'label': inhibition_label(value), 'source_locator': str(docfile),
                        'assumptions': 'database_asserted_response; primary_review_not_general_adoption',
                        **{k: parsed[k] for k in ['full_key', 'connectivity', 'smiles', 'scaffold', *FEATURES]}})
            audit.append({'document': docid, 'doi': doi, 'activity_id': r['activity_id'],
                'assay_id': r['assay_chembl_id'], 'target_organism': r.get('target_organism'),
                'raw_type': r['standard_type'], 'raw_unit': r['standard_units'],
                'raw_value': r['standard_value'], 'raw_qualifier': r['standard_relation'],
                'status': status, 'assay_description': description})
            statuses[status] += 1
        registry.append({'document': docid, 'doi': doi, 'title': doc['title'],
            'complete_source_records': len(raw), 'plant_records': sum(r.get('target_organism') in PLANTS for r in raw),
            'usable_experimental_responses': statuses['experimental_database_response'],
            'status_counts': json.dumps(statuses)})
    return observations, audit, registry, potency


def coumarin_tables(path):
    root = ET.fromstring(path.read_bytes())
    doi = next(e.text for e in root.findall('.//article-id') if e.attrib.get('pub-id-type') == 'doi')
    observations = []
    endpoints = ['germination_frequency', 'normal_seedling_count', 'fresh_biomass']
    for t, endpoint in zip(root.findall('.//table-wrap'), endpoints, strict = True):
        rows = t.findall('.//tbody/tr')
        if len(rows) != 6:
            raise ValueError('Expected all six source compounds')
        for row in rows:
            cells = [''.join(c.itertext()).strip() for c in row]
            code = cells[0]
            values = [float(re.search(NUMBER, c)[0]) for c in cells[1:]]
            if len(values) != 6 or values[0] <= 0:
                raise ValueError('Expected control plus five doses')
            for dose, value in zip([50, 100, 200, 400, 800], values[1:], strict = True):
                observations.append({'observation_id': f'COUM2020:{t.attrib["id"]}:{code}:{dose}',
                    'compound_id': 'COUM2020:' + code, 'source_name': code, 'source_doi': doi,
                    'source_locator': t.attrib['id'] + '; ' + code,
                    'species': 'Lactuca sativa', 'endpoint': endpoint,
                    'concentration': dose, 'dose_unit': 'ug/mL', 'observation_hours': 168,
                    'mean': value, 'control_mean': values[0],
                    'derived_inhibition_percent': 100 * (1 - value / values[0]),
                    'raw_cell': cells[1 + [50, 100, 200, 400, 800].index(dose) + 1],
                    'n_pet_dishes': 3, 'seeds_per_dish': 30,
                    'vehicle': '7 g/L agar with 8 percent Tween80; pH5.8',
                    'identity_status': 'source_code_only_structure_mapping_pending',
                    'origin_status': 'synthetic_eugenol_derivative_not_verified_natural',
                    'limits': 'ratio_of_reported_means; no replicate-level uncertainty'})
    return observations


def curve_analysis(rows):
    grouped = defaultdict(list)
    for r in rows:
        grouped[r['compound_id'], r['species'], r['endpoint'], r['dose_unit']].append(r)
    summaries, predictions = [], []
    for key, rs in sorted(grouped.items()):
        rs.sort(key = lambda r: float(r['concentration']))
        x = np.log10([float(r['concentration']) for r in rs])
        y = np.array([float(r['derived_inhibition_percent']) for r in rs])
        if len(set(x)) < 3:
            continue
        iso = IsotonicRegression(increasing = True, out_of_bounds = 'clip').fit(x, y)
        fitted = iso.predict(x)
        if fitted.max() < 50:
            status, cross = 'above_tested_range_under_monotone_assumption', ''
        elif fitted.min() >= 50:
            status, cross = 'at_or_below_lowest_tested_dose', ''
        else:
            status = 'interpolated_within_tested_range'
            cross = 10 ** float(np.interp(50, fitted, x))
        summaries.append({'compound_id': key[0], 'species': key[1], 'endpoint': key[2], 'unit': key[3],
            'doses': len(x), 'min_dose': 10 ** x.min(), 'max_dose': 10 ** x.max(),
            'min_observed_inhibition': y.min(), 'max_observed_inhibition': y.max(),
            'monotone_fit_mae': float(np.mean(abs(fitted - y))),
            'downward_steps_over_10_percentage_points': int(np.sum(np.diff(y) < -10)),
            'ec50_status': status, 'descriptive_50pct_crossing': cross,
            'interpretation': 'descriptive_monotone_mean_curve_not_mechanistic_EC50_or_validated_potency'})
        # Only interior doses test interpolation; boundary extrapolation is not scored.
        for i in range(1, len(x) - 1):
            tr = np.arange(len(x)) != i
            pred = {
                'training_median': float(np.median(y[tr])),
                'linear_logdose': float(np.polyval(np.polyfit(x[tr], y[tr], 1), x[i])),
                'isotonic_logdose': float(IsotonicRegression(increasing = True,
                    out_of_bounds = 'clip').fit(x[tr], y[tr]).predict(x[i:i + 1])[0])}
            predictions.extend({'compound_id': key[0], 'species': key[1], 'endpoint': key[2],
                'dose': 10 ** x[i], 'unit': key[3], 'observed': y[i], 'profile': name,
                'prediction': p, 'evaluation': 'held_out_interior_dose_known_compound_same_study'}
                for name, p in pred.items())
    return summaries, predictions


NUMERIC = FEATURES + ['log_molar', 'log_kg_ha', 'log_soil_mg_kg', 'log_reported_ppm', 'log_duration_h']
CATEGORICAL = ['plant_species', 'endpoint_family', 'dose_family']


def design_rows(rows):
    out = []
    for r in rows:
        f = exposure_features(r['dose'], r['dose_unit'], float(r['molecular_weight']))
        r = {**r, **f, 'endpoint_family': endpoint_family(r['endpoint']),
             'log_duration_h': duration_hours(r['duration'], r['duration_unit'])}
        out.append([float(r[k]) for k in NUMERIC] + [str(r[k]) for k in [*CATEGORICAL, 'reference_id']])
    return np.array(out, dtype = object)


def model(profile):
    chemistry = list(range(len(FEATURES)))
    context_numeric = list(range(len(FEATURES), len(NUMERIC)))
    categories = list(range(len(NUMERIC), len(NUMERIC) + len(CATEGORICAL)))
    numeric = chemistry if profile == 'chemistry' else context_numeric if profile == 'context' else chemistry + context_numeric
    cats = [] if profile == 'chemistry' else categories
    if profile == 'chemistry_context_study':
        cats = cats + [len(NUMERIC) + len(CATEGORICAL)]
    transformers = [('numeric', make_pipeline(SimpleImputer(strategy = 'median', add_indicator = True,
                        keep_empty_features = True), StandardScaler()), numeric)]
    if cats:
        transformers.append(('context', OneHotEncoder(handle_unknown = 'ignore'), cats))
    return make_pipeline(ColumnTransformer(transformers), LogisticRegression(
        C = 1, class_weight = 'balanced', max_iter = 3000, random_state = SEED))


def contextual_benchmark(rows):
    rows = [r for r in rows if r.get('label') not in {None, ''}]
    x, y = design_rows(rows), np.array([int(r['label']) for r in rows])
    predictions, metrics, uncertainty, support, coefficients = [], [], [], [], []
    for protocol in ['publication', 'chemical_group']:
        groups = np.array([r['reference_id'] for r in rows]) if protocol == 'publication' else merged_groups(rows)
        if len(set(groups)) < 5:
            raise ValueError('Insufficient grouped validation support')
        pred = {p: np.full(len(y), -1) for p in ['chemistry', 'context', 'chemistry_context', 'chemistry_context_study']}
        for fold, (train, test) in enumerate(GroupKFold(5).split(x, y, groups)):
            if set(groups[train]) & set(groups[test]):
                raise ValueError('Grouped leakage')
            if set(y[train]) != {0, 1}:
                raise ValueError('Insufficient training classes')
            weights = chemical_weights([rows[i] for i in train])
            support.append({'protocol': protocol, 'fold': fold, 'train_rows': len(train),
                'test_rows': len(test), 'train_high': int(y[train].sum()), 'test_high': int(y[test].sum()),
                'test_groups': len(set(groups[test])),
                'overlap_structures': len({rows[i]['full_key'] for i in train} & {rows[i]['full_key'] for i in test})})
            for profile, decisions in pred.items():
                fitted = model(profile).fit(x[train], y[train], logisticregression__sample_weight = weights)
                if np.any(fitted[-1].n_iter_ >= fitted[-1].max_iter):
                    raise ValueError('Logistic convergence failed')
                probability = fitted.predict_proba(x[test])[:, 1]
                decisions[test] = probability >= .5
                coefficients.extend({'protocol': protocol, 'fold': fold, 'profile': profile,
                    'transformed_feature': str(feature), 'weight_for_high_response': float(weight)}
                    for feature, weight in zip(fitted[0].get_feature_names_out(), fitted[-1].coef_[0], strict = True))
                predictions.extend({'protocol': protocol, 'fold': fold, 'profile': profile,
                    'observation_id': rows[i]['observation_id'], 'full_key': rows[i]['full_key'],
                    'reference_id': rows[i]['reference_id'], 'group': str(groups[i]),
                    'observed': int(y[i]), 'probability': float(p)}
                    for i, p in zip(test, probability, strict = True))
        w = chemical_weights(rows)
        for profile, p in pred.items():
            if np.any(p < 0):
                raise ValueError('Incomplete predictions')
            precision, recall, f1, count = precision_recall_fscore_support(y, p,
                labels = [0, 1], sample_weight = w, zero_division = 0)
            metrics.append({'protocol': protocol, 'profile': profile, 'rows': len(rows),
                'structures': len({r['full_key'] for r in rows}),
                'macro_f1': float(f1_score(y, p, labels = [0, 1], average = 'macro', sample_weight = w)),
                'high_f1': float(f1[1]), 'high_recall': float(recall[1]), 'high_precision': float(precision[1]),
                'weighted_high_support': float(count[1])})
            if profile != 'chemistry':
                uncertainty.append({'protocol': protocol, 'profile': profile,
                    **paired_bootstrap(y, pred['chemistry'], p, groups, w, [0, 1])})
        print('Context benchmark', protocol, 'complete', flush = True)
    return predictions, metrics, uncertainty, support, coefficients


def run(sources, accepted, flavonoids, output):
    sources, accepted, flavonoids, output = map(Path, [sources, accepted, flavonoids, output])
    verify_bundle(accepted / 'plant-v5')
    source_registry = json.loads((sources / 'sources.json').read_text())
    for r in source_registry:
        if r.get('sha256') and sha256(sources / r['name']) != r['sha256']:
            raise ValueError('Acquired source hash mismatch')
    files = [*sources.glob('*'), accepted / 'plant-v5/manifest.json',
        accepted / 'plant-v5/plant_training_observations.csv',
        flavonoids / 'transcription-v1/observations.csv', flavonoids / 'analysis-v2/compounds.csv']
    before = {str(p): sha256(p) for p in files if p.is_file()}
    new, audit, registry, potency = chembl_rows(sources)
    old = [r for r in read_csv(accepted / 'plant-v5/plant_training_observations.csv') if r['label_kind'] == 'quantitative']
    old_ids = {r['observation_id'] for r in old}
    new = [r for r in new if r['observation_id'] not in old_ids]
    observations = [*old, *new]
    if len({r['observation_id'] for r in observations}) != len(observations):
        raise ValueError('Duplicate observations')
    curves = coumarin_tables(sources / 'coumarins2020.xml')
    flav = [{**r, 'concentration': r['concentration_uM'], 'dose_unit': 'uM'}
            for r in read_csv(flavonoids / 'transcription-v1/observations.csv')]
    summaries, curve_predictions = curve_analysis([*flav, *curves])
    predictions, metrics, uncertainty, support, coefficients = contextual_benchmark(observations)
    output.mkdir(parents = True, exist_ok = False)
    products = {'new_chembl_responses': new, 'source_record_audit': audit, 'publication_registry': registry,
        'separate_plant_potency': potency, 'combined_experimental_responses': observations,
        'coumarin_primary_observations': curves, 'curve_summaries': summaries,
        'curve_predictions': curve_predictions, 'context_predictions': predictions,
        'context_metrics': metrics, 'context_intervals': uncertainty, 'context_support': support,
        'context_coefficients': coefficients}
    curve_metrics = []
    for source in ['FLAV2012', 'COUM2020']:
        for profile in ['training_median', 'linear_logdose', 'isotonic_logdose']:
            rs = [r for r in curve_predictions if r['compound_id'].startswith(source) and r['profile'] == profile]
            y, p = [[float(r[k]) for r in rs] for k in ['observed', 'prediction']]
            curve_metrics.append({'source': source, 'profile': profile, 'held_out_points': len(rs),
                'mae_percentage_points': float(mean_absolute_error(y, p)),
                'spearman': float(spearmanr(y, p).statistic),
                'claim': 'interpolation_same_compound_and_study_not_new_chemical_validation'})
    products['curve_metrics'] = curve_metrics
    for name, rs in products.items():
        write_csv(output / f'{name}.csv', rs, list(dict.fromkeys(k for r in rs for k in r)))
    if before != {p: sha256(p) for p in before}:
        raise ValueError('Input changed')
    rep = output / 'reproduction'
    rep.mkdir()
    for name in ['plant_evidence_experiments.py', 'accepted_plant.py', 'accepted_plant_models.py',
                 'research_followup.py', 'evidence_models.py', 'evidence_release.py', 'data_sprint.py']:
        shutil.copyfile(Path(__file__).parent / name, rep / name)
    result = {'inputs': before, 'new_chembl_observations': len(new),
        'new_chembl_structures': len({r['full_key'] for r in new} - {r['full_key'] for r in old}),
        'combined_response_observations': len(observations),
        'combined_binary_observations': sum(r.get('label') not in {None, ''} for r in observations),
        'new_primary_coumarin_responses': len(curves), 'curves': len(summaries),
        'policy': 'New experimental products; no changes to canonical adopted labels. '
                  'ChEMBL complete series preserve unknowns; numerical percent inhibition requires '
                  'explicit source direction, scalar dose, exact qualifier and valid structure. '
                  'Coumarin source codes stay unmapped and synthetic. Context models use fold-local '
                  'imputation/scaling/encoding, chemical-frequency weights and protected holdouts.',
        'limits': 'Database assertions are not independent primary review. Numeric intermediates '
                  'are excluded only from binary fits. Context models remain heterogeneous; '
                  'study indicators are regularized offsets, not a fitted Bayesian hierarchy. '
                  'Curve fits use reported means, no replicate uncertainty; monotonicity may fail. '
                  'Omitted and not-conducted outcomes never become zero inhibition.',
        'products': {str(p.relative_to(output)): sha256(p) for p in output.rglob('*') if p.is_file()}}
    (output / 'manifest.json').write_text(json.dumps(result, indent = 2) + '\n')
    return {k: v for k, v in result.items() if k not in {'inputs', 'products'}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for name in ['sources', 'accepted', 'flavonoids', 'output']:
        parser.add_argument('--' + name, type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(run(args.sources, args.accepted, args.flavonoids, args.output), indent = 2))
