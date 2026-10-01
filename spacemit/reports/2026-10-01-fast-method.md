# Completed pilots and applied fast test method

Status snapshot: 2026-10-01, approximately 22:52 Asia/Singapore.
Read live `phase` and final `exit-status` before treating a run as completed.

## Completed evidence

- [Original layout pilot](raw/k1-layout-20260930-153134/summary.md): exit 0;
  235 cases per layout matched bit for bit; all 24 model completions matched
  within each model/context group. Q32 reduced 2k TTFT by 0.89% on 2B and
  1.98% on 4B. Q16 slightly regressed on 4B/2k. These are small effects with
  two launches per arm, no significance claim and no matched 8k comparison.
  The compact layout remains experimental.
- [Complete-answer quality matrix](raw/document-quality-20260930-full-v2/summary.md):
  all 24 pairs completed, verified cache reuse and were judged in both orders.
  Three configurations pass descriptive gates. 2B/4k needs review: the cache
  question scored 2/5 for both arms. Board generation succeeded; collector
  exit 2 reports that review requirement. No full-matrix quality pass.

## Implemented method

[Launch commands](../bench/README.md#fast-optimization-screens) and
[design rationale](../experiments/2026-09-30-fast-test-design.md).

The controller reuses the completed isolated layout build only after source
and artifact checks. It records model/runtime hashes and actual GGUF head
shapes. Each layout runs 241 concurrent numerical cases, including long KV
histories, before six balanced operator blocks with four pinned workers.

The initial model screen uses 2B/512, one output token and six balanced
launches. It verifies zero cache reuse, complete requests, exact input tokens
and matching output hashes. A candidate advances only when its mean prompt
benefit exceeds both 3% and the observed full control range. Qualifying
candidates then run 2B/2k and 4B/1k comparisons. An eligible winner can resume
into fresh 8k pairs; natural-answer quality uses the separate grouped runner.
One-token requests establish neither decode throughput nor answer quality.

## Applied run

The first run, `k1-fast-20261001-224021`, passed all 241 concurrent cases per
layout in 16.41 seconds. Its operator stage exceeded the original 90-second
budget and exited 1. No model stage ran and no timing pass is claimed.
Completed 4B/8k operator calls took roughly 248-280 ms each in the inspected
control block; warmups and calibration also consume time.

The corrected run is `k1-fast-20261001-224957`, using a **300-second operator
budget**, with all shapes and six blocks retained. Board session:
`k1_fast_k1-fast-20261001-224957`; local collector:
`k1_fast_collect_k1-fast-20261001-224957`. The corrected run has also passed all 241 numerical cases per layout and is
in operator timing at this snapshot.

Results directory:
`spacemit/reports/raw/k1-fast-20261001-224957`.
The model screen has a separate 45-minute upper bound. Build, full-file
provenance hashing and lock waiting are additional costs; a typical completion
time has not yet been measured. A completed inconclusive screen is exit 0,
which means the protocol completed, not that a candidate is faster.

## Next decision

Retain the existing layout unless the staged model gate qualifies a candidate.
If the result is inconclusive, avoid a costly 8k layout comparison and profile
remaining recurrent/prefill work before changing another operator. Treat
recurrent fusion and shared K/V packing as separate candidates with their own
correctness cases and source fingerprints.
