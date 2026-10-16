#!/usr/bin/env python3
"""比较优化片段的实际二进制，输出有限预测与低成本补测建议。"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import time
from common import digest, read, write

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('fragment_binary', HERE / 'binary-input.py')
binary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binary)
ENGINES = {'state3.py': 2, 'state6.py': 6, 'state8.py': 8}


class EvidenceError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def artifact(root, record):
    require(isinstance(record, dict), '文件证据必须为对象。')
    path = (root / record['path']).resolve()
    require(digest(path) == record['sha256'], f'文件身份不同：{record["path"]}')
    return path


def contract(value):
    require(isinstance(value, dict), '缺少片段契约。')
    for field in ('work_id', 'input_description', 'boundary', 'compile_context'):
        require(isinstance(value.get(field), str) and value[field].strip(), f'契约缺少 {field}。')
    for field in ('live_inputs', 'live_outputs', 'memory_effects'):
        require(isinstance(value.get(field), list) and value[field]
                and all(isinstance(item, str) and item.strip() for item in value[field]), f'契约缺少 {field}。')
    require(value.get('equivalent_work_per_iteration') is True, '未声明每次迭代完成相同工作。')
    require(value.get('cpu') == 0 and value.get('threads') == 1, '当前只支持 CPU 0 与单线程。')
    require(value.get('boundary_kind') == 'steady-loop', '当前只预测固定循环稳态成本。')
    require(value.get('memory_scenario') in ('no-memory', 'hot-read-only'), '访存场景未覆盖。')
    require(value.get('entry_state') == 'repeated-steady-loop', '入口状态未覆盖。')
    return value


def numerical(root, manifest):
    checks = manifest.get('numerical_checks', [])
    if not checks:
        return dict(status='missing', cases=0, limits=['缺少数值证据，不产生有效收益预测。'])
    rows, ids = [], set()
    for check in checks:
        require(check['id'] not in ids, '数值检查身份重复。')
        ids.add(check['id'])
        paths = [artifact(root, check[key]) for key in ('baseline', 'candidate', 'reference')]
        data = [path.read_bytes() for path in paths]
        require(all(data), '数值转储不能为空。')
        identities = [manifest[key]['elf']['sha256'] for key in ('baseline', 'candidate')]
        require(check.get('elf_sha256') == identities, '数值证据的二进制身份不同。')
        rows.append(dict(id=check['id'], exact_equal=data[0] == data[1] == data[2],
                         bytes=[len(item) for item in data], sha256=[digest(path) for path in paths]))
    return dict(status='passed-tested-cases' if all(row['exact_equal'] for row in rows) else 'failed',
                cases=len(rows), rows=rows,
                limits=['字节比较只核验所附测试输出。', '转储生成过程与完整输出范围由夹具协议提供。',
                        '有限输入相同不能证明所有输入语义等价。'])


def arm(root, record, conditions):
    elf, trace = artifact(root, record['elf']), artifact(root, record['trace'])
    lengths = record['iterations']
    require(isinstance(lengths, list) and lengths and all(type(n) is int and n > 0 for n in lengths), '轨迹迭代声明无效。')
    body = binary.loop(elf, record['symbol'])
    kinds = {item['kind'] for item in body['instructions']}
    require(kinds <= {'add', 'mul', 'load'}, '首版片段入口只覆盖 add、mul 与只读 load。')
    require('load' not in kinds or conditions['memory_scenario'] == 'hot-read-only', '加载缺少热只读场景声明。')
    audit = binary.trace(trace, body, lengths)
    return body, dict(symbol=record['symbol'], elf_sha256=digest(elf), trace_sha256=digest(trace),
                      loop_range=[body['first'], body['last'] + 4], instructions=len(body['instructions']) + 2,
                      dynamic_audit=audit)


def prediction(root, record, bodies):
    model_path, engine_path = artifact(root, record['model']), artifact(root, record['engine'])
    frozen = read(model_path)
    require(engine_path.name in ENGINES, '状态引擎不在首版范围内。')
    require(frozen['engine_files'].get(engine_path.name) == digest(engine_path), '状态引擎与冻结模型身份不同。')
    require(frozen['schema'] == ENGINES[engine_path.name], '状态引擎与模型版本不同。')
    engine_spec = importlib.util.spec_from_file_location('fragment_' + record['id'], engine_path)
    engine = importlib.util.module_from_spec(engine_spec)
    engine_spec.loader.exec_module(engine)
    params = engine.prepare_parameters(frozen['parameters'])
    cycles = [engine.steady(engine.compiled(body), params) for body in bodies]
    require(all(math.isfinite(n) and n > 0 for n in cycles), '模型没有产生有效稳态周期。')
    ratio = cycles[1] / cycles[0]
    return dict(id=record['id'], model_sha256=digest(model_path), engine_sha256=digest(engine_path),
                cycles_per_iteration=dict(baseline=cycles[0], candidate=cycles[1]),
                candidate_over_baseline=ratio, predicted_gain_percent=100 * (1 - ratio),
                direction='faster' if ratio < 1 else 'slower' if ratio > 1 else 'tie',
                prediction_interval=None, prediction_confidence=None)


def recommendation(result):
    if result['numerical']['status'] == 'failed':
        return dict(action='repair-numerical-contract', reason='所附输出不同，当前不能作有效收益比较。')
    if result['numerical']['status'] == 'missing':
        if any(gap != '缺少数值检查。' for gap in result['gaps']):
            return dict(action='resolve-evidence-gap', reason='先核对文件身份与片段契约，再补充数值检查。')
        return dict(action='collect-numerical-evidence', reason='先补充代表输入与独立参考输出。')
    if result['gaps']:
        return dict(action='resolve-evidence-gap', reason='先解决所列缺口；必要时做小规模 K1 配对实测。')
    if len({row['direction'] for row in result['predictions']}) > 1:
        return dict(action='paired-native-test-for-model-disagreement', reason='模型方向有分歧，优先检查此片段。')
    return dict(action='paired-native-test-before-expanded-tests',
                reason='点预测可以安排补测顺序；新片段尚无独立校准，不能据此直接确认或放弃优化。')


def evaluate(manifest_path):
    started = time.perf_counter()
    manifest_path = Path(manifest_path).resolve()
    manifest, root = read(manifest_path), manifest_path.parent
    result = dict(schema=1, id=manifest.get('id'), manifest_sha256=digest(manifest_path),
                  status='evidence-incomplete', retained=True, automatic_performance_rejection=False,
                  automatic_full_test=False, prediction_confidence=None, prediction_interval=None,
                  predictions=[], gaps=[], numerical=dict(status='missing', cases=0), arms={},
                  limits=['当前仅覆盖单个固定计数标量循环的稳态成本。',
                          '入口与出口契约是调用者声明，工具不能证明全部语义。',
                          '片段提取可能改变寄存器分配与指令布局。',
                          '热只读声明不证明实际缓存命中；模型不预测缓存缺失。',
                          '稳态预测不包含函数调用、初始化或循环启动与排空成本。',
                          '模型分歧范围不是预测置信区间；一致也不证明准确。',
                          '不使用旧批次校准界限，不作完整算子或任务收益声明。'])
    stages = {}
    try:
        require(manifest.get('schema') == 1 and isinstance(manifest.get('id'), str), '清单身份无效。')
        conditions = contract(manifest['contract'])
        result['declared_contract'] = conditions
        start = time.perf_counter()
        for key in ('baseline', 'candidate'):
            artifact(root, manifest[key]['elf'])
        result['numerical'] = numerical(root, manifest)
        stages['numerical_seconds'] = time.perf_counter() - start
        if result['numerical']['status'] == 'failed':
            result['status'] = 'numerical-failed'
        elif result['numerical']['status'] == 'missing':
            result['gaps'].append('缺少数值检查。')
        else:
            start = time.perf_counter()
            bodies = []
            for key in ('baseline', 'candidate'):
                body, audit = arm(root, manifest[key], conditions)
                bodies.append(body)
                result['arms'][key] = audit
            stages['binary_trace_audit_seconds'] = time.perf_counter() - start
            start = time.perf_counter()
            models = manifest.get('models', [])
            require(models and len({row['id'] for row in models}) == len(models), '模型清单缺失或身份重复。')
            for row in models:
                try:
                    result['predictions'].append(prediction(root, row, bodies))
                except (ValueError, KeyError, OSError, TypeError, struct.error) as error:
                    result['gaps'].append(f'模型 {row["id"]}：{error}')
            stages['prediction_seconds'] = time.perf_counter() - start
            primary = [row for row in result['predictions'] if row['id'] == manifest.get('primary_model')]
            require(len(primary) == 1, '主模型预测缺失。')
            result['primary_prediction'] = primary[0]
            ratios = [row['candidate_over_baseline'] for row in result['predictions']]
            result['model_sensitivity_ratio_range'] = [min(ratios), max(ratios)]
            result['status'] = 'exploratory-pair-estimate' if not result['gaps'] else 'evidence-incomplete'
    except (ValueError, KeyError, OSError, TypeError, struct.error) as error:
        result['gaps'].append(str(error))
        result['status'] = 'evidence-incomplete'
        result['predictions'] = []
        result.pop('primary_prediction', None)
        result.pop('model_sensitivity_ratio_range', None)
    result['recommendation'] = recommendation(result)
    measured = time.perf_counter() - started
    external, unknown = {}, []
    declared = manifest.get('cost_seconds', {})
    for key in ('build', 'trace_acquisition', 'native_measurement'):
        value = declared.get(key) if isinstance(declared, dict) else None
        if type(value) in (int, float) and math.isfinite(value) and value >= 0:
            external[key] = value
        else:
            unknown.append(key)
    result['cost'] = dict(comparison_elapsed_seconds=measured, measured_stages=stages,
                          declared_external_seconds=external, unknown_stages=unknown,
                          known_subtotal_seconds=measured + sum(external.values()), total_seconds=None,
                          limits=['外部成本由调用者声明。', '缺少外部阶段时不能报告完整评估成本。',
                                  '本次时间不包含进程启动与报告写入。'])
    stable = {key: value for key, value in result.items() if key != 'cost'}
    result['comparison_sha256'] = hashlib.sha256(json.dumps(stable, sort_keys=True, separators=(',', ':'),
                                                          ensure_ascii=False).encode()).hexdigest()
    return result


def markdown(result):
    lines = ['# 代码片段比较', '', f'状态：`{result["status"]}`。',
             f'数值检查：`{result["numerical"]["status"]}`，测试输入数为 {result["numerical"]["cases"]}。', '',
             '| 模型 | 基线周期/迭代 | 候选周期/迭代 | 预测耗时比 | 预测收益 |', '| --- | ---: | ---: | ---: | ---: |']
    for row in result['predictions']:
        cycles = row['cycles_per_iteration']
        lines.append(f'| {row["id"]} | {cycles["baseline"]:.6g} | {cycles["candidate"]:.6g} | '
                     f'{row["candidate_over_baseline"]:.6g} | {row["predicted_gain_percent"]:.4f}% |')
    lines += ['', '建议：' + result['recommendation']['reason'], '', '全部候选保留。预测界限与预测置信度尚不可用。', '']
    for gap in result['gaps']:
        lines.append('- 缺口：' + gap)
    lines += ['', '本次比较耗时：' + f'{result["cost"]["comparison_elapsed_seconds"]:.6f} s。',
              '完整评估成本尚未核验。', '']
    lines.extend('- ' + item for item in result['limits'])
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--markdown', type=Path)
    args = parser.parse_args()
    result = evaluate(args.manifest)
    write(args.output, result)
    if args.markdown:
        with args.markdown.open('x') as stream:
            stream.write(markdown(result))
    print(json.dumps(dict(status=result['status'], recommendation=result['recommendation'],
                          comparison_sha256=result['comparison_sha256']), ensure_ascii=False))
