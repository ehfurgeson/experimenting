import concurrent.futures,hashlib,json
from pathlib import Path
from urllib.parse import quote
import requests
root=Path(__file__).parent/'sources'
names=['flavone','7-hydroxyflavone','7-methoxyflavone','chrysin','5,7-dimethoxyflavone',"3\u2032,4\u2032-dimethoxyflavone",'luteolin','luteolin tetramethyl ether','3-hydroxyflavone','3-methoxyflavone','morin','quercetin','rutin','beta-naphthoflavone','genistein','flavanone','7-hydroxyflavanone','7-methoxyflavanone','pinocembrin','5,7-dimethoxyflavanone','naringenin','naringin','hesperetin','hesperidin','(+)-catechin','catechol','phloridzin']
def fetch(pair):
 i,name=pair;path=root/f'flavonoid-{i:02}.pubchem.json'
 url='https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/'+quote(name,safe='')+'/property/IsomericSMILES,InChIKey,MolecularFormula/JSON'
 item=dict(row=i,name=name,url=url,file=path.name)
 try:
  r=requests.get(url,timeout=25);item.update(status=r.status_code,bytes=len(r.content))
  if r.ok:
   data=r.json();props=data.get('PropertyTable',{}).get('Properties',[])
   if props and all(p.get('InChIKey') and p.get('SMILES') for p in props):
    path.write_bytes(r.content);item.update(hits=len(props),sha256=hashlib.sha256(r.content).hexdigest())
 except (requests.RequestException,ValueError) as e:item['error']=str(e)
 return item
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:log=list(ex.map(fetch,enumerate(names,1)))
(root/'identity_retrieval.json').write_text(json.dumps(log,indent=2)+'\n')
for x in log:print(x['row'],x['name'],x.get('status'),x.get('hits'),x.get('error',''))
