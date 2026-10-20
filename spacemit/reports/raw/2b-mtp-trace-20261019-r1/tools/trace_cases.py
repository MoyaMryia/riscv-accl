#!/usr/bin/env python3
"""从常驻后端采集原始提案、恢复重放和完整回答。"""
import json
from pathlib import Path
import re
import signal
import statistics
import time
import urllib.request

import diagnostic as base
import head_ablation
import head_probe
import model_head_check
from router_e2e import CATEGORIES

ARMS = ('direct', 'prefix', 'lowacc')
LOG_DRAIN_S = 2.0
FALLBACK = r'disable speculation after \d+ accepted in \d+ verification steps'
STAMP = re.compile(r'(\d+)\.(\d{2})\.(\d{3})\.(\d{3})')
STATS = re.compile(r'draft-mtp:[^\n]*dur\(b,g,a\) = ([\d.]+), ([\d.]+), ([\d.]+) ms')


def validate_plan(plan):
    if not isinstance(plan, dict) or type(plan.get('prefix_rows')) is not int or plan['prefix_rows'] <= 0:
        raise ValueError('prefix_rows must be a positive integer')
    stages = plan.get('stages')
    if not isinstance(stages, list) or len(stages) != len(CATEGORIES):
        raise ValueError('plan must contain four stages')
    seen = set()
    for stage in stages:
        if not isinstance(stage, dict) or stage.get('category') not in CATEGORIES or stage['category'] in seen:
            raise ValueError('stage category is invalid or repeated')
        if type(stage.get('repeats')) is not int or stage['repeats'] <= 0:
            raise ValueError('stage repeats must be a positive integer')
        seen.add(stage['category'])
    return plan


def verify_prefix_rows(path, expected):
    with path.open('rb') as stream:
        model = model_head_check._read_model(stream)
    head = next(t for t in model['tensors'] if t[0].endswith(model_head_check._HEAD_SUFFIX))
    if head[1][1] != expected:
        raise ValueError('diagnostic prefix rows differ from the actual model')


def schedule(plan, cases, legacy):
    queue = []
    for stage in plan['stages']:
        pool = [c for c in cases if c['category'] == stage['category']]
        if stage['category'] == 'code':
            pool = [legacy, *pool]
        for repeat in range(1, stage['repeats'] + 1):
            for index, case in enumerate(pool):
                offset = (repeat + index - 1) % len(ARMS)
                queue.extend((stage['category'], repeat, case, arm) for arm in ARMS[offset:] + ARMS[:offset])
    return queue


def cumulative_stats(text, *, required=False):
    rows = STATS.findall(text)
    if not rows:
        if required:
            raise ValueError('native draft timing is absent')
        return (0.0, 0.0, 0.0)
    return tuple(map(float, rows[-1]))


def analyze_trace(fragment, metrics, arm):
    events = head_probe.trace_events(fragment)
    if arm == 'direct':
        if events:
            raise ValueError('direct backend emitted draft events')
        return None
    task_ids = set()
    for event in events:
        match = re.search(r'\btask\s+(\d+)\s*\|', event['log_line'])
        if not match:
            raise ValueError('draft event has no task identifier')
        task_ids.add(match[1])
    if len(task_ids) != 1:
        raise ValueError('trace must contain exactly one native task')
    counts = head_ablation.verify_trace(events, metrics)
    counts['original_restore_fraction'] = counts['original_restores'] / counts['original_steps']
    histogram = {}
    gaps = []
    pending = False
    prior_time = None
    for event in events:
        stamp = STAMP.search(event['log_line'])
        if not stamp:
            raise ValueError('draft event timestamp is absent')
        minute, second, milli, micro = map(int, stamp.groups())
        now = (minute * 60 + second) * 1000 + milli + micro / 1000
        if pending:
            gap = now - prior_time
            if gap < 0:
                raise ValueError('native event timestamps go backwards')
            gaps.append(gap)
        else:
            key = str(event['accepted'])
            histogram[key] = histogram.get(key, 0) + 1
        pending = event['restore_checkpoint']
        prior_time = now
    counts.update(accept_histogram=histogram, replay_gap_ms=gaps, events=events)
    return counts


def log_fragment(path, offset, arm):
    end = time.monotonic() + LOG_DRAIN_S
    while True:
        with path.open('rb') as stream:
            stream.seek(offset)
            fragment = stream.read().decode('utf-8')
        if 'prompt eval time' in fragment and (arm == 'direct' or STATS.search(fragment)):
            return fragment
        if time.monotonic() >= end:
            raise TimeoutError('native request log did not finish')
        time.sleep(.01)


def summarize(records):
    result = {'quality_failures': sum(r['quality']['passed'] is False for r in records), 'cases': {}}
    for case_id in dict.fromkeys(r['case_id'] for r in records):
        selected = [r for r in records if r['case_id'] == case_id]
        values = {}
        for arm in ARMS:
            rows = [r for r in selected if r['arm'] == arm]
            if not rows:
                continue
            trace = [r['verification'] for r in rows if r['verification'] is not None]
            proposed = sum(t['original_proposed'] for t in trace)
            steps = sum(t['original_steps'] for t in trace)
            values[arm] = {'samples': len(rows),
                'wall_mean_s': statistics.mean(r['response']['wall_s'] for r in rows),
                'ttft_mean_s': statistics.mean(r['response']['ttft_s'] for r in rows),
                'prefill_mean_ms': statistics.mean(r['response']['timings']['prompt_ms'] for r in rows),
                'decode_mean_ms': statistics.mean(r['response']['timings']['predicted_ms'] for r in rows),
                'original_acceptance': sum(t['original_first_accepted'] for t in trace) / proposed if proposed else None,
                'restore_fraction': sum(t['original_restores'] for t in trace) / steps if steps else None,
                'draft_mean_ms': statistics.mean(r['draft_duration_delta_ms'][1] for r in rows) if trace else None,
                'coverage_mean': statistics.mean(r['coverage']['prefix_fraction'] for r in rows),
                'fallback_events': sum(len(r['fallback_events']) for r in rows),
                'quality_failures': sum(r['quality']['passed'] is False for r in rows)}
        result['cases'][case_id] = values
    return result


def run(args, cases, chat, assessor, quality, processes, urls):
    legacy = {'case_id': 'legacy_unicode_runs', 'category': 'code', 'code_task': 'unicode_runs',
              'messages': args.legacy_data['messages'], 'required_facts': [], 'required_citations': []}
    queue = schedule(args.trace_plan, cases, legacy)
    root = args.output / 'diagnostics'
    root.mkdir()
    base.save(root / 'protocol.json', {'plan': args.trace_plan, 'planned': len(queue), 'arms': ARMS,
        'trace': True, 'client': 'native HTTP', 'classification': False,
        'timing': 'HTTP through SSE EOF; model load and analysis excluded',
        'replay_gap': 'restore log marker to next verification log marker'})
    records = []
    for stage, repeat, case, arm in queue:
        for process in processes.values():
            if process.poll() is not None:
                raise RuntimeError('a resident process exited during diagnostics')
        folder = root / stage / f'round-{repeat}' / case['case_id'] / arm
        folder.mkdir(parents=True)
        payload = chat.request_body(case['messages'], 'local', 0, args.max_tokens)
        payload.update(cache_prompt=False, stream_options={'include_usage': True}, verbose=True)
        base.save(folder / 'request.json', payload)
        with args.lease.acquire(args.request_lock):
            prompt_count = chat.count_prompt_tokens(urls['direct'], payload, base.DEADLINE_S)
            if prompt_count + args.max_tokens > base.CONTEXT:
                raise ValueError('complete input and output do not fit')
            path = args.output / 'backends' / arm / 'server.log'
            before_log = path.read_bytes()
            before_stats = cumulative_stats(before_log.decode('utf-8'))
            before = base.resource_snapshot(processes[arm].pid)
            handler = signal.signal(signal.SIGALRM, base.deadline_handler)
            signal.alarm(base.DEADLINE_S)
            try:
                response = chat.complete(urls[arm], payload, base.DEADLINE_S, display=False)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, handler)
            base.save(folder / 'answer.json', response)
            (folder / 'answer.txt').write_text(response['answer'])
            fragment = log_fragment(path, len(before_log), arm)
            (folder / 'server-fragment.log').write_text(fragment)
            metrics = base.validate_response(response, prompt_count, 'direct' if arm == 'direct' else 'mtp',
                                             max_tokens=args.max_tokens)
            verification = analyze_trace(fragment, metrics, arm)
            after_stats = cumulative_stats(fragment, required=arm != 'direct')
            delta = tuple(a - b for a, b in zip(after_stats, before_stats)) if arm != 'direct' else None
            if delta is not None and any(t < 0 for t in delta):
                raise ValueError('native cumulative draft timing went backwards')
            if case is legacy:
                checks = quality.check_code('unicode_runs', response['answer'])
                if checks.get('pass') is True and checks.get('checks') != base.CODE_CHECKS:
                    raise ValueError('legacy code check coverage differs')
                judged = {'passed': checks.get('pass') is True, 'result': checks}
            else:
                judged = assessor.assess(case, response['answer'], args.quality)
            data = json.dumps({'content': response['answer'], 'add_special': False, 'parse_special': False}).encode()
            request = urllib.request.Request(urls[arm] + '/tokenize', data=data,
                                             headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(request, timeout=30) as reply:
                coverage = head_probe.prefix_coverage(json.load(reply)['tokens'], args.trace_plan['prefix_rows'])
            record = {'case_id': case['case_id'], 'category': stage, 'round': repeat, 'arm': arm,
                'response': response, 'metrics': metrics, 'quality': judged, 'verification': verification,
                'draft_duration_delta_ms': delta, 'fallback_events': re.findall(FALLBACK, fragment),
                'coverage': coverage, 'resources_before': before,
                'resources_after': base.resource_snapshot(processes[arm].pid)}
        base.save(folder / 'result.json', record)
        records.append(record)
        base.save(root / 'progress.json', {'completed': len(records), 'planned': len(queue),
            'case_id': case['case_id'], 'arm': arm, 'stage': stage, 'round': repeat})
        base.save(root / 'summary.json', summarize(records))
        print(json.dumps({'completed': len(records), 'planned': len(queue), 'case': case['case_id'],
            'arm': arm, 'wall_s': response['wall_s'], 'quality': judged['passed'],
            'acceptance': verification['original_first_acceptance'] if verification else None,
            'restores': verification['original_restores'] if verification else None}), flush=True)
    return records
