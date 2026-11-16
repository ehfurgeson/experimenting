import sys,csv,json
from pathlib import Path
sys.path.insert(0,'analysis')
from activity_preflight import run
root=Path('experiments/bioherbicide-expansion-2026-11-12')
holds=root/'identity_holds.csv'
holds.write_text('compound_id,reason\nCHEMBL2253255,N-allyl versus N-cyclopropyl\nCHEMBL2253236,unreadable substituent\nCHEMBL2253237,unresolved geometry\n')
adoption=Path('analysis/outputs/human-review-adopted-2026-11-11-final')
compounds=Path('analysis/outputs/chembl-review-screen-2026-10-29-final/structural_features.parquet')
# Source preparation uses input_smiles in this export; construct explicit new input.
import polars as pl
records=pl.read_parquet(compounds).to_dicts()
with (root/'baseline_compounds.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['compound_id','smiles']);w.writeheader()
 for r in records: w.writerow({'compound_id':r['compound_id'],'smiles':r['input_smiles']})
summary=[]
for name in ['K1998-TWO-SPECIES-VERY-ACTIVE-1MM-v1','OKAMOTO-1991-UPLAND-10G-AI-PER-A-v0.1','LI2006-AR-150G-POST-BOUNDS-v0.1','HE2011-AR-1500G-POST-BANDS-v0.1']:
 label_path=adoption/f'HUMAN-{name}.csv'
 # K1998 natural compounds occur in second-pass extended feature set.
 labels=list(csv.DictReader(label_path.open()))
 ids={r['compound_id'] for r in labels}
 all_features=pl.read_parquet(adoption/'contrast_features.parquet').to_dicts()
 by_id={r['compound_id']:r for r in records+all_features}
 missing=ids-set(by_id)
 if missing: print(name,'MISSING',missing);continue
 path=root/f'compounds_{name}.csv'
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['compound_id','smiles']);w.writeheader()
  for cid in sorted(ids):
   r=by_id[cid]; w.writerow({'compound_id':cid,'smiles':r.get('input_smiles') or r.get('canonical_structure')})
 m=run(path,label_path,[holds],root/'baseline_preflight'/name)
 summary.append({'policy':name,**m['reports'][0]})
 print(name,m['reports'][0])
(root/'baseline_support.json').write_text(json.dumps(summary,indent=2)+'\n')
