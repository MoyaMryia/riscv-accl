# Decode diagnostic clock repair

The initial run `k1-decode-audit-20261007-070430` stopped after 311.27 seconds
with `perf samples outside declared decode window`. Both board and collector
recorded exit status 1. Its failed evidence remains unchanged.

## Verified evidence before failure

- Baseline, audit-off and audit-on each passed 104 production graph cases.
  All three collected native dumps have SHA-256
  `e31997719879fb9a858f9e970af7e11ceb68124657d41c53bd3b3f82c4dbd4dc`.
- The first 2B/256 cold request generated all 65 requested tokens, with zero
  prompt reuse and the expected 256-token prompt. It reported 24.63 prompt
  tokens/s and 4.49 generated tokens/s. This is a single profiled, capped
  diagnostic request, not an optimization or useful-answer comparison.
- The failed archive checksum, exact archive file list, 28 artifact hashes,
  11 staged source hashes and three frozen collector hashes were independently
  checked. Remote staged hashes were also verified by the collector.

## Cause and supported repair

The initial perf recording contains 14,081 samples. Its timestamp range was
806515.630770–806530.108252 seconds, while Python's monotonic control window
began at 806538.198222 seconds. These are different clock domains.

A separate two-second busy-process probe recorded 398 samples per arm:

| Clock setting | Monotonic minus raw clock | Samples inside the monotonic control window |
| --- | ---: | --- |
| perf default | 22.620471488 s | No |
| `perf record --clockid mono` | 22.620563775 s | Yes, all 398 |

The probe establishes that the default recording clock and Python's monotonic
clock do not align on this board. The repair explicitly selects CLOCK_MONOTONIC
in perf. It retains the original one-millisecond boundary tolerance and sample
count/loss gates; it does not translate timestamps by a fitted offset.

The revised matched run also disables the server's optional empty-run warmup
in both arms. The targeted model probe then exposed a separate harness issue:
the server performs an M=2 context-removal compatibility test before becoming
healthy even with `--no-warmup`. The source calls
`common_context_can_seq_rm()` in `tools/server/server-context.cpp`; its
implementation in `common/common.cpp` evaluates two tokens and clears memory.
The first short probe preserved 748 startup records separately identifiable
before the request, alongside 49,364 request records.

The harness now records health-readiness time. It classifies only M=1/2
invocations that finish before that timestamp as startup evidence. All remaining
records must begin within the measured request; a record in the readiness/request
gap remains an error. Startup records are preserved and reported separately,
and do not enter prefill/decode or duplicate-packing totals. Seven regression
checks pass, including rejection of gap records. Full cold-input telemetry and
output identity remain required.

Probe evidence: `raw/k1-decode-clock-probe-20261007-0740/summary.json`.
The targeted matched model probe and subsequent fresh campaign are recorded in
`raw/k1-decode-packing-campaign.json`. No shared-packing candidate or speedup is
qualified by this repair.

## Repair validation and current run

The passing short model probe (`k1-decode-validation-probe-20261007-0750`)
generated a complete 65-token audit response at a 32-token cold prompt and
matched the saved repaired profile response exactly in prompt IDs, token IDs
and text. The profile had 13,739 samples inside the explicit monotonic window.
The counter analysis passed 1,536 adjacent gate/up pairs, 64 per layer across
24 layers. It reported 16.72 ms of smaller-branch summed packing work over
those pairs, or 0.0332% of audited single-row GEMM worker elapsed. This tiny
short-probe fraction does not qualify sharing; the full four-case diagnostic
must still be interpreted. It is not a wall-time savings estimate.

The failed and passing model-probe archives were independently checked against
their exact file lists, archive checksums and all 21 / 11 artifact hashes.
The passing probe reuses the preceding profile request as its control; its
counter response is new. This is targeted repair validation, not a model timing
comparison or the full 256/2,048-token matrix.

Fresh full run `k1-decode-audit-20261007-074314` was dispatched at 07:43
Asia/Singapore in board and collector tmux through direct SSH `musepipro`.
Replacement monitor `k1-decode-packing-20261007-074314` is active every 30 minutes;
the original monitor is paused. Previous failed artifacts and baseline hashes
are retained.
