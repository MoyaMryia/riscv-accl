#!/usr/bin/env python3
"""验证并发核心分组、完整输出和故障停止。"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'lab/server-parallel-validation-20261011'
OUT.mkdir(exist_ok=False)
base = json.loads((ROOT/'lab/server-validation-20261011/conv-plan/plan.json').read_text())
plan = copy.deepcopy(base)
plan['scope'] = 'parallel infrastructure check; repeated shapes are not performance samples'
plan['cases'] = []
for repeat in range(2):
    for case in base['cases']:
        case = copy.deepcopy(case)
        case['id'] += '-r'+str(repeat+1)
        plan['cases'].append(case)
(OUT/'plan.json').write_text(json.dumps(plan, indent=2)+'\n')
subprocess.run([sys.executable, ROOT/'spacemit/bench/qemu-screen/parallel.py', OUT/'positive',
    '--plan', OUT/'plan.json', '--cores-per-job', '4', '--max-jobs', '5'], check=True)
result = json.loads((OUT/'positive/result.json').read_text())
topology = json.loads((OUT/'positive/topology.json').read_text())
expected = [list(range(n, n+4)) for n in (0, 4, 8, 12, 16)]
assert [g['cpus'] for g in topology['groups']] == expected
assert [g['kind'] for g in topology['groups']] == ['P', 'P', 'E', 'E', 'E']
assert result['status'] == 'screen-complete-needs-board'
assert result['maximum_active_jobs'] == 5 and len(result['cases']) == 8
serial = json.loads((ROOT/'lab/server-validation-20261011/conv-result/result.json').read_text())
serial = {c['id']: c for c in serial['cases']}
for record in result['cases']:
    assert record['actual_affinity'] == record['group']['cpus']
    child = json.loads((OUT/'positive'/record['id']/'result.json').read_text())['cases'][0]
    reference = serial[record['id'].rsplit('-r', 1)[0]]
    for arm in ('control', 'candidate'):
        assert child['arms'][arm] == reference['arms'][arm]
negative = copy.deepcopy(plan)
negative['scope'] = 'intentional invalid control argument; dispatcher stop check'
negative['cases'][0]['control']['args'][0] = '123'
(OUT/'negative-plan.json').write_text(json.dumps(negative, indent=2)+'\n')
subprocess.run([sys.executable, ROOT/'spacemit/bench/qemu-screen/parallel.py', OUT/'negative',
    '--plan', OUT/'negative-plan.json', '--cores-per-job', '4', '--max-jobs', '5'], check=True)
stopped = json.loads((OUT/'negative/result.json').read_text())
assert stopped['status'] == 'stopped'
assert stopped['first_stop_case'] == negative['cases'][0]['id']
child = json.loads((OUT/'negative'/stopped['first_stop_case']/'result.json').read_text())
assert child['cases'][0]['status'] == 'control-execution-failed'
assert stopped['unstarted_cases']
review = {'status': 'passed', 'positive_cases': 8, 'maximum_active_jobs': 5,
    'groups': topology['groups'], 'serial_full_output_and_metrics_equal': True,
    'intentional_stop_status': child['cases'][0]['status'],
    'unstarted_cases': stopped['unstarted_cases'],
    'K1_performance': 'unverified'}
(OUT/'review.json').write_text(json.dumps(review, indent=2)+'\n')
print(json.dumps(review, indent=2))
