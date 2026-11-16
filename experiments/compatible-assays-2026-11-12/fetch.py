import hashlib,json
from pathlib import Path
import requests
root=Path(__file__).parent/'sources'
urls={
 'cuscuta2022.html':('https://www.mdpi.com/2077-0472/12/10/1746','Identification of Allelochemicals'),
 'flavonoids2012.html':('https://pmc.ncbi.nlm.nih.gov/articles/PMC3382788/','In Vitro Phytotoxicity'),
 'pollen2016.html':('https://pmc.ncbi.nlm.nih.gov/articles/PMC5011872/','Novel small molecule modulators'),
 'prestwick2025.html':('https://pmc.ncbi.nlm.nih.gov/articles/PMC12032938/','A high-throughput differential'),
}
log=[]
for name,(url,title) in urls.items():
 try:
  r=requests.get(url,timeout=25)
  valid=r.ok and title.casefold() in r.text.casefold() and len(r.content)>30000
  item=dict(file=name,url=url,status=r.status_code,bytes=len(r.content),content_check=valid)
  if valid:
   (root/name).write_bytes(r.content);item['sha256']=hashlib.sha256(r.content).hexdigest()
  log.append(item)
 except requests.RequestException as e:log.append(dict(file=name,url=url,error=str(e)))
(root/'retrieval.json').write_text(json.dumps(log,indent=2)+'\n')
print(json.dumps(log,indent=2))
