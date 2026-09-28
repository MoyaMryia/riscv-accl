// Synthetic correctness gate for the experimental page map and F16 attention gather.
#include "llama-kv-page-map.h"
#include "ggml.h"
#include "ggml-cpu.h"
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>

static void require(bool condition, const char * message) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", message);
        std::exit(1);
    }
}

int main() {
    auto empty = llama_kv_page_rows(1024, [](uint32_t) { return true; }, 256);
    require(empty.size() == 256 && empty.front() == -1 && empty.back() == -1, "empty padding");
    auto partial = llama_kv_page_rows(35, [](uint32_t i) { return i != 34; });
    require(partial == std::vector<int32_t>({32, 33, 34}), "partial final page");
    bool rejected = false;
    try { llama_kv_page_rows(64, [](uint32_t) { return false; }, 32); }
    catch (const std::runtime_error &) { rejected = true; }
    require(rejected, "undersized map rejected");

    ggml_context * ctx = ggml_init({64u*1024u*1024u, nullptr, false});
    require(ctx != nullptr, "context allocation");
    constexpr int width = 256, heads = 2, physical = 1024, compact = 256, queries = 32;
    auto * q = ggml_new_tensor_4d(ctx, GGML_TYPE_F32, width, queries, heads*2, 1);
    auto * k = ggml_new_tensor_2d(ctx, GGML_TYPE_F16, width*heads, physical);
    auto * v = ggml_new_tensor_2d(ctx, GGML_TYPE_F16, width*heads, physical);
    auto * rows = ggml_new_tensor_1d(ctx, GGML_TYPE_I32, compact);
    auto * dense_mask = ggml_new_tensor_4d(ctx, GGML_TYPE_F16, physical, queries, 1, 1);
    auto * page_mask = ggml_new_tensor_4d(ctx, GGML_TYPE_F16, compact, queries, 1, 1);
    for (int64_t i = 0; i < ggml_nelements(q); ++i) {
        static_cast<float *>(q->data)[i] = std::sin(i * 0.137f);
    }
    for (int i = 0; i < width*heads*physical; ++i) {
        static_cast<ggml_fp16_t *>(k->data)[i] = ggml_fp32_to_fp16(std::cos(i * 0.017f));
        static_cast<ggml_fp16_t *>(v->data)[i] = ggml_fp32_to_fp16(std::sin(i * 0.021f));
    }
    auto * kg = ggml_cast(ctx, ggml_get_rows(ctx, k, rows), GGML_TYPE_F16);
    auto * vg = ggml_cast(ctx, ggml_get_rows(ctx, v, rows), GGML_TYPE_F16);
    // Match the cache layout: [head_width, kv_heads, tokens] is permuted for attention.
    auto * kd = ggml_permute(ctx, ggml_reshape_4d(ctx, k, width, heads, physical, 1), 0, 2, 1, 3);
    auto * vd = ggml_permute(ctx, ggml_reshape_4d(ctx, v, width, heads, physical, 1), 0, 2, 1, 3);
    kg = ggml_permute(ctx, ggml_reshape_4d(ctx, kg, width, heads, compact, 1), 0, 2, 1, 3);
    vg = ggml_permute(ctx, ggml_reshape_4d(ctx, vg, width, heads, compact, 1), 0, 2, 1, 3);
    auto * dense = ggml_flash_attn_ext(ctx, q, kd, vd, dense_mask, 1.0f/16, 0, 0);
    auto * paged = ggml_flash_attn_ext(ctx, q, kg, vg, page_mask, 1.0f/16, 0, 0);
    ggml_flash_attn_ext_set_prec(dense, GGML_PREC_F32);
    ggml_flash_attn_ext_set_prec(paged, GGML_PREC_F32);
    auto * graph = ggml_new_graph(ctx);
    ggml_build_forward_expand(graph, dense);
    ggml_build_forward_expand(graph, paged);
    // Reuse this graph with two different page maps of the same padded size.
    for (int round = 0; round < 2; ++round) {
        std::vector<bool> occupied(physical, false);
        for (int i = 0; i < 25; ++i) {
            occupied[(round ? 128 : 0) + i] = true;
            occupied[(round ? 896 : 768) + i] = true;
        }
        auto map = llama_kv_page_rows(physical, [&](uint32_t i) { return !occupied[i]; }, compact);
        require(map[0] == (round ? 128 : 0) && map[32] == (round ? 896 : 768) && map[64] == -1,
                "ordered physical page map with padding");
        for (int j = 0; j < compact; ++j) {
            static_cast<int32_t *>(rows->data)[j] = std::max(map[j], 0);
        }
        for (int query = 0; query < queries; ++query) {
            // Vary the mask per query to exercise cell holes and causal tails.
            for (int j = 0; j < physical; ++j) {
                bool keep = occupied[j] && (j % 32 <= query);
                static_cast<ggml_fp16_t *>(dense_mask->data)[query*physical+j] = ggml_fp32_to_fp16(keep ? 0 : -INFINITY);
            }
            for (int j = 0; j < compact; ++j) {
                int p = map[j];
                bool keep = p >= 0 && occupied[p] && (p % 32 <= query);
                static_cast<ggml_fp16_t *>(page_mask->data)[query*compact+j] = ggml_fp32_to_fp16(keep ? 0 : -INFINITY);
            }
        }
        require(ggml_graph_compute_with_ctx(ctx, graph, 4) == GGML_STATUS_SUCCESS, "graph compute");
        float max_error = 0;
        for (int64_t i = 0; i < ggml_nelements(dense); ++i) {
            float a = static_cast<float *>(dense->data)[i];
            float b = static_cast<float *>(paged->data)[i];
            require(std::isfinite(a) && std::isfinite(b), "finite attention output");
            max_error = std::max(max_error, std::abs(a-b));
        }
        require(max_error < 1e-5f, "dense and gathered attention agree");
        std::printf("round=%d physical_span=%d gathered_span=%d max_abs_error=%g\n", round, physical, compact, max_error);
    }
    ggml_free(ctx);
    std::puts("PASS: page boundaries, holes, padding, causal masks, GQA and changed mapping with reused graph");
}
