#!/usr/bin/env python3
"""核验已通过的原生记录，并在新目录重跑模型阶段。"""
import json
import subprocess
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
        self.summary.update(revision='combined-fixture-r4', parent_result=receipt['parent_root'],
                            native_reuse_receipt_sha256=board.digest(self.root/'native-reuse.json'),
                            native_review_sha256=board.digest(self.root/'native-independent-review.json'))
        self.phase('archive retained native evidence')
        archive = self.root/'retained-native-evidence.tar.gz'
        skip = ['C-ssm-3.bin','control-ssm.bin','original-ssm.bin',
                'C2-r2-control-numeric.bin','C2-r2-original-numeric.bin','combined-legacy-gdn.bin',
                'control-attention.bin','original-attention.bin']
        subprocess.run(['tar','-czf',str(archive),*[f'--exclude=./{name}' for name in skip],
                        '-C',str(source),'.'],check=True,timeout=900)
        (self.root/'archive-ready.json').write_text(json.dumps({'sha256':board.digest(archive),
            'bytes':archive.stat().st_size,'parent_files':receipt['parent_files']},indent=2)+'\n')
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
