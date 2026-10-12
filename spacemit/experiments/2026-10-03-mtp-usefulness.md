# Checkpoint MTP: complete-answer usefulness pilot

Purpose: measure whether MTP retains useful answers while it reduces
latency. This measurement does not require the same wording or the same
token sequence as direct decoding. The pilot is separate from the failed
native RS rollback checks. It does not establish mathematical losslessness,
and it does not repair the RS path.

## Predeclared configuration

- Required Qwen3.5 2B/4B Q4_0 models; tested `a990751` build and recorded
  hashes.
- Four threads, F16 KV, batch/microbatch 32, wide attention, layout 0,
  routing 0. Both arms use the same routing, so the measured effect concerns
  MTP.
- Direct decoding versus checkpoint MTP, draft length 3, `SPINE_SPEC_RS=0`.
- Context 6144. Every request sends the same complete task input in both
  arms. Caching and context shifting are disabled. The runner checks the
  actual input counts.
- Natural stopping, with a 512-token cap for concise document answers and a
  1536-token cap for code and Chinese prose. A length-capped output is
  incomplete.
- Six tasks per model and one request per arm: **24 requests**. The order is
  direct→MTP on 2B and MTP→direct on 4B. MTP reverses the task order. This
  stage is a pilot, not replication.

## Tasks and independent checks

Three public-document/synthetic-evidence tasks use a complete ~2k fixture:
documented API routes, orion→maple→cedar→cobalt tracing, and 17+23+38
aggregation. All six evidence blocks remain present, and they are
distributed through the document. Both arms check the same known facts and
citation markers.

Two Python tasks require builtins-only functions: merge busy intervals and
find free windows, and Unicode run-length encoding and decoding. The runner
saves the code, and then it parses and executes the code in a child process.
The child has restricted builtins, restricted AST constructs, and CPU/memory
limits. The runner checks the code against deterministic edge cases and
generated test inputs. Imports, classes, file access, network access, and
runtime introspection are excluded from the task. Fenced source is accepted,
and invalid or rejected code is retained.

A Chinese prose task explains a supplied fictional shipping and refund
policy, and it gives examples. The runner checks the known facts, and then
both answers are cloud-scored against the exact source evidence. This task
also supplies a longer natural generation. These tasks do not make a general
coding or multilingual benchmark.

## Judging and acceptance

Only complete, cold, and correctly counted pairs are eligible. The existing
blind judge sends both answer orders to `mimo-v2.6-flash` through the
previously configured Xiaomi MiMo endpoint. The workstation reads the key
from `~/.secret_ai_key`. The key is not copied to the board, and it is not
written to results. The runner sends only public/synthetic task evidence and
generated answers.

For each model, require all six pairs and both judge orders. Require no new
required-fact, citation-marker, or functional-code regression. Require a mean
MTP score no more than 0.25 below direct, and no individual mean pair loss
above 0.5 on the 0–5 scale. The runner reports baseline omissions that are
shared, and it does not label them as MTP regressions.

The separate "useful in this pilot" flag needs three more conditions: an MTP
mean score of at least 4/5, all candidate fact checks and functional-code
tests passed, and total paired task latency improved by more than 3% on both
models. Citation-marker omissions that are shared with the baseline remain
explicit. They are not a separate absolute blocker for this relative-quality
experiment. These thresholds are practical pilot criteria. They are not
statistical noninferiority. One judge cannot establish general semantic
equivalence.

Report answer lengths, text identity, TTFT, total latency, decode throughput,
RSS, and actual draft-acceptance counters. When answers differ in length,
total latency and per-token throughput answer different questions. Retain
both values. No inference default changes automatically.

## Execution

Completed run: `mtp-quality-20261003-173915` on `musepipro-wg`.
Generation took 1 h 39 m 37 s. Collection and recovered cloud scoring are
complete. See the [results](../reports/2026-10-03-mtp-usefulness-results.md).
The predeclared protocol above remains the description of the original run.
The earlier `mtp-quality-20261003-173545` and `mtp-quality-20261003-173723`
launches were stopped during runtime verification. That stop corrected judge
evidence and permitted the Python builtin `type()` in functional checks,
before the inference comparisons.

```bash
python3 spacemit/bench/test-mtp-quality.py
python3 spacemit/bench/start-mtp-quality.py
```

The launcher offloads board generation and local collection/scoring to tmux.
The board budget is six hours after a maximum one-hour lock wait. Individual
requests have a 30-minute budget. Expected generation is roughly 1–2 hours,
based on observed rates and anticipated answer lengths. Caps and lengths can
make it longer. Observed progress will replace this estimate.

The new run directory contains `run.json`, `phase`, `summary.json`, saved
documents and cases, and readable answers. After collection, inspect
`quality-summary.md`, the per-model comparisons and judgments, and
`collector-exit-status`. Exit status 0 means that the pilot usefulness
criteria cleared. Exit status 2 means that a completed review is necessary.
Exit status 1 means that infrastructure or judging failed. The run retains
failed and incomplete requests. The collector verifies the archive and every
individual artifact hash.
