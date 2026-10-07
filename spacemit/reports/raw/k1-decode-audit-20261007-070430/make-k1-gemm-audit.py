#!/usr/bin/env python3
"""Instrument production Q4_0 matrix packing/staging/compute/wait costs."""
from pathlib import Path
import argparse


def generate(text):
    start=text.index('    void forward_mul_mat(ggml_compute_params * params, ggml_tensor * op) {')
    end=text.index('    void forward_mul_mat_id(',start)
    body=text[start:end]
    anchor='''        const int64_t a_k_blks = spacemit_kernels::div_round_up(gemm_k, a_blk_len);'''
    if body.count(anchor)!=1: raise ValueError('unexpected GEMM selection')
    # Wrap only the existing function calls. No arithmetic, partitioning,
    # staging ownership or barrier order changes.
    for old,new in [('gemm_kernel(', 'audit_gemm('),
                    ('quantize_a_row_i8(', 'audit_quant_row('),
                    ('quantize_a_4row_i8(', 'audit_quant_four('),
                    ('spacemit_kernels::rvv::memcpy1d(', 'audit_copy('),
                    ('spacemit_spert_grid_sync()', 'audit_grid()'),
                    ('spine_barrier_wait(', 'audit_pair(')]: body=body.replace(old,new)
    wrappers='''        const char * audit_env = getenv("SPINE_GEMM_AUDIT");
        K1GemmAudit audit(audit_env && strcmp(audit_env, "1") == 0 &&
                          std::is_same_v<BLOC_TYPE, block_q4_0>, ith, gemm_m, gemm_n, gemm_k);
        auto audit_gemm = [&](auto... args) {
            K1GemmSection section(audit, 2);
            return gemm_kernel(args...);
        };
        auto audit_quant_row = [&](auto... args) {
            K1GemmSection section(audit, 0); quantize_a_row_i8(args...);
        };
        auto audit_quant_four = [&](auto... args) {
            K1GemmSection section(audit, 0); quantize_a_4row_i8(args...);
        };
        auto audit_copy = [&](void * dst, const void * src, size_t size) {
            K1GemmSection section(audit, 1);
            if (audit.enabled) audit.copy_bytes += size;
            spacemit_kernels::rvv::memcpy1d(dst, src, size);
        };
        auto audit_grid = [&]() {
            K1GemmSection section(audit, 3); spacemit_spert_grid_sync();
        };
        auto audit_pair = [&](spine_barrier_t * barrier) {
            K1GemmSection section(audit, 4); spine_barrier_wait(barrier);
        };

'''
    body=body.replace(anchor,wrappers+anchor)
    probe='''        void *        tcm_buffer      = spacemit_spert_shared_buffer(&tcm_buffer_size);'''
    if body.count(probe)!=1: raise ValueError('unexpected buffer accessor')
    body=body.replace(probe,probe+'\n        audit.buffer_size = tcm_buffer ? tcm_buffer_size : 0;')
    declarations=r'''
// Per-worker elapsed sections include waiting and clock overhead. Records are
// diagnostic, not a speed comparison. File locking happens after measurement.
struct K1GemmAudit {
    using Clock = std::chrono::steady_clock;
    bool enabled;
    int ith;
    int64_t m,n,k;
    double ns[5] = {};
    uint64_t calls[5] = {};
    uint64_t copy_bytes = 0;
    long buffer_size = 0;
    Clock::time_point begin;
    K1GemmAudit(bool e,int i,int64_t mm,int64_t nn,int64_t kk):enabled(e),ith(i),m(mm),n(nn),k(kk) {
        if (enabled) begin=Clock::now();
    }
    ~K1GemmAudit() {
        if (!enabled) return;
        double total=std::chrono::duration<double,std::nano>(Clock::now()-begin).count();
        fprintf(stderr,"K1_GEMM_AUDIT {\"ith\":%d,\"m\":%ld,\"n\":%ld,\"k\":%ld,\"buffer_size\":%ld,\"copy_bytes\":%lu,\"total_ns\":%.3f,\"section_ns\":[%.3f,%.3f,%.3f,%.3f,%.3f],\"section_calls\":[%lu,%lu,%lu,%lu,%lu]}\n",
                ith,m,n,k,buffer_size,copy_bytes,total,ns[0],ns[1],ns[2],ns[3],ns[4],
                calls[0],calls[1],calls[2],calls[3],calls[4]);
    }
};
struct K1GemmSection {
    K1GemmAudit & a;
    int id;
    K1GemmAudit::Clock::time_point begin;
    K1GemmSection(K1GemmAudit & aa,int i):a(aa),id(i) { if (a.enabled) begin=K1GemmAudit::Clock::now(); }
    ~K1GemmSection() {
        if (a.enabled) {
            a.ns[id]+=std::chrono::duration<double,std::nano>(K1GemmAudit::Clock::now()-begin).count();
            ++a.calls[id];
        }
    }
};
'''
    text=text[:start]+body+text[end:]
    anchor='thread_local TLSContext tls_context;'
    if text.count(anchor)!=1: raise ValueError('unexpected namespace')
    return text.replace('#include <algorithm>','#include <algorithm>\n#include <chrono>',1).replace(anchor,anchor+'\n'+declarations,1)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('source',type=Path); p.add_argument('output',type=Path)
    args=p.parse_args(); args.output.write_text(generate(args.source.read_text()))
