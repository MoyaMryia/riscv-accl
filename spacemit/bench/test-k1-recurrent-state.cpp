// Small same-shape replay tests for the tested SpaceMiT fork (not upstream HEAD).
#include "llama.h"
#include "ggml-backend.h"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

using Context = std::unique_ptr<llama_context, decltype(&llama_free)>;

Context context(llama_model * model, unsigned rs) {
    auto p = llama_context_default_params();
    p.n_ctx = 256; p.n_batch = 32; p.n_ubatch = 32; p.n_seq_max = 1;
    p.n_rs_seq = rs; p.n_threads = 4; p.n_threads_batch = 4;
    p.flash_attn_type = LLAMA_FLASH_ATTN_TYPE_ENABLED;
    p.type_k = GGML_TYPE_F16; p.type_v = GGML_TYPE_F16;
    Context ctx(llama_init_from_model(model, p), llama_free);
    if (!ctx) throw std::runtime_error("context creation failed");
    if (llama_n_rs_seq(ctx.get()) != rs) throw std::runtime_error("RS configuration differs");
    return ctx;
}

// Forced valid tokens avoid different free-running histories in the comparison.
void decode(llama_context * ctx, int position, int count, int vocab) {
    auto b = llama_batch_init(32, 0, 1);
    try {
        for (int start = 0; start < count; start += 32) {
            b.n_tokens = std::min(32, count - start);
            for (int i = 0; i < b.n_tokens; ++i) {
                const int pos = position + start + i;
                b.token[i] = 100 + ((pos * 17 + 11) % (vocab - 100));
                b.pos[i] = pos; b.n_seq_id[i] = 1; b.seq_id[i][0] = 0;
                b.logits[i] = 1;
            }
            if (llama_decode(ctx, b)) throw std::runtime_error("decode failed");
        }
    } catch (...) { llama_batch_free(b); throw; }
    llama_batch_free(b);
}

std::vector<float> logits(llama_context * ctx, int vocab) {
    const auto * p = llama_get_logits_ith(ctx, -1);
    if (!p) throw std::runtime_error("missing logits");
    return {p, p + vocab};
}

void compare(const char * name, unsigned rs, int prefix,
             const std::vector<float> & a, const std::vector<float> & b) {
    bool finite = true, equal = true;
    double max_abs = 0, squared_error = 0, squared_reference = 0;
    for (size_t i = 0; i < a.size(); ++i) {
        finite &= std::isfinite(a[i]) && std::isfinite(b[i]);
        equal &= std::memcmp(&a[i], &b[i], sizeof(float)) == 0;
        if (std::isfinite(a[i]) && std::isfinite(b[i])) {
            const double d = double(a[i]) - b[i];
            max_abs = std::max(max_abs, std::abs(d));
            squared_error += d*d; squared_reference += double(a[i])*a[i];
        }
    }
    const auto aa = std::max_element(a.begin(), a.end()) - a.begin();
    const auto bb = std::max_element(b.begin(), b.end()) - b.begin();
    printf("{\"case\":\"%s\",\"rs\":%u,\"prefix\":%d,\"status\":\"%s\","
           "\"finite\":%s,\"bitwise_equal\":%s,\"argmax_equal\":%s,"
           "\"max_abs\":%.17g,\"normalized_squared_error\":%.17g}\n",
           name, rs, prefix, finite && equal ? "pass" : "mismatch",
           finite ? "true" : "false", equal ? "true" : "false",
           aa == bb ? "true" : "false", max_abs,
           squared_error / std::max(1e-30, squared_reference));
    fflush(stdout);
}

std::vector<uint8_t> save(llama_context * ctx, unsigned flags) {
    const auto n = llama_state_seq_get_size_ext(ctx, 0, flags);
    if (!n || n > 256*1024*1024) throw std::runtime_error("invalid state size");
    std::vector<uint8_t> bytes(n);
    if (llama_state_seq_get_data_ext(ctx, bytes.data(), n, 0, flags) != n)
        throw std::runtime_error("incomplete state save");
    return bytes;
}

bool remove(llama_context * ctx, int from) {
    return llama_memory_seq_rm(llama_get_memory(ctx), 0, from, -1);
}

void unsupported(const char * name, unsigned rs, int prefix) {
    printf("{\"case\":\"%s\",\"rs\":%u,\"prefix\":%d,\"status\":\"unsupported\","
           "\"reason\":\"tail removal refused; not counted as a pass\"}\n", name, rs, prefix);
    fflush(stdout);
}

void replay(llama_model * model, int vocab, unsigned rs, int prefix,
            const char * name, int flags, bool dirty, int rollback) {
    auto reference = context(model, rs), work = context(model, rs);
    decode(reference.get(), 0, prefix, vocab);
    if (rollback || dirty || flags == LLAMA_STATE_SEQ_FLAGS_PARTIAL_ONLY || flags == -1)
        decode(work.get(), 0, prefix, vocab);
    if (rollback) {
        decode(work.get(), prefix, rollback, vocab);
        if (!remove(work.get(), prefix)) { unsupported(name, rs, prefix); return; }
    } else if (flags != -1) {
        const auto bytes = save(reference.get(), flags);
        if (dirty) {
            decode(work.get(), prefix, 3, vocab);
            // Partial snapshots omit attention KV. Remove the stale attention
            // suffix as well; a refusal cannot be treated as successful restore.
            if (flags && !remove(work.get(), prefix)) { unsupported(name, rs, prefix); return; }
        }
        if (llama_state_seq_set_data_ext(work.get(), bytes.data(), bytes.size(), 0, flags) != bytes.size())
            throw std::runtime_error("incomplete state restore");
    }
    // Both arms replay M=1 then M=3, with the same token positions and shapes.
    for (int count : {1, 3}) {
        decode(reference.get(), prefix, count, vocab);
        decode(work.get(), prefix, count, vocab);
        const auto a = logits(reference.get(), vocab), b = logits(work.get(), vocab);
        const auto step_name = std::string(name) + "-replay" + std::to_string(count);
        compare(step_name.c_str(), rs, prefix, a, b);
        prefix += count;
    }
    if (rollback && rs) {
        // Repeat a one-token rollback on the same used context.
        decode(work.get(), prefix, 1, vocab);
        if (!remove(work.get(), prefix)) { unsupported("repeated-rollback", rs, prefix); return; }
        decode(reference.get(), prefix, 1, vocab); decode(work.get(), prefix, 1, vocab);
        compare("repeated-rollback", rs, prefix, logits(reference.get(), vocab), logits(work.get(), vocab));
    }
}

int main(int argc, char ** argv) {
    if (argc != 2) { fprintf(stderr, "usage: state-probe MODEL\n"); return 1; }
    ggml_backend_load_all(); llama_backend_init();
    auto mp = llama_model_default_params(); mp.n_gpu_layers = 0;
    std::unique_ptr<llama_model, decltype(&llama_model_free)> model(
        llama_model_load_from_file(argv[1], mp), llama_model_free);
    if (!model) return 1;
    const int vocab = llama_vocab_n_tokens(llama_model_get_vocab(model.get()));
    if (vocab <= 100) return 1;
    try {
        for (unsigned rs : {0u, 3u}) {
            replay(model.get(), vocab, rs, 32, "same-shape", -1, false, 0);
            replay(model.get(), vocab, rs, 32, "full-fresh", 0, false, 0);
            replay(model.get(), vocab, rs, 32, "full-dirty", 0, true, 0);
            replay(model.get(), vocab, rs, 32, "partial-seeded", 1, false, 0);
            replay(model.get(), vocab, rs, 32, "partial-dirty", 1, true, 0);
            for (int prefix : {31, 32, 33})
                for (int depth : {1, 3}) {
                    const auto name = "whole-batch-rollback" + std::to_string(depth);
                    replay(model.get(), vocab, rs, prefix, name.c_str(), 0, true, depth);
                }
        }
    } catch (const std::exception & error) {
        fprintf(stderr, "state probe error: %s\n", error.what()); return 1;
    }
    model.reset(); llama_backend_free();
    // Numerical mismatches are data, not an infrastructure process failure.
    return 0;
}
