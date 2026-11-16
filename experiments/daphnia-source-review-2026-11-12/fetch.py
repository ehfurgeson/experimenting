import hashlib,json
from pathlib import Path
import requests
root=Path(__file__).parent/'sources'
url='https://www.lookchem.com/FreePDFArticle_623-05-2_6656292.htm'
try:
 r=requests.get(url,timeout=25);item=dict(url=url,status=r.status_code,bytes=len(r.content))
 if r.ok:
  p=root/'kamaya2005_landing.html';p.write_bytes(r.content);item.update(file=p.name,sha256=hashlib.sha256(r.content).hexdigest())
except requests.RequestException as e:item=dict(url=url,error=str(e))
(root/'retrieval.json').write_text(json.dumps(item,indent=2)+'\n');print(json.dumps(item,indent=2))
