# Checkpoint MTP: complete-answer usefulness pilot

Purpose: measure whether MTP retains useful answers while reducing latency,
without requiring the same wording or token sequence as direct decoding.
This is separate from the failed native RS rollback checks. It does not
establish mathematical losslessness or repair the RS path.

## Predeclared configuration

- Required Qwen3.5 2B/4B Q4_0 models; tested `a990751` build and recorded hashes.
- Four threads, F16 KV, batch/microbatch 32, wide attention, layout 0, routing 0.
  Both arms use the same routing so the measured effect concerns MTP.
- Direct decoding versus checkpoint MTP, draft length 3, `SPINE_SPEC_RS=0`.
- Context 6144. Every request sends the same complete task input in both arms;
  caching and context shifting are disabled. Actual input counts are checked.
- Natural stopping, with a 512-token cap for concise document answers and a
  1536-token cap for code/Chinese prose. Length-capped outputs are incomplete.
- Six tasks per model, one request per arm: **24 requests**. Direct→MTP on 2B,
  MTP→direct on 4B; MTP reverses task order. This is a pilot, not replication.

## Tasks and independent checks

Three public-document/synthetic-evidence tasks use a complete ~2k fixture:
documented API routes, orion→maple→cedar→cobalt tracing, and 17+23+38 aggregation.
All six evidence blocks remain present, distributed through the document.
The same known facts and citation markers are checked in both arms.

Two Python tasks require builtins-only functions: merge busy intervals/find
free windows, and Unicode run-length encoding/decoding. Saved code is parsed,
executed in a child with restricted builtins/AST constructs and CPU/memory
limits, and checked against deterministic edge cases and generated test inputs.
Imports, classes, file/network access and runtime introspection are excluded
from the task. Fenced source is accepted; invalid or rejected code is retained.

A Chinese prose task explains a supplied fictional shipping/refund policy and
gives examples. Known facts are checked, then both answers are cloud-scored
against the exact source evidence. It also supplies a longer natural generation.
These tasks do not constitute a general coding or multilingual benchmark.

## Judging and acceptance

Only complete, cold, correctly counted pairs are eligible. The existing blind
judge sends both answer orders to `mimo-v2.6-flash` through the previously
configured Xiaomi MiMo endpoint. The key is read from `~/.secret_ai_key` on
the workstation; it is not copied to the board or written to results. Only
public/synthetic task evidence and generated answers are sent.

For each model, require all six pairs and both judge orders, no new required-fact,
citation-marker or functional-code regression, mean MTP score no more than
0.25 below direct, and no individual mean pair loss above 0.5 on the 0–5 scale.
Shared baseline omissions are reported without labelling them MTP regressions.

The separate "useful in this pilot" flag additionally requires MTP mean score
at least 4/5, all candidate fact checks and functional-code tests passing,
and total paired task latency improving by more than 3% on both models.
Citation-marker omissions shared with the baseline remain explicit; they are
not a separate absolute blocker for this relative-quality experiment.
These thresholds are practical pilot criteria, not statistical noninferiority.
One judge cannot establish general semantic equivalence.

Report answer lengths, text identity, TTFT, total latency, decode throughput,
RSS and actual draft-acceptance counters. When answers differ in length, total
latency and per-token throughput answer different questions; retain both.
No inference default is changed automatically.

## Execution

Completed run: `mtp-quality-20261003-173915` on `musepipro-wg`.
Generation took 1 h 39 m 37 s; collection and recovered cloud scoring are
complete. See the [results](../reports/2026-10-03-mtp-usefulness-results.md).
The predeclared protocol below remains the description of the original run.
The earlier `mtp-quality-20261003-173545` and `mtp-quality-20261003-173723`
launches were stopped during runtime verification to correct judge evidence
and permit Python builtin `type()` in functional checks, before inference comparisons.

```bash
python3 spacemit/bench/test-mtp-quality.py
python3 spacemit/bench/start-mtp-quality.py
```

The launcher offloads board generation and local collection/scoring to tmux.
The board budget is six hours after a maximum one-hour lock wait; individual
requests have a 30-minute budget. Expected generation is roughly 1–2 hours,
based on observed rates and anticipated answer lengths; caps and lengths can
make it longer. This estimate will be replaced by observed progress.

The new run directory contains `run.json`, `phase`, `summary.json`, saved
documents/cases and readable answers. After collection, inspect
`quality-summary.md`, per-model comparisons/judgments and `collector-exit-status`:
0 means the pilot usefulness criteria cleared, 2 means completed review is
required, 1 means infrastructure or judging failed. Failed/incomplete requests
are retained. The collector verifies archive and individual artifact hashes.
