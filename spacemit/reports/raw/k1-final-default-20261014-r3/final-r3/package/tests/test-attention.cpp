#include "ggml.h"
#include "ggml-cpu.h"
#if defined(SPINE_K1_BOARD)
#include "spacemit/ime.h"
#endif
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

static void require(bool ok, const char * reason) {
    if (!ok) { fprintf(stderr, "FAIL: %s\n", reason); std::exit(1); }
}

struct Fixture {
    ggml_context * ctx;
    ggml_threadpool_t pool;
    ggml_cgraph * graph;
    ggml_cplan plan;
    ggml_tensor * dst;
    std::vector<float> output;
    std::vector<unsigned char> scratch;
    std::vector<std::pair<ggml_tensor *, std::vector<unsigned char>>> inputs;
    int dim, heads, history, threads;
    bool partials;

    Fixture(int nk, int h, int mask_mode, int pad, int extra=0, int d=256,
            int kv=0, int nth=4, bool ref=false, int seqs=1, bool f32=false)
        : dim(d), heads(h), history(nk), threads(nth) {
        if (!kv) kv = h/4;
        ctx = ggml_init({32*1024*1024 + size_t(nk)*kv*(d+pad)*seqs*8, nullptr, false});
        require(ctx, "context");
        auto * q = ggml_new_tensor_4d(ctx, GGML_TYPE_F32, d, 1, h, seqs);
        const ggml_type type = f32 ? GGML_TYPE_F32 : GGML_TYPE_F16;
        auto * kb = ggml_new_tensor_4d(ctx, type, d+pad, nk, kv, seqs);
        auto * vb = ggml_new_tensor_4d(ctx, type, d+pad, nk, kv, seqs);
        auto * k = ggml_view_4d(ctx, kb, d, nk, kv, seqs, kb->nb[1], kb->nb[2], kb->nb[3], 0);
        auto * v = ggml_view_4d(ctx, vb, d, nk, kv, seqs, vb->nb[1], vb->nb[2], vb->nb[3], 0);
        auto * mask = mask_mode ? ggml_new_tensor_4d(ctx, GGML_TYPE_F16, nk, 1, h, seqs) : nullptr;
        uint32_t state = 42;
        auto next = [&] { state = state*1664525u+1013904223u; return (int(state>>16)-32768)/32768.0f; };
        for (int64_t i=0; i<ggml_nelements(q); ++i) ((float *) q->data)[i] = next();
        for (auto * t : {kb, vb}) for (int64_t i=0; i<ggml_nelements(t); ++i) {
            const float r = next();
            if (f32) ((float *) t->data)[i] = r;
            else ((ggml_fp16_t *) t->data)[i] = ggml_fp32_to_fp16(r);
        }
        if (mask) for (int64_t i=0; i<ggml_nelements(mask); ++i) {
            const bool blocked = mask_mode == 2 || (i % nk > nk/2 && (i/nk)%2 == 0);
            ((ggml_fp16_t *) mask->data)[i] = ggml_fp32_to_fp16(blocked ? -INFINITY : -0.37f*std::fabs(next()));
        }
        dst = ggml_flash_attn_ext(ctx, q, k, v, mask, 1.0f/sqrtf(float(d)),
                                 extra == 1 ? 1.0f : 0.0f, extra == 2 ? 4.0f : 0.0f);
        auto * sinks = extra == 3 ? ggml_new_tensor_1d(ctx, GGML_TYPE_F32, h) : nullptr;
        if (sinks) {
            for (int i=0; i<h; ++i) ((float *) sinks->data)[i] = next();
            dst->src[4] = sinks;
        }
        for (auto * t : {q, kb, vb, mask, sinks}) if (t) {
            const auto * bytes = (const unsigned char *) t->data;
            inputs.push_back({t, {bytes, bytes + ggml_nbytes(t)}});
        }
        output.assign(ggml_nelements(dst)+32, 12345.25f);
        dst->data = output.data()+16;
        graph = ggml_new_graph(ctx);
        ggml_build_forward_expand(graph, dst);
        auto p = ggml_threadpool_params_default(nth);
        pool = ggml_threadpool_new(&p);
        require(pool, "threadpool");
        plan = ggml_graph_plan(graph, nth, pool);
#if defined(SPINE_K1_BOARD)
        const int preferred = ggml_backend_cpu_riscv64_spacemit_num_prefer_cores();
        if (preferred > 0) threads = std::min(nth, preferred);
#endif
        plan.use_ref = ref;
        scratch.assign(plan.work_size+128, 0xa5);
        plan.work_data = scratch.data()+64;
        partials = !ref && seqs == 1 && nk >= 512;
    }
    void run(const char * a, const char * b) {
        setenv("SPINE_K1_FA_DECODE", a, 1);
        setenv("SPINE_K1_FA_GQA", b, 1);
        std::fill(scratch.begin(), scratch.end(), 0xa5);
        std::fill(output.begin(), output.end(), 12345.25f);
        require(ggml_graph_compute(graph, &plan) == GGML_STATUS_SUCCESS, "graph");
        check();
    }
    double compute(int iterations) {
        const auto start = std::chrono::steady_clock::now();
        for (int i=0; i<iterations; ++i) require(ggml_graph_compute(graph, &plan) == GGML_STATUS_SUCCESS, "graph");
        return std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
    }
    void check() const {
        for (size_t i=0; i<16; ++i) require(output[i] == 12345.25f && output[output.size()-1-i] == 12345.25f, "output guards");
        for (size_t i=0; i<64; ++i) require(scratch[i] == 0xa5 && scratch[scratch.size()-1-i] == 0xa5, "scratch guards");
        for (size_t i=16; i<output.size()-16; ++i) require(std::isfinite(output[i]), "finite output");
        for (const auto & input : inputs) require(memcmp(input.first->data, input.second.data(), input.second.size()) == 0, "input changed");
    }
    std::vector<unsigned char> segments() const {
        if (!partials) return {};
        const size_t offset = 64 + threads*(dim*3+16)*sizeof(float);
        const size_t size = heads*threads*(dim+2)*sizeof(float);
        require(offset+size <= scratch.size()-64, "partial capacity");
        return {scratch.begin()+offset, scratch.begin()+offset+size};
    }
    ~Fixture() { ggml_threadpool_free(pool); ggml_free(ctx); }
};

int main(int argc, char ** argv) {
    if (argc == 3 && strcmp(argv[1], "--bench") == 0) {
        require(strcmp(argv[2], "A1") == 0 || strcmp(argv[2], "B1") == 0, "benchmark arm");
        setenv("SPINE_K1_TRACE", "0", 1);
        for (int nk : {256,2048}) for (int heads : {8,16}) {
            Fixture f(nk, heads, 1, 0);
            f.run("0", "0");
            const auto control = f.output;
            const bool a = strcmp(argv[2], "A1") == 0;
            f.run(a ? "1" : "0", a ? "0" : "1");
            require(memcmp(control.data(), f.output.data(), control.size()*4) == 0, "benchmark output");
            for (int block=0; block<6; ++block) for (int arm : (block%2 ? std::vector<int>{1,0} : std::vector<int>{0,1})) {
                setenv("SPINE_K1_FA_DECODE", arm && a ? "1" : "0", 1);
                setenv("SPINE_K1_FA_GQA", arm && !a ? "1" : "0", 1);
                f.compute(1);
                int iterations = 1;
                double elapsed;
                while (true) {
                    elapsed = f.compute(iterations);
                    if (elapsed >= 100) break;
                    require(iterations < 1048576, "calibration limit");
                    iterations *= 2;
                }
                f.check();
                require(memcmp(control.data(), f.output.data(), control.size()*4) == 0, "timed output");
                printf("{\"candidate\":\"%s\",\"block\":%d,\"arm\":%d,\"history\":%d,\"heads\":%d,\"iterations\":%d,\"wall_ms\":%.9f,\"ms_per_call\":%.9f}\n",
                    argv[2],block,arm,nk,heads,iterations,elapsed,elapsed/iterations);
                fflush(stdout);
            }
        }
        return 0;
    }
    require(argc == 1 || (argc == 3 && strcmp(argv[1], "--dump") == 0), "usage: test-attention [--dump FILE]");
    FILE * dump = argc == 3 ? fopen(argv[2], "wb") : nullptr;
    require(argc == 1 || dump, "dump file");
    ggml_time_init();
    int cases = 0;
    auto exercise = [&](int nk, int h, int mask, int pad, int extra=0, int d=256,
                        int kv=0, int nth=4, bool ref=false, int seqs=1, bool f32=false) {
        Fixture f(nk, h, mask, pad, extra, d, kv, nth, ref, seqs, f32);
        f.run("0", "0");
        const auto control = f.output;
        const auto parts = f.segments();
        if (dump) {
            require(fwrite(control.data(), sizeof(float), control.size(), dump) == control.size(), "output dump");
            require(fwrite(parts.data(), 1, parts.size(), dump) == parts.size(), "partial dump");
        }
        for (const auto & mode : std::vector<std::pair<const char *, const char *>>{
                {"1", "0"}, {"0", "1"}, {"1", "1"}, {"invalid", "0"}, {"0", "01"}}) {
            f.run(mode.first, mode.second);
            if (memcmp(control.data(), f.output.data(), control.size()*sizeof(float)) != 0 || parts != f.segments()) {
                fprintf(stderr, "case: history=%d heads=%d mask=%d pad=%d extra=%d dim=%d kv=%d threads=%d ref=%d seqs=%d f32=%d A=%s B=%s\n",
                    nk,h,mask,pad,extra,d,kv,nth,ref,seqs,f32,mode.first,mode.second);
                require(false, "output or partials differ bitwise");
            }
        }
        f.run("1", "0");
        require(memcmp(control.data(), f.output.data(), control.size()*sizeof(float)) == 0, "repeat");
        ++cases;
    };
    for (int nk : {1,255,256,511,512,513,2048}) for (int h : {8,16})
        for (int mask : {0,1,2}) for (int pad : {0,13}) exercise(nk,h,mask,pad);
    for (int extra : {1,2,3}) exercise(513,8,1,0,extra);
    exercise(513,8,1,0,0,128);
    exercise(513,8,1,0,0,256,4);
    for (int nth : {1,2,8}) exercise(513,8,1,0,0,256,0,nth);
    exercise(513,8,1,0,0,256,0,4,true);
    exercise(513,8,1,0,0,256,0,4,false,2);
    exercise(513,8,1,0,0,256,0,4,false,1,true);
    if (dump) require(fclose(dump) == 0, "dump close");
    printf("PASS: %d attention cases; outputs, partials, inputs and guards\n", cases);
}
