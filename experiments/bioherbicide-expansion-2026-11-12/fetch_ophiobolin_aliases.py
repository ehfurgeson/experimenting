from pathlib import Path
from urllib.parse import quote
import requests,json,hashlib,time
root=Path('experiments/bioherbicide-expansion-2026-11-12/sources')
names=['3-anhydroophiobolin A','6-epiophiobolin B','3-anhydro-6-epiophiobolin B']
log=[]
for name in names:
 url=f'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{quote(name)}/property/IsomericSMILES,InChIKey,MolecularFormula/JSON'
 try:
  r=requests.get(url,timeout=20);item={'name':name,'url':url,'status':r.status_code,'bytes':len(r.content)}
  if r.ok:
   filename=name.replace(' ','_')+'.pubchem.json';(root/filename).write_bytes(r.content);item.update(file=filename,sha256=hashlib.sha256(r.content).hexdigest())
  log.append(item)
 except requests.RequestException as e:log.append({'name':name,'error':str(e)})
 time.sleep(.3)
(root/'ophiobolin_alias_log.json').write_text(json.dumps(log,indent=2)+'\n')
for x in log:print(x['name'],x.get('status'),x.get('bytes'),x.get('error',''))
