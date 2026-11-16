"""Local preservation only: explicit research roots and hash-linked dependencies."""
import hashlib,json,subprocess,tarfile
from pathlib import Path
ROOT=Path.cwd().resolve()
DEST=ROOT/'experiments/backups/pre-main-2026-11-12'
ARCHIVE=DEST/'research-preservation.tar.gz'
assert not ARCHIVE.exists(),'Never overwrite an archive'
roots=sorted([p for p in (ROOT/'experiments').iterdir() if p.is_dir() and p.name.endswith('2026-11-12')]+list((ROOT/'analysis/outputs').glob('*2026-11-12*')))
files=set();pending=[];outside=[];missing=[];references=[]
def add(p):
 p=Path(p)
 if not p.is_absolute():p=ROOT/p
 if p.is_symlink():raise ValueError(f'Symlink not allowed: {p}')
 p=p.resolve()
 if not p.is_relative_to(ROOT):outside.append(str(p));return
 if p.is_relative_to(DEST):raise ValueError('Archive dependency cannot refer to archive itself')
 if any(x in {'.env','.aws','.git','.codex','.agents'} for x in p.relative_to(ROOT).parts):raise ValueError(f'Private runtime path: {p}')
 if not p.is_file():missing.append(str(p));return
 if p not in files:
  files.add(p)
  if 'manifest' in p.name.lower() and p.suffix=='.json':pending.append(p)
for root in roots:
 for p in root.rglob('*'):
  if p.is_symlink():raise ValueError(f'Symlink not allowed: {p}')
  if p.is_file() and '__pycache__' not in p.parts and p.name!='.DS_Store':add(p)
while pending:
 path=pending.pop()
 try:data=json.loads(path.read_text())
 except (UnicodeDecodeError,ValueError):continue
 if not isinstance(data,dict):continue
 for section in ['input_hashes','output_hashes','code_hashes','lock_hashes','source_hashes']:
  entries=data.get(section,{})
  if not isinstance(entries,dict):continue
  for name,digest in entries.items():
   if isinstance(name,str) and isinstance(digest,str) and len(digest)==64:
    add(name);references.append((str(path.relative_to(ROOT)),section,name,digest))
def digest_file(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
entries=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=digest_file(p)) for p in sorted(files)]
by_path={str(ROOT/r['path']):r for r in entries}
mismatches=[dict(manifest=m,section=s,path=n,recorded_sha256=d,current_sha256=by_path[str(Path(n).resolve())]['sha256']) for m,s,n,d in references if str(Path(n).resolve()) in by_path and by_path[str(Path(n).resolve())]['sha256']!=d]
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
inventory=dict(format_version=1,source_repository_root=str(ROOT),source_git_commit=head,roots=[str(p.relative_to(ROOT)) for p in roots],files=entries,files_count=len(entries),total_file_bytes=sum(x['bytes'] for x in entries),outside_repository_dependencies=sorted(set(outside)),missing_referenced_paths=sorted(set(missing)),historical_hash_differences=mismatches,scope='Local research preservation; includes unfinished/failed runs without approving them. Existing absolute manifest paths retained. Git bundle preserves historical code; current code hashes can differ from historical manifests. Not a credential backup or a clean-clone bootstrap.')
(DEST/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
print(json.dumps({k:inventory[k] for k in ['source_git_commit','files_count','total_file_bytes','outside_repository_dependencies','missing_referenced_paths']},indent=2),flush=True)
bundle=DEST/'repository.bundle'
subprocess.run(['git','bundle','create',str(bundle),'HEAD','main'],check=True)
subprocess.run(['git','bundle','verify',str(bundle)],check=True)
with tarfile.open(DEST/'research-preservation.partial','w:gz',compresslevel=3) as tar:
 for entry in entries:tar.add(ROOT/entry['path'],arcname='workspace/'+entry['path'],recursive=False)
 for p in [bundle,DEST/'inventory.json',Path(__file__)]:tar.add(p,arcname=p.name,recursive=False)
(DEST/'research-preservation.partial').rename(ARCHIVE)
# Read and hash every restored file from the archive stream; do not extract over the checkout.
with tarfile.open(ARCHIVE,'r:gz') as tar:
 members={m.name:m for m in tar.getmembers()}
 assert len(members)==len(entries)+3
 for entry in entries:
  name='workspace/'+entry['path'];member=members[name]
  assert member.isfile() and member.size==entry['bytes']
  h=hashlib.sha256();stream=tar.extractfile(member)
  for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
  assert h.hexdigest()==entry['sha256'],name
receipt=dict(archive=str(ARCHIVE),archive_sha256=digest_file(ARCHIVE),archive_bytes=ARCHIVE.stat().st_size,inventory_sha256=digest_file(DEST/'inventory.json'),bundle_sha256=digest_file(bundle),verified_workspace_files=len(entries),archive_members=len(members),source_git_commit=head,git_bundle_verified=True,all_archived_file_hashes_verified=True,scope=inventory['scope'])
(DEST/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2),flush=True)
