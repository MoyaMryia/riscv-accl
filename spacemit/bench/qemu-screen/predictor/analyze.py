#!/usr/bin/env python3
"""统一检查候选身份、动态轨迹、模型覆盖和独立误差。"""
import argparse
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import json
from itertools import combinations
import math
import os
from pathlib import Path
import re
import shlex
import statistics
import subprocess
import sys

from model import cache_replay, cfg, semantics, vector_context

HERE = Path(__file__).resolve().parent


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''): digest.update(chunk)
    return digest.hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def seal(out):
    (out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(out))+'\n'
        for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS'))


def load(path):
    return json.loads(Path(path).read_text())


def command(argv, out, name, env=None, timeout=120):
    argv = list(map(str,argv))
    write(out/(name+'-command.json'),{'argv':argv,'environment':env})
    with (out/(name+'.log')).open('w') as stream:
        try:
            code = subprocess.run(argv,stdout=stream,stderr=subprocess.STDOUT,
                                  env=os.environ | (env or {}),timeout=timeout).returncode
        except subprocess.TimeoutExpired: code = 'timeout'
    write(out/(name+'-exit.json'),{'returncode':code})
    return code


def inventory(elf, out, symbol, tool_prefix, supplied=None):
    if supplied:
        inv = load(supplied['path'])
        if sha(supplied['path']) != supplied['sha256'] or inv['elf_sha256'] != sha(elf):
            raise ValueError('外部汇编清单身份不同')
        if len(inv['functions']) != 1 or inv['functions'][0]['symbol'] != symbol:
            raise ValueError('外部汇编清单的符号不同')
        write(out/'supplied-inventory.json',inv)
        return inv
    code = command([sys.executable,HERE.parent/'assembly-inventory.py',elf,out/'inventory',
                    '--symbol-regex','^'+re.escape(symbol)+'$','--tool-prefix',tool_prefix],out,'inventory')
    if code: raise ValueError('实际汇编提取失败')
    return load(out/'inventory/inventory.json')


def coverage(inventories):
    records = []
    for path in inventories:
        inv = load(path)
        for function in inv['functions']:
            contexts = cfg(function)
            by_pc = {r['pc']:r for r in contexts['vector_uses']}
            unknown = Counter()
            for item in function['instructions']:
                context = None
                vector_use = by_pc.get(item['address'])
                if vector_use and not vector_use['ambiguous']:
                    match = re.search(r'e(8|16|32|64),\s*(m(?:f[248]|[1248]))',vector_use['contexts'][0])
                    if match:
                        token = match[2]
                        lmul = Fraction(1,int(token[2:])) if token.startswith('mf') else Fraction(int(token[1:]))
                        context = {'lmul':str(lmul),'sew':int(match[1]),'tail_agnostic':False,'mask_agnostic':False}
                _,_,gaps = semantics(item,context)
                unknown.update(gaps)
            records.append({'symbol':function['symbol'],'elf_sha256':inv['elf_sha256'],
                'inventory_sha256':sha(path),'static_instructions':function['static_instructions'],
                'cfg':contexts,'semantic_gaps':dict(unknown),'status':'coverage-audit',
                'static_dependency_limit':'SEW and LMUL require unique CFG context; tail and mask dependencies are conservative; AVL is not proved',
                'K1_cycles':None,'automatic_performance_rejection':False})
    return records


def read_trace(path, function, bias=0):
    index = {i['address']+bias:i for i in function['instructions']}
    rows = []
    previous, end = None, None
    edges, gaps, contexts, mnemonics, branches = Counter(),Counter(),Counter(),Counter(),Counter()
    writers, readers = {},defaultdict(set)
    cross_domain = Counter()
    memory_writers = {}
    memory_providers = set()
    memory_RAW_edges = memory_RAW_bytes = 0
    memory_unknown = 0
    load_bytes = store_bytes = 0
    for line in Path(path).read_text().splitlines():
        event = json.loads(line)
        if end: raise ValueError('轨迹结束记录后还有事件')
        if event['kind'] == 'end': end = event; continue
        if event['kind'] == 'instruction':
            memory_RAW_edges += len(memory_providers); memory_providers.clear()
            if event['seq'] != 1+sum(mnemonics.values()): raise ValueError('轨迹指令顺序不连续')
            if event['pc'] not in index: raise ValueError('轨迹地址不属于固定二进制')
            item = index[event['pc']]
            if int(event['encoding'],16) != int(item['encoding'],16) or event['size'] != item['bytes']:
                raise ValueError('轨迹指令字节与固定二进制不同')
            event['item'] = item
            context, gap = vector_context(event)
            event['context'] = context
            isvector = item['objdump_mnemonic'].startswith('v') and not item['objdump_mnemonic'].startswith('vset')
            if isvector:
                if gap: gaps[gap] += 1
                elif context:
                    contexts[json.dumps(context,sort_keys=True)] += 1
                    if context['vl'] != context['vlmax']: gaps['MCA-partial-VL-not-validated'] += 1
                if not (int(event['encoding'],16) >> 25 & 1) and event.get('v0') is None:
                    gaps['mask-register-unavailable'] += 1
            if previous and event['segment'] == previous['segment']:
                if event['pc'] <= previous['pc']: branches[(previous['pc'],event['pc'])] += 1
            else:
                writers.clear(); readers.clear()
                memory_writers.clear()
                if previous: gaps['outside-ROI-dependency-boundary'] += 1
            read, written, missing = semantics(item,context)
            gaps.update(missing)
            for register in read:
                if register in writers:
                    edges['RAW'] += 1
                    before = writers[register][1]
                    after = 'vector' if isvector else 'scalar'
                    if before != after: cross_domain[before+'->'+after] += 1
                readers[register].add(event['seq'])
            for register in written:
                if register in writers: edges['WAW'] += 1
                edges['WAR'] += sum(n != event['seq'] for n in readers[register])
                writers[register] = (event['seq'],'vector' if isvector else 'scalar')
                readers[register].clear()
            mnemonics[item['mnemonic']] += 1
            previous = event
        elif event['kind'] == 'memory':
            if previous is None or event['seq'] != previous['seq']: raise ValueError('访存事件没有对应指令')
            if not isinstance(event['address'],int) or event['address'] < 0 or event['bytes'] <= 0: raise ValueError('访存参数无效')
            if event['store']: store_bytes += event['bytes']
            else: load_bytes += event['bytes']
            for address in range(event['address'],event['address']+event['bytes']):
                if event['store']:
                    if len(memory_writers) < 1048576 or address in memory_writers:
                        memory_writers[address] = event['seq']
                    else: gaps['memory-dependency-address-cap'] += 1
                elif address in memory_writers:
                    provider = memory_writers[address]
                    if provider != event['seq']:
                        memory_providers.add(provider); memory_RAW_bytes += 1
                else: memory_unknown += 1
        else: raise ValueError('未知轨迹事件')
        rows.append(event)
    if not end or end['failure']: raise ValueError('轨迹缺少有效结束记录')
    if end['recorded'] != sum(mnemonics.values()): raise ValueError('轨迹结束计数不一致')
    memory_RAW_edges += len(memory_providers)
    if end['truncated']: gaps['trace-truncated'] += 1
    return rows, {'trace_sha256':sha(path),'instructions':sum(mnemonics.values()),'end':end,
        'load_bytes':load_bytes,'store_bytes':store_bytes,'mnemonics':dict(mnemonics),
        'vector_contexts':[dict(json.loads(k),instructions=v) for k,v in contexts.items()],
        'dependency_edges':dict(edges),'cross_domain_RAW':dict(cross_domain),
        'address_dependency_edges':{'RAW':memory_RAW_edges,'overlap_bytes':memory_RAW_bytes,
            'bytes_without_ROI_writer':memory_unknown,'scope':'per-thread exact virtual-byte RAW; reset at external boundaries; no cross-thread coherence'},
        'observed_backedges':[{'from':a,'to':b,'count':n} for (a,b),n in branches.items()],
        'gaps':dict(gaps),'dependency_status':'conservative-register-groups; lane and memory dependencies incomplete'}


def mca(rows, tool, out, maximum):
    instructions = [r for r in rows if r['kind']=='instruction']
    chosen = instructions[:maximum]
    result = {'status':'model-coverage-insufficient','instructions':len(chosen),
              'scope':'one dynamic window; no cache or inter-thread timing','K1_cycles':None,
              'window_is_complete_trace':len(chosen)==len(instructions),'gaps':[]}
    lines = ['.text']
    targets = set()
    if len({r['segment'] for r in chosen})>1: result['gaps'].append('outside-ROI-boundaries-not-timed')
    for row in chosen:
        item = row['item']; name = item['objdump_mnemonic']; operands = item['operands']
        if item['family'] in ('ime-known-encoding','unresolved-encoding'):
            result['gaps'].append('IME-or-unknown-timing')
            lines.append('.4byte 0x'+item['encoding'] if item['bytes']==4 else '.2byte 0x'+item['encoding'])
            continue
        if name.startswith('v') and not name.startswith('vset'):
            context = row['context']
            if not context:
                result['gaps'].append('vector-context-missing'); continue
            lmul = Fraction(context['lmul'])
            token = 'M'+str(lmul.numerator) if lmul >= 1 else 'MF'+str(lmul.denominator)
            lines += ['# LLVM-MCA-RISCV-LMUL '+token,'# LLVM-MCA-RISCV-SEW E'+str(context['sew'])]
            if context['vl'] != context['vlmax']: result['gaps'].append('partial-VL')
        def label(match):
            targets.add(match[1]); return '.Lpc_'+match[1]
        operands = re.sub(r'\b([0-9a-f]+)\s+<[^>]+>',label,operands)
        lines.append(name+' '+operands)
    if len(chosen) != len(instructions): result['gaps'].append('window-truncated')
    lines += ['.set .Lpc_'+pc+', 0x'+pc for pc in sorted(targets)]
    (out/'dynamic-window.s').write_text('\n'.join(lines)+'\n')
    if any(g in result['gaps'] for g in ('IME-or-unknown-timing','vector-context-missing')):
        return result
    code = command([tool,'-mtriple=riscv64','-mcpu=spacemit-x60','-mattr=+v,+zfh,+zvfh',
        '--skip-unsupported-instructions=none','-iterations=1','-resource-pressure',out/'dynamic-window.s'],out,'mca',timeout=90)
    result['returncode'] = code
    log = (out/'mca.log').read_text()
    result['diagnostics'] = [s for s in log.splitlines() if 'warning:' in s or 'error:' in s]
    if code: result['status'] = 'model-instruction-unsupported' if 'error:' in log else 'fixture-failed'; return result
    for label in ('Instructions','Total Cycles','Block RThroughput'):
        match = re.search(r'^'+re.escape(label)+r':\s+([0-9.]+)',log,re.M)
        if match: result[label] = float(match[1])
    if result.get('Instructions') != len(chosen): result['status'] = 'fixture-failed'; return result
    result['status'] = 'local-dynamic-window-unvalidated'
    result['gaps'] += ['branch-prediction','MCA-memory-alias-default','unvalidated-X60-model','no-cache-overlap']
    return result


def trace_plan(plan_path, out, args):
    if min(args.max_instructions,args.mca_window,args.max_mca_threads)<=0:
        raise ValueError('轨迹和模型上限必须为正数')
    plan = load(plan_path)
    result = {'schema':1,'plan_sha256':sha(plan_path),'status':'running','cases':[],
              'automatic_performance_rejection':False,'K1_prediction_accuracy':'unvalidated'}
    write(out/'result.json',result)
    if command([plan['qemu'],'--version'],out,'qemu-version',timeout=10): raise ValueError('QEMU 版本检查失败')
    for path,digest in plan.get('sources',{}).items():
        if sha(path) != digest: raise ValueError('固定源码身份不同：'+path)
    flags = shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','glib-2.0'],text=True))
    plugin = out/'trace.so'
    if command(['cc','-std=c11','-O2','-shared','-fPIC','-fvisibility=hidden','-Wall','-Wextra','-Werror',
        '-I'+str(Path(plan['header']).parent),HERE/'trace.c','-o',plugin,*flags],out,'build-plugin'):
        raise ValueError('轨迹插件构建失败')
    tool_prefix = str(Path(plan['nm']).with_name('riscv64-unknown-linux-gnu-'))
    result['identities'] = {p:sha(p) for p in (plan['qemu'],plan['header'],str(plugin),str(HERE/'trace.c'))}
    if args.mca:
        result['identities'][str(args.mca)] = sha(args.mca)
        command([args.mca,'--version'],out,'mca-version')
    ids = set()
    for case in plan['cases']:
        name = case['id']
        if not re.fullmatch(r'[A-Za-z0-9_-]+',name) or name in ids: raise ValueError('用例标识无效')
        ids.add(name)
        record = {'id':name,'arms':{},'status':'running'}; result['cases'].append(record)
        for arm in ('control','candidate'):
            item = case[arm]; elf = Path(item['elf'])
            if sha(elf) != item['sha256']: raise ValueError('目标二进制身份不同')
            if 'reuse' in item:
                reuse = item['reuse']; saved = load(reuse['result'])
                if sha(reuse['result']) != reuse['sha256']: raise ValueError('复用结果身份不同')
                previous_case = next(c for c in saved['cases'] if c['id']==reuse['case'])
                previous_arm = previous_case['arms'][reuse['arm']]
                if previous_case['status']!='needs-board' or previous_arm['elf_sha256']!=item['sha256']:
                    raise ValueError('复用结果没有通过既定功能检查')
                if previous_arm.get('image_sha256',previous_arm['elf_sha256']) != item.get('image_sha256',item['sha256']):
                    raise ValueError('复用代码映像身份不同')
                if sha(reuse['dump']) != previous_arm['dump_sha256']: raise ValueError('复用完整转储身份不同')
                paths = list(Path(reuse['trace_directory']).glob('trace-cpu*.jsonl'))
                if {sha(p) for p in paths}!={t['trace_sha256'] for t in previous_arm['threads'].values()}:
                    raise ValueError('复用轨迹身份不同')
                record['arms'][arm] = previous_arm | {'reused_from':reuse}
                write(out/'result.json',result)
                continue
            folder = out/(name+'-'+arm); folder.mkdir()
            image = Path(item.get('image',elf))
            if sha(image) != item.get('image_sha256',item['sha256']): raise ValueError('实际代码映像身份不同')
            inv = inventory(image,folder,item['symbol'],tool_prefix,item.get('inventory'))
            if len(inv['functions']) != 1: raise ValueError('热点函数不唯一')
            function = inv['functions'][0]
            bias = item.get('load_bias',0)
            first = function['start']+bias
            dump_name = item.get('dump_filename','complete.bin')
            if Path(dump_name).name != dump_name: raise ValueError('转储文件名必须是普通文件名')
            dump = folder/dump_name
            option = f'{plugin},start={first},end={first+function["size_bytes"]},out={folder}/trace,max={args.max_instructions}'
            argv = [plan['qemu'],*plan.get('qemu_args',[]),'-cpu',plan['cpu'],'-plugin',option,elf,
                    *[word.replace('{dump}',str(dump)) for word in item['args']]]
            if not any('{dump}' in word for word in item['args']): raise ValueError('完整转储参数缺失')
            code = command(argv,folder,'qemu',item.get('env'),plan['timeout_seconds'])
            if code:
                record['status'] = 'unsupported-instruction' if code == -4 else 'fixture-failed'
                result['status'] = 'stopped'; write(out/'result.json',result); return result
            if not dump.is_file() or dump.stat().st_size == 0: raise ValueError('完整转储缺失')
            paths = sorted(folder.glob('trace-cpu*.jsonl'))
            policy = case.get('roi_thread_policy')
            if policy:
                if not policy['minimum'] <= len(paths) <= policy['maximum']:
                    raise ValueError('实际热点线程标识总数超出固定范围')
            elif len(paths) != case['roi_threads']: raise ValueError('实际热点线程数不同')
            traces = {}; summaries = {}
            for path in paths:
                cpu = int(re.search(r'cpu(\d+)\.',path.name)[1])
                rows, summary = read_trace(path,function,bias)
                traces[cpu] = rows; summaries[cpu] = summary
                if args.mca and len(summaries) <= args.max_mca_threads:
                    mca_out = folder/f'mca-cpu{cpu}'; mca_out.mkdir()
                    summary['mca'] = mca(rows,args.mca,mca_out,args.mca_window)
            mapping = {str(cpu):i for i,cpu in enumerate(sorted(traces))}
            parameters = {'thread_to_core':mapping,'core_to_cluster':{str(i):i//4 for i in mapping.values()},
                'line_bytes':64,'l1_bytes':32768,'l2_bytes':524288,'l1_ways':8,'l2_ways':8,
                'replacement':'LRU','write_policy':'write-back; write-allocate',
                'parameter_status':'capacity from K1 manual; all other cache parameters assumed; target mapping declared'}
            caches = [cache_replay(traces,parameters,mode) for mode in ('serial','round-robin')] if len(traces) <= 8 and case.get('cache_model',True) else []
            record['arms'][arm] = {'elf_sha256':sha(elf),'image_sha256':sha(image),'dump_sha256':sha(dump),'dump_bytes':dump.stat().st_size,
                'symbol':item['symbol'],'load_bias':bias,'threads':summaries,'cfg':cfg(function),
                'cache_scenarios':caches,'distinct_thread_ids':len(traces),
                'concurrent_thread_count':'not inferred from lifetime thread IDs',
                'mca_thread_limit':args.max_mca_threads,
                'scope_gaps':([] if caches else ['cache replay requires declared lifetime-thread cohorts and target schedule'])}
            write(out/'result.json',result)
        a,b = (record['arms'][arm] for arm in ('control','candidate'))
        if a['dump_sha256'] != b['dump_sha256'] or a['dump_bytes'] != b['dump_bytes']:
            record['status'] = 'numeric-stop'; result['status'] = 'stopped'; write(out/'result.json',result); return result
        record['status'] = 'needs-board'
        record['numerical_status'] = 'complete-dumps-identical'
        write(out/'result.json',result)
    result['status'] = 'complete-needs-board'; write(out/'result.json',result)
    return result


def evaluate(protocol_path, data_path):
    protocol,data = load(protocol_path),load(data_path)
    if protocol.get('actual_gain_threshold') != .03 or protocol.get('automatic_performance_rejection') is not False:
        raise ValueError('实际 3% 门槛与禁止自动淘汰的规则不能改变')
    rows = data['records']
    ids = [r['id'] for r in rows]
    if len(ids) != len(set(ids)): raise ValueError('标定记录标识重复')
    train = [r for r in rows if r['split']=='train']; test = [r for r in rows if r['split']=='test']
    if any(r['split'] not in ('train','test','retrospective') for r in rows): raise ValueError('未知数据划分')
    if {r['group'] for r in train} & {r['group'] for r in test}: raise ValueError('训练组与测试组重叠')
    for r in train+test:
        if r['group'] not in protocol[r['split']+'_groups']: raise ValueError('记录没有预先固定的数据组')
        for key in ('predicted_cycles','measured_cycles'):
            if not isinstance(r[key],(float,int)) or not math.isfinite(r[key]) or r[key] <= 0: raise ValueError('周期值必须为正有限数')
    result = {'schema':1,'protocol_sha256':sha(protocol_path),'data_sha256':sha(data_path),
        'automatic_performance_rejection':False,'status':'insufficient-independent-data',
        'cycle_errors':[],'pairs':[],'retrospective_count':sum(r['split']=='retrospective' for r in rows)}
    if not train or not test: return result
    scale = sum(r['predicted_cycles']*r['measured_cycles'] for r in train)/sum(r['predicted_cycles']**2 for r in train)
    result['train_scale'] = scale
    by_id = {r['id']:r for r in test}
    errors = []
    for r in test:
        predicted = r['predicted_cycles']*scale
        error = abs(predicted/r['measured_cycles']-1); errors.append(error)
        result['cycle_errors'].append({'id':r['id'],'predicted_cycles':predicted,'measured_cycles':r['measured_cycles'],
            'signed_cycle_error':predicted-r['measured_cycles'],'absolute_relative_error':error})
    pair_errors,ranking,false_rejection = [],0,0
    paired_ids = set()
    for pair in data.get('pairs',[]):
        a,b = by_id[pair['control']],by_id[pair['candidate']]
        if a['group'] != b['group']: raise ValueError('配对数据组不同')
        identity = (a['id'],b['id'])
        if identity in paired_ids or a['id']==b['id']: raise ValueError('重复或无效候选配对')
        paired_ids.add(identity)
        measured = 1-b['measured_cycles']/a['measured_cycles']
        predicted = 1-b['predicted_cycles']/a['predicted_cycles']
        error = abs(predicted-measured); pair_errors.append(error)
        wrong = measured*predicted < 0; ranking += wrong
        risk = measured >= .03 and predicted < .03; false_rejection += risk
        e = max(errors); ratio = 1-predicted
        interval = [1-ratio*(1+e)/(1-e),1-ratio*(1-e)/(1+e)] if e < 1 else None
        result['pairs'].append(dict(pair,measured_gain=measured,predicted_gain=predicted,error_percentage_points=100*error,
            ranking_wrong=wrong,false_rejection_risk=risk,observed_error_gain_interval=interval,
            decision='needs-board',interval_scope='observed test maximum; no population confidence bound'))
    order_errors = ties = 0
    comparisons = []
    for a,b in combinations(result['pairs'],2):
        if a.get('ranking_group','declared-relative-gain') != b.get('ranking_group','declared-relative-gain'): continue
        measured_order = a['measured_gain']-b['measured_gain']
        predicted_order = a['predicted_gain']-b['predicted_gain']
        wrong = measured_order*predicted_order < 0
        tied = predicted_order==0 and measured_order!=0
        order_errors += wrong; ties += tied
        comparisons.append({'a':a['candidate'],'b':b['candidate'],'measured_gain_difference':measured_order,
            'predicted_gain_difference':predicted_order,'wrong':wrong,'predicted_tie':tied})
    result.update(cycle_error_median=statistics.median(errors),cycle_error_max=max(errors),
        relative_change_error_max_percentage_points=100*max(pair_errors) if pair_errors else None,
        direction_errors=ranking,pair_order_errors=order_errors,predicted_ties=ties,
        ranking_errors=ranking+order_errors,ranking_comparisons=comparisons,
        false_rejection_risks=false_rejection,independent_test_groups=len({r['group'] for r in test}))
    enough = result['independent_test_groups'] >= protocol['minimum_test_groups'] and len(pair_errors) >= protocol['minimum_pairs']
    if enough:
        result['status'] = 'ranking-accepted' if (result['cycle_error_median'] <= protocol['cycle_error_median_max'] and
            result['cycle_error_max'] <= protocol['cycle_error_max'] and max(pair_errors) <= protocol['relative_change_error_max'] and
            ranking+order_errors==0 and false_rejection==0) else 'model-validation-failed'
    if any(not r.get('model_coverage_complete',True) for r in train+test):
        result['coverage_status'] = 'model-coverage-insufficient'
        if result['status']=='ranking-accepted': result['status']='model-coverage-insufficient'
    result['scope'] = data.get('scope','declared dataset only')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action',required=True)
    p = sub.add_parser('coverage'); p.add_argument('inventories',type=Path,nargs='+')
    p = sub.add_parser('trace'); p.add_argument('plan',type=Path); p.add_argument('--mca',type=Path)
    p.add_argument('--max-instructions',type=int,default=200000)
    p.add_argument('--mca-window',type=int,default=1024)
    p.add_argument('--max-mca-threads',type=int,default=4)
    p = sub.add_parser('evaluate'); p.add_argument('protocol',type=Path); p.add_argument('data',type=Path)
    p = sub.add_parser('replay'); p.add_argument('directory',type=Path); p.add_argument('inventory',type=Path)
    p.add_argument('--load-bias',type=int,default=0)
    p = sub.add_parser('compile-cost'); p.add_argument('directory',type=Path); p.add_argument('inventory',type=Path); p.add_argument('--load-bias',type=int,default=0)
    p = sub.add_parser('cost'); p.add_argument('program',type=Path); p.add_argument('--profiles',type=Path,nargs='+',required=True)
    p = sub.add_parser('rank'); p.add_argument('plan',type=Path)
    p = sub.add_parser('suite'); p.add_argument('--traces',type=Path,nargs='+',required=True)
    p.add_argument('--coverage',type=Path); p.add_argument('--validation',type=Path)
    p.add_argument('--native',type=Path)
    for p in sub.choices.values(): p.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(); out = args.output.resolve(); out.mkdir(parents=True,exist_ok=False)
    try:
        if args.action == 'compile-cost':
            from k1cost import compile_program
            result = compile_program(args.directory,args.inventory,out,args.load_bias)
        elif args.action == 'cost':
            from k1cost import predict
            result = predict(args.program,args.profiles,out)
        elif args.action == 'rank':
            from priority import rank
            result = rank(args.plan,out)
        elif args.action == 'coverage': result = {'schema':1,'records':coverage(args.inventories)}
        elif args.action == 'trace': result = trace_plan(args.plan,out,args)
        elif args.action == 'evaluate': result = evaluate(args.protocol,args.data)
        elif args.action == 'replay':
            inv = load(args.inventory)
            if len(inv['functions']) != 1: raise ValueError('重放输入必须只有一个热点')
            result = {'schema':1,'inventory_sha256':sha(args.inventory),'elf_sha256':inv['elf_sha256'],'threads':{}}
            paths = sorted(args.directory.glob('trace-cpu*.jsonl'))
            if not paths: raise ValueError('没有轨迹文件')
            for path in paths:
                _,summary = read_trace(path,inv['functions'][0],args.load_bias)
                result['threads'][path.name] = summary
        else:
            from summarize import summarize
            result = summarize(args.traces,args.coverage,args.validation,out,args.native)
        write(out/'result.json',result)
        if args.action not in ('suite','rank','cost'): (out/'report.md').write_text('# K1 候选分析结果\n\n'
            '本结果对应同目录 result.json。\n'
            '已实现：身份检查、路径记录、保守寄存器依赖、缓存假设重放与误差验收接口。\n'
            '已验证范围必须按本次 result.json 的实际记录判断。\n'
            '待验证：K1 周期精度、缓存参数、线程交错、一致性与完整 IME 时序。\n'
            '未实现：自动性能淘汰与完整系统模拟。\n'
            '数值检查必须通过。性能结果用于安排投入和补测。\n')
    except Exception as error:
        existing = load(out/'result.json') if (out/'result.json').exists() else {}
        existing.update(status='fixture-failed',error=str(error)); write(out/'result.json',existing)
        raise
    finally:
        write(out/'source-identities.json',{str(p):sha(p) for p in sorted(HERE.iterdir()) if p.suffix in ('.py','.c','.json')})
        seal(out)
    print(out/'result.json')


if __name__ == '__main__': main()
