#pragma once

void spine_k1_conv_silu(const ggml_compute_params * p, ggml_tensor * conv, ggml_tensor * silu) {
    spine_k1_ssm_conv_cpu(p, conv);
    const int64_t channels = conv->ne[0];
    const int64_t width = (channels + p->nth - 1)/p->nth;
    const int64_t first = width*p->ith;
    const int64_t last = std::min(first + width, channels);
    if (first >= last) return;
    for (int64_t seq = 0; seq < conv->ne[2]; ++seq) {
        for (int64_t token = 0; token < conv->ne[1]; ++token) {
            const auto * x = (const float *) ((const char *) conv->data + seq*conv->nb[2] + token*conv->nb[1]);
            auto * y = (float *) ((char *) silu->data + seq*silu->nb[2] + token*silu->nb[1]);
            ggml_vec_silu_f32(last - first, y + first, x + first);
        }
    }
}
