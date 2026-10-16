"""只读检查四块 TCM 的映射，不修改设备内容。"""
import fcntl,json,mmap,os
from pathlib import Path
lock_path=Path('/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock')
with lock_path.open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 result={'uid':os.getuid(),'device':'/dev/tcm','write_test':False,'blocks':[]}
 try:
  fd=os.open('/dev/tcm',os.O_RDWR)
 except OSError as exc:
  result.update(open_ok=False,errno=exc.errno,error=str(exc))
 else:
  result['open_ok']=True
  try:
   for block in range(4):
    try:
     with mmap.mmap(fd,131072,flags=mmap.MAP_SHARED,prot=mmap.PROT_READ,offset=block*131072) as region:
      first=region[0];last=region[-1]
      result['blocks'].append({'block':block,'size_bytes':131072,'map_ok':True,'edge_reads_ok':True})
    except OSError as exc:result['blocks'].append({'block':block,'map_ok':False,'errno':exc.errno,'error':str(exc)})
  finally:os.close(fd)
 print(json.dumps(result,indent=2))
