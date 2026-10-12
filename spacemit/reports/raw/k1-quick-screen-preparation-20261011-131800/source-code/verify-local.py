#!/usr/bin/env python3
"""在本机检查原型，不派发板端任务。"""
import argparse
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
spec=importlib.util.spec_from_file_location('quick_run',HERE/'run.py')
run=importlib.util.module_from_spec(spec); spec.loader.exec_module(run)


def main(payload, out):
    if out.exists(): raise ValueError('destination exists')
    out.mkdir(parents=True)
    commands=[]
    summary={'k1_performance':'unverified','ime_execution':'pending-K1','checks':{}}
    source=REPO/'lab/local-reference/source-a990751-clean'
    build=REPO/'lab/local-candidates-final-20261008/build-rvv'
    recipes=json.loads((build/'compile_commands.json').read_text())
    link=subprocess.check_output(['ninja','-C',build,'-t','commands','bin/libggml-cpu.so.0.16.0'],text=True).splitlines()[-1]
    def command(args,label,env=None):
        args=list(map(str,args)); commands.append({'argv':args,'label':label})
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        with (out/(label+'.log')).open('w') as stream:
            subprocess.run(args,cwd=build,env=env,stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=600)
        return (out/(label+'.log')).read_text(errors='replace')
    def recipe(relative):
        found=[r for r in recipes if r['file'].endswith('/'+relative)]
        if len(found)!=1: raise ValueError('compile recipe differs')
        return found[0]
    compiler=shlex.split(recipe('ops.cpp')['command'])[0]
    command(['g++','-O2','-std=c++17','-ffp-contract=off','-fsanitize=address,undefined','-fno-omit-frame-pointer',
        payload/'conv.cpp','-pthread','-o',out/'conv-host'],'conv-host-build')
    env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0')
    text=command([out/'conv-host'],'conv-host-numeric',env)
    if 'PASS: 60 convolution cases;' not in text: raise ValueError('host count differs')
    summary['checks']['conv_host_sanitizers']=True
    summary['leak_check']='disabled because LeakSanitizer cannot use ptrace in this sandbox'
    command([compiler,'-O3','-std=c++17','-ffp-contract=off','-march=rv64gcv_zfh_zvfh',
        payload/'conv.cpp','-pthread','-o',out/'conv-rvv'],'conv-rvv-build')
    qemu=['qemu-riscv64','-L',REPO/'lab/toolchain/toolchain/riscv/sysroot',
        '-cpu','rv64,v=true,vlen=256,elen=64,zfh=true,zvfh=true']
    text=command([*qemu,out/'conv-rvv'],'conv-rvv-numeric')
    if 'PASS: 60 convolution cases;' not in text: raise ValueError('RVV count differs')
    summary['checks']['conv_qemu']=True
    cpu=out/'cpu.o'; cpu_rel='ggml/src/ggml-cpu/ggml-cpu.c'
    command(run.compile_args(recipe('ggml-cpu.c')['command'],source/cpu_rel,cpu,(source/cpu_rel).parent),'cpu-build')
    hashes={}
    for arm,ops_source in (('original',source/'ggml/src/ggml-cpu/ops.cpp'),
            ('b2',payload/'B2/overlay/ggml/src/ggml-cpu/ops.cpp')):
        obj=out/(arm+'.o'); library_dir=out/arm; library_dir.mkdir()
        args=run.compile_args(recipe('ops.cpp')['command'],ops_source,obj,source/'ggml/src/ggml-cpu')
        args.insert(1,'-I'+str(ops_source.parent))
        command(args,arm+'-ops-build')
        library=library_dir/'libggml-cpu.so.0.16.0'
        command(run.link_args(link,library,{'/ops.cpp.o':obj,'/ggml-cpu.c.o':cpu}),arm+'-link')
        for suffix in ('.so','.so.0'): (library_dir/('libggml-cpu'+suffix)).symlink_to(library.name)
        if arm=='b2':
            command([compiler,'-O3','-std=c++17','-march=rv64gcv_zfh_zvfh',payload/'b2.cpp',
                '-I'+str(source/'ggml/include'),'-L'+str(library_dir),'-L'+str(build/'bin'),
                '-lggml-cpu','-lggml-base','-pthread','-o',out/'test-b2'],'b2-fixture-build')
    for arm in ('original','b2'):
        env={k:v for k,v in os.environ.items() if not k.startswith('SPINE_')}
        env.update(LD_LIBRARY_PATH=str(out/arm)+':'+str(build/'bin'),SPINE_K1_TRACE='1')
        dump=out/(arm+'.bin')
        text=command([*qemu,out/'test-b2','--dump',dump],arm+'-numeric',env)
        if 'PASS: 159 B2 cases;' not in text: raise ValueError('B2 count differs')
        if arm=='b2':
            for tile in (8,16):
                for worker in range(4):
                    if f'QUICK_B2 tile={tile} worker={worker} workers=4' not in text:
                        raise ValueError('B2 worker trace differs')
        hashes[arm]=run.sha(dump)
    if len(set(hashes.values()))!=1: raise ValueError('B2 original dumps differ')
    summary['checks']['b2_qemu']={'cases':159,'dump_sha256':hashes}
    args=run.compile_args(recipe('ops.cpp')['command'],payload/'ime-schedule.cpp',out/'ime-schedule.s',
        source/'ggml/src/ggml-cpu/spacemit')
    args.insert(1,'-DRISCV64_SPACEMIT_IME1'); args.remove('-c'); args.insert(1,'-S')
    command(args,'ime-assembly-output')
    summary['checks']['ime_cpp_to_assembly']=True
    includes=[payload,source/'ggml/include',source/'ggml/src',source/'include',
        source/'ggml/src/ggml-cpu/spacemit']
    for name in ('ime','ime-graph'):
        command([compiler,'-O3','-std=c++17','-march=rv64gcv_zfh_zvfh',
            *('-I'+str(p) for p in includes),'-c',payload/(name+'.cpp'),'-o',out/(name+'-fixture.o')],
            name+'-fixture-compile')
    summary['checks']['ime_fixture_compile']=True
    text=(payload/'ime-schedule.cpp').read_text()
    def macro(name):
        part=text[text.index('#define '+name+' '):].split('\n\n',1)[0]
        return [line.strip() for line in re.findall(r'"([^"\n]+)\\n\\t"',part)]
    old, new=macro('K1_M1_K32_LOAD'), macro('QUICK_M1_LOAD')
    if Counter(old)!=Counter(new) or old==new: raise ValueError('IME instruction set or order differs')
    def evaluate(instructions,seed):
        memory=bytes((i*73+seed*31)%256 for i in range(2048))
        registers={f'v{i}':[0]*32 for i in range(16)}
        pointers={f's{i}':i*256 for i in range(1,7)}
        vl=32
        for line in instructions:
            op,args=line.split(None,1); args=[a.strip() for a in args.split(',')]
            if op=='vsetvli': vl=8 if args[-1]=='mf4' else 32
            elif op=='vle8.v':
                pos=pointers[args[1].strip('()')]
                registers[args[0]][:vl]=memory[pos:pos+vl]
            elif op=='addi': pointers[args[0]]=pointers[args[1]]+int(args[2])
            elif op in ('vand.vi','vsrl.vi'):
                source=registers[args[1]][:vl]; value=int(args[2])
                registers[args[0]][:vl]=[x&value if op=='vand.vi' else x>>value for x in source]
            else: raise ValueError('unsupported IME load instruction')
        return registers,pointers,vl
    for seed in range(64):
        if evaluate(old,seed)!=evaluate(new,seed): raise ValueError('IME load dataflow differs')
    summary['checks']['ime_load_dataflow']={'seeds':64,'instructions_preserved':True}
    # 门槛必须区分明显收益、退化、噪声和无效输入。
    assert run.gate([10.0]*6,[9.0]*6)['advance']
    assert run.gate([10.0]*6,[11.0]*6)['clear_regression']
    assert not run.gate([9.0,11.0]*3,[9.5]*6)['advance']
    for invalid in ([float('nan')]*6,[0.0]*6,[1.0]*5):
        try: run.gate([10.0]*6,invalid)
        except ValueError: pass
        else: raise ValueError('invalid samples passed')
    summary['checks']['gate_cases']=True
    (out/'local-checks.json').write_text(json.dumps(summary,indent=2)+'\n')
    receipts={str(p.relative_to(out)):run.sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
    (out/'SHA256SUMS').write_text(''.join(value+'  '+name+'\n' for name,value in receipts.items()))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('payload',type=Path); parser.add_argument('output',type=Path)
    args=parser.parse_args(); main(args.payload.resolve(),args.output.resolve())
