#!/usr/bin/env python3
"""Resume saved MTP scoring with a recorded judge transport fix; no board rerun."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resume(root, key_file):
    fixed_judge = HERE / 'judge-shared-document-cache.py'
    original_judge = root / fixed_judge.name
    # Retain the original staged code and its artifact/hash receipt. The only
    # override is the HTTP transport helper; prompt, grading and resume logic
    # still come from the original judge module.
    original = load('original_judge', original_judge)
    fixed = load('fixed_judge', fixed_judge)
    def transport(url, model, key, messages, timeout, retries, max_tokens):
        return fixed.chat_completion(url, model, key, messages, timeout, retries, max(max_tokens, 4096))
    original.chat_completion = transport
    scorer = load('original_scorer', root / 'score-mtp-quality.py')
    original_loader = scorer.module
    def loader(name, folder=root):
        return original if name == 'judge-shared-document-cache' else original_loader(name, folder)
    scorer.module = loader
    evidence = {
        'status': 'running',
        'change': 'Retry incomplete/disconnected HTTP responses and malformed judgments; original rubric, saved generations and staged files retained.',
        'judge_response_token_budget': 4096,
        'original_judge_sha256': hashlib.sha256(original_judge.read_bytes()).hexdigest(),
        'transport_fix_sha256': hashlib.sha256(fixed_judge.read_bytes()).hexdigest(),
        'recovery_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'prior_collector_exit': (root / 'collector-exit-status').read_text().strip(),
    }
    record = root / 'scoring-recovery.json'
    record.write_text(json.dumps(evidence, indent=2) + '\n')
    try:
        manifest = json.loads((root / 'run.json').read_text())
        result = scorer.score(root, key_file, manifest['judge']['base_url'], manifest['judge']['model'])
        status = 0 if result['candidate_useful_in_pilot'] else 2
        evidence.update(status='completed', exit=status)
        (root / 'collector-exit-status').write_text(str(status) + '\n')
    except BaseException as error:
        evidence.update(status='failed', error=type(error).__name__)
        (root / 'scoring-phase').write_text('recovery failed: ' + type(error).__name__ + '\n')
        raise
    finally:
        record.write_text(json.dumps(evidence, indent=2) + '\n')
        with (root / 'scoring-recovery-history.jsonl').open('a') as output:
            output.write(json.dumps(evidence) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--key-file', type=Path, default=Path.home() / '.secret_ai_key')
    args = parser.parse_args()
    resume(args.root.resolve(), args.key_file.resolve())
