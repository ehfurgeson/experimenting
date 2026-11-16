"""Measure actual input imputation and controlled no-imputation comparisons."""
import hashlib
import json
import random
import sys
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from sklearn.model_selection import StratifiedGroupKFold

BASE = Path.cwd()
sys.path.insert(0, str(BASE / 'analysis'))
import classifiers
import stats
import structure_models as sm
from formula import FORMULA_FEATURES
from structure import DESCRIPTORS

SOURCE = BASE / 'analysis/outputs/structure-2026-10-28-stress-baseline/structural_features.parquet'
TRAITS = BASE / 'analysis/data/compound_traits.parquet'
OUT = BASE / 'analysis/outputs/imputation-audit-2026-10-29'
if OUT.exists(): raise FileExistsError(OUT)
rows = pl.read_parquet(SOURCE).to_dicts()
original_factory = sm.make_estimator

def no_imputation():
    estimator = original_factory()
    estimator.set_params(impute='passthrough')
    return estimator

def no_imputation_evaluate(records, representation):
    sm.make_estimator = no_imputation
    try:
        return sm.evaluate(records, 'selection_target', representation)
    finally:
        sm.make_estimator = original_factory

structural = []
for representation in sm.REPRESENTATIONS:
    current = sm.evaluate(rows, 'selection_target', representation)
    training = current['training']
    x = sm.feature_matrix(training, representation)
    missing = ~np.isfinite(x)
    complete = [r for i, r in enumerate(training) if not missing[i].any()]
    matched_imputed = current if len(complete) == len(training) else sm.evaluate(complete, 'selection_target', representation)
    matched_plain = no_imputation_evaluate(complete, representation)
    assert [{k:v for k,v in r.items() if k!='probability'} for r in matched_imputed['oof']] == [{k:v for k,v in r.items() if k!='probability'} for r in matched_plain['oof']]
    probability_changes = [abs(a['probability']-b['probability']) for a,b in zip(matched_imputed['oof'],matched_plain['oof'],strict=True)]
    class_changes = sum((a['probability']>=.5)!=(b['probability']>=.5) for a,b in zip(matched_imputed['oof'],matched_plain['oof'],strict=True))
    y = np.array([r['selection_target'] for r in training])
    groups = np.array([r['scaffold'] for r in training])
    splits = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=sm.SEED).split(x, y, groups)
    fold_counts = [{'fold':f, 'train_imputed_cells':int(missing[tr].sum()),
                    'test_imputed_cells':int(missing[te].sum())}
                   for f, (tr, te) in enumerate(splits)]
    columns = []
    if representation in {'formula','combined'}: columns += FORMULA_FEATURES
    if representation in {'descriptors','combined'}: columns += DESCRIPTORS
    if representation in {'morgan','combined'}: columns += [f'morgan_{i}' for i in range(2048)]
    item = {
        'representation':representation, 'n':len(training), 'feature_count':x.shape[1],
        'input_cells':int(x.size), 'missing_cells':int(missing.sum()),
        'affected_compounds':[{key:r.get(key) for key in ('compound_id','query','derived_formula','formula_status')}
                              for i,r in enumerate(training) if missing[i].any()],
        'missing_by_feature':{key:int(missing[:,j].sum()) for j,key in enumerate(columns) if missing[:,j].any()},
        'fold_counts':fold_counts, 'current_report':current['report'],
        'complete_case_n':len(complete), 'complete_case_median_report':matched_imputed['report'],
        'complete_case_no_imputation_report':matched_plain['report'],
        'matched_oof_predictions_exactly_identical':matched_imputed['oof']==matched_plain['oof'],
        'matched_max_probability_change':max(probability_changes,default=0),
        'matched_predicted_classes_changed':int(class_changes),
    }
    if missing.any():
        try: no_imputation_evaluate(training, representation)
        except ValueError as error:
            item['strict_no_imputation_full_data_error'] = str(error).split('\n')[0]
        else: raise AssertionError('Missing input unexpectedly accepted by PCA')
    structural.append(item)
    print(representation,'n=',len(training),'missing=',int(missing.sum()),
          'current BA=',current['report']['balanced_accuracy'],
          'complete/no-imputation BA=',matched_plain['report']['balanced_accuracy'],flush=True)

# Controlled comparison on the same common cohort used in the earlier report.
common = [r for r in rows if sm.eligible(r, 'formula') and r.get('selection_target') is not None]
common_reports = []
for representation in sm.REPRESENTATIONS:
    with_imputer = sm.evaluate(common, 'selection_target', representation)
    without_imputer = no_imputation_evaluate(common, representation)
    assert with_imputer['report'] == without_imputer['report']
    assert with_imputer['oof'] == without_imputer['oof']
    common_reports.append({'representation':representation, 'n':len(common),
                           'with_imputer':with_imputer['report'],
                           'without_imputer':without_imputer['report'],
                           'oof_exactly_identical':True})

# Older notebook model: reproduce its exact folds before comparing alternatives.
frame = pl.read_parquet(TRAITS)
features = classifiers.FEATURES
old_rows = classifiers.rows_for(frame, features, lambda r:1 if r['chemical_group']=='herbicide' else 0)
x = np.array([[r[k] for k in features] for r in old_rows],dtype=float)
missing = ~np.isfinite(x)
positives=[i for i,r in enumerate(old_rows) if r['target']==1]
negatives=[i for i,r in enumerate(old_rows) if r['target']==0]
rng=random.Random(20261021);rng.shuffle(positives);rng.shuffle(negatives)
buckets=[[] for _ in range(5)]
for group in (positives,negatives):
    for index,i in enumerate(group):buckets[index%5].append(i)
predictions=[]
for f,test in enumerate(buckets):
    train=[i for j,b in enumerate(buckets) if j!=f for i in b]
    filled,medians=stats.impute([old_rows[i] for i in train],features)
    held,_=stats.impute([old_rows[i] for i in test],features,medians)
    scaled,parameters=stats.standardize(filled,features)
    held_scaled,_=stats.standardize(held,features,parameters=parameters)
    weights,bias=stats.logistic_regression(scaled,features,'target')
    complete_train=[old_rows[i] for i in train if not missing[i].any()]
    complete_test=[i for i in test if not missing[i].any()]
    clean_scaled,clean_parameters=stats.standardize(complete_train,features)
    clean_held,_=stats.standardize([old_rows[i] for i in complete_test],features,parameters=clean_parameters)
    clean_weights,clean_bias=stats.logistic_regression(clean_scaled,features,'target')
    clean_prediction={i:int(stats.predict(clean_weights,clean_bias,r,features)>=.5)
                      for i,r in zip(complete_test,clean_held,strict=True)}
    for i,r in zip(test,held_scaled,strict=True):
        predictions.append({'i':i,'fold':f,'label':old_rows[i]['target'],
                            'missing':bool(missing[i].any()),
                            'median_prediction':int(stats.predict(weights,bias,r,features)>=.5),
                            'complete_training_prediction':clean_prediction.get(i)})
original_accuracy=accuracy_score([r['label'] for r in predictions],[r['median_prediction'] for r in predictions])
assert original_accuracy == stats.cross_validated_accuracy(old_rows,features,'target')
shared=[r for r in predictions if not r['missing']]
by_compound=frame.to_dicts()
older={
    'n':len(old_rows), 'feature_count':len(features), 'input_cells':int(x.size),
    'missing_cells':int(missing.sum()),
    'missing_by_feature':{k:int(missing[:,j].sum()) for j,k in enumerate(features) if missing[:,j].any()},
    'affected_compounds':[{key:r.get(key) for key in ('compound_id','query','chemical_group')}
                          for i,r in enumerate(by_compound) if missing[i].any()],
    'original_median_imputed_accuracy_n176':float(original_accuracy),
    'matched_test_n':len(shared),
    'median_training_matched_test_accuracy':float(accuracy_score([r['label'] for r in shared],[r['median_prediction'] for r in shared])),
    'complete_training_matched_test_accuracy':float(accuracy_score([r['label'] for r in shared],[r['complete_training_prediction'] for r in shared])),
    'changed_predictions_on_matched_test':sum(r['median_prediction']!=r['complete_training_prediction'] for r in shared),
    'complete_case_refolded_accuracy_n174':stats.cross_validated_accuracy([r for i,r in enumerate(old_rows) if not missing[i].any()],features,'target'),
    'drop_xlogp_accuracy_n176':stats.cross_validated_accuracy(old_rows,[k for k in features if k!='xlogp'],'target'),
    'note':'The matched comparison preserves original folds/test compounds but removes incomplete training rows; it changes training data and is not an isolated imputer intervention.',
}
print('older notebook:',json.dumps(older),flush=True)
OUT.mkdir(parents=True)
result={'scope':'Diagnostic only; source models and data unchanged; selection target, not herbicidal activity.',
        'structural':structural,'older_notebook':older,'controlled_common_cohort':common_reports,
        'input_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (SOURCE,TRAITS)},
        'code_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [BASE/'analysis/structure_models.py',BASE/'analysis/stats.py',BASE/'analysis/classifiers.py',Path(__file__)]}}
(OUT/'audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print('Saved',OUT/'audit.json',flush=True)
