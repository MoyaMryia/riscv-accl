import tarfile,hashlib,posixpath,json
from pathlib import Path
p=Path('spacemit/reports/raw/k1-predictor-v1-20261011/local-evidence.tar.gz')
expected='b2fb49e3d3290094676914117593bd51511cf6658d24e82e9bbf0a68aaa825d5'
h=hashlib.sha256()
with p.open('rb') as f:
 for b in iter(lambda:f.read(1048576),b''):h.update(b)
assert h.hexdigest()==expected
hashes={};receipts={};links={}
with tarfile.open(p,'r|gz') as t:
 for m in t:
  if m.issym():links[m.name]=posixpath.normpath(posixpath.join(posixpath.dirname(m.name),m.linkname));continue
  if not m.isfile():continue
  f=t.extractfile(m);h=hashlib.sha256();data=[] if m.name.endswith('SHA256SUMS') else None
  for b in iter(lambda:f.read(1048576),b''):
   h.update(b)
   if data is not None:data.append(b)
  hashes[m.name]=h.hexdigest()
  if data is not None:receipts[m.name]=b''.join(data).decode()
for name,target in links.items():
 while target in links:target=links[target]
 if target in hashes:hashes[name]=hashes[target]
base_map={'lab/k1-predictor-20261011-v1/native-payload/run/SHA256SUMS':'lab/k1-predictor-20261011-v1/native-payload'}
checks=0;missing=[];mismatch=[]
for source,s in receipts.items():
 for line in s.splitlines():
  checksum,name=line.split(maxsplit=1);name=name.lstrip('*')
  name=posixpath.normpath(posixpath.join(base_map.get(source,posixpath.dirname(source)),name))
  if name not in hashes:missing.append(dict(source=source,path=name));continue
  checks+=1
  if hashes[name]!=checksum:mismatch.append(dict(source=source,path=name))
r=dict(archive_sha256=expected,files_hashed=len(hashes),receipt_files=len(receipts),receipt_entries_checked=checks,declared_receipt_bases=base_map,missing=missing,mismatch=mismatch)
Path('spacemit/reports/raw/k1-predictor-v1-20261011/local-archive-verification.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2));assert not missing and not mismatch
