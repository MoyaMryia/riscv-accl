#include "ggml.h"
#include "ggml-cpu-impl.h"
#include "ops.h"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <pthread.h>
#include <sched.h>
#include <thread>
#include <vector>
#include <dlfcn.h>

namespace spacemit_kernels::rvv {
void forward_flash_attn_ext_f16_tiled_vlen1024_vf16(
    const ggml_compute_params *, ggml_tensor *, int, int, void *, size_t);
}

static void require(bool ok, const char * message) {
    if (!ok) { fprintf(stderr, "FAIL: %s\n", message); exit(1); }
}

using Clock = std::chrono::steady_clock;
static double elapsed_ms(Clock::time_point start) {
    return std::chrono::duration<double, std::milli>(Clock::now() - start).count();
}

struct Fixture {
    static constexpr int threads = 4;
    ggml_context * ctx;
    ggml_tensor * dst;
    void * allocation;
    float * scratch;
    size_t bytes;
    int nr;
    std::vector<float> guarded_output;
    std::vector<std::pair<ggml_tensor *, std::vector<unsigned char>>> input_copies;


    Fixture(int dk, int nq, int nk, int mask_mode, int rows, uint32_t id,
            int heads = 6, int kv_heads = 2, int padding = 0, int extra = 0, int sequences = 1) {
        require(heads >= kv_heads && heads % kv_heads == 0, "head grouping");
        const size_t memory = 8 * 1024 * 1024 + (size_t) nk * kv_heads * (dk + padding) * 4 * sequences;
        ctx = ggml_init({memory, nullptr, false});
        require(ctx != nullptr, "context allocation");
        auto * q = ggml_new_tensor_4d(ctx, GGML_TYPE_F32, dk, nq, heads, sequences);
        auto * kb = ggml_new_tensor_4d(ctx, GGML_TYPE_F16, dk + padding, nk, kv_heads, sequences);
        auto * vb = ggml_new_tensor_4d(ctx, GGML_TYPE_F16, dk + padding, nk, kv_heads, sequences);
        auto * k = ggml_view_4d(ctx, kb, dk, nk, kv_heads, sequences, kb->nb[1], kb->nb[2], kb->nb[3], 0);
        auto * v = ggml_view_4d(ctx, vb, dk, nk, kv_heads, sequences, vb->nb[1], vb->nb[2], vb->nb[3], 0);
        auto * mask = mask_mode ? ggml_new_tensor_4d(ctx, GGML_TYPE_F16, nk, nq, 1, 1) : nullptr;
        uint32_t state = 42 + id;
        auto next = [&] {
            state = state * 1664525u + 1013904223u;
            return ((int) (state >> 16) - 32768) / 32768.0f;
        };
        for (int64_t i = 0; i < ggml_nelements(q); ++i) ((float *) q->data)[i] = next();
        for (ggml_tensor * t : {kb, vb}) {
            for (int64_t i = 0; i < ggml_nelements(t); ++i)
                ((ggml_fp16_t *) t->data)[i] = ggml_fp32_to_fp16(next());
        }
        if (mask) {
            for (int iq = 0; iq < nq; ++iq) for (int ik = 0; ik < nk; ++ik) {
                bool blocked = mask_mode == 2 || ik > std::max(0, nk - nq + iq);
                ((ggml_fp16_t *) mask->data)[iq * nk + ik] =
                    ggml_fp32_to_fp16(blocked ? -INFINITY : 0.0f);
            }
        }
        dst = ggml_flash_attn_ext(ctx, q, k, v, mask, 1.0f / sqrtf((float) dk), extra ? 1.0f : 0.0f, extra ? 4.0f : 0.0f);
        ggml_tensor * sinks = nullptr;
        if (extra) {
            sinks = ggml_new_tensor_1d(ctx, GGML_TYPE_F32, heads);
            for (int h = 0; h < heads; ++h) ((float *) sinks->data)[h] = next();
            dst->src[4] = sinks;
        }
        for (ggml_tensor * t : {q, kb, vb, mask, sinks}) if (t) {
            auto * data = (unsigned char *) t->data;
            input_copies.push_back({t, std::vector<unsigned char>(data, data + ggml_nbytes(t))});
        }
        guarded_output.resize(ggml_nelements(dst) + 32, 12345.0f);
        dst->data = guarded_output.data() + 16;
        std::fill((float *) dst->data, (float *) dst->data + ggml_nelements(dst), std::numeric_limits<float>::quiet_NaN());
        ggml_flash_attn_ext_set_prec(dst, GGML_PREC_F32);
        const bool compact = rows && dk == 256 && nq >= 16;
        const size_t pad = CACHE_LINE_SIZE_F32 * sizeof(float);
        const size_t stride = compact ?
            sizeof(ggml_fp16_t) * (rows * dk + 64 * (dk + dk)) +
            sizeof(float) * (2 * rows * 64 + rows * dk) + pad :
            sizeof(float) * (64 * dk + 2 * 64 * 64 + 64 * dk + 64 * dk + 64 * dk) + pad;
        bytes = stride * threads;
        require(posix_memalign(&allocation, 64, bytes + 128) == 0, "scratch allocation");
        memset(allocation, 0xa5, bytes + 128);
        scratch = (float *) ((char *) allocation + 64);
        std::fill(scratch, scratch + bytes / sizeof(float), std::numeric_limits<float>::quiet_NaN());
        nr = nq * heads * sequences;
    }
    void call(int ith) {
        const int dr = (nr + threads - 1) / threads;
        ggml_compute_params params {ith, threads, bytes, scratch, nullptr, false};
        spacemit_kernels::rvv::forward_flash_attn_ext_f16_tiled_vlen1024_vf16(
            &params, dst, dr * ith, std::min(dr * (ith + 1), nr), nullptr, 0);
    }
    void check() {
        for (const auto & input : input_copies)
            require(memcmp(input.first->data, input.second.data(), input.second.size()) == 0, "input changed");
        for (int i = 0; i < 16; ++i) {
            require(guarded_output[i] == 12345.0f, "output underflow");
            require(guarded_output[guarded_output.size() - 1 - i] == 12345.0f, "output overflow");
        }
        for (int i = 0; i < 64; ++i) {
            require(((unsigned char *) allocation)[i] == 0xa5, "scratch underflow");
            require(((unsigned char *) allocation)[64 + bytes + i] == 0xa5, "scratch overflow");
        }
        for (int64_t i = 0; i < ggml_nelements(dst); ++i)
            require(std::isfinite(((float *) dst->data)[i]), "non-finite output from poisoned padding");
    }
    ~Fixture() { free(allocation); ggml_free(ctx); }
};

// Workers persist across iterations. Barriers bracket only the kernel calls.
struct Team {
    Fixture & fixture;
    pthread_barrier_t barrier;
    std::vector<std::thread> workers;
    std::atomic<bool> quit {false};
    int iterations = 1;
    double worker_ms[4] {};
    int cpus[4] {};
    double stages[4][8] {};
    using Reset = void (*)();
    using Read = void (*)(double *);
    Reset reset = (Reset) dlsym(RTLD_DEFAULT, "spine_k1_attention_profile_reset");
    Read read = (Read) dlsym(RTLD_DEFAULT, "spine_k1_attention_profile_read");
    Team(Fixture & f, bool pin) : fixture(f) {
        require(pthread_barrier_init(&barrier, nullptr, 5) == 0, "barrier init");
        for (int ith = 0; ith < 4; ++ith) workers.emplace_back([&, ith, pin] {
            if (pin) {
                cpu_set_t set; CPU_ZERO(&set); CPU_SET(ith, &set);
                require(pthread_setaffinity_np(pthread_self(), sizeof(set), &set) == 0, "worker affinity");
            }
            for (;;) {
                pthread_barrier_wait(&barrier);
                if (quit.load()) break;
                if (reset) reset();
                auto start = Clock::now();
                for (int j = 0; j < iterations; ++j) fixture.call(ith);
                worker_ms[ith] = elapsed_ms(start);
                if (read) read(stages[ith]);
                cpus[ith] = sched_getcpu();
                pthread_barrier_wait(&barrier);
            }
        });
    }
    double run(int n) {
        iterations = n;
        auto start = Clock::now();
        pthread_barrier_wait(&barrier);
        pthread_barrier_wait(&barrier);
        return elapsed_ms(start);
    }
    ~Team() {
        quit.store(true); pthread_barrier_wait(&barrier);
        for (auto & w : workers) w.join();
        pthread_barrier_destroy(&barrier);
    }
};

static void exercise(FILE * output, int dk, int nq, int nk, int mask, int rows, uint32_t id) {
    Fixture f(dk, nq, nk, mask, rows, id);
    { Team team(f, false); team.run(1); }
    f.check();
    const uint32_t count = (uint32_t) ggml_nelements(f.dst);
    require(fwrite(&id, sizeof(id), 1, output) == 1, "write case ID");
    require(fwrite(&count, sizeof(count), 1, output) == 1, "write output length");
    require(fwrite(f.dst->data, sizeof(float), count, output) == count, "write output");
}


static void benchmark(int block, int heads, int kv_heads, int nk, int mask) {
    Fixture f(256, 32, nk, mask, 0, 1000 + nk + mask, heads, kv_heads);
    Team team(f, true);
    team.run(1);
    int iterations = 1;
    do {
        team.run(iterations);
        if (*std::max_element(team.worker_ms, team.worker_ms + 4) >= 100.0) break;
        iterations *= 2;
        require(iterations <= 1048576, "calibration limit");
    } while (true);
    f.check();
    const double slowest = *std::max_element(team.worker_ms, team.worker_ms + 4);
    printf("{\"mode\":%d,\"profile\":%d,\"block\":%d,\"heads\":%d,\"kv_heads\":%d,\"q_rows\":32,\"kv_rows\":%d,\"mask\":%d,\"iterations\":%d,\"slowest_ms\":%.6f,\"ms_per_call\":%.6f,\"cpus\":[%d,%d,%d,%d],\"stage_sum_ns\":[",
           getenv("SPINE_FA_K1_INFRA") ? atoi(getenv("SPINE_FA_K1_INFRA")) : 0,
           getenv("SPINE_FA_K1_PROFILE") ? atoi(getenv("SPINE_FA_K1_PROFILE")) : 0,
           block, heads, kv_heads, nk, mask, iterations, slowest, slowest / iterations,
           team.cpus[0], team.cpus[1], team.cpus[2], team.cpus[3]);
    for (int j = 0; j < 8; ++j) {
        double total = 0;
        for (int i = 0; i < 4; ++i) total += team.stages[i][j];
        printf("%s%.3f", j ? "," : "", total);
    }
    printf("]}\n");
}

int main(int argc, char ** argv) {
    require(!getenv("SPINE_FA_K1_LAYOUT") || strcmp(getenv("SPINE_FA_K1_LAYOUT"), "0") == 0,
            "infrastructure test requires layout 0");
    if (argc == 7 && strcmp(argv[1], "--bench") == 0) {
        benchmark(atoi(argv[2]), atoi(argv[3]), atoi(argv[4]), atoi(argv[5]), atoi(argv[6]));
        return 0;
    }
    require(argc == 2, "usage: test-attention OUTPUT.bin OR --bench BLOCK HEADS KV_HEADS HISTORY MASK");
    FILE * output = fopen(argv[1], "wb"); require(output != nullptr, "open output");
    uint32_t cases = 0;
    for (int nq : {16, 17, 31, 32, 33, 48, 65})
        for (int nk : {1, 15, 16, 17, 31, 32, 48, 63, 64, 65, 97})
            for (int mask : {0, 1, 2}) exercise(output, 256, nq, nk, mask, 0, cases++);
    for (int dk : {128, 256}) for (int nq : {1, 15})
        exercise(output, dk, nq, 65, 1, 0, cases++);
    for (int nk : {2048, 8193}) for (int mask : {0, 1, 2})
        exercise(output, 256, 33, nk, mask, 0, cases++);
    for (int padding : {0, 8}) for (int nk : {63, 64, 65, 129})
        for (int mask : {0, 1, 2}) for (int extra : {0, 1}) {
            Fixture f(256, 17, nk, mask, 0, cases, 8, 2, padding, extra, 2);
            { Team team(f, false); team.run(1); }
            f.check();
            const uint32_t count = (uint32_t) ggml_nelements(f.dst);
            require(fwrite(&cases, sizeof(cases), 1, output) == 1, "write id");
            require(fwrite(&count, sizeof(count), 1, output) == 1, "write length");
            require(fwrite(f.dst->data, sizeof(float), count, output) == count, "write output");
            ++cases;
        }
    require(fclose(output) == 0, "close output");
    fprintf(stderr, "PASS: %u concurrent cases; inputs/output/scratch guards, padded strides, sinks and finite outputs verified\n", cases);
}
