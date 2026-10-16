"""从已核验状态夹具生成固定参数和无优化变量的检查版本。"""


def generate(text):
    def replace(old, new):
        nonlocal text
        if text.count(old) != 1:
            raise ValueError('state fixture anchor differs: ' + old)
        text = text.replace(old, new)

    replace('#include "llama.h"', '#include "llama.h"\n#include "spine-k1-defaults.h"')
    replace('static void select_arm(int arm) {',
        'static void select_arm(int arm) {\n'
        '    if (arm == -1) {\n'
        '        for (const char * name : {"SPINE_K1_FA_GQA", "SPINE_K1_SSM_CONV",\n'
        '                 "SPINE_GDN_PREFILL", "SPINE_K1_GDN_REVISION"}) {\n'
        '            unsetenv(name);\n'
        '        }\n'
        '        return;\n'
        '    }')
    replace('p.n_ctx = 4096; p.n_batch = 32; p.n_ubatch = 32; p.n_seq_max = 1;',
        'p.n_ctx = 4096; p.n_batch = SPINE_K1_DEFAULT_BATCH;\n'
        '    p.n_ubatch = SPINE_K1_DEFAULT_BATCH; p.n_seq_max = 1;')
    replace('p.n_rs_seq = rs; p.n_threads = 4; p.n_threads_batch = 4;',
        'p.n_rs_seq = rs; p.n_threads = SPINE_K1_DEFAULT_THREADS;\n'
        '    p.n_threads_batch = SPINE_K1_DEFAULT_THREADS;')
    replace('llama_n_threads(ctx.get()) == 4 && llama_n_threads_batch(ctx.get()) == 4,',
        'llama_n_threads(ctx.get()) == SPINE_K1_DEFAULT_THREADS &&\n'
        '            llama_n_threads_batch(ctx.get()) == SPINE_K1_DEFAULT_THREADS,')
    replace('    require(bool(ctx), "context allocation");',
        '    require(bool(ctx), "context allocation");\n'
        '    require(llama_n_batch(ctx.get()) == SPINE_K1_DEFAULT_BATCH &&\n'
        '            llama_n_ubatch(ctx.get()) == SPINE_K1_DEFAULT_BATCH, "context batch size differs");')
    replace('    for (int offset = 0; offset < count; offset += 32) {\n'
        '        b.n_tokens = std::min(32, count-offset);',
        '    const int step = std::min(32, SPINE_K1_DEFAULT_BATCH);\n'
        '    for (int offset = 0; offset < count; offset += step) {\n'
        '        b.n_tokens = std::min(step, count-offset);')
    replace('require((arm >= 0 && arm <= 8), "arm");',
        'require((arm >= -1 && arm <= 8), "arm");')
    return text
