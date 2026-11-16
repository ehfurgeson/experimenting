"""Follow the actual deposited inhibitor component, not a default cofactor link."""
import hashlib,json
from pathlib import Path
import requests
root=Path('experiments/binding-pilot-2026-11-12/sources')
urls={'UP0_chemcomp.json':'https://data.rcsb.org/rest/v1/core/chemcomp/UP0','cornexistin_primary.html':'https://pmc.ncbi.nlm.nih.gov/articles/PMC7614749/'}
log=[]
for name,url in urls.items():
 path=root/name
 if path.exists():raise ValueError('Preserve snapshots')
 r=requests.get(url,timeout=30);path.write_bytes(r.content)
 log.append({'file':name,'url':url,'http_status':r.status_code,'bytes':len(r.content),'sha256':hashlib.sha256(r.content).hexdigest(),'date':'2026-11-12'})
 r.raise_for_status()
 if name.endswith('.json'):assert r.json()['chem_comp']['id']=='UP0'
 else:assert b'cornexistin' in r.content.lower() and b'7614749' in r.content
(root/'bound_form_retrieval_log.json').write_text(json.dumps(log,indent=2)+'\n')
for x in log:print(x['file'],x['http_status'],x['bytes'])
