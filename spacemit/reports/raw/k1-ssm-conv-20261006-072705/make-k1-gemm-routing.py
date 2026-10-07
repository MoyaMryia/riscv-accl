#!/usr/bin/env python3
"""Generate an opt-in Q4_0 staging bypass in the verified production IME path."""
import argparse
from pathlib import Path


def generate(text):
    anchor = '        void *        tcm_buffer      = spacemit_spert_shared_buffer(&tcm_buffer_size);\n'
    if text.count(anchor) != 1 or 'SPINE_K1_GEMM_ROUTE' in text:
        raise ValueError('unexpected production GEMM source')
    addition = r'''
        // Experimental routing only: use the existing direct-memory branch.
        // Quantization, packed weights and IME kernels retain their arithmetic.
        static const int k1_route = [] {
            const char * value = std::getenv("SPINE_K1_GEMM_ROUTE");
            return value && value[0] >= '0' && value[0] <= '3' && value[1] == '\0'
                       ? value[0] - '0' : 0;
        }();
        if constexpr (std::is_same_v<BLOC_TYPE, block_q4_0> && INTER_SIZE == 32 && NB_COLS == 16) {
            const bool eligible = global_spine_env_info.use_ime1 && gemm_k % 32 == 0 && gemm_n % 16 == 0;
            const bool requested = k1_route == 3 || (k1_route == 1 && gemm_m > 1) ||
                                   (k1_route == 2 && gemm_m == 1);
            const bool bypass = eligible && requested && tcm_buffer != nullptr;
            if (ith == 0) {
                static bool reported[2] = {false, false};
                const int phase = gemm_m == 1 ? 0 : 1;
                if (!reported[phase]) {
                    reported[phase] = true;
                    fprintf(stderr, "K1_GEMM_ROUTE mode=%d phase=%s eligible=%d bypass=%d buffer_size=%ld\n",
                            k1_route, phase ? "prefill" : "single", eligible, bypass, tcm_buffer_size);
                }
            }
            if (bypass) {
                tcm_buffer = nullptr;
                tcm_buffer_size = 0;
            }
        }
'''
    return text.replace(anchor, anchor + addition)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    a.output.write_text(generate(a.source.read_text()))
