#!/usr/bin/env python3
"""从板端实际二进制分析固定标定小内核，并计算保留测试误差。"""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import queue
import re
import statistics
import sys

from analyze import command, evaluate, load, seal, sha, write
from model import target

HERE = Path(__file__).resolve().parent


def slope(points):
    x = statistics.mean(a for a,b in points)
    y = statistics.mean(b for a,b in points)
    value = sum((a-x)*(b-y) for a,b in points)/sum((a-x)**2 for a,b in points)
    return {'slope':value,'intercept':y-value*x,
            'residuals':[b-(value*a+y-value*x) for a,b in points]}


def main(args):
    out = args.output.resolve(); out.mkdir(parents=True,exist_ok=False)
    plan = load(args.board/'plan.json')
    run_dir = args.board/'run' if (args.board/'run').is_dir() else args.board
    protocol = args.board/'validation-protocol.json'
    if sha(protocol) != plan['protocol_sha256']: raise ValueError('验收协议身份不同')
    if (run_dir/'exit-status').read_text().strip() != '0': raise ValueError('板端标定夹具失败')
    samples = [json.loads(line) for line in (run_dir/'samples.jsonl').read_text().splitlines()]
    if any(not r['valid'] or r['enabled'] != r['running'] or r['output'] != r['expected'] for r in samples):
        raise ValueError('板端样本无效，必须保留失败记录')
    expected = {(r['id'],n,rep) for r in plan['records'] for n in plan['lengths'] for rep in range(plan['repetitions'])}
    actual = [(r['id'],r['iterations'],r['repeat']) for r in samples]
    if len(actual) != len(set(actual)) or set(actual) != expected: raise ValueError('原始样本覆盖不同')
    sample_index = {(r['id'],r['iterations'],r['repeat']):r for r in samples}
    groups = defaultdict(dict)
    for item in plan['records']:
        if item['split']=='test': groups[item['group']][item['arm']] = item
    for group,arms in groups.items():
        for n in plan['lengths']:
            checks = {sample_index[(item['id'],n,rep)]['vector_checksum'] for item in arms.values() for rep in range(plan['repetitions'])}
            outputs = {sample_index[(item['id'],n,rep)]['output'] for item in arms.values() for rep in range(plan['repetitions'])}
            if len(checks) != 1 or len(outputs) != 1: raise ValueError('保留测试组的完整向量对照不同：'+group)
    binary = args.board/'measure'
    if command([sys.executable,HERE.parent/'assembly-inventory.py',binary,out/'inventory',
        '--symbol-regex','^cal_','--tool-prefix',args.tool_prefix],out,'inventory'):
        raise ValueError('无法读取实际二进制')
    inv = load(out/'inventory/inventory.json')
    functions = {f['symbol']:f for f in inv['functions']}
    slots = queue.Queue()
    allowed = sorted(__import__('os').sched_getaffinity(0))
    for core in allowed[:args.jobs]: slots.put(core)
    jobs,records = [],[]
    for item in plan['records']:
        function = functions[item['symbol']]
        branches = [i for i in function['instructions'] if i['objdump_mnemonic']=='bne' and target(i) is not None and target(i)<i['address']]
        if len(branches)!=1: raise ValueError('标定内核必须只有一个回边')
        branch = branches[0]
        body = [i for i in function['instructions'] if target(branch) <= i['address'] <= branch['address']]
        if len(body)!=len(item['body']): raise ValueError('实际循环指令数量不同')
        folder = out/item['id']; folder.mkdir()
        lines = ['.text','# LLVM-MCA-RISCV-LMUL M1','# LLVM-MCA-RISCV-SEW E32','.Lbody:']
        for insn in body:
            name,operands = insn['objdump_mnemonic'],insn['operands']
            operands = re.sub(r'\b[0-9a-f]+\s+<[^>]+>','.Lbody',operands)
            lines.append(name+' '+operands)
            if name=='vsetivli':
                sew = re.search(r'\be(8|16|32|64),',operands)[1]
                lines += ['# LLVM-MCA-RISCV-LMUL M1','# LLVM-MCA-RISCV-SEW E'+sew]
        (folder/'actual-body.s').write_text('\n'.join(lines)+'\n')
        write(folder/'actual-body.json',body)
        values = [(s['iterations'],s['cycles']) for s in samples if s['id']==item['id']]
        fit = slope(values)
        if fit['slope'] <= 0: raise ValueError('实测周期斜率不是正数')
        record = {k:item[k] for k in ('id','group','split','arm','scope')}
        record.update(measured_cycles=fit['slope'],measured_fit=fit,cycle_scope='steady-state cycles per loop iteration',
            model_coverage_complete=not item['group'].startswith('mixed-load'),
            model_gaps=['VL=8 is smaller than VLMAX; MCA model uses VLMAX'] if item['group'].startswith('mixed-load') else [],
            actual_binary_sha256=sha(binary),actual_body_sha256=sha(folder/'actual-body.json'))
        records.append(record)
        for n in plan['lengths']: jobs.append((folder,n,record,len(body)))
    def run(job):
        folder,n,record,count = job
        core = slots.get()
        try:
            code = command(['taskset','-c',str(core),args.mca,'-mtriple=riscv64','-mcpu=spacemit-x60',
                '-mattr=+v','--skip-unsupported-instructions=none','-iterations='+str(n),folder/'actual-body.s'],folder,'mca-'+str(n))
            if code: raise ValueError('标定循环模型无法分析：'+record['id'])
            log = (folder/('mca-'+str(n)+'.log')).read_text()
            instructions = int(re.search(r'^Instructions:\s+(\d+)',log,re.M)[1])
            if instructions != n*count: raise ValueError('模型指令数量不同')
            cycles = int(re.search(r'^Total Cycles:\s+(\d+)',log,re.M)[1])
            return record['id'],n,cycles
        finally: slots.put(core)
    with ThreadPoolExecutor(max_workers=min(args.jobs,len(allowed))) as pool: modeled = list(pool.map(run,jobs))
    for record in records:
        points = [(n,c) for identity,n,c in modeled if identity==record['id']]
        record['predicted_fit'] = slope(points); record['predicted_cycles'] = record['predicted_fit']['slope']
    data = {'schema':1,'records':records,'pairs':[{'control':arms['control']['id'],'candidate':arms['candidate']['id']} for arms in groups.values()],
        'plan_sha256':sha(args.board/'plan.json'),'samples_sha256':sha(run_dir/'samples.jsonl'),
        'mca_sha256':sha(args.mca),'scope':plan['scope']}
    write(out/'data.json',data)
    result = evaluate(protocol,out/'data.json')
    write(out/'evaluation.json',result)
    seal(out)
    print(json.dumps({k:v for k,v in result.items() if k not in ('cycle_errors','pairs')},indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board',type=Path); parser.add_argument('--mca',type=Path,required=True)
    parser.add_argument('--tool-prefix',type=Path,required=True); parser.add_argument('--jobs',type=int,default=5)
    parser.add_argument('--output',type=Path,required=True)
    main(parser.parse_args())
