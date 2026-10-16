#!/usr/bin/env python3
"""从实际二进制建立可追溯的 LLVM 调度模型对照。"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import importlib.util
import os
from pathlib import Path
import statistics
import subprocess
from common import digest, read, write, seal

HERE = Path(__file__).resolve().parent
ITERATIONS = (128, 256, 512)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def assembly(body):
    """只转写已解码的标量机器码，并保留循环控制。"""
    lines = ['.option norvc', '.option norelax', '.Lloop:']
    for row in body['instructions']:
        word = int(row['encoding'], 16)
        rd, rs1, rs2 = (word >> 7) & 31, (word >> 15) & 31, (word >> 20) & 31
        if row['kind'] in ('add', 'mul'):
            base = 0x33 if row['kind'] == 'add' else 0x02000033
            expected = base | (rd << 7) | (rs1 << 15) | (rs2 << 20)
            text = f'{row["kind"]} x{rd},x{rs1},x{rs2}'
        elif row['kind'] == 'load':
            offset = row['address_offset']
            expected = 0x3003 | (rd << 7) | (rs1 << 15) | ((offset & 4095) << 20)
            text = f'ld x{rd},{offset}(x{rs1})'
        else:
            raise ValueError('本对照未覆盖向量或 IME 指令。')
        if word != expected:
            raise ValueError('汇编转写与实际机器码不同。')
        lines.append(text)
    counter = body['counter']
    lines.extend([f'addi x{counter},x{counter},-1', f'bnez x{counter},.Lloop'])
    return '\n'.join(lines) + '\n'


def prepare(a):
    import model
    binary = module('baseline_binary', HERE / 'binary-input.py')
    engines = []
    for name, model_path, engine_path in (
        ('state3', a.model3, HERE / 'state3.py'), ('state6', a.model6, HERE / 'state6.py')
    ):
        frozen = read(model_path)
        if frozen['engine_files'].get(engine_path.name) != digest(engine_path):
            raise ValueError('冻结引擎身份不同。')
        engine = module('baseline_' + name, engine_path)
        engines.append((name, engine, engine.prepare_parameters(frozen['parameters'])))
    a.output.mkdir()
    (a.output / 'assembly').mkdir()
    records, pairs, sources = [], [], []
    for batch_index, root in enumerate(a.batch):
        plan_path = root / 'payload/plan.json'
        plan = read(plan_path)
        elf = root / 'payload/measure'
        if digest(elf) != plan['binary_sha256']:
            raise ValueError('历史二进制身份不同。')
        data = {}
        for split in sorted({r['split'] for r in plan['records']}):
            data[split] = model.observations(plan, root / ('run-' + split), split)
        sources.append(dict(batch=root.name, plan_sha256=digest(plan_path), elf_sha256=digest(elf),
            run_receipts={s: digest(root / ('run-' + s) / 'SHA256SUMS') for s in data}))
        grouped = defaultdict(list)
        for row in plan['records']:
            key = f'b{batch_index}-{row["id"]}'
            actual = data[row['split']]['cycles'][row['id']]
            record = dict(key=key, batch=root.name, id=row['id'], split=row['split'], group=row['group'],
                family=row.get('family', row['mode']), arm=row['arm'], unroll=row['unroll'],
                observed_cycles=actual, retained=True, status='scope-uncovered')
            body = binary.loop(elf, row['id'])
            record['encodings'] = [f'{word:08x}' for word in body['encodings'].values()]
            record['loop_range'] = [body['first'], body['last'] + 4]
            if all(op['kind'] in ('add', 'mul', 'load') for op in body['instructions']):
                path = a.output / 'assembly' / (key + '.s')
                path.write_text(assembly(body))
                record.update(status='ready', assembly=str(path.relative_to(a.output)),
                    assembly_sha256=digest(path), instruction_count=len(body['instructions']) + 2,
                    predictions={name: engine.steady(engine.compiled(body), parameters)
                        for name, engine, parameters in engines})
            else:
                record['reason'] = '本轮只比较标量循环；向量与 IME 成本没有被省略。'
            records.append(record)
            if row['mode'] in ('holdout', 'reorder', 'queue-holdout'):
                grouped[row['group'], row['unroll'], row['split']].append((row, record))
        for (group, unroll, split), values in sorted(grouped.items()):
            values.sort(key=lambda value: value[0]['arm'])
            if len(values) != 2 or [r['arm'] for r, _ in values] != [0, 1]:
                raise ValueError('历史重排组不完整。')
            for length in plan['dump_lengths']:
                paths = [root / ('run-' + split) / 'dumps' / f'{r["id"]}-{length}.bin' for r, _ in values]
                if paths[0].read_bytes() != paths[1].read_bytes():
                    raise ValueError('历史重排完整输出不同。')
            ids = [r['id'] for r, _ in values]
            repeated = [data[split]['slopes'][ids[1]][k] / value
                for k, value in data[split]['slopes'][ids[0]].items()]
            pairs.append(dict(batch=root.name, group=group, unroll=unroll, split=split,
                keys=[r['key'] for _, r in values], paired_repeat_ratio_range=[min(repeated), max(repeated)],
                complete_dump_pairs=len(plan['dump_lengths']), retained=True))
    write(a.output / 'manifest.json', dict(schema=1, sources=sources, records=records, pairs=pairs,
        iterations=ITERATIONS, model_sha256=dict(state3=digest(a.model3), state6=digest(a.model6)),
        tool_sha256=digest(__file__), limits=[
            '历史原生数据已经公开；本轮不是独立后测。',
            'LLVM 资源吞吐下界不作为循环周期。',
            '本轮只比较标量固定循环；缓存状态、前端和分支预测未建模。',
            '配对重复范围不是预测置信区间。', '全部候选继续保留。']))
    seal(a.output)


def summary(document, iterations, count):
    if document['TargetInfo']['CPUName'] != 'spacemit-x60':
        raise ValueError('LLVM 目标不是 spacemit-x60。')
    regions = document['CodeRegions']
    if len(regions) != 1:
        raise ValueError('LLVM 代码区域数量不同。')
    region = regions[0]
    result = region['SummaryView']
    if result['Iterations'] != iterations or result['Instructions'] != iterations * count:
        raise ValueError('LLVM 没有分析完整循环指令。')
    if len(region['Instructions']) != count or len(region['InstructionInfoView']['InstructionList']) != count:
        raise ValueError('LLVM 静态指令数量不同。')
    if not isinstance(result['TotalCycles'], (int, float)) or result['TotalCycles'] <= 0:
        raise ValueError('LLVM 周期数无效。')
    return result


def verify(root):
    """核对独立目录收据，并拒绝目录外路径。"""
    root = root.resolve()
    expected = set()
    for line in (root / 'SHA256SUMS').read_text().splitlines():
        checksum, name = line.split('  ', 1)
        path = root / name
        if name in expected or not path.resolve().is_relative_to(root) or digest(path) != checksum:
            raise ValueError('对照目录收据不同。')
        expected.add(name)
    actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name != 'SHA256SUMS'}
    if actual != expected:
        raise ValueError('对照目录文件清单不同。')


def run(a):
    verify(a.input)
    manifest = read(a.input / 'manifest.json')
    a.output.mkdir()
    version = subprocess.run([str(a.mca), '--version'], capture_output=True, text=True, timeout=20, check=True)
    (a.output / 'version.txt').write_text(version.stdout)
    write(a.output / 'runtime.json', dict(mca_sha256=digest(a.mca), manifest_sha256=digest(a.input / 'manifest.json'),
        host=list(os.uname()), started_at_utc=datetime.now(timezone.utc).isoformat(),
        libraries=[dict(path=str(p), sha256=digest(p)) for p in a.library]))
    results = []
    for record in manifest['records']:
        result = dict(key=record['key'], retained=True, status=record['status'])
        if record['status'] == 'ready':
            source = a.input / record['assembly']
            if digest(source) != record['assembly_sha256']:
                raise ValueError('对照汇编身份不同。')
            directory = a.output / record['key']
            directory.mkdir()
            summaries = []
            try:
                for iterations in manifest['iterations']:
                    command = [str(a.mca), '-mtriple=riscv64', '-mcpu=spacemit-x60',
                        '-skip-unsupported-instructions=none', '-json', f'-iterations={iterations}', str(source)]
                    write(directory / f'command-{iterations}.json', command)
                    completed = subprocess.run(command, capture_output=True, text=True, timeout=30)
                    (directory / f'output-{iterations}.json').write_text(completed.stdout)
                    (directory / f'error-{iterations}.txt').write_text(completed.stderr)
                    write(directory / f'exit-{iterations}.json', completed.returncode)
                    if completed.returncode != 0 or completed.stderr.strip():
                        raise ValueError('LLVM 拒绝输入或报告诊断；本候选没有性能结论。')
                    summaries.append(summary(__import__('json').loads(completed.stdout), iterations, record['instruction_count']))
                xs = manifest['iterations']
                slopes = [(summaries[i + 1]['TotalCycles'] - summaries[i]['TotalCycles']) / (xs[i + 1] - xs[i]) for i in (0, 1)]
                if min(slopes) <= 0:
                    raise ValueError('LLVM 周期增量无效。')
                result.update(status='complete', cycles=slopes[-1], incremental_cycles=slopes,
                    incremental_difference=abs(slopes[1] - slopes[0]), summaries=summaries)
            except (ValueError, KeyError, subprocess.TimeoutExpired) as error:
                result.update(status='failed', reason=str(error))
        results.append(result)
    write(a.output / 'results.json', dict(records=results, completed_at_utc=datetime.now(timezone.utc).isoformat()))
    seal(a.output)


def metric(rows, key):
    values = [r[key] for r in rows]
    return dict(count=len(values), median=statistics.median(values), maximum=max(values)) if values else dict(count=0)


def assess(a):
    verify(a.input)
    verify(a.run)
    manifest = read(a.input / 'manifest.json')
    runtime = read(a.run / 'runtime.json')
    if runtime['manifest_sha256'] != digest(a.input / 'manifest.json'):
        raise ValueError('远端输入身份不同。')
    results = read(a.run / 'results.json')['records']
    if [r['key'] for r in results] != [r['key'] for r in manifest['records']]:
        raise ValueError('远端候选不完整。')
    index, records, pairs = {}, [], []
    for source, result in zip(manifest['records'], results):
        row = dict(source, mca=result)
        if result['status'] == 'complete':
            row['predictions']['llvm_mca'] = result['cycles']
            row['cycle_error_factors'] = {k: max(v / row['observed_cycles'], row['observed_cycles'] / v)
                for k, v in row['predictions'].items()}
        index[row['key']] = row
        records.append(row)
    for source in manifest['pairs']:
        rows = [index[k] for k in source['keys']]
        pair = dict(source, status='uncovered')
        if all(r['mca']['status'] == 'complete' for r in rows):
            truth = rows[1]['observed_cycles'] / rows[0]['observed_cycles']
            low, high = source['paired_repeat_ratio_range']
            pair.update(status='complete', observed_ratio=truth, observed_gain_below_one_percent=abs(truth - 1) < .01,
                repeat_range_crosses_one=low <= 1 <= high, predictions={})
            for name in rows[0]['predictions']:
                ratio = rows[1]['predictions'][name] / rows[0]['predictions'][name]
                pair['predictions'][name] = dict(ratio=ratio, gain_error_percentage_points=100 * abs(ratio - truth),
                    direction_agreement=((ratio > 1) - (ratio < 1)) == ((truth > 1) - (truth < 1)))
        pairs.append(pair)
    summaries = []
    for batch, split in sorted({(r['batch'], r['split']) for r in records}):
        functions = [r for r in records if r['batch'] == batch and r['split'] == split]
        covered = [r for r in functions if r['mca']['status'] == 'complete']
        paired = [p for p in pairs if p['batch'] == batch and p['split'] == split and p['status'] == 'complete']
        discernible = [p for p in paired if not p['observed_gain_below_one_percent'] and not p['repeat_range_crosses_one']]
        models = {}
        for name in ('llvm_mca', 'state3', 'state6'):
            errors = [dict(error=r['cycle_error_factors'][name]) for r in covered]
            gain = [p['predictions'][name] for p in paired]
            models[name] = dict(cycle_error_factor=metric(errors, 'error'), gain_error_percentage_points=metric(gain, 'gain_error_percentage_points'),
                discernible_pairs=len(discernible), discernible_direction_agreement=sum(p['predictions'][name]['direction_agreement'] for p in discernible))
        summaries.append(dict(batch=batch, split=split, functions=len(functions), covered=len(covered), pairs=len(paired), models=models))
    write(a.output, dict(schema=1, manifest_sha256=digest(a.input / 'manifest.json'), runtime=runtime,
        results_sha256=digest(a.run / 'results.json'), summaries=summaries, records=records, pairs=pairs,
        maximum_incremental_difference=max((r['mca']['incremental_difference'] for r in records if r['mca']['status'] == 'complete'), default=None),
        independent_validation=False, prediction_confidence=None, automatic_performance_rejection=False, limits=manifest['limits']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--batch', type=Path, action='append', required=True)
    for name in ('output', 'model3', 'model6'):
        p.add_argument('--' + name, type=Path, required=True)
    p = sub.add_parser('run')
    for name in ('input', 'output', 'mca'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--library', type=Path, action='append', default=[])
    p = sub.add_parser('assess')
    for name in ('input', 'run', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    globals()[args.action](args)
