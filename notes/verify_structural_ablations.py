import csv,hashlib,json
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT=Path('analysis/outputs')
def read(path):
 with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
reference={}
for row in read(ROOT/'structure-2026-10-28-stress-baseline/out_of_fold.csv'):
 if row['target']=='selection_target' and row['representation']=='formula':
  reference[row['compound_id']]=int(row['fold'])
for mode in ['fixed','nested']:
 root=ROOT/f'ablations-{mode}-2026-10-29-final'
 manifest=json.loads((root/'manifest.json').read_text())
 for section in ['input_hashes','code_hashes','lock_hashes','output_hashes']:
  for p,digest in manifest[section].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest,(root,section,p)
 cohort=read(root/'cohort.csv');ids={r['compound_id'] for r in cohort}
 assert len(cohort)==len(ids)==171 and ids==set(reference)
 assert sum(int(r['label']) for r in cohort)==55
 assert manifest['imputed_cells']==0
 by_profile=defaultdict(list)
 for row in read(root/'out_of_fold.csv'):by_profile[row['profile']].append(row)
 assert len(by_profile)==9
 for profile,rows in by_profile.items():
  assert len(rows)==len({r['compound_id'] for r in rows})==171
  assert {r['compound_id']:int(r['fold']) for r in rows}==reference
  assignment=defaultdict(set)
  for r in rows:assignment[r['scaffold']].add(r['fold'])
  assert all(len(folds)==1 for folds in assignment.values())
 fixed_reference={r['profile']:float(r['balanced_accuracy']) for r in read(ROOT/'ablations-fixed-2026-10-29/ablation_models.csv')}
 if mode=='fixed':
  assert {r['profile']:float(r['balanced_accuracy']) for r in manifest['reports']}==fixed_reference
  assert not read(root/'inner_scores.csv')
 else:
  scores=defaultdict(lambda:defaultdict(list))
  history=read(root/'inner_scores.csv');assert len(history)==675
  for row in history:scores[(row['profile'],int(row['fold']))][float(row['c'])].append(float(row['balanced_accuracy']))
  for row in read(root/'folds.csv'):
   choices=scores[(row['profile'],int(row['fold']))]
   assert len(choices)==5 and all(len(s)==3 for s in choices.values())
   means={c:float(np.mean(s)) for c,s in choices.items()}
   chosen=min(c for c,s in means.items() if abs(s-max(means.values()))<=1e-12)
   assert float(row['selected_c'])==chosen
   assert abs(float(row['inner_best_balanced_accuracy'])-means[chosen])<1e-12
 print(mode, 'verified: 171 identical compounds, original outer folds, complete OOF, source/product hashes and C selection')
