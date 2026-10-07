# Sustained decode profiling and FFN activation-packing audit

Status: completed and independently verified in 24.43 minutes. See the
[measured results](../reports/2026-10-07-decode-packing-results.md).
Duplicate FFN packing is 0.024–0.035% of audited GEMM worker elapsed and does
not justify a shared-packing implementation. No optimization speedup is claimed.
The initial run passed native identity
but failed the profile clock audit; see the
[verified repair](../reports/2026-10-07-decode-clock-repair.md).

Run: `k1-decode-audit-20261007-074314`. Direct SSH: `musepipro`.
Board directory: `/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-decode-audit-20261007-074314`.
Local artifacts: `spacemit/reports/raw/k1-decode-audit-20261007-074314`.

## Question and baseline

Does sustained decode spend enough work packing the same activation for the
FFN gate and up branches to justify explicit per-execution sharing? Which CPU
functions and synchronization paths dominate decode after route-3 staging bypass?
The earlier prefill profile cannot answer this decode question.

The control is the preserved route-3 CPU library from
`k1-gemm-routing-20261003-005740`, with its library and original object hashes
checked. Source is the pinned `a990751` snapshot with the existing wide RVV
changes. A private library adds counters around existing calls. Neither arm
changes matrix arithmetic, weights, quantization, attention layout or worker count.
MTP is off; this experiment does not enable the optional hybrid SSM graph.

## Declared diagnostic

1. Compare route-3 baseline, instrumented-library audit-off and audit-on native
   dumps: 104 production graph cases each, including M tails, real weight
   repacking, Q8 fallback, unchanged inputs and output/scratch guards.
2. Run Qwen3.5-2B/4B Q4_0 at cold prompt lengths 256 and 2,048, four workers,
   batch/microbatch 32, context 4,096, F16 KV, wide RVV attention, optional
   model warmup disabled in both arms, seed 42 and
   temperature zero. Generate exactly 65 capped tokens with EOS ignored.
3. For each model/length, first profile the uninstrumented route-3 library using
   `cpu-clock:u`, explicit CLOCK_MONOTONIC, 199 Hz and frame-pointer stacks. Recording starts only after
   receipt of the first streamed token. It ends after the final event. Saved
   timestamps check that samples belong to this decode window; require at least
   100 samples and no lost events. Pipeline overlap can omit part of the first
   decode execution. The profile is not a prefill measurement.
4. In a separate matched cold request, record GEMM worker durations for activation
   quantization, staging copies, GEMM, grid waits and pair waits. Record weight and
   activation names, M/N/K, input address, monotonic start time and input bytes
   packed. The server log preserves every counter. The server's obligatory M=2
   compatibility test before health readiness is inventoried separately; only
   startup M=1/2 records that finish before readiness can be excluded. Other
   records must start inside the measured request, with gap records rejected.
   Verify clocks, section bounds,
   four workers and route-3 buffer bypass. Require complete token IDs, full cold
   prompt telemetry and exact prompt/token/text identity across the pair.
5. Align worker executions before trimming the first-token boundary. Match only
   adjacent complementary gate/up branches of the same layer with equal
   input address, activation name, shape and worker count. Each execution can
   participate in only one pair. Report the smaller branch's summed packing work
   as a diagnostic priority signal; it is not a cache or a lifetime proof.

Eight model requests and four decode profiles are planned. Board execution and
verified collection are in tmux. The board job has a four-hour execution bound
after acquiring the shared benchmark lock. The collector has a 24-hour bound.
Archive file list, archive checksum, every extracted artifact hash and staged
Python/shell/C++ code hashes are checked. Native dumps are collected as `.data`.

## Following implementation gates

An exploratory priority signal is smaller-branch packing work of at least 3%
of audited decode GEMM worker elapsed in a measured case. This is not an expected
3% wall-time improvement and does not qualify an optimization. Worker waits
overlap, section clocks and logging perturb execution, and non-GEMM work is absent
from that denominator. Inspect absolute cost and the uninstrumented CPU profile
before deciding. Also inspect prefill counters when comparing priorities.

If evidence supports sharing, implement explicit paired execution with scratch
owned by that execution. Retain the existing quantizer, scales, weight layouts,
both matrix outputs and unsupported-path fallbacks. Never reuse by tensor pointer
across graph executions: arena addresses recur. Audit graph/state and scratch
lifetimes, then use native correctness, repeated operator timing and matched cold
model ABBA gates. Benefit must exceed both 3% and measured control spread, with
no clear regression. Only an advancing candidate proceeds to complete naturally
stopped answers, held-out facts/code checks and two-order cloud judging.

If packing is small, use the measured decode profile and source to investigate
dispatch/synchronization or another supported bottleneck. Do not infer removable
wall time from sampled CPU shares or reinterpret a negative gate as a defect.

## Monitoring and commands

The completed follow-up checked roughly every 30 minutes and remained quiet while
healthy; it is now paused. It diagnosed and repaired technical faults. A repaired
inference rerun gets a fresh directory and a new monitor; prior evidence and
gates remain intact. Collection-only recovery never restarts inference.

```bash
python3 spacemit/bench/start-k1-decode-audit.py --board musepipro
python3 spacemit/bench/start-k1-decode-audit.py --collect-only \
  --run-dir spacemit/reports/raw/k1-decode-audit-20261007-074314
python3 spacemit/bench/test-k1-decode-audit.py
```

No default is changed. Capped throughput, CPU attribution, overlapping worker
elapsed and complete useful-answer speed are separate evidence categories.
