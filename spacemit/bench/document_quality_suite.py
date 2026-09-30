"""Chat quality extension for bench-shared-document-cache.py (stdlib only)."""

import hashlib
import importlib.util
import json
import re
import statistics
import subprocess
import time
from pathlib import Path


def load_chat():
    path = Path(__file__).resolve().parent.parent / 'serve' / 'cached-document-chat.py'
    spec = importlib.util.spec_from_file_location('cached_document_chat', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evidence_cases(readme):
    """Extract exact passages; fail if the pinned source no longer matches."""
    lines = readme.splitlines()

    def excerpt(needle, count=1):
        index = next(i for i, line in enumerate(lines) if needle in line)
        return '\n'.join(lines[index:index + count]).strip(), index + 1

    definitions = [
        ('routes', '* [OpenAI API]', 1,
         'Which three OpenAI-compatible route types are listed?',
         ['chat completions', 'responses', 'embeddings'],
         [r'chat\s+completions?', r'responses?', r'embeddings?']),
        ('batches', '| `-b, --batch-size N`', 2,
         'Give the logical batch and physical microbatch flags and their documented defaults.',
         ['--batch-size default 2048', '--ubatch-size default 512'],
         [r'2048', r'512', r'(?:--batch-size|(?<!\w)-b\b)', r'(?:--ubatch-size|(?<!\w)-ub\b)']),
        ('cache', '`cache_prompt`: Re-use', 1,
         'What does cache_prompt reuse, what gets reprocessed, and are identical logits guaranteed?',
         ['reuse the common prefix/KV cache', 'evaluate only the differing suffix',
          'bit-for-bit identical logits are not guaranteed because batching can differ'],
         [r'(?:prefix|cache)', r'suffix', r'(?:not guaranteed|not.*identical|no guarantee|nondeterministic)', r'batch']),
        ('slot', '`id_slot`: Assign', 1,
         'What does id_slot do, and what is its default value and default assignment behavior?',
         ['assign a completion to a specific slot', 'default -1 selects an idle slot'],
         [r'slot', r'[-−]\s*1', r'idle']),
        ('health', '### GET `/health`', 14,
         'Does /health require an API key? Give its alternative path and the loading and ready HTTP codes.',
         ['no API key check', '/v1/health also works', '503 while loading', '200 when ready'],
         [r'(?:no|not|without|public)', r'/v1/health', r'503', r'200']),
        ('tokenize', '### POST `/tokenize`', 9,
         'What field supplies text to /tokenize? What does add_special control and what is its default?',
         ['content is required', 'add_special inserts special tokens such as BOS', 'default false'],
         [r'content', r'(?:special|BOS)', r'false']),
    ]
    cases = []
    for index, (case_id, needle, count, question, facts, patterns) in enumerate(definitions):
        evidence, line = excerpt(needle, count)
        source_id = f'S{index + 1}'
        cases.append({'case_id': case_id, 'source_id': source_id,
                      'position': ('beginning', 'middle', 'end')[index // 2],
                      'question': question + f' Answer in at most 90 words and cite [{source_id}].',
                      'evidence': f'[{source_id}] tools/server/README.md:{line}\n{evidence}',
                      'required_facts': facts, 'fact_patterns': patterns})
    return cases


def make_document(url, chat, source_cases, corpus, budget, timeout):
    """Keep all evidence intact and fill the gaps with unmodified public text."""
    tokens = chat.post_json(url + '/tokenize', {'content': corpus, 'add_special': False}, timeout)['tokens']
    groups = ['\n\n'.join(c['evidence'] for c in source_cases[i:i + 2]) for i in (0, 2, 4)]
    # Separate source blocks to exercise evidence at the beginning, middle and end.
    def build(n):
        filler = chat.post_json(url + '/detokenize', {'tokens': tokens[:n]}, timeout)['content'] if n else ''
        # Split on a line boundary; avoid changing individual source lines.
        split = filler.find('\n', len(filler) // 2)
        split = len(filler) // 2 if split < 0 else split
        return ('Public documentation benchmark. Cite the labelled source blocks.\n\n'
                + groups[0] + '\n\n[Additional public documentation]\n' + filler[:split]
                + '\n\n' + groups[1] + '\n\n[Additional public documentation]\n'
                + filler[split:] + '\n\n' + groups[2])

    low, high = 0, min(len(tokens), budget)
    document = build(0)
    if len(chat.post_json(url + '/tokenize', {'content': document, 'add_special': False}, timeout)['tokens']) > budget:
        raise ValueError('document budget cannot contain all six evidence blocks')
    while low <= high:
        middle = (low + high) // 2
        candidate = build(middle)
        count = len(chat.post_json(url + '/tokenize', {'content': candidate, 'add_special': False}, timeout)['tokens'])
        if count <= budget:
            document = candidate
            low = middle + 1
        else:
            high = middle - 1
    count = len(chat.post_json(url + '/tokenize', {'content': document, 'add_special': False}, timeout)['tokens'])
    for case in source_cases:
        assert case['evidence'] in document
        start = document.index(case['evidence'])
        case['evidence_char_offset'] = start
        case['evidence_char_fraction'] = round(start / len(document), 4)
    return document, count


def fact_check(case, answer):
    plain = re.sub(r'[`*_]', '', answer)
    return {'required_fact_hits': [bool(re.search(p, plain, re.I | re.S)) for p in case['fact_patterns']],
            'expected_citation_present': f"[{case['source_id']}]" in answer}


def pair_audit(case, arms, prompt_tokens, document_tokens):
    warm, cold = arms['warm'], arms['cold']
    complete = all(r.get('finish_reason') == 'stop' and r.get('answer', '').strip()
                   and not r.get('reasoning_text') and '<think>' not in r.get('answer', '') for r in arms.values())
    cached = warm.get('usage', {}).get('prompt_tokens_details', {}).get('cached_tokens')
    cold_cached = cold.get('usage', {}).get('prompt_tokens_details', {}).get('cached_tokens')
    warm_slot, cold_slot = warm.get('server_slot'), cold.get('server_slot')
    cache_ok = (isinstance(cached, int) and cached >= .9 * document_tokens and cold_cached == 0
                and warm_slot == cold_slot == 0)
    return {'complete_pair': complete, 'cache_verified': cache_ok,
            'eligible_for_judging': complete and cache_ok,
            'warm_cached_tokens': cached, 'cold_cached_tokens': cold_cached,
            'prompt_tokens': prompt_tokens,
            'ttft_speedup': cold['ttft_s'] / warm['ttft_s'] if warm.get('ttft_s') else None,
            'text_identical': warm.get('answer_sha256') == cold.get('answer_sha256'),
            'warm_facts': fact_check(case, warm.get('answer', '')),
            'cold_facts': fact_check(case, cold.get('answer', ''))}


def run_chat_suite(args, bench):
    if min(args.context, args.n_predict, args.timeout, args.ctx_size) < 1:
        raise ValueError('context, output cap, timeout and allocation must be positive')
    if args.output.exists() or args.log.exists():
        raise FileExistsError('refusing to overwrite existing output or server log')
    for path in (args.server, args.model, args.document, args.source_readme):
        if not path.is_file():
            raise FileNotFoundError(path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    chat = load_chat()
    all_cases = evidence_cases(args.source_readme.read_text())
    selected = args.case_id or [c['case_id'] for c in all_cases]
    if len(set(selected)) != len(selected) or set(selected) - {c['case_id'] for c in all_cases}:
        raise ValueError('unknown or duplicate case ID')
    command = [str(args.server), '-m', str(args.model), '--alias', 'local', '-t', '4',
               '-c', str(args.ctx_size), '--parallel', '1', '-b', '32', '-ub', '32',
               '-fa', 'on', '--host', '127.0.0.1', '--port', str(args.port), '-ctk', 'f16', '-ctv', 'f16']
    url = f'http://127.0.0.1:{args.port}'
    pairs = []
    with args.log.open('xb') as log, args.output.open('x') as output:
        proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        try:
            bench.wait_healthy(proc, url, min(args.timeout, 180))
            document, doc_tokens = make_document(url, chat, all_cases, args.document.read_text(), args.context, args.timeout)
            doc_file = args.output.with_suffix('.document.txt')
            doc_file.write_text(document)
            document_sha = hashlib.sha256(document.encode()).hexdigest()
            config = {'kind': 'config', 'suite': 'chat-quality-v1', 'model_size': args.model_size,
                      'document_budget': args.context, 'document_tokens': doc_tokens,
                      'document_sha256': document_sha, 'document_file': str(doc_file),
                      'source_readme_sha256': hashlib.sha256(args.source_readme.read_bytes()).hexdigest(),
                      'max_tokens': args.n_predict, 'ctx_size': args.ctx_size,
                      'command': command, 'cases': all_cases,
                      'system_instruction': chat.SYSTEM_INSTRUCTION}
            code_files = [Path(__file__), Path(__file__).with_name('bench-shared-document-cache.py'),
                          Path(__file__).parent.parent / 'serve' / 'cached-document-chat.py']
            config['code_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in code_files}
            config['server_sha256'] = hashlib.sha256(args.server.read_bytes()).hexdigest()
            output.write(json.dumps(config) + '\n'); output.flush()
            for index, case in enumerate(c for c in all_cases if c['case_id'] in selected):
                base = chat.request_body(chat.messages(document, case['question']), 'local', 0, args.n_predict)
                base.update({'stream_options': {'include_usage': True}, 'verbose': True})
                prompt_tokens = chat.count_prompt_tokens(url, base, args.timeout)
                if prompt_tokens + args.n_predict > args.ctx_size:
                    raise ValueError('chat prompt plus output cap exceeds context allocation')
                arms = {}
                order = ['warm', 'cold'] if index % 2 == 0 else ['cold', 'warm']
                for arm in order:
                    if arm == 'warm':
                        # Never warm with the target question itself, including cold-first pairs.
                        primer = chat.request_body(chat.messages(document, 'Reply with the word Ready.'), 'local', 0, 24)
                        primer.update({'stream_options': {'include_usage': True}, 'verbose': True})
                        primer_result = chat.complete(url, primer, args.timeout, display=False)
                        if primer_result['server_slot'] != 0:
                            raise RuntimeError('primer did not use physical slot 0')
                        output.write(json.dumps({'kind': 'primer', 'case_id': case['case_id'], 'result': primer_result}) + '\n')
                    payload = dict(base, cache_prompt=arm == 'warm')
                    result = chat.complete(url, payload, args.timeout, display=False)
                    arms[arm] = result
                    output.write(json.dumps({'kind': 'measurement', 'case_id': case['case_id'],
                                             'arm': arm, 'cache_prompt': payload['cache_prompt'],
                                             'prompt_tokens': prompt_tokens, 'result': result}) + '\n')
                    output.flush()
                    print(f"{args.model_size}/{args.context} {case['case_id']} {arm}: "
                          f"TTFT {result['ttft_s']}s, finish {result['finish_reason']}", flush=True)
                audit = pair_audit(case, arms, prompt_tokens, doc_tokens)
                pair = {'kind': 'pair', 'case_id': f"{args.model_size}-{args.context}-{case['case_id']}",
                        'question': case['question'], 'evidence': case['evidence'],
                        'required_facts': case['required_facts'], 'position': case['position'],
                        'order': order, 'cold_answer': arms['cold']['answer'], 'warm_answer': arms['warm']['answer'],
                        'document_sha256': document_sha, 'audit': audit,
                        'cold_finish_reason': arms['cold']['finish_reason'],
                        'warm_finish_reason': arms['warm']['finish_reason'],
                        'cold_ttft_s': arms['cold']['ttft_s'], 'warm_ttft_s': arms['warm']['ttft_s']}
                pairs.append(pair)
                output.write(json.dumps(pair) + '\n'); output.flush()
                print(f"PAIR {pair['case_id']}: {json.dumps(audit)}", flush=True)
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill(); proc.wait()
    judge_cases = [{k: p[k] for k in ('case_id', 'question', 'evidence', 'required_facts', 'cold_answer', 'warm_answer')}
                   for p in pairs if p['audit']['eligible_for_judging']]
    args.output.with_suffix('.judge-input.json').write_text(json.dumps(judge_cases, indent=2) + '\n')
    summary = {'expected_pairs': len(selected), 'recorded_pairs': len(pairs),
               'completed_pairs': sum(p['audit']['complete_pair'] for p in pairs),
               'cache_verified_pairs': sum(p['audit']['cache_verified'] for p in pairs),
               'judge_eligible_pairs': len(judge_cases),
               'median_ttft_speedup': statistics.median(p['audit']['ttft_speedup'] for p in pairs)}
    args.output.with_suffix('.summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    if 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' not in args.log.read_text():
        raise RuntimeError('RVV activation marker missing from server log')
    print(json.dumps(summary), flush=True)
