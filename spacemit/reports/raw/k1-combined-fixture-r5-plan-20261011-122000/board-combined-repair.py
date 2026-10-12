#!/usr/bin/env python3
"""核验已通过的原生记录，并在新目录重跑模型阶段。"""
import json
import subprocess
import re
from pathlib import Path

import board

parent = board.module('combined_repaired_controller', board.HERE/'board-combined.py')


class RepairRun(parent.Run):
    def native_stage(self):
        modes = json.loads((self.root/'artifact-modes.json').read_text())
        for relative, mode in modes.items():
            if (self.root/relative).stat().st_mode & 0o777 != mode:
                raise ValueError('artifact mode differs: '+relative)
        self.verify()
        self.phase('verify retained native stage and exact libraries')
        receipt = json.loads((self.root/'native-reuse.json').read_text())
        source = Path(receipt['parent_root'])
        for relative, expected in receipt['parent_files'].items():
            if board.digest(source/relative) != expected:
                raise ValueError('retained native evidence differs: '+relative)
        for relative, expected in receipt['copied_artifacts'].items():
            if board.digest(self.root/relative) != expected:
                raise ValueError('copied library or probe differs: '+relative)
        previous = json.loads((source/'summary.json').read_text())
        if previous['error'] != 'hybrid activation markers absent':
            raise ValueError('parent failure differs')
        if previous['candidates']['C']['status'] != 'operator-screen-complete':
            raise ValueError('parent native stage did not complete')
        if not previous['combined_operator_gate'] or not previous['strict_operator_gate']['eligible']:
            raise ValueError('parent native gate did not pass')
        for key in ('candidates', 'original_control', 'strict_operator_gate',
                    'combined_operator_gate', 'revision_assembly', 'eligible_for_model_gates'):
            self.summary[key] = previous[key]
        self.summary.update(revision='combined-fixture-r5', parent_result=receipt['parent_root'],
                            native_reuse_receipt_sha256=board.digest(self.root/'native-reuse.json'),
                            native_review_sha256=board.digest(self.root/'native-independent-review.json'))
        self.phase('verify retained evidence archive')
        archive_source = json.loads((self.root/'retained-archive.json').read_text())
        if board.digest(Path(archive_source['path'])) != archive_source['sha256']:
            raise ValueError('retained native archive differs')
        self.phase('verify runtime loader dependencies')
        loader = Path('/lib/ld-linux-riscv64-lp64d.so.1')
        checks = {}
        for original in (True, False):
            for binary, label in ((self.root/'C/test-combined-state','probe'),(self.server,'server')):
                name = ('original-' if original else 'candidate-')+label
                env = self.model_env('C0', original)
                result = subprocess.run([str(loader),'--list',str(binary)],env=env,
                    stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=60,check=True)
                (self.root/('loader-'+name+'.log')).write_text(result.stdout)
                paths = dict(re.findall(r'([\w.+-]+) => (/[^(\s]+)', result.stdout))
                for soname in ('libggml.so.0','libggml-base.so.0','libllama.so.0'):
                    actual = Path(paths[soname])
                    if original or soname != 'libllama.so.0':
                        expected = self.expected['artifacts_sha256'][str(actual)]
                    else:
                        if actual.resolve() != (self.root/'C/lib'/soname).resolve():
                            raise ValueError('candidate loader uses original llama')
                        expected = receipt['copied_artifacts']['C/lib/'+soname]
                    if board.digest(actual) != expected:
                        raise ValueError('runtime dependency differs: '+soname)
                checks[name] = {'paths':paths,'runtime':env['LD_LIBRARY_PATH']}
        self.summary['loader_preflight'] = checks
        self.phase('short live activation preflight')
        reference, record = self.probe('2B','C0','short',suffix='-smoke')
        smoke = {'C0':record}
        for arm in ('H','G','L','P','F'):
            mapping, record = self.probe('2B',arm,'short',suffix='-smoke')
            if mapping != reference:
                raise parent.common.NumericalStop('short preflight vocabulary differs: '+arm)
            smoke[arm] = record
        mapping, record = self.probe('2B','F','short',rs3=True,suffix='-smoke')
        if any(value != reference[key] for key,value in mapping.items()):
            raise parent.common.NumericalStop('short preflight RS fallback differs')
        smoke['F-rs3'] = record
        self.summary['live_preflight'] = smoke
        self.phase('live activation preflight passed; fresh formal model states pending')


if __name__ == '__main__':
    parent.Run = RepairRun
    raise SystemExit(parent.main())
