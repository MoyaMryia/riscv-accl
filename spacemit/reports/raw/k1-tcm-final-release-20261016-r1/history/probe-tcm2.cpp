// Probe2: spine_thread_tcm_malloc bandwidth per tile + ai_core_tcm_size.
#include "spert_abi.h"
#include "spert_engine.hpp"
#include <cstdio>
#include <cstring>
#include <chrono>

extern "C" void probe_kernel(int64_t ctx, void * args) {
    (void) args;
    int tile = (int) spine_grid(ctx, 0);

    int64_t tcm_sz = spine_get_ai_core_tcm_size();
    void * tcm = spine_thread_tcm_malloc(ctx, 131072);

    spert::SharedBufferView v = spert::detail::ctx_shared_buffer();

    if (tile == 0) {
        fprintf(stderr, "[probe2] ai_core_tcm_size=%ld shared=%p tcm_malloc=%p\n",
                (long) tcm_sz, v.data, tcm);
    }
    char * buf = (char *) (tcm ? tcm : v.data);
    size_t sz  = 131072;

    auto t0 = std::chrono::steady_clock::now();
    const int reps = 2000;
    for (int r = 0; r < reps; r++) memset(buf, r, sz);
    auto t1 = std::chrono::steady_clock::now();
    volatile int64_t sink = 0;
    int64_t acc = 0;
    for (int r = 0; r < reps; r++) {
        const int64_t * q = (const int64_t *) buf;
        for (size_t i = 0; i < sz / 8; i += 8) acc += q[i];
    }
    auto t2 = std::chrono::steady_clock::now();
    sink = acc;
    double w_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    double r_ms = std::chrono::duration<double, std::milli>(t2 - t1).count();
    double gb   = (double) sz * reps / 1e9;
    fprintf(stderr, "[probe2] tile=%d buf=%s write=%.2f GB/s read=%.2f GB/s\n",
            tile, tcm ? "tcm_malloc" : "shared", gb / (w_ms / 1e3), gb / (r_ms / 1e3));
    if (tcm) spine_thread_tcm_free(ctx, tcm);
}

int main() {
    int64_t core_ids[4] = {0, 1, 2, 3};
    int64_t stream = spine_require_stream_with_config(4, core_ids);
    if (!stream) { fprintf(stderr, "require_stream failed\n"); return 1; }
    spine_parallel_dispatch_1d(stream, (void *) probe_kernel, nullptr, 4);
    spine_release_stream(stream);
    return 0;
}
