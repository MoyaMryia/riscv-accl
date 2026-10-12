import json, os, subprocess
from pathlib import Path
repo=Path('/home/moyamryia/Projects/riscv-accl');root=Path(__file__).resolve().parent
old=repo/'lab/k1-local-candidates-C2-r2-20261009-061500';build=repo/'lab/local-candidates-final-20261008/build-rvv'
compiler=repo/'lab/toolchain/toolchain/riscv/bin/riscv64-unknown-linux-gnu-g++'
assert (root/'C/overlay/ggml/src/ggml-cpu/ops.cpp').read_bytes()==(old/'C/overlay/ggml/src/ggml-cpu/ops.cpp').read_bytes()
assert (root/'C/overlay/ggml/src/ggml-cpu/spine-k1-gdn-prefill-r2.h').read_bytes()==(old/'C/overlay/ggml/src/ggml-cpu/spine-k1-gdn-prefill-r2.h').read_bytes()
def run(args,log,env=None):
 with (root/log).open('w') as f:subprocess.run(list(map(str,args)),stdout=f,stderr=subprocess.STDOUT,check=True,env=env,timeout=1800)
binary=root/'test-gdn-r2'
run([compiler,'-O2','-std=c++17','-march=rv64gcv_zfh_zvfh',root/'C/test-gdn-r2.cpp','-I'+str(repo/'lab/local-candidates-final-20261008/test-bundle/source/ggml/include'),'-L'+str(old/'r2-lib'),'-L'+str(build/'bin'),'-lggml-cpu','-lggml-base','-pthread','-o',binary],'fixture-build.log')
for name in ('original','r2'):
 env={k:v for k,v in os.environ.items() if not k.startswith('SPINE_')};env['LD_LIBRARY_PATH']=str(old/(name+'-lib'))+':'+str(build/'bin')
 run(['qemu-riscv64','-L',repo/'lab/toolchain/toolchain/riscv/sysroot','-cpu','rv64,v=true,vlen=256,elen=64,zfh=true,zvfh=true',binary,'--dump',root/(name+'.bin')],name+'-numeric.log',env)
 text=(root/(name+'-numeric.log')).read_text();assert 'PASS: 158' in text;assert text.count('K1_GDN_THREADS actual=4 plan=4')==158
assert (root/'original.bin').read_bytes()==(root/'r2.bin').read_bytes()
(root/'local-checks.json').write_text(json.dumps({'status':'pass','cases_per_library':158,'actual_threads':4,'original_control_equal':True,'candidate_inline_bitwise_equal':True,'k1_performance':'unverified'},indent=2)+'\n')
