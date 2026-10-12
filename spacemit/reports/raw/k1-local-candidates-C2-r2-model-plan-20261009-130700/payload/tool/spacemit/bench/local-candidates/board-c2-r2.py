#!/usr/bin/env python3
"""Run the C2-r2 numeric and operator gates."""
import json
import re
import sys

import board


class RevisedRun(board.Run):
    def __init__(self, root):
        super().__init__(root)
        if self.arms != ['C']:
            raise ValueError('C2-r2 requires one C arm')
        self.summary['revision'] = 'C2-r2'
        self.summary['parent_result'] = 'k1-local-candidates-C2-repeat-20261008-215300'

    def verify(self):
        super().verify()
        manifest = json.loads((self.root/'C/manifest.json').read_text())
        if manifest['revision'] != 'C2-r2':
            raise ValueError('revision label differs')
        if board.digest(self.root/'C/test-gdn-r2.cpp') != manifest['fixture_sha256']:
            raise ValueError('GDN fixture hash differs')

    def build_all(self):
        super().build_all()
        if self.summary['candidates']['C']['build'] != 'pass':
            return
        self.harness('C', self.root/'C/test-gdn-r2.cpp', 'test-gdn-r2')
        text = self.command(['objdump', '-d', '-C', self.root/'C/ops.cpp.o'], 'C2-r2-assembly')
        start = re.search(r'^\w+ <spine_k1_gdn_prefill128\([^\n]*>:\n', text, re.M)
        if not start:
            raise ValueError('GDN revision assembly is absent')
        rest = text[start.end():]
        end = re.search(r'^\w+ <(?!\.L)[^\n]+>:\n', rest, re.M)
        body = rest[:end.start()] if end else rest
        if re.search(r'\b(?:sp|vs[1248]r\.v|vl[1248]re\d+\.v)\b', body):
            raise ValueError('GDN revision uses the stack or whole-register transfers')
        if len(re.findall(r'\bvle32\.v\b', body)) != 8 or len(re.findall(r'\bvse32\.v\b', body)) != 2:
            raise ValueError('GDN revision memory instruction count differs')
        if len(re.findall(r'\bvfredusum\.vs\b', body)) != 2:
            raise ValueError('GDN reduction instruction count differs')
        self.summary['revision_assembly'] = {'state_loads_per_row': 2, 'state_stores_per_row': 2,
                                             'stack_transfers': 0, 'log': 'C2-r2-assembly.log'}

    def numeric(self, arm, reference_attention, reference_ssm):
        result = super().numeric(arm, reference_attention, reference_ssm)
        values = {}
        for library in ('original', 'control', 'C'):
            value, text = self.dump(library, self.root/'C/test-gdn-r2', [],
                                    'C2-r2-'+library+'-numeric', 'PASS: 158')
            values[library] = value
            if 'K1_GDN_THREADS plan=4' not in text:
                raise ValueError('actual GDN thread count is absent')
            if library == 'C' and 'SPINE_GDN_PREFILL_R2: retained two state segments' not in text:
                raise ValueError('GDN revision activation is absent')
            if library == 'C':
                workers = set(re.findall(r'K1_GDN_R2 worker=(\d+) workers=4 state=128', text))
                if workers != {'0', '1', '2', '3'}:
                    raise ValueError('actual GDN worker evidence is incomplete')
        if len(set(values.values())) != 1:
            raise ValueError('original GDN output or state differs')
        result['gdn_original_control_sha256'] = values
        result['gdn_revision'] = 'two retained state segments; exact output and state'
        return result

    def operators(self, arm):
        self.phase('operator screen C2-r2')
        text = self.command([self.root/'C/test-gdn-r2', '--bench'], 'C2-r2-operators', arm,
                            updates={'SPINE_K1_TRACE': '0'})
        rows = [json.loads(line) for line in text.splitlines() if line.startswith('{')]
        expected = [(heads, tokens, block, mode) for heads in (16, 32) for tokens in (8, 32)
                    for block in range(6) for mode in ((1, 0) if block % 2 else (0, 1))]
        actual = [(r['heads'], r['tokens'], r['block'], r['mode']) for r in rows]
        if actual != expected or any(r['state_size'] != 128 or r['key_heads'] != 16 for r in rows):
            raise ValueError('GDN operator shapes or order differ')
        if text.count('K1_GDN_THREADS plan=4') != 4:
            raise ValueError('GDN operator thread evidence differs')
        comparisons = self.comparisons(rows, ['heads', 'tokens'], 'mode')
        eligible = not any(r['clear_regression'] for r in comparisons)
        eligible = eligible and all(r['advance'] for r in comparisons if r['tokens'] == 32)
        self.summary['strict_operator_gate'] = {'eligible': eligible, 'primary_tokens': 32,
                                                'primary_heads': [16, 32]}
        return {'C2': comparisons}

    def execute(self):
        super().execute()
        eligible = self.summary.get('strict_operator_gate', {}).get('eligible', False)
        self.summary['eligible_for_model_gates'] = ['C2-r2'] if eligible else []
        self.summary['models'] = 'pending' if eligible else 'not-eligible'
        self.phase('C2-r2 operator gates complete; model gates pending' if eligible
                   else 'C2-r2 operator gates complete; model gates stopped')


if __name__ == '__main__':
    board.Run = RevisedRun
    sys.exit(board.main())
