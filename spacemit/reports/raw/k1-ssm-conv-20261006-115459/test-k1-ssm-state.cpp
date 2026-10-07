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
    auto p=llama_context_default_params();
    p.n_ctx=256; p.n_batch=32; p.n_ubatch=32; p.n_seq_max=1;
    p.n_rs_seq=rs; p.n_threads=4; p.n_threads_batch=4;
    p.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_ENABLED;
    p.type_k=GGML_TYPE_F16; p.type_v=GGML_TYPE_F16;
    Context ctx(llama_init_from_model(model,p),llama_free);
    require(bool(ctx),"context allocation"); return ctx;
}
static void decode(llama_context * ctx, int mode, int start, int count, int vocab) {
    setenv("SPINE_K1_SSM_CONV",mode==0?"0":mode==1?"1":"2",1);
    auto b=llama_batch_init(32,0,1);
    for (int offset=0; offset<count; offset+=32) {
        b.n_tokens=std::min(32,count-offset);
        for (int i=0; i<b.n_tokens; ++i) {
            int pos=start+offset+i;
            b.token[i]=100+(pos*17+11)%(vocab-100);
            b.pos[i]=pos; b.n_seq_id[i]=1; b.seq_id[i][0]=0;
            b.logits[i]=i==b.n_tokens-1;
        }
        if (llama_decode(ctx,b)) { llama_batch_free(b); throw std::runtime_error("decode failed"); }
    }
    llama_batch_free(b);
}
static void compare(llama_context * reference, llama_context * candidate, int vocab, int mode, unsigned rs, int reset, int prefix) {
    const float * a=llama_get_logits_ith(reference,-1);
    const float * b=llama_get_logits_ith(candidate,-1);
    require(a && b,"missing logits");
    double max_abs=0;
    for (int i=0; i<vocab; ++i) {
        require(std::isfinite(a[i]) && std::isfinite(b[i]),"nonfinite logits");
        max_abs=std::max(max_abs,std::abs(double(a[i])-b[i]));
    }
    bool equal=std::memcmp(a,b,size_t(vocab)*sizeof(float))==0;
    printf("{\"mode\":%d,\"rs\":%u,\"reset\":%d,\"prefix\":%d,\"bitwise_equal\":%s,\"max_abs\":%.17g}\n",
        mode,rs,reset,prefix,equal?"true":"false",max_abs);
    fflush(stdout); require(equal,"candidate logits differ");
}
int main(int argc,char ** argv) {
    if (argc!=3) { fprintf(stderr,"usage: state-probe MODEL CANDIDATE_MODE\n"); return 1; }
    const int mode=std::atoi(argv[2]);
    ggml_backend_load_all(); llama_backend_init();
    try {
        require(mode==1 || mode==2,"candidate mode");
        auto p=llama_model_default_params(); p.n_gpu_layers=0;
        std::unique_ptr<llama_model,decltype(&llama_model_free)> model(llama_model_load_from_file(argv[1],p),llama_model_free);
        require(bool(model),"model allocation");
        const int vocab=llama_vocab_n_tokens(llama_model_get_vocab(model.get()));
        for (unsigned rs : {0u,3u}) {
            auto reference=context(model.get(),rs), candidate=context(model.get(),rs);
            for (int reset=0; reset<2; ++reset) {
                if (reset) {
                    llama_memory_clear(llama_get_memory(reference.get()),true);
                    llama_memory_clear(llama_get_memory(candidate.get()),true);
                }
                int prefix=0;
                for (int count : {3,29,1,3}) {
                    decode(reference.get(),0,prefix,count,vocab);
                    decode(candidate.get(),mode,prefix,count,vocab);
                    prefix+=count;
                    compare(reference.get(),candidate.get(),vocab,mode,rs,reset,prefix);
                }
            }
        }
        printf("PASS: 16 full-vocabulary state comparisons; mode=%d; chunk/decode/reset/RS-fallback\n",mode);
    } catch (const std::exception & e) { fprintf(stderr,"FAIL: %s\n",e.what()); return 1; }
    llama_backend_free();
}
