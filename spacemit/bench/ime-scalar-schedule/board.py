#!/usr/bin/env python3
"""在隔离目录检查 IME 标量指令调度候选。"""
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


base = module('ime_board', HERE/'k1-ime-test.py')
patcher = module('scalar_prepare', HERE/'prepare.py')


class Run(base.Run):
    switch = 'SPINE_IME_SCALAR_SCHEDULE'
    title = 'K1 IME scalar instruction schedule'

    def generate(self, text):
        return patcher.generate(text)

    def activation(self, text, mode):
        if f'SPINE_IME_SCALAR_SCHEDULE: mode={mode} Q4_0 M4 K32 enabled' not in text:
            raise ValueError('候选或基线启用记录缺失。')

    def prepare(self):
        super().prepare()
        screen = Path.home()/'Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-20261008-184350'
        receipt = json.loads((screen.parent/'k1-local-candidates-C1-repeat-20261008-202900/repeat-1/result.json').read_text())['identity']
        accepted = screen/'C/lib'
        for name, key in (('libggml-cpu.so', 'library_sha256'), ('libllama.so', 'model_library_sha256')):
            if base.fast.digest(accepted/name) != receipt[key]:
                raise ValueError('已验证 C1 库身份不同。')
        commands = json.loads((screen/'commands.json').read_text())
        args = next(row['argv'].copy() for row in commands if row['log'] == 'C-ggml-cpu-link.log')
        args[args.index('-o')+1] = str(self.root/'lib/verified-c1.so')
        self.command(args, 'verify-c1-link.log', 120, cwd=self.build)
        if base.fast.digest(self.root/'lib/verified-c1.so') != receipt['library_sha256']:
            raise ValueError('C1 目标文件不能重现已验证库。')
        args[args.index('-o')+1] = str(self.root/'lib/libggml-cpu.so.0.16.0')
        replaced = 0
        objects = {}
        for i, word in enumerate(args):
            if word.endswith('/spacemit/ime1_kernels.cpp.o'):
                args[i] = str(self.root/'candidate-ime1.o')
                replaced += 1
            elif word.endswith('.o'):
                path = Path(word) if Path(word).is_absolute() else self.build/word
                objects[str(path)] = base.fast.digest(path)
        if replaced != 1:
            raise ValueError('IME 目标文件不唯一。')
        self.command(args, 'link-c1.log', 120, cwd=self.build)
        self.env.update(SPINE_K1_SSM_CONV='3', SPINE_K1_GEMM_ROUTE='3', SPINE_GDN_PREFILL='0')
        self.env['LD_LIBRARY_PATH'] = str(self.root/'lib')+':'+str(accepted)+':'+self.expected['runtime']['LD_LIBRARY_PATH']
        self.provenance.update(c1_identity=receipt, c1_objects_sha256=objects, c1_link=args,
            candidate_library_sha256=base.fast.digest(self.root/'lib/libggml-cpu.so.0.16.0'),
            runtime={k:v for k,v in self.env.items() if k.startswith('SPINE_') or k=='LD_LIBRARY_PATH'},
            hardware={'uname':subprocess.check_output(['uname','-a'],text=True),
                      'meminfo':Path('/proc/meminfo').read_text(), 'cpuinfo':Path('/proc/cpuinfo').read_text(),
                      'frequency_khz':Path('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq').read_text().strip()})
        base.fast.write_json(self.root/'provenance.json', self.provenance)

    def native(self):
        self.phase('native numerical gate')
        self.command([self.root/'test-ime'], 'numeric.log', 120, self.env)
        if 'PASS: 288 cases;' not in (self.root/'numeric.log').read_text():
            raise ValueError('数值检查不完整。')
        self.summary['stages']['numeric'] = {'cases':288, 'bitwise_equal':True, 'modes':[1], 'scalar_m4_reference':True}
        self.save()
        self.phase('operator timing')
        ks = sorted({v for shape in self.shapes.values() for v in shape.values()})
        with (self.root/'operator.jsonl').open('w') as output, (self.root/'operator.err').open('w') as err:
            subprocess.run([str(self.root/'test-ime'), '--bench', *map(str,ks)], stdout=output, stderr=err,
                           check=True, timeout=300, env=self.env)
        rows = [json.loads(line) for line in (self.root/'operator.jsonl').read_text().splitlines()]
        expected = {(k,n,b,m) for k in ks for n in (16,32) for b in range(6) for m in (0,1)}
        if len(rows) != len(expected) or {(r['k'],r['n'],r['block'],r['mode']) for r in rows} != expected:
            raise ValueError('算子测量臂缺失。')
        if any(r['slowest_ms'] < 200 or r['cpus'] != [0,1,2,3] for r in rows):
            raise ValueError('算子测量配置不同。')
        comparisons = []
        for k in ks:
            for n in (16,32):
                arms = {m:[r['ms_per_call'] for r in rows if (r['k'],r['n'],r['mode']) == (k,n,m)] for m in (0,1)}
                comparisons.append({'k':k, 'n':n, **base.fast.gate(arms[0],arms[1])})
        self.summary['stages']['operators'] = {'records':len(rows), 'comparisons':comparisons}
        self.save()
        both_models = all(any(row['advance'] and row['k'] in shape.values() for row in comparisons) for shape in self.shapes.values())
        return 1 if both_models and not any(row['clear_regression'] for row in comparisons) else None

    def run(self):
        try:
            self.prepare()
            winner = self.native()
            if winner is None:
                self.summary.update(status='inconclusive', reason='算子初筛未通过；保留原内核，不执行模型性能测试。')
            else:
                results = [self.model(model,512,1) for model in ('2B','4B')]
                self.summary.update(status='screen eligible' if all(row['advance'] for row in results) else 'inconclusive',
                                    reason='模型初筛完成；完整答案、状态回滚、解码和长上下文仍待验证。')
            self.save()
            self.phase(self.summary['status'])
        except BaseException as exc:
            self.summary.update(status='failed', reason=f'{type(exc).__name__}: {exc}')
            self.save()
            raise


if __name__ == '__main__':
    root = Path(sys.argv[1]).resolve()
    lock_path = Path.home()/'Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock'
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if subprocess.run(['pgrep','-x','llama-server'], stdout=subprocess.DEVNULL).returncode == 0:
            raise RuntimeError('实机已有模型服务。')
        for key in list(os.environ):
            if key.startswith('SPINE_'):
                del os.environ[key]
        Run(root).run()
