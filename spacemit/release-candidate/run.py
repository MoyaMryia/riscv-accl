#!/usr/bin/env python3
"""按显式配置启动固定模型，并清除继承的实验设置。"""
import argparse
import json
import os
from pathlib import Path
import package

HERE = Path(__file__).resolve().parent
CANDIDATES = ('c1', 'c2-r2', 'b1-r2')


def environment(profile, binary_dir, spert, tcm, enable=(), disable=(), trace=False):
    profiles = json.loads((HERE/'profiles.json').read_text())
    selection = dict(profiles[profile]['candidates'])
    if (enable or disable) and profile != 'experimental':
        raise ValueError('candidate overrides require profile experimental')
    if set(enable) & set(disable):
        raise ValueError('conflicting candidate switches')
    for n in enable: selection[n] = True
    for n in disable: selection[n] = False
    env = {k:v for k,v in os.environ.items() if not k.startswith(('SPINE_', 'SPACEMIT_', 'GGML_', 'LLAMA_', 'OMP_', 'GOMP_', 'KMP_')) and k not in ('LD_LIBRARY_PATH','LD_PRELOAD','LD_AUDIT')}
    env.update(SPINE_FA_WIDE_TILE='1', SPINE_FA_K1_LAYOUT='0',
        SPINE_K1_GEMM_ROUTE=str(profiles[profile]['route']),
        SPINE_K1_SSM_CONV='3' if selection['c1'] else '0',
        SPINE_GDN_PREFILL='1' if selection['c2-r2'] else '0',
        SPINE_K1_GDN_REVISION='1' if selection['c2-r2'] else '0',
        SPINE_K1_FA_GQA='1' if selection['b1-r2'] else '0',
        SPINE_K1_FA_DECODE='0', SPINE_K1_TRACE='1' if trace else '0',
        SPINE_K1_CONV_SILU='0', SPINE_IME_SCALAR_SCHEDULE='0',
        LD_LIBRARY_PATH=':'.join(str(p.resolve()) for p in (binary_dir,tcm,spert/'lib')))
    return env


def verify_binaries(build):
    record=json.loads((build/'build-receipt.json').read_text())
    if record['package'] != package.manifest()['version']:
        raise ValueError('binary package differs')
    actual={p.name for p in (build/'bin').iterdir() if p.is_file()}
    if actual!=set(record['binaries']): raise ValueError('binary file list differs')
    for n,h in record['binaries'].items():
        if package.sha(build/'bin'/n)!=h: raise ValueError('binary differs: '+n)
    return record


def verify_model(model):
    digest=package.sha(model)
    matches=[n for n,m in package.manifest()['models'].items() if m['sha256']==digest]
    if len(matches)!=1: raise ValueError('model differs from manifest')
    return matches[0],digest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,default=HERE/'build')
    p.add_argument('--model',type=Path,required=True)
    p.add_argument('--profile',choices=list(json.loads((HERE/'profiles.json').read_text())),default='optimized')
    p.add_argument('--enable',action='append',choices=CANDIDATES,default=[])
    p.add_argument('--disable',action='append',choices=CANDIDATES,default=[])
    p.add_argument('--spert',type=Path,default=Path(os.environ.get('K1_SPERT_DIR',str(Path.home()/'Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2'))))
    p.add_argument('--tcm',type=Path,default=Path(os.environ.get('K1_TCM_DIR',str(Path.home()/'Projects/llm-bench/.toolchain/spine-tcm'))))
    p.add_argument('--port',type=int,default=8080)
    p.add_argument('--trace',action='store_true')
    p.add_argument('--describe',action='store_true')
    p.add_argument('--receipt',type=Path)
    args=p.parse_args()
    try:
        build=args.build.resolve()
        env=environment(args.profile,build/'bin',args.spert,args.tcm,args.enable,args.disable,args.trace)
        record=verify_binaries(build)
        model_id,digest=verify_model(args.model)
        dependencies={Path(n).name:h for n,h in record['dependencies'].items()}
        for n,h in dependencies.items():
            paths=[d/n for d in (args.tcm,args.spert/'lib') if (d/n).is_file()]
            if not paths or not any(package.sha(f)==h for f in paths): raise ValueError('runtime differs: '+n)
        argv=[str(build/'bin/llama-server'),'-m',str(args.model.resolve()),'--alias','local','-t','4','-tb','4',
            '-c','6144','--parallel','1','-b','32','-ub','32','-fa','on','-ctk','f16','-ctv','f16',
            '-ngl','0','--no-context-shift','--host','127.0.0.1','--port',str(args.port)]
        receipt=dict(version=package.manifest()['version'],profile=args.profile,model=model_id,model_sha256=digest,
            argv=argv,environment={k:v for k,v in env.items() if k.startswith('SPINE_') or k=='LD_LIBRARY_PATH'},trace=args.trace)
        if args.receipt: args.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
        if args.describe:
            print(json.dumps(receipt,indent=2)); return
        if not os.environ.get('TMUX') or os.environ.get('K1_PACKAGE_LOCK_FD')!='9': raise ValueError('use with-lock.sh in tmux')
        os.fstat(9)
        os.execve(argv[0],argv,env)
    except (ValueError,OSError) as error:
        p.exit(1,str(error)+'\n')

if __name__=='__main__': main()
