import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path('analysis').resolve()))
from screen import prepare, write_csv
root = Path('analysis/outputs/chembl-2026-10-28')
compounds = {}
review = []
audit = []
for path in sorted((root/'raw/chembl').glob('*.json')):
 b=json.loads(path.read_text()); activities=[r for p in b['activity_pages'] for r in p['activities']]
 local=[]
 for a in activities:
  identity=a['molecule_chembl_id']
  row={'compound_id':identity,'canonical_smiles':a.get('canonical_smiles'),'query':a.get('molecule_pref_name')}
  if identity in compounds and compounds[identity]['canonical_smiles'] != row['canonical_smiles']:
   raise ValueError(f'Conflicting structure for {identity}')
  compounds[identity]=row;local.append(row)
  review.append({**{k:a.get(k) for k in ['activity_id','assay_chembl_id','molecule_chembl_id','canonical_smiles','standard_type','standard_relation','standard_value','standard_units','activity_comment','data_validity_comment','potential_duplicate']},'assay_description':b['assay']['description'],'document_chembl_id':b['document']['document_chembl_id'],'doi':b['document'].get('doi'),'snapshot_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 features=prepare(list({r['compound_id']:r for r in local}.values()))
 entry={'assay':b['assay']['assay_chembl_id'],'records':len(activities),'molecules':len(features),'valid_structures':sum(r['structure_status']=='valid' for r in features),'scaffolds':len({r['scaffold'] for r in features if r['structure_status']=='valid'}),'endpoint_units':dict(Counter(str((a.get('standard_type'),a.get('standard_units'))) for a in activities)),'relations':dict(Counter(str(a.get('standard_relation')) for a in activities)),'values':dict(Counter(str(a.get('standard_value')) for a in activities)),'doi':b['document'].get('doi')}
 audit.append(entry);print(json.dumps(entry),flush=True)
write_csv(root/'candidates.csv', list(compounds.values()),['compound_id','canonical_smiles','query'])
write_csv(root/'activity_review.csv',review,list(review[0]))
(root/'acquisition_audit.json').write_text(json.dumps({'assays':audit,'unique_molecules':len(compounds),'records':len(review)},indent=2)+'\n')
print('TOTAL',len(review),'records',len(compounds),'unique molecules')
