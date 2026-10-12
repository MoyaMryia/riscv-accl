"""以 K1 实测分项成本重放实际依赖，输出声明场景的性能范围。"""
from collections import Counter
import hashlib
import gzip
import json
import math
from pathlib import Path
import statistics
from analyze import load,sha,write,seal
from model import semantics,vector_context,Cache,INTEGER,BRANCH,LOAD,STORE


def compile_program(directory,inventory,out,bias=0):
    inv=load(inventory)
    if len(inv['functions'])!=1:raise ValueError('成本程序必须对应一个实际函数。')
    index={i['address']+bias:i for i in inv['functions'][0]['instructions']}
    operations=[];operation_index={};threads=[]
    for path in sorted(directory.glob('trace-cpu*.jsonl')):
        target=out/(path.stem+'.jsonl.gz');count=0;end=None;pending=None
        with path.open() as source,gzip.open(target,'wt',compresslevel=1) as dest:
            def flush():
                if pending is not None:dest.write(json.dumps(pending,separators=(',',':'))+'\n')
            for line in source:
                e=json.loads(line)
                if end is not None:raise ValueError('结束记录后仍有事件。')
                if e['kind']=='instruction':
                    flush();count+=1
                    if e['seq']!=count:raise ValueError('实际轨迹顺序不连续。')
                    item=index.get(e['pc'])
                    if item is None or int(item['encoding'],16)!=int(e['encoding'],16) or item['bytes']!=e['size']:
                        raise ValueError('实际指令字节与库存不一致。')
                    signature=(e['pc'],e.get('vl'),e.get('vtype'),e.get('vlenb'),e.get('vstart'))
                    if signature not in operation_index:
                        context,gap=vector_context(e);read,written,gaps=semantics(item,context)
                        if item['family']=='ime-known-encoding':
                            word=int(e['encoding'],16);rd=(word>>7)&31;rs1=(word>>15)&31;rs2=(word>>20)&31
                            if (word&0xfe00707f)==0xe200302b and rd%2==0 and rd<=30 and context and context['sew']==8 and context['lmul']=='1' and context['vl']==32:
                                read={f'v{rd}',f'v{rd+1}',f'v{rs1}',f'v{rs2}'};written={f'v{rd}',f'v{rd+1}'};gaps=[]
                            else:gaps=['IME-shape-not-calibrated']
                        if item['objdump_mnemonic'].startswith('v') and not item['objdump_mnemonic'].startswith('vset') and gap:gaps.append(gap)
                        operation_index[signature]=len(operations)
                        operations.append(dict(pc=e['pc'],name=item['objdump_mnemonic'],family=item['family'],encoding=e['encoding'],
                            context=context,read=sorted(read),write=sorted(written),gaps=gaps))
                    pending=[operation_index[signature],e['segment'],[]]
                elif e['kind']=='memory':
                    if pending is None or e['seq']!=count or e['address']<0 or e['bytes']<=0:raise ValueError('访存事件无对应指令。')
                    pending[2].append([e['address'],e['bytes'],bool(e['store'])])
                elif e['kind']=='end':end=e
                else:raise ValueError('未知轨迹事件。')
            flush()
        if end is None or end['failure'] or end['recorded']!=count or end['instructions']<count or (not end['truncated'] and end['instructions']!=count):
            raise ValueError('轨迹结束状态不完整。')
        threads.append(dict(file=target.name,sha256=sha(target),instructions=count,end=end,trace_sha256=sha(path)))
    if not threads:raise ValueError('没有实际轨迹。')
    write(out/'operations.json',operations)
    result=dict(schema=2,kind='verified-K1-cost-program',elf_sha256=inv['elf_sha256'],inventory_sha256=sha(inventory),
        operations_sha256=sha(out/'operations.json'),threads=threads,
        complete=all(not t['end']['truncated'] for t in threads),scope='one ROI function; outside calls and synchronization are not timed')
    write(out/'program.json',result)
    return result


def parameters(profiles):
    table={};identities=[]
    for path in profiles:
        profile=load(path);identities.append(dict(path=str(path),sha256=sha(path),evidence=profile['evidence']))
        for key,p in profile['parameters'].items():
            if key in table:raise ValueError('分项参数重复。')
            table[key]=p
    return table,identities


def model_identity(identities):
    files=['k1cost.py','model.py','analyze.py']
    definition=dict(version='k1cost-v3',source_sha256={name:sha(Path(__file__).parent/name) for name in files},
                    profile_sha256=sorted(p['sha256'] for p in identities))
    digest=hashlib.sha256(json.dumps(definition,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return digest,definition


def lookup(table,op,memory):
    context=op['context'];name=op['name']
    sew=context['sew'] if context and (name.startswith('v') or op['family']=='ime-known-encoding') else 0
    lmul=context['lmul'] if sew else '0';vl=context['vl'] if sew else 0
    if op['family']=='ime-known-encoding':name='vmadot.s8'
    stride=0;footprint=0
    if name in ('vle32.v','vlse32.v'):
        footprint=4096
        if name=='vlse32.v':
            addresses=[x[0] for x in memory]
            differences={b-a for a,b in zip(addresses,addresses[1:])}
            stride=next(iter(differences)) if len(differences)==1 else None
    if name=='ld':stride=64;footprint=4096
    key='|'.join(map(str,(name,sew,lmul,vl,stride,footprint)))
    return table.get(key),key


def component(table,op,memory,band):
    param,key=lookup(table,op,memory)
    source='measured';gaps=list(op['gaps'])
    def select(mode):
        if band=='central':return mode['cycles_per_operation']
        return mode['measurement_range'][0 if band=='low' else 1]
    if param and all(m['status']=='measured-positive' for m in param['modes'].values()):
        dependent=select(param['modes']['dependent'])
        stream=param['modes'].get('independent')
        occupancy=select(stream) if stream else 1.0
        latency=dependent
        if op['name'] in ('vle32.v','vlse32.v'):
            load=table.get('ld|0|0|0|64|4096')
            latency=max(occupancy,select(load['modes']['dependent'])) if load else max(occupancy,4)
            gaps.append('vector-load-readiness-from-scalar-pointer-chain')
        if op['name'] in LOAD and op['name']!='ld':
            load=table.get('ld|0|0|0|64|4096')
            latency=max(occupancy,select(load['modes']['dependent'])) if load else max(occupancy,4)
            gaps.append('scalar-load-readiness-from-pointer-chain')
        if dependent and param['modes']['dependent'].get('dependency')=='store-address-reuse-no-RAW':
            gaps.append('store-completion-not-isolated')
        if op['name']=='vmv.v.i':gaps.append('constant-vector-result-readiness-not-isolated')
        if op['name']=='ld':gaps.append('scalar-load-throughput-assumed-one-cycle')
    else:
        source='assumed';name=op['name']
        if name in LOAD or name in STORE or 'memory' in op['family']:
            latency,occupancy=(4.0,1.0)
        elif name.startswith(('vset','c.')) or name in INTEGER or name in BRANCH or name in ('jal','jalr'):
            latency,occupancy=(1.0,0.5)
        elif name.startswith(('vf','f')):
            latency,occupancy=(5.0,2.0)
        elif name.startswith('v'):
            latency,occupancy=(3.0,1.0)
        else:latency,occupancy=(4.0,1.0)
        factor=.5 if band=='low' else 2.0 if band=='high' else 1.0
        latency*=factor;occupancy*=factor;gaps.append('uncalibrated-instruction-cost:'+name)
    if min(latency,occupancy)<=0 or not all(math.isfinite(x) for x in (latency,occupancy)):
        raise ValueError('分项成本不是有限正数。')
    port='memory' if memory else 'vector' if op['name'].startswith('v') or op['family']=='ime-known-encoding' else 'float' if op['name'].startswith('f') else 'scalar'
    return latency,occupancy,port,source,gaps,key


def replay_thread(path,operations,table,band,memory_mode):
    l1=Cache(32768,64,8);l2=Cache(524288,64,8)
    pointer={size:table.get(f'ld|0|0|0|64|{size}') for size in (4096,131072,8388608)}
    def pointer_cost(size):
        p=pointer[size]
        if p is None:return {4096:4,131072:12,8388608:100}[size]
        m=p['modes']['dependent'];return m['cycles_per_operation'] if band=='central' else m['measurement_range'][0 if band=='low' else 1]
    l2_penalty=max(0,pointer_cost(131072)-pointer_cost(4096))
    memory_penalty=max(l2_penalty,pointer_cost(8388608)-pointer_cost(4096))
    ready={};ports={};memory_ready={};front=0.0;slots=0;last_segment=None;finished=0.0
    counts=Counter();gaps=Counter();keys=Counter();memo={};segment_count=0;cache_counts=Counter()
    with gzip.open(path,'rt') as source:
        for line in source:
            index,segment,memory=json.loads(line);op=operations[index]
            stride=0
            if op['name']=='vlse32.v' and len(memory)>1:stride=memory[1][0]-memory[0][0]
            cache_key=(index,stride,len(memory))
            if cache_key not in memo:memo[cache_key]=component(table,op,memory,band)
            latency,occupancy,port,kind,missing,key=memo[cache_key]
            counts['instructions']+=1;counts[kind]+=1;gaps.update(missing);keys[key]+=1
            if last_segment!=segment:
                if last_segment is not None:
                    front=max(front,finished);gaps['outside-ROI-time-and-dependencies-unknown']+=1
                ready={};last_segment=segment;segment_count+=1
            delay=0.0;memory_wait=0.0;accessed={}
            for address,size,store in memory:
                for line_address in range(address//64,(address+size-1)//64+1):
                    last_read,last_write=memory_ready.get(line_address,(0.0,0.0))
                    memory_wait=max(memory_wait,last_write,last_read if store else 0.0)
                    accessed[line_address]=accessed.get(line_address,False) or store
                    hit,_=l1.access(line_address,store)
                    cache_counts['L1_hit' if hit else 'L1_miss']+=1
                    if not hit:
                        hit2,_=l2.access(line_address,store)
                        cache_counts['L2_hit' if hit2 else 'L2_miss']+=1
                        if not store and memory_mode=='capacity':delay+=l2_penalty if hit2 else memory_penalty
            candidate=max([front,ports.get(port,0.0),memory_wait]+[ready.get(r,0.0) for r in op['read']+op['write']])
            if candidate>front:front=candidate;slots=0
            if slots>=2:front+=1.0;slots=0
            issue=front;slots+=1;complete=issue+latency+delay
            ports[port]=issue+occupancy
            for register in op['write']:ready[register]=complete
            for address,store in accessed.items():
                last_read,last_write=memory_ready.get(address,(0.0,0.0))
                memory_ready[address]=(last_read,complete) if store else (max(last_read,complete),last_write)
            if accessed:gaps['cache-line-memory-order-is-conservative']+=1
            finished=max(finished,complete)
    return dict(estimated_component_cycles=finished,counts=dict(counts),gaps=dict(gaps),
                keys=dict(keys),segments=segment_count,cache_assumption_counts=dict(cache_counts))


def predict(program,profiles,out):
    meta=load(program/'program.json');operations=load(program/'operations.json')
    if sha(program/'operations.json')!=meta['operations_sha256']:raise ValueError('成本程序操作身份不一致。')
    for t in meta['threads']:
        if sha(program/t['file'])!=t['sha256']:raise ValueError('成本程序轨迹身份不一致。')
    table,identities=parameters(profiles);scenarios=[]
    identity,definition=model_identity(identities)
    for band,memory_mode in [('low','warm'),('central','warm'),('high','capacity')]:
        threads={t['file']:replay_thread(program/t['file'],operations,table,band,memory_mode) for t in meta['threads']}
        costs=[r['estimated_component_cycles'] for r in threads.values()]
        scenarios.append(dict(name=band+'-'+memory_mode,threads=threads,
            cohort_cycles=max(costs),serial_cycles=math.fsum(costs)))
    central=scenarios[1]['threads'];counts=Counter();gaps=Counter()
    for r in central.values():counts.update(r['counts']);gaps.update(r['gaps'])
    counter_scopes=[p['evidence'].get('counter',{}) for p in identities]
    if any(p.get('type')!='PERF_TYPE_RAW' or p.get('config')!='0x22' for p in counter_scopes):
        gaps['legacy-PMU-user-filter-unverified']+=1
    result=dict(schema=3,kind='K1-empirical-trace-cost',model_version='k1cost-v3',
        model_sha256=identity,model_definition=definition,
        program_sha256=sha(program/'program.json'),profiles=identities,scenarios=scenarios,
        native_counter_scopes=counter_scopes,
        coverage=dict(trace_complete=meta['complete'],scope_matched=False,
            calibrated_instruction_fraction=counts['measured']/counts['instructions'],gaps=sorted(gaps)),
        counts=dict(counts),gaps=dict(gaps),automatic_action='none',
        confidence='exploratory; no independent full-kernel residual calibration',
        assumptions=['fluid in-order issue with width two','empirical stream cost used as resource occupancy',
            'WAW waits for previous write; no register renaming','separate scalar, float, vector and memory resource classes',
            'same virtual cache line conservatively orders memory RAW, WAR and WAW',
            'capacity case serializes penalties from random pointer chains','warm case omits extra capacity penalties',
            'virtual-address LRU caches are sensitivity assumptions','per-thread L2 replay omits sharing and coherence',
            'cohort=max and serial=sum declare two thread combinations; synchronization remains unknown'],
        scope=meta['scope'],K1_wall_time_ms=None)
    write(out/'cost.json',result)
    lines=['# K1 轨迹成本估计','','结果用于比较投入方向，不触发任何性能淘汰。',
        '这些范围是声明场景的敏感性范围，不是预测置信区间。',
        f'实际指令成本直接标定覆盖率为 {100*result["coverage"]["calibrated_instruction_fraction"]:.3f}%。',
        f'轨迹完整性为 {meta["complete"]}。','',
        '| 场景 | 并发队列成本／周期 | 串行成本／周期 |','| --- | ---: | ---: |']
    for s in scenarios:lines.append(f'| {s["name"]} | {s["cohort_cycles"]:.3f} | {s["serial_cycles"]:.3f} |')
    lines+=['','并发队列成本采用各线程最大值，串行成本采用各线程之和。',
            '这两个组合不证明实际线程调度或同步耗时。',
            '缺失分项使用显式假设，并降低证据强度。',
            '完整算子与新算法的独立误差校准仍待完成。','']
    (out/'report.md').write_text('\n'.join(lines));return result
