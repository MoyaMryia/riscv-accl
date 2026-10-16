#!/usr/bin/env python3
"""生成只移动独立标量指令的 IME M4 候选。"""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import shutil

PIN = 'a990751d55a4c54acf2bb77d44282c2093652359'
KERNEL_SHA256 = '5c2a5465101f0699c8d28f64b9720f1b2fc703c99dc4d3d2a85aee92bfb4ea8e'
RELATIVE = 'ggml/src/ggml-cpu/spacemit/ime1_kernels.cpp'


def assembly(ops):
    return '\n'.join('                "' + op.ljust(45) + '\\n\\t"' for op in ops)


def instructions():
    control = ['vsetvli t0, zero, e8, m1']
    for i in range(4):
        control += [f'vle8.v v{6+i}, (s{1+i})', f'addi s{1+i}, s{1+i}, 128']
    control += [f'vand.vi v{2+i}, v{6+i}, 15' for i in range(4)]
    control += [f'vsrl.vi v{6+i}, v{6+i}, 4' for i in range(4)]
    control += ['vsetvli t0, zero, e8, m1', 'vle8.v v10, (a1)',
                'addi a1, a1, 32', 'vle8.v v11, (a1)', 'addi a1, a1, 32']
    control += [f'vadd.vi v{i}, v{i}, -8' for i in range(2, 10)]
    control += [f'vmadot v{16+2*i}, v10, v{2+i}' for i in range(4)]
    control += [f'vmadot v{16+2*i}, v11, v{6+i}' for i in range(4)]
    control += ['addi t2, t2, -1', 'bnez t2, BLOCK_INNER_LOOP%=']
    candidate = []
    for op in control:
        if op.startswith('addi s') or op == 'addi t2, t2, -1':
            continue
        candidate.append(op)
        if op.startswith('vand.vi'):
            i = int(op.split()[1].rstrip(',')[1:]) - 2
            candidate.append(f'addi s{1+i}, s{1+i}, 128')
        if op == 'vadd.vi v8, v8, -8':
            candidate.append('addi t2, t2, -1')
    if [s for s in control if s.startswith('v')] != [s for s in candidate if s.startswith('v')]:
        raise ValueError('向量指令顺序不同。')
    if sorted(control) != sorted(candidate):
        raise ValueError('指令集合不同。')
    return control, candidate


def generate(original):
    if hashlib.sha256(original.encode()).hexdigest() != KERNEL_SHA256:
        raise ValueError('基线内核身份不同。')
    begin = original.index('template <bool HasZeroPoint>\nvoid SQ4BitGemmM4Kernel_')
    end = original.index('template <bool HasZeroPoint>\nvoid SQ4BitGemmM1Kernel_', begin)
    region = original[begin:end].rstrip()
    signature_start = region.index('void SQ4BitGemmM4Kernel_')
    signature = region[signature_start:region.index(' {', signature_start)]
    body = region[region.index('    } else {') + len('    } else {'):region.rfind('\n    }\n}')]
    start = body.index('                "BLOCK_INNER_LOOP%=')
    stop = body.index('\n\n                LOAD_SCALE_4x16_FP16_OPT', start)
    if body[start:stop].count('LOAD_B_16x8x2') != 1:
        raise ValueError('原内循环不同。')
    _, candidate = instructions()
    body = body[:start] + assembly(['BLOCK_INNER_LOOP%=:'] + candidate) + body[stop:]
    helper = 'static ' + signature.replace('SQ4BitGemmM4Kernel_CompInt8_ScaleFp16_Impl', 'k1_ime_scalar_schedule')
    helper += ' {\n    const size_t INNER = BlkLen / 16;\n    size_t LDC = ldc * sizeof(float);\n    float tmp[4 * 16];\n'
    helper += body + '\n}\n\n'
    result = original[:end] + helper + original[end:]
    begin = result.index('size_t gemm_kernel_i8i4(')
    brace = result.index('{', begin)
    signature = result[begin:brace].strip()
    result = result[:begin] + result[begin:].replace('size_t gemm_kernel_i8i4(', 'static size_t k1_original_gemm_kernel_i8i4(', 1)
    insert = result.index('\nsize_t gemm_kernel_i8i8(', begin)
    args = 'blk_len, quant_a_ptr, quant_b_data, quant_b_zp, c_ptr, count_m, count_n, k_blks, ldc'
    api = signature.replace('size_t gemm_kernel_i8i4(', 'extern "C" size_t spine_k1_ime_m4_test(int mode, ')
    api += ''' {
    if (mode == 1 && blk_len == 32 && count_m >= 4 && count_n > 0 && count_n % 16 == 0 && quant_b_zp == nullptr) {
        k1_ime_scalar_schedule(blk_len, quant_a_ptr, quant_b_data, c_ptr, count_n, k_blks, ldc);
        return 4;
    }
    return k1_original_gemm_kernel_i8i4(''' + args + ''');
}
'''
    wrapper = signature + ''' {
    static const int mode = [] {
        const char * value = getenv("SPINE_IME_SCALAR_SCHEDULE");
        return value && value[0] == '1' && value[1] == 0 ? 1 : 0;
    }();
    if (blk_len == 32 && count_m >= 4 && count_n > 0 && count_n % 16 == 0 && quant_b_zp == nullptr) {
        static const bool logged = [] {
            fprintf(stderr, "SPINE_IME_SCALAR_SCHEDULE: mode=%d Q4_0 M4 K32 enabled\\n", mode);
            return true;
        }();
        (void) logged;
    }
    return spine_k1_ime_m4_test(mode, ''' + args + ''');
}
'''
    result = result[:insert] + '\n' + api + '\n' + wrapper + result[insert:]
    return result.replace('#include <algorithm>', '#include <algorithm>\n#include <cstdio>\n#include <cstdlib>', 1)


def fixture(original):
    if hashlib.sha256(original.encode()).hexdigest() != 'a49a603edaa830af82ccff8c5b922fcfdbc8722a18050e1cd06a4bec04d9df69':
        raise ValueError('原数值测试身份不同。')
    result = re.sub(r'//[^\n]*', '', original)
    result = result.replace('const int order[6][3]={{0,4,5},{5,4,0},{4,0,5},{5,0,4},{0,5,4},{4,5,0}};',
                            'const int order[6][2]={{0,1},{1,0},{0,1},{1,0},{0,1},{1,0}};')
    result = result.replace('team.times+4)>=50', 'team.times+4)>=200')
    result = result.replace('for(int mode:{1,2,3,4,5})', 'for(int mode:{1})')
    return result.replace('five modes bitwise equal', 'one mode bitwise equal')


def bundle(destination, expected):
    bench = Path(__file__).resolve().parents[1]
    destination.mkdir(parents=True)
    for name in ('k1-ime-test.py', 'make-k1-ime-candidate.py', 'k1-fast-test.py', 'bench-lifecycle.py'):
        shutil.copyfile(bench/name, destination/name)
    for name in ('prepare.py', 'board.py'):
        shutil.copyfile(Path(__file__).resolve().parent/name, destination/name)
    (destination/'test-k1-ime.cpp').write_text(fixture((bench/'test-k1-ime.cpp').read_text()))
    shutil.copyfile(expected, destination/'expected-provenance.json')
    (destination/'run.sh').write_text('''#!/usr/bin/env bash
set -euo pipefail
SCALAR_ROOT=$1
exec >> "$SCALAR_ROOT/run.log" 2>&1
trap 'scalar_status=$?; printf "%s\\n" "$scalar_status" > "$SCALAR_ROOT/exit-status"' EXIT
timeout --signal=TERM --kill-after=20s 1200s python3 "$SCALAR_ROOT/board.py" "$SCALAR_ROOT"
''')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path, nargs='?')
    parser.add_argument('output', type=Path, nargs='?')
    parser.add_argument('--bundle', type=Path)
    parser.add_argument('--expected', type=Path)
    args = parser.parse_args()
    if args.bundle:
        if not args.expected or args.baseline or args.output:
            parser.error('--bundle 必须使用 --expected，且不能使用源码位置参数。')
        bundle(args.bundle, args.expected)
        raise SystemExit(0)
    if not args.baseline or not args.output or args.expected:
        parser.error('必须指定基线源码与输出文件。')
    original = args.baseline.read_text()
    candidate = generate(original)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(candidate)
    patch = ''.join(difflib.unified_diff(original.splitlines(True), candidate.splitlines(True), fromfile='a/'+RELATIVE, tofile='b/'+RELATIVE))
    args.output.with_suffix('.patch').write_text(patch)
    control_ops, candidate_ops = instructions()
    receipt = {'source_commit': PIN, 'baseline_sha256': hashlib.sha256(original.encode()).hexdigest(),
               'candidate_sha256': hashlib.sha256(candidate.encode()).hexdigest(),
               'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'control_instructions': control_ops, 'candidate_instructions': candidate_ops,
               'vector_order_equal': True, 'instruction_multiset_equal': True,
               'scope': '只移动四条 B 地址推进和一条循环计数指令。'}
    args.output.with_suffix('.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
