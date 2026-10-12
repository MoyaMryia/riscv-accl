#include "ggml.h"
#include "ggml-cpu.h"
#include "spine-k1-ssm-conv.h"
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

int main(int argc, char ** argv) {
    const bool bench = argc == 2 && strcmp(argv[1], "--bench") == 0;
    const bool diagnostic = argc == 2 && strcmp(argv[1], "--diagnose") == 0;
    require(argc == 1 || bench || diagnostic, "usage: test-conv-silu [--bench|--diagnose]");
    if (diagnostic) setenv("SPINE_K1_CONV_SILU_DIAG", "1", 1);
    if (bench) setenv("SPINE_K1_TRACE", "0", 1);
    int cases = 0;
    for (int channels : (bench || diagnostic ? std::vector<int>{6144,8192} : std::vector<int>{1,63,64,65,128,256}))
    for (int tokens : (bench || diagnostic ? std::vector<int>{32} : std::vector<int>{1,31,32,33}))
    for (int seqs : (bench || diagnostic ? std::vector<int>{1} : std::vector<int>{1,2}))
    for (int observation : (bench || diagnostic ? std::vector<int>{0} : std::vector<int>{0,1,2})) {
        auto * ctx = ggml_init({16*1024*1024, nullptr, false});
        require(ctx, "context");
        auto * input = ggml_new_tensor_3d(ctx, GGML_TYPE_F32, channels, tokens+3, seqs);
        auto * weights = ggml_new_tensor_2d(ctx, GGML_TYPE_F32, 4, channels);
        uint32_t seed = 42;
        for (auto * t : {input, weights}) for (int64_t i=0; i<ggml_nelements(t); ++i) {
            seed = seed*1664525u+1013904223u;
            ((float *) t->data)[i] = 4*(int(seed>>16)-32768)/32768.0f;
        }
        const std::vector<float> saved_input((float *) input->data, (float *) input->data+ggml_nelements(input));
        const std::vector<float> saved_weights((float *) weights->data, (float *) weights->data+ggml_nelements(weights));
        auto * conv = spine_k1_ssm_conv_channels_major(ctx, input, weights, 2);
        auto * output = ggml_silu(ctx, conv);
        const size_t count = ggml_nelements(conv);
        std::vector<float> raw(count+32, 12345.25f), final(count+32, 12345.25f);
        conv->data = raw.data()+16;
        output->data = final.data()+16;
        auto * graph = ggml_new_graph(ctx);
        ggml_build_forward_expand(graph, output);
        if (observation == 1) ggml_set_output(conv);
        if (observation == 2) ggml_build_forward_expand(graph, ggml_scale(ctx, conv, 2.0f));
        auto p = ggml_threadpool_params_default(4);
        auto * pool = ggml_threadpool_new(&p);
        auto plan = ggml_graph_plan(graph, 4, pool);
        std::vector<unsigned char> scratch(plan.work_size+128, 0xa5);
        plan.work_data = scratch.data()+64;
        auto run = [&](const char * mode) {
            setenv("SPINE_K1_CONV_SILU", mode, 1);
            std::fill(raw.begin(), raw.end(), 12345.25f);
            std::fill(final.begin(), final.end(), 12345.25f);
            require(ggml_graph_compute(graph, &plan) == GGML_STATUS_SUCCESS, "graph");
            for (auto * values : {&raw, &final}) {
                for (size_t i=0; i<16; ++i) require((*values)[i] == 12345.25f && (*values)[values->size()-1-i] == 12345.25f, "guards");
                for (size_t i=16; i<values->size()-16; ++i) require(std::isfinite((*values)[i]), "finite output");
            }
            for (size_t i=0; i<64; ++i) require(scratch[i] == 0xa5 && scratch[scratch.size()-1-i] == 0xa5, "scratch guards");
            require(memcmp(input->data, saved_input.data(), saved_input.size()*4) == 0, "input changed");
            require(memcmp(weights->data, saved_weights.data(), saved_weights.size()*4) == 0, "weights changed");
        };
        run("0");
        const auto control_raw = raw, control_final = final;
        for (const char * mode : {"1", "1", "01", "invalid"}) {
            run(mode);
            require(memcmp(raw.data(), control_raw.data(), raw.size()*4) == 0, "raw differs bitwise");
            require(memcmp(final.data(), control_final.data(), final.size()*4) == 0, "SiLU differs bitwise");
        }
        plan.use_ref = true;
        run("0");
        const auto reference = final;
        run("1");
        require(reference == final, "reference fallback");
        plan.use_ref = false;
        if (bench) for (int block=0; block<6; ++block)
        for (int arm : (block%2 ? std::vector<int>{1,0} : std::vector<int>{0,1})) {
            setenv("SPINE_K1_CONV_SILU", arm ? "1" : "0", 1);
            require(ggml_graph_compute(graph, &plan) == GGML_STATUS_SUCCESS, "warm graph");
            int iterations = 1;
            double elapsed;
            while (true) {
                const auto start = std::chrono::steady_clock::now();
                for (int i=0; i<iterations; ++i)
                    require(ggml_graph_compute(graph, &plan) == GGML_STATUS_SUCCESS, "timed graph");
                elapsed = std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
                if (elapsed >= 100) break;
                require(iterations < 1048576, "calibration limit");
                iterations *= 2;
            }
            require(memcmp(raw.data(), control_raw.data(), raw.size()*4) == 0, "timed raw");
            require(memcmp(final.data(), control_final.data(), final.size()*4) == 0, "timed SiLU");
            printf("{\"candidate\":\"D\",\"block\":%d,\"arm\":%d,\"channels\":%d,\"tokens\":%d,\"iterations\":%d,\"wall_ms\":%.9f,\"ms_per_call\":%.9f}\n",
                block,arm,channels,tokens,iterations,elapsed,elapsed/iterations);
            fflush(stdout);
        }
        ggml_threadpool_free(pool);
        ggml_free(ctx);
        ++cases;
    }
    printf("PASS: %d convolution/SiLU cases; outputs, observers, inputs and guards\n", cases);
}
