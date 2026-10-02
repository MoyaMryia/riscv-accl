#include "ggml.h"
#include "ggml-cpu.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

static void require(bool ok,const char * why) {
    if (!ok) { fprintf(stderr,"FAIL: %s\n",why); exit(1); }
}
using Clock=std::chrono::steady_clock;

struct Fixture {
    static constexpr float guard=12345.25f;
    ggml_context * ctx;
    ggml_tensor * dst;
    ggml_tensor * state;
    ggml_threadpool * pool;
    ggml_cgraph * graph;
    ggml_cplan plan;
    std::vector<float> output, initial;
    std::vector<uint8_t> scratch, inputs;
    std::vector<ggml_tensor *> tensors;
    size_t count, finite_count;
    bool external;
    Fixture(int s,int h,int hk,int tokens,int seqs,int slots,bool kda,bool ext=false):external(ext) {
        const size_t memory=8*1024*1024+(size_t)s*s*h*seqs*(slots+2)*4+(size_t)s*h*tokens*seqs*24;
        ctx=ggml_init({memory,nullptr,false}); require(ctx,"context");
        auto * q=ggml_new_tensor_4d(ctx,GGML_TYPE_F32,s,hk,tokens,seqs);
        auto * k=ggml_new_tensor_4d(ctx,GGML_TYPE_F32,s,hk,tokens,seqs);
        auto * v=ggml_new_tensor_4d(ctx,GGML_TYPE_F32,s,h,tokens,seqs);
        auto * g=ggml_new_tensor_4d(ctx,GGML_TYPE_F32,kda?s:1,h,tokens,seqs);
        auto * b=ggml_new_tensor_4d(ctx,GGML_TYPE_F32,1,h,tokens,seqs);
        state=ggml_new_tensor_4d(ctx,GGML_TYPE_F32,s,s,h,seqs);
        uint32_t seed=42;
        auto next=[&] { seed=seed*1664525u+1013904223u; return ((int)(seed>>16)-32768)/32768.0f; };
        tensors={q,k,v,g,b,state};
        for (auto * t:tensors) for (int64_t i=0;i<ggml_nelements(t);++i) {
            const float r=next();
            ((float *)t->data)[i]=t==g?-std::fabs(r):t==b?0.5f+0.25f*r:0.1f*r;
        }
        initial.assign((float *)state->data,(float *)state->data+ggml_nelements(state));
        for (auto * t:tensors) {
            const auto * p=(const uint8_t *)t->data;
            inputs.insert(inputs.end(),p,p+ggml_nbytes(t));
        }
        dst=ggml_gated_delta_net(ctx,q,k,v,g,b,state,slots);
        if (ext) ggml_gated_delta_net_set_state_out(dst,state);
        count=ggml_nelements(dst);
        finite_count=(size_t)s*h*tokens*seqs+(ext?0:(size_t)s*s*h*seqs*std::min(slots,tokens));
        output.assign(count+32,guard); dst->data=output.data()+16;
        graph=ggml_new_graph(ctx); ggml_build_forward_expand(graph,dst);
        auto p=ggml_threadpool_params_default(4);
        for (int i=0;i<4;++i) p.cpumask[i]=true;
        p.strict_cpu=true;
        pool=ggml_threadpool_new(&p); require(pool,"threadpool");
        plan=ggml_graph_plan(graph,4,pool);
        scratch.assign(plan.work_size+128,0xa5); plan.work_data=scratch.data()+64;
    }
    double run(int mode,int iterations=1) {
        setenv("SPINE_GDN_PREFILL",mode?"1":"0",1);
        setenv("SPINE_GDN_RVV","1",1);
        const auto start=Clock::now();
        for(int i=0;i<iterations;++i) require(ggml_graph_compute(graph,&plan)==GGML_STATUS_SUCCESS,"graph compute");
        return std::chrono::duration<double,std::milli>(Clock::now()-start).count();
    }
    void reset() {
        std::copy(initial.begin(),initial.end(),(float *)state->data);
        std::fill(output.begin(),output.end(),guard);
    }
    void check() {
        for(size_t i=0;i<16;++i) require(output[i]==guard && output[count+16+i]==guard,"output guard");
        for(size_t i=0;i<64;++i) require(scratch[i]==0xa5 && scratch[64+plan.work_size+i]==0xa5,"scratch guard");
        for(size_t i=0;i<finite_count;++i) require(std::isfinite(output[i+16]),"nonfinite output/state");
        for(size_t i=finite_count;i<count;++i) require(output[i+16]==guard,"unwritten snapshot/tail changed");
        size_t offset=0;
        for(auto * t:tensors) {
            if (!(external && t==state)) require(memcmp(inputs.data()+offset,t->data,ggml_nbytes(t))==0,"input overwritten");
            offset+=ggml_nbytes(t);
        }
    }
    ~Fixture() { ggml_threadpool_free(pool); ggml_free(ctx); }
};

int main(int argc,char ** argv) {
    if (argc==2 && strcmp(argv[1],"--bench")==0) {
        // GGUF metadata: both S128/Hk16; H16 for 2B, H32 for 4B.
        for(int h:{16,32}) for(int tokens:{8,32}) {
            Fixture f(128,h,16,tokens,1,1,false);
            for(int block=0;block<6;++block) for(int mode:(block%2?std::vector<int>{1,0}:std::vector<int>{0,1})) {
                f.reset(); f.run(mode); int iterations=1; double elapsed;
                do { elapsed=f.run(mode,iterations); if(elapsed>=100)break; iterations*=2; require(iterations<=1048576,"calibration"); } while(true);
                f.check();
                printf("{\"block\":%d,\"mode\":%d,\"state_size\":128,\"heads\":%d,\"key_heads\":16,"
                       "\"tokens\":%d,\"iterations\":%d,\"wall_ms\":%.9f,\"ms_per_call\":%.9f}\n",
                       block,mode,h,tokens,iterations,elapsed,elapsed/iterations); fflush(stdout);
            }
        }
        return 0;
    }
    require(argc==1,"usage: test-gdn [--bench]");
    int cases=0;
    auto exercise=[&](int s,int h,int tokens,int seqs,int slots,bool kda,bool ext) {
        Fixture f(s,h,h/2,tokens,seqs,slots,kda,ext);
        f.run(0); f.check(); const auto control=f.output;
        std::vector<float> state0((float *)f.state->data,(float *)f.state->data+ggml_nelements(f.state));
        f.reset(); f.run(1); f.check();
        if (memcmp(control.data(),f.output.data(),control.size()*4)!=0 ||
            memcmp(state0.data(),f.state->data,state0.size()*4)!=0) {
            fprintf(stderr,"case: S%d H%d T%d seq%d K%d kda%d external%d\n",s,h,tokens,seqs,slots,kda,ext);
            require(false,"attention/state differs bitwise");
        }
        ++cases;
    };
    for(int s:{32,128,256}) for(int h:{4,8}) for(int tokens:{1,2,7,32}) for(int seqs:{1,2}) {
        exercise(s,h,tokens,seqs,1,false,false);
        exercise(s,h,tokens,seqs,3,false,false);
        exercise(s,h,tokens,seqs,1,true,false);
        if(tokens==1)exercise(s,h,tokens,seqs,1,false,true);
    }
    for(int h:{16,32}) exercise(128,h,32,1,1,false,false);
    printf("PASS: %d cases; attention/final states bitwise equal; fallbacks, inputs and guards intact\n",cases);
}
