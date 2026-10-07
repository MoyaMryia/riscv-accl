#pragma once
#if defined(__riscv_vector)
#include <riscv_vector.h>
#endif

// No fused multiply/add: the measured reference multiplies taps then performs
// an ordered FP32 reduction starting at +0. Independent channel lanes retain
// that arithmetic without the per-channel horizontal reduction.
#if defined(__GNUC__)
__attribute__((optimize("fp-contract=off")))
#endif
static void spine_k1_ssm_conv_cpu(const ggml_compute_params * params, ggml_tensor * dst) {
    const ggml_tensor * input = dst->src[0];
    const ggml_tensor * weights = dst->src[1];
    const int64_t channels = input->ne[0];
    const int64_t taps = weights->ne[0];
    GGML_ASSERT(input->type == GGML_TYPE_F32 && weights->type == GGML_TYPE_F32);
    GGML_ASSERT(input->nb[0] == sizeof(float) && weights->nb[0] == sizeof(float));
    GGML_ASSERT(input->ne[1] == taps - 1 + dst->ne[1]);
    GGML_ASSERT(channels == weights->ne[1] && channels == dst->ne[0]);
    GGML_ASSERT(input->ne[2] == dst->ne[2] && dst->nb[0] == sizeof(float));
    const int64_t per_thread = (channels + params->nth - 1) / params->nth;
    const int64_t first = per_thread * params->ith;
    const int64_t last = std::min(first + per_thread, channels);
    for (int64_t seq = 0; seq < dst->ne[2]; ++seq) {
        for (int64_t token = 0; token < dst->ne[1]; ++token) {
            const char * window = (const char *) input->data + seq*input->nb[2] + token*input->nb[1];
            float * output = (float *) ((char *) dst->data + seq*dst->nb[2] + token*dst->nb[1]);
            int64_t channel = first;
#if defined(__riscv_vector)
            if (dst->op_params[0] == 2) {
                while (channel < last) {
                    const size_t vl = __riscv_vsetvl_e32m1(last - channel);
                    vfloat32m1_t sum = __riscv_vfmv_v_f_f32m1(0.0f, vl);
                    for (int64_t tap = 0; tap < taps; ++tap) {
                        const float * x = (const float *) (window + tap*input->nb[1]) + channel;
                        const float * w = (const float *) ((const char *) weights->data + channel*weights->nb[1]) + tap;
                        const vfloat32m1_t xv = __riscv_vle32_v_f32m1(x, vl);
                        const vfloat32m1_t wv = __riscv_vlse32_v_f32m1(w, weights->nb[1], vl);
                        const vfloat32m1_t product = __riscv_vfmul_vv_f32m1(xv, wv, vl);
                        sum = __riscv_vfadd_vv_f32m1(sum, product, vl);
                    }
                    __riscv_vse32_v_f32m1(output + channel, sum, vl);
                    channel += vl;
                }
            }
#endif
            for (; channel < last; ++channel) {
                float sum = 0.0f;
                for (int64_t tap = 0; tap < taps; ++tap) {
                    const float x = ((const float *) (window + tap*input->nb[1]))[channel];
                    const float w = ((const float *) ((const char *) weights->data + channel*weights->nb[1]))[tap];
                    sum += x*w;
                }
                output[channel] = sum;
            }
        }
    }
}
