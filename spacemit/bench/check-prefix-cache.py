#!/usr/bin/env python3
"""Gate a three-request, same-server prefix-cache benchmark."""

import argparse
import json
from pathlib import Path


def check(path: Path, expected_context: int) -> None:
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    config = [record for record in records if record.get("kind") == "config"]
    runs = [record for record in records if record.get("kind") == "measurement"]
    assert len(config) == 1 and len(runs) == 3, "expected one config and three runs"
    assert len(records) == 4, "unexpected records"
    cfg = config[0]
    assert cfg["cache_prompt"] is True and cfg["contexts"] == [expected_context]
    assert cfg["repeats"] == 3 and cfg["concurrency"] == 1
    assert cfg["mode"] == "plain" and cfg["n_predict"] == 32
    assert cfg["cache_type_k"] == cfg["cache_type_v"] == "f16"
    assert cfg["runtime_env"].get("SPINE_FA_WIDE_TILE") == "1"
    assert [run["repeat"] for run in runs] == [0, 1, 2]

    results = []
    for run in runs:
        assert run["context_tokens"] == expected_context
        assert len(run["results"]) == 1
        result = run["results"][0]
        assert result["error"] is None, result["error"]
        assert result["stop_type"] == "limit" and result["tokens_predicted"] == 32
        assert len(result["token_ids"]) == 32
        assert result["timings"]["predicted_n"] == 32
        results.append(result)

    cold = results[0]
    assert cold["timings"]["cache_n"] == 0, "first request was not cold"
    assert cold["timings"]["prompt_n"] == expected_context
    for index, warm in enumerate(results[1:], 1):
        assert warm["token_ids"] == cold["token_ids"], f"run {index}: token IDs differ"
        assert warm["sha256"] == cold["sha256"], f"run {index}: text differs"
        assert warm["timings"]["cache_n"] >= 0.9 * expected_context, f"run {index}: low cache hit"
        assert warm["timings"]["prompt_n"] <= 0.1 * expected_context, f"run {index}: too much re-prefill"
        assert warm["ttft_ms"] <= 0.5 * cold["ttft_ms"], f"run {index}: insufficient TTFT improvement"

    print(f"PASS {expected_context}: cold TTFT {cold['ttft_ms']/1000:.2f}s; "
          + "; ".join(f"warm {index} {warm['ttft_ms']/1000:.2f}s, "
                      f"cache {warm['timings']['cache_n']}/{expected_context}"
                      for index, warm in enumerate(results[1:], 1)), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("context", type=int)
    args = parser.parse_args()
    check(args.record, args.context)
