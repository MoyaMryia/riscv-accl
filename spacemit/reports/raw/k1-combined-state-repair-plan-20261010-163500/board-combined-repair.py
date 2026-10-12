#!/usr/bin/env python3
"""核验已通过的原生记录，并在新目录重跑模型阶段。"""
import json
from pathlib import Path

import board

parent = board.module('combined_repaired_controller', board.HERE/'board-combined.py')


class RepairRun(parent.Run):
    def native_stage(self):
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
        self.summary.update(revision='combined-fixture-r2', parent_result=receipt['parent_root'],
                            native_reuse_receipt_sha256=board.digest(self.root/'native-reuse.json'),
                            native_review_sha256=board.digest(self.root/'native-independent-review.json'))
        self.phase('native stage retained; fresh model states pending')


if __name__ == '__main__':
    parent.Run = RepairRun
    raise SystemExit(parent.main())
