#!/usr/bin/env python3
"""Gate changed-question prefix reuse against a forced-cold control."""

import argparse
import json
from pathlib import Path


def audit(path: Path, context: int, model_size: str):
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    assert len(records) == 4, 'expected configuration and three requests'
    config, a, warm, cold = records
    assert config['kind'] == 'config'
    assert config['model_size'] == model_size and config['context'] == context
    assert config['SPINE_FA_WIDE_TILE'] == '1'
    assert config['document_tokens_available'] >= context
    assert config['questions'][0] != config['questions'][1]
    assert [r['name'] for r in (a, warm, cold)] == [
        'question_a_cold', 'question_b_warm', 'question_b_cold_control']
    assert a['cache_prompt'] is True and warm['cache_prompt'] is True
    assert cold['cache_prompt'] is False
    assert warm['prompt_tokens'] == cold['prompt_tokens']
    for record in (a, warm, cold):
        assert record['kind'] == 'measurement'
        result = record['result']
        assert result['error'] is None, result['error']
        assert result['stop_type'] == 'limit' and result['tokens_predicted'] == 32
        assert len(result['token_ids']) == 32
        assert result['server_slot'] == 0
        assert result['ttft_ms'] is not None and result['ttft_ms'] > 0
        assert result['timings']['predicted_n'] == 32
    assert a['result']['timings']['cache_n'] == 0
    assert cold['result']['timings']['cache_n'] == 0, 'cold control reused cached tokens'
    assert cold['result']['timings']['prompt_n'] == cold['prompt_tokens']
    assert warm['result']['timings']['cache_n'] >= .9 * context, 'shared prefix was not reused'
    assert warm['result']['timings']['prompt_n'] <= .1 * context + 256
    assert warm['result']['token_ids'] == cold['result']['token_ids'], 'new-question token IDs differ'
    assert warm['result']['sha256'] == cold['result']['sha256'], 'new-question text differs'
    cold_ttft = cold['result']['ttft_ms']
    warm_ttft = warm['result']['ttft_ms']
    assert warm_ttft <= .5 * cold_ttft, 'new-question cache gives insufficient TTFT improvement'
    print(f'PASS {model_size} {context}: new question cold {cold_ttft / 1000:.2f}s, '
          f'warm {warm_ttft / 1000:.2f}s, '
          f'cache {warm["result"]["timings"]["cache_n"]}/{context}, exact 32 tokens',
          flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path)
    parser.add_argument('context', type=int)
    parser.add_argument('model_size', choices=['2B', '4B'])
    args = parser.parse_args()
    audit(args.record, args.context, args.model_size)
