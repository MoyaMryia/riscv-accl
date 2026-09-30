#include "ggml.h"
#include "ggml-cpu-impl.h"
#include "ops.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <vector>

namespace spacemit_kernels::rvv {
void forward_flash_attn_ext_f16_tiled_vlen1024_vf16(
    const ggml_compute_params *, ggml_tensor *, int, int, void *, size_t);
}

static void require(bool ok, const char * message) {
    if (!ok) {
        fprintf(stderr, "FAIL: %s\n", message);
        exit(1);
    }
}

static void exercise(FILE * output, int dk, int nq, int nk, int mask_mode, int rows, uint32_t id) {
    constexpr int heads = 6, kv_heads = 2, threads = 4;
    ggml_context * ctx = ggml_init({8 * 1024 * 1024, nullptr, false});
    require(ctx != nullptr, "context allocation");
    ggml_tensor * q = ggml_new_tensor_4d(ctx, GGML_TYPE_F32, dk, nq, heads, 1);
    ggml_tensor * k = ggml_new_tensor_4d(ctx, GGML_TYPE_F16, dk, nk, kv_heads, 1);
    ggml_tensor * v = ggml_new_tensor_4d(ctx, GGML_TYPE_F16, dk, nk, kv_heads, 1);
    ggml_tensor * mask = mask_mode ? ggml_new_tensor_4d(ctx, GGML_TYPE_F16, nk, nq, 1, 1) : nullptr;
    uint32_t state = 42 + id;
    auto next = [&] {
        state = state * 1664525u + 1013904223u;
        return ((int) (state >> 16) - 32768) / 32768.0f;
    };
    for (int64_t i = 0; i < ggml_nelements(q); ++i) ((float *) q->data)[i] = next();
    for (ggml_tensor * t : {k, v}) {
        for (int64_t i = 0; i < ggml_nelements(t); ++i) {
            ((ggml_fp16_t *) t->data)[i] = ggml_fp32_to_fp16(next());
        }
    }
    if (mask) {
        for (int iq = 0; iq < nq; ++iq) {
            for (int ik = 0; ik < nk; ++ik) {
                const bool blocked = mask_mode == 2 || ik > std::max(0, nk - nq + iq);
                ((ggml_fp16_t *) mask->data)[iq * nk + ik] =
                    ggml_fp32_to_fp16(blocked ? -INFINITY : 0.0f);
            }
        }
    }
    ggml_tensor * dst = ggml_flash_attn_ext(ctx, q, k, v, mask, 1.0f / sqrtf((float) dk), 0, 0);
    ggml_flash_attn_ext_set_prec(dst, GGML_PREC_F32);
    const bool compact = rows && dk == 256 && nq >= 16;
    const size_t pad = CACHE_LINE_SIZE_F32 * sizeof(float);
    const size_t stride = compact ?
        sizeof(ggml_fp16_t) * (rows * dk + 64 * (dk + dk)) +
        sizeof(float) * (2 * rows * 64 + rows * dk) + pad :
        sizeof(float) * (64 * dk + 2 * 64 * 64 + 64 * dk + 64 * dk + 64 * dk) + pad;
    void * allocation = nullptr;
    const size_t bytes = stride * threads;
    require(posix_memalign(&allocation, 64, bytes + 128) == 0, "scratch allocation");
    memset(allocation, 0xa5, bytes + 128);
    float * scratch = (float *) ((char *) allocation + 64);
    std::fill(scratch, scratch + bytes / sizeof(float), std::numeric_limits<float>::quiet_NaN());
    const int nr = nq * heads;
    const int dr = (nr + threads - 1) / threads;
    for (int ith = 0; ith < threads; ++ith) {
        ggml_compute_params params {ith, threads, bytes, scratch, nullptr, false};
        spacemit_kernels::rvv::forward_flash_attn_ext_f16_tiled_vlen1024_vf16(
            &params, dst, dr * ith, std::min(dr * (ith + 1), nr), nullptr, 0);
    }
    for (int i = 0; i < 64; ++i) {
        require(((unsigned char *) allocation)[i] == 0xa5, "scratch underflow");
        require(((unsigned char *) allocation)[64 + bytes + i] == 0xa5, "scratch overflow");
    }
    const uint32_t count = (uint32_t) ggml_nelements(dst);
    for (uint32_t i = 0; i < count; ++i) {
        require(std::isfinite(((float *) dst->data)[i]), "non-finite output from poisoned padding");
    }
    require(fwrite(&id, sizeof(id), 1, output) == 1, "write case ID");
    require(fwrite(&count, sizeof(count), 1, output) == 1, "write output length");
    require(fwrite(dst->data, sizeof(float), count, output) == count, "write output");
    free(allocation);
    ggml_free(ctx);
}

int main(int argc, char ** argv) {
    require(argc == 2, "usage: test-k1-attention-layout OUTPUT.bin");
    const char * env = getenv("SPINE_FA_K1_LAYOUT");
    const int rows = env ? atoi(env) : 0;
    require(rows == 0 || rows == 16 || rows == 32, "layout must be 0, 16 or 32");
    FILE * output = fopen(argv[1], "wb");
    require(output != nullptr, "open output");
    uint32_t cases = 0;
    for (int nq : {16, 17, 31, 32, 33, 48, 65}) {
        for (int nk : {1, 15, 16, 17, 31, 32, 48, 63, 64, 65, 97}) {
            for (int mask : {0, 1, 2}) exercise(output, 256, nq, nk, mask, rows, cases++);
        }
    }
    for (int dk : {128, 256}) {
        for (int nq : {1, 15}) exercise(output, dk, nq, 65, 1, rows, cases++);
    }
    require(fclose(output) == 0, "close output");
    fprintf(stderr, "PASS: %u cases; scratch guards and finite outputs verified\n", cases);
}
