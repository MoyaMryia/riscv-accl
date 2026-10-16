#!/usr/bin/env python3
"""采集所选配置的一次完整片段调用，不自动启动原生或全量测试。"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import time
from common import digest, read, seal, write

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), HERE / (name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check = load('fragment-check')
invocation = load('fragment-invocation')


def collect(payload, numerical, qemu, header, compiler, output, cases, maximum, trace_calls=0, decoded=True):
    payload, numerical, qemu, header = (Path(p).resolve() for p in (payload, numerical, qemu, header))
    check.receipts(payload)
    check.receipts(numerical)
    plan = read(payload / 'input-plan.json')
    identity = digest(payload / 'fragment')
    prior = read(numerical / 'result.json')
    if identity != prior['binary_sha256'] or digest(qemu) != prior['qemu_sha256']:
        raise ValueError('完整调用采集与原数值检查的 ELF 或 QEMU 身份不同。')
    if not cases or len(set(cases)) != len(cases) or any(type(i) is not int or not 0 <= i < len(plan['cases']) for i in cases):
        raise ValueError('采集配置身份无效或重复。')
    if type(maximum) is not int or not 0 < maximum <= 10000000:
        raise ValueError('轨迹上限必须为 1 至 10000000 条指令。')
    if type(trace_calls) is not int or not 0 <= trace_calls <= 64:
        raise ValueError('调用循环采集次数必须为 1 至 64，或使用 0 采集单次直接调用。')
    out = Path(output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    flags = shlex.split(subprocess.check_output(['pkg-config', '--cflags', '--libs', 'glib-2.0'], text=True))
    command = [str(Path(compiler).absolute()), '-O2', '-std=c11', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
               '-I'+str(header.parent), str(HERE/'fragment-trace.c'), '-o', str(out/'trace.so'), *flags]
    write(out / 'build-command.json', command)
    with (out / 'build.log').open('x') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=60, check=True)
    env = dict(os.environ)
    env['LD_LIBRARY_PATH'] = str(qemu.parent.parent/'lib') + (':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    records = []
    for ci in cases:
        case = plan['cases'][ci]
        for ki, kernel in enumerate(plan['kernels']):
            name = case['id']+'-'+kernel['id']
            symbol = 'fragment_repeat' if trace_calls else kernel['symbol']
            first, _ = invocation.binary.function(payload/'fragment', symbol)
            command = [str(qemu), '-cpu', 'max,vlen=256,elen=64,vext_spec=v1.0', '-plugin',
                       f'{out/"trace.so"},entry={first},out={out/name},max={maximum}',
                       str(payload/'fragment'), 'trace' if trace_calls else 'check', str(ci), str(ki), '17',
                       *([str(trace_calls)] if trace_calls else []), str(out/(name+'.bin')), 'exact']
            write(out/(name+'-command.json'), command)
            start = time.perf_counter()
            with (out/(name+'.log')).open('x') as log:
                subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=60, check=True)
            elapsed = time.perf_counter()-start
            traces = list(out.glob(name+'-cpu*.jsonl'))
            if len(traces) != 1:
                raise ValueError('当前入口必须只产生一个处理器的完整调用轨迹。')
            original = numerical/'dumps'/(name+'-seed17.bin')
            if (out/(name+'.bin')).read_bytes() != original.read_bytes():
                raise ValueError('完整调用与原数值转储不同。')
            report, instructions = invocation.audit(traces[0], payload/'fragment', symbol)
            write(out/(name+'-audit.json'), report)
            if decoded:
                with (out/(name+'-decoded.jsonl')).open('x') as stream:
                    for row in instructions:
                        stream.write(json.dumps(row, sort_keys=True)+'\n')
            records.append(dict(case=case['id'], kernel=kernel['id'], capture_seconds=elapsed, audit=report))
    result = dict(schema=1, status='selected-complete-invocations-audited', records=records,
                  binary_sha256=identity, qemu_sha256=digest(qemu), plugin_sha256=digest(out/'trace.so'),
                  plugin_header_sha256=digest(header),
                  tool_files={name:digest(HERE/name) for name in ('fragment-trace.c', 'fragment-call.py', 'fragment-invocation.py')},
                  selected_cases=[plan['cases'][i]['id'] for i in cases], trace_calls=trace_calls,
                  K1_cycles=None, prediction_confidence=None,
                  automatic_native_test=False, automatic_full_test=False, automatic_performance_rejection=False,
                  retained_candidates=[k['id'] for k in plan['kernels']],
                  limits=['仅采集所选配置与 seed17 的首次调用。', '完整调用核验不提供性能置信度。'])
    write(out/'result.json', result)
    seal(out)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('payload', 'qemu-check', 'qemu', 'header', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--compiler', type=Path, default=Path('/usr/bin/cc'))
    p.add_argument('--cases', type=int, nargs='+', default=[0])
    p.add_argument('--max-instructions', type=int, default=200000)
    p.add_argument('--trace-calls', type=int, default=0)
    p.add_argument('--skip-decoded', action='store_true')
    a = p.parse_args()
    result = collect(a.payload, a.qemu_check, a.qemu, a.header, a.compiler, a.output, a.cases,
                     a.max_instructions, a.trace_calls, not a.skip_decoded)
    print(json.dumps(dict(status=result['status'], invocations=len(result['records'])), ensure_ascii=False))
