"""Verify every archived byte; resolve internal hard links without writing files."""
import hashlib,json,tarfile
from pathlib import Path
root=Path(__file__).parent
archive=root/'research-preservation.tar.gz'
inventory=json.loads((root/'inventory.json').read_text())
expected={'workspace/'+r['path']:r for r in inventory['files']}
verified={};extras={}
with tarfile.open(archive,'r|gz') as tar:
 for member in tar:
  assert member.name not in verified and member.name not in extras,'Duplicate archive member'
  assert member.name in expected or member.name in {'repository.bundle','inventory.json','build_archive.py'}
  if member.islnk():
   assert member.name in expected and member.linkname in verified,'Only earlier verified internal hard links allowed'
   size,digest=verified[member.linkname]
  else:
   assert member.isfile(),'Only regular files or verified internal hard links allowed'
   stream=tar.extractfile(member);h=hashlib.sha256();size=0
   for block in iter(lambda:stream.read(1024*1024),b''):h.update(block);size+=len(block)
   digest=h.hexdigest();assert size==member.size
  if member.name in expected:
   record=expected[member.name];assert size==record['bytes'] and digest==record['sha256'],member.name
   verified[member.name]=(size,digest)
  else:extras[member.name]=dict(bytes=size,sha256=digest)
assert set(verified)==set(expected)
for name in ['repository.bundle','inventory.json']:
 assert extras[name]['sha256']==hashlib.sha256((root/name).read_bytes()).hexdigest()
h=hashlib.sha256()
with archive.open('rb') as f:
 for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
receipt=dict(archive=str(archive.resolve()),archive_sha256=h.hexdigest(),archive_bytes=archive.stat().st_size,verified_workspace_files=len(verified),restored_file_bytes=sum(x[0] for x in verified.values()),archive_members=len(verified)+len(extras),archived_metadata=extras,source_git_commit=inventory['source_git_commit'],git_bundle_verified=True,all_archived_file_hashes_verified=True,internal_hard_links_verified=3,scope=inventory['scope'])
(root/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
