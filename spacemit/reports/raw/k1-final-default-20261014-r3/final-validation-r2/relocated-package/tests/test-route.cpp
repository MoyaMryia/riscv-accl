#include "ggml.h"
#include "ggml-cpu.h"
#include "ggml-backend.h"
#include "ggml-alloc.h"
#include "ime.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

static void require(bool ok, const char * why) {
    if (!ok) { fprintf(stderr, "FAIL: %s\n", why); exit(1); }
}
using Clock = std::chrono::steady_clock;

struct Fixture {
    static constexpr float guard = 12345.25f;
    ggml_context * weights_ctx;
    ggml_context * ctx;
    ggml_backend_buffer_t buffer;
    ggml_tensor * weights;
    ggml_tensor * activation;
    ggml_tensor * dst;
    ggml_threadpool_t pool;
    ggml_cgraph * graph;
    ggml_cplan plan;
    std::vector<float> output, input;
    std::vector<uint8_t> scratch, packed;
    size_t count, packed_size;
    Fixture(int m, int k, int n, ggml_type type = GGML_TYPE_Q4_0) {
        weights_ctx = ggml_init({1024*1024, nullptr, true});
        require(weights_ctx, "weights context");
        weights = ggml_new_tensor_2d(weights_ctx, type, k, n);
        auto buft = ggml_backend_cpu_riscv64_spacemit_buffer_type();
        buffer = ggml_backend_alloc_ctx_tensors_from_buft(weights_ctx, buft);
        require(buffer && weights->data && weights->extra, "SpaceMiT repacked weights");
        uint32_t seed = 42;
        auto next = [&] { seed = seed*1664525u+1013904223u; return ((int)(seed>>16)-32768)/32768.0f; };
        std::vector<float> logical((size_t)k*n);
        for (auto & v : logical) v = next();
        std::vector<uint8_t> quantized(ggml_nbytes(weights));
        require(ggml_quantize_chunk(type, logical.data(), quantized.data(), 0, n, k, nullptr) == quantized.size(), "quantization size");
        ggml_backend_tensor_set(weights, quantized.data(), 0, quantized.size());
        packed_size = ggml_backend_buft_get_alloc_size(buft, weights);
        packed.assign((uint8_t *)weights->data, (uint8_t *)weights->data+packed_size);
        ctx = ggml_init({8*1024*1024+(size_t)m*(k+n)*sizeof(float), nullptr, false});
        require(ctx, "activation context");
        activation = ggml_new_tensor_2d(ctx, GGML_TYPE_F32, k, m);
        input.resize((size_t)m*k);
        for (auto & v : input) v = next();
        memcpy(activation->data, input.data(), input.size()*sizeof(float));
        dst = ggml_mul_mat(ctx, weights, activation);
        count = ggml_nelements(dst);
        output.assign(count+32, guard);
        dst->data = output.data()+16;
        graph = ggml_new_graph(ctx);
        ggml_build_forward_expand(graph, dst);
        auto p = ggml_threadpool_params_default(4);
        for (int i=0; i<4; ++i) p.cpumask[i] = true;
        p.strict_cpu = true;
        pool = ggml_threadpool_new(&p);
        require(pool, "threadpool");
        plan = ggml_graph_plan(graph, 4, pool);
        scratch.assign(plan.work_size+128, 0xa5);
        plan.work_data = scratch.data()+64;
    }
    double run(int iterations=1) {
        const auto start = Clock::now();
        for (int i=0; i<iterations; ++i)
            require(ggml_graph_compute(graph, &plan) == GGML_STATUS_SUCCESS, "production graph compute");
        return std::chrono::duration<double,std::milli>(Clock::now()-start).count();
    }
    void check() {
        for (size_t i=0; i<16; ++i) require(output[i]==guard && output[count+16+i]==guard, "output guards");
        for (size_t i=0; i<64; ++i) require(scratch[i]==0xa5 && scratch[64+plan.work_size+i]==0xa5, "scratch guards");
        for (size_t i=0; i<count; ++i) require(std::isfinite(output[i+16]) && output[i+16]!=guard, "unwritten/nonfinite output");
        require(memcmp(input.data(), activation->data, input.size()*sizeof(float))==0, "activation overwritten");
        require(memcmp(packed.data(), weights->data, packed_size)==0, "packed weights overwritten");
    }
    ~Fixture() {
        ggml_threadpool_free(pool);
        ggml_free(ctx);
        ggml_backend_buffer_free(buffer);
        ggml_free(weights_ctx);
    }
};

int main(int argc, char ** argv) {
    if (argc==5 && strcmp(argv[1], "--bench")==0) {
        int m=atoi(argv[2]), k=atoi(argv[3]), n=atoi(argv[4]);
        require(m>0 && k>0 && k%32==0 && n>0 && n%16==0, "benchmark dimensions");
        Fixture f(m,k,n);
        f.run(); // initialize runtime and log dispatch outside the timer
        int iterations=1;
        double elapsed;
        do {
            elapsed=f.run(iterations);
            if (elapsed>=100) break;
            iterations*=2;
            require(iterations<=1048576, "calibration limit");
        } while (true);
        f.check();
        printf("{\"m\":%d,\"k\":%d,\"n\":%d,\"iterations\":%d,\"wall_ms\":%.9f,\"ms_per_call\":%.9f}\n",
               m,k,n,iterations,elapsed,elapsed/iterations);
        return 0;
    }
    require(argc==3 && strcmp(argv[1], "--dump")==0, "usage: --dump file | --bench m k n");
    FILE * out=fopen(argv[2], "wb"); require(out, "dump file");
    int cases=0;
    auto exercise=[&](int m,int k,int n,ggml_type type=GGML_TYPE_Q4_0) {
        Fixture f(m,k,n,type); f.run(); f.check();
        require(fwrite(f.output.data()+16,sizeof(float),f.count,out)==f.count,"dump write");
        ++cases;
    };
    for (int m : {1,2,3,4,7,16,32})
        for (int k : {32,64,256,2048})
            for (int n : {16,32,128}) exercise(m,k,n);
    for (int m : {1,3,32})
        for (int k : {2560,6144,9216})
            for (int n : {64,128}) exercise(m,k,n);
    // Different trait/quantization must retain its original routing.
    exercise(1,256,64,GGML_TYPE_Q8_0);
    exercise(32,256,64,GGML_TYPE_Q8_0);
    require(fclose(out)==0,"dump close");
    printf("PASS: %d production graph cases; input/output/scratch guards\n",cases);
}
