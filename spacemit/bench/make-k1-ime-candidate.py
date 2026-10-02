#!/usr/bin/env python3
"""Add opt-in scheduling experiments to the audited IME1 M4 Q4_0 kernel."""
import argparse
import difflib
from pathlib import Path


def assembly(instructions):
    return '\n'.join('                "' + op.ljust(45) + '\\n\\t"' for op in instructions)


def step(scheduled):
    a = ['vle8.v v10, (a1)', 'addi a1, a1, 32', 'vle8.v v11, (a1)', 'addi a1, a1, 32']
    loads = [op for i in range(4) for op in (f'vle8.v v{6+i}, (s{1+i})', f'addi s{1+i}, s{1+i}, 128')]
    low = [f'vand.vi v{2+i}, v{6+i}, 15' for i in range(4)]
    high = [f'vsrl.vi v{6+i}, v{6+i}, 4' for i in range(4)]
    bias = [f'vadd.vi v{i}, v{i}, -8' for i in range(2, 10)]
    dots = [f'vmadot v{16+2*i}, v10, v{2+i}' for i in range(4)]
    high_dots = [f'vmadot v{16+2*i}, v11, v{6+i}' for i in range(4)]
    if not scheduled:
        return loads + low + high + a + bias + dots + high_dots
    result = a.copy()
    for i in range(4):
        result += loads[2*i:2*i+2] + [low[i], high[i], bias[i], bias[i+4], dots[i]]
    return result + high_dots


def generate(original):
    begin = original.index('template <bool HasZeroPoint>\nvoid SQ4BitGemmM4Kernel_')
    end = original.index('template <bool HasZeroPoint>\nvoid SQ4BitGemmM1Kernel_', begin)
    region = original[begin:end].rstrip()
    split = region.index('    } else {') + len('    } else {')
    body = region[split:region.rfind('\n    }\n}')]
    assert body.count('LOAD_B_16x8x2') == 1
    loop_start = body.index('                "BLOCK_INNER_LOOP%=')
    loop_end = body.index('\n\n                LOAD_SCALE_4x16_FP16_OPT', loop_start)
    decl = region[region.index('void SQ4BitGemmM4Kernel_'):region.index(' {', region.index('void SQ4BitGemmM4Kernel_'))]
    prefix = '\n    const size_t INNER = BlkLen / 16;\n    size_t LDC = ldc * sizeof(float);\n    float tmp[4 * 16];\n'
    helpers = []
    for mode in (1, 2, 3):
        ops = ['vsetvli t0, zero, e8, m1']
        if mode == 1:
            ops = ['BLOCK_INNER_LOOP%=:'] + ops + step(True) + ['addi t2, t2, -1', 'bnez t2, BLOCK_INNER_LOOP%=']
        else:
            ops += step(mode == 3) * 2
        candidate = body[:loop_start] + assembly(ops) + body[loop_end:]
        signature = decl.replace('SQ4BitGemmM4Kernel_CompInt8_ScaleFp16_Impl', f'k1_ime_m4_mode{mode}')
        helpers.append('static ' + signature + ' {' + prefix + candidate + '\n}\n')
    result = original[:end] + '\n// K32 experiments retain each accumulator\'s dot and scale order.\n' + '\n'.join(helpers) + '\n' + original[end:]
    begin = result.index('size_t gemm_kernel_i8i4(')
    brace = result.index('{', begin)
    signature = result[begin:brace].strip()
    result = result[:begin] + result[begin:].replace('size_t gemm_kernel_i8i4(', 'static size_t k1_original_gemm_kernel_i8i4(', 1)
    insert = result.index('\nsize_t gemm_kernel_i8i8(', begin)
    args = 'blk_len, quant_a_ptr, quant_b_data, quant_b_zp, c_ptr, count_m, count_n, k_blks, ldc'
    api = signature.replace('size_t gemm_kernel_i8i4(', 'extern "C" size_t spine_k1_ime_m4_test(int mode, ')
    api += ''' {
    if (blk_len == 32 && count_m >= 4 && count_n > 0 && count_n % 16 == 0 && quant_b_zp == nullptr && mode > 0 && mode <= 3) {
        if (mode == 1) k1_ime_m4_mode1(blk_len, quant_a_ptr, quant_b_data, c_ptr, count_n, k_blks, ldc);
        if (mode == 2) k1_ime_m4_mode2(blk_len, quant_a_ptr, quant_b_data, c_ptr, count_n, k_blks, ldc);
        if (mode == 3) k1_ime_m4_mode3(blk_len, quant_a_ptr, quant_b_data, c_ptr, count_n, k_blks, ldc);
        return 4;
    }
    return k1_original_gemm_kernel_i8i4(''' + args + ''');
}
'''
    wrapper = signature + ''' {
    static const int mode = [] {
        const char * value = getenv("SPINE_IME_M4_SCHEDULE");
        return value && value[0] >= '1' && value[0] <= '3' && value[1] == 0 ? value[0] - '0' : 0;
    }();
    if (blk_len == 32 && count_m >= 4 && count_n > 0 && count_n % 16 == 0 && quant_b_zp == nullptr) {
        static const bool logged = [] {
            fprintf(stderr, "SPINE_IME_M4_SCHEDULE: mode=%d Q4_0 M4 K32 enabled\\n", mode);
            return true;
        }();
        (void) logged;
    }
    return spine_k1_ime_m4_test(mode, ''' + args + ''');
}
'''
    result = result[:insert] + '\n' + api + '\n' + wrapper + result[insert:]
    return result.replace('#include <algorithm>', '#include <algorithm>\n#include <cstdio>\n#include <cstdlib>', 1)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('baseline', type=Path)
    p.add_argument('output', type=Path)
    args = p.parse_args()
    old = args.baseline.read_text(); new = generate(old)
    args.output.write_text(new)
    args.output.with_suffix('.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
        fromfile='a/ggml/src/ggml-cpu/spacemit/ime1_kernels.cpp', tofile='b/ggml/src/ggml-cpu/spacemit/ime1_kernels.cpp')))
