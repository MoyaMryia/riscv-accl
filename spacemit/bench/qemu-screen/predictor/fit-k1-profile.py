#!/usr/bin/env python3
"""从 K1 全部标定样本估计分项成本，保留测量误差和覆盖限制。"""
import argparse
from collections import defaultdict
import math
from pathlib import Path
import statistics
from analyze import load, sha, write, seal
from model import target


def linear(points):
    x=statistics.mean(a for a,b in points); y=statistics.mean(b for a,b in points)
    denominator=math.fsum((a-x)**2 for a,b in points)
    if denominator<=0:raise ValueError('拟合自变量没有变化。')
    slope=math.fsum((a-x)*(b-y) for a,b in points)/denominator
    residuals=[b-y-slope*(a-x) for a,b in points]
    return dict(slope=slope,intercept=y-slope*x,residuals=residuals)


def key_id(key):
    return '|'.join(str(key[k]) for k in ('op','sew','lmul','vl','stride','footprint'))


def fit(board, inventory, output):
    output.mkdir(parents=True,exist_ok=False)
    plan=load(board/'plan.json'); inv=load(inventory)
    if sha(board/'measure')!=plan['binary_sha256'] or inv['elf_sha256']!=plan['binary_sha256']:
        raise ValueError('标定二进制身份不一致。')
    run=board/'run'
    if (run/'exit-status').read_text().strip()!='0' or (run/'phase').read_text().strip()!='complete':
        raise ValueError('板端标定未完整结束。')
    import json
    samples=[json.loads(line) for line in (run/'samples.jsonl').read_text().splitlines()]
    expected={(r['id'],rep,n) for r in plan['records'] for rep in range(plan['repetitions']) for n in plan['lengths']}
    actual=[(s['id'],s['repeat'],s['iterations']) for s in samples]
    if set(actual)!=expected or len(actual)!=len(expected):raise ValueError('标定样本覆盖不一致。')
    for s in samples:
        if not s['valid'] or s['cpu']!=plan['cpu'] or s['cycles']<=0 or s['output']!=s['expected'] or s['enabled']<=0 or s['enabled']!=s['running']:
            raise ValueError('标定包含无效样本。')
    functions={f['symbol']:f for f in inv['functions']}
    indexed={(s['id'],s['repeat'],s['iterations']):s for s in samples}
    grouped=defaultdict(list); fits=[]; frequency=set(); switches=0
    for s in samples:
        frequency.update((s['frequency_before_khz'],s['frequency_after_khz']))
        switches+=s['involuntary_switches']
    for r in plan['records']:
        f=functions[r['id']]
        branches=[i for i in f['instructions'] if i['objdump_mnemonic']=='bne' and target(i) is not None and target(i)<i['address']]
        if len(branches)!=1:raise ValueError('标定函数回边数量不一致。')
        branch=branches[0]
        body=[i for i in f['instructions'] if target(branch)<=i['address']<=branch['address']]
        if len(body)!=r['operations']+3 or any((i['family']!='ime-known-encoding' if r['key']['op']=='vmadot.s8' else i['objdump_mnemonic']!=r['key']['op']) for i in body[:r['operations']]):
            raise ValueError('标定循环与实际指令不一致。')
        if r['key']['op']=='vmadot.s8':
            words=[int(i['encoding'],16) for i in body[:r['operations']]]
            expected=[int(line.split()[1],16) for line in r['body'][:r['operations']]]
            if words!=expected:raise ValueError('IME 标定编码不一致。')
        rep_fits=[]
        for rep in range(plan['repetitions']):
            points=[(n,indexed[(r['id'],rep,n)]['cycles']) for n in plan['lengths']]
            value=linear(points);rep_fits.append(value)
            grouped[(key_id(r['key']),r['mode'],rep)].append((r['operations'],value['slope']))
        fits.append(dict(id=r['id'],body_sha256=__import__('hashlib').sha256(__import__('json').dumps(body,sort_keys=True).encode()).hexdigest(),replicate_fits=rep_fits))
    parameters={}
    for r in plan['records']:
        identity=key_id(r['key']);p=parameters.setdefault(identity,dict(key=r['key'],modes={}))
        if r['mode'] in p['modes']:continue
        values=[linear(grouped[(identity,r['mode'],rep)]) for rep in range(plan['repetitions'])]
        costs=[v['slope'] for v in values]
        positive=all(math.isfinite(c) and c>0 for c in costs)
        dep=r.get('dependency','RAW-chain' if r['key']['op'] not in ('vle32.v','vlse32.v') else 'destination-reuse-no-RAW')
        p['modes'][r['mode']]=dict(chains=r['chains'],cycles_per_operation=statistics.median(costs),
            replicate_cycles_per_operation=costs,measurement_range=[min(costs),max(costs)],
            overhead_intercepts=[v['intercept'] for v in values],
            count_fit_residuals=[v['residuals'] for v in values],status='measured-positive' if positive else 'unstable-fit',
            dependency=dep if r['mode']=='dependent' else 'independent-register-streams')
    profile=dict(schema=2,kind='K1-empirical-component-profile',parameters=parameters,
        evidence=dict(binary_sha256=plan['binary_sha256'],plan_sha256=sha(board/'plan.json'),
            samples_sha256=sha(run/'samples.jsonl'),inventory_sha256=sha(inventory),
            samples=len(samples),keys=len(parameters),cpu=plan['cpu'],frequency_snapshots_khz=sorted(frequency),
            involuntary_switches=switches,counter=plan.get('counter',dict(
                type='PERF_TYPE_HARDWARE',config='PERF_COUNT_HW_CPU_CYCLES',
                scope='legacy generic event; exclude_kernel request does not establish user-only scope'))),
        scope=plan['protocol'],prediction_validation=dict(status='not-yet-validated',
            scope='parameter measurements alone do not prove unseen-kernel accuracy'),
        limits=['warm CPU 0 only','stream cost includes finite independent-chain limits',
                'vector memory latency is not isolated','no multicore bandwidth or coherence model',
                'measurement ranges are not prediction confidence intervals'])
    write(output/'profile.json',profile);write(output/'replicate-fits.json',fits)
    lines=['# K1 分项成本标定','','这些范围只表示重复测量波动，不是新算法预测置信区间。','',
           '| 指令 | SEW | LMUL | VL | 步长 | 工作集／字节 | 依赖链成本 | 独立流成本 |',
           '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for p in parameters.values():
        k=p['key'];a=p['modes']['dependent']['cycles_per_operation'];b=p['modes'].get('independent',{}).get('cycles_per_operation')
        lines.append(f'| {k["op"]} | {k["sew"]} | {k["lmul"]} | {k["vl"]} | {k["stride"]} | {k["footprint"]} | {a:.4f} | {b:.4f} |' if b is not None else f'| {k["op"]} | 0 | 0 | 0 | {k["stride"]} | {k["footprint"]} | {a:.4f} | 未测 |')
    lines+=['','单位为每条被测操作的稳态周期。',
        '依赖链与独立流的指令数量拟合会分离循环控制的固定贡献。',
        '向量加载的依赖模式只复用目的寄存器，不是加载结果的 RAW 依赖链。',
        '随机指针工作集不能自动对应某个物理缓存层级。',
        '跨线程带宽与完整算法精度仍待验证。','']
    (output/'report.md').write_text('\n'.join(lines));seal(output)
    print(output/'profile.json')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('board',type=Path)
    p.add_argument('--inventory',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();fit(a.board,a.inventory,a.output)
