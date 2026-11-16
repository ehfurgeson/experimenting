"""Acquire a primary-authored abstract snapshot; never call it primary full text."""
import hashlib,json
from pathlib import Path
import requests
root=Path('experiments/aquatic-context-2026-11-12/sources')
path=root/'kamaya2005_pubmed.html'
if path.exists():raise ValueError('Preserve existing source snapshot')
url='https://pubmed.ncbi.nlm.nih.gov/15722097/'
r=requests.get(url,timeout=30)
log={'url':url,'status':r.status_code,'bytes':len(r.content),'date':'2026-11-12'}
(root/'retrieval_log.json').write_text(json.dumps(log,indent=2)+'\n')
r.raise_for_status()
assert b'15722097' in r.content and b'7.45' in r.content and b'Acute toxicity of benzoic acids' in r.content
path.write_bytes(r.content)
registry=[{'source_id':'KAMAYA2005-ABSTRACT','kind':'primary_abstract','reference_number':'80404','file':path.name,'sha256':hashlib.sha256(r.content).hexdigest(),'url':url,'limitations':'Primary-authored abstract reproduced in PubMed; not full methods or result table; initial pH7.45+/-0.05; study-to-row propagation is provisional.'}]
(root/'sources.json').write_text(json.dumps(registry,indent=2)+'\n')
print(log)
