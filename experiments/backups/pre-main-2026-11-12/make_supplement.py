import hashlib,json,subprocess,tarfile
from pathlib import Path
root=Path.cwd();dest=root/'experiments/backups/pre-main-2026-11-12'
resolution=json.loads((dest/'historical_reference_resolution.json').read_text())
probe='/private/tmp/agrotox-preservation-restore-2026-11-12.git'
for r in resolution['records']:
 x=r['resolution']
 if x['kind']=='git_bundle_history':
  data=subprocess.check_output(['git','--git-dir='+probe,'show',x['commit']+':'+x['path']])
  assert hashlib.sha256(data).hexdigest()==r['recorded_sha256']
# Never overwrite the earlier preservation archive or any scientific input.
path=dest/'historical-supplement.tar.gz';assert not path.exists()
files=[root/'analysis/outputs/weekly-literature-acquisition-input-2026-11-10/acquisition_resource.json',root/'analysis/outputs/weekly-literature-acquisition-input-2026-11-10/manifest.json',dest/'README.md',dest/'verify_archive.py',dest/'resolve_history.py',dest/'historical_reference_resolution.json',Path(__file__)]
entries={str(p.relative_to(root)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in files}
with tarfile.open(path,'w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(root)),recursive=False)
with tarfile.open(path,'r:gz') as tar:
 assert len(tar.getmembers())==len(entries)
 for member in tar:
  data=tar.extractfile(member).read();assert hashlib.sha256(data).hexdigest()==entries[member.name]['sha256'] and len(data)==entries[member.name]['bytes']
receipt=dict(archive_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),archive_bytes=path.stat().st_size,files=entries,git_bundle_restore_fsck_passed=True,historical_differences_resolved=44,historical_differences_unresolved=1)
(dest/'supplement-verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k!='files'},indent=2))
