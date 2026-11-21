"""Continuous, assay-specific pilots with every dose of a chemical held out jointly."""

import argparse
import json
import shutil
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import f1_score, mean_absolute_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from data_sprint import read_csv, sha256, write_csv
from evidence_models import merged_groups
from evidence_release import FEATURES, structure
from plant_evidence_experiments import inhibition_label


def assay_forest():
    return RandomForestRegressor(n_estimators=200, min_samples_leaf=5, random_state=20261117, n_jobs=2)


def cluster_mae_interval(y, baseline, proposed, groups, repeats = 2000):
    groups, inverse = np.unique(groups, return_inverse = True)
    counts = np.bincount(inverse)
    delta = np.bincount(inverse, weights = abs(y - proposed) - abs(y - baseline))
    rng = np.random.default_rng(20261117)
    draws = []
    for _ in range(repeats):
        w = rng.multinomial(len(groups), np.full(len(groups), 1 / len(groups)))
        draws.append(float((w @ delta) / (w @ counts)))
    return {'mae_difference': float(delta.sum() / counts.sum()),
            'conditional_lower95': float(np.quantile(draws, .025)),
            'conditional_upper95': float(np.quantile(draws, .975)),
            'chemical_clusters': len(groups), 'draws': repeats}


def run(flavonoids, output):
    flavonoids, output = Path(flavonoids), Path(output)
    paths = [flavonoids / 'transcription-v1/observations.csv', flavonoids / 'analysis-v2/compounds.csv']
    before = {str(p): sha256(p) for p in paths}
    identities = {r['compound_id']: structure(r['smiles']) for r in read_csv(paths[1])}
    panels = defaultdict(list)
    for r in read_csv(paths[0]):
        parsed = identities[r['compound_id']]
        if parsed['identity_status'] != 'valid':
            raise ValueError('Unresolved assay structure')
        panels[r['species'], r['endpoint']].append({**r, **parsed})
    predictions, results, intervals, split_rows = [], [], [], []
    for (species, endpoint), rows in panels.items():
        y = np.array([float(r['derived_inhibition_percent']) for r in rows])
        x = np.array([[float(r[f]) for f in FEATURES] + [np.log10(float(r['concentration_uM']))] for r in rows])
        for protocol in ['full_structure', 'chemical_group']:
            groups = np.array([r['full_key'] for r in rows]) if protocol == 'full_structure' else merged_groups(rows)
            if len(set(groups)) < 5:
                raise ValueError('Insufficient assay groups; do not weaken split silently')
            profiles = ['median', 'dose_only_ridge', 'chemistry_dose_ridge', 'chemistry_dose_forest']
            pred = {p: np.full(len(rows), np.nan) for p in profiles}
            for fold, (train, test) in enumerate(GroupKFold(5).split(x, y, groups)):
                if set(groups[train]) & set(groups[test]):
                    raise ValueError('Chemical leakage across doses')
                models = {'median': DummyRegressor(strategy = 'median'),
                    'dose_only_ridge': make_pipeline(StandardScaler(), Ridge(alpha = 1)),
                    'chemistry_dose_ridge': make_pipeline(StandardScaler(), Ridge(alpha = 10)),
                          'chemistry_dose_forest': assay_forest()}
                split_rows.extend({'species': species, 'endpoint': endpoint, 'protocol': protocol,
                    'fold': fold, 'observation_id': rows[i]['observation_id'], 'full_key': rows[i]['full_key'],
                    'group': str(groups[i]), 'role': role} for role, indices in [('train', train), ('test', test)] for i in indices)
                for profile, model in models.items():
                    matrix = x[:, -1:] if profile == 'dose_only_ridge' else x
                    model.fit(matrix[train], y[train])
                    p = model.predict(matrix[test])
                    pred[profile][test] = p
                    predictions.extend({'species': species, 'endpoint': endpoint, 'protocol': protocol,
                        'fold': fold, 'profile': profile, 'observation_id': rows[i]['observation_id'],
                        'full_key': rows[i]['full_key'], 'dose_uM': rows[i]['concentration_uM'],
                        'observed': y[i], 'predicted': value} for i, value in zip(test, p, strict = True))
            known = np.array([inhibition_label(value) is not None for value in y])
            labels = np.array([inhibition_label(value) or 0 for value in y])[known]
            for profile, p in pred.items():
                if not np.isfinite(p).all():
                    raise ValueError('Incomplete assay evaluation')
                results.append({'species': species, 'endpoint': endpoint, 'protocol': protocol,
                    'profile': profile, 'observations': len(rows), 'structures': len({r['full_key'] for r in rows}),
                    'mae_percentage_points': float(mean_absolute_error(y, p)),
                    'threshold_macro_f1': float(f1_score(labels, p[known] >= 40,
                        labels = [0, 1], average = 'macro', zero_division = 0)),
                    'threshold_high_support': int(labels.sum()), 'threshold_low_support': int((labels == 0).sum()),
                    'limits': 'one_publication_same_protocol_new_chemistry; regression_uses_all_intermediate_responses'})
                if profile != 'median':
                    intervals.append({'species': species, 'endpoint': endpoint, 'protocol': protocol,
                        'profile': profile, **cluster_mae_interval(y, pred['median'], p, groups)})
        print('Assay panel', species, endpoint, 'complete', flush = True)
    output.mkdir(parents = True, exist_ok = False)
    for name, data in [('predictions', predictions), ('metrics', results), ('intervals', intervals), ('split_membership', split_rows)]:
        write_csv(output / f'{name}.csv', data, list(data[0]))
    shutil.copyfile(__file__, output / Path(__file__).name)
    if before != {p: sha256(p) for p in before}:
        raise ValueError('Assay input changed')
    manifest = {'inputs': before, 'panels': len(panels), 'observations': sum(map(len, panels.values())),
        'policy': 'Four independent species/endpoint panels; 120h;1/10/100uM. Fixed profiles, '
                  'no tuning. Hold every dose of a chemical together, plus scaffold/connectivity sensitivity. '
                  'No prediction clipping. Macro-F1 is secondary on true <=20/>=40 bands; intermediates '
                  'remain in continuous regression. A >=40 prediction is called high; otherwise low.',
        'limits': 'Retrospective single-publication AI-mapped identities and ratios of rounded means; '
                  'no new-study transfer, biological replication expansion, natural-origin or safety claim. '
                  'Cluster intervals condition on fixed predictions, without refitting or multiplicity correction.',
        'products': {str(p.relative_to(output)): sha256(p) for p in output.rglob('*') if p.is_file()}}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--flavonoids', type = Path, required = True)
    parser.add_argument('--output', type = Path, required = True)
    args = parser.parse_args()
    run(args.flavonoids, args.output)
