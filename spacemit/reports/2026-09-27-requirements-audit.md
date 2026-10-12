# 2B/4B inference checklist: evidence audit

> Dated campaign snapshot. The measurements apply to the stated workload and
> date. Queued/running statements below are historical. Use the
> [current guide](../DOCS.md) and the [reports index](README.md) for later
> results and for the current status.

Date: 2026-09-27. Board: MUSE-Pi-Pro K1/X60. The
[completed-gates report](2026-09-27-completed-gates.md) contains the
measurements and the limitations. This file maps each original checklist
item to its current proof. A queued run is not evidence of its result.

| Requested item | Current evidence | Status / remaining gate |
| --- | --- | --- |
| Client time to first token for 2B and 4B | The [lifecycle baseline](2026-09-25-lifecycle.md) measures client TTFT at 128, 2k, 8k, and 12k prompts for both models. | Measured. |
| Sustained prefill improvement for both models | The [RVV 2k/8k off/on/on/off records](raw/2026-09-25-lifecycle/lifecycle-rvv32-long.jsonl) and the [short records](raw/2026-09-25-lifecycle/lifecycle-rvv32.jsonl) pass exact-output audits. The integrated 2B 12k off/on result is 1,653.70 → 741.47 s, with exact output. | Demonstrated at 2k and 8k for both models, and at 12k for 2B. The integrated 4B 12k off/on pair is live. The 12k arms have only one pair per model. |
| Long-duration decode stability, both sizes | The [code-prompt 4,096-token traces](raw/2026-09-25-lifecycle/lifecycle-code-long.jsonl) give two requests per direct/MTP mode and model, bounded decode RSS, and no error or multi-minute stall. The longest 4B direct request took about 43.2 min. The [repeated synthetic 2,048-token runs](raw/2026-09-25-lifecycle/followup.jsonl) also completed. | Bounded stability is verified over the observed requests, not over indefinite service operation. Direct/MTP long-code token identity fails, and it is a separate correctness gate. |
| 4B speculative concurrency | The [pinned-slot c4/c8 ABBA](raw/2026-09-25-lifecycle/lifecycle-code-pinned.jsonl) verifies all slots and 128-token hashes. MTP is 2.9% and 2.4% slower than direct. | Measured for the fixed prompt and the 128-token output. Direct is the supported setting at c4/c8 on this workload. |
| >8k throughput degradation | The [direct 128–12,288-token curves](raw/2026-09-25-lifecycle/context-curves.svg) and the [baseline JSONL](raw/2026-09-25-lifecycle/baseline.jsonl) cover both sizes. | Measured through 12k. |
| Memory jitter and KV-cache overhead | The [baseline](2026-09-25-lifecycle.md) gives sampled RSS jitter at 8k and 12k, per-token F16 target KV payload, and 8k/16k allocation differences. The [memory records](raw/2026-09-25-lifecycle/) include process RSS and virtual size. | Measured for those allocations. The target KV payload is an analytical component, while process RSS includes runtime and model overhead. |
| Long-context windowed MTP | The [12k same-binary controls](raw/2026-09-25-lifecycle/lifecycle-windowed-control.jsonl) and the [window runs](raw/2026-09-25-lifecycle/lifecycle-windowed.jsonl) show exact 128-token hashes and 68.5/135.3 MiB peak-RSS savings. | The memory effect is verified. One long pair per model leaves the speed attribution pending. A fresh full/window/window/full run is queued. Long-code MTP identity remains unresolved. |
| KV compression | The [4B F16/Q4_0/Q4_0/F16 ABBA](raw/2026-09-25-lifecycle/lifecycle-4b-kv-abba.jsonl) shows 367.6 MiB lower loaded RSS and exact 32-token output. 2B Q4_0 slowed 2k prefill. | Evaluated. The 4B 512-output identity test is queued. Q4_0 cannot use the current F16-only RVV prefill kernel. |
| Layered offloading | The [OpenCL 0/4-layer ABBA](raw/2026-09-25-lifecycle/lifecycle-opencl.jsonl) and the device/server logs show zero layers transferred. PowerVR exposes OpenCL C 1.2 and none of the required subgroup extensions, and the fork rejects the device. | Feasibility was tested. Real layered GPU offload remains unavailable on this board and backend. There is no GPU speed claim. |
| Paged scheduling | The [occupied-page gather test and ABBA](../experiments/2026-09-26-page-gather.md) verify numerical correctness and 64 streamed completions. But throughput fell 2.1% and 2.9% for 2B/4B, and RSS rose slightly. | The prototype was evaluated negatively. It retains full preallocation and copies the gathered rows. Full page allocation/reclamation and direct page-index attention remain unimplemented. Verbose compaction telemetry is queued. |

The measured speed improvement that we currently recommend for cold prefill
is the opt-in RVV F16 attention kernel. Direct decoding remains the
correctness-preserving choice for arbitrary long code, because the observed
MTP code output first differs at generated index 179 (2B) and 303 (4B). The
draft-length, target-logit, and RS rollback diagnostics are queued, to
locate that divergence.

## Cross-cutting validation and scope

| Requested item | Current evidence | Remaining gate |
| --- | --- | --- |
| Full 2B/4B prefill and decode matrix, including the main quantization paths | The [lifecycle campaign](2026-09-25-lifecycle.md) compares Q4_0-weight 2B and 4B with F16 K/V at 128, 2k, 8k, and 12k. RVV off/on prefill is replicated through 8k. Short-context F16/Q8_0/Q4_0 KV measurements exist for both models, and 4B F16/Q4_0 is replicated at 2k. The earlier [Q8_0 IME1 study](2026-09-24-integrated-k1.md) covers 4B kernels and server results. | There is no matched, all-cell Q4_0-versus-Q8_0 weight matrix on both sizes through long context. Distinguish weight quantization from KV quantization. Extend the configurations that have a plausible speed or memory benefit. |
| Small 1.8%–3.3% improvements | The [M4 scale results](2026-09-24-integrated-k1.md) report these point estimates with small paired comparisons. | There is no defensible confidence interval or significance claim yet. Repeat matched pairs across launches, and report the paired distribution and interval, before you treat these values as established gains. |
| Output equality beyond three short greedy prompts | The [lifecycle auditor](../bench/audit-lifecycle.py) checks exact token hashes on numerous fixed greedy requests, including 12k prefill, 4,096-token generation, and pinned 4B c4/c8 output. It detects a direct/MTP mismatch at generated token 179 for 2B and 303 for 4B on long code. | Exactness remains workload- and configuration-scoped. Resolve the MTP mismatch. Then use varied code, prose, and multilingual prompts, longer outputs, slot reuse, and specified sampling configurations. Quantized KV need not be token-identical to F16, so assess its quality separately. |
| Adaptive speculative policy | The [low-acceptance fallback](2026-09-24-lowacc.md) improves a low-acceptance Chinese prompt for both sizes, and it resets at the next request. The [timing gate](2026-09-24-integrated-k1.md) disabled a beneficial mapped-head request incorrectly, and we excluded it. | Test a representative mixed workload and long outputs before you enable a broad policy. Fix MTP long-code correctness first. A short early throughput window is not a reliable admission rule. |
| Integrated optimization report | The [completed-gates report](2026-09-27-completed-gates.md) maps RVV to cold prefill, direct/MTP to decode, and windowed MTP, KV compression, page gathering, and offload feasibility to long-context or memory effects. | Update that report as the serialized 4B 12k and diagnostic runs finish. Keep the negative outcomes and the unmeasured cells explicit. |

## Next measurement decisions

1. Finish the already-running 4B integrated 12k RVV off/on pair and its
   strict output audit. Report the single-pair result as a single pair.
2. Diagnose the first long-code direct/MTP token divergence with the queued
   draft-length, target-logit, and rollback sweeps. Until that work
   concludes, use direct decode when exact output is necessary on varied
   long prompts.
3. Analyze the queued 4B long-output Q4_0 KV check and the
   full/window/window/full 12k MTP comparison. Adopt windowing for speed
   only if the interleaved comparison confirms it. Its measured RSS savings
   stand independently.
4. For the small M4 claims, collect enough paired repeats to estimate
   run-to-run variation and a confidence interval. Do not spend a long board
   campaign on every matrix cell before you identify a configuration that is
   worth a deployment.
5. Extend the context length from 12k to 16k, and then to 32k/64k only with
   a compatible larger context allocation and explicit time and RAM limits.
   Record TTFT, prefill and decode curves, resident-memory jitter, KV
   allocation, output completeness, and any failure. The current 16k KV
   numbers are allocation comparisons, not 16k-prompt benchmarks.

Actual GPU layer offload requires a compatible PowerVR backend or another
supported device. The measured OpenCL attempt transferred zero layers. Full
paged scheduling requires allocation/reclamation and mapped attention that
avoids the measured gather-copy cost. Neither route has a justified speed
claim on this board yet.
