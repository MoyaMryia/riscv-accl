import json, os, shlex, subprocess, sys
from pathlib import Path
repo=Path('/home/moyamryia/Projects/riscv-accl')
sys.path.insert(0,str(repo/'spacemit/bench/local-candidates'))
import board
root=Path(__file__).resolve().parent
build=repo/'lab/local-candidates-final-20261008/build-rvv'
src=repo/'lab/local-candidates-final-20261008/test-bundle/source'
recipe=next(r for r in json.loads((build/'compile_commands.json').read_text()) if r['file'].endswith('/ops.cpp'))
compiler=shlex.split(recipe['command'])[0]
link=subprocess.check_output(['ninja','-C',str(build),'-t','commands','bin/libggml-cpu.so.0.16.0'],text=True).splitlines()[-1]
def run(args,label,env=None):
    with (root/(label+'.log')).open('w') as f:
        subprocess.run(list(map(str,args)),cwd=build,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=1800)
for name,original in [('original',repo/'lab/local-reference/source-a990751-clean/ggml/src/ggml-cpu/ops.cpp'),('r2',root/'C/overlay/ggml/src/ggml-cpu/ops.cpp')]:
    obj=root/(name+'-ops.o')
    args=board.ime.compile_argv(recipe['command'],original,obj,src/'ggml/src/ggml-cpu')
    args.insert(1,'-I'+str(repo/'spacemit/bench'))
    run(args,name+'-compile')
    directory=root/(name+'-lib');directory.mkdir()
    lib=directory/'libggml-cpu.so.0.16.0'
    run(board.ssm.rewrite_link(link,lib,{'/ops.cpp.o':obj}),name+'-link')
    for suffix in ('.so','.so.0'):(directory/('libggml-cpu'+suffix)).symlink_to(lib.name)
    if name=='r2':
        run([Path(compiler).with_name('riscv64-unknown-linux-gnu-objdump'),'-d','-C',obj],'r2-assembly')
binary=root/'test-gdn-r2'
run([compiler,'-O2','-std=c++17','-march=rv64gcv_zfh_zvfh',root/'C/test-gdn-r2.cpp','-I'+str(src/'ggml/include'),'-L'+str(root/'r2-lib'),'-L'+str(build/'bin'),'-lggml-cpu','-lggml-base','-pthread','-o',binary],'fixture-build')
qemu=['qemu-riscv64','-L',repo/'lab/toolchain/toolchain/riscv/sysroot','-cpu','rv64,v=true,vlen=256,elen=64,zfh=true,zvfh=true']
summary={'k1_performance':'unverified','results':{}}
for name in ('original','r2'):
    env={k:v for k,v in os.environ.items() if not k.startswith('SPINE_')}
    env.update(LD_LIBRARY_PATH=str(root/(name+'-lib'))+':'+str(build/'bin'),SPINE_K1_TRACE='1')
    run([*qemu,binary,'--dump',root/(name+'.bin')],name+'-numeric',env)
    text=(root/(name+'-numeric.log')).read_text()
    if 'PASS: 158' not in text:raise ValueError('numeric count differs')
    if name=='r2' and 'SPINE_GDN_PREFILL_R2: retained two state segments' not in text:raise ValueError('revision path is absent')
    summary['results'][name]={'dump_sha256':board.digest(root/(name+'.bin')),'pass':True}
if summary['results']['original']['dump_sha256']!=summary['results']['r2']['dump_sha256']:raise ValueError('original control differs')
(root/'local-checks.json').write_text(json.dumps(summary,indent=2)+'\n')
