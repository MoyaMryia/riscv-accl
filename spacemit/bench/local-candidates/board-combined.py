#!/usr/bin/env python3
"""串行构建组合库，并执行原生、模型状态和冷请求门槛。"""
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import traceback

import board
import combined_common as common

c2 = board.module('combined_c2_board', board.HERE/'board-c2-r2.py')
cold = board.module('combined_cold', board.HERE/'combined-cold.py')
answers = board.module('combined_answers', board.HERE/'complete_answers_combined.py')


class Run(c2.RevisedRun):
    def __init__(self, root):
        super().__init__(root)
        self.summary['revision'] = 'combined-r1'
        self.summary['scope'] = '固定组合实验；生产默认配置不变。'

    def env(self, arm):
        env = super().env(arm)
        env['SPINE_K1_GDN_REVISION'] = '1' if arm == 'C' else '0'
        return env

    def verify(self):
        board.Run.verify(self)
        manifest = json.loads((self.root/'C/manifest.json').read_text())
        if manifest['revision'] != 'combined-r1':
            raise ValueError('combined revision differs')
        for name, key in [('test-gdn-r2.cpp', 'fixture_sha256'), ('test-combined-state.cpp', 'combined_probe_sha256')]:
            if board.digest(self.root/'C'/name) != manifest[key]:
                raise ValueError('combined fixture differs: '+name)
        for path, expected in json.loads((self.root/'frozen-files.json').read_text()).items():
            if board.digest(self.root/path) != expected:
                raise ValueError('frozen payload differs: '+path)

    def build_all(self):
        super().build_all()
        if self.summary['candidates']['C']['build'] != 'pass':
            raise ValueError('combined build failed')
        self.harness('C', board.HERE/'test-attention.cpp', 'test-attention')
        self.harness('C', self.root/'C/test-combined-state.cpp', 'test-combined-state', True)

    def dump(self, arm, binary, args, label, expected):
        path = self.root/(label+'.bin')
        text = self.command([binary, *args, '--dump', path], label, arm)
        if expected not in text:
            raise ValueError('numeric case count differs: '+label)
        return board.digest(path), text

    def numeric(self, arm, reference_attention, reference_ssm):
        result = super().numeric(arm, reference_attention, reference_ssm)
        value, text = self.dump('C', self.root/'C/test-attention', [], 'combined-attention', 'PASS: 95')
        if value != reference_attention:
            raise ValueError('combined attention differs from original')
        rows = re.findall(r'K1_FA path=([\w-]+) heads=(\d+) kv_heads=(\d+) history=(\d+) chunk=\d+:\d+ worker=(\d+) workers=(\d+)', text)
        required = [('reference-underfilled-groups', 8, n) for n in (255, 256, 511)]
        required += [('B1', h, n) for h in (8, 16) for n in (512, 513, 2048)] + [('B1', 16, 256)]
        for path, heads, history in required:
            workers = {int(worker) for actual, h, kv, n, worker, count in rows
                       if (actual, int(h), int(kv), int(n), int(count)) == (path, heads, heads//4, history, 4)}
            if workers != {0, 1, 2, 3}:
                raise ValueError('attention dispatch coverage differs')
        path = self.root/'combined-legacy-gdn.bin'
        self.command([self.root/'C/test-gdn-r2', '--dump', path], 'combined-legacy-gdn', 'C',
                     updates={'SPINE_K1_GDN_REVISION': '0'})
        if board.digest(path) != result['gdn_original_control_sha256']['original']:
            raise ValueError('legacy GDN differs from original')
        result.update(attention_cases=95, attention_sha256=value, attention_required_shapes=len(required))
        return result

    def operators(self, arm):
        result = super().operators(arm)
        rows = []
        for block in range(6):
            for channels in (6144, 8192):
                for tokens in (1, 32):
                    for mode in ((0, 3) if block % 2 == 0 else (3, 0)):
                        label = f'combined-ssm-c{channels}-t{tokens}-b{block}-m{mode}'
                        text = self.command([self.root/'C/test-ssm', '--bench', mode, channels, 4, tokens, 1],
                                            label, 'C', updates={'SPINE_K1_TRACE': '0'})
                        sample = [json.loads(line) for line in text.splitlines() if line.startswith('{')]
                        if len(sample) != 1:
                            raise ValueError('SSM measurement count differs')
                        rows.append(dict(sample[0], block=block))
        (self.root/'combined-ssm-operators.json').write_text(json.dumps(rows, indent=2)+'\n')
        result['C1'] = self.comparisons(rows, ['channels', 'tokens'], 'mode', 3, 200)
        text = self.command([self.root/'C/test-attention', '--bench', 'B1'], 'combined-attention-operators', 'C',
                            updates={'SPINE_K1_TRACE': '0'})
        rows = [json.loads(line) for line in text.splitlines() if line.startswith('{')]
        result['B1'] = self.comparisons(rows, ['history', 'heads'])
        if len(result['C1']) != 4 or len(result['B1']) != 4:
            raise ValueError('operator shapes differ')
        eligible = self.summary['strict_operator_gate']['eligible']
        eligible &= not any(row['clear_regression'] for values in result.values() for row in values)
        eligible &= all(row['advance'] for row in result['C1'] if row['tokens'] == 32)
        eligible &= all(row['advance'] for row in result['B1'] if (row['history'], row['heads']) != (256, 8))
        self.summary['combined_operator_gate'] = bool(eligible)
        return result

    def model_env(self, arm, original=False):
        env = common.arm_env(arm, self.root/'C/lib', self.expected['runtime'])
        if original:
            env['LD_LIBRARY_PATH'] = self.expected['runtime']['LD_LIBRARY_PATH']
        return env

    def probe(self, model, arm, profile, original=False, rs3=False, suffix=''):
        label = f'state-{model}-{arm}'+('-original' if original else '')+('-rs3' if rs3 else '')+suffix
        self.phase(label)
        dump = self.root/(label+'.bin')
        command = [self.root/'C/test-combined-state', self.expected['models'][model]['path'],
                   common.ARMS[arm], dump, profile] + (['rs3'] if rs3 else [])
        env = self.model_env(arm, original)
        (self.root/(label+'.config.json')).write_text(json.dumps({'argv': list(map(str, command)),
            'runtime': {key: value for key, value in env.items() if key.startswith('SPINE_') or key == 'LD_LIBRARY_PATH'}}, indent=2)+'\n')
        with (self.root/(label+'.log')).open('w') as output:
            try:
                subprocess.run(list(map(str, command)), stdout=output, stderr=subprocess.STDOUT,
                               env=env, timeout=5400, check=True)
            except subprocess.CalledProcessError as exc:
                text = (self.root/(label+'.log')).read_text()
                if 'FAIL: candidate logits differ' in text or 'FAIL: nonfinite logits' in text:
                    raise common.NumericalStop('state numerical difference: '+label) from exc
                raise
        return self.validate_probe(label, arm, profile, original, rs3)

    def validate_probe(self, label, arm, profile, original=False, rs3=False):
        dump = self.root/(label+'.bin')
        text = (self.root/(label+'.log')).read_text()
        rows = [json.loads(line) for line in text.splitlines() if line.startswith('{')]
        prefixes = [32, 33, 64, 96] + ([] if profile == 'short' else [255, 256, 511, 512, 2047, 2048])
        keys = [(rs, reset, prefix) for rs in ([3] if rs3 else [0, 3]) for reset in (0, 1) for prefix in prefixes]
        if [(row['rs'], row['reset'], row['prefix']) for row in rows] != keys:
            raise ValueError('state coverage differs')
        if not all(row['bitwise_equal'] and row['max_abs'] == 0 for row in rows):
            raise common.NumericalStop('state numerical difference')
        if f'PASS: {len(keys)} full-vocabulary records;' not in text:
            raise ValueError('state completion marker is absent')
        threads = re.findall(r'COMBO_STATE threads=(\d+) batch_threads=(\d+) rs=(\d+)', text)
        if len(threads) != (1 if rs3 else 2)*(2 if arm != 'C0' else 1) or any(a != '4' or b != '4' for a, b, _ in threads):
            raise ValueError('state thread count differs')
        spans = re.findall(r'COMBO_STATE begin arm=(\d+)[^\n]*\n(.*?)COMBO_STATE end arm=\1', text, re.S)
        if len(spans) != len(keys)*(2 if arm != 'C0' else 1):
            raise ValueError('state arm spans differ')
        for active, span in spans:
            if active == '0' and ('K1_GDN_R2 worker=' in span or 'SPINE_GDN_PREFILL_R2:' in span or 'K1_FA path=B1 ' in span):
                raise ValueError('state control activates a candidate')
        selected = '\n'.join(span for active, span in spans if int(active) == common.ARMS[arm])
        if original:
            self.check_original_activation(text, arm)
        else:
            common.activation(selected, arm, fixed_route=False, require_shared=arm in ('B', 'F') and profile == 'long', rs3=rs3)
        self.check_routes(text, original)
        data = dump.read_bytes()
        if len(data) != sum(row['vocab']*4 for row in rows):
            raise ValueError('state dump size differs')
        mapping, offset = {}, 0
        for key, row in zip(keys, rows):
            size = row['vocab']*4
            mapping[key] = data[offset:offset+size]
            offset += size
        return mapping, {'rows': rows, 'dump_sha256': board.digest(dump), 'log_sha256': board.digest(self.root/(label+'.log'))}

    def verify_identity(self):
        self.verify_baseline()
        for path, value in self.summary['model_identity']['files'].items():
            if board.digest(path) != value:
                raise ValueError('combined identity changed: '+path)

    @staticmethod
    def check_routes(text, original=False):
        if 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' not in text:
            raise ValueError('state attention path evidence is absent')
        if not original and 'K1_GEMM_ROUTE mode=3' not in text:
            raise ValueError('state candidate route evidence is absent')

    @staticmethod
    def check_original_activation(text, arm):
        if arm != 'C0':
            raise ValueError('original library arm differs')
        markers = ('K1_SSM_CONV ', 'SPINE_GDN_PREFILL:', 'SPINE_GDN_PREFILL_R2:',
                   'K1_GDN_R2 worker=', 'K1_FA path=B1 ')
        if any(marker in text for marker in markers):
            raise ValueError('original library has a candidate marker')

    def native_stage(self):
        board.Run.execute(self)

    def execute(self):
        self.native_stage()
        if self.summary['candidates']['C'].get('status') == 'failed':
            raise RuntimeError('native stage failed: '+self.summary['candidates']['C'].get('error', 'unknown'))
        if not self.summary.get('combined_operator_gate'):
            self.summary['status'] = 'operator-gate-stopped'
            self.phase('combined operator gate stopped')
            return
        self.summary.update(state={}, rounds=[])
        files = {str(p): board.digest(p) for p in (self.root/'C/lib').glob('*.so*') if p.is_file()}
        files.update({info['path']: info['sha256'] for info in self.expected['models'].values()})
        files[str(self.server)] = board.digest(self.server)
        for path in ['C/test-combined-state', *json.loads((self.root/'frozen-files.json').read_text()).keys()]:
            files[str(self.root/path)] = board.digest(self.root/path)
        self.summary['model_identity'] = {'files': files, 'source_manifest_sha256': board.digest(self.root/'C/manifest.json')}
        for model in ('2B', '4B'):
            reference, record = self.probe(model, 'C0', 'long', original=True)
            saved = {'original': record}
            for arm in ('C0', 'H', 'G', 'L', 'P', 'B', 'F'):
                profile = 'long' if arm in ('C0', 'B', 'F') else 'short'
                mapping, record = self.probe(model, arm, profile)
                if any(value != reference[key] for key, value in mapping.items()):
                    raise common.NumericalStop('original full vocabulary differs: '+model+' '+arm)
                saved[arm] = record
                if arm in ('H', 'G', 'P', 'F'):
                    fallback, receipt = self.probe(model, arm, profile, rs3=True)
                    if any(value != reference[key] for key, value in fallback.items()):
                        raise common.NumericalStop('fresh RS fallback differs')
                    saved[arm]['fresh_rs3'] = receipt
                self.summary['state'][model] = saved
                self.save()
        self.verify_identity()
        for number in (1, 2):
            result = cold.compare_round(self.root, number, self, self.summary['model_identity'])
            self.summary['rounds'].append(result)
            self.verify_identity()
            if result['status'] != 'eligible':
                self.summary['status'] = result['status']
                self.phase('combined performance gate stopped; preserve results')
                return
        def expired(signum, frame):
            raise TimeoutError('complete-answer request budget expired')
        signal.signal(signal.SIGALRM, expired)
        signal.signal(signal.SIGTERM, expired)
        self.summary['complete_answers'] = {}
        for arm in ('P', 'F'):
            self.phase('complete paired answers '+arm)
            destination = self.root/('complete-answers-'+arm)
            value = answers.collect(destination, self.source, self.server, self.expected, self.root/'C/lib', arm)
            for model in ('2B', '4B'):
                pairs = json.loads((destination/(model+'-pairs.json')).read_text())
                for task, pair in pairs.items():
                    if pair['C0']['request'] != pair[arm]['request'] or pair['C0']['answer'] != pair[arm]['answer']:
                        raise ValueError('complete answer differs: '+arm+' '+model+' '+task)
                common.activation((destination/(model+'-'+arm+'.server.log')).read_text(), arm,
                                  require_both=True, require_shared=arm == 'F')
            self.summary['complete_answers'][arm] = value
            self.verify_identity()
            self.save()
        self.summary['status'] = 'complete-answers-generated; review-pending'
        self.phase('combined campaign complete; local review pending')


def main():
    def expired(signum, frame):
        raise TimeoutError('combined campaign budget expired')
    signal.signal(signal.SIGTERM, expired)
    signal.signal(signal.SIGALRM, expired)
    run = Run(Path(sys.argv[1]))
    lock_path = Path.home()/'Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock'
    run.phase('wait for shared experiment lock')
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            run.execute()
        except common.NumericalStop as exc:
            run.summary.update(status='numerical-gate-stopped', error=str(exc))
            (run.root/'numerical-stop.txt').write_text(traceback.format_exc())
            run.phase('combined numerical gate stopped; preserve result')
        except BaseException as exc:
            run.summary.update(status='failed', error=str(exc))
            (run.root/'failure.txt').write_text(traceback.format_exc())
            run.phase('combined campaign failed; preserve evidence')
            raise
        finally:
            try:
                run.verify_baseline()
            finally:
                run.save()
    return 0


if __name__ == '__main__':
    sys.exit(main())
