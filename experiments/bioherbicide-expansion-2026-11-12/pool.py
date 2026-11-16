import sys,csv,json
from pathlib import Path
sys.path.insert(0,'analysis')
import polars as pl
from activity_preflight import run
from labels import LABEL_FIELDS
from screen import write_csv
root=Path('experiments/bioherbicide-expansion-2026-11-12')
sources=root/'sources'
root=root/'pooled-v2-corrected-doi'
root.mkdir()
adopt=Path('analysis/outputs/human-review-adopted-2026-11-11-final')
features=list(csv.DictReader((adopt/'accepted_activity_features.csv').open()))
compounds={}; labels=[];lineage=[]
policy='EXPERIMENT-HETEROGENEOUS-REPORTED-EXTREMES-v1'
for r in features:
 parent=r['activity_policy']
 if not any(s in parent for s in ['LI2006','HE2011']):continue
 cid=r['compound_id'];assert cid not in compounds
 compounds[cid]={'compound_id':cid,'smiles':r['input_smiles']}
 labels.append({k:r.get(k,'') for k in LABEL_FIELDS})
 lineage.append({'compound_id':cid,'parent_policy':parent,'publication': 'Li2006' if 'LI2006' in parent else 'He2011','evidence_status':'frozen_human_adopted'})
 labels[-1]['activity_policy']=policy
for n,activity in [('confertin','active'),('neoambrosin','inactive')]:
 raw=json.loads((sources/f'{n}.pubchem.json').read_text())['PropertyTable']['Properties']
 assert len(raw)==1
 r=raw[0];cid=f'AMBROSIA2019:{n}'
 compounds[cid]={'compound_id':cid,'smiles':r['SMILES']}
 labels.append({'compound_id':cid,'herbicidal_activity':activity,'natural_origin':'natural','origin_reference':'10.3390/molecules24050835 sections 2.1/3.3; provisional name-to-structure mapping','activity_reference':'10.3390/molecules24050835 Table 2','activity_context':'Lactuca sativa; 1000 micromolar; 7 days; ordinal germination/growth; grade 4 confertin or 0 neoambrosin; provisional identity and vehicle/replication gaps retained','activity_policy':policy})
 lineage.append({'compound_id':cid,'parent_policy':'EXPERIMENT-AMBROSIA2019-LETTUCE-1MM-7D-ORDINAL-v1','publication':'Ambrosia2019','evidence_status':'AI_experimental_provisional_not_human_reviewed'})
write_csv(root/'pooled_compounds.csv',list(compounds.values()),['compound_id','smiles'])
write_csv(root/'pooled_labels.csv',labels,['compound_id']+sorted(LABEL_FIELDS-{'compound_id'}))
write_csv(root/'pooled_lineage.csv',lineage,list(lineage[0]))
m=run(root/'pooled_compounds.csv',root/'pooled_labels.csv',[root.parent/'identity_holds.csv'],root/'pooled_preflight')
print(json.dumps(m['reports'],indent=2))
