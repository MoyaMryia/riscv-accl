#!/usr/bin/env python3
"""Stage, run, collect, judge and summarize the full document-cache quality matrix.

Default: 2B/4B x 4k/8k, six questions each. --detach keeps the local collector
in tmux; board generation always runs in a separate tmux session. The cloud
key stays on the workstation. No existing result is overwritten.
"""

import argparse
import datetime
import importlib.util
import json
import shlex
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def command(argv, **kwargs):
    return subprocess.run(argv, check=True, text=True, **kwargs)


def remote(board, argv):
    return command(['ssh', '-o', 'ConnectTimeout=15', '-o', 'ServerAliveInterval=15',
                    '-o', 'ServerAliveCountMax=2', board, shlex.join(argv)],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60).stdout.strip()


def load_judge():
    spec = importlib.util.spec_from_file_location('quality_judge', HERE / 'judge-shared-document-cache.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def summarize(run_dir, labels, errors):
    rows, details, total_pairs, eligible_pairs = [], [], 0, 0
    manifest_path = run_dir / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for label in labels:
        path = run_dir / f'{label}.jsonl'
        if not path.exists():
            rows.append({'label': label, 'status': 'generation failed or missing', 'error': errors.get(label)})
            continue
        records = list(map(json.loads, path.read_text().splitlines()))
        pairs = [r for r in records if r['kind'] == 'pair']
        finishes = {f"{label}-{r['case_id']}": {} for r in records if r['kind'] == 'measurement'}
        for record in records:
            if record['kind'] == 'measurement':
                finishes[f"{label}-{record['case_id']}"][record['arm']] = record['result']['finish_reason']
        marks_path = run_dir / f'{label}.judge.jsonl'
        marks = {r['case_id']: r for r in map(json.loads, marks_path.read_text().splitlines())} if marks_path.exists() else {}
        valid = [p for p in pairs if p['audit']['eligible_for_judging']]
        total_pairs += len(pairs); eligible_pairs += len(valid)
        factual_regressions = [p['case_id'] for p in valid
                               if sum(p['audit']['warm_facts']['required_fact_hits'])
                               < sum(p['audit']['cold_facts']['required_fact_hits'])]
        citation_regressions = [p['case_id'] for p in valid
                                if p['audit']['cold_facts']['expected_citation_present']
                                and not p['audit']['warm_facts']['expected_citation_present']]
        judged = [marks[p['case_id']] for p in valid if p['case_id'] in marks]
        for pair in pairs:
            mark = marks.get(pair['case_id'], {})
            details.append({'case_id': pair['case_id'], 'position': pair.get('position'),
                            'eligible': pair['audit']['eligible_for_judging'],
                            'cold_finish_reason': pair.get('cold_finish_reason', finishes.get(pair['case_id'], {}).get('cold')),
                            'warm_finish_reason': pair.get('warm_finish_reason', finishes.get(pair['case_id'], {}).get('warm')),
                            'cold_ttft_s': pair['cold_ttft_s'], 'warm_ttft_s': pair['warm_ttft_s'],
                            'cold_score': mark.get('cold_mean_score'), 'warm_score': mark.get('warm_mean_score'),
                            'audit': pair['audit']})
        cold = statistics.mean(m['cold_mean_score'] for m in judged) if judged else None
        warm = statistics.mean(m['warm_mean_score'] for m in judged) if judged else None
        disagreements = [m['case_id'] for m in judged
                         if any(m['passes'][0][arm]['score'] != m['passes'][1][arm]['score']
                                for arm in ('cold', 'warm'))]
        expected = len(manifest.get('case_ids', [])) or len(pairs)
        all_evaluated = bool(pairs) and len(pairs) == len(valid) == len(judged) == expected
        # A declared descriptive pilot gate; this is not statistical equivalence.
        gate = (all_evaluated and not errors.get(label) and not factual_regressions
                and not citation_regressions and warm >= cold - .5
                and all(m['warm_mean_score'] >= 3 for m in judged))
        rows.append({'label': label, 'status': 'PILOT PASS' if gate else 'REVIEW REQUIRED',
                     'expected_pairs': expected, 'pairs': len(pairs),
                     'completed': sum(p['audit']['complete_pair'] for p in pairs),
                     'cache_verified': sum(p['audit']['cache_verified'] for p in pairs),
                     'eligible': len(valid), 'judged': len(judged),
                     'median_cold_ttft_s': statistics.median(p['cold_ttft_s'] for p in pairs) if pairs else None,
                     'median_warm_ttft_s': statistics.median(p['warm_ttft_s'] for p in pairs) if pairs else None,
                     'cold_mean_score': cold, 'warm_mean_score': warm,
                     'fact_regressions': factual_regressions, 'citation_regressions': citation_regressions,
                     'judge_order_disagreements': disagreements, 'error': errors.get(label)})
    result = {'configurations': rows, 'cases': details, 'recorded_pairs': total_pairs, 'eligible_pairs': eligible_pairs,
              'limitations': 'Constructed public documentation corpus, a small fact-question set, one cloud judge; descriptive pilot only.'}
    (run_dir / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    lines = ['# Document cache quality benchmark', '', result['limitations'], '',
             'Completed answers require finish_reason=stop and no reasoning text. Only completed pairs with verified same-slot cache reuse are judged.', '',
             '| Configuration | Complete / recorded | Judged | Cold TTFT | Cached TTFT | Cold / cached score | Status |',
             '| --- | ---: | ---: | ---: | ---: | ---: | --- |']
    def number(value):
        return '—' if value is None else f'{value:.2f}'
    for row in rows:
        lines.append(f"| {row['label']} | {row.get('completed', 0)} / {row.get('pairs', 0)} | "
                     f"{row.get('judged', 0)} | {number(row.get('median_cold_ttft_s'))} s | "
                     f"{number(row.get('median_warm_ttft_s'))} s | {number(row.get('cold_mean_score'))} / "
                     f"{number(row.get('warm_mean_score'))} | {row['status']} |")
    lines += ['', '| Question | Position | Cold / cached finish | Cold / cached score | Eligible |',
              '| --- | --- | --- | ---: | --- |']
    for case in details:
        lines.append(f"| {case['case_id']} | {case['position']} | {case['cold_finish_reason']} / "
                     f"{case['warm_finish_reason']} | {number(case['cold_score'])} / "
                     f"{number(case['warm_score'])} | {case['eligible']} |")
    lines += ['', 'Pilot gate: all requested pairs complete and judged; no required-fact or citation regression; '
              'cached mean no more than 0.5 points below cold; each cached score at least 3/5. '
              'Fact matching checks required terms and does not establish correctness by itself.', '']
    for row in rows:
        if row.get('error') or row.get('fact_regressions') or row.get('citation_regressions') or row.get('judge_order_disagreements'):
            lines += [f"- {row['label']}: {json.dumps({k: row.get(k) for k in ('error', 'fact_regressions', 'citation_regressions', 'judge_order_disagreements')})}"]
    (run_dir / 'summary.md').write_text('\n'.join(lines) + '\n')
    return result


def run(args):
    run_dir = args.run_dir.resolve()
    if (run_dir / 'manifest.json').exists():
        raise ValueError('run directory already contains a benchmark')
    run_dir.mkdir(parents=True, exist_ok=True)
    judge = load_judge()
    # Validate key locally before spending hours generating; never log or stage it.
    key = args.key_file.read_text().strip()
    if not key or '\n' in key:
        raise ValueError('key file must contain one nonempty key line')
    url = judge.endpoint(args.base_url, False)
    board_home = remote(args.board, ['python3', '-c', 'from pathlib import Path; print(Path.home())'])
    remote_root = f'{board_home}/Projects/riscv-accl-bench-2026-09-27/quality-suite/{run_dir.name}'
    remote(args.board, ['mkdir', '-p', remote_root + '/bench', remote_root + '/serve'])
    for directory, names in [('bench', ['bench-lifecycle.py', 'bench-shared-document-cache.py',
                                        'document_quality_suite.py', 'run-all-document-quality-board.sh']),
                             ('serve', ['cached-document-chat.py'])]:
        paths = [str(HERE.parent / directory / name) for name in names]
        command(['scp', *paths, f'{args.board}:{remote_root}/{directory}/'], timeout=60)
    labels = [f'{model}-{context}' for model in args.models for context in args.contexts]
    manifest = {'models': args.models, 'contexts': args.contexts, 'max_tokens': args.max_tokens,
                'case_ids': args.case_id or ['routes', 'batches', 'cache', 'slot', 'health', 'tokenize'],
                'remote_root': remote_root, 'board': args.board, 'judge_model': args.judge_model,
                'expected_pairs': len(labels) * len(args.case_id or range(6))}
    (run_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (run_dir / 'summary.md').write_text(
        '# Document cache quality benchmark\n\nRunning; final results are pending.\n\n'
        f"Requested configurations: {', '.join(labels)}. Expected pairs: {manifest['expected_pairs']}.\n\n"
        'The collector replaces this file as configurations complete and are judged.\n')
    session = 'docq_' + run_dir.name
    board_command = shlex.join(['bash', remote_root + '/bench/run-all-document-quality-board.sh',
                               remote_root, ' '.join(args.models), ' '.join(map(str, args.contexts)),
                               str(args.max_tokens), ' '.join(args.case_id or [])])
    board_command += ' > ' + shlex.quote(remote_root + '/matrix.log') + ' 2>&1'
    remote(args.board, ['tmux', 'new-session', '-d', '-s', session, board_command])
    print(f'Board tmux {session}; results {run_dir}', flush=True)
    remaining, errors = set(labels), {}
    deadline = time.monotonic() + args.suite_timeout
    while remaining:
        if time.monotonic() >= deadline:
            raise TimeoutError('collector deadline exceeded; board tmux may still be running')
        for label in labels:
            if label not in remaining:
                continue
            try:
                status = remote(args.board, ['cat', remote_root + f'/{label}.exit-status'])
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                continue
            # Collect partial records too, so failed configurations remain diagnosable.
            for suffix in ('.jsonl', '.server.log', '.driver.log', '.judge-input.json', '.summary.json', '.document.txt', '.exit-status'):
                try:
                    command(['scp', f'{args.board}:{remote_root}/{label}{suffix}', str(run_dir)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=60)
                except subprocess.CalledProcessError:
                    pass
            if status != '0':
                errors[label] = f'generation exit {status}; see {label}.driver.log'
            else:
                try:
                    cases = json.loads((run_dir / f'{label}.judge-input.json').read_text())
                    if cases:
                        out = run_dir / f'{label}.judge.jsonl'
                        with out.open('x') as handle:
                            for case in cases:
                                result = judge.grade_case(case, url, args.judge_model, key, 120, 2, 1536, True)
                                handle.write(json.dumps(result) + '\n'); handle.flush()
                                print(f"{case['case_id']}: cold {result['cold_mean_score']}/5, "
                                      f"cached {result['warm_mean_score']}/5", flush=True)
                    else:
                        errors[label] = 'No completed pairs with verified cache reuse; judging skipped'
                except (ValueError, RuntimeError, OSError) as exc:
                    errors[label] = f'judging failed: {type(exc).__name__}'
            remaining.remove(label)
            summarize(run_dir, [l for l in labels if l not in remaining], errors)
        if remaining:
            time.sleep(60)
    result = summarize(run_dir, labels, errors)
    status = 1 if errors else (0 if all(r['status'] == 'PILOT PASS' for r in result['configurations']) else 2)
    (run_dir / 'exit-status').write_text(f'{status}\n')
    print(json.dumps(result, indent=2), flush=True)
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', default='musepipro-wg')
    parser.add_argument('--models', choices=['2B', '4B'], nargs='+', default=['2B', '4B'])
    parser.add_argument('--contexts', type=int, nargs='+', default=[4096, 8192])
    parser.add_argument('--max-tokens', type=int, default=512)
    parser.add_argument('--case-id', action='append', choices=['routes', 'batches', 'cache', 'slot', 'health', 'tokenize'])
    parser.add_argument('--base-url', default='https://api.xiaomimimo.com/v1')
    parser.add_argument('--judge-model', default='mimo-v2.6-flash')
    parser.add_argument('--key-file', type=Path, default=Path.home() / '.secret_ai_key')
    parser.add_argument('--suite-timeout', type=int, default=86400)
    parser.add_argument('--run-dir', type=Path,
                        default=HERE.parent / 'reports/raw' / ('document-quality-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S')))
    parser.add_argument('--detach', action='store_true')
    args = parser.parse_args()
    if min(*args.contexts, args.max_tokens, args.suite_timeout) < 1:
        parser.error('contexts, max-tokens and suite-timeout must be positive')
    if len(set(args.models)) != len(args.models) or len(set(args.contexts)) != len(args.contexts):
        parser.error('duplicate model/context configuration')
    if args.case_id and len(set(args.case_id)) != len(args.case_id):
        parser.error('duplicate case ID')
    if args.detach:
        args.run_dir = args.run_dir.resolve()
        args.run_dir.mkdir(parents=True, exist_ok=False)
        session = 'docq_local_' + args.run_dir.name
        argv = [sys.executable, str(Path(__file__).resolve()),
                *[a for a in sys.argv[1:] if a != '--detach']]
        if '--run-dir' not in sys.argv:
            argv += ['--run-dir', str(args.run_dir)]
        invocation = shlex.join(argv) + ' > ' + shlex.quote(str(args.run_dir / 'collector.log')) + ' 2>&1'
        command(['tmux', 'new-session', '-d', '-s', session, invocation])
        print(f'Started local tmux {session}. Read {args.run_dir}/summary.md after completion.')
        return 0
    try:
        return run(args)
    except Exception as exc:
        args.run_dir.mkdir(parents=True, exist_ok=True)
        # Avoid echoing response bodies or credentials from network exceptions.
        (args.run_dir / 'failure.txt').write_text(f'Collector failed: {type(exc).__name__}\n')
        (args.run_dir / 'exit-status').write_text('1\n')
        print(f'Collector failed: {type(exc).__name__}; inspect driver logs.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
