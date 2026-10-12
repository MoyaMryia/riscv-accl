#!/usr/bin/env python3
"""用有界内存重放共享缓存假设，保留冷态与重复调用状态。"""
import argparse
from collections import Counter,defaultdict
import gzip
import json
from pathlib import Path
import time
from analyze import load,write,sha,seal
from model import Cache


def replay(program,quantum,passes,segment_barriers):
    if min(quantum,passes)<=0:raise ValueError('重放参数必须为正数。')
    meta=load(program/'program.json')
    if not meta['complete'] or len(meta['threads'])!=4:raise ValueError('共享缓存重放必须使用完整四线程轨迹。')
    paths=[]
    for t in meta['threads']:
        p=program/t['file']
        if sha(p)!=t['sha256']:raise ValueError('共享缓存输入身份不同。')
        paths.append(p)
    l1=[Cache(32768,64,8) for _ in paths];l2=Cache(524288,64,8)
    owners=defaultdict(set);results=[];start=time.perf_counter()
    for iteration in range(passes):
        files=[gzip.open(p,'rt') for p in paths];iterators=[iter(f) for f in files]
        pending={j:json.loads(next(it)) for j,it in enumerate(iterators)}
        stats=Counter({k:0 for k in ('instructions','line_accesses','L1_dirty_evictions','L2_hit','L2_miss',
                                    'lower_line_fills','lower_dirty_evictions','lower_transfer_bytes')})
        per_thread=[Counter() for _ in paths]
        before_wb=l2.writebacks
        try:
            while pending:
                phase=min(r[1] for r in pending.values()) if segment_barriers else None
                for cpu in list(pending):
                    if phase is not None and pending[cpu][1]!=phase:continue
                    for _ in range(quantum):
                        row=pending[cpu]
                        if phase is not None and row[1]!=phase:break
                        stats['instructions']+=1;blocks={}
                        for address,size,store in row[2]:
                            for block in range(address//64,(address+size-1)//64+1):blocks[block]=blocks.get(block,False) or store
                        for block,store in blocks.items():
                            owners[block].add(cpu);stats['line_accesses']+=1
                            hit,dirty=l1[cpu].access(block,store)
                            per_thread[cpu]['L1_hit' if hit else 'L1_miss']+=1
                            if dirty is not None:
                                lower_hit,_=l2.access(dirty,True)
                                stats['L1_dirty_evictions']+=1;stats['lower_line_fills']+=not lower_hit
                            if not hit:
                                lower_hit,_=l2.access(block,False)
                                stats['L2_hit' if lower_hit else 'L2_miss']+=1;stats['lower_line_fills']+=not lower_hit
                        line=next(iterators[cpu],None)
                        if line is None:del pending[cpu];break
                        pending[cpu]=json.loads(line)
        finally:
            for f in files:f.close()
        stats['lower_dirty_evictions']=l2.writebacks-before_wb
        stats['lower_transfer_bytes']=(stats['lower_line_fills']+stats['lower_dirty_evictions'])*64
        if stats['instructions']!=sum(t['instructions'] for t in meta['threads']):raise ValueError('共享缓存指令数不同。')
        results.append(dict(pass_index=iteration,state='cold-declared-cache' if iteration==0 else 'repeated-call-cache',
                            counts=dict(stats),per_thread=[dict(r) for r in per_thread]))
    return dict(schema=3,program_sha256=sha(program/'program.json'),implementation_sha256=sha(Path(__file__)),quantum_instructions=quantum,
        segment_barriers=segment_barriers,passes=results,elapsed_seconds=time.perf_counter()-start,
        virtual_span_line_bytes=len(owners)*64,cross_thread_lines=sum(len(v)>1 for v in owners.values()),
        parameters=dict(line_bytes=64,private_L1_bytes=32768,shared_L2_bytes=524288,ways=8,replacement='LRU'),
        scope='declared cache traffic and thread order; no hardware DDR traffic or K1 timing claim',
        limits=['virtual index and cache geometry are sensitivity assumptions',
            'no physical translation, coherence, prefetch or TLB model',
            'no inclusive eviction or pending final dirty-line flush',
            'segment alignment requires a caller declaration about external barriers',
            'external callees are absent from ROI traces',
            'lower transfer bytes are modeled traffic; they are not measured DDR bytes'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('program',type=Path)
    p.add_argument('--quantum',type=int,default=64);p.add_argument('--passes',type=int,default=2)
    p.add_argument('--segment-barriers',action='store_true');p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    write(a.output/'shared-cache.json',replay(a.program,a.quantum,a.passes,a.segment_barriers));seal(a.output)
