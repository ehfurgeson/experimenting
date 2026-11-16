"""Fixed separate A/B evaluation and agreement, never independent teacher validation."""
import argparse
import csv
import html
import importlib.metadata
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import altair as alt
import numpy as np
from scipy.stats import spearmanr
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from evidence_release import FEATURES, sha, write_csv
from oob import oob_permutation

SEED = 20261112


def read(path):
    with Path(path).open() as stream:
        return list(csv.DictReader(stream))


def merged_groups(rows):
    """Transitive union keeps both identical connectivity and scaffold together."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    for r in rows:
        a, b = find('C:' + r['connectivity']), find('S:' + r['scaffold'])
        parent[max(a, b)] = min(a, b)
    return np.array([find('C:' + r['connectivity']) for r in rows])


def regression_metrics(y, pred):
    rank = float(spearmanr(y, pred).statistic) if len(set(pred)) > 1 else None
    return {'mae_log10': float(mean_absolute_error(y, pred)),
            'rmse_log10': float(np.sqrt(np.mean((y - pred) ** 2))),
            'bias_log10': float(np.mean(pred - y)), 'spearman': rank}


def classification_metrics(y, pred, probabilities):
    precision, recall, f1, support = precision_recall_fscore_support(
        y, pred, labels = [0, 1, 2], zero_division = 0)
    result = {'macro_f1': float(f1_score(y, pred, labels = [0, 1, 2], average = 'macro',
                                       zero_division = 0)),
              'balanced_accuracy': float(balanced_accuracy_score(y, pred)),
              'confusion': confusion_matrix(y, pred, labels = [0, 1, 2]).tolist()}
    for c in range(3):
        result.update({f'class_{c}_precision': float(precision[c]),
                       f'class_{c}_recall': float(recall[c]), f'class_{c}_f1': float(f1[c]),
                       f'class_{c}_n': int(support[c]),
                       f'class_{c}_auroc': float(roc_auc_score(y == c, probabilities[:, c]))
                       if 0 < np.sum(y == c) < len(y) else None})
    return result


def evaluate(rows, pathway):
    x = np.array([[float(r[f]) for f in FEATURES] for r in rows])
    y = np.array([float(r['target_log10_mg_kg']) for r in rows])
    labels = np.array([int(r['ld50_bin']) for r in rows])
    if len({r['full_key'] for r in rows}) != len(rows) or not np.isfinite(x).all():
        raise ValueError('Require unique structures and finite features')
    groups = merged_groups(rows)
    if len(set(groups)) < 5:
        return {'status': [{'pathway': pathway, 'status': 'unsupported_fewer_than_five_groups'}],
                'metrics': [], 'predictions': [], 'splits': [], 'weights': [], 'oob': []}
    metrics, predictions, splits, weights, status = [], [], [], [], []
    for fold, (train, test) in enumerate(GroupKFold(5).split(x, labels, groups)):
        if set(groups[train]) & set(groups[test]):
            raise AssertionError('Group leakage')
        common = {'pathway': pathway, 'fold': fold, 'n_train': len(train), 'n_test': len(test),
                  'train_groups': len(set(groups[train])), 'test_groups': len(set(groups[test])),
                  'train_classes': json.dumps(dict(Counter(map(int, labels[train])))),
                  'test_classes': json.dumps(dict(Counter(map(int, labels[test]))))}
        status.append({**common, 'status': 'supported' if len(set(labels[train])) == 3 and
                       len(set(labels[test])) == 3 else 'classification_unsupported_class_support'})
        splits.extend({'pathway': pathway, 'fold': fold, 'role': role,
                       'full_key': rows[i]['full_key'], 'group': groups[i]}
                      for role, indices in [('train', train), ('test', test)] for i in indices)
        regressors = {
            'median': DummyRegressor(strategy = 'median'),
            'ridge': make_pipeline(StandardScaler(), Ridge(alpha = 1)),
            'forest': RandomForestRegressor(n_estimators = 200, min_samples_leaf = 5,
                                             max_features = 1.0, random_state = SEED, n_jobs = 2),
        }
        for name, model in regressors.items():
            model.fit(x[train], y[train])
            pred = model.predict(x[test])
            metrics.append({**common, 'task': 'regression', 'profile': name,
                            **regression_metrics(y[test], pred)})
            predictions.extend({'pathway': pathway, 'fold': fold, 'task': 'regression',
                                'profile': name, 'full_key': rows[i]['full_key'],
                                'observed': float(y[i]), 'predicted': float(p)}
                               for i, p in zip(test, pred, strict = True))
        if len(set(labels[train])) != 3 or len(set(labels[test])) != 3:
            continue
        classifiers = {
            'majority': DummyClassifier(strategy = 'most_frequent'),
            'logistic': make_pipeline(StandardScaler(), LogisticRegression(
                C = 1, class_weight = 'balanced', max_iter = 2000, random_state = SEED)),
            'forest': RandomForestClassifier(n_estimators = 200, min_samples_leaf = 5,
                                              max_features = 1.0, class_weight = 'balanced',
                                              random_state = SEED, n_jobs = 2),
        }
        for name, model in classifiers.items():
            model.fit(x[train], labels[train])
            pred, proba = model.predict(x[test]), model.predict_proba(x[test])
            metrics.append({**common, 'task': 'classification', 'profile': name,
                            **classification_metrics(labels[test], pred, proba)})
            predictions.extend({'pathway': pathway, 'fold': fold, 'task': 'classification',
                                'profile': name, 'full_key': rows[i]['full_key'],
                                'observed': int(labels[i]), 'predicted': int(p),
                                **{f'probability_{c}': float(prob[c]) for c in range(3)}}
                               for i, p, prob in zip(test, pred, proba, strict = True))
            if name == 'logistic':
                fitted = model[-1]
                for cls, coefs, intercept in zip(fitted.classes_, fitted.coef_, fitted.intercept_,
                                                  strict = True):
                    weights.extend({'pathway': pathway, 'fold': fold, 'class': int(cls),
                                    'feature': f, 'standardized_weight': float(v),
                                    'intercept': float(intercept)}
                                   for f, v in zip(FEATURES, coefs, strict = True))
        print(pathway, 'fold', fold, 'complete', flush = True)
    # Explicit binary low-LD50 versus remainder diagnostic supports the existing OOB API.
    # This whole-cohort diagnostic supplies no held-out performance claim.
    oob = []
    if len(set(labels == 0)) == 2:
        forest = RandomForestClassifier(n_estimators = 200, min_samples_leaf = 5,
                                        max_features = 1.0, class_weight = 'balanced',
                                        random_state = SEED, n_jobs = 2).fit(x, (labels == 0).astype(int))
        oob = [{'pathway': pathway, 'target': 'low_LD50_vs_rest', 'evaluation': 'whole_cohort_OOB',
                **r} for r in oob_permutation(forest, x, (labels == 0).astype(int), FEATURES,
                                              repeats = 3, seed = SEED)]
    else:
        status.append({'pathway': pathway, 'status': 'OOB_unsupported_binary_class_support'})
    return {'metrics': metrics, 'predictions': predictions, 'splits': splits, 'weights': weights,
            'status': status, 'oob': oob}


def paired_agreement(a, b):
    bykey = {r['full_key']: r for r in b}
    pairs = []
    for r in a:
        s = bykey.get(r['full_key'])
        if s:
            measured, predicted = float(r['target_log10_mg_kg']), float(s['target_log10_mg_kg'])
            pairs.append({'full_key': r['full_key'], 'A_log10_mg_kg': measured,
                          'B_log10_mg_kg': predicted, 'difference_B_minus_A': predicted - measured,
                          'A_bin': r['ld50_bin'], 'B_bin': s['ld50_bin'],
                          'training_membership': s['training_membership'],
                          'ad_conclusion': s['ad_conclusion'], 'independence':
                          'known_teacher_training_compound_overlap' if 'Tr' in
                          s['training_membership'].split(';') else
                          'provider_test_tag_independence_unverified' if 'Tst' in
                          s['training_membership'].split(';') else 'unknown_shared_lineage',
                          'A_source_record_ids': r['source_record_ids'],
                          'B_source_record_ids': s['source_record_ids']})
    summaries = []
    strata = {'all': pairs}
    for membership in sorted({r['training_membership'] for r in pairs}):
        strata['membership_' + membership] = [r for r in pairs if
                                              r['training_membership'] == membership]
    for name, rs in strata.items():
        if not rs:
            continue
        observed = np.array([r['A_log10_mg_kg'] for r in rs])
        predicted = np.array([r['B_log10_mg_kg'] for r in rs])
        summaries.append({'stratum': name, 'n': len(rs),
                          **regression_metrics(observed, predicted),
                          'same_bin_fraction': float(np.mean([r['A_bin'] == r['B_bin'] for r in rs])),
                          'interpretation': 'agreement_only_not_independent_validation'})
    return pairs, summaries


def svg(chart):
    import vl_convert as vlc
    return vlc.vegalite_to_svg(chart.to_dict())


def run(release, output):
    release, output = Path(release), Path(output)
    if output.exists() or output.resolve().is_relative_to(release.resolve()):
        raise ValueError('Choose a fresh evaluation directory outside the release')
    manifest = json.loads((release / 'manifest.json').read_text())
    for name, expected in manifest['outputs'].items():
        if sha(release / name) != expected:
            raise ValueError('Frozen release hash mismatch: ' + name)
    output.mkdir(parents = True)
    a, b = read(release / 'A_compounds.csv'), read(release / 'B_compounds.csv')
    result = [evaluate(a, 'A'), evaluate(b, 'B')]
    for product in ['metrics', 'predictions', 'splits', 'weights', 'status', 'oob']:
        write_csv(output / (product + '.csv'), [r for data in result for r in data[product]])
    pairs, agreement = paired_agreement(a, b)
    write_csv(output / 'paired_agreement.csv', pairs)
    write_csv(output / 'agreement_summary.csv', agreement)
    pooled = []
    for data in result:
        strata = defaultdict(list)
        for r in data['predictions']:
            strata[(r['pathway'], r['task'], r['profile'])].append(r)
        for (pathway, task, profile), rs in strata.items():
            y = np.array([r['observed'] for r in rs])
            pred = np.array([r['predicted'] for r in rs])
            m = regression_metrics(y, pred) if task == 'regression' else classification_metrics(
                y, pred, np.array([[r[f'probability_{c}'] for c in range(3)] for r in rs]))
            pooled.append({'pathway': pathway, 'task': task, 'profile': profile, 'n': len(rs), **m})
    write_csv(output / 'pooled_metrics.csv', pooled)
    coverage = json.loads((release / 'coverage.json').read_text())
    runtime = {name: importlib.metadata.version(name) for name in
               ['numpy', 'scipy', 'scikit-learn', 'polars', 'rdkit', 'altair', 'vl-convert-python']}
    (output / 'runtime.json').write_text(json.dumps(runtime, indent = 2) + '\n')
    decision = {
        'C': 'defer', 'reason': 'Shared teacher/experimental lineage and incomplete original-study '
        'context prevent an independent untouched experimental test set. No combined fit run.',
        'completed': ['Separate frozen A/B cohorts', 'Five scaffold/connectivity grouped outer folds',
                      'Fixed regression/classification profiles and baselines',
                      'Standardized logistic weights', 'Binary low-LD50 OOB diagnostic',
                      'Paired full-key agreement with teacher-membership strata'],
        'provisional': ['Provider structures, tested-form and dose-context interpretation',
                        'A source aggregation and incomplete primary-study deduplication',
                        'All model results are AI experimental'],
        'unsupported': ['Both-X-and-y measured features', 'Independent teacher validation',
                        'Publication/provider held-out validation', 'Calibrated prediction intervals',
                        'Plant-activity external model'],
        'planned': ['Audit original studies and tested chemical forms',
                    'Qualify new TEST/VEGA/GenRA/Toolbox inference routes',
                    'Recover remaining primary plant/aquatic series',
                    'Revisit C only after original-study and teacher-overlap audits'],
    }
    (output / 'decision_C.json').write_text(json.dumps(decision, indent = 2) + '\n')
    # Scientific figures use standard Vega-Lite plots; deterministic subsample is labeled.
    rng = np.random.default_rng(SEED)
    plotted = [pairs[i] for i in sorted(rng.choice(len(pairs), min(1000, len(pairs)), replace = False))]
    scatter = alt.Chart(alt.Data(values = plotted)).mark_circle(size = 14, opacity = .3).encode(
        x = alt.X('A_log10_mg_kg:Q', title = 'Measured A: log10(mg/kg)'),
        y = alt.Y('B_log10_mg_kg:Q', title = 'CATMoS B: log10(mg/kg)'),
        color = 'training_membership:N').properties(width = 620, height = 350,
                                                   title = 'Agreement only: up to 1,000 paired structures')
    scatter_svg = svg(scatter)
    (output / 'paired_agreement.svg').write_text(scatter_svg)
    residuals = []
    for data in result:
        for profile in ('median', 'ridge', 'forest'):
            rs = [r for r in data['predictions'] if r['task'] == 'regression' and
                  r['profile'] == profile]
            if not rs:
                continue
            hist, edges = np.histogram([r['predicted'] - r['observed'] for r in rs],
                                        bins = np.linspace(-6, 6, 49))
            residuals.extend({'pathway': rs[0]['pathway'], 'profile': profile,
                              'left': float(edges[i]), 'right': float(edges[i + 1]),
                              'count': int(n)} for i, n in enumerate(hist))
    write_csv(output / 'residual_histogram.csv', residuals)
    residual_svg = svg(alt.Chart(alt.Data(values = residuals)).mark_bar(opacity = .5).encode(
        x = alt.X('left:Q', title = 'Held-out prediction minus target: log10 dose',
                  scale = alt.Scale(domain = [-6, 6])), x2 = 'right:Q', y = 'count:Q',
        color = 'profile:N', row = 'pathway:N').properties(width = 620, height = 150))
    (output / 'residuals.svg').write_text(residual_svg)
    metric_rows = ''.join('<tr>' + ''.join('<td>' + html.escape(str(r.get(k, ''))) + '</td>'
                                         for k in ['pathway', 'task', 'profile', 'n', 'mae_log10',
                                                   'macro_f1']) + '</tr>' for r in pooled)
    report = f'''<!doctype html><html><meta charset="utf-8"><title>Separate evidence release</title>
    <style>body{{font:17px system-ui;max-width:1000px;margin:40px auto;color:#203239}}
    td,th{{text-align:left;padding:9px;border-bottom:1px solid #ddd}}svg{{max-width:100%}}
    code{{background:#eee}} h1,h2{{color:#174b47}}</style>
    <h1>Experimental outcomes and outside-model estimates</h1>
    <p>AI experimental release · 12 November 2026. These datasets do not establish safety,
    plant efficacy or a validated biological activity model.</p>
    <h2>Completed</h2><p>A: {len(a):,} full structures with provisional exact experimental
    compound medians. B: {len(b):,} full structures with eligible, Inside-domain stored CATMoS
    estimates. {len(pairs):,} exact-key pairs. Original TEST cache: {coverage['TEST_compounds']}
    compounds; {coverage['TEST_records']:,} rows. No new TEST inference was run.</p>
    <p>Both pathways use seven structure-derived features. A targets experiments and B targets
    a teacher estimate. Five scaffold/connectivity groups hold chemicals apart. Repeated
    source records do not become independent samples. Lower LD50 means greater acute hazard.</p>
    <table><tr><th>Pathway</th><th>Task</th><th>Profile</th><th>Held-out n</th>
    <th>MAE log10</th><th>Macro-F1</th></tr>{metric_rows}</table>
    <p>Classification uses fixed historical 1,080/3,400 mg/kg cohort cutoffs, not regulatory
    categories. One log10 dose error means a tenfold dose difference. Baselines are included.
    Per-fold support, confusion counts, per-class scores/AUROC and membership are CSV outputs.</p>
    <h2>Provisional agreement</h2>{scatter_svg}<pre>{html.escape(json.dumps(agreement, indent=2))}</pre>
    <p>These comparisons have shared NICEATM/ChemIDplus/TEST lineage. Source training/test tags
    do not prove independence for this archive version. Actual tested-form, original study,
    exposure and purity need further review. No embedded teacher measurements were added to A.</p>
    <h2>Held-out residuals</h2>{residual_svg}<p>Histogram shows residuals from −6 to +6 log units.
    Full unbinned predictions retain every residual. No calibrated intervals were fitted.</p>
    <h2>Decision: defer C</h2><p>{html.escape(decision['reason'])}</p>
    <p>Standardized logistic weights describe associations. OOB permutations are a separate
    binary low-LD50-versus-rest, whole-cohort diagnostic, with three repeats. Their SD measures
    stability, not significance, and OOB does not hold scaffolds out.</p>
    <h2>Planned and unsupported</h2><p>{html.escape('; '.join(decision['unsupported']))}.</p>
    <p>{html.escape('; '.join(decision['planned']))}.</p></html>'''
    (output / 'walkthrough.html').write_text(report)
    (output / 'reproduction').mkdir()
    for path in [Path(__file__), Path(__file__).parent / 'oob.py',
                 Path(__file__).parent / 'evidence_release.py']:
        shutil.copyfile(path, output / 'reproduction' / path.name)
    frozen = {'release_manifest_sha256': sha(release / 'manifest.json'),
              'protocol_sha256': manifest['protocol_sha256'], 'runtime': runtime,
              'code': {str(p): sha(p) for p in [Path(__file__), Path(__file__).parent / 'oob.py',
                                                Path(__file__).parent / 'evidence_release.py']},
              'outputs': {str(p.relative_to(output)): sha(p) for p in sorted(output.rglob('*'))
                          if p.is_file()}, 'decision_C': 'defer'}
    (output / 'manifest.json').write_text(json.dumps(frozen, indent = 2) + '\n')
    return pooled, agreement


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--release', type = Path, required = True)
    parser.add_argument('--output', type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(run(args.release, args.output), indent = 2))
