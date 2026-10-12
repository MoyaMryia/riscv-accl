# Staged validation of long context and MTP

This protocol follows the [research review](../reports/2026-10-03-validation-practice.md).
The run completed. See the [results and retained gates](../reports/2026-10-03-staged-validation-results.md).

Completed run: `k1-validation-20261003-124720`, launched on October 3 at 12:47
Asia/Singapore. Board tmux: `k1_validation_k1-validation-20261003-124720`.
Local collector tmux: `k1_validation_collect_k1-validation-20261003-124720`.
The [run manifest](../reports/raw/k1-validation-20261003-124720/run.json)
records the staged code hashes and the remote directory. Execution took
4.16 hours. The overall acceptance gate did not clear, and 4B/32k was
skipped.

## Fixed configuration

SpaceMiT fork `a990751` with the recorded wide attention modifications, and
the verified isolated GEMM routing binary from
`k1-gemm-routing-20261003-005740`. Qwen3.5 2B/4B Q4_0, F16 KV, four threads,
batch/microbatch 32, CPU inference, wide attention enabled, and attention
layout 0. The runner checks source, runtime, model, and candidate binary
hashes before execution. It copies the candidate library into the new run
directory, and the default source/build settings do not change.

## Schedule and acceptance

1. **Native recurrent-state checks, both models.** Compare full vocabulary
   logits in two fresh contexts with identical shapes. Test full restore
   into fresh contexts and into used contexts, and test partial restore into
   contexts with the matching attention prefix. Check RS=0 and RS=3,
   whole-batch rollback of one and three tokens around positions 31/32/33,
   and repeated rollback. Require finite, bitwise-equal same-shape replay.
   Record argmax, maximum absolute error, and normalized squared error. A
   refused removal is unsupported. It is never a pass. Sequence isolation and
   stochastic distribution tests remain future coverage.
2. **Forced-trajectory diagnosis, both models.** Adapt the existing perfect
   draft probe to this fork, to F16 KV, and to batch 32. Generate 512 tokens
   from the frozen historical 128-token code fixture. Then replay its
   identical token history with M=1 and M=3. The M=1 top-two comparison must
   match exactly. M=3 shifts and flips are diagnostic. Decimal output uses
   nine significant digits to preserve FP32 values. Full-vocabulary
   comparisons occur in stage 1.
3. **End-to-end MTP, both models.** Replicate 512-output direct,
   checkpoint-MTP, and RS-MTP requests with identical frozen inputs. Record
   the first differing token, hashes, completion counts, and diagnostic
   timing. These fixed-length outputs are not complete-answer quality
   measurements. The runner records MTP failures independently, and they do
   not suppress direct-routing tests.
4. **Combined routing at actual 8192 input tokens, both models.** Run mode
   0/3/3/0 with 64 outputs per request, context 12288, cold prompts, and
   context shifting disabled. Require identical input/output hashes and exact
   completion counts. Each phase must improve beyond max(3%, baseline range)
   with no clear regression. Two requests per arm are an engineering pilot.
5. **Full-document usefulness, both models.** Build a roughly 4096-token
   fixture with unmodified public documentation filler and all six labelled
   evidence blocks. Select three declared tasks: documented API routes,
   three-link tracing (orion → maple → cedar → cobalt), and aggregation of
   receipts (17+23+38=78). Links and receipts occur at the beginning, in the
   middle, and at the end. Mode 0 runs the three tasks in order, and mode 3
   reverses the task order. Every request sends the complete same document.
   It disables cache reuse, uses a 512 output cap, and must stop naturally
   with no reasoning output. Check required facts and citations, and report
   baseline limitations and candidate regressions. This stage is a declared
   pilot. It is not a RULER or LongBench score. No cloud judge is necessary
   for these deterministic facts. Different text alone is not a failure.
6. **Conditional 4B/32k feasibility.** Only after both routing and quality
   gates clear, run one mode-3 request with exactly 32768 input tokens and
   64 output tokens, context 33792, no shifting, and a five-hour request
   budget. Require 10 GiB available before the start. Abort below 2 GiB, or
   if swap is in use. Record RSS, system headroom, swap counters, hashes, and
   completion. This stage demonstrates fixed-length feasibility only. It is
   not 32k acceleration and not answer usefulness. A timeout means
   incomplete within this budget. 64k is not scheduled.

The board driver owns the shared benchmark lock and a 12-hour overall budget.
It terminates every server after its stage, and the timeout cleanup includes
the process group. A workstation tmux collector waits independently. It
retrieves compressed artifacts, verifies every collected file hash, and
recomputes the completed gates. The collector sends no messages and does not
change report claims automatically.

## Commands

```bash
python3 spacemit/bench/test-k1-validation.py
python3 spacemit/bench/start-k1-validation.py
```

The launcher prints its board/collector tmux sessions and its local results
directory. Inspect `phase`, `summary.json`, `driver.log`, and, after
collection, `verification.json` in that directory. Recheck the collected
artifacts with:

```bash
python3 spacemit/bench/verify-k1-validation.py spacemit/reports/raw/RUN_NAME
```

The 12-hour bound is a safety limit. It is not an ETA. Completion depends on
the measured long-context cost and on whether the 32k gate opens. The run
retains early failures and skips.
