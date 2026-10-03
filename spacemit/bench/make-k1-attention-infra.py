#!/usr/bin/env python3
"""Generate independently selectable attention data-movement experiments."""
import argparse
from pathlib import Path


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('unexpected attention source: ' + old[:80])
    return text.replace(old, new, 1)


def generate(text):
    # Helpers are cloned; the original paths remain available for fallbacks.
    qstart = text.index('static inline void rvv_qk_dot_tile_f16_x1(')
    pstart = text.index('static inline void rvv_pv_accumulate_f16_x1(', qstart)
    pend = text.index('static inline void rvv_qk_dot_tile(', pstart)
    qk = text[qstart:pstart].replace('rvv_qk_dot_tile_f16_', 'k1_qk_m2_')
    qk = qk.replace('f16m1', 'f16m2').replace('e16m1', 'e16m2').replace('f32m2', 'f32m4')
    qk = qk.replace('vfloat16m1_t', 'vfloat16m2_t').replace('vfloat32m2_t', 'vfloat32m4_t')
    pv = text[pstart:pend].replace('static inline void rvv_pv_accumulate_f16_',
                                  'template<int Variant> static inline void k1_pv_strided_')
    pv = pv.replace('int64_t          dv) {', 'int64_t          dv, size_t row_stride) {')
    pv = pv.replace('v_pack + tk * dv + d_off',
                    '(Variant == 1 ? (const _Float16 *) ((const char *) v_pack + tk * row_stride) + d_off : v_pack + tk * dv + d_off)')
    if pv.count('size_t row_stride') != 2 or pv.count('tk * row_stride') != 2:
        raise ValueError('unexpected PV helper layout')
    timer = '''
// Diagnostic timers are compiled out of ordinary timing/model arms.
static thread_local double k1_attention_ns[8] = {};
extern "C" __attribute__((visibility("default"))) void spine_k1_attention_profile_reset() {
    std::fill(k1_attention_ns, k1_attention_ns + 8, 0.0);
}
extern "C" __attribute__((visibility("default"))) void spine_k1_attention_profile_read(double * out) {
    std::copy(k1_attention_ns, k1_attention_ns + 8, out);
}
template<bool Enabled> struct K1AttentionTimer {
    using Clock = std::chrono::steady_clock;
    Clock::time_point last;
    int stage = 0;
    K1AttentionTimer() { if constexpr (Enabled) last = Clock::now(); }
    void step(int next) {
        if constexpr (Enabled) {
            auto now = Clock::now();
            k1_attention_ns[stage] += std::chrono::duration<double, std::nano>(now - last).count();
            last = now; stage = next;
        }
    }
    ~K1AttentionTimer() { if constexpr (Enabled) step(0); }
};
'''
    text = text[:pend] + qk + pv + timer + text[pend:]
    text = once(text, '#include <algorithm>', '#include <algorithm>\n#include <chrono>')
    start = text.index('template<int Q_TILE_SZ, bool Compact>')
    end = text.index('\nvoid forward_flash_attn_ext_f16_tiled_vlen1024_vf16(', start)
    kernel = text[start:end]
    kernel = once(kernel, 'template<int Q_TILE_SZ, bool Compact>',
                  'template<int Q_TILE_SZ, bool Compact, int Variant = 0, bool Profile = false>')
    kernel = once(kernel, '    const ggml_tensor * q     = dst->src[0];',
                  '    K1AttentionTimer<Profile> timer;\n    const ggml_tensor * q     = dst->src[0];')
    kernel = once(kernel, '    while (ir < ir1) {', '    while (ir < ir1) {\n        timer.step(0);')
    kernel = once(kernel, '            if constexpr (!Compact) {', '''            timer.step(1);
            if constexpr (!Compact) {''')
    kernel = once(kernel, '                rvv_zero_f32(V32, KV_TILE_SZ * DV);', '''                // Direct reads apply only to full F16 tiles; partial tiles retain
                // their initialized packed padding and all 64 PV operations.
                if (!(Variant == 1 && kv_type == GGML_TYPE_F16 && kv_tile == KV_TILE_SZ))
                    rvv_zero_f32(V32, KV_TILE_SZ * DV);''')
    kernel = once(kernel, '            if (kv_type == GGML_TYPE_F16) {\n                rvv_transposed',
                  '            timer.step(2);\n            if (kv_type == GGML_TYPE_F16) {\n                rvv_transposed')
    kernel = kernel.replace('                int tq = 0;\n                for (; tq + 3 < tile_rows; tq += 4) {',
                            '                timer.step(3);\n                int tq = 0;\n                for (; tq + 3 < tile_rows; tq += 4) {', 1)
    kernel = kernel.replace('rvv_qk_dot_tile_f16_x4(', '(Variant == 2 ? k1_qk_m2_x4 : rvv_qk_dot_tile_f16_x4)(')
    kernel = kernel.replace('rvv_qk_dot_tile_f16_x1(', '(Variant == 2 ? k1_qk_m2_x1 : rvv_qk_dot_tile_f16_x1)(')
    kernel = once(kernel, '            // Set padded KQ entries', '            timer.step(4);\n            // Set padded KQ entries')
    kernel = once(kernel, '            // PV still reads', '            timer.step(5);\n            // PV still reads')
    pack = '                memcpy2d(V_f16, DV * sizeof(_Float16), v_data, nbv1, kv_tile, DV * sizeof(_Float16));'
    kernel = once(kernel, pack, '''                const bool direct_v = Variant == 1 && kv_tile == KV_TILE_SZ;
                if (!direct_v) {
                    memcpy2d(V_f16, DV * sizeof(_Float16), v_data, nbv1, kv_tile, DV * sizeof(_Float16));
                }
                const _Float16 * pv_data = direct_v ? (const _Float16 *) v_data : V_f16;
                const size_t pv_stride = direct_v ? nbv1 : DV * sizeof(_Float16);
                timer.step(6);''')
    # Both variant/control use the same strided helper with compile-time fixed
    # stride for the control. Original helpers are retained outside this kernel.
    kernel = kernel.replace('rvv_pv_accumulate_f16_x1(', 'k1_pv_strided_x1<Variant>(')
    kernel = kernel.replace('rvv_pv_accumulate_f16_x4(', 'k1_pv_strided_x4<Variant>(')
    kernel = kernel.replace(', V_f16,', ', pv_data,')
    kernel = kernel.replace('KV_TILE_SZ, DV);', 'KV_TILE_SZ, DV, pv_stride);')
    # The F32 branch uses the original helper and must not get an extra arg.
    kernel = kernel.replace('V32, KV_TILE_SZ, DV, pv_stride);', 'V32, KV_TILE_SZ, DV);')
    kernel = once(kernel, '        // sinks (apply', '        timer.step(7);\n        // sinks (apply')
    text = text[:start] + kernel + text[end:]
    entry = '    const bool eligible = rows && !params->use_ref'
    dispatch = '''    static const int variant = [] {
        const char * e = getenv("SPINE_FA_K1_INFRA");
        if (!e || strcmp(e, "0") == 0) return 0;
        if (strcmp(e, "1") == 0) return 1;
        if (strcmp(e, "2") == 0) return 2;
        GGML_ABORT("SPINE_FA_K1_INFRA must be 0, 1 or 2");
    }();
    static const bool profile = [] {
        const char * e = getenv("SPINE_FA_K1_PROFILE");
        return e && strcmp(e, "1") == 0;
    }();
    const bool infra_eligible = rows == 0 && !params->use_ref && __riscv_vlenb() == 32 &&
        dst->src[0]->type == GGML_TYPE_F32 && dst->src[1]->type == GGML_TYPE_F16 &&
        dst->src[2]->type == GGML_TYPE_F16 && dst->src[1]->ne[0] == 256 && dst->src[2]->ne[0] == 256;
    if (infra_eligible) {
        static std::atomic<bool> logged {false};
        if (!logged.exchange(true))
            fprintf(stderr, "SPINE_FA_K1_INFRA: mode=%d profile=%d legacy Q64 KV64\\n", variant, (int) profile);
#define K1_DISPATCH(V) \\
        if (profile) forward_flash_attn_ext_f16_tiled_impl<ggml_fa_tile_config::Q, false, V, true>(params, dst, ir0, ir1, tcm_buffer, tcm_buffer_size); \\
        else forward_flash_attn_ext_f16_tiled_impl<ggml_fa_tile_config::Q, false, V, false>(params, dst, ir0, ir1, tcm_buffer, tcm_buffer_size);
        if (variant == 1) { K1_DISPATCH(1) }
        else if (variant == 2) { K1_DISPATCH(2) }
        else { K1_DISPATCH(0) }
#undef K1_DISPATCH
        return;
    }
'''
    text = once(text, entry, dispatch + entry)
    return text


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    args = p.parse_args(); args.output.write_text(generate(args.source.read_text()))
