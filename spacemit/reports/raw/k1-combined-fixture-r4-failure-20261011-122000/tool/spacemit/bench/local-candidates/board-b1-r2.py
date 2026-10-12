#!/usr/bin/env python3
"""Run B1-r2 operator gates and verify the declared dispatch boundary."""
import re
import sys

import board


class RevisedRun(board.Run):
    def __init__(self, root):
        super().__init__(root)
        if self.arms != ['B1']:
            raise ValueError('B1-r2 requires one B1 arm')
        self.summary['revision'] = 'B1-r2'
        self.summary['parent_result'] = 'k1-local-candidates-20261008-184350'

    def numeric(self, arm, reference_attention, reference_ssm):
        result = super().numeric(arm, reference_attention, reference_ssm)
        text = (self.root/'B1-numeric.log').read_text()
        rows = re.findall(r'K1_FA path=([\w-]+) heads=(\d+) kv_heads=(\d+) history=(\d+) chunk=\d+:\d+ worker=(\d+) workers=(\d+)', text)
        required = [('reference-underfilled-groups', 8, history) for history in (255, 256, 511)]
        required += [('B1', heads, history) for heads in (8, 16) for history in (512, 513, 2048)]
        required += [('B1', 16, 256)]
        for path, heads, history in required:
            workers = {int(worker) for actual, h, kv, n, worker, count in rows
                       if (actual, int(h), int(kv), int(n), int(count)) == (path, heads, heads//4, history, 4)}
            if workers != {0, 1, 2, 3}:
                raise ValueError('B1-r2 dispatch evidence is incomplete: '+str((path, heads, history)))
        if any(path == 'B1' and int(n) < 512 and int(kv) < int(count)
               for path, heads, kv, n, worker, count in rows):
            raise ValueError('B1-r2 uses an underfilled group path')
        result['dispatch_boundary'] = 'short underfilled groups use the original path'
        result['required_shapes_verified'] = len(required)
        return result


if __name__ == '__main__':
    board.Run = RevisedRun
    sys.exit(board.main())
