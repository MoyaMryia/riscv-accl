#!/usr/bin/env python3
"""在共用锁内构建、检查数值并采集训练分组。"""
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

ROOT = Path.cwd().resolve()
BASE = Path('/home/moyamryia/Projects/riscv-accl-bench-2026-09-27')
SOURCE = BASE/'k1-layout-20260930-153134/source'
OLD = {'ime': BASE/'k1-ime-20261002-184503', 'conv': BASE/'k1-ssm-conv-20261006-115459'}

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def digest(path):
    return hashlib.file_digest(open(path, 'rb'), 'sha256').hexdigest()

def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2)+'\n')

def command(args, env=None, timeout=300):
    result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=timeout)
    with open('commands.jsonl', 'a') as out:
        out.write(json.dumps({'time': now(), 'argv': [str(x) for x in args], 'returncode': result.returncode})+'\n')
    if result.returncode:
        raise RuntimeError(f'{args}: {result.returncode}\n{result.stdout}\n{result.stderr}')
    return result

def snapshot():
    paths = [Path('/proc/loadavg'), Path('/proc/stat')]
    paths += list(Path('/sys/class/thermal').glob('thermal_zone*/temp'))
    paths += list(Path('/sys/devices/system/cpu').glob('cpu[0-9]*/cpufreq/scaling_cur_freq'))
    return {'time': now(), 'files': {str(p): p.read_text().strip() for p in paths if p.exists()},
            'processes': subprocess.run(['ps','-eo','pid,comm,pcpu'],text=True,capture_output=True,check=True).stdout}

def env_for(family):
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = str(ROOT/family/'lib')
    env['SPINE_FA_WIDE_TILE'] = '1'
    return env

def prepare():
    (ROOT/'numeric').mkdir()
    (ROOT/'timing').mkdir()
    save('host.json', {'time':now(),'uname':command(['uname','-a']).stdout,
                      'cpuinfo':Path('/proc/cpuinfo').read_text(), 'environment': {'SPINE_FA_WIDE_TILE':'1'}})
    for family, old in OLD.items():
        root = ROOT/family
        (root/'lib').mkdir(parents=True)
        shutil.copytree(SOURCE/'ggml/include', root/'include')
        for path in old.glob('*provenance.json'):
            shutil.copy2(path, root/path.name)
        if family=='ime':
            fixture = old/'test-k1-ime.cpp'
            shutil.copy2(SOURCE/'ggml/src/ggml-cpu/spacemit/ime_kernels.h', root/'include/ime_kernels.h')
            for name in ['baseline-ime1.cpp','candidate-ime1.cpp','candidate-ime1.patch']:
                if (old/name).is_file(): shutil.copy2(old/name,root/name)
            binary = old/'test-ime'
        else:
            fixture = old/'test-k1-ssm-conv.cpp'
            for name in ['spine-k1-ssm-conv.h','spine-k1-ssm-kernel.h','candidate-ssm-conv.patch']:
                shutil.copy2(old/name, root/name)
            shutil.copy2(old/'candidate/ggml/src/ggml-cpu/ops.cpp', root/'candidate-ops.cpp')
            binary = old/'test-ssm'
        shutil.copy2(fixture, root/('original-'+fixture.name))
        text = fixture.read_text()
        if family=='conv':
            replacements = {
                'uint32_t seed = 123;': 'uint32_t seed = operator_seed;',
                'ggml_threadpool_params_default(4)': 'ggml_threadpool_params_default(operator_threads)',
                'cpu<4': 'cpu<operator_threads',
                'ggml_graph_plan(graph, 4, pool)': 'ggml_graph_plan(graph, operator_threads, pool)',
                'pool = ggml_threadpool_new(&params);': 'if (!operator_pool) { operator_pool = ggml_threadpool_new(&params); std::atexit([] { ggml_threadpool_free(operator_pool); }); }\n        pool = operator_pool;',
                'ggml_threadpool_free(pool);': '',
            }
            for before, after in replacements.items():
                if text.count(before)!=1: raise ValueError(f'fixture edit count: {before}')
                text = text.replace(before, after)
            save(root/'fixture-edits.json', replacements)
        (root/fixture.name).write_text(text)
        oldenv = os.environ.copy()
        oldenv['LD_LIBRARY_PATH'] = f'{old}/lib:{SOURCE}/build/bin'
        links = command(['ldd',str(binary)],env=oldenv).stdout
        (root/'original-ldd.txt').write_text(links)
        for line in links.splitlines():
            parts = line.split()
            if len(parts)>2 and parts[1]=='=>' and parts[2].startswith('/'):
                path = Path(parts[2])
                shutil.copy2(path.resolve(), root/'lib'/path.name)
        cpu = root/'lib/libggml-cpu.so.0'
        base = root/'lib/libggml-base.so.0'
        if not cpu.is_file() or not base.is_file(): raise ValueError('library dependency')
        (root/'lib/libggml-cpu.so').symlink_to(cpu.name)
        (root/'lib/libggml-base.so').symlink_to(base.name)
        args = ['g++','-O3','-std=c++17','-march=rv64gcv_zfh_zvfh_zicbop_zihintpause_zba','-mabi=lp64d',
                '-I'+str(root),'-I'+str(root/'include'),str(ROOT/(family+'.cpp')),
                '-L'+str(root/'lib'),'-lggml-cpu','-lggml-base','-pthread','-o',str(root/'operator')]
        result = command(args)
        (root/'build.log').write_text(result.stdout+result.stderr)
        (root/'ldd.txt').write_text(command(['ldd',str(root/'operator')], env=env_for(family)).stdout)
    files = {str(p.relative_to(ROOT)): digest(p) for p in ROOT.rglob('*') if p.is_file() and p.name not in ['commands.jsonl','driver.log','state.json']}
    save('frozen-artifacts.json', files)
    return digest(ROOT/'frozen-artifacts.json')

def arguments(case, mode, arm, dump):
    shape = case['shape']
    result = [str(ROOT/case['family']/'operator'), mode, *map(str,shape), str(case['thread_count']), str(case['seed'])]
    if case['family']=='conv': result.append(str(case['padding']))
    return result + [str(arm), str(dump)]

def main():
    if Path('state.json').exists(): raise RuntimeError('batch exists; do not repeat')
    state = {'status':'prepare','started':now(),'pending':['numeric','train'],'held_out_measured':False}
    save('state.json',state)
    identity = prepare()
    plan = json.loads(Path('plan.json').read_text())
    cases = []
    for group in plan['groups']:
        if group['split']!='train': continue
        for threads in group['threads']:
            cases.append(dict(group, id=f'{group["id"]}-t{threads}', thread_count=threads))
    rng = __import__('random').Random(plan['seed']+1)
    rng.shuffle(cases)
    save('training-cases.json', cases)
    receipts = []
    state.update(status='numeric',artifact_sha256=identity)
    save('state.json',state)
    for case in cases:
        arms = [0,1] if case['family']=='ime' else [0,2]
        hashes = []
        for arm in arms:
            name = f'{case["id"]}-a{arm}'
            path = ROOT/'numeric'/(name+'.bin')
            result = command(arguments(case,'numeric',arm,path), env=env_for(case['family']))
            (ROOT/'numeric'/(name+'.log')).write_text(result.stdout+result.stderr)
            hashes.append(digest(path))
        if len(set(hashes))!=1: raise ValueError(f'numeric arms differ: {case["id"]}')
        receipts.append({'case':case, 'arms':arms, 'sha256':hashes[0], 'bytes':path.stat().st_size})
        save('numeric-receipts.json', receipts)
        print('NUMERIC', case['id'], flush=True)
    state.update(status='train',pending=['train'],numeric_cases=len(receipts))
    save('state.json',state)
    rows = 0
    for case in cases:
        before = snapshot()
        result = command(arguments(case,'bench',0,ROOT/'unused.bin'), env=env_for(case['family']))
        after = snapshot()
        raw = ROOT/'timing'/case['id']
        raw.with_suffix('.jsonl').write_text(result.stdout)
        raw.with_suffix('.stderr').write_text(result.stderr)
        save(raw.with_suffix('.host.json'), {'before':before,'after':after})
        values = [json.loads(line) for line in result.stdout.splitlines()]
        arms = [0,1] if case['family']=='ime' else [0,2]
        expected = {(r,l,a) for r in range(7) for l in range(3) for a in arms}
        actual = [(v['repeat'],v['length'],v['arm']) for v in values]
        if len(actual)!=42 or set(actual)!=expected: raise ValueError('sample coverage')
        with open('observations.jsonl','a') as out:
            for value in values:
                if value['calls']<=0 or not math.isfinite(value['wall_ms']) or value['wall_ms']<=0: raise ValueError('sample values')
                if case['family']=='ime':
                    if len(value['threads'])!=case['thread_count']: raise ValueError('worker coverage')
                    for worker in value['threads']:
                        if worker['enabled']!=worker['running'] or worker['cycles']<=0: raise ValueError('PMU coverage')
                out.write(json.dumps({'schema':1,'case':case,'artifact_sha256':identity,'numeric_sha256':next(x['sha256'] for x in receipts if x['case']['id']==case['id']), **value})+'\n')
                rows += 1
        state.update(timing_cases=rows//42,rows=rows)
        save('state.json',state)
        print('TIMING',case['id'],rows,flush=True)
    state.update(status='complete',pending=[],finished=now(),cases=len(cases),rows=rows)
    save('state.json',state)
    save('sha256.json',{str(p.relative_to(ROOT)):digest(p) for p in ROOT.rglob('*') if p.is_file() and p.name not in ['sha256.json','driver.log']})
    print('COMPLETE',rows,flush=True)

if __name__=='__main__':
    try:
        main()
    except BaseException as error:
        if Path('state.json').exists():
            state=json.loads(Path('state.json').read_text())
            state.update(status='failed',error=str(error),failed=now())
            save('state.json',state)
        traceback.print_exc()
        sys.exit(1)
