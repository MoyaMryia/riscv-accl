#!/usr/bin/env python3
"""Add branch identity and input-byte counters to the existing GEMM audit."""
import argparse
import importlib.util
from pathlib import Path


def module(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('unexpected audit anchor: ' + old[:80])
    return text.replace(old, new)


def generate(text):
    text = module('make-k1-gemm-routing').generate(text)
    text = module('make-k1-gemm-audit').generate(text)
    # Routing is inserted after the shared-buffer accessor; measure the buffer
    # actually used after that routing decision, rather than the original TCM.
    text = replace_once(text, '\n        audit.buffer_size = tcm_buffer ? tcm_buffer_size : 0;', '')
    text = replace_once(text, '        if (getenv("SPINE_TCM_DEBUG")) {',
                        '        audit.buffer_size = tcm_buffer ? tcm_buffer_size : 0;\n        if (getenv("SPINE_TCM_DEBUG")) {')
    text = replace_once(text, '#include <chrono>', '#include <chrono>\n#include <tuple>')
    text = replace_once(text, '    uint64_t copy_bytes = 0;', '''    uint64_t copy_bytes = 0;
    uint64_t packing_input_bytes = 0;
    const char * weight = "";
    const char * activation = "";
    const void * input = nullptr;
    int nth = 0;
    char safe_weight[128] = {};
    char safe_activation[128] = {};''')
    text = replace_once(text,
        '    K1GemmAudit(bool e,int i,int64_t mm,int64_t nn,int64_t kk):enabled(e),ith(i),m(mm),n(nn),k(kk) {',
        '''    K1GemmAudit(bool e,int i,int64_t mm,int64_t nn,int64_t kk,
                int threads,const ggml_tensor * w,const ggml_tensor * a):enabled(e),ith(i),m(mm),n(nn),k(kk) {
        nth = threads;
        input = a->data;
        snprintf(safe_weight, sizeof(safe_weight), "%s", w->name);
        snprintf(safe_activation, sizeof(safe_activation), "%s", a->name);
        for (char * s : {safe_weight, safe_activation}) {
            for (char * p=s; *p; ++p) {
                if (*p == '"' || *p == '\\\\' || static_cast<unsigned char>(*p) < 32) *p='_';
            }
        }
        weight = safe_weight;
        activation = safe_activation;''')
    text = replace_once(text,
        'std::is_same_v<BLOC_TYPE, block_q4_0>, ith, gemm_m, gemm_n, gemm_k);',
        'std::is_same_v<BLOC_TYPE, block_q4_0>, ith, gemm_m, gemm_n, gemm_k, nth, src0, src1);')
    text = replace_once(text,
        '            K1GemmSection section(audit, 0); quantize_a_row_i8(args...);',
        '''            K1GemmSection section(audit, 0);
            if (audit.enabled) audit.packing_input_bytes += std::get<2>(std::forward_as_tuple(args...)) * sizeof(float);
            quantize_a_row_i8(args...);''')
    text = replace_once(text,
        '            K1GemmSection section(audit, 0); quantize_a_4row_i8(args...);',
        '''            K1GemmSection section(audit, 0);
            if (audit.enabled) audit.packing_input_bytes += 4 * std::get<2>(std::forward_as_tuple(args...)) * sizeof(float);
            quantize_a_4row_i8(args...);''')
    text = replace_once(text,
        '        fprintf(stderr,"K1_GEMM_AUDIT {',
        '''        const auto begin_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(begin.time_since_epoch()).count();
        fprintf(stderr,"K1_DECODE_AUDIT {''')
    text = replace_once(text,
        r'"ith\":%d,\"m\":%ld',
        r'"ith\":%d,\"nth\":%d,\"weight\":\"%s\",\"activation\":\"%s\",\"input\":\"%p\",\"begin_ns\":%lld,\"packing_input_bytes\":%lu,\"m\":%ld')
    text = replace_once(text,
        '                ith,m,n,k,buffer_size,copy_bytes,total,',
        '                ith,nth,weight,activation,input,(long long)begin_ns,packing_input_bytes,m,n,k,buffer_size,copy_bytes,total,')
    return text


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(generate(args.source.read_text()))
