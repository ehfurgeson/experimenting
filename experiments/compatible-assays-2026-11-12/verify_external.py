import csv,hashlib,json,math,sys
from pathlib import Path
import numpy as np
from sklearn.metrics import f1_score,precision_score,recall_score,balanced_accuracy_score,roc_auc_score,confusion_matrix
sys.path.insert(0,'analysis')
from screen import read_records
root=Path(__file__).parent
out=Path('analysis/outputs/experimental-flavonoid-transfer-2026-11-12')
reports=list(csv.DictReader((out/'reports.csv').open()));predictions=list(csv.DictReader((out/'predictions.csv').open()));members=list(csv.DictReader((out/'membership.csv').open()))
assert len(reports)==24 and len(predictions)==558
old=read_records(Path('analysis/outputs/experimental-heterogeneous-activity-2026-11-12/structural_features.parquet'))
rows=read_records(root/'external-inputs-v1/features.parquet');byid={r['compound_id']:r for r in rows}
assert len(rows)==100 and sum(r['activity_target'] is not None for r in rows)==93
for r in old:
 for k,v in r.items():
  if k!='activity_policy':assert byid[r['compound_id']][k]==v,(r['compound_id'],k)
checks=0
for report in reports:
 p=[r for r in predictions if all(r[k]==report[k] for k in ['publication','scenario','profile'])]
 y=np.array([int(r['label']) for r in p]);pr=np.array([float(r['probability']) for r in p]);pred=pr>=.5;base=np.array([int(r['baseline_prediction']) for r in p])
 metrics=dict(f1=f1_score(y,pred,zero_division=0),precision=precision_score(y,pred,zero_division=0),recall=recall_score(y,pred,zero_division=0),balanced_accuracy=balanced_accuracy_score(y,pred),roc_auc=roc_auc_score(y,pr),baseline_f1=f1_score(y,base,zero_division=0),baseline_balanced_accuracy=balanced_accuracy_score(y,base))
 for k,v in metrics.items():assert math.isclose(float(report[k]),v,abs_tol=1e-12)
 for k,v in zip(['tn','fp','fn','tp'],confusion_matrix(y,pred,labels=[0,1]).ravel(),strict=True):assert int(report[k])==v
 m=[r for r in members if all(r[k]==report[k] for k in ['publication','scenario'])]
 train=[r for r in m if r['partition']=='train'];test=[r for r in m if r['partition']=='test']
 assert not {r['compound_id'] for r in train}&{r['compound_id'] for r in test}
 assert len(train)==int(report['train_n']) and len(test)==int(report['test_n'])==len(p)
 if report['publication']=='Flavonoids2012':
  assert {r['compound_id'] for r in train}<={r['compound_id'] for r in old}
  assert len(train)==(73 if report['scenario']=='publication_only' else 52)
 if report['scenario']=='publication_and_scaffold':assert not {r['scaffold'] for r in train}&{r['scaffold'] for r in test}
 checks+=1
hashes=0
for path in [root/'external-inputs-v1/manifest.json',out/'manifest.json']:
 manifest=json.loads(path.read_text())
 for section in ['input_hashes','output_hashes','code_hashes','lock_hashes']:
  for name,digest in manifest[section].items():
   assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,(path,name)
   hashes+=1
result=dict(reports_recomputed=checks,predictions_checked=len(predictions),old_training_compounds_unchanged=73,primary_test_n=20,primary_test_active=2,hashes_checked=hashes,split_disjointness=True,scope='Fixed exploratory transfer test with incompatible assay targets; not validated efficacy prediction')
(root/'external_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
