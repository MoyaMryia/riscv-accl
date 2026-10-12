#!/usr/bin/env python3
"""Recompute collected validation claims from the request/state artifacts."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def verify(root):
    receipt = json.loads((root / 'collection-receipt.json').read_text())
    for name, expected in receipt['files_sha256'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ValueError('collected artifact hash changed: ' + name)
    run = json.loads((root / 'run.json').read_text())
    for name, expected in run['code_sha256'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ValueError('staged code changed: ' + name)
    spec = importlib.util.spec_from_file_location('validation_verify', root / 'k1-validation.py')
    validation = importlib.util.module_from_spec(spec); spec.loader.exec_module(validation)
    summary = json.loads((root / 'summary.json').read_text()); checks = {}
    for model in ('2B', '4B'):
        stages = summary['stages']
        name = model + '-8k-routing'
        if stages.get(name, {}).get('status') == 'pass':
            rows = []; labels = []
            for i, mode in enumerate((0, 3, 3, 0)):
                label = f'{model}-8192-q{mode}-pass{i+1}'; labels.append(label)
                rows.extend(json.loads(line) for line in (root / (label + '.jsonl')).read_text().splitlines())
                validation.module('k1-gemm-routing').check_activation((root / (label + '.server.log')).read_text(), mode, ('prefill', 'single'))
            if validation.routing_gate(rows, labels) != stages[name]: raise ValueError('routing summary differs')
            checks[name] = 'recomputed'
        name = model + '-mtp512'
        if stages.get(name, {}).get('status') in ('pass', 'mismatch'):
            records = {}
            for arm in ('direct', 'checkpoint', 'rs'):
                rows = [json.loads(line) for line in (root / (model + '-mtp512-' + arm + '.jsonl')).read_text().splitlines()]
                validation.fast.check_model_records(rows, [model + '-mtp512-' + arm], 128, output_tokens=512)
                records[arm] = next(r['results'][0] for r in rows if r['kind'] == 'measurement')
            for arm in ('checkpoint', 'rs'):
                difference = validation.first_difference(records['direct']['token_ids'], records[arm]['token_ids'])
                if difference != stages[name]['results'][arm]['first_difference']: raise ValueError('MTP summary differs')
            checks[name] = 'recomputed'
        name = model + '-state'
        if stages.get(name, {}).get('status') in ('pass', 'mismatch', 'incomplete coverage'):
            records = json.loads((root / (name + '.json')).read_text())
            counts = {s: sum(r['status'] == s for r in records) for s in ('pass', 'mismatch', 'unsupported')}
            if counts != stages[name]['counts'] or len(records) != stages[name]['records']:
                raise ValueError('state summary differs')
            checks[name] = 'recomputed; unsupported excluded from passes'
        name = model + '-forced'
        if stages.get(name, {}).get('status') in ('pass', 'failed control'):
            direct = [json.loads(line) for line in (root / (name + '-direct.jsonl')).read_text().splitlines()]
            if len(direct) != 512: raise ValueError('incomplete forced direct trajectory')
            for k in (1, 3):
                records = [json.loads(line) for line in (root / (name + f'-k{k}.jsonl')).read_text().splitlines()]
                if len(records) != 512 or [r['i'] for r in records] != list(range(512)):
                    raise ValueError('incomplete forced replay')
                flips = [r['i'] for r in records if not r['match']]
                shifts = [abs(r['v_at_d' + str(i)] - r['d' + str(i)]) for r in records for i in (1, 2)]
                expected = stages[name]['replays'][str(k)]
                if (len(flips), flips[0] if flips else None, max(shifts)) != (expected['flips'], expected['first_flip'], expected['max_top2_shift']):
                    raise ValueError('forced trajectory summary differs')
            checks[name] = 'recomputed; M>1 shifts remain diagnostic'
        name = model + '-answers'
        if stages.get(name, {}).get('status') == 'pass':
            pairs = json.loads((root / (model + '-answers.json')).read_text())
            cases = json.loads((root / (model + '-quality-cases.json')).read_text())['cases']
            document = (root / (model + '-quality-document.txt')).read_text()
            digest = hashlib.sha256(document.encode()).hexdigest()
            for case in cases:
                for arm in ('0', '3'):
                    r = pairs[case['case_id']][arm]
                    if r['request']['cache_prompt'] or not validation.complete_answer(r, r['prompt_tokens']):
                        raise ValueError('incomplete or cached quality answer')
                    if r['document_sha256'] != digest or document not in r['request']['messages'][-1]['content']:
                        raise ValueError('full quality document changed')
                    hits = validation.quality.fact_check(case, r['answer'])['required_fact_hits']
                    if hits != r['facts']['required_fact_hits']: raise ValueError('fact summary differs')
                    if arm == '3' and (not all(hits) or not all('[' + c + ']' in r['answer'] for c in case['citations'])):
                        raise ValueError('candidate answer lacks required facts/citations')
            checks[name] = 'full input, complete cold answers and facts rechecked'
    name = '4B-32k-feasibility'
    if summary['stages'].get(name, {}).get('status') == 'pass':
        label = '4B-32768-q3-feasibility'
        rows = [json.loads(line) for line in (root / (label + '.jsonl')).read_text().splitlines()]
        validation.fast.check_model_records(rows, [label], 32768, output_tokens=64)
        config = next(r for r in rows if r['kind'] == 'config')
        if not config.get('no_context_shift') or config['ctx_size'] < 32768 + 64:
            raise ValueError('32k overflow protection missing')
        resources = json.loads((root / '32k-resources.json').read_text())
        if resources['low_memory_abort'] or any(r['swap_used_kib'] for r in resources['samples']):
            raise ValueError('32k resource gate not cleared')
        checks[name] = 'actual counts, completion and resources rechecked'
    return {'artifact_hashes': len(receipt['files_sha256']), 'checks': checks,
            'unverified_stages': {k: v['status'] for k, v in summary['stages'].items() if k not in checks}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('root', type=Path)
    print(json.dumps(verify(parser.parse_args().root.resolve()), indent=2))
