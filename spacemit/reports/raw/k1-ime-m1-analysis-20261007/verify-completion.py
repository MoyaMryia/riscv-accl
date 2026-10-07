#!/usr/bin/env python3
"""Independently verify the frozen fixed-K32 experiment without rerunning it."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import statistics
import tarfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent/'k1-ime-m1-k32-20261007-121231'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
run=json.loads((ROOT/'run.json').read_text())
receipt=json.loads((ROOT/'collection-receipt.json').read_text())
summary=json.loads((ROOT/'summary.json').read_text())
verified=json.loads((ROOT/'collection-verification.json').read_text())
provenance=json.loads((ROOT/'provenance.json').read_text())
expected=json.loads((ROOT/'expected-provenance.json').read_text())
routing=json.loads((ROOT/'routing-provenance.json').read_text())
assert (ROOT/'exit-status').read_text().strip()=='0'
assert (ROOT/'collector-exit-status').read_text().strip()=='0'
assert verified['board_exit_status']=='0'
assert verified['remote_staged_code_sha256']==run['code_sha256']
assert verified['staged_code_verified'] and verified['collector_code_verified']
assert sha(ROOT/'profile-artifacts.tar.gz')==receipt['archive_sha256']
with tarfile.open(ROOT/'profile-artifacts.tar.gz') as bundle:
    members=bundle.getmembers(); names=[m.name for m in members]
    assert len(names)==len(set(names)) and set(names)==set(receipt['files_sha256'])
    assert all(m.isfile() and Path(m.name).name==m.name for m in members)
    for m in members:
        assert hashlib.sha256(bundle.extractfile(m).read()).hexdigest()==receipt['files_sha256'][m.name]
assert all(sha(ROOT/n)==h for n,h in receipt['files_sha256'].items())
assert all(sha(ROOT/n)==h for n,h in run['code_sha256'].items())
assert all(sha(ROOT/n)==h for n,h in run['collector_code_sha256'].items())
assert provenance['models']==expected['models']==routing['models']
assert provenance['baseline_relink_sha256']==provenance['baseline_route3_library']['sha256']==routing['candidate_library_sha256']=='43363dad9c500bd71d5ad7cc9d0108efff5c58133b7b8b39d69b3edeb94952ee'
assert sha(ROOT/'baseline-ime-m1-k32.cpp')==provenance['baseline_kernel_sha256']
assert sha(ROOT/'candidate-ime-m1-k32.cpp')==provenance['candidate_source_sha256']
assert 'PASS: 480 cases;' in (ROOT/'raw-numeric.log').read_text()
assert summary['stages']['raw_numeric']['cases']==480
assert summary['stages']['raw_numeric']['bitwise_equal']
runner_spec=importlib.util.spec_from_file_location('frozen_runner',ROOT/'k1-ime-m1-k32.py')
runner=importlib.util.module_from_spec(runner_spec); runner_spec.loader.exec_module(runner)
assert runner.patcher.generate((ROOT/'baseline-ime-m1-k32.cpp').read_text())==(ROOT/'candidate-ime-m1-k32.cpp').read_text()
assert set(summary['stages'])=={'raw_numeric','production_numeric','operators'}
native=summary['stages']['production_numeric']
assert native['cases_per_arm']==104 and native['bitwise_equal'] and native['arms']==[-1,0,1]
for mode in (-1,0,1):
    log=(ROOT/f'graph-{mode}.log').read_text()
    assert 'PASS: 104 production graph cases;' in log
    runner.Run.activation(None,log,mode,('single','prefill'))
    assert sha(ROOT/f'graph-{mode}.data')==native['sha256'][str(mode)]
assert len(set(native['sha256'].values()))==1
assert len(native['full_shape_checks'])==6
shapes=set()
for r in native['full_shape_checks']:
    assert r['m']==1
    shapes.add((r['model'],r['m'],r['k'],r['n']))
    for mode in (-1,0,1):
        name=f"full-{r['model']}-k{r['k']}-n{r['n']}-q{mode}"
        assert (ROOT/(name+'.data')).stat().st_size==r['n']*4
        assert sha(ROOT/(name+'.data'))==r['sha256'][str(mode)]
        runner.Run.activation(None,(ROOT/(name+'.log')).read_text(),mode)
    assert len(set(r['sha256'].values()))==1
assert sum(r['n']==248320 for r in native['full_shape_checks'])==2
for model,d in provenance['shapes'].items():
    shapes.add((model,32,d['embedding_length'],d['feed_forward_length']))
rows=[json.loads(line) for line in (ROOT/'operator.jsonl').read_text().splitlines()]
assert len(rows)==144
assert {(r['model'],r['m'],r['k'],r['n'],r['block'],r['mode']) for r in rows}=={(*s,b,q) for s in shapes for b in range(6) for q in (-1,0,1)}
for r in rows:
    name=f"op-{r['model']}-m{r['m']}-k{r['k']}-n{r['n']}-b{r['block']}-q{r['mode']}"
    log=(ROOT/(name+'.log')).read_text()
    found=[json.loads(line) for line in log.splitlines() if line.startswith('{')]
    assert len(found)==1
    assert all(found[0][k]==r[k] for k in found[0])
    assert r['wall_ms']>=100 and r['iterations']>0 and math.isfinite(r['ms_per_call']) and r['ms_per_call']>0
    assert math.isclose(r['ms_per_call'],r['wall_ms']/r['iterations'],rel_tol=1e-8)
    runner.Run.activation(None,log,r['mode'],('single',) if r['m']==1 else ('prefill',))
    assert 'cpu_mask: f' in log and 'num_perfer_cores: 4' in log
comparisons=summary['stages']['operators']['comparisons']; controls=summary['stages']['operators']['original_control_checks']
assert len(comparisons)==len(controls)==8
assert summary['stages']['operators']['records']==144
result=[]
for shape in sorted(shapes):
    model,m,k,n=shape
    arms={mode:[r['ms_per_call'] for r in rows if (r['model'],r['m'],r['k'],r['n'],r['mode'])==(*shape,mode)] for mode in (-1,0,1)}
    for table,a,b in [(comparisons,0,1),(controls,-1,0)]:
        saved=next(r for r in table if (r['model'],r['m'],r['k'],r['n'])==shape)
        recalculated=runner.fast.gate(arms[a],arms[b])
        assert all(saved[key]==value for key,value in recalculated.items())
    result.append(dict(model=model,m=m,k=k,n=n,original_ms=statistics.mean(arms[-1]),control_ms=statistics.mean(arms[0]),candidate_ms=statistics.mean(arms[1]),
        reduction_vs_control_pct=100*(1-statistics.mean(arms[1])/statistics.mean(arms[0])),
        reduction_vs_original_pct=100*(1-statistics.mean(arms[1])/statistics.mean(arms[-1])),
        control_range_pct=runner.fast.gate(arms[0],arms[1])['control_range_pct']))
assert not any(r['advance'] for r in comparisons)
assert not any(r['clear_regression'] for r in comparisons+controls)
assert summary['status']=='inconclusive'
assembly=(ROOT/'assembly.txt').read_text()
helper=assembly[assembly.index('<spacemit_kernels::(anonymous namespace)::k1_m1_k32_fixed'):assembly.index('<spacemit_kernels::ime1::quantize_a_4row_i8')]
assert 'LOOP_INNER' not in helper
assert len(re.findall(r'\bvmadot\s',helper))==16
assert len(re.findall(r'\bvfmacc\.vv\s',helper))==4
start=helper.index('<LOOP_K'); end=helper.index('bnez\t',start)
assert '<LOOP_K' in helper[end:helper.index('\n',end)]
assert not re.search(r'\b(?:beqz|bnez|blt|bge|bltu|bgeu|beq|bne)\s',helper[start:end])
assert 'LOOP_INNER' in assembly[len(helper):]
output=dict(status='verified negative operator screen',board_exit_status=0,collector_exit_status=0,elapsed_s=summary['elapsed_s'],
 artifacts_verified=len(receipt['files_sha256']),archive_sha256=receipt['archive_sha256'],staged_code_count=len(run['code_sha256']),collector_code_count=len(run['collector_code_sha256']),
 raw_cases=480,production_cases_per_arm=104,full_shapes_per_arm=6,full_vocabulary=248320,bitwise_equal=True,operators=144,
 assembly=dict(fixed_steps=2,vmadot_per_block=16,block_fma=4,inner_branch_removed=True,original_fallback_retained=True),
 measurements=result,all_operator_advancement_gates_failed=True,clear_regressions=0,
 skipped=['full-model state/reset/RS snapshots','cold model ABBA at 256/2048 tokens','naturally complete useful answers'],
 limitations='Warm production operators only; control variability is substantial for some shapes. No reliable speed gain or whole-model/quality conclusion. Artifact checks exclude this derived verification directory.')
remote_path=HERE/'remote-preservation.json'
if remote_path.exists():
    remote=json.loads(remote_path.read_text())
    assert remote['board_exit_status']==0
    assert remote['files_verified']==len(remote['files_sha256'])==40
    assert all(remote['files_sha256'][name]==value for name,value in provenance['linked_object_sha256'].items())
    assert remote['files_sha256'][provenance['baseline_route3_library']['path']]==provenance['baseline_route3_library']['sha256']
    assert remote['files_sha256'][run['remote_root']+'/lib/libggml-cpu.so.0.16.0']==provenance['candidate_library_sha256']
    assert all(remote['files_sha256'][run['remote_root']+'/'+name]==value for name,value in run['code_sha256'].items())
    output.update(remote_preservation_files=40,remote_preservation_verified=True)
(HERE/'verification.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(output,indent=2))
