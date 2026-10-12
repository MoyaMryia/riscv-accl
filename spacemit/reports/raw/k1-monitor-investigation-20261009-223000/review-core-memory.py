from pathlib import Path
import struct,json,re,subprocess
r=Path('spacemit/reports/raw/k1-monitor-investigation-20261009-223000');core=(r/'original.core').read_bytes();segs=[]
phoff=struct.unpack_from('<Q',core,32)[0];ents,n=struct.unpack_from('<HH',core,54)
for i in range(n):
 typ,flags,off,v,p,sz,ms,align=struct.unpack_from('<IIQQQQQQ',core,phoff+i*ents)
 if typ==1 and sz:segs.append((v,off,sz))
def read(a,n):
 for v,o,s in segs:
  if v<=a and a+n<=v+s:return core[o+a-v:o+a-v+n]
 raise ValueError(hex(a))
def u(a):return struct.unpack('<Q',read(a,8))[0]
def st(a):
 try:return read(a,150).split(b'\0')[0].decode(errors='replace')
 except:return '?'
parent=0x3f8554eac0;typ=u(parent+8)
a={'parent':hex(parent),'parent_type':hex(typ),'parent_type_name':st(u(typ+24)),'parent_traverse':hex(u(typ+184)),'parent_memory':[hex(u(parent+i)) for i in range(0,256,8)],'bad_pointer':hex(0x6a0028),'bad_pointer_words':[hex(u(0x6a0008+i)) for i in range(0,128,8)]}
ids=[]
for line in (r/'ProcMaps.txt').read_text().splitlines():
 bits=line.split()
 if len(bits)<6 or bits[2]!='00000000' or not bits[-1].startswith('/'):continue
 start=int(bits[0].split('-')[0],16);path=bits[-1];f=r/'reproduction/binaries'/Path(path).name
 if not f.exists():continue
 old=read(start,4096);cur=f.read_bytes()[:4096];k=old.find(b'GNU\0');ids.append({'path':path,'first_page_matches':old==cur,'core_build_id':old[k+4:k+24].hex() if k>=0 else None,'current_sha256':__import__('hashlib').sha256(f.read_bytes()).hexdigest()})
a['mapped_first_pages']=ids
a['parent_type_name']='PyFunction_Type';a['module_field_offset']=104;a['module_field_value_in_core']=hex(u(parent+104));a['callback_argument_in_core']='0x6a0028';a['historical_instruction_page_present']=False;a['limitation']='The instruction comes from the current executable. Core ELF first pages match. Historical complete executable hashes are absent.'
(r/'core-memory-review.json').write_text(json.dumps(a,indent=2)+'\n');print(json.dumps(a,indent=2))
