#!/usr/bin/env python3
"""在本机复核两机全部记录与速度比。"""
import hashlib
import json
from pathlib import Path
import statistics

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[1]
reference = json.loads((ROOT/'lab/k1-server-deploy-20261011/received/validation/conv-result/result.json').read_text())
reference = {c['id']: c for c in reference['cases']}
summary = {'status': 'passed', 'hosts': {}, 'paired_cases_checked': 0, 'receipt_entries_checked': 0,
    'K1_performance': 'unverified', 'scope': 'full host workflow; compiler and Python versions differ'}
for host, folder, jobs in [('local', WORK/'run-local', 3),
        ('server', WORK/'received-server/run-server', 5)]:
    result = json.loads((folder/'result.json').read_text())
    assert result['status'] == 'complete'
    for line in (folder/'BENCHMARK-SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        assert hashlib.sha256((folder/name).read_bytes()).hexdigest() == digest
        summary['receipt_entries_checked'] += 1
    for run in result['warmup']+result['runs']:
        path = folder/run['name']
        batch = json.loads((path/'result.json').read_text())
        topology = json.loads((path/'topology.json').read_text())
        assert batch['status'] == 'screen-complete-needs-board' and len(batch['cases']) == 40
        expected_jobs = 1 if run['jobs_requested'] == 1 else jobs
        assert len(topology['groups']) == expected_jobs
        assert batch['maximum_active_jobs'] == expected_jobs
        for item in batch['cases']:
            assert item['actual_affinity'] == item['group']['cpus']
            child = json.loads((path/item['id']/'result.json').read_text())['cases'][0]
            expected = reference[item['id'].rsplit('-r', 1)[0]]
            assert child['status'] == 'needs-board'
            for arm in ('control', 'candidate'):
                assert child['arms'][arm] == expected['arms'][arm]
            summary['paired_cases_checked'] += 1
    median = {mode: statistics.median(r['wall_seconds'] for r in result['runs']
        if r['name'].startswith(mode+'-')) for mode in ('serial', 'parallel')}
    assert median == result['median_seconds']
    summary['hosts'][host] = {'median_seconds': median, 'runs': result['runs'],
        'parallel_jobs': jobs, 'parallel_speedup': median['serial']/median['parallel'],
        'cases_per_second': {mode: 40/value for mode, value in median.items()}}
    for key in ('plan_sha256', 'parallel_sha256', 'batch_sha256'):
        summary.setdefault('identities', {}).setdefault(key, result[key])
        assert summary['identities'][key] == result[key]
local, server = (summary['hosts'][key]['median_seconds'] for key in ('local', 'server'))
summary['server_speedup_vs_local'] = {mode: local[mode]/server[mode] for mode in ('serial', 'parallel')}
summary['server_parallel_vs_local_serial'] = local['serial']/server['parallel']
(WORK/'local-review.json').write_text(json.dumps(summary, indent=2)+'\n')
print(json.dumps(summary, indent=2))
