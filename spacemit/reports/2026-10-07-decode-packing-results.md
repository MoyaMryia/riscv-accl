# Sustained decode and FFN packing results

Date: October 7, 2026, Asia/Singapore. Run:
`k1-decode-audit-20261007-074314`. **Completed and independently verified.**
Board and collector exit statuses are zero. Board execution took 24.43 minutes.
The [protocol](../experiments/2026-10-07-decode-packing-audit.md) and
[clock/startup repair](2026-10-07-decode-clock-repair.md) describe the isolated
route-3 diagnostic. No production default changed.

## Decision

Do not implement shared FFN activation packing for the measured decode workloads.
The duplicate branch costs only **0.024–0.035% of audited GEMM worker elapsed**,
well below the declared 3% exploratory priority signal. The duplicate exists,
but it is not a significant cost in this configuration. No paired operator or
pointer cache was introduced. Candidate operator/model/complete-answer stages
were therefore not run.

Source and thread-level review also rejects treating the approximately 20%
SPERT `sync_impl` CPU share as removable inference latency. Every sample at
that leaf belongs to the calling thread, not a computing worker. The synchronous
dispatch waits for four workers to finish the graph. Its CPU occupancy does not
show that workers could complete the graph sooner if that wait were removed.

## Verification

- 104 production graph cases in each baseline/audit-off/audit-on arm; all three
  collected output dumps match exactly. Real weight repacking, M tails, Q8
  fallback, input preservation and output/scratch guards pass.
- Eight complete cold requests: two arms for 2B/4B at 256 and 2,048 prompt tokens.
  Each generates all 65 requested capped tokens. All four pairs match exactly
  in prompt IDs, full output token IDs and text. All report zero prompt reuse.
- Four decode profiles: explicit CLOCK_MONOTONIC, first-token enable boundary,
  verified sample windows, 14,051–40,811 samples, and no lost events.
- All request counters reproduce the saved attribution summaries. Startup
  compatibility checks are separate: 748 records per 2B arm and 996 per 4B arm.
  Only M=1/2 invocations finishing before health readiness can be excluded;
  request/gap clock and timing-section checks remain strict.
- Archive checksum, exact archive file list and **86 artifact hashes** verified.
  Eleven staged code hashes and three frozen collector hashes pass; remote
  source, both CPU libraries and staged code were independently rechecked.

The independent [verification script](raw/k1-decode-analysis-20261007/verify-completion.py)
and [output](raw/k1-decode-analysis-20261007/verification.json) are additional
derived evidence, outside the 86-file board receipt.

## Measured rates and packing cost

The rates below are from one **profiled baseline request per case**, not a
speedup comparison. The counter request is separate because logging and section
clocks perturb timing. The model weights, quantizer, matrix arithmetic, full
vocabulary and route-3 bypass are unchanged. Batch/microbatch is 32; four workers,
F16 KV, context 4,096, wide RVV attention, seed 42 and temperature zero are fixed.
Optional warmup is disabled in both arms; the server's compulsory compatibility
probe still runs before readiness and does not enter these request totals.

| Model / prompt | Prefill tokens/s | Decode tokens/s | All activation packing, decode | Duplicate FFN branch | Duplicate branch summed worker time |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2B / 256 | 24.67 | 4.49 | 0.344% | 0.0327% | 16.10 ms |
| 2B / 2,048 | 23.55 | 3.80 | 0.360% | 0.0352% | 17.39 ms |
| 4B / 256 | 9.82 | 2.08 | 0.279% | 0.0251% | 24.95 ms |
| 4B / 2,048 | 9.24 | 1.57 | 0.279% | 0.0240% | 23.83 ms |

Both packing columns divide summed section durations by **summed GEMM worker
elapsed**, which overlaps across workers. They are not wall-time percentages.
Duplicate time covers all measured pairs, not one token. All activation packing
in prefill accounts for 2.07–2.13% on 2B and 1.56–1.59% on 4B of the corresponding
GEMM worker denominator; this does not establish a useful prefill fusion gain.

The audit identifies 1,536 adjacent same-input gate/up pairs per 2B request
(24 layers × 64 decode steps) and 2,048 per 4B request (32 × 64). The smaller
branch packs 12 MiB / 20 MiB of F32 input across those pairs. This is input
byte counting, not measured DDR traffic. All route-3 request counters report
zero staging-copy bytes and zero TCM buffer size.

## Decode CPU attribution and source interpretation

| Model / prompt | Two resolved IME labels, self CPU | Calling-thread `sync_impl`, self CPU | Worker `barrier_coro`, self CPU | Attention visible stacks |
| --- | ---: | ---: | ---: | ---: |
| 2B / 256 | 66.57% | 20.01% | 4.73% | 0.72% |
| 2B / 2,048 | 56.03% | 20.07% | 4.90% | 6.36% |
| 4B / 256 | 62.60% | 20.04% | 6.84% | 1.63% |
| 4B / 2,048 | 48.61% | 20.06% | 5.41% | 10.41% |

`nm -anC` resolves `LOOP_K360` at `0x148720` and `LOOP_INNER360` at `0x148786`
inside `spacemit_kernels::ime1::gemm_kernel_i8i4`, whose symbol starts at
`0x147f1e`, in the preserved route-3 library. Missing stack frames place these
assembly leaves in the automatic `other_or_unattributed` bucket; that bucket
does not mean matrix work disappeared. Self shares use disjoint sampled leaves.
Visible attention stacks are lower bounds where callers are missing; do not
add them to overlapping stack categories or interpret them as wall savings.

The output head (`token_embd.weight`) accounts for 21.84% of audited decode
GEMM worker elapsed on 2B and 13.58–13.62% on 4B. Its packing component is tiny.
That is a substantial matrix workload, not permission to prune vocabulary:
every output logit remains part of the test.

The exact adapter source hash is
`0a101c364aab377cd9f6510421f5540c784de0ed8d8de87ed2f2506dd7bb7294`.
`spacemit_spert_launch_graph_kernel()` acquires a stream, synchronously dispatches
the whole graph and releases that stream afterward. Keeping it permanently
checked out would change core ownership and can starve other backends. The
graph callback synchronizes after compute nodes; operators also use barriers
for packed scratch publication. Blindly removing either wait breaks the
completion/dependency contract. The worker barrier share identifies work to
attribute more precisely, not a proven safe deletion.

## Supported next action and limitations

The next defensible performance screen targets the **M=1 Q4_0/IME hot kernel**
at K32 packing, including FFN widths and the full 248,320-column output head.
Inspect the exact generated instruction sequence, then compare a minimal load/
branch scheduling candidate with the unchanged kernel. This is distinct from
the previously rejected M4 prefill scheduling variants. Require exact native
tails/guards/fallback outputs and repeated concurrent production-operator
measurements before cold model ABBA timing. No such M1 candidate has been
implemented or qualified by this diagnostic. Worker-barrier/node attribution
is a second investigation target if a safe dependency-preserving change exists.

No new acceleration is claimed. Capped requests cannot establish naturally
complete useful-answer speed or quality. These eight runs add no cloud grades
and do not alter the previously recorded shared answer failures. One pair per
case is not a statistical-equivalence test. The hardware limit has not been
established. This diagnostic campaign is complete; its follow-up is paused.
