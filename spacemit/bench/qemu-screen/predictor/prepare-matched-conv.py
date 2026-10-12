#!/usr/bin/env python3
"""建立板端与轨迹共用的完整卷积夹具。"""
import argparse
from pathlib import Path
import shutil
import subprocess
from analyze import sha,write,seal,load

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    source=HERE.parents[1]/'quick-screen/conv.cpp'
    original=source.read_text()
    if original.count('    void step(')!=1:raise ValueError('卷积函数边界不同。')
    (out/'conv-kernel.cpp').write_text(original.replace('    void step(', '    __attribute__((noinline,noclone)) void step('))
    common=source.with_name('common.h').read_text()
    boundary='    void sync() { pthread_barrier_wait(&stage); }'
    if common.count(boundary)!=1:raise ValueError('屏障边界不同。')
    declarations=r'''
struct SyncStats { uint64_t count=0,wall_ns=0,cpu_ns=0; };
static thread_local SyncStats sync_stats;
static thread_local bool sync_measure=false;
static thread_local int sync_counter_fd=-1;
static uint64_t matched_ns(clockid_t clock) {
    timespec value{}; need(clock_gettime(clock,&value)==0,"clock read");
    return uint64_t(value.tv_sec)*1000000000+value.tv_nsec;
}
'''
    common=common.replace('struct Workers {',declarations+'\nstruct Workers {')
    common=common.replace(boundary,r'''    __attribute__((noinline)) void sync() {
        if(sync_counter_fd>=0) need(ioctl(sync_counter_fd,PERF_EVENT_IOC_DISABLE,PERF_IOC_FLAG_GROUP)==0,"sync counter pause");
        if(!sync_measure) { pthread_barrier_wait(&stage); }
        else {
            uint64_t wall=matched_ns(CLOCK_MONOTONIC),cpu=matched_ns(CLOCK_THREAD_CPUTIME_ID);
            pthread_barrier_wait(&stage);
            sync_stats.cpu_ns+=matched_ns(CLOCK_THREAD_CPUTIME_ID)-cpu;
            sync_stats.wall_ns+=matched_ns(CLOCK_MONOTONIC)-wall; ++sync_stats.count;
        }
        if(sync_counter_fd>=0) need(ioctl(sync_counter_fd,PERF_EVENT_IOC_ENABLE,PERF_IOC_FLAG_GROUP)==0,"sync counter resume");
    }''')
    (out/'common.h').write_text(common)
    (out/'matched-common.h').write_text('#pragma once\n#include "common.h"\n')
    shutil.copy2(HERE/'conv-matched.cpp',out/'conv-matched.cpp')
    compiler=(REPO/'lab/toolchain/toolchain/riscv/bin/riscv64-unknown-linux-gnu-g++').resolve()
    binary=out/'matched'
    argv=list(map(str,[compiler,'-O3','-g','-static','-fno-pie','-no-pie','-ffp-contract=off',
        '-march=rv64gcv_zfh_zvfh','-std=c++17',out/'conv-matched.cpp','-pthread','-o',binary]))
    write(out/'build-command.json',argv)
    (out/'compiler-version.log').write_text(subprocess.check_output([compiler,'--version'],text=True))
    with (out/'build.log').open('w') as log:subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,check=True)
    subprocess.run(['python3',HERE.parent/'assembly-inventory.py',binary,out/'inventory',
        '--symbol-regex','_ZN4Conv4stepE','--tool-prefix',str(compiler).removesuffix('g++')],check=True)
    inv=load(out/'inventory/inventory.json')
    if len(inv['functions'])!=1:raise ValueError('必须有唯一的卷积函数。')
    cases=[]
    for c,t in [(6144,8),(8192,8),(6144,32),(8192,32)]:
        cases.append(dict(id=f'conv-C{c}-T{t}',channels=c,tokens=t))
    write(out/'plan.json',dict(schema=3,binary_sha256=sha(binary),symbol=inv['functions'][0]['symbol'],
        counter=dict(type='PERF_TYPE_RAW',config='0x22',scope='K1 U-mode cycle event; run counter-audit first'),
        instruction_counter_scope='generic instruction event; user-only filtering is not established',
        cases=cases,repeats=7,threads=[0,1,2,3],
        scope='same binary and Conv::step; native calls include Workers::sync; ROI trace excludes its body',
        limits=['barrier diagnostics include clock overhead and are separate from primary samples',
                'bench-roi pauses counters in Workers::sync; caller loops and pause boundary instructions remain',
                'bench-roi changes barrier arrival time and does not establish uninstrumented wall performance',
                'native cycles exclude kernel time; wall time includes waits',
                'frequency snapshots do not prove a constant clock']))
    shutil.copy2(HERE/'run-matched-board.sh',out/'run-matched-board.sh')
    seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);main(p.parse_args())
