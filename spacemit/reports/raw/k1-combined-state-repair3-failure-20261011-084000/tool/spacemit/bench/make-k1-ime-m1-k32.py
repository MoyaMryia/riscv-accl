#!/usr/bin/env python3
"""Generate an opt-in fixed-two-step M1 kernel from the pinned source."""
import argparse
import hashlib
from pathlib import Path

BASELINE_SHA256 = '5c2a5465101f0699c8d28f64b9720f1b2fc703c99dc4d3d2a85aee92bfb4ea8e'


def generate(text):
    if hashlib.sha256(text.encode()).hexdigest() != BASELINE_SHA256:
        raise ValueError('M1 specialization requires the exact verified original kernel')
    start = text.index('template <bool HasZeroPoint>\nvoid SQ4BitGemmM1Kernel_')
    end = text.index('\n\n\n// ---- Q8_0', start)
    original = text[start:end]
    signature = original[original.index('void SQ4Bit'):original.index('    GGML_UNUSED(ldc);')]
    signature = signature.replace('void SQ4BitGemmM1Kernel_CompInt8_ScaleFp16_Impl',
                                  'static __attribute__((noinline)) void k1_m1_k32_fixed')
    body = original.split('    } else {\n', 1)[1]
    if not body.endswith('    }\n}'):
        raise ValueError('unexpected M1 function ending')
    body = body[:-len('    }\n}')]
    inner_label = '                "LOOP_INNER%=:                        \\n\\t"\n'
    begin = body.index(inner_label)
    branch = '                "bnez         t5, LOOP_INNER%=        \\n\\t"\n'
    finish = body.index(branch, begin)
    step = body[begin+len(inner_label):finish]
    # All loads, nibble operations, dot instructions and pointer increments stay
    # in their original order. Only the dead inner counter and branches vanish.
    step = step.replace('SQ4BIT_KERNEL_LOAD_1x8x2_4X8X4', 'K1_M1_K32_LOAD')
    body = body[:begin] + step + step + body[finish+len(branch):]
    counter = '                "addi         t5, %[INNER], 0         \\n\\t"\n'
    if body.count(counter) != 1:
        raise ValueError('unexpected inner counter')
    body = body.replace(counter, '').replace('[INNER] "r"(INNER), ', '').replace('"t5", ', '')
    macro_start = text.index('#define SQ4BIT_KERNEL_LOAD_1x8x2_4X8X4 ')
    macro_end = text.index('\n\n#define SQ4BIT_KERNEL_LOAD_ZP_', macro_start)
    macro = text[macro_start:macro_end].replace('SQ4BIT_KERNEL_LOAD_1x8x2_4X8X4', 'K1_M1_K32_LOAD')
    decrement = next(line for line in macro.splitlines(True) if 'addi         t5, t5, -1' in line)
    macro = macro.replace(decrement, '')
    helper = ('\n// Fixed K32: two original int-dot steps, one original scale/FMA per block.\n'
              + macro + '\n\n' + signature + '    GGML_UNUSED(ldc);\n' + body + '}\n#undef K1_M1_K32_LOAD\n')
    text = text[:end] + helper + text[end:]
    text = text.replace('#include <algorithm>', '#include <algorithm>\n#include <atomic>\n#include <cstdio>\n#include <cstdlib>')
    needle = 'size_t gemm_kernel_i8i4(size_t'
    if text.count(needle) != 1:
        raise ValueError('public Q4 entry point is not unique')
    text = text.replace(needle, 'static size_t k1_original_gemm_i8i4(size_t', 1)
    insert = text.index('\nsize_t gemm_kernel_i8i8(')
    wrapper = r'''
// Mode 0 preserves the original implementation; mode 1 is experimental.
static bool k1_m1_k32_eligible(size_t bl, const uint8_t *zp, size_t m, size_t n, size_t kb) {
    return bl == 32 && zp == nullptr && m == 1 && n > 0 && kb > 0;
}
extern "C" size_t spine_k1_ime_m1_test(int mode, size_t bl, const uint8_t *a,
        const uint8_t *b, const uint8_t *zp, float *c, size_t m, size_t n, size_t kb, size_t ld) {
    if (mode == 1 && k1_m1_k32_eligible(bl, zp, m, n, kb)) {
        k1_m1_k32_fixed(bl, a, b, c, n, kb, ld);
        return 1;
    }
    return k1_original_gemm_i8i4(bl, a, b, zp, c, m, n, kb, ld);
}
size_t gemm_kernel_i8i4(size_t bl, const uint8_t *a, const uint8_t *b,
        const uint8_t *zp, float *c, size_t m, size_t n, size_t kb, size_t ld) {
    static const int mode = [] {
        const char *value = std::getenv("SPINE_IME_M1_K32");
        return value && std::strcmp(value, "1") == 0 ? 1 : 0;
    }();
    if (k1_m1_k32_eligible(bl, zp, m, n, kb)) {
        static std::atomic<bool> logged{false};
        if (!logged.load(std::memory_order_relaxed) && !logged.exchange(true, std::memory_order_relaxed))
            std::fprintf(stderr, "SPINE_IME_M1_K32: mode=%d Q4_0 M1 K32 enabled\n", mode);
    }
    return spine_k1_ime_m1_test(mode, bl, a, b, zp, c, m, n, kb, ld);
}
'''
    text = text[:insert] + wrapper + text[insert:]
    text = text.replace('#include <cstdlib>', '#include <cstdlib>\n#include <cstring>')
    return text


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path); parser.add_argument('output', type=Path)
    args = parser.parse_args(); args.output.write_text(generate(args.source.read_text()))
