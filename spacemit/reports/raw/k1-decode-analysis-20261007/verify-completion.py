#!/usr/bin/env python3
"""Independently recheck the frozen decode diagnostic and derive its report table."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent/'k1-decode-audit-20261007-074314'
spec = importlib.util.spec_from_file_location('frozen_audit', ROOT/'k1-decode-audit.py')
audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
run = json.loads((ROOT/'run.json').read_text())
receipt = json.loads((ROOT/'collection-receipt.json').read_text())
summary = json.loads((ROOT/'summary.json').read_text())
verification = json.loads((ROOT/'collection-verification.json').read_text())
assert (ROOT/'exit-status').read_text().strip() == '0'
assert (ROOT/'collector-exit-status').read_text().strip() == '0'
assert verification['board_exit_status'] == '0'
assert verification['remote_staged_code_sha256'] == run['code_sha256']
assert sha(ROOT/'profile-artifacts.tar.gz') == receipt['archive_sha256']
with tarfile.open(ROOT/'profile-artifacts.tar.gz') as bundle:
    members = bundle.getmembers()
    names = [m.name for m in members]
    assert len(names) == len(set(names)) and set(names) == set(receipt['files_sha256'])
    assert all(m.isfile() and Path(m.name).name == m.name for m in members)
assert all(sha(ROOT/n) == h for n,h in receipt['files_sha256'].items())
assert all(sha(ROOT/n) == h for n,h in run['code_sha256'].items())
assert all(sha(ROOT/n) == h for n,h in run['collector_code_sha256'].items())
expected = json.loads((ROOT/'expected-provenance.json').read_text())
provenance = json.loads((ROOT/'provenance.json').read_text())
assert provenance['models'] == expected['models']
assert provenance['settings']['perf_clockid'] == 'CLOCK_MONOTONIC'
assert provenance['settings']['model_warmup'] is False
native = summary['stages']['native']
assert native['cases_per_arm'] == 104 and native['bitwise_equal']
for arm in ('baseline','audit-off','audit-on'):
    assert 'PASS: 104 production graph cases; input/output/scratch guards' in (ROOT/(arm+'.native.log')).read_text()
    assert sha(ROOT/(arm+'.native.data')) == native['output_sha256'][arm]
assert len(set(native['output_sha256'].values())) == 1
assert summary['status'] == 'diagnostic complete'
assert set(summary['stages']) == {'native','2B-256','2B-2048','4B-256','4B-2048'}
cases = []
for model in ('2B','4B'):
    for length in (256,2048):
        case = f'{model}-{length}'
        requests = {}
        for arm in ('profile','audit'):
            label = case+'-'+arm
            r = json.loads((ROOT/(label+'.request.json')).read_text())
            assert len(r['prompt_ids']) == length
            assert len(r['token_ids']) == r['tokens_predicted'] == 65
            assert r['stop_type'] == 'limit' and not r['error'] and r['server_slot'] == 0
            assert r['timings']['prompt_n'] == length and r['timings']['cache_n'] == 0
            assert r['sha256'] == hashlib.sha256(r['text'].encode()).hexdigest()
            assert r['tokens_sha256'] == hashlib.sha256(json.dumps(r['token_ids'],separators=(',',':')).encode()).hexdigest()
            assert r['server_ready_ns'] <= r['request_start_ns'] < r['first_token_ns'] < r['request_end_ns']
            assert r['profile_window']['enable_sent_ns'] >= r['first_token_ns']
            log = (ROOT/(label+'.server.log')).read_text()
            markers = re.findall(r'K1_GEMM_ROUTE mode=(\d) phase=(prefill|single) eligible=(\d) bypass=(\d)',log)
            assert {m[1] for m in markers} == {'prefill','single'}
            assert all(m[0] == '3' and m[2:] == ('1','1') for m in markers)
            assert 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled' in log
            assert '--no-warmup' in r['server_command']
            requests[arm] = r
        assert all(requests['profile'][k] == requests['audit'][k] for k in ('prompt_ids','token_ids','text'))
        stacks = (ROOT/(case+'-profile.stacks.txt')).read_text()
        cpu = audit.profile.summarize(stacks)
        cpu_saved = json.loads((ROOT/(case+'-profile.profile.json')).read_text())
        assert all(cpu[k] == cpu_saved[k] for k in cpu)
        assert audit.verify_sample_window(stacks, requests['profile']['profile_window']) == cpu_saved['sample_window_verification']
        assert 'PERF_RECORD_LOST' not in (ROOT/(case+'-profile.lost.txt')).read_text()
        rows = [json.loads(line) for line in (ROOT/(case+'-audit.counters.jsonl')).read_text().splitlines()]
        log_rows = [json.loads(line.split('K1_DECODE_AUDIT ',1)[1]) for line in (ROOT/(case+'-audit.server.log')).read_text().splitlines() if line.startswith('K1_DECODE_AUDIT ')]
        assert rows == log_rows
        counters = audit.audit_summary(rows, requests['audit'])
        assert counters == json.loads((ROOT/(case+'-audit.attribution.json')).read_text())
        pairs = counters['ffn_pairs']
        assert pairs['adjacent_same_input_pairs'] == (1536 if model == '2B' else 2048)
        assert set(pairs['pairs_by_layer'].values()) == {64}
        period_sum = main_sync = worker_sync = 0
        pending = False
        for line in stacks.splitlines():
            match = re.match(r'^\S+\s+(\d+)/(\d+)\s+[\d.]+:\s+(\d+)\s+cpu-clock:u:',line)
            if match:
                pid,tid,period = map(int,match.groups()); period_sum += period; pending = True
            elif pending and line.strip():
                pending = False
                if 'sync_impl' in line:
                    if tid == pid: main_sync += period
                    else: worker_sync += period
        assert worker_sync == 0
        dec = counters['decode']; pref = counters['prefill']
        head = counters['decode_weights']['token_embd.weight']
        cases.append(dict(model=model,prompt_tokens=length,exact_identity=True,decode_tokens_s=requests['profile']['timings']['predicted_per_second'],
                          prefill_tokens_s=requests['profile']['timings']['prompt_per_second'],samples=cpu['samples'],
                          ime_self_cpu_pct=sum(x['cpu_pct'] for x in cpu['top_self'] if x['symbol'] in ('LOOP_INNER360','LOOP_K360')),
                          calling_thread_sync_cpu_pct=100*main_sync/period_sum,
                          worker_barrier_self_cpu_pct=sum(x['cpu_pct'] for x in cpu['top_self'] if 'barrier_coro' in x['symbol']),
                          decode_quant_worker_pct=100*dec['elapsed_fraction']['activation_quantization'],
                          prefill_quant_worker_pct=100*pref['elapsed_fraction']['activation_quantization'],
                          duplicate_branch_worker_pct=100*pairs['worker_elapsed_fraction'],
                          duplicate_branch_worker_ms=pairs['smaller_branch_worker_packing_ns']/1e6,
                          pairs=pairs['adjacent_same_input_pairs'],duplicate_input_bytes=pairs['smaller_branch_input_bytes'],
                          head_gemm_worker_pct=100*head['worker_elapsed_ns']/dec['worker_elapsed_ns'],
                          startup_records=counters['startup_compatibility_probe']['records']))
result = dict(status='verified',board_exit_status=0,collector_exit_status=0,elapsed_s=summary['elapsed_s'],
              artifacts_verified=len(receipt['files_sha256']),staged_code_verified=len(run['code_sha256']),
              collector_code_verified=len(run['collector_code_sha256']),native_cases_per_arm=104,native_arms=3,
              requests=8,profiles=4,cases=cases,packing_candidate_advanced=False,
              reason='Duplicate FFN packing is below the declared 3% priority signal in every case. No pointer cache or paired operation introduced.')
(HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
