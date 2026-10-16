#!/usr/bin/env python3
"""固定结果完成顺序探针、数据划分与实际二进制。"""
import argparse
import copy
import importlib.util
from pathlib import Path
import random
import shutil
import subprocess
from common import digest, read, seal, write
from prepare import HERE
import state3
import state6

spec = importlib.util.spec_from_file_location('completion_probes', HERE / 'prepare-probes-r4.py')
r4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r4)
scalar = r4.scalar


def body(config, packets, renamed):
    ops = []
    for packet in range(packets):
        if config['family'] == 'completion-order':
            first, second = config['type_order']
            ops += [scalar(first, 0, 6)] + [scalar('add', 7) for _ in range(config['gap'])]
            ops += [scalar(second, 1 if renamed else 0, 6)]
        else:
            producer, reader, overwrite = config['type_order']
            lane = packet % config['chains']
            source, destination = 2 * lane, 2 * lane + 1
            ops += [scalar(producer, source, 6), scalar(reader, destination, destination, source)]
            ops += [scalar('add', 7) for _ in range(config['gap'])]
            ops += [scalar(overwrite, 4 + lane if renamed else source, 6)]
    return ops


def definitions():
    configs = []
    for order in (('mul', 'add'), ('load', 'add'), ('mul', 'load'), ('load', 'mul'), ('add', 'mul'), ('add', 'load')):
        for gap in (0, 1, 3, 7):
            configs.append(dict(family='completion-order', type_order=list(order), chains=1, gap=gap))
    for producer in ('mul', 'load'):
        for reader in ('add', 'mul'):
            for overwrite in ('add', 'load'):
                for chains in (1, 2):
                    for gap in (0, 3, 7):
                        configs.append(dict(family='operand-wait', type_order=[producer, reader, overwrite], chains=chains, gap=gap))
    random.Random(2026101281).shuffle(configs)
    rows = []
    for index, config in enumerate(configs):
        config.update(group=f'r8-group-{index:03d}', split='training' if index < 44 else 'calibration' if index < 63 else 'test')
        for packets in (9, 21):
            for arm in (0, 1):
                rows.append(dict(**config, packets=packets, unroll=packets, arm=arm, mode='completion-probe',
                    role='mechanism', semantic_pair=False, kinds=list(dict.fromkeys(config['type_order'] + ['add'])),
                    instructions=body(config, packets, bool(arm))))
    for pair in r4.validation():
        if pair['chains'] == 2:
            continue
        pair = copy.deepcopy(pair)
        packets = {12: 9, 20: 21}[pair['packets']]
        original = [scalar(kind, 4 * j + i % pair['chains']) for i in range(packets) for j, kind in enumerate(pair['kinds'])]
        grouped, order = r4.by_kind(original, pair['kinds'])
        pair.update(group=pair['group'].replace('r4-', 'r8-').replace(f'-p{pair["packets"]}', f'-p{packets}'),
            split='test', packets=packets, unroll=packets, role='semantic-validation', semantic_pair=True,
            instructions=grouped if pair['arm'] == 0 else original,
            original_order=order if pair['arm'] == 0 else list(range(len(original))),
            original_dependencies=[sorted(e) for e in r4.dependencies(original)])
        rows.append(pair)
    for index, row in enumerate(rows):
        row['id'] = f'cpu_{index:03d}'
    return configs, rows


def main(a):
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    models = [('state3', state3, a.prior3), ('state6', state6, a.prior6)]
    parameters = []
    for name, engine, path in models:
        frozen = read(path)
        if digest(HERE / (name + '.py')) != frozen['engine_files'][name + '.py']:
            raise ValueError('冻结引擎身份不同。')
        parameters.append(engine.prepare_parameters(frozen['parameters']))
    configs, rows = definitions()
    blocks, refs = [], []
    for row in rows:
        row['prior_cycles'] = {name: engine.steady(engine.compiled(row), p) for (name, engine, _), p in zip(models, parameters)}
        asm, ref = r4.render4(row)
        blocks.append(asm)
        refs += ref
    random.Random(2026101282).shuffle(blocks)
    (out / 'kernels.s').write_text('\n'.join(['.text', '.option norvc'] + [line for block in blocks for line in block]) + '\n')
    declarations = '\n'.join(f'extern uint64_t {r["id"]}(uint64_t,void *,void *);' for r in rows)
    table = ',\n'.join('{"%s","%s","%s",%s,ref_%s}' % (r['id'], r['group'], r['split'], r['id'], r['id']) for r in rows)
    driver = (HERE / 'measure.c').read_text().replace('/* DECLARATIONS */', declarations).replace('/* REFERENCES */', '\n'.join(refs)).replace('/* TABLE */', table)
    (out / 'measure.c').write_text(driver.replace('8192,32768,131072', '65536,262144,1048576').replace('rep<9', 'rep<5'))
    compiler = a.compiler.resolve()
    command = [str(compiler), '-O2', '-g', '-static', '-fno-pie', '-no-pie', '-march=rv64gcv', '-Wall', '-Wextra', '-Werror', str(out / 'measure.c'), str(out / 'kernels.s'), '-o', str(out / 'measure')]
    write(out / 'build-command.json', command)
    with (out / 'build.log').open('w') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    with (out / 'disassembly.txt').open('w') as log:
        subprocess.run([str(compiler).removesuffix('gcc') + 'objdump', '-d', str(out / 'measure')], stdout=log, check=True)
    audit = HERE.parent / 'qemu-screen/predictor/counter-audit.c'
    shutil.copyfile(audit, out / 'counter-audit.c')
    subprocess.run([str(compiler), '-O2', '-static', '-march=rv64gcv', str(audit), '-o', str(out / 'counter-audit')], check=True)
    for path, name in ((HERE / 'run-board.sh', 'run-board.sh'), (a.protocol, 'protocol.md'), (a.prior3, 'prior3.json'), (a.prior6, 'prior6.json')):
        shutil.copyfile(path, out / name)
    write(out / 'candidate-groups.json', configs)
    write(out / 'plan.json', dict(schema=8, batch='k1-cpu-completion-model-20261012-r8', records=rows,
        lengths=[65536, 262144, 1048576], repetitions=5, dump_lengths=[3, 17], cpu=0,
        binary_sha256=digest(out / 'measure'), compiler_sha256=digest(compiler), protocol_sha256=digest(a.protocol),
        prior_models={name: digest(path) for name, _, path in models}, prediction_confidence=None,
        limits=['本轮只覆盖固定热只读标量循环。', '机制探针目标版本没有通用数值等价声明。',
            '重排检查不使用机制探针校准界限。', '全部候选继续保留。']))
    seal(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'compiler', 'prior3', 'prior6', 'protocol'):
        parser.add_argument('--' + name, type=Path, required=True)
    main(parser.parse_args())
