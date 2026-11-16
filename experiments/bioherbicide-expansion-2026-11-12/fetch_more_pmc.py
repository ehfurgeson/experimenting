from pathlib import Path
import requests,json,hashlib
root=Path('experiments/bioherbicide-expansion-2026-11-12/sources')
urls={'marinefungi2018.html':'https://pmc.ncbi.nlm.nih.gov/articles/PMC9089327/', 'ophiobolins2021.html':'https://pmc.ncbi.nlm.nih.gov/articles/PMC9157744/', 'dittrichia2025.html':'https://pmc.ncbi.nlm.nih.gov/articles/PMC12526312/'}
log=[]
for name,url in urls.items():
 try:
  r=requests.get(url,timeout=25); item={'file':name,'url':url,'status':r.status_code,'bytes':len(r.content)}
  if r.ok:
   (root/name).write_bytes(r.content);item['sha256']=hashlib.sha256(r.content).hexdigest()
  log.append(item)
 except requests.RequestException as e:log.append({'file':name,'url':url,'error':str(e)})
(root/'more_pmc_retrieval_log.json').write_text(json.dumps(log,indent=2)+'\n')
for x in log:print(x['file'],x.get('status'),x.get('bytes'),x.get('error',''))
