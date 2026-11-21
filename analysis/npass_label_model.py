"""Trace NPASS LD50 provenance and test conservative source-linked augmentation."""

import argparse
import json
from collections import Counter, defaultdict
from math import log10
from pathlib import Path
from statistics import median

import numpy as np

from accepted_uncertainty import paired_intervals
from data_sprint import read_csv, sha256
from evidence_models import classification_metrics, merged_groups, toxicity_forest
from evidence_release import FEATURES, ld50_bin, number, structure, write_csv
from expansion_toxicity import compatible_bins
from sprint_report import compressed_rows, verify_bundle

UNIT_SCALE = {'mg/kg': 1, 'mg.kg-1': 1, 'g/Kg': 1000}


def source_links(npass, epa, measured):
    related, exact = defaultdict(list), defaultdict(set)
    for row in epa:
        key = row['full_inchikey']
        if not key or key in measured:
            continue
        dose = float(row['value'])
        related[key, dose, row['qualifier']].append(row)
        if row['status'] == 'endpoint_eligible_exact':
            exact[key].add(dose)
    leads, matches = [], []
    for row in npass:
        if row['endpoint'] != 'LD50' or row['test_species'] != 'Rattus norvegicus':
            continue
        key = row['full_inchikey']
        if not key or key in measured:
            continue
        scale, dose = UNIT_SCALE.get(row['unit']), number(row['value'])
        if scale is None or dose is None or dose <= 0 or row['qualifier'] not in {'=', '>', '>=', '<', '<='}:
            continue
        dose *= scale
        hit = related.get((key, dose, row['qualifier']), [])
        leads.append({**row, 'normalized_mg_kg': dose, 'epa_matches': len(hit)})
        matches.extend({
            'full_key': key, 'dose_mg_kg': dose, 'qualifier': row['qualifier'],
            'npass_record': row['source_record_id'], 'npass_citation': row['citation'],
            'epa_record': e['source_record_id'], 'epa_name': e['source_chemical_name'],
            'epa_table': e['source_table'], 'epa_status': e['status'], 'epa_study': e['source_study_id'],
            'epa_reference': e['citation'], 'epa_url': e['source_url'],
            'epa_tested_form_field': e['tested_form'],
        } for e in hit)
    return leads, matches, exact


def build_labels(matches, exact, identities, reviews):
    by_key = defaultdict(set)
    for row in matches:
        if row['epa_status'] == 'endpoint_eligible_exact' and row['npass_citation'] == 'Database:ToxVal':
            by_key[row['full_key']].add(row['dose_mg_kg'])
    pending = set(by_key)
    smiles = {}
    for row in identities:
        key = row['full_inchikey']
        if key in pending and row['identity_status'] == 'valid':
            smiles.setdefault(key, row['original_structure'])
    labels, decisions = [], []
    for key, doses in sorted(by_key.items()):
        source = reviews.get(key)
        identity = structure(smiles.get(key))
        bins = {ld50_bin(log10(dose)) for dose in exact[key]}
        point = median(doses)
        disposition = 'epa_linked_sensitivity'
        if identity.get('full_key') != key or identity['identity_status'] != 'valid':
            disposition = 'identity_hold'
        elif source and source['decision'] == 'hold':
            disposition = 'manual_source_hold'
        elif len(bins) != 1:
            disposition = 'epa_points_cross_bin'
        elif source and source['decision'] == 'endpoint_confirmed':
            point = float(source['dose_mg_kg'])
            if point not in doses:
                raise ValueError(f'Reviewed endpoint does not match source records: {key}')
            disposition = 'endpoint_confirmed'
        decisions.append({'full_key': key, 'matched_exact_doses': ';'.join(map(str, sorted(doses))),
                          'epa_exact_bins': ';'.join(map(str, sorted(bins))), 'disposition': disposition})
        if disposition in {'endpoint_confirmed', 'epa_linked_sensitivity'}:
            labels.append({**identity, 'ld50_bin': ld50_bin(log10(point)),
                           'dose_mg_kg': point, 'disposition': disposition})
    return labels, decisions


def trusted_labels(leads, identities):
    records = defaultdict(set)
    for row in leads:
        records[row['full_inchikey']].add((row['normalized_mg_kg'], row['qualifier']))
    smiles = {r['full_inchikey']: r['original_structure'] for r in identities
              if r['full_inchikey'] in records and r['identity_status'] == 'valid'}
    labels, decisions = [], []
    names = {'low': 0, 'medium': 1, 'high': 2}
    for key, observations in sorted(records.items()):
        identity = structure(smiles.get(key))
        exact = sorted(dose for dose, qualifier in observations if qualifier == '=')
        bounds = sorted((dose, qualifier) for dose, qualifier in observations if qualifier != '=')
        admissible = set(names)
        for dose, qualifier in bounds:
            admissible.intersection_update(compatible_bins(dose, qualifier))
        log_dose = median(map(log10, exact)) if exact else None
        dose = 10 ** log_dose if log_dose is not None else None
        bucket = (ld50_bin(log_dose) if log_dose is not None else
                  names[next(iter(admissible))] if len(admissible) == 1 else None)
        if identity.get('full_key') != key or identity['identity_status'] != 'valid':
            disposition = 'identity_hold'
        elif exact:
            disposition = 'trusted_exact'
        elif bucket is not None:
            disposition = 'trusted_single_bin_bounds'
        else:
            disposition = 'ambiguous_or_conflicting_bounds'
        details = {'full_key': key, 'disposition': disposition, 'distinct_exact_points': len(exact),
                   'distinct_bounds': len(bounds), 'exact_points_cross_bins':
                   len({ld50_bin(log10(value)) for value in exact}) > 1,
                   'bounds_compatible_with_assigned_bin': not bounds or bucket is None or
                   bucket in {names[name] for name in admissible}, 'ld50_bin': bucket, 'dose_mg_kg': dose}
        decisions.append(details)
        if disposition.startswith('trusted_'):
            labels.append({**identity, **details})
    return labels, decisions


def evaluate(measured, folds, additions, trust_provider=False):
    rows = [*measured, *additions]
    x = np.array([[float(row[f]) for f in FEATURES] for row in rows])
    y = np.array([int(row['ld50_bin']) for row in rows])
    n = len(measured)
    keys = [row['full_key'] for row in rows]
    if len(set(keys)) != len(keys) or set(keys[:n]) != folds.keys() or not np.isfinite(x).all():
        raise ValueError('Duplicate structures, missing split membership or invalid features')
    assignment = np.array([int(folds[key]['fold']) for key in keys[:n]])
    baseline_groups = np.array([folds[key]['group'] for key in keys[:n]])
    joint_groups = merged_groups(rows)
    subgroup, exact_profile, all_profile = (
        ('trusted_exact', 'trusted_npass_exact', 'trusted_npass_exact_and_bounds') if trust_provider else
        ('endpoint_confirmed', 'source_checked_additions', 'all_source_linked_additions'))
    narrow_subset = np.array([r.get('disposition') == subgroup for r in rows])
    names = ('structure', exact_profile, all_profile)
    held = {name: np.full((n, 3), np.nan) for name in names}
    training = []
    for fold in sorted(set(assignment)):
        test = np.flatnonzero(assignment == fold)
        baseline = np.flatnonzero(assignment != fold)
        if set(baseline_groups[test]) & set(baseline_groups[baseline]):
            raise ValueError('Original split contains group leakage')
        allowed = (np.arange(len(rows)) >= n) & ~np.isin(joint_groups, joint_groups[test])
        for name, extra in zip(names, ([], np.flatnonzero(allowed & narrow_subset), np.flatnonzero(allowed)),
                               strict=True):
            train = np.concatenate((baseline, np.asarray(extra, dtype=int)))
            model = toxicity_forest().fit(x[train], y[train])
            held[name][test] = model.predict_proba(x[test])
            training.append({'fold': int(fold), 'profile': name, 'train_measured': len(baseline),
                             'train_additions': len(extra), 'test_measured': len(test)})
        print(f'NPASS fold {fold}: {int(allowed.sum())} eligible additions', flush=True)
    if any(not np.isfinite(prob).all() for prob in held.values()):
        raise ValueError('Incomplete paired predictions')
    preds = {name: prob.argmax(axis=1) for name, prob in held.items()}
    metrics = [{'profile': name, 'structures': n,
                **classification_metrics(y[:n], preds[name], held[name])} for name in names]
    intervals = [{'profile': name, **row} for name in names[1:] for row in paired_intervals(
        y[:n], preds['structure'], preds[name], baseline_groups, 'classification')]
    predictions = [{'full_key': key, 'fold': int(assignment[i]), 'profile': name,
                    'observed': int(y[i]), 'predicted': int(preds[name][i]),
                    **{f'probability_{c}': float(held[name][i, c]) for c in (0, 1, 2)}}
                   for i, key in enumerate(keys[:n]) for name in names]
    return {'metrics.csv': metrics, 'paired_intervals.csv': intervals,
            'held_out_predictions.csv': predictions, 'training_support.csv': training}


def run(release, models, npass, toxval, review, output, trust_provider=False):
    release, models, npass, output = map(Path, (release, models, npass, output))
    toxval = list(map(Path, toxval))
    if not trust_provider and (review is None or not toxval):
        raise ValueError('The source-linked experiment requires the review ledger and ToxVal inputs')
    for bundle in (release, npass, *toxval):
        verify_bundle(bundle)
    metadata = json.loads((models / 'manifest.json').read_text())
    split_path = models / 'splits.csv'
    if (metadata['release_manifest_sha256'] != sha256(release / 'manifest.json')
            or metadata['outputs']['splits.csv'] != sha256(split_path)):
        raise ValueError('Model splits do not match release')
    folds = {row['full_key']: row for row in read_csv(split_path)
             if row['pathway'] == 'A' and row['role'] == 'test'}
    measured = read_csv(release / 'A_compounds.csv')
    leads, matches, exact = source_links(
        compressed_rows(npass / 'npass_toxicity_all.csv.gz'),
        (row for folder in toxval for row in compressed_rows(folder / 'toxval_candidate_rat_oral.csv.gz')),
        {r['full_key'] for r in measured})
    identities = compressed_rows(npass / 'npass_identity.csv.gz')
    if trust_provider:
        additions, decisions = trusted_labels(leads, identities)
    else:
        review = Path(review)
        reviews = {row['full_key']: row for row in read_csv(review)}
        additions, decisions = build_labels(matches, exact, identities, reviews)
    results = evaluate(measured, folds, additions, trust_provider)
    products = {**results, 'npass_leads.csv': leads,
                'label_decisions.csv': decisions, 'candidate_labels.csv': additions}
    if toxval:
        products['epa_links.csv'] = matches
    output.mkdir(parents=True, exist_ok=False)
    for name, rows in products.items():
        write_csv(output / name, rows)
    inputs = [split_path, *(p / 'manifest.json' for p in (release, models, npass, *toxval))]
    if not trust_provider:
        inputs.append(review)
    summary = {'inputs': {str(p): sha256(p) for p in inputs},
               'products': {name: sha256(output / name) for name in products},
               'decisions': dict(Counter(row['disposition'] for row in decisions)),
               'lead_records': len(leads), 'lead_structures': len({r['full_inchikey'] for r in leads}),
               'linked_records': len({r['npass_record'] for r in matches}),
               'linked_structures': len({r['full_key'] for r in matches}),
               'label_policy': ('Assume missing NPASS rat LD50 route, acute context and experimental '
                                'status are compatible with the ICE target.' if trust_provider else
                                'Require endpoint-eligible EPA links for the sensitivity cohort.')}
    (output / 'manifest.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('release', 'models', 'npass', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--review', type=Path)
    parser.add_argument('--toxval', type=Path, action='append', default=[])
    parser.add_argument('--trust-provider', action='store_true')
    print(json.dumps(run(**vars(parser.parse_args())), indent=2))
