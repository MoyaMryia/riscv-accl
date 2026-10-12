#!/usr/bin/env python3
"""Compile and test the isolated candidates without a board."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess

import prepare

HERE = prepare.HERE
REPO = prepare.REPO


def run(argv, log, env=None, cwd=None):
    with log.open('w') as output:
        subprocess.run(list(map(str, argv)), stdout=output, stderr=subprocess.STDOUT,
                       env=env, cwd=cwd, check=True, timeout=1800)


def check(source, root, rvv, reference_lib):
    if root.exists():
        raise ValueError('destination exists: ' + str(root))
    root.mkdir(parents=True)
    for kind in ('control', 'A1', 'B1', 'C', 'D', 'test-bundle'):
        prepare.generate(source, root/kind, kind, kind == 'test-bundle')
    src = root/'test-bundle/source'
    summary = {'k1_performance': 'unverified', 'results': {}, 'artifacts_sha256': {}}
    modes = ['native', 'rvv'] if rvv else ['native']
    for mode in modes:
        build = root/('build-'+mode)
        compiler = Path('/usr/bin/g++') if mode == 'native' else REPO/'lab/toolchain/toolchain/riscv/bin/riscv64-unknown-linux-gnu-g++'
        cc = compiler.with_name('gcc') if mode == 'native' else compiler.with_name('riscv64-unknown-linux-gnu-gcc')
        options = ['-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
                   '-DGGML_CCACHE=OFF', '-DGGML_NATIVE=OFF', '-DGGML_CPU_REPACK=OFF', '-DGGML_OPENMP=OFF']
        options += ['-DLLAMA_BUILD_'+s+'=OFF' for s in ('COMMON','TESTS','EXAMPLES','TOOLS','APP','SERVER','UI')]
        options += ['-DCMAKE_C_COMPILER='+str(cc), '-DCMAKE_CXX_COMPILER='+str(compiler)]
        if mode == 'rvv':
            options += ['-DCMAKE_SYSTEM_NAME=Linux', '-DCMAKE_SYSTEM_PROCESSOR=riscv64',
                        '-DGGML_RVV=ON', '-DGGML_RV_ZFH=ON', '-DGGML_RV_ZVFH=ON']
        else:
            options += ['-DGGML_'+s+'=OFF' for s in ('AVX','AVX2','AVX512','FMA','F16C','BMI2','SSE42')]
        run(['cmake','-S',src,'-B',build,'-G','Ninja',*options], root/(mode+'-configure.log'))
        run(['cmake','--build',build,'--target','ggml-cpu','-j','4'], root/(mode+'-build.log'))
        objdump = Path('/usr/bin/objdump') if mode == 'native' else compiler.with_name('riscv64-unknown-linux-gnu-objdump')
        objects = list(build.glob('**/ops.cpp.o'))
        if len(objects) != 1:
            raise ValueError('operator object not unique')
        run([objdump,'-d','-C',objects[0]],root/(mode+'-ops-assembly.txt'))
        for artifact in [objects[0],*build.glob('bin/*.so.*')]:
            if artifact.is_symlink(): continue
            summary['artifacts_sha256'][str(artifact.relative_to(root))] = prepare.digest(artifact.read_bytes())
        recipes = json.loads((build/'compile_commands.json').read_text())
        for kind in ('A1','B1','C','D'):
            for relative in (prepare.OPS, prepare.CPU, 'src/models/delta-net-base.cpp', 'src/models/qwen35.cpp'):
                candidate = root/kind/'overlay'/relative
                if not candidate.exists():
                    continue
                recipe, = [r for r in recipes if r['file'] == str(src/relative)]
                argv = shlex.split(recipe['command'])
                index = argv.index('-o')
                del argv[index:index+2]
                argv[argv.index('-c')] = '-fsyntax-only'
                argv[argv.index(str(src/relative))] = str(candidate)
                argv.insert(1, '-I'+str(candidate.parent))
                argv.insert(2, '-I'+str((src/relative).parent))
                run(argv, root/(mode+'-'+kind+'-'+candidate.name+'.syntax.log'), cwd=build)
        prefix = []
        if mode == 'rvv':
            prefix = ['qemu-riscv64','-L',REPO/'lab/toolchain/toolchain/riscv/sysroot',
                      '-cpu','rv64,v=true,vlen=256,elen=64,zfh=true,zvfh=true']
        env = {k:v for k,v in os.environ.items() if not k.startswith(('SPINE_', 'SPACEMIT_'))}
        env.update(LD_LIBRARY_PATH=str(build/'bin'), SPINE_K1_TRACE='1')
        fixtures = [('attention',HERE/'test-attention.cpp'), ('conv-silu',HERE/'test-conv-silu.cpp'),
                    ('ssm',HERE.parent/'test-k1-ssm-conv.cpp'), ('gdn',HERE.parent/'test-k1-gdn.cpp')]
        for name, path in fixtures:
            binary = root/(name+'-'+mode)
            flags = ['-march=rv64gcv_zfh_zvfh'] if mode == 'rvv' else []
            run([compiler,'-O2','-std=c++17',*flags,path,'-I'+str(src/'ggml/include'),
                 '-I'+str(HERE.parent),'-L'+str(build/'bin'),'-lggml-cpu','-lggml-base','-o',binary],
                root/(name+'-'+mode+'.compile.log'))
            args = []
            if name == 'ssm':
                args = ['3','--dump',root/(name+'-'+mode+'.bin')]
            if name == 'attention':
                args = ['--dump',root/(name+'-'+mode+'.bin')]
            local_env = dict(env, SPINE_GDN_PREFILL='1', SPINE_K1_SSM_CONV='3')
            log = root/(name+'-'+mode+'.log')
            run([*prefix,binary,*args], log, local_env)
            text = log.read_text()
            expected = {'attention':'PASS: 95 ', 'conv-silu':'PASS: 144 ', 'ssm':'PASS: 432 ', 'gdn':'PASS: 158 '}[name]
            if expected not in text:
                raise ValueError('test result absent: '+str(log))
            if name == 'attention' and mode == 'rvv':
                if not all('path='+p in text for p in ('A1','B1','reference')):
                    raise ValueError('attention path evidence absent')
            if name == 'conv-silu' and 'result=paired' not in text:
                raise ValueError('pair path evidence absent')
            if name == 'gdn' and mode == 'rvv' and 'SPINE_GDN_PREFILL: scalar-gate K1 RVV fusion enabled' not in text:
                raise ValueError('GDN path evidence absent')
            summary['results'][name+'-'+mode] = next(line for line in text.splitlines() if line.startswith('PASS:'))
        if mode == 'native' and reference_lib:
            original = dict(env, LD_LIBRARY_PATH=str(reference_lib))
            original_dump = root/'attention-original.bin'
            run([root/'attention-native','--dump',original_dump], root/'attention-original.log', original)
            if prepare.digest(original_dump.read_bytes()) != prepare.digest((root/'attention-native.bin').read_bytes()):
                raise ValueError('original attention output differs')
            for label, path, arm_env, flag in (
                    ('original',original_dump,original,'0'),
                    ('control',root/'ssm-control.bin',env,'0')):
                if label == 'original': path = root/'ssm-original.bin'
                run([root/'ssm-native',flag,'--dump',path],root/('ssm-'+label+'.log'),arm_env)
            hashes = {prepare.digest((root/name).read_bytes()) for name in ('ssm-original.bin','ssm-control.bin','ssm-native.bin')}
            if len(hashes) != 1:
                raise ValueError('original/control/hybrid convolution differs')
            summary['results']['original-native'] = 'attention partials, convolution and history match the original library'
    for path in sorted(root.glob('*')):
        if path.is_file(): summary['artifacts_sha256'][path.name] = prepare.digest(path.read_bytes())
    (root/'checks.json').write_text(json.dumps(summary, indent=2)+'\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--source', type=Path, default=REPO/'lab/local-reference/source-a990751-clean')
    parser.add_argument('--rvv', action='store_true')
    parser.add_argument('--reference-lib', type=Path)
    args = parser.parse_args()
    result = check(args.source.resolve(), args.destination.resolve(), args.rvv,
                   args.reference_lib.resolve() if args.reference_lib else None)
    print(json.dumps(result['results'], indent=2))
