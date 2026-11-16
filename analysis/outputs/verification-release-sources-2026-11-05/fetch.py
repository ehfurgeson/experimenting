"""Public source acquisition only; no label assignment or training."""
import csv,json,time
from datetime import UTC,datetime
from pathlib import Path
from urllib.parse import quote
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

root=Path.cwd(); release=root/'notes/compound_verification_release_2026-11-05'
out=root/'analysis/outputs/verification-release-sources-2026-11-05'
assert not out.exists()
out.mkdir(parents=True)
rows=list(csv.DictReader((release/'independent_structure_origin_crosschecks.csv').open()))
leads=list(csv.DictReader((release/'new_out_of_worksheet_compound_leads.csv').open()))
jobs=[]
for r in rows:
 url=r['reference_url'];kind='ppdb_html'
 if 'pubchem.ncbi.nlm.nih.gov/compound/' in url:
  cid=url.rsplit('/',1)[1];url=f'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/IsomericSMILES,InChIKey/JSON';kind='pubchem_json'
 jobs.append(('reference:'+r['compound_id'],url,kind,r['reference_url']))
for r in leads:
 url='https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/'+quote(r['name'],safe='')+'/property/IsomericSMILES,InChIKey/JSON'
 jobs.append(('lead:'+r['name'],url,'pubchem_json',r['source_reference']))
jobs.append(('primary:2021','https://www.jstage.jst.go.jp/article/mycosci/62/1/62_MYC515/_html/-char/en','primary_html','https://doi.org/10.47371/mycosci.2020.11.002'))
session=requests.Session();session.mount('https://',HTTPAdapter(max_retries=Retry(total=3,backoff_factor=1,status_forcelist=[429,500,502,503,504])))
for i,(key,url,kind,reference_url) in enumerate(jobs):
 saved={'key':key,'url':url,'kind':kind,'reference_url':reference_url,'retrieved_at':datetime.now(UTC).isoformat(),'status':None,'body':None,'error':None}
 try:
  r=session.get(url,timeout=45);saved.update(status=r.status_code,body=r.text,final_url=r.url)
 except requests.RequestException as exc:saved['error']=type(exc).__name__
 (out/f'{i:03d}.json').write_text(json.dumps(saved,indent=2)+'\n')
 print(key,saved['status'],flush=True);time.sleep(.3)
import shutil,hashlib
shutil.copyfile(__file__,out/'fetch.py')
(out/'manifest.json').write_text(json.dumps({'acquisition_only':True,'source_release':str(release),'requests':len(jobs),'output_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}},indent=2)+'\n')
