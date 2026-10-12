#pragma once
#include <cstdio>
#include <cstdlib>
#include <cstring>

static bool spine_k1_flag(const char * name) {
    const char * value = getenv(name);
    return value && strcmp(value, "1") == 0;
}

static bool spine_k1_fa_shape(const ggml_compute_params * p, const ggml_tensor * dst) {
#if defined(__riscv_v_intrinsic) && defined(__riscv_zvfh)
    if (__riscv_vsetvlmax_e8m1() != 32) return false;
#else
    return false;
#endif
    const auto * q = dst->src[0];
    const auto * k = dst->src[1];
    const auto * v = dst->src[2];
    float bias, cap;
    memcpy(&bias, dst->op_params + 1, sizeof(bias));
    memcpy(&cap, dst->op_params + 2, sizeof(cap));
    return !p->use_ref && p->nth == 4 &&
        q->type == GGML_TYPE_F32 && k->type == GGML_TYPE_F16 && v->type == GGML_TYPE_F16 &&
        q->ne[0] == 256 && k->ne[0] == 256 && v->ne[0] == 256 &&
        q->ne[1] == 1 && q->ne[3] == 1 && k->ne[3] == 1 && v->ne[3] == 1 &&
        k->ne[1] > 0 && k->ne[1] == v->ne[1] &&
        k->ne[2] > 0 && k->ne[2] == v->ne[2] && q->ne[2] % k->ne[2] == 0 &&
        q->nb[0] == 4 && k->nb[0] == 2 && v->nb[0] == 2 &&
        dst->nb[0] == 4 && dst->nb[1] == 256*sizeof(float) &&
        bias == 0.0f && cap == 0.0f && dst->src[4] == nullptr;
}

static void spine_k1_fa_trace(const ggml_compute_params * p, const ggml_tensor * dst,
        const char * path, int64_t first, int64_t last) {
    if (spine_k1_flag("SPINE_K1_TRACE")) {
        fprintf(stderr, "K1_FA path=%s heads=%lld kv_heads=%lld history=%lld chunk=%lld:%lld worker=%d workers=%d\n",
            path, (long long) dst->src[0]->ne[2], (long long) dst->src[1]->ne[2],
            (long long) dst->src[1]->ne[1], (long long) first, (long long) last, p->ith, p->nth);
    }
}

static inline void spine_k1_dot256(const ggml_fp16_t * x, const ggml_fp16_t * y, float * out) {
#if defined(__riscv_v_intrinsic) && defined(__riscv_zvfh)
    int vl = __riscv_vsetvlmax_e32m2();
    vfloat32m1_t vs = __riscv_vfmv_v_f_f32m1(0.0f, 1);
    vfloat32m2_t sum = __riscv_vreinterpret_v_u32m2_f32m2(__riscv_vmv_v_x_u32m2(0, vl));
    vfloat16m1_t ax = __riscv_vfmv_v_f_f16m1(0.0f, vl), ay = ax;
    for (int i = 0; i < 256; i += vl) {
        vl = __riscv_vsetvl_e16m1(256 - i);
        ax = __riscv_vle16_v_f16m1_tu(ax, (const _Float16 *) (x + i), vl);
        ay = __riscv_vle16_v_f16m1_tu(ay, (const _Float16 *) (y + i), vl);
        sum = __riscv_vfwmacc_vv_f32m2_tu(sum, ax, ay, vl);
    }
    vl = __riscv_vsetvlmax_e32m1();
    const vfloat32m1_t pair = __riscv_vfadd_vv_f32m1(
        __riscv_vget_v_f32m2_f32m1(sum, 0), __riscv_vget_v_f32m2_f32m1(sum, 1), vl);
    vs = __riscv_vfredusum_vs_f32m1_f32m1(pair, vs, vl);
    ggml_float result = 0.0;
    result += __riscv_vfmv_f_s_f32m1_f32(vs);
    *out = result;
#else
    ggml_vec_dot_f16(256, out, 0, const_cast<ggml_fp16_t *>(x), 0, const_cast<ggml_fp16_t *>(y), 0, 1);
#endif
}

struct alignas(64) spine_k1_group_scratch {
    ggml_fp16_t query[4][256];
    ggml_fp16_t value[4][256];
    float output[256];
    float maximum[4];
    float total[4];
};
static_assert(sizeof(spine_k1_group_scratch) == 5184, "group scratch size");
static_assert(sizeof(spine_k1_group_scratch) <= 6*1024, "group scratch limit");

static inline void spine_k1_dot4(const ggml_fp16_t * key,
        const ggml_fp16_t query[4][256], float result[4]) {
#if defined(__riscv_v_intrinsic) && defined(__riscv_zvfh)
    int vl = __riscv_vsetvlmax_e32m2();
    const vfloat32m2_t zero = __riscv_vreinterpret_v_u32m2_f32m2(__riscv_vmv_v_x_u32m2(0, vl));
    vfloat32m2_t s0 = zero, s1 = zero, s2 = zero, s3 = zero;
    vfloat16m1_t ax = __riscv_vfmv_v_f_f16m1(0.0f, vl);
    vfloat16m1_t ay0 = ax, ay1 = ax, ay2 = ax, ay3 = ax;
    for (int i = 0; i < 256; i += vl) {
        vl = __riscv_vsetvl_e16m1(256 - i);
        ax = __riscv_vle16_v_f16m1_tu(ax, (const _Float16 *) (key + i), vl);
#define SPINE_DOT_HEAD(H) \
        ay##H = __riscv_vle16_v_f16m1_tu(ay##H, (const _Float16 *) (query[H] + i), vl); \
        s##H = __riscv_vfwmacc_vv_f32m2_tu(s##H, ax, ay##H, vl)
        SPINE_DOT_HEAD(0); SPINE_DOT_HEAD(1); SPINE_DOT_HEAD(2); SPINE_DOT_HEAD(3);
#undef SPINE_DOT_HEAD
    }
    vl = __riscv_vsetvlmax_e32m1();
#define SPINE_REDUCE_HEAD(H) { \
        vfloat32m1_t vs = __riscv_vfmv_v_f_f32m1(0.0f, 1); \
        const vfloat32m1_t pair = __riscv_vfadd_vv_f32m1( \
            __riscv_vget_v_f32m2_f32m1(s##H, 0), __riscv_vget_v_f32m2_f32m1(s##H, 1), vl); \
        vs = __riscv_vfredusum_vs_f32m1_f32m1(pair, vs, vl); \
        ggml_float value = 0.0; value += __riscv_vfmv_f_s_f32m1_f32(vs); result[H] = value; }
    SPINE_REDUCE_HEAD(0); SPINE_REDUCE_HEAD(1); SPINE_REDUCE_HEAD(2); SPINE_REDUCE_HEAD(3);
#undef SPINE_REDUCE_HEAD
#else
    for (int h = 0; h < 4; ++h) spine_k1_dot256(key, query[h], result + h);
#endif
}

static inline void spine_k1_mad4(ggml_fp16_t acc[4][256], const ggml_fp16_t * value,
        const float weight[4], const bool active[4]) {
#if defined(__riscv_v_intrinsic) && defined(__riscv_zvfh)
    ggml_fp16_t bits[4];
    for (int h = 0; h < 4; ++h) bits[h] = GGML_CPU_FP32_TO_FP16(weight[h]);
    for (int i = 0; i < 256;) {
        const int vl = __riscv_vsetvl_e16m4(256 - i);
        const vfloat16m4_t vx = __riscv_vle16_v_f16m4((const _Float16 *) (value + i), vl);
        for (int h = 0; h < 4; ++h) if (active[h]) {
            vfloat16m4_t vy = __riscv_vle16_v_f16m4((const _Float16 *) (acc[h] + i), vl);
            vy = __riscv_vfmacc_vf_f16m4(vy, *(const _Float16 *) (bits + h), vx, vl);
            __riscv_vse16_v_f16m4((_Float16 *) (acc[h] + i), vy, vl);
            __asm__ __volatile__("" ::: "memory");
        }
        i += vl;
    }
#else
    for (int h = 0; h < 4; ++h) if (active[h]) ggml_vec_mad_f16(256, acc[h], value, weight[h]);
#endif
}

static void spine_k1_gqa_chunk(const ggml_compute_params * p, ggml_tensor * dst,
        int64_t group, int64_t first, int64_t last, float * partials, int64_t stride) {
    GGML_UNUSED(p);
    spine_k1_group_scratch scratch;
    const auto * q = dst->src[0];
    const auto * k = dst->src[1];
    const auto * v = dst->src[2];
    const auto * mask = dst->src[3];
    const ggml_fp16_t * masks[4];
    float scale;
    memcpy(&scale, dst->op_params, sizeof(scale));
    const auto convert = ggml_get_type_traits_cpu(GGML_TYPE_F16)->from_float;
    for (int h = 0; h < 4; ++h) {
        const int64_t head = 4*group + h;
        convert((const float *) ((const char *) q->data + head*q->nb[2]), scratch.query[h], 256);
        memset(scratch.value[h], 0, sizeof(scratch.value[h]));
        scratch.maximum[h] = -INFINITY;
        scratch.total[h] = 0.0f;
        masks[h] = mask ? (const ggml_fp16_t *) ((const char *) mask->data +
            (head % mask->ne[2])*mask->nb[2]) : nullptr;
    }
    for (int64_t ic = first; ic < last; ++ic) {
        float score[4], weight[4] = {1, 1, 1, 1};
        bool active[4];
        const auto * key = (const ggml_fp16_t *) ((const char *) k->data + ic*k->nb[1] + group*k->nb[2]);
        const auto * value = (const ggml_fp16_t *) ((const char *) v->data + ic*v->nb[1] + group*v->nb[2]);
        spine_k1_dot4(key, scratch.query, score);
        for (int h = 0; h < 4; ++h) {
            const float mv = masks[h] ? GGML_CPU_FP16_TO_FP32(masks[h][ic]) : 0.0f;
            active[h] = mv != -INFINITY;
            if (!active[h]) continue;
            const float s = score[h]*scale + mv;
            float ms = 1.0f;
            if (s > scratch.maximum[h]) {
                ms = expf(scratch.maximum[h] - s);
                scratch.maximum[h] = s;
                ggml_vec_scale_f16(256, scratch.value[h], ms);
            } else {
                weight[h] = expf(s - scratch.maximum[h]);
            }
            scratch.total[h] = scratch.total[h]*ms + weight[h];
        }
        spine_k1_mad4(scratch.value, value, weight, active);
    }
    for (int h = 0; h < 4; ++h) {
        const int64_t head = 4*group + h;
        for (int d = 0; d < 256; ++d) scratch.output[d] = GGML_CPU_FP16_TO_FP32(scratch.value[h][d]);
        if (partials) {
            float * out = partials + head*stride;
            out[0] = scratch.maximum[h];
            out[1] = scratch.total[h];
            memcpy(out + 2, scratch.output, sizeof(scratch.output));
        } else {
            const float inv = scratch.total[h] == 0.0f ? 0.0f : 1.0f/scratch.total[h];
            ggml_vec_scale_f32(256, scratch.output, inv);
            memcpy((char *) dst->data + head*dst->nb[1], scratch.output, sizeof(scratch.output));
        }
    }
}
