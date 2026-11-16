"""Try NCBI's XML endpoint after the HTML response failed content checks."""
import hashlib,json
from pathlib import Path
from xml.etree import ElementTree as ET
import requests
root=Path('experiments/aquatic-context-2026-11-12/sources')
path=root/'kamaya2005_pubmed.xml'
if path.exists():raise ValueError('Preserve existing source snapshot')
url='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=15722097&retmode=xml'
r=requests.get(url,timeout=30)
path.write_bytes(r.content)
log={'url':url,'status':r.status_code,'bytes':len(r.content),'date':'2026-11-12','sha256':hashlib.sha256(r.content).hexdigest()}
(root/'xml_retrieval_log.json').write_text(json.dumps(log,indent=2)+'\n')
r.raise_for_status()
tree=ET.fromstring(r.content)
abstract=' '.join(''.join(t.itertext()) for t in tree.findall('.//AbstractText'))
assert tree.findtext('.//PMID')=='15722097' and '7.45' in abstract
registry=[{'source_id':'KAMAYA2005-ABSTRACT','kind':'primary_abstract','reference_number':'80404','file':path.name,'sha256':log['sha256'],'url':url,'limitations':'Primary-authored abstract reproduced in PubMed; not full methods or result table; initial pH7.45+/-0.05; study-to-row propagation is provisional.'}]
(root/'sources.json').write_text(json.dumps(registry,indent=2)+'\n')
print(log)
