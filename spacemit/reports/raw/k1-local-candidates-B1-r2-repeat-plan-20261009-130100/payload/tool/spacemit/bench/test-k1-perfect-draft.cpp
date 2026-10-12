// K1 adaptation: fixed 128-token reproduction fixture, F16 KV, batch 32.
#include "llama.h"
#include "ggml-backend.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace {

struct Top2 {
    llama_token id1 = -1;
    llama_token id2 = -1;
    float l1 = -INFINITY;
    float l2 = -INFINITY;
};

struct Step {
    llama_token t = -1;
    llama_token id1 = -1;
    llama_token id2 = -1;
    float l1 = 0;
    float l2 = 0;
};

Top2 top2_of(const float * logits, int n) {
    Top2 t;
    for (int i = 0; i < n; ++i) {
        const float v = logits[i];
        if (!std::isfinite(v)) { fprintf(stderr, "nonfinite logits\n"); exit(1); }
        if (v > t.l1) {
            t.l2 = t.l1; t.id2 = t.id1;
            t.l1 = v;    t.id1 = i;
        } else if (v > t.l2) {
            t.l2 = v; t.id2 = i;
        }
    }
    return t;
}

std::string read_file(const char * path) {
    std::ifstream f(path, std::ios::binary);
    if (!f) {
        fprintf(stderr, "error: cannot open %s\n", path);
        exit(1);
    }
    std::ostringstream ss;
    ss << f.rdbuf();
    return ss.str();
}

struct Args {
    const char * mode = nullptr;
    const char * model = nullptr;
    const char * prompt_file = nullptr;
    const char * traj_path = nullptr;
    const char * out_path = nullptr;
    int n_predict = 4096;
    int threads = 4;
    int k = 1;
};

Args parse_args(int argc, char ** argv) {
    Args a;
    if (argc < 2) {
        fprintf(stderr, "usage: verify-probe direct|verify [options]\n");
        exit(1);
    }
    a.mode = argv[1];
    if (strcmp(a.mode, "direct") != 0 && strcmp(a.mode, "verify") != 0) {
        fprintf(stderr, "error: unknown mode %s\n", a.mode);
        exit(1);
    }
    for (int i = 2; i < argc; i += 2) {
        const char * key = argv[i];
        const char * val = (i + 1 < argc) ? argv[i + 1] : "";
        if      (!strcmp(key, "--model"))       a.model = val;
        else if (!strcmp(key, "--prompt-file")) a.prompt_file = val;
        else if (!strcmp(key, "--traj"))        a.traj_path = val;
        else if (!strcmp(key, "--out"))         a.out_path = val;
        else if (!strcmp(key, "--n-predict"))   a.n_predict = atoi(val);
        else if (!strcmp(key, "--threads"))     a.threads = atoi(val);
        else if (!strcmp(key, "--k"))           a.k = atoi(val);
        else { fprintf(stderr, "error: unknown option %s\n", key); exit(1); }
    }
    if (!a.model || !a.prompt_file) {
        fprintf(stderr, "error: --model and --prompt-file are required\n");
        exit(1);
    }
    if (!strcmp(a.mode, "verify") && (!a.traj_path || !a.out_path)) {
        fprintf(stderr, "error: verify mode needs --traj and --out\n");
        exit(1);
    }
    if (a.k < 1 || a.k > 32) {
        fprintf(stderr, "error: --k must be in [1, 32]\n");
        exit(1);
    }
    return a;
}

struct Session {
    llama_model * model = nullptr;
    llama_context * ctx = nullptr;
    const llama_vocab * vocab = nullptr;
    int n_vocab = 0;
    llama_batch batch = {};
    Session() = default;
    Session(const Session &) = delete;
    Session(Session && other) noexcept : model(other.model), ctx(other.ctx), vocab(other.vocab), n_vocab(other.n_vocab), batch(other.batch), prompt(std::move(other.prompt)), pos0(other.pos0) { other.model = nullptr; other.ctx = nullptr; other.batch = {}; }
    std::vector<llama_token> prompt;
    llama_pos pos0 = 0;

    ~Session() {
        if (batch.token)  llama_batch_free(batch);
        if (ctx)          llama_free(ctx);
        if (model)        llama_model_free(model);
    }
};

Session make_session(const Args & a) {
    Session s;
    auto mp = llama_model_default_params(); mp.n_gpu_layers = 0;
    s.model = llama_model_load_from_file(a.model, mp);
    if (!s.model) {
        fprintf(stderr, "error: failed to load model %s\n", a.model);
        exit(1);
    }
    s.vocab = llama_model_get_vocab(s.model);
    s.n_vocab = llama_vocab_n_tokens(s.vocab);

    const std::string text = read_file(a.prompt_file);
    s.prompt.resize(text.size() + 8);
    int n_prompt = llama_tokenize(s.vocab, text.data(), (int) text.size(),
                                        s.prompt.data(), (int) s.prompt.size(),
                                        true, true);
    if (n_prompt < 0) {
        fprintf(stderr, "error: tokenization overflow\n");
        exit(1);
    }
    if (n_prompt < 128) { fprintf(stderr, "fixture shorter than 128 tokens\n"); exit(1); }
    n_prompt = 128;
    s.prompt.resize(n_prompt);

    llama_context_params cp = llama_context_default_params();
    cp.n_ctx     = std::max(512u, (uint32_t)(n_prompt + a.n_predict + 32));
    cp.n_batch   = 32;
    cp.n_ubatch  = 32;
    cp.type_k = GGML_TYPE_F16; cp.type_v = GGML_TYPE_F16;
    cp.flash_attn_type = LLAMA_FLASH_ATTN_TYPE_ENABLED;
    cp.n_seq_max = 1;
    cp.n_threads = a.threads;
    cp.n_threads_batch = a.threads;
    s.ctx = llama_init_from_model(s.model, cp);
    if (!s.ctx) {
        fprintf(stderr, "error: failed to create context\n");
        exit(1);
    }
    s.batch = llama_batch_init(32, 0, 1);
    s.pos0  = n_prompt;
    fprintf(stderr, "model=%s vocab=%d prompt_tokens=%d n_predict=%d threads=%d\n",
            a.model, s.n_vocab, n_prompt, a.n_predict, a.threads);
    return s;
}

// Prefill the prompt; returns the top-2 of the last row's logits (predicts
// trajectory token 0). Chunking is fixed (32) so both modes prefill
// identically.
Top2 prefill(Session & s) {
    Top2 pred;
    const int n = (int) s.prompt.size();
    for (int c = 0; c < n; c += 32) {
        const int m = std::min(32, n - c);
        s.batch.n_tokens = m;
        for (int i = 0; i < m; ++i) {
            s.batch.token[i]  = s.prompt[c + i];
            s.batch.pos[i]    = c + i;
            s.batch.n_seq_id[i] = 1;
            s.batch.seq_id[i][0] = 0;
            s.batch.logits[i] = (c + i == n - 1);
        }
        if (llama_decode(s.ctx, s.batch)) {
            fprintf(stderr, "error: prefill decode failed at %d\n", c);
            exit(1);
        }
        if (c + m == n) {
            pred = top2_of(llama_get_logits_ith(s.ctx, m - 1), s.n_vocab);
        }
    }
    return pred;
}

std::string piece_of(const Session & s, llama_token t) {
    char buf[64];
    const int n = llama_token_to_piece(s.vocab, t, buf, sizeof(buf), 0, true);
    if (n <= 0) {
        return "";
    }
    return std::string(buf, buf + n);
}

void escape_into(const std::string & src, std::string & dst) {
    for (unsigned char c : src) {
        if (c == '"' || c == '\\') {
            dst += '\\'; dst += c;
        } else if (c < 0x20) {
            char tmp[8];
            snprintf(tmp, sizeof(tmp), "\\u%04x", c);
            dst += tmp;
        } else {
            dst += c;
        }
    }
}

int run_direct(const Args & a) {
    Session s = make_session(a);
    FILE * out = fopen(a.traj_path, "w");
    if (!out) {
        fprintf(stderr, "error: cannot write %s\n", a.traj_path);
        return 1;
    }
    const auto t0 = std::chrono::steady_clock::now();
    Top2 pred = prefill(s);
    int decoded = 0;
    for (int i = 0; i < a.n_predict; ++i) {
        fprintf(out, "{\"i\":%d,\"t\":%d,\"id1\":%d,\"l1\":%.9g,\"id2\":%d,\"l2\":%.9g,\"margin\":%.9g}\n",
                i, (int) pred.id1, (int) pred.id1, pred.l1, (int) pred.id2, pred.l2, pred.l1 - pred.l2);
        if (i == a.n_predict - 1) {
            break;
        }
        s.batch.n_tokens = 1;
        s.batch.token[0]    = pred.id1;
        s.batch.pos[0]      = s.pos0 + i;
        s.batch.n_seq_id[0] = 1;
        s.batch.seq_id[0][0] = 0;
        s.batch.logits[0]   = 1;
        if (llama_decode(s.ctx, s.batch)) {
            fprintf(stderr, "error: decode failed at %d\n", i);
            return 1;
        }
        pred = top2_of(llama_get_logits_ith(s.ctx, 0), s.n_vocab);
        ++decoded;
    }
    const double wall = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    fclose(out);
    fprintf(stderr, "{\"mode\":\"direct\",\"n\":%d,\"decode_steps\":%d,\"tok_per_s\":%.3f,\"wall_s\":%.2f}\n",
            a.n_predict, decoded, decoded / wall, wall);
    return 0;
}

struct FlipStat {
    double sum = 0;
    double sum_sq = 0;
    double max = 0;
    long   count = 0;
    std::vector<float> all;
};

void add_shift(FlipStat & f, float v) {
    const double a = std::abs((double) v);
    f.sum += a;
    f.sum_sq += a * a;
    f.max = std::max(f.max, a);
    ++f.count;
    f.all.push_back(a);
}

int run_verify(const Args & a) {
    // trajectory from the direct run
    std::vector<Step> traj;
    {
        std::ifstream in(a.traj_path);
        if (!in) {
            fprintf(stderr, "error: cannot read %s\n", a.traj_path);
            return 1;
        }
        std::string line;
        while (std::getline(in, line)) {
            Step st;
            int idx = 0;
            if (sscanf(line.c_str(),
                       "{\"i\":%d,\"t\":%d,\"id1\":%d,\"l1\":%f,\"id2\":%d,\"l2\":%f",
                       &idx, (int *) &st.t, (int *) &st.id1, &st.l1,
                       (int *) &st.id2, &st.l2) == 6) {
                if (idx != int(traj.size()) || st.id1 < 0 || st.id2 < 0 || !std::isfinite(st.l1) || !std::isfinite(st.l2)) return 1;
                traj.push_back(st);
            }
        }
    }
    Args a2 = a;
    if (traj.size() != size_t(a.n_predict)) { fprintf(stderr, "incomplete trajectory\n"); return 1; }
    a2.n_predict = a.n_predict;

    Session s = make_session(a2);
    FILE * out = fopen(a.out_path, "w");
    if (!out) {
        fprintf(stderr, "error: cannot write %s\n", a.out_path);
        return 1;
    }

    const auto t0 = std::chrono::steady_clock::now();
    const Top2 pred0 = prefill(s);

    FlipStat shift;
    int first_flip = -1;
    int n_flips = 0;

    auto check = [&](const Top2 & v, const float * raw, const Step & d, int i) {
        const bool match = (v.id1 == d.id1);
        add_shift(shift, raw[d.id1] - d.l1);
        add_shift(shift, raw[d.id2] - d.l2);
        if (!match) {
            ++n_flips;
            if (first_flip < 0) {
                first_flip = i;
                fprintf(stderr, "first flip at %d: direct %d (%.4f) vs verify %d (%.4f) pieces '%s' / '%s'\n",
                        i, (int) d.id1, d.l1, (int) v.id1, v.l1,
                        piece_of(s, d.id1).c_str(), piece_of(s, v.id1).c_str());
            }
        }
        fprintf(out,
                "{\"i\":%d,\"match\":%s,\"d_id\":%d,\"v_id\":%d,\"d1\":%.9g,\"d2\":%.9g,"
                "\"v_at_d1\":%.9g,\"v_at_d2\":%.9g,\"vmargin\":%.9g,\"dmargin\":%.9g}\n",
                i, match ? "true" : "false", (int) d.id1, (int) v.id1, d.l1, d.l2,
                raw[d.id1], raw[d.id2], v.l1 - v.l2, d.l1 - d.l2);
    };

    // token 0 is predicted by the prefill's last row in both modes; the logits
    // buffer still holds the last prefill chunk here (no decode since)
    check(pred0, llama_get_logits_ith(s.ctx, ((int) s.prompt.size() - 1) % 32), traj[0], 0);

    for (int c = 0; c < a2.n_predict; c += a.k) {
        // decode tokens T[c .. c+m-1] in one M=m ubatch; row j predicts T[c+j+1]
        const int m = std::min(a.k, a2.n_predict - c);
        s.batch.n_tokens = m;
        for (int j = 0; j < m; ++j) {
            s.batch.token[j]    = traj[c + j].t;
            s.batch.pos[j]      = s.pos0 + c + j;
            s.batch.n_seq_id[j] = 1;
            s.batch.seq_id[j][0] = 0;
            s.batch.logits[j]   = 1;
        }
        if (llama_decode(s.ctx, s.batch)) {
            fprintf(stderr, "error: verify decode failed at %d\n", c);
            return 1;
        }
        for (int j = 0; j < m; ++j) {
            const int idx = c + j + 1;
            if (idx >= a2.n_predict) {
                break;
            }
            const float * raw = llama_get_logits_ith(s.ctx, j);
            check(top2_of(raw, s.n_vocab), raw, traj[idx], idx);
        }
        if ((c / a.k) % 256 == 0) {
            fprintf(stderr, "\rverify %d/%d flips=%d", c, a2.n_predict, n_flips);
            fflush(stderr);
        }
    }
    const double wall = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();

    std::vector<float> sorted = shift.all;
    std::sort(sorted.begin(), sorted.end());
    const float p50 = sorted.empty() ? 0 : sorted[sorted.size() / 2];
    const float p95 = sorted.empty() ? 0 : sorted[(size_t)(sorted.size() * 0.95)];
    fclose(out);
    fprintf(stderr,
            "\n{\"mode\":\"verify\",\"k\":%d,\"n\":%d,\"first_flip\":%d,\"n_flips\":%d,"
            "\"flips_per_1k\":%.3f,\"shift_mean\":%.9g,\"shift_p50\":%.9g,\"shift_p95\":%.9g,"
            "\"shift_max\":%.9g,\"tok_per_s\":%.3f,\"wall_s\":%.2f}\n",
            a.k, a2.n_predict, first_flip, n_flips,
            1000.0 * n_flips / std::max(1, a2.n_predict),
            shift.count ? shift.sum / shift.count : 0.0,
            p50, p95, shift.max,
            a2.n_predict / wall, wall);
    return 0;
}

} // namespace

int main(int argc, char ** argv) {
    ggml_backend_load_all(); llama_backend_init();
    const Args a = parse_args(argc, argv);
    return !strcmp(a.mode, "direct") ? run_direct(a) : run_verify(a);
}
