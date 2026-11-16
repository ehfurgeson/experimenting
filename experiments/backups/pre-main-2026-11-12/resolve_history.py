import hashlib,json,subprocess
from pathlib import Path
root=Path.cwd();out=root/'experiments/backups/pre-main-2026-11-12'
x=json.loads((out/'inventory.json').read_text());byhash={r['sha256']:r['path'] for r in x['files']}
cache={};records=[]
for ref in x['historical_hash_differences']:
 digest=ref['recorded_sha256'];path=Path(ref['path']).relative_to(root).as_posix()
 if digest in byhash:
  resolution=dict(kind='archived_file',path=byhash[digest])
 else:
  if path not in cache:
   versions={}
   commits=subprocess.check_output(['git','log','--all','--format=%H','--',path],text=True).splitlines()
   for commit in commits:
    r=subprocess.run(['git','show',f'{commit}:{path}'],capture_output=True)
    if r.returncode==0:versions[hashlib.sha256(r.stdout).hexdigest()]=commit
   cache[path]=versions
  commit=cache[path].get(digest)
  resolution=dict(kind='git_bundle_history',commit=commit,path=path) if commit else dict(kind='unresolved')
 records.append(dict(**ref,resolution=resolution))
result=dict(historical_differences=len(records),resolved=sum(r['resolution']['kind']!='unresolved' for r in records),records=records)
(out/'historical_reference_resolution.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))
for r in records:
 if r['resolution']['kind']=='unresolved':print('UNRESOLVED',r['section'],r['path'],r['recorded_sha256'])
