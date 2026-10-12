# Decode diagnostic clock repair

The initial run `k1-decode-audit-20261007-070430` stopped after 311.27 seconds,
with `perf samples outside declared decode window`. The board and the collector
both recorded exit status 1. The failed evidence remains unchanged.

## Verified evidence before failure

- The baseline, the audit-off arm, and the audit-on arm each passed 104
  production graph cases. All three collected native dumps have SHA-256
  `e31997719879fb9a858f9e970af7e11ceb68124657d41c53bd3b3f82c4dbd4dc`.
- The first 2B/256 cold request generated all 65 requested tokens, with zero
  prompt reuse and the expected 256-token prompt. It reported 24.63 prompt
  tokens/s and 4.49 generated tokens/s. This request is a single profiled,
  capped diagnostic request. It is not an optimization or a useful-answer
  comparison.
- We independently checked the failed archive checksum, the exact archive file
  list, the 28 artifact hashes, the 11 staged source hashes, and the three
  frozen collector hashes. The collector verified also the remote staged
  hashes.

## Cause and supported repair

The initial perf recording contains 14,081 samples. Its timestamp range was
806515.630770 to 806530.108252 seconds. But the monotonic control window of
Python began at 806538.198222 seconds. These values are from different clock
domains.

A separate two-second busy-process probe recorded 398 samples per arm:

| Clock setting | Monotonic minus raw clock | Samples inside the monotonic control window |
| --- | ---: | --- |
| perf default | 22.620471488 s | No |
| `perf record --clockid mono` | 22.620563775 s | Yes, all 398 |

The probe establishes that the default recording clock and the Python
monotonic clock do not align on this board. The repair selects CLOCK_MONOTONIC
explicitly in perf. It retains the original one-millisecond boundary tolerance
and the sample count and loss gates. It does not translate the timestamps by a
fitted offset.

The revised matched run disables also the optional empty-run warmup of the
server, in both arms. A targeted model probe then exposed a separate harness
issue: the server performs an M=2 context-removal compatibility test before it
becomes healthy, even with `--no-warmup`. The source calls
`common_context_can_seq_rm()` in `tools/server/server-context.cpp`. Its
implementation in `common/common.cpp` evaluates two tokens and clears memory.
The first short probe preserved 748 startup records separately. They are
identifiable before the request, and they accompanied 49,364 request records.

The harness now records the health-readiness time. It classifies only the M=1/2
invocations that finish before that timestamp as startup evidence. All the
remaining records must begin inside the measured request. A record in the
readiness/request gap remains an error. The run preserves the startup records
and reports them separately. Those records do not enter the prefill/decode or
the duplicate-packing totals. Seven regression checks pass, including the
rejection of the gap records. Full cold-input telemetry and output identity
remain necessary.

Probe evidence:
`raw/k1-decode-clock-probe-20261007-0740/summary.json`. The targeted matched
model probe and the subsequent fresh campaign are recorded in
`raw/k1-decode-packing-campaign.json`. This repair qualifies no shared-packing
candidate and no speedup.

## Repair validation and current run

The passing short model probe
(`k1-decode-validation-probe-20261007-0750`) generated a complete 65-token
audit response, at a 32-token cold prompt. It matched the saved repaired
profile response exactly in the prompt IDs, the token IDs, and the text. The
profile had 13,739 samples inside the explicit monotonic window. The counter
analysis passed 1,536 adjacent gate/up pairs, 64 per layer across 24 layers. It
reported 16.72 ms of smaller-branch summed packing work over those pairs, or
0.0332% of the audited single-row GEMM worker elapsed. This tiny short-probe
fraction does not qualify the sharing. We must still interpret the full
four-case diagnostic. The fraction is not a wall-time savings estimate.

We independently checked the failed and the passing model-probe archives
against their exact file lists, the archive checksums, and all 21 and 11
artifact hashes. The passing probe reuses the preceding profile request as its
control. Its counter response is new. This test is a targeted repair
validation. It is not a model timing comparison and not the full
256/2,048-token matrix.

The fresh full run `k1-decode-audit-20261007-074314` was dispatched at 07:43
Asia/Singapore, in board and collector tmux, through direct SSH `musepipro`.
The replacement monitor `k1-decode-packing-20261007-074314` is active every 30
minutes, and the original monitor is paused. We retain the previous failed
artifacts and the baseline hashes.
