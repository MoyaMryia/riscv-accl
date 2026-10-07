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

static void require(bool good, const char * reason) {
    if (!good) { fprintf(stderr, "FAIL: %s\n", reason); std::exit(1); }
}

// Exercise the real CPU graph, including concat, history layout conversion,
// convolution, and state write-back. No synthetic replacement kernel.
struct Fixture {
    static constexpr float guard = 12345.25f;
    ggml_context * ctx;
    ggml_threadpool_t pool;
    ggml_cgraph * graph;
    ggml_cplan plan;
    ggml_tensor * x; ggml_tensor * w; ggml_tensor * history;
    ggml_tensor * output; ggml_tensor * tail_output;
    std::vector<float> xdata, wdata, hdata, result, state;
    std::vector<unsigned char> scratch;
    int channels, taps, tokens, sequences, mode, padding;

    Fixture(int c, int k, int t, int s, int m, int p = 0)
        : channels(c), taps(k), tokens(t), sequences(s), mode(m), padding(p) {
        ctx = ggml_init({8*1024*1024 + size_t(c)*(t+k)*s*32, nullptr, false});
        require(ctx, "context allocation");
        x = ggml_new_tensor_3d(ctx, GGML_TYPE_F32, c, t, s);
        w = ggml_new_tensor_2d(ctx, GGML_TYPE_F32, k, c);
        history = ggml_new_tensor_3d(ctx, GGML_TYPE_F32, k-1, c, s);
        // Strided projection inputs check that graph construction respects nb[];
        // concat creates the contiguous convolution input in both graph modes.
        x->nb[1] = (c+p)*sizeof(float); x->nb[2] = t*x->nb[1];
        xdata.assign(size_t(c+p)*t*s+32, guard);
        wdata.assign(size_t(k)*c+32, guard);
        hdata.assign(size_t(k-1)*c*s+32, guard);
        x->data = xdata.data()+16; w->data = wdata.data()+16;
        history->data = hdata.data()+16;
        uint32_t seed = 123;
        auto next = [&] { seed = seed*1664525u+1013904223u; return (int(seed>>16)-32768)/32768.0f; };
        for (int q=0; q<s; ++q) for (int a=0; a<t; ++a) for (int j=0; j<c; ++j)
            xdata[16+(q*t+a)*(c+p)+j] = next();
        for (int j=0; j<c; ++j) for (int a=0; a<k; ++a) wdata[16+j*k+a] = next();
        for (size_t j=16; j<hdata.size()-16; ++j) hdata[j] = next();
        ggml_tensor * input;
        ggml_tensor * tail;
        if (m == 0) {
            input = ggml_concat(ctx, history, ggml_transpose(ctx, x), 0);
            output = ggml_ssm_conv(ctx, input, w);
            tail = ggml_view_3d(ctx, input, k-1, c, s,
                input->nb[1], input->nb[2], t*sizeof(float));
        } else {
            input = ggml_concat(ctx, ggml_cont(ctx, ggml_transpose(ctx, history)), x, 1);
            output = spine_k1_ssm_conv_channels_major(ctx, input, w, m);
            tail = ggml_transpose(ctx, ggml_view_3d(ctx, input, c, k-1, s,
                input->nb[1], input->nb[2], t*input->nb[1]));
            // Preserve a diagnostic switch for reproducing the fork's broken
            // CPY transpose path. The candidate materializes this cropped view
            // before writing it into the persistent time-major cache.
            if (!std::getenv("SPINE_SSM_DIAG_LEGACY_COPY")) tail = ggml_cont(ctx, tail);
        }
        tail_output = ggml_new_tensor_3d(ctx, GGML_TYPE_F32, k-1, c, s);
        result.assign(size_t(c)*t*s+32, guard);
        state.assign(size_t(k-1)*c*s+32, guard);
        output->data = result.data()+16; tail_output->data = state.data()+16;
        graph = ggml_new_graph(ctx);
        ggml_build_forward_expand(graph, ggml_cpy(ctx, tail, tail_output));
        ggml_build_forward_expand(graph, output);
        auto params = ggml_threadpool_params_default(4);
        for (int cpu=0; cpu<4; ++cpu) params.cpumask[cpu] = true;
        params.strict_cpu = true;
        pool = ggml_threadpool_new(&params);
        require(pool, "threadpool allocation");
        plan = ggml_graph_plan(graph, 4, pool);
        scratch.assign(plan.work_size+128, 0xa5);
        plan.work_data = scratch.data()+64;
    }
    double run(int iterations = 1) {
        const auto start = std::chrono::steady_clock::now();
        for (int i=0; i<iterations; ++i)
            require(ggml_graph_compute(graph, &plan) == GGML_STATUS_SUCCESS, "CPU graph execution");
        return std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
    }
    void check() {
        for (const auto * values : {&xdata,&wdata,&hdata,&result,&state})
            for (size_t i=0; i<16; ++i)
                require((*values)[i] == guard && (*values)[values->size()-16+i] == guard, "tensor guards");
        for (size_t i=0; i<64; ++i)
            require(scratch[i] == 0xa5 && scratch[64+plan.work_size+i] == 0xa5, "scratch guards");
        // Independent ordered-FP32 reference; explicit rounding prevents FMA.
        for (int q=0; q<sequences; ++q) for (int a=0; a<tokens; ++a) for (int j=0; j<channels; ++j) {
            float sum = 0;
            for (int tap=0; tap<taps; ++tap) {
                const int pos = a+tap;
                const float value = pos < taps-1
                    ? hdata[16+(q*channels+j)*(taps-1)+pos]
                    : xdata[16+(q*tokens+pos-taps+1)*(channels+padding)+j];
                volatile float product = value*wdata[16+j*taps+tap];
                sum += product;
            }
            const float actual = result[16+(q*tokens+a)*channels+j];
            require(std::isfinite(actual) && std::memcmp(&sum, &actual, sizeof(float)) == 0, "convolution bitwise reference");
        }
        for (int q=0; q<sequences; ++q) for (int j=0; j<channels; ++j) for (int tap=0; tap<taps-1; ++tap) {
            const int pos = tokens+tap;
            const float expected = pos < taps-1
                ? hdata[16+(q*channels+j)*(taps-1)+pos]
                : xdata[16+(q*tokens+pos-taps+1)*(channels+padding)+j];
            const float actual = state[16+(q*channels+j)*(taps-1)+tap];
            if (actual != expected) {
                fprintf(stderr, "HISTORY_MISMATCH mode=%d channels=%d taps=%d tokens=%d sequences=%d padding=%d seq=%d channel=%d tap=%d expected=%.9g actual=%.9g\n",
                    mode,channels,taps,tokens,sequences,padding,q,j,tap,expected,actual);
                require(false, "history write-back");
            }
        }
    }
    ~Fixture() { ggml_threadpool_free(pool); ggml_free(ctx); }
};

int main(int argc, char ** argv) {
    if (argc == 8 && std::strcmp(argv[1], "--case") == 0) {
        const int mode=std::atoi(argv[2]), channels=std::atoi(argv[3]), taps=std::atoi(argv[4]);
        const int tokens=std::atoi(argv[5]), sequences=std::atoi(argv[6]), padding=std::atoi(argv[7]);
        require(mode>=0 && mode<=2 && channels>0 && taps>1 && tokens>0 && sequences>0 && padding>=0,"case arguments");
        Fixture f(channels,taps,tokens,sequences,mode,padding);
        f.run(); f.check(); f.run(); f.check();
        printf("PASS: targeted case mode=%d channels=%d taps=%d tokens=%d sequences=%d padding=%d\n",mode,channels,taps,tokens,sequences,padding);
        return 0;
    }
    if (argc == 7 && std::strcmp(argv[1], "--bench") == 0) {
        const int mode = std::atoi(argv[2]), channels = std::atoi(argv[3]);
        const int taps = std::atoi(argv[4]), tokens = std::atoi(argv[5]), sequences = std::atoi(argv[6]);
        require(mode >= 0 && mode <= 2 && channels > 0 && taps > 1 && tokens > 0 && sequences > 0, "bench arguments");
        Fixture f(channels,taps,tokens,sequences,mode); f.run(); f.check();
        int count=1; double elapsed;
        do { elapsed=f.run(count); if (elapsed<200) count*=2; } while(elapsed<200 && count<1048576);
        f.check();
        printf("{\"mode\":%d,\"channels\":%d,\"taps\":%d,\"tokens\":%d,\"sequences\":%d,\"iterations\":%d,\"wall_ms\":%.9g,\"ms_per_call\":%.9g}\n",
            mode,channels,taps,tokens,sequences,count,elapsed,elapsed/count);
        return 0;
    }
    require(argc == 4, "usage: test-ssm MODE --dump FILE or --bench MODE CHANNELS TAPS TOKENS SEQUENCES");
    const int mode=std::atoi(argv[1]); require(mode>=0 && mode<=2 && std::strcmp(argv[2],"--dump")==0, "numeric arguments");
    FILE * file=std::fopen(argv[3],"wb"); require(file,"output dump");
    int cases=0;
    for (int channels : {1,7,8,9,31,129,1024,6144,8192})
        for (int taps : {3,4,9}) for (int tokens : {1,3,32,33})
            for (int sequences : {1,2}) for (int padding : {0,3}) {
                Fixture f(channels,taps,tokens,sequences,mode,padding);
                const auto x=f.xdata, w=f.wdata, h=f.hdata;
                f.run(); f.check(); f.run(); f.check();
                require(f.xdata==x && f.wdata==w && f.hdata==h,"input tensors changed");
                require(std::fwrite(f.result.data()+16,sizeof(float),f.result.size()-32,file)==f.result.size()-32,"output dump write");
                require(std::fwrite(f.state.data()+16,sizeof(float),f.state.size()-32,file)==f.state.size()-32,"state dump write");
                ++cases;
            }
    require(std::fclose(file)==0,"output dump close");
    printf("PASS: %d convolution graph cases; mode=%d; exact FP32/state/guards/strides/repeat checks\n",cases,mode);
}
