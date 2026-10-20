#!/usr/bin/env python3
"""在独立目录中向已有实验服务追加诊断请求。"""
import argparse
import json
import os
from pathlib import Path
import re
import signal
import sys
import urllib.request

import diagnostic as base
import trace_cases
import batch_controller
import isolated_trace


class LiveProcess:
    def __init__(self, pid):
        if type(pid) is not int or pid <= 0:
            raise ValueError('service PID is invalid')
        self.pid = pid
        self.start = self._stat()[19]

    def _stat(self):
        return Path(f'/proc/{self.pid}/stat').read_text().rpartition(')')[2].split()

    def poll(self):
        try:
            status = self._stat()
        except FileNotFoundError:
            return 1
        return 1 if status[0] == 'Z' or status[19] != self.start else None


def input_paths(args):
    here = Path(__file__).parent
    paths = {name: here / (name + '.py') for name in
        ('diagnostic', 'trace_cases', 'head_ablation', 'head_probe', 'general_suite',
         'model_head_check', 'router_e2e', 'router_cases', 'discovery_materials',
         'batch_controller', 'isolated_trace', 'attempt_worker', 'repetition_guard')}
    paths.update(attach=Path(__file__), cases=args.cases, diagnostic_plan=args.diagnostic_plan,
                 legacy_request=args.legacy_request, assessment=args.cases_module,
                 chat=args.chat, quality=args.quality, policy=args.service / 'router/policy.py',
                 request_lease=args.service / 'router/request_lease.py')
    return paths


def read_cases(path, policy, assessor):
    cases = json.loads(path.read_text())
    if not isinstance(cases, list) or not cases:
        raise ValueError('diagnostic cases must be a nonempty list')
    ids, texts, categories = set(), set(), set()
    for case in cases:
        if not isinstance(case, dict) or case.get('category') not in trace_cases.CATEGORIES:
            raise ValueError('diagnostic case category is invalid')
        name = case.get('case_id')
        if not isinstance(name, str) or not re.fullmatch(r'[a-z][a-z0-9_]*', name) or name in ids:
            raise ValueError('diagnostic case identifier is invalid or repeated')
        text = re.sub(r'\s+', ' ', policy.request_text(case)).strip().casefold()
        if text in texts:
            raise ValueError('diagnostic request text is repeated')
        for field in ('required_facts', 'required_citations'):
            if not isinstance(case.get(field), list) or not all(isinstance(v, str) for v in case[field]):
                raise ValueError('diagnostic reference is invalid')
        if case['category'] == 'code' and case.get('code_task') not in assessor.FAMILIES:
            raise ValueError('diagnostic code family is invalid')
        ids.add(name)
        texts.add(text)
        categories.add(case['category'])
    if categories != set(trace_cases.CATEGORIES):
        raise ValueError('diagnostic categories are incomplete')
    return cases


def verify_completion(progress, protocol):
    expected = protocol['planned']
    if type(expected) is not int or expected <= 0 or any(type(progress.get(k)) is not int for k in ('completed', 'planned')):
        raise ValueError('previous diagnostic counts are invalid')
    if progress['completed'] != expected or progress['planned'] != expected:
        raise RuntimeError('previous diagnostics are incomplete or counts differ')
    return expected


def attach(service):
    result = service / 'result'
    ready = json.loads((result / 'ready.json').read_text())
    expected = {*trace_cases.ARMS, 'encoder', 'gateway'}
    if ready.get('trace') is not True or not isinstance(ready.get('processes'), dict) or set(ready['processes']) != expected:
        raise ValueError('service roles or trace mode differ')
    controller = LiveProcess(ready['pid'])
    if controller.poll() is not None:
        raise RuntimeError('service controller is not alive')
    os.stat(f'/proc/{controller.pid}/fd/9')
    progress = json.loads((result / 'diagnostics/progress.json').read_text())
    protocol = json.loads((result / 'diagnostics/protocol.json').read_text())
    verify_completion(progress, protocol)
    identity = json.loads((result / 'identity.json').read_text())
    if identity['server']['sha256'] != base.SERVER_SHA:
        raise ValueError('service server identity differs from r3')
    processes, urls, observed = {}, {}, {}
    for name, pid in ready['processes'].items():
        process = LiveProcess(pid)
        folder = result / 'gateway' if name == 'gateway' else result / 'backends' / name
        launch = json.loads((folder / 'launch.json').read_text())
        argv = Path(f'/proc/{pid}/cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
        if argv != launch['argv'] or process.poll() is not None:
            raise ValueError('live process command differs: ' + name)
        if name in trace_cases.ARMS:
            env = dict(v.split('=', 1) for v in Path(f'/proc/{pid}/environ').read_text().split('\0') if v)
            required = {'LLAMA_TRACE': '1', 'SPINE_SPEC_RS': '0',
                        'SPINE_SPEC_LOWACC': '1' if name == 'lowacc' else '0'}
            if any(env.get(key) != value for key, value in required.items()):
                raise ValueError('live decoder environment differs: ' + name)
            if argv[argv.index('--host') + 1] != '127.0.0.1':
                raise ValueError('use loopback decoder addresses')
            urls[name] = 'http://127.0.0.1:' + argv[argv.index('--port') + 1]
            with urllib.request.urlopen(urls[name] + '/props', timeout=30) as response:
                props = json.load(response)
            if props['total_slots'] != 1 or props['default_generation_settings']['n_ctx'] != base.CONTEXT:
                raise ValueError('live decoder context differs')
        if name == 'gateway':
            if argv[argv.index('--request-lock') + 1] != str(result / 'request.lock'):
                raise ValueError('gateway request lock differs')
        processes[name] = process
        observed[name] = {'pid': pid, 'start': process.start, 'argv': argv}
    processes['controller'] = controller
    return processes, urls, {'service': str(service), 'ready': ready, 'identity': identity,
                             'processes': observed}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'service', 'cases', 'cases-module', 'chat', 'quality',
                 'diagnostic-plan', 'legacy-request', 'tool-receipt'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--max-tokens', type=int, default=base.MAX_TOKENS)
    args = parser.parse_args(argv)
    if not os.environ.get('TMUX') or not 0 < args.max_tokens < base.CONTEXT:
        parser.error('use tmux and an output budget below the context size')
    signal.signal(signal.SIGTERM, base.term_handler)
    args.output.mkdir(parents=True)
    paths = input_paths(args)
    hashes = {key: base.sha256(path) for key, path in paths.items()}
    if hashes != json.loads(args.tool_receipt.read_text()):
        raise ValueError('attachment tool or dataset hashes differ')
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
    policy = base.load_module('attach_policy', paths['policy'])
    assessor = base.load_module('attach_assessor', args.cases_module)
    cases = read_cases(args.cases, policy, assessor)
    args.trace_plan = trace_cases.validate_plan(json.loads(args.diagnostic_plan.read_text()))
    args.legacy_data = json.loads(args.legacy_request.read_text())
    policy.request_text(args.legacy_data)
    args.lease = base.load_module('attach_lease', paths['request_lease'])
    args.request_lock = args.service / 'result/request.lock'
    with args.lease.acquire(args.request_lock):
        processes, urls, identity = attach(args.service)
        trace_cases.verify_prefix_rows(Path(identity['identity']['models']['2B']['path']), args.trace_plan['prefix_rows'])
    identity['attachment_tools'] = hashes
    base.save(args.output / 'attachment.json', identity)
    summary = isolated_trace.run(args, cases, processes, urls, backend_root=args.service / 'result/backends')
    return batch_controller.exit_code(summary)


if __name__ == '__main__':
    sys.exit(main())
