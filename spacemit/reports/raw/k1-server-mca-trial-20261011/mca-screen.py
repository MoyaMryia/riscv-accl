#!/usr/bin/env python3
"""检查真实汇编的模型覆盖，并执行隔离的调度分析。"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def assembly(function):
    lines = ['.text', '# LLVM-MCA-RISCV-LMUL M1', '# LLVM-MCA-RISCV-SEW E32']
    unresolved = []
    for item in function['instructions']:
        name = item['objdump_mnemonic']
        operands = item['operands']
        if name.startswith('.') or item['family'] == 'ime-known-encoding':
            unresolved.append(item)
            continue
        operands = re.sub(r'\b([0-9a-f]+)\s+<[^>]+>', lambda m: '.Lpc_'+m[1], operands)
        lines.append('.Lpc_'+format(item['address'], 'x')+':')
        lines.append(name+' '+operands)
        if name in ('vsetvli', 'vsetivli'):
            match = re.search(r'\be(8|16|32|64),\s*(m[f]?[1248]),', operands)
            if not match:
                raise ValueError('向量配置无法解析')
            lines += ['# LLVM-MCA-RISCV-LMUL '+match[2].upper(),
                      '# LLVM-MCA-RISCV-SEW E'+match[1]]
    return '\n'.join(lines)+'\n', unresolved


def main(args):
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    tool = args.mca.resolve()
    base = [str(tool), '-mtriple=riscv64', '-mcpu=spacemit-x60',
            '-mattr=+v,+zfh,+zvfh', '--skip-unsupported-instructions=none']
    version = subprocess.check_output([tool, '--version'], text=True)
    (out/'version.log').write_text(version)
    records = []
    commands = []
    inputs = {}
    jobs = []
    for index, path in enumerate(args.inventories):
        inventory = json.loads(path.read_text())
        inputs[str(path.resolve())] = sha(path)
        for number, function in enumerate(inventory['functions']):
            name = f'inventory-{index}-function-{number}'
            text, unresolved = assembly(function)
            (out/(name+'.s')).write_text(text)
            record = {'id': name, 'symbol': function['symbol'],
                      'elf_sha256': inventory['elf_sha256'],
                      'expected_instructions': function['static_instructions'],
                      'unresolved': unresolved,
                      'vector_context': 'linear address order; initial M1/E32; not path verified',
                      'performance_status': 'not-a-function-time-prediction'}
            records.append(record)
            if unresolved:
                record['status'] = 'coverage-gap'
            else:
                jobs.append((record, 1))
    # 这个区域只有一条循环路径，向量配置固定为 E32/M8。
    gdn = next(r for r in records if 'spine_k1_gdn_prefill128' in r['symbol'])
    source = json.loads(args.inventories[0].read_text())
    function = next(f for f in source['functions'] if f['symbol'] == gdn['symbol'])
    branch = next(i for i in function['instructions'] if i['objdump_mnemonic'] == 'c.bnez')
    start = int(re.match(r'\s*[^,]+,\s*([0-9a-f]+)', branch['operands'])[1], 16)
    body = dict(function)
    body['instructions'] = [i for i in function['instructions'] if start <= i['address'] <= branch['address']]
    text, unresolved = assembly(body)
    text = text.replace('RISCV-LMUL M1', 'RISCV-LMUL M8', 1)
    assert not unresolved
    record = {'id': 'gdn-r2-loop', 'symbol': function['symbol'],
              'expected_instructions': len(body['instructions']),
              'vector_context': 'E32/M8, VL=64 from fixed function preamble; no cache model',
              'performance_status': 'local-loop-model-only; K1-unvalidated', 'unresolved': []}
    (out/'gdn-r2-loop.s').write_text(text)
    records.append(record)
    jobs.append((record, 100))

    def run(job):
        record, iterations = job
        command = base+['-iterations='+str(iterations), '-resource-pressure',
                        '-timeline', '-timeline-max-iterations=2', str(out/(record['id']+'.s'))]
        commands.append(command)
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, timeout=60)
            log = result.stdout
            record['returncode'] = result.returncode
        except subprocess.TimeoutExpired as error:
            log = (error.stdout or b'').decode(errors='replace') if isinstance(error.stdout, bytes) else error.stdout or ''
            record['status'] = 'tool-timeout'
            (out/(record['id']+'.log')).write_text(log)
            return
        (out/(record['id']+'.log')).write_text(log)
        record['status'] = 'tool-failure' if result.returncode else 'analyzed'
        for label in ('Instructions', 'Total Cycles', 'Block RThroughput', 'Dispatch Width'):
            match = re.search(r'^'+re.escape(label)+r':\s+([0-9.]+)', log, re.M)
            if match:
                record[label] = float(match[1])
        if result.returncode == 0:
            if record.get('Instructions') != iterations*record['expected_instructions']:
                record['status'] = 'instruction-count-mismatch'
        record['iterations'] = iterations
        record['diagnostics'] = [line for line in log.splitlines() if 'warning:' in line or 'error:' in line]

    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(run, jobs))
    summary = {'schema': 1, 'tool_sha256': sha(tool), 'source_sha256': sha(__file__),
               'inputs': inputs, 'records': records,
               'scope': 'instruction coverage and one fixed GDN loop; no dynamic full-function timing',
               'K1_prediction_accuracy': 'unvalidated', 'automatic_performance_rejection': False}
    (out/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
    (out/'result.json').write_text(json.dumps(summary, indent=2)+'\n')
    (out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(out))+'\n'
        for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS'))
    print(json.dumps([{k: r[k] for k in ('id', 'status', 'Instructions', 'Total Cycles', 'Block RThroughput') if k in r}
                      for r in records], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mca', type=Path, required=True)
    parser.add_argument('--inventories', type=Path, nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args())
