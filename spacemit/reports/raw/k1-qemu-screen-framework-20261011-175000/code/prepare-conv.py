#!/usr/bin/env python3
"""为已准备的卷积原型生成固定工作量计划。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(out):
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = HERE.parent/'quick-screen/conv.cpp'
    common = source.with_name('common.h')
    original = source.read_text()
    if original.count('    void step(') != 1: raise ValueError('source boundary differs')
    (out/'conv-kernel.cpp').write_text(original.replace('    void step(', '    __attribute__((noinline)) void step('))
    shutil.copy2(common, out/'common.h')
    shutil.copy2(HERE/'conv-profile.cpp', out/'conv-profile.cpp')
    compiler = REPO/'lab/toolchain/toolchain/riscv/bin/riscv64-unknown-linux-gnu-g++'
    binary = out/'conv-profile'
    command = list(map(str, [compiler, '-O3', '-g', '-static', '-fno-pie', '-no-pie', '-ffp-contract=off',
        '-march=rv64gcv_zfh_zvfh', '-std=c++17', out/'conv-profile.cpp', '-pthread', '-o', binary]))
    (out/'build-command.json').write_text(json.dumps(command, indent=2)+'\n')
    with (out/'build.log').open('w') as stream:
        subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=120)
    nm = compiler.with_name('riscv64-unknown-linux-gnu-nm')
    symbols = subprocess.check_output([nm, '-S', '--defined-only', binary], text=True)
    (out/'symbols.log').write_text(symbols)
    found = [line.split()[-1] for line in symbols.splitlines() if '_ZN4Conv4stepE' in line]
    if len(found) != 1: raise ValueError('kernel symbol is not unique')
    cases = []
    for c in (6144, 8192):
        for t in (8, 32):
            case = {'id': f'conv-C{c}-T{t}', 'correctness': 'complete input/output/state and guards', 'roi_threads': 4}
            for key, arm in (('control', 0), ('candidate', 1)):
                case[key] = {'elf': str(binary), 'sha256': sha(binary), 'symbol': found[0],
                    'args': [str(c), str(t), str(arm), '{dump}']}
            cases.append(case)
    plan = {'schema': 1, 'scope': 'four-thread split-source convolution prototype, one call per arm',
        'sources': {str(p): sha(p) for p in (source, common, HERE/'conv-profile.cpp', compiler,
            out/'conv-kernel.cpp', out/'common.h', out/'conv-profile.cpp')},
        'qemu': shutil.which('qemu-riscv64'), 'header': '/usr/local/include/qemu-plugin.h',
        'cpu': 'rv64,v=true,vlen=256,elen=64,zfh=true,zvfh=true', 'nm': str(nm),
        'timeout_seconds': 120, 'cases': cases}
    (out/'plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    (out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(out.iterdir()) if p.is_file()))
    print(out/'plan.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    main(parser.parse_args().output)
