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

    Fixture(int dk, int nq, int nk, int mask_mode, int rows, uint32_t id,
            int heads = 6, int kv_heads = 2) {
        require(heads >= kv_heads && heads % kv_heads == 0, "head grouping");
        const size_t memory = 8 * 1024 * 1024 + (size_t) nk * kv_heads * dk * 4;
        ctx = ggml_init({memory, nullptr, false});
        require(ctx != nullptr, "context allocation");
        auto * q = ggml_new_tensor_4d(ctx, GGML_TYPE_F32, dk, nq, heads, 1);
        auto * k = ggml_new_tensor_4d(ctx, GGML_TYPE_F16, dk, nk, kv_heads, 1);
        auto * v = ggml_new_tensor_4d(ctx, GGML_TYPE_F16, dk, nk, kv_heads, 1);
        auto * mask = mask_mode ? ggml_new_tensor_4d(ctx, GGML_TYPE_F16, nk, nq, 1, 1) : nullptr;
        uint32_t state = 42 + id;
        auto next = [&] {
            state = state * 1664525u + 1013904223u;
            return ((int) (state >> 16) - 32768) / 32768.0f;
        };
        for (int64_t i = 0; i < ggml_nelements(q); ++i) ((float *) q->data)[i] = next();
        for (ggml_tensor * t : {k, v}) {
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
        dst = ggml_flash_attn_ext(ctx, q, k, v, mask, 1.0f / sqrtf((float) dk), 0, 0);
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
        nr = nq * heads;
    }
    void call(int ith) {
        const int dr = (nr + threads - 1) / threads;
        ggml_compute_params params {ith, threads, bytes, scratch, nullptr, false};
        spacemit_kernels::rvv::forward_flash_attn_ext_f16_tiled_vlen1024_vf16(
            &params, dst, dr * ith, std::min(dr * (ith + 1), nr), nullptr, 0);
    }
    void check() {
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
                auto start = Clock::now();
                for (int j = 0; j < iterations; ++j) fixture.call(ith);
                worker_ms[ith] = elapsed_ms(start);
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

static void benchmark(int rows, int block, int heads, int kv_heads) {
    for (int nk : {128, 2048, 8192}) for (int mask : {0, 1}) {
        Fixture f(256, 32, nk, mask, rows, 1000 + nk + mask, heads, kv_heads);
        Team team(f, true);
        team.run(1);
        int iterations = 1;
        double wall;
        do {
            wall = team.run(iterations);
            if (*std::max_element(team.worker_ms, team.worker_ms + 4) >= 100.0) break;
            iterations *= 2;
            require(iterations <= 1048576, "benchmark calibration limit");
        } while (true);
        f.check();
        const double slowest = *std::max_element(team.worker_ms, team.worker_ms + 4);
        printf("{\"layout\":%d,\"block\":%d,\"heads\":%d,\"kv_heads\":%d,"
               "\"q_rows\":32,\"kv_rows\":%d,\"mask\":%d,\"iterations\":%d,"
               "\"wall_ms\":%.6f,\"slowest_worker_ms\":%.6f,\"ms_per_call\":%.6f,"
               "\"worker_cpus\":[%d,%d,%d,%d],\"input_policy\":\"repeated deterministic tensors\"}\n",
               rows, block, heads, kv_heads, nk, mask, iterations, wall, slowest,
               slowest / iterations, team.cpus[0], team.cpus[1], team.cpus[2], team.cpus[3]);
        fflush(stdout);
    }
}

int main(int argc, char ** argv) {
    const char * env = getenv("SPINE_FA_K1_LAYOUT");
    const int rows = env ? atoi(env) : 0;
    require(rows == 0 || rows == 16 || rows == 32, "layout must be 0, 16 or 32");
    if (argc == 7 && strcmp(argv[1], "--bench") == 0) {
        benchmark(rows, atoi(argv[2]), atoi(argv[3]), atoi(argv[4]));
        benchmark(rows, atoi(argv[2]), atoi(argv[5]), atoi(argv[6]));
        return 0;
    }
    require(argc == 2 || (argc == 3 && strcmp(argv[2], "--long") == 0),
            "usage: test-layout OUTPUT.bin [--long] OR --bench BLOCK H2 KV2 H4 KV4");
    FILE * output = fopen(argv[1], "wb"); require(output != nullptr, "open output");
    uint32_t cases = 0;
    for (int nq : {16, 17, 31, 32, 33, 48, 65})
        for (int nk : {1, 15, 16, 17, 31, 32, 48, 63, 64, 65, 97})
            for (int mask : {0, 1, 2}) exercise(output, 256, nq, nk, mask, rows, cases++);
    for (int dk : {128, 256}) for (int nq : {1, 15})
        exercise(output, dk, nq, 65, 1, rows, cases++);
    if (argc == 3) for (int nk : {2048, 8193}) for (int mask : {0, 1, 2})
        exercise(output, 256, 33, nk, mask, rows, cases++);
    require(fclose(output) == 0, "close output");
    fprintf(stderr, "PASS: %u concurrent cases; scratch guards and finite outputs verified\n", cases);
}
