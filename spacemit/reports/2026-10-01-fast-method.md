# Completed pilots and applied fast test method

Completion update: 2026-10-02, Asia/Singapore.
Read the live `phase` and the final `exit-status`, before you treat a run as
completed.

## Completed evidence

- [Original layout pilot](raw/k1-layout-20260930-153134/summary.md): exit 0.
  235 cases per layout matched bit for bit, and all 24 model completions
  matched inside each model/context group. Q32 reduced 2k TTFT by 0.89% on 2B
  and by 1.98% on 4B. Q16 slightly regressed on 4B/2k. These are small
  effects, with two launches per arm. There is no significance claim and no
  matched 8k comparison. The compact layout remains experimental.
- [Complete-answer quality matrix](raw/document-quality-20260930-full-v2/summary.md):
  all 24 pairs completed, and they verified cache reuse and were judged in
  both orders. Three configurations pass the descriptive gates. 2B/4k needs a
  review, because the cache question scored 2/5 for both arms. Board
  generation succeeded. Collector exit 2 reports that review requirement.
  There is no full-matrix quality pass.

## Implemented method

The [launch commands](../bench/README.md#fast-optimization-screens) and the
[design rationale](../experiments/2026-09-30-fast-test-design.md) describe the
method.

The controller reuses the completed isolated layout build only after source
and artifact checks. It records model and runtime hashes, and the actual GGUF
head shapes. Each layout runs 241 concurrent numerical cases, including long KV
histories, before six balanced operator blocks with four pinned workers.

The initial model screen uses 2B/512, one output token, and six balanced
launches. It verifies zero cache reuse, complete requests, exact input tokens,
and matching output hashes. A candidate advances only when its mean prompt
benefit exceeds both 3% and the observed full control range. The qualifying
candidates then run 2B/2k and 4B/1k comparisons. An eligible winner can resume
into fresh 8k pairs. Natural-answer quality uses the separate grouped runner.
One-token requests establish neither decode throughput nor answer quality.

## Applied run

The first run, `k1-fast-20261001-224021`, passed all 241 concurrent cases per
layout in 16.41 seconds. Its operator stage exceeded the original 90-second
budget and exited 1. No model stage ran, and the run claims no timing pass.
The completed 4B/8k operator calls took roughly 248–280 ms each in the
inspected control block. Warmups and calibration also consume time.

The corrected run is `k1-fast-20261001-224957`. It uses a **300-second
operator budget**, and it retains all shapes and all six blocks. Board
session: `k1_fast_k1-fast-20261001-224957`. Local collector:
`k1_fast_collect_k1-fast-20261001-224957`. The corrected run completed at
22:58:26 on October 1, with exit 0 and status **inconclusive**. All 241
numerical cases per layout passed. Operator timing took 136.21 seconds for
216 records, and the model screen took 214.50 seconds. The Q16 and Q32
prompt-time reductions were 0.32% and 0.53%, below the advancement threshold.
The runner skipped the longer model and quality stages.

Results directory:
`spacemit/reports/raw/k1-fast-20261001-224957`.
The model screen has a separate 45-minute upper bound. Build, full-file
provenance hashing, and lock waiting are additional costs. This screen
completed in 507.14 seconds (8.45 minutes), including preparation. That
duration is one observation, not a general estimate. A completed
inconclusive screen exits 0. That exit means that the protocol completed. It
does not mean that a candidate is faster.

## Next decision

Retain the existing layout, unless the staged model gate qualifies a
candidate. If the result is inconclusive, avoid a costly 8k layout comparison.
Instead, profile the remaining recurrent and prefill work, before you change
another operator. Treat recurrent fusion and shared K/V packing as separate
candidates. Each candidate needs its own correctness cases and source
fingerprints.

The next measured step is the
[October 2 cold-prefill profile](2026-10-02-prefill-profile.md).
