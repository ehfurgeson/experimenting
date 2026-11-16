from pathlib import Path
import requests,json,hashlib
root=Path('experiments/bioherbicide-expansion-2026-11-12/sources')
urls={
'pileostegia2016.pdf':'https://journals.sagepub.com/doi/pdf/10.1177/1934578X1601100716',
'semenovia2012.pdf':'https://journals.sagepub.com/doi/pdf/10.1177/1934578X1200701019',
'pileostegia2016.html':'https://journals.sagepub.com/doi/10.1177/1934578X1601100716',
'semenovia2012.html':'https://journals.sagepub.com/doi/10.1177/1934578X1200701019',
'pileostegia2016_usda.html':'https://www.ars.usda.gov/research/publications/publication/?seqNo115=311353',
'diarylamines2026.html':'https://pubs.acs.org/doi/10.1021/acsagscitech.6c00071',
}
log=[]
for name,url in urls.items():
 try:
  r=requests.get(url,timeout=25);item={'file':name,'url':url,'status':r.status_code,'bytes':len(r.content)}
  if r.ok:
   (root/name).write_bytes(r.content);item['sha256']=hashlib.sha256(r.content).hexdigest()
  log.append(item)
 except requests.RequestException as e:log.append({'file':name,'url':url,'error':str(e)})
(root/'additional_retrieval_log.json').write_text(json.dumps(log,indent=2)+'\n')
for x in log:print(x['file'],x.get('status'),x.get('bytes'),x.get('error',''))
