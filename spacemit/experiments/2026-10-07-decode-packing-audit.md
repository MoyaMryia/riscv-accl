# Sustained decode profiling and FFN activation-packing audit

Status: completed and independently verified in 24.43 minutes. See the
[measured results](../reports/2026-10-07-decode-packing-results.md).
Duplicate FFN packing is 0.024–0.035% of audited GEMM worker elapsed. This
share does not justify a shared-packing implementation. The audit claims no
optimization speedup. The initial run passed native identity but failed the
profile clock audit. See the [verified repair](../reports/2026-10-07-decode-clock-repair.md).

Run: `k1-decode-audit-20261007-074314`. Direct SSH: `musepipro`.
Board directory: `/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-decode-audit-20261007-074314`.
Local artifacts: `spacemit/reports/raw/k1-decode-audit-20261007-074314`.

## Question and baseline

Does sustained decode spend enough work on the packing of the same
activation for the FFN gate and up branches? Is that work enough to justify
explicit per-execution sharing? Which CPU functions and synchronization
paths dominate decode after the route-3 staging bypass? The earlier prefill
profile cannot answer this decode question.

The control is the preserved route-3 CPU library from
`k1-gemm-routing-20261003-005740`, and the runner checks its library and
original object hashes. The source is the pinned `a990751` snapshot with the
existing wide RVV changes. A private library adds counters around existing
calls. Neither arm changes matrix arithmetic, weights, quantization,
attention layout, or worker count. MTP is off. This experiment does not
enable the optional hybrid SSM graph.

## Declared diagnostic

1. Compare the route-3 baseline, the instrumented-library audit-off arm, and
   the audit-on arm: 104 production graph cases each. Include M tails, real
   weight repacking, the Q8 fallback, unchanged inputs, and output/scratch
   guards.
2. Run Qwen3.5-2B/4B Q4_0 at cold prompt lengths 256 and 2,048, with four
   workers, batch/microbatch 32, context 4,096, F16 KV, wide RVV attention,
   optional model warmup disabled in both arms, seed 42, and temperature
   zero. Generate exactly 65 capped tokens, and ignore EOS.
3. For each model and length, first profile the uninstrumented route-3
   library. Use `cpu-clock:u`, explicit CLOCK_MONOTONIC, 199 Hz, and
   frame-pointer stacks. Recording starts only after the receipt of the
   first streamed token, and it ends after the final event. Saved timestamps
   check that the samples belong to this decode window. Require at least
   100 samples and no lost events. Pipeline overlap can omit part of the
   first decode execution. The profile is not a prefill measurement.
4. In a separate matched cold request, record GEMM worker durations for
   activation quantization, staging copies, GEMM, grid waits, and pair
   waits. Record weight and activation names, M/N/K, input address,
   monotonic start time, and packed input bytes. The server log preserves
   every counter. The server inventories its obligatory M=2 compatibility
   test separately, before health readiness. Exclude only the startup M=1/2
   records that finish before readiness. All other records must start inside
   the measured request, and the runner rejects gap records. Verify clocks,
   section bounds, four workers, and the route-3 buffer bypass. Require
   complete token IDs, full cold prompt telemetry, and exact prompt, token,
   and text identity across the pair.
5. Align worker executions before you trim the first-token boundary. Match
   only adjacent complementary gate/up branches of the same layer that have
   equal input address, activation name, shape, and worker count. Each
   execution can participate in one pair only. Report the summed packing
   work of the smaller branch as a diagnostic priority signal. That signal
   is not a cache proof and not a lifetime proof.

The plan includes eight model requests and four decode profiles. Board
execution and verified collection run in tmux. The board job has a four-hour
execution bound after it acquires the shared benchmark lock. The collector
has a 24-hour bound. The runner checks the archive file list, the archive
checksum, every extracted artifact hash, and the staged Python/shell/C++
code hashes. It collects native dumps as `.data`.

## Following implementation gates

An exploratory priority signal is a smaller-branch packing work of at least
3% of audited decode GEMM worker elapsed in a measured case. That share is
not an expected 3% wall-time improvement, and it does not qualify an
optimization. Worker waits overlap, section clocks and logging perturb
execution, and non-GEMM work is absent from the denominator. Inspect the
absolute cost and the uninstrumented CPU profile before you decide. Inspect
also the prefill counters when you compare priorities.

If the evidence supports sharing, implement explicit paired execution, with
scratch that the execution owns. Retain the existing quantizer, scales,
weight layouts, both matrix outputs, and unsupported-path fallbacks. Never
reuse scratch by tensor pointer across graph executions: arena addresses
recur. Audit graph, state, and scratch lifetimes. Then use native
correctness, repeated operator timing, and matched cold model ABBA gates.
The benefit must exceed both 3% and the measured control spread, with no
clear regression. Only an advancing candidate proceeds to complete
naturally stopped answers, held-out facts and code checks, and two-order
cloud judging.

If packing is small, use the measured decode profile and the source to
investigate dispatch, synchronization, or another supported bottleneck. Do
not infer removable wall time from sampled CPU shares. Do not reinterpret a
negative gate as a defect.

## Monitoring and commands

The completed follow-up checked roughly every 30 minutes, and it remained
quiet while healthy. It is now paused. The follow-up diagnosed and repaired
technical faults. A repaired inference rerun gets a fresh directory and a
new monitor. Prior evidence and gates remain intact. Collection-only
recovery never restarts inference.

```bash
python3 spacemit/bench/start-k1-decode-audit.py --board musepipro
python3 spacemit/bench/start-k1-decode-audit.py --collect-only \
  --run-dir spacemit/reports/raw/k1-decode-audit-20261007-074314
python3 spacemit/bench/test-k1-decode-audit.py
```

No default changes. Capped throughput, CPU attribution, overlapping worker
elapsed, and complete useful-answer speed are separate evidence categories.
