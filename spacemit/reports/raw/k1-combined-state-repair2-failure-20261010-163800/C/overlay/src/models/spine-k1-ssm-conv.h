#pragma once
// Internal opt-in CPU experiment; this is not a public GGML API extension.
#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-cpu.h"
#include <cstdlib>

static inline int spine_k1_ssm_conv_mode() {
    const char * value = std::getenv("SPINE_K1_SSM_CONV");
    return value && (value[0] == '1' || value[0] == '2' || value[0] == '3') && value[1] == 0
        ? value[0] - '0' : 0;
}

static inline int spine_k1_ssm_conv_dispatch(int requested, int64_t tokens) {
    // Mode 3 uses only the measured winning batch shape. Keep partial
    // microbatches and single-token decode on the original graph.
    return requested == 3 ? (tokens >= 32 ? 2 : 0) : requested;
}

static inline int spine_k1_ssm_conv_mode_for_tokens(int64_t tokens) {
    return spine_k1_ssm_conv_dispatch(spine_k1_ssm_conv_mode(), tokens);
}

static inline bool spine_k1_ssm_cpu_only(ggml_backend_sched_t sched) {
    return sched && ggml_backend_sched_get_n_backends(sched) == 1 &&
        ggml_backend_is_cpu(ggml_backend_sched_get_backend(sched, 0));
}

// Channels-major input, original [channels, tokens, sequences] output.
// Call only on the CPU backend. op_params[0] is reserved by this experiment.
static inline ggml_tensor * spine_k1_ssm_conv_channels_major(
        ggml_context * ctx, ggml_tensor * input, ggml_tensor * weights, int mode) {
    GGML_ASSERT(mode == 1 || mode == 2);
    GGML_ASSERT(input->type == GGML_TYPE_F32 && weights->type == GGML_TYPE_F32);
    GGML_ASSERT(ggml_is_3d(input) && ggml_is_matrix(weights));
    GGML_ASSERT(input->ne[0] == weights->ne[1]);
    const int64_t tokens = input->ne[1] - weights->ne[0] + 1;
    GGML_ASSERT(tokens > 0);
    ggml_tensor * result = ggml_new_tensor_3d(ctx, GGML_TYPE_F32,
        input->ne[0], tokens, input->ne[2]);
    result->op = GGML_OP_SSM_CONV;
    result->src[0] = input;
    result->src[1] = weights;
    result->op_params[0] = mode;
    return result;
}
