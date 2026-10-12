#pragma once

#if defined(__riscv_v_intrinsic)
__attribute__((noinline))
static void spine_k1_gdn_prefill128(float * state, const float * key, const float * value,
        const float * query, float gate, float beta, float scale, float * output) {
    const size_t vl = __riscv_vsetvl_e32m8(64);
    for (int j = 0; j < 128; ++j) {
        float * row = state + j*128;
        vfloat32m8_t first = __riscv_vle32_v_f32m8(row, vl);
        vfloat32m8_t second = __riscv_vle32_v_f32m8(row+64, vl);
        first = __riscv_vfmul_vf_f32m8(first, gate, vl);
        second = __riscv_vfmul_vf_f32m8(second, gate, vl);
        vfloat32m8_t sum = __riscv_vfmv_v_f_f32m8(0.0f, vl);
        sum = __riscv_vfmacc_vv_f32m8(sum, first, __riscv_vle32_v_f32m8(key, vl), vl);
        sum = __riscv_vfmacc_vv_f32m8(sum, second, __riscv_vle32_v_f32m8(key+64, vl), vl);
        const float dot_key = __riscv_vfmv_f_s_f32m1_f32(__riscv_vfredusum_vs_f32m8_f32m1(
                sum, __riscv_vfmv_v_f_f32m1(0.0f, 1), vl));
        const float delta = (value[j]-dot_key)*beta;
        first = __riscv_vfmacc_vf_f32m8(first, delta, __riscv_vle32_v_f32m8(key, vl), vl);
        __riscv_vse32_v_f32m8(row, first, vl);
        sum = __riscv_vfmv_v_f_f32m8(0.0f, vl);
        sum = __riscv_vfmacc_vv_f32m8(sum, first, __riscv_vle32_v_f32m8(query, vl), vl);
        second = __riscv_vfmacc_vf_f32m8(second, delta, __riscv_vle32_v_f32m8(key+64, vl), vl);
        __riscv_vse32_v_f32m8(row+64, second, vl);
        sum = __riscv_vfmacc_vv_f32m8(sum, second, __riscv_vle32_v_f32m8(query+64, vl), vl);
        const float dot_query = __riscv_vfmv_f_s_f32m1_f32(__riscv_vfredusum_vs_f32m8_f32m1(
                sum, __riscv_vfmv_v_f_f32m1(0.0f, 1), vl));
        output[j] = dot_query*scale;
    }
}
#endif
