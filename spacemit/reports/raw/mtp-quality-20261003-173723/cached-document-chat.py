#!/usr/bin/env python3
"""Ask changing questions over one cached document in one llama-server slot.

Keep this process and the server alive for follow-up questions. The document
and system instruction stay byte-for-byte identical; only the final question
changes. llama-server performs the actual prefix reuse with cache_prompt=true.
"""

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SYSTEM_INSTRUCTION = (
    'Answer the question using the document. Be concise and factual. '
    'If the document does not contain the answer, say so. '
    'Give the answer directly without reasoning tags.'
)


def post_json(url, payload, timeout):
    request = urllib.request.Request(
        url, json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        {'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def messages(document, question):
    return [
        {'role': 'system', 'content': SYSTEM_INSTRUCTION},
        {'role': 'user', 'content': f'Document:\n{document}\n\nQuestion: {question}'},
    ]


def request_body(chat_messages, model, slot, max_tokens):
    return {
        'model': model, 'messages': chat_messages, 'cache_prompt': True,
        'id_slot': slot, 'stream': True, 'temperature': 0, 'seed': 42,
        'max_tokens': max_tokens, 'chat_template_kwargs': {'enable_thinking': False},
    }


def count_prompt_tokens(url, payload, timeout):
    count = post_json(url + '/v1/chat/completions/input_tokens', payload, timeout)['input_tokens']
    if not isinstance(count, int) or count < 1:
        raise RuntimeError('server did not return a positive input token count')
    return count


def complete(url, payload, timeout, display=True):
    request = urllib.request.Request(
        url + '/v1/chat/completions',
        json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        {'Content-Type': 'application/json'}, method='POST')
    start = time.monotonic()
    first = None
    parts = []
    finish_reason = None
    usage = {}
    timings = {}
    server_slot = None
    reasoning = []
    with urllib.request.urlopen(request, timeout=timeout) as response:
        for raw in response:
            if not raw.startswith(b'data: '):
                continue
            data = raw[6:].strip()
            if data == b'[DONE]':
                break
            event = json.loads(data)
            if event.get('error'):
                raise RuntimeError('server returned a completion error')
            usage.update(event.get('usage') or {})
            timings.update(event.get('timings') or {})
            if isinstance(event.get('__verbose'), dict):
                server_slot = event['__verbose'].get('id_slot')
            for choice in event.get('choices', []):
                delta = choice.get('delta') or {}
                if isinstance(delta.get('reasoning_content'), str):
                    reasoning.append(delta['reasoning_content'])
                content = delta.get('content')
                if isinstance(content, str) and content:
                    if first is None:
                        first = time.monotonic()
                    parts.append(content)
                    if display:
                        print(content, end='', flush=True)
                if choice.get('finish_reason'):
                    finish_reason = choice['finish_reason']
    if display:
        print(flush=True)
    if first is None or not parts:
        raise RuntimeError('server returned no answer text')
    if finish_reason is None:
        raise RuntimeError('completion stream ended without a finish reason')
    answer = ''.join(parts)
    return {
        'answer': answer,
        'ttft_s': round(first - start, 3),
        'wall_s': round(time.monotonic() - start, 3),
        'finish_reason': finish_reason,
        'answer_sha256': hashlib.sha256(answer.encode()).hexdigest(),
        'usage': usage, 'timings': timings, 'server_slot': server_slot,
        'reasoning_text': ''.join(reasoning),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--document', type=Path, required=True)
    parser.add_argument('--url', default='http://127.0.0.1:18085')
    parser.add_argument('--model', default='local')
    parser.add_argument('--slot', type=int, default=0)
    parser.add_argument('--max-tokens', type=int, default=512)
    parser.add_argument('--ctx-size', type=int, required=True, help='must equal the server context allocation')
    parser.add_argument('--timeout', type=int, default=7200)
    parser.add_argument('--question', action='append', help='repeat for multiple questions; omit for interactive mode')
    parser.add_argument('--output', type=Path, help='optional JSONL log with answer text and latency')
    args = parser.parse_args()
    if args.slot < 0 or args.max_tokens < 1 or args.timeout < 1 or args.ctx_size < 1:
        parser.error('slot must be nonnegative; max-tokens, ctx-size, and timeout must be positive')
    document = args.document.read_text(encoding='utf-8')
    if not document.strip():
        parser.error('document is empty')
    url = args.url.rstrip('/')
    with urllib.request.urlopen(url + '/health', timeout=10) as response:
        if response.status != 200:
            raise RuntimeError('server is not healthy')
    document_sha = hashlib.sha256(document.encode()).hexdigest()
    if args.output and args.output.exists():
        parser.error('refusing to overwrite the output file')
    output = args.output.open('x', encoding='utf-8') if args.output else None
    try:
        questions = args.question
        if questions is None:
            questions = iter(lambda: input('\nQuestion (blank to quit): ').strip(), '')
        for question in questions:
            if not question.strip():
                continue
            payload = request_body(messages(document, question), args.model, args.slot, args.max_tokens)
            prompt_tokens = count_prompt_tokens(url, payload, args.timeout)
            if prompt_tokens + args.max_tokens > args.ctx_size:
                raise ValueError(f'prompt {prompt_tokens} + output {args.max_tokens} exceeds context {args.ctx_size}')
            print(f'Prompt: {prompt_tokens} tokens; cached document SHA-256: {document_sha[:12]}', file=sys.stderr)
            result = complete(url, payload, args.timeout)
            print(f"TTFT {result['ttft_s']:.2f}s; wall {result['wall_s']:.2f}s; stop {result['finish_reason']}",
                  file=sys.stderr)
            if output:
                output.write(json.dumps({'question': question, 'document_sha256': document_sha,
                                         'prompt_tokens': prompt_tokens, 'slot': args.slot,
                                         'cache_prompt': True, **result}, ensure_ascii=False) + '\n')
                output.flush()
    finally:
        if output:
            output.close()


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, urllib.error.URLError, RuntimeError) as exc:
        print(f'cached-document chat failed: {exc}', file=sys.stderr)
        sys.exit(1)
