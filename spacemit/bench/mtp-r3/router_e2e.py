#!/usr/bin/env python3
"""在两个常驻 r3 后端上对照直接请求和自动路由。"""
import argparse
from collections import Counter
from contextlib import ExitStack
from fractions import Fraction
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import time
import urllib.request

import diagnostic as base

CATEGORIES = ('code', 'chinese', 'qa', 'long_document')
CASES_PER_CATEGORY = 3
ARMS = ('baseline', 'routed')
CONTROL_CANDIDATE = 'manual_prefix'
ACCEPTANCE = {'max_category_slowdown_pct': 3.0}
REVIEW_ACCEPTANCE = {'max_mean_quality_loss': 0.25, 'new_fact_citation_code_errors': 0}


def read_cases(path, policy, per_category=CASES_PER_CATEGORY, code_tasks=None, allowed=None):
    """读入固定套件或发现集；per_category 为 None 时只要求每个类别非空。"""
    cases = json.loads(path.read_text())
    counts = Counter(c.get('category') for c in cases if isinstance(c, dict))
    if not isinstance(cases, list) or not cases or set(counts) - set(CATEGORIES):
        raise ValueError('case categories or counts differ')
    if per_category is None:
        expected = set(allowed) if allowed is not None else set(CATEGORIES)
        if set(counts) != expected:
            raise ValueError('case categories or counts differ')
    elif counts != Counter({c: per_category for c in CATEGORIES}):
        raise ValueError('case categories or counts differ')
    ids = set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get('case_id'), str) or not re.fullmatch(r'[a-z][a-z0-9_]*', case['case_id']) or case['case_id'] in ids:
            raise ValueError('case identifier is invalid or repeated')
        ids.add(case['case_id'])
        policy.request_text(case)
        for field in ('required_facts', 'required_citations'):
            if not isinstance(case.get(field), list) or not all(isinstance(value, str) for value in case[field]):
                raise ValueError('case reference is invalid: ' + field)
        if case['category'] == 'code':
            task = case.get('code_task')
            if (task not in code_tasks) if code_tasks is not None else (task != case['case_id']):
                raise ValueError('code task differs from the case identifier')
    return cases


def stop_process(process, output, expected):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    base.save(output / 'exit.json', {'returncode': process.returncode})
    if process.returncode not in expected:
        raise RuntimeError('managed process exited abnormally: ' + str(process.returncode))


def start_backend(stack, args, libraries, route, model_path, port, *, trace=False, lowacc=False):
    folder = args.output / 'backends' / route
    folder.mkdir(parents=True)
    extra = [] if route == 'direct' else ['--spec-type', 'draft-mtp', '--spec-draft-n-max',
        str(base.DRAFT_MAX), '--spec-draft-p-min', '0.0']
    argv = list(map(str, [args.server, '-m', model_path, '--alias', 'local', '--host',
        '127.0.0.1', '--port', port, '--log-verbosity', base.LOG_VERBOSITY, *extra]))
    environment = base.clean_environment(os.environ, libraries, lowacc=lowacc, trace=trace)
    base.save(folder / 'launch.json', {'argv': argv, 'environment': environment})
    log = stack.enter_context((folder / 'server.log').open('w'))
    process = subprocess.Popen(argv, env=environment, stdout=log, stderr=subprocess.STDOUT)
    stack.callback(stop_process, process, folder, (0,))
    url = f'http://127.0.0.1:{port}'
    begin = time.monotonic()
    base.wait_ready(process, url)
    actual = dict(part.split('=', 1) for part in Path(f'/proc/{process.pid}/environ').read_text().split('\0') if part)
    if any(actual.get(key) != value for key, value in environment.items()):
        raise ValueError('native environment differs')
    text = (folder / 'server.log').read_text()
    effective = args.effective_module.verify(text, base.CONFIG)
    speculation = base.verify_speculation(text, 'direct' if route == 'direct' else 'mtp')
    with urllib.request.urlopen(url + '/props', timeout=30) as response:
        properties = json.load(response)
    if properties['total_slots'] != 1 or properties['default_generation_settings']['n_ctx'] != base.CONTEXT:
        raise ValueError('native slot count or context differs')
    base.save(folder / 'properties.json', {'effective_defaults': effective,
        'speculation': speculation, 'properties': properties, 'startup_s': time.monotonic() - begin})
    return process, url


def start_encoder(stack, args, libraries, head, port):
    folder = args.output / 'backends' / 'encoder'
    folder.mkdir(parents=True)
    command = [str(args.server), '-m', str(args.bert_model), '--host', '127.0.0.1', '--port', str(port),
        '--alias', 'router-bert', '--embedding', '--pooling', 'cls', '--embd-normalize', '-1',
        '--ctx-size', str(head['max_tokens']), '--batch-size', str(head['max_tokens']),
        '--ubatch-size', str(head['max_tokens']), '--parallel', '1', '--threads', str(base.CONFIG['threads']),
        '--threads-batch', str(base.CONFIG['threads']), '--flash-attn', 'off', '--log-verbosity', str(base.LOG_VERBOSITY)]
    environment = base.clean_environment(os.environ, libraries, lowacc=False)
    base.save(folder / 'launch.json', {'argv': command, 'environment': environment})
    log = stack.enter_context((folder / 'server.log').open('w'))
    process = subprocess.Popen(command, env=environment, stdout=log, stderr=subprocess.STDOUT)
    stack.callback(stop_process, process, folder, (0,))
    url = f'http://127.0.0.1:{port}'
    begin = time.monotonic()
    base.wait_ready(process, url)
    observed = dict(part.split('=', 1) for part in Path(f'/proc/{process.pid}/environ').read_text().split('\0') if part)
    if any(observed.get(key) != value for key, value in environment.items()):
        raise ValueError('encoder environment differs')
    with urllib.request.urlopen(url + '/props', timeout=30) as response:
        properties = json.load(response)
    if properties['total_slots'] != 1 or properties['default_generation_settings']['n_ctx'] != head['max_tokens']:
        raise ValueError('encoder context or slot count differs')
    base.save(folder / 'properties.json', {'properties': properties, 'startup_s': time.monotonic() - begin})
    return process, url


def resources(processes):
    result = {}
    for name, process in processes.items():
        rollup = Path(f'/proc/{process.pid}/smaps_rollup').read_text()
        fields = dict((name, int(value)) for name, value in re.findall(r'^(\w+):\s+(\d+) kB$', rollup, re.M))
        result[name] = {'pid': process.pid, **base.resource_snapshot(process.pid),
            'smaps_kib': {key: fields[key] for key in ('Rss', 'Pss', 'Private_Clean', 'Private_Dirty')}}
    return result


def response_route(response, arm, classifier_name='ngram'):
    if arm == 'baseline':
        return 'direct', 0.0
    headers = response['http_headers']
    if headers.get('x-classifier') != classifier_name:
        raise ValueError('live classifier differs')
    route = headers.get('x-decode-route')
    classify_ms = float(headers['x-classify-ms'])
    if arm == CONTROL_CANDIDATE:
        if route != 'prefix' or headers.get('x-route-reason') != 'manual' or classify_ms != 0:
            raise ValueError('manual route headers differ')
    else:
        if route not in ('direct', 'prefix') or headers.get('x-route-reason') != 'class_map':
            raise ValueError('live route headers differ')
        base.finite_positive(classify_ms, 'classify_ms')
    return route, classify_ms


def run_matrix(args, cases, chat, assessor, direct_url, gateway_url, processes, candidate=ARMS[1]):
    records = []
    arms = (ARMS[0], candidate)
    for index, case in enumerate(cases):
        folder = args.output / 'cases' / case['case_id']
        folder.mkdir(parents=True)
        payload = chat.request_body(case['messages'], 'local', 0, args.max_tokens)
        payload.update(cache_prompt=False, stream_options={'include_usage': True}, verbose=True)
        base.save(folder / 'request.json', payload)
        prompt_count = chat.count_prompt_tokens(direct_url, payload, base.DEADLINE_S)
        if prompt_count + args.max_tokens > base.CONTEXT:
            raise ValueError('complete input and output do not fit: ' + case['case_id'])
        order = arms if index % 2 == 0 else tuple(reversed(arms))
        for arm in order:
            for process in processes.values():
                if process.poll() is not None:
                    raise RuntimeError('a resident process exited during the batch')
            before = resources(processes)
            old_handler = signal.signal(signal.SIGALRM, base.deadline_handler)
            signal.alarm(base.DEADLINE_S)
            try:
                options = {'headers': {'X-Decode-Mode': 'prefix'}} if arm == CONTROL_CANDIDATE else {}
                response = chat.complete(direct_url if arm == 'baseline' else gateway_url,
                                         payload, base.DEADLINE_S, display=False, **options)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            arm_folder = folder / arm
            arm_folder.mkdir()
            base.save(arm_folder / 'answer.json', response)
            (arm_folder / 'answer.txt').write_text(response['answer'])
            route, classify_ms = response_route(response, arm, args.classifier_name)
            metrics = base.validate_response(response, prompt_count, 'mtp' if route == 'prefix' else 'direct',
                                             max_tokens=args.max_tokens)
            quality = assessor.assess(case, response['answer'], args.quality)
            record = {'case_id': case['case_id'], 'category': case['category'], 'arm': arm,
                'route': route, 'classify_ms': classify_ms, 'response': response,
                'metrics': metrics, 'quality': quality, 'resources_before': before,
                'resources_after': resources(processes)}
            base.save(arm_folder / 'result.json', record)
            records.append(record)
            base.save(args.output / 'progress.json', {'completed': len(records),
                'planned': len(cases) * len(arms), 'case_id': case['case_id'], 'arm': arm})
            print(json.dumps({'completed': len(records), 'case': case['case_id'], 'arm': arm,
                'route': route, 'wall_s': response['wall_s'], 'quality': quality['passed']}), flush=True)
    return records


def summarize(cases, records, candidate=ARMS[1]):
    arms = (ARMS[0], candidate)
    indexed = {(row['case_id'], row['arm']): row for row in records}
    if len(indexed) != len(records) or set(indexed) != {(case['case_id'], arm) for case in cases for arm in arms}:
        raise ValueError('paired result matrix is incomplete or repeated')
    result = {'categories': {}, 'candidate': candidate,
        'routes': dict(Counter(row['route'] for row in records if row['arm'] == candidate))}
    for category in CATEGORIES:
        selected = [case for case in cases if case['category'] == category]
        if not selected:
            continue
        pairs = [(indexed[(case['case_id'], 'baseline')], indexed[(case['case_id'], candidate)]) for case in selected]
        baseline = sum(d['response']['wall_s'] for d, r in pairs)
        routed = sum(r['response']['wall_s'] for d, r in pairs)
        paired_slowdown = sum(100 * (Fraction(str(r['response']['wall_s'])) /
            Fraction(str(d['response']['wall_s'])) - 1) for d, r in pairs) / len(pairs)
        result['categories'][category] = {'pairs': len(pairs), 'baseline_total_s': baseline,
            'routed_total_s': routed, 'total_wall_reduction_pct': 100 * (1 - routed / baseline),
            'paired_slowdown_mean_pct': float(paired_slowdown),
            'speed_gate': paired_slowdown <= Fraction(str(ACCEPTANCE['max_category_slowdown_pct']))}
    baseline = sum(row['baseline_total_s'] for row in result['categories'].values())
    routed = sum(row['routed_total_s'] for row in result['categories'].values())
    new_code_failures = [case['case_id'] for case in cases if case['category'] == 'code'
        and indexed[(case['case_id'], 'baseline')]['quality']['passed'] is True
        and indexed[(case['case_id'], candidate)]['quality']['passed'] is False]
    quality_gate = False if new_code_failures else None
    result.update(baseline_total_s=baseline, routed_total_s=routed,
        wall_reduction_pct=100 * (1 - routed / baseline),
        category_speed_gate=all(row['speed_gate'] for row in result['categories'].values()),
        code_checks={arm: [row['quality'] for row in records if row['arm'] == arm and row['category'] == 'code'] for arm in arms},
        new_code_failures=new_code_failures, noncode_review=None, quality_gate=quality_gate)
    result['adoption_gate'] = False if not result['category_speed_gate'] or quality_gate is False else None
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'server', 'models', 'spert', 'tcm', 'manifest', 'build-receipt',
                 'chat', 'quality', 'effective', 'tool-receipt', 'cases', 'cases-module', 'router'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--base-port', type=int, default=18110)
    parser.add_argument('--code-controls', action='store_true')
    parser.add_argument('--max-tokens', type=int, default=base.MAX_TOKENS)
    parser.add_argument('--bert-model', type=Path)
    parser.add_argument('--bert-head', type=Path)
    parser.add_argument('--serve', action='store_true')
    parser.add_argument('--diagnostic-plan', type=Path)
    parser.add_argument('--legacy-request', type=Path)
    args = parser.parse_args(argv)
    if bool(args.diagnostic_plan) != bool(args.legacy_request) or (args.diagnostic_plan and not args.serve):
        parser.error('diagnostics require --serve, --diagnostic-plan and --legacy-request')
    trace = args.diagnostic_plan is not None
    if args.serve and args.code_controls:
        parser.error('--serve and --code-controls are separate modes')
    if trace and not args.bert_model:
        parser.error('the diagnostic service requires the BERT encoder and head')
    if bool(args.bert_model) != bool(args.bert_head):
        parser.error('provide both BERT encoder and head')
    args.classifier_name = 'bert' if args.bert_model else 'ngram'
    last_port = args.base_port + (4 if trace else 3 if args.bert_model else 2)
    if not os.environ.get('TMUX') or not 0 < args.base_port <= last_port < 65536 or not 0 < args.max_tokens < base.CONTEXT:
        parser.error('use tmux, valid consecutive ports, and an output budget below the context size')
    signal.signal(signal.SIGTERM, base.term_handler)
    args.port = args.base_port + 2
    backend_ports = [args.base_port, args.base_port + 1]
    if args.bert_model:
        backend_ports.append(args.base_port + 3)
    if trace:
        backend_ports.append(args.base_port + 4)
    for port in backend_ports:
        with socket.socket() as sock:
            if sock.connect_ex(('127.0.0.1', port)) == 0:
                raise RuntimeError('a backend port is occupied')
    args.output.mkdir(parents=True, exist_ok=False)
    extras = tool_extras(args, trace)
    models, identities = base.verify_inputs(args, model_names=('2B',), extra_tools=extras)
    base.save(args.output / 'identity.json', identities)
    policy = base.load_module('bench_router_policy', args.router / 'policy.py')
    assessor = base.load_module('bench_router_cases', args.cases_module)
    trace_worker = None
    allowed = None
    if trace:
        trace_worker = base.load_module('live_trace_cases', extras['trace_cases'])
        args.trace_plan = trace_worker.validate_plan(json.loads(args.diagnostic_plan.read_text()))
        allowed = {stage['category'] for stage in args.trace_plan['stages']}
        trace_worker.verify_prefix_rows(models['2B'], args.trace_plan['prefix_rows'])
    cases = read_cases(args.cases, policy, None if trace else CASES_PER_CATEGORY,
                       assessor.FAMILIES if trace else None, allowed)
    if trace:
        args.lease = base.load_module('live_request_lease', args.router / 'request_lease.py')
        args.request_lock = args.output / 'request.lock'
        args.legacy_data = json.loads(args.legacy_request.read_text())
        policy.request_text(args.legacy_data)
    candidate = CONTROL_CANDIDATE if args.code_controls else ARMS[1]
    if args.code_controls:
        cases = [case for case in cases if case['category'] == 'code']
    chat = base.load_module('bench_router_chat', args.chat)
    args.effective_module = base.load_module('bench_router_effective', args.effective)
    bert_head = None
    if args.bert_model:
        sys.path.insert(0, str(args.router))
        import bert_runtime
        bert_head = bert_runtime.load_head(args.bert_head)
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
    base.save(args.output / 'protocol.json', {'categories': [c for c in CATEGORIES if any(case['category'] == c for case in cases)],
        'case_ids': [case['case_id'] for case in cases],
        'cases_per_category': None if trace else CASES_PER_CATEGORY,
        'arms': [ARMS[0], candidate], 'acceptance': ACCEPTANCE,
        'review_acceptance': REVIEW_ACCEPTANCE, 'review_state': 'pending_blind_review', 'native_config': base.CONFIG, 'context': base.CONTEXT,
        'max_tokens': args.max_tokens, 'draft_max': base.DRAFT_MAX, 'score_guard': False,
        'request_mode': 'prefix' if args.code_controls else 'auto',
        'classification': not args.code_controls, 'classifier': args.classifier_name,
        'dataset_role': 'diagnostic_regression' if trace else 'fixed_suite',
        'serve': args.serve, 'trace': trace, 'diagnostic_plan': args.trace_plan if trace else None,
        'encoder_port': args.base_port + 3 if args.bert_model else None,
        'rs_snapshots': 0, 'lowacc': False, 'cache_prompt': False,
        'request_deadline_s': base.DEADLINE_S, 'backend_ports': [args.base_port, args.base_port + 1],
        'proxy_port': args.port, 'order': 'alternate baseline-first and routed-first by case index',
        'baseline_residency': 'all configured native backends remain resident', 'client': 'board loopback',
        'timing': 'HTTP open through framed SSE EOF; classification and relay included; server load excluded'})
    libraries = f'{args.server.parent}:{args.tcm}:{args.spert / "lib"}'
    processes = {}
    with ExitStack() as stack:
        processes['direct'], direct_url = start_backend(stack, args, libraries, 'direct', models['2B'], args.base_port,
                                                       trace=trace)
        base.save(args.output / 'direct_only_resources.json', resources(processes))
        processes['prefix'], prefix_url = start_backend(stack, args, libraries, 'prefix', models['2B'], args.base_port + 1,
                                                       trace=trace)
        lowacc_url = None
        if trace:
            processes['lowacc'], lowacc_url = start_backend(stack, args, libraries, 'lowacc', models['2B'],
                                                           args.base_port + 4, trace=True, lowacc=True)
        classifier_options = ['--model', str(args.router / 'model.json.gz')]
        if args.bert_model:
            base.save(args.output / 'two_decoder_resources.json', resources(processes))
            processes['encoder'], encoder_url = start_encoder(stack, args, libraries, bert_head, args.base_port + 3)
            classifier_options = ['--bert-head', str(args.bert_head), '--bert-url', encoder_url]
        folder = args.output / 'gateway'
        folder.mkdir()
        command = [sys.executable, '-u', str(args.router / 'proxy.py'), *classifier_options,
            '--direct', direct_url, '--prefix', prefix_url, '--port', str(args.port)]
        if trace:
            command += ['--request-lock', str(args.request_lock)]
        base.save(folder / 'launch.json', {'argv': command})
        log = stack.enter_context((folder / 'proxy.log').open('w'))
        processes['gateway'] = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        stack.callback(stop_process, processes['gateway'], folder, (0, -signal.SIGTERM))
        gateway_url = f'http://127.0.0.1:{args.port}'
        base.wait_ready(processes['gateway'], gateway_url)
        with urllib.request.urlopen(gateway_url + '/health', timeout=30) as response:
            health = json.load(response)
        expected_health = {'gateway': 'ready', 'routes': ['direct', 'prefix'], 'score_guard': False}
        if args.bert_model:
            expected_health['classifier'] = 'bert'
        if health != expected_health:
            raise ValueError('gateway configuration differs')
        base.save(folder / 'health.json', health)
        base.save(args.output / 'resident_resources.json', resources(processes))
        if args.serve:
            base.save(args.output / 'ready.json', {'url': gateway_url, 'pid': os.getpid(), 'trace': trace,
                'processes': {name: process.pid for name, process in processes.items()}})
            print('EXPERIMENTAL_SERVICE_READY', gateway_url, flush=True)
            if trace:
                executor = base.load_module('live_isolated_trace', extras['isolated_trace'])
                controller = executor.run(args, cases, processes,
                                          {'direct': direct_url, 'prefix': prefix_url, 'lowacc': lowacc_url},
                                          backend_root=args.output / 'backends')
                status = executor.batch_status(controller)
                base.save(args.output / 'batch-status.json', status)
                if status['exit_code']:
                    print('DIAGNOSTICS_BATCH_FAILED', json.dumps(status['counts']), flush=True)
                    return status['exit_code']
                print('DIAGNOSTICS_COMPLETE_SERVICE_REMAINS_READY', flush=True)
            while True:
                if any(process.poll() is not None for process in processes.values()):
                    raise RuntimeError('an experimental service process exited')
                time.sleep(1)
        records = run_matrix(args, cases, chat, assessor, direct_url, gateway_url, processes, candidate)
        result = summarize(cases, records, candidate)
        base.save(args.output / 'summary.json', result)
    return 2 if any(row['quality']['passed'] is False for row in records) else 0


def tool_extras(args, trace):
    """返回工具集映射。键名必须与工具收据相同，并避免同名不同文件。"""
    extras = {'router_e2e': Path(__file__), 'cases_module': args.cases_module, 'cases': args.cases}
    if trace:
        extras.update({name: Path(__file__).with_name(name + '.py') for name in
                       ('trace_cases', 'head_probe', 'head_ablation', 'general_suite', 'model_head_check',
                        'batch_controller', 'isolated_trace', 'attempt_worker', 'repetition_guard',
                        'discovery_cases', 'discovery_materials')})
        extras.update(diagnostic_plan=args.diagnostic_plan, legacy_request=args.legacy_request)
    router_files = ['classifier.py', 'policy.py', 'proxy.py']
    if trace:
        router_files.append('request_lease.py')
    if args.bert_model:
        router_files += ['bert_common.py', 'bert_runtime.py']
        extras.update(bert_model=args.bert_model, bert_head=args.bert_head)
    else:
        router_files.append('model.json.gz')
    extras.update({'router_' + name: args.router / name for name in router_files})
    return extras


if __name__ == '__main__':
    sys.exit(main())
