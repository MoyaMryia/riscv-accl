#include "llama.h"
#include "ggml-backend.h"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <stdexcept>
#include <vector>

static void require(bool good, const char * reason) {
    if (!good) throw std::runtime_error(reason);
}
using Context = std::unique_ptr<llama_context, decltype(&llama_free)>;
static Context context(llama_model * model, unsigned rs) {
    auto p = llama_context_default_params();
    p.n_ctx = 4096; p.n_batch = 32; p.n_ubatch = 32; p.n_seq_max = 1;
    p.n_rs_seq = rs; p.n_threads = 4; p.n_threads_batch = 4;
    p.flash_attn_type = LLAMA_FLASH_ATTN_TYPE_ENABLED;
    p.type_k = GGML_TYPE_F16; p.type_v = GGML_TYPE_F16;
    Context ctx(llama_init_from_model(model, p), llama_free);
    require(bool(ctx), "context allocation");
    require(llama_n_threads(ctx.get()) == 4 && llama_n_threads_batch(ctx.get()) == 4,
            "context thread count differs");
    fprintf(stderr, "B1_STATE threads=%d batch_threads=%d rs=%u\n",
            llama_n_threads(ctx.get()), llama_n_threads_batch(ctx.get()), rs);
    return ctx;
}
static void decode(llama_context * ctx, int arm, int start, int count, int vocab) {
    setenv("SPINE_K1_FA_GQA", arm ? "1" : "0", 1);
    fprintf(stderr, "B1_STATE begin arm=%d start=%d count=%d\n", arm, start, count);
    auto b = llama_batch_init(32, 0, 1);
    for (int offset = 0; offset < count; offset += 32) {
        b.n_tokens = std::min(32, count-offset);
        for (int i = 0; i < b.n_tokens; ++i) {
            const int pos = start+offset+i;
            b.token[i] = 100+(pos*17+11)%(vocab-100);
            b.pos[i] = pos; b.n_seq_id[i] = 1; b.seq_id[i][0] = 0;
            b.logits[i] = i == b.n_tokens-1;
        }
        if (llama_decode(ctx, b)) {
            llama_batch_free(b);
            throw std::runtime_error("decode failed");
        }
    }
    llama_batch_free(b);
    fprintf(stderr, "B1_STATE end arm=%d\n", arm);
}
int main(int argc, char ** argv) {
    if (argc != 4) {
        fprintf(stderr, "usage: b1-state MODEL ARM DUMP\n");
        return 1;
    }
    const int arm = std::atoi(argv[2]);
    ggml_backend_load_all(); llama_backend_init();
    try {
        require(arm == 0 || arm == 1, "arm");
        FILE * dump = std::fopen(argv[3], "wb");
        require(dump, "dump file");
        auto p = llama_model_default_params(); p.n_gpu_layers = 0;
        std::unique_ptr<llama_model, decltype(&llama_model_free)> model(
            llama_model_load_from_file(argv[1], p), llama_model_free);
        require(bool(model), "model allocation");
        const int vocab = llama_vocab_n_tokens(llama_model_get_vocab(model.get()));
        int comparisons = 0;
        for (unsigned rs : {0u, 3u}) {
            setenv("SPINE_K1_FA_GQA", "0", 1);
            auto reference = context(model.get(), rs);
            Context candidate(nullptr, llama_free);
            if (arm) {
                setenv("SPINE_K1_FA_GQA", "1", 1);
                candidate = context(model.get(), rs);
            }
            for (int reset = 0; reset < 2; ++reset) {
                if (reset) {
                    llama_memory_clear(llama_get_memory(reference.get()), true);
                    if (candidate) llama_memory_clear(llama_get_memory(candidate.get()), true);
                }
                int prefix = 0;
                for (int count : {32, 1, 31, 32, 159, 1, 255, 1, 1535, 1}) {
                    decode(reference.get(), 0, prefix, count, vocab);
                    if (candidate) decode(candidate.get(), 1, prefix, count, vocab);
                    prefix += count;
                    const float * a = llama_get_logits_ith(reference.get(), -1);
                    const float * b = candidate ? llama_get_logits_ith(candidate.get(), -1) : a;
                    require(a && b, "missing logits");
                    double max_abs = 0;
                    for (int i = 0; i < vocab; ++i) {
                        require(std::isfinite(a[i]) && std::isfinite(b[i]), "nonfinite logits");
                        max_abs = std::max(max_abs, std::abs(double(a[i])-b[i]));
                    }
                    const bool equal = std::memcmp(a, b, size_t(vocab)*sizeof(float)) == 0;
                    require(std::fwrite(b, sizeof(float), vocab, dump) == size_t(vocab), "dump write");
                    printf("{\"arm\":%d,\"rs\":%u,\"reset\":%d,\"prefix\":%d,"
                           "\"vocab\":%d,\"bitwise_equal\":%s,\"max_abs\":%.17g}\n",
                           arm, rs, reset, prefix, vocab, equal ? "true" : "false", max_abs);
                    fflush(stdout);
                    require(equal, "candidate logits differ");
                    ++comparisons;
                }
            }
        }
        require(comparisons == 40, "comparison count");
        require(std::fclose(dump) == 0, "dump close");
        printf("PASS: 40 full-vocabulary records; mixed chunks/reset/RS/long history\n");
    } catch (const std::exception & e) {
        fprintf(stderr, "FAIL: %s\n", e.what());
        return 1;
    }
    llama_backend_free();
}
