import hashlib,json
from pathlib import Path
import requests
root=Path('/Users/ehfurgeson/Documents/GitHub/agrochem-toxicity/experiments/bioherbicide-expansion-2026-11-12/sources')
urls={
 'sorbicillinoids2019.html':'https://www.frontiersin.org/journals/chemistry/articles/10.3389/fchem.2019.00435/full',
 'nonenolides2021.xml':'https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC8541495',
 'rosemary2018.html':'https://pmc.ncbi.nlm.nih.gov/articles/PMC6316382/',
 'ambrosia2019.html':'https://pmc.ncbi.nlm.nih.gov/articles/PMC6429092/',
 'nonenolides2021.html':'https://pmc.ncbi.nlm.nih.gov/articles/PMC8541495/',
 'cleomside2020.html':'https://pmc.ncbi.nlm.nih.gov/articles/PMC7582273/',
}
log=[]
for name,url in urls.items():
 try:
  r=requests.get(url,timeout=25)
  item={'file':name,'url':url,'status':r.status_code,'bytes':len(r.content)}
  if r.ok:
   (root/name).write_bytes(r.content)
   item['sha256']=hashlib.sha256(r.content).hexdigest()
  log.append(item)
 except requests.RequestException as e:
  log.append({'file':name,'url':url,'error':str(e)})
(root/'retrieval_log.json').write_text(json.dumps(log,indent=2)+'\n')
for x in log: print(x['file'],x.get('status'),x.get('bytes'),x.get('error',''))
