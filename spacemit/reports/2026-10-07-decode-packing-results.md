# Sustained decode and FFN packing results

Date: October 7, 2026, Asia/Singapore. Run:
`k1-decode-audit-20261007-074314`. Status: **completed and independently
verified**. The board and collector exit statuses are zero. The board execution
took 24.43 minutes. The
[protocol](../experiments/2026-10-07-decode-packing-audit.md) and the
[clock/startup repair](2026-10-07-decode-clock-repair.md) describe this
isolated route-3 diagnostic. No production default changed.

## Decision

Do not implement a shared FFN activation packing for the measured decode
workloads. The duplicate branch costs only **0.024–0.035% of audited GEMM
worker elapsed**. That value is well below the declared 3% exploratory
priority signal. The duplicate exists, but it is not a significant cost in this
configuration. We introduced no paired operator and no pointer cache. The
candidate operator, model, and complete-answer stages therefore did not run.

A source and thread-level review also rejects a treatment of the approximately
20% SPERT `sync_impl` CPU share as removable inference latency. Every sample at
that leaf belongs to the calling thread, not to a computing worker. The
synchronous dispatch waits for the four workers to finish the graph. Its CPU
occupancy does not show that the workers could complete the graph sooner, if
that wait were removed.

## Verification

- 104 production graph cases in each of the baseline, audit-off, and audit-on
  arms. All three collected output dumps match exactly. The real weight
  repacking, the M tails, the Q8 fallback, the input preservation, and the
  output/scratch guards pass.
- Eight complete cold requests: two arms for 2B/4B, at 256 and 2,048 prompt
  tokens. Each request generates all 65 requested capped tokens. All four
  pairs match exactly in the prompt IDs, the full output token IDs, and the
  text. All four pairs report zero prompt reuse.
- Four decode profiles: explicit CLOCK_MONOTONIC, a first-token enable
  boundary, verified sample windows, 14,051 to 40,811 samples, and no lost
  events.
- All request counters reproduce the saved attribution summaries. The startup
  compatibility checks are separate: 748 records per 2B arm, and 996 per 4B
  arm. Only the M=1/2 invocations that finish before health readiness can be
  excluded. The request/gap clock and the timing-section checks remain
  strict.
- The archive checksum, the exact archive file list, and **86 artifact hashes**
  are verified. Eleven staged code hashes and three frozen collector hashes
  pass. We independently rechecked the remote source, both CPU libraries, and
  the staged code.

The independent
[verification script](raw/k1-decode-analysis-20261007/verify-completion.py)
and [output](raw/k1-decode-analysis-20261007/verification.json) are additional
derived evidence. They are outside the 86-file board receipt.

## Measured rates and packing cost

The rates below come from one **profiled baseline request per case**. They are
not a speedup comparison. The counter request is separate, because the logging
and the section clocks perturb the timing. The model weights, the quantizer,
the matrix arithmetic, the full vocabulary, and the route-3 bypass are
unchanged. The batch and microbatch are 32. The four workers, the F16 KV, the
context 4,096, the wide RVV attention, the seed 42, and the temperature zero
are fixed. The optional warmup is disabled in both arms. The compulsory
compatibility probe of the server still runs before readiness, and it does not
enter these request totals.

| Model / prompt | Prefill tokens/s | Decode tokens/s | All activation packing, decode | Duplicate FFN branch | Duplicate branch summed worker time |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2B / 256 | 24.67 | 4.49 | 0.344% | 0.0327% | 16.10 ms |
| 2B / 2,048 | 23.55 | 3.80 | 0.360% | 0.0352% | 17.39 ms |
| 4B / 256 | 9.82 | 2.08 | 0.279% | 0.0251% | 24.95 ms |
| 4B / 2,048 | 9.24 | 1.57 | 0.279% | 0.0240% | 23.83 ms |

Both packing columns divide the summed section durations by the **summed GEMM
worker elapsed**, which overlaps across the workers. They are not wall-time
percentages. The duplicate time covers all the measured pairs, not one token.
The total activation packing in prefill accounts for 2.07–2.13% on 2B and for
1.56–1.59% on 4B, of the corresponding GEMM worker denominator. This result
does not establish a useful prefill fusion gain.

The audit identifies 1,536 adjacent same-input gate/up pairs per 2B request
(24 layers × 64 decode steps), and 2,048 per 4B request (32 × 64). The smaller
branch packs 12 MiB and 20 MiB of F32 input across those pairs. This result is
an input byte count, not measured DDR traffic. All the route-3 request counters
report zero staging-copy bytes and a zero TCM buffer size.

## Decode CPU attribution and source interpretation

| Model / prompt | Two resolved IME labels, self CPU | Calling-thread `sync_impl`, self CPU | Worker `barrier_coro`, self CPU | Attention visible stacks |
| --- | ---: | ---: | ---: | ---: |
| 2B / 256 | 66.57% | 20.01% | 4.73% | 0.72% |
| 2B / 2,048 | 56.03% | 20.07% | 4.90% | 6.36% |
| 4B / 256 | 62.60% | 20.04% | 6.84% | 1.63% |
| 4B / 2,048 | 48.61% | 20.06% | 5.41% | 10.41% |

`nm -anC` resolves `LOOP_K360` at `0x148720` and `LOOP_INNER360` at
`0x148786`, inside `spacemit_kernels::ime1::gemm_kernel_i8i4`. That symbol
starts at `0x147f1e`, in the preserved route-3 library. Missing stack frames
place these assembly leaves in the automatic `other_or_unattributed` bucket.
That bucket does not mean that the matrix work disappeared. The self shares use
disjoint sampled leaves. The visible attention stacks are lower bounds, where
the callers are missing. Do not add them to the overlapping stack categories,
and do not interpret them as wall savings.

The output head (`token_embd.weight`) accounts for 21.84% of the audited decode
GEMM worker elapsed on 2B, and for 13.58–13.62% on 4B. Its packing component is
tiny. That head is a substantial matrix workload. It is not permission to prune
the vocabulary: every output logit remains part of the test.

The exact adapter source hash is
`0a101c364aab377cd9f6510421f5540c784de0ed8d8de87ed2f2506dd7bb7294`.
`spacemit_spert_launch_graph_kernel()` acquires a stream, dispatches the whole
graph synchronously, and releases that stream afterwards. A permanent checkout
of that stream would change the core ownership, and it can starve the other
backends. The graph callback synchronizes after the compute nodes. The
operators use barriers also for the publication of the packed scratch. A blind
removal of either wait breaks the completion and dependency contract. The
worker barrier share identifies work that needs a more precise attribution. It
is not a proven safe deletion.

## Supported next action and limitations

The next defensible performance screen targets the **M=1 Q4_0/IME hot
kernel**, at the K32 packing. It includes the FFN widths and the full
248,320-column output head. Inspect the exact generated instruction sequence.
Then compare a minimal load and branch scheduling candidate against the
unchanged kernel. This work is distinct from the previously rejected M4 prefill
scheduling variants. Require exact native tails, guards, and fallback outputs,
and repeated concurrent production-operator measurements, before any cold model
ABBA timing. This diagnostic has implemented and qualified no such M1
candidate. A worker-barrier and node attribution is a second investigation
target, if a safe dependency-preserving change exists.

This run claims no new acceleration. Capped requests cannot establish a
naturally complete useful-answer speed or quality. These eight runs add no
cloud grades, and they do not alter the previously recorded shared answer
failures. One pair per case is not a statistical-equivalence test. We have not
established the hardware limit. This diagnostic campaign is complete, and its
follow-up is paused.
