from pathlib import Path
from urllib.parse import quote
import requests,json,hashlib,time
root=Path('experiments/bioherbicide-expansion-2026-11-12/sources')
urls={
 'dittrichia2025_supplement.zip':'https://pmc.ncbi.nlm.nih.gov/articles/instance/12526312/bin/molecules-30-03950-s001.zip',
 'marinefungi2018.pdf':'https://pubs.rsc.org/en/content/articlepdf/2018/ra/c8ra08047j',
}
for name in ['3-anhydro-ophiobolin A','6-epi-ophiobolin A','6-epi-ophiobolin B','3-anhydro-6-epi-ophiobolin B','ophiobolin I']:
 urls[name.replace(' ','_')+'.pubchem.json']=f'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{quote(name)}/property/IsomericSMILES,InChIKey,MolecularFormula/JSON'
log=[]
for name,url in urls.items():
 try:
  r=requests.get(url,timeout=25);item={'file':name,'url':url,'status':r.status_code,'bytes':len(r.content)}
  if r.ok:
   (root/name).write_bytes(r.content);item['sha256']=hashlib.sha256(r.content).hexdigest()
  log.append(item)
 except requests.RequestException as e:log.append({'file':name,'url':url,'error':str(e)})
 time.sleep(.3)
(root/'ophiobolins_retrieval_log.json').write_text(json.dumps(log,indent=2)+'\n')
for x in log:print(x['file'],x.get('status'),x.get('bytes'),x.get('error',''))
