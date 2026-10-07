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
    (void)mode; // M1 mode is fixed per process; compare independent full dumps.
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
static void snapshot(llama_context * ctx, FILE * out, int vocab, unsigned rs, int reset, int prefix) {
    const float *values=llama_get_logits_ith(ctx,-1); require(values,"missing logits");
    for (int i=0;i<vocab;++i) require(std::isfinite(values[i]),"nonfinite logits");
    require(fwrite(values,sizeof(float),vocab,out)==size_t(vocab),"snapshot write");
    printf("{\"rs\":%u,\"reset\":%d,\"prefix\":%d,\"vocab\":%d}\n",rs,reset,prefix,vocab);
    fflush(stdout);
}
int main(int argc,char **argv) {
    if (argc!=3) { fprintf(stderr,"usage: state MODEL DUMP\n"); return 1; }
    ggml_backend_load_all(); llama_backend_init();
    try {
        auto p=llama_model_default_params(); p.n_gpu_layers=0;
        std::unique_ptr<llama_model,decltype(&llama_model_free)> model(llama_model_load_from_file(argv[1],p),llama_model_free);
        require(bool(model),"model allocation");
        const int vocab=llama_vocab_n_tokens(llama_model_get_vocab(model.get()));
        FILE *out=fopen(argv[2],"wb"); require(out,"dump file");
        for (unsigned rs : {0u,3u}) {
            auto ctx=context(model.get(),rs);
            for (int reset=0;reset<2;++reset) {
                if (reset) llama_memory_clear(llama_get_memory(ctx.get()),true);
                int prefix=0;
                for (int count : {32,1,31,32}) {
                    decode(ctx.get(),0,prefix,count,vocab); prefix+=count;
                    snapshot(ctx.get(),out,vocab,rs,reset,prefix);
                }
            }
        }
        require(fclose(out)==0,"dump close");
        printf("PASS: 16 full-vocabulary snapshots; chunk/decode/reset/RS-reference\n");
    } catch (const std::exception &e) { fprintf(stderr,"FAIL: %s\n",e.what()); return 1; }
    llama_backend_free();
}
