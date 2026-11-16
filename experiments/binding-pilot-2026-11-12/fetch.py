"""Bounded public structural-evidence acquisition for two declared complexes."""
import hashlib,json,time
from datetime import datetime,UTC
from pathlib import Path
from urllib.parse import quote
import requests
root=Path('experiments/binding-pilot-2026-11-12/sources')
if (root/'retrieval_log.json').exists():raise ValueError('Use a new cache version')
log=[]
def fetch(name,url,kind='json'):
 path=root/name
 if path.exists():raise ValueError('Preserve source snapshot')
 try:
  r=requests.get(url,timeout=30);path.write_bytes(r.content)
  record={'file':name,'url':url,'status':r.status_code,'bytes':len(r.content),'sha256':hashlib.sha256(r.content).hexdigest(),'retrieved_at':datetime.now(UTC).isoformat()}
  data=None
  if r.ok:
   try:data=r.json() if kind=='json' else r.text
   except ValueError:record['validation']='not_json'
  log.append(record);time.sleep(.3);return data
 except requests.RequestException as error:
  log.append({'file':name,'url':url,'error':str(error)});return None
for pdb in ['1KMH','8CI0']:
 data=fetch(f'{pdb}_entry.json',f'https://data.rcsb.org/rest/v1/core/entry/{pdb}')
 if not data:continue
 assert data['rcsb_id']==pdb
 ids=data['rcsb_entry_container_identifiers']
 for entity in ids.get('polymer_entity_ids',[]):
  fetch(f'{pdb}_polymer_{entity}.json',f'https://data.rcsb.org/rest/v1/core/polymer_entity/{pdb}/{entity}')
 for entity in ids.get('non_polymer_entity_ids',[]):
  fetch(f'{pdb}_nonpolymer_{entity}.json',f'https://data.rcsb.org/rest/v1/core/nonpolymer_entity/{pdb}/{entity}')
for comp in ['TTX','8EL']:
 fetch(f'{comp}_chemcomp.json',f'https://data.rcsb.org/rest/v1/core/chemcomp/{comp}')
for name in ['tentoxin','cornexistin']:
 fetch(f'{name}_pubchem.json',f'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{quote(name)}/property/IsomericSMILES,InChIKey,MolecularFormula/JSON')
fetch('tentoxin_primary.html','https://pmc.ncbi.nlm.nih.gov/articles/PMC122546/',kind='text')
(root/'retrieval_log.json').write_text(json.dumps(log,indent=2)+'\n')
for r in log:print(r['file'],r.get('status'),r.get('bytes'),r.get('validation',r.get('error','')))
