import hashlib,json
from pathlib import Path
import requests
root=Path(__file__).parent/'sources'
url='https://hwbdocs.env.nm.gov/Los%20Alamos%20National%20Labs/References/9483.PDF'
r=requests.get(url,timeout=30)
item=dict(url=url,status=r.status_code,bytes=len(r.content),valid_pdf=r.ok and r.content.startswith(b'%PDF-'))
if item['valid_pdf']:
 p=root/'kuhn1989.pdf';p.write_bytes(r.content);item.update(file=p.name,sha256=hashlib.sha256(r.content).hexdigest())
(root/'retrieval.json').write_text(json.dumps(item,indent=2)+'\n');print(json.dumps(item,indent=2))
