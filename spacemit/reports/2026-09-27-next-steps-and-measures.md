# Next steps and requested measures: Qwen3.5 2B/4B on MUSE-Pi-Pro

> Dated campaign snapshot. Measurements apply to the stated workload and date.
> Queued/running statements below are historical; use the
> [current guide](../DOCS.md) and the [reports index](README.md) for later results and current status.

Date: 2026-09-27. This is the original 2026-09-27 working list for the user's prefill, decode, long-context, and validation checklist. **Measured** means a board result exists for the stated scope; **partial** means the requested broader claim is still open; **pending** means a run is queued or active and has no result yet. A queued run must not be counted as evidence. Detailed results are in the [requirements audit](2026-09-27-requirements-audit.md) and [completed-gates report](2026-09-27-completed-gates.md).

Read this first:

Basic Requirements

    Models must use exactly Qwen3.5-2B-Instruct and Qwen3.5-4B-Instruct. Both are mandatory.

    The deployment toolchain must use SpacemiT’s open-source llama.cpp.

    Both models must support local inference and must not depend on cloud APIs.

    The solution must provide two result sets: baseline and optimized. It must include at least one quantifiable performance optimization and explain its improvement on prefill, decode, or long-context performance.

    Provide complete deployment instructions, run scripts, and test results.

Advanced Challenges

    Continuously optimize prefill performance for Qwen3.5-2B and Qwen3.5-4B, aiming for higher throughput and lower first-token latency.

    Continuously optimize decode performance for both models, aiming for higher tokens/s and more stable long-duration generation.

    Solve long-context problems such as significant throughput degradation, severe memory jitter, and high KV cache overhead.

    Optimization may be implemented through quantization, KV cache compression, layered offloading, paged scheduling, and modifications to llama.cpp.

Background Key Point

The task is to deploy Qwen3.5 series models locally using SpacemiT’s open-source llama.cpp, and optimize around prefill, decode, and long-context performance.




## 1. Prefill optimization

| Measure requested | Current status | What to do next |
| --- | --- | --- |
| Client time to first token (TTFT) for Qwen3.5 2B and 4B | **Measured** at 128, 2,048, 8,192, and 12,288 prompt tokens for both Q4_0-weight models with F16 K/V. | Keep client TTFT, server prompt time, and prompt tokens/s in every matched comparison. |
| Lower first-token latency | **Measured improvement:** the opt-in RVV F16 attention path cut 2k TTFT by 18.8% (2B) and 32.7% (4B), and 8k TTFT by 49.2% and 64.0%. Cold long-prompt TTFT remains substantial. | Finish the active integrated 4B 12k off/on pair. Report the absolute latency as well as the percentage change. |
| Sustained prefill improvement for both model sizes | **Measured** in replicated 2k and 8k RVV off/on/on/off comparisons with exact greedy output. One integrated 2B 12k pair cut TTFT from 1,653.70 to 741.47 seconds. | Audit the 4B 12k pair when complete. Replicate 12k before treating its effect as a precise estimate. |
| Prefill across 8k, 16k, 32k, and 64k prompts | **Partial:** actual requests reach 12,288 tokens; 16k was tested as a KV allocation size, not a 16k prompt. | Measure actual 16k requests first. For 32k/64k, enlarge context allocation and set explicit time and RAM limits; record completion or failure, TTFT, prompt rate, and memory. |
| Both models and both principal weight-quantization paths | **Partial:** the lifecycle curve uses Q4_0 weights. Earlier 4B Q8_0 IME1 work is not a matched 2B/4B long-context matrix. F16/Q8_0/Q4_0 KV tests are a separate cache-format comparison. | Run matched Q4_0- and Q8_0-weight baselines and optimized arms at selected short and long prompts for each available 2B/4B model. Keep weight format and KV format separate in the report. |

## 2. Decode optimization

| Measure requested | Current status | What to do next |
| --- | --- | --- |
| Stable long-time generation | **Measured within bounds:** two complete 4,096-token code-prompt requests per direct/MTP mode and model, plus repeated 2,048-token synthetic requests. The longest measured 4B direct request took about 43 minutes. No server errors or runaway decode RSS appeared. | Repeat on varied prompts and, if service stability is the target, add a longer multi-request soak. Do not describe finite runs as indefinite stability. |
| Decode tokens/s over extended generation | **Measured:** per-event traces support 128-token windows, first/second-half rates, stream-gap tails, and decode-phase RSS drift. | Present the windowed rate curves for both models and modes alongside average tokens/s; include the prompt and output lengths. |
| 4B speculative concurrency | **Measured** at single stream and pinned 4/8 streams. In the fixed 128-token code workload, MTP aggregate throughput was about 2.9% lower at four streams and 2.4% lower at eight than direct. | Retain direct decoding for that concurrent workload. Test longer outputs and representative prompts only after the MTP correctness issue is resolved; repeat small differences before claiming a general regression. |
| Adaptive speculative policy | **Partial:** low-acceptance fallback improved the measured low-acceptance Chinese prompt for 2B/4B; a short-window timing gate disabled a beneficial mapped-head case and was rejected. | Diagnose long-code MTP divergence, then test a mixed held-out workload with per-request acceptance and full draft/verify cost. Compare direct, fixed MTP, and fallback. |
| Complete single-/multi-stream direct/MTP comparison for 2B/4B | **Partial:** both sizes have direct/MTP long single-stream runs; 4B has c1/c4/c8 evidence. A balanced, varied 2B/4B matrix is absent. | Choose representative code, prose, and multilingual prompts. Measure c1/c2/c4/c8 with matched output length, token hashes, aggregate throughput, per-request latency, and slot IDs. |

## 3. Long-context optimization

| Measure requested | Current status | What to do next |
| --- | --- | --- |
| Actual context benchmarks beyond 8k | **Measured** at 12,288 tokens for both models. | Extend to 16k, then consider 32k/64k under explicit resource limits. |
| Throughput-degradation curve | **Measured** for direct prefill and decode from 128 through 12,288 prompt tokens. RVV off/on is replicated through 8k and has one 2B 12k pair. | Add the completed 4B 12k RVV point, then actual 16k+ points with the same model, context allocation, batch, and cache format within each comparison. |
| Memory jitter | **Measured** from sampled process RSS and system MemAvailable in the 8k/12k lifecycle records; decode-phase RSS is separated from prefill growth. | Continue sampling at 16k+, report range or percentiles and first-to-last decode RSS drift, and note whether swap or OOM occurs. |
| KV-cache overhead | **Measured in part:** GGUF-based F16 KV payload estimates, whole-process F16/Q8_0/Q4_0 footprints, and 8k-versus-16k allocation differences. | For actual 16k+ workloads, report cache allocation, loaded and peak process RSS, virtual size, and model/draft/runtime overhead separately where instrumentation permits. |
| KV cache compression | **Evaluated:** 4B Q4_0 K/V saved about 367.6 MiB loaded RSS and cut 2k TTFT 12.1% against generic F16 in a repeated comparison; 2B Q4_0 slowed 2k prefill. The RVV prefill kernel currently requires F16 K/V. | Analyze the queued 4B 512-output F16/Q4_0 comparison; assess quality and memory/speed tradeoffs at longer prompts. |
| Layered offloading | **Feasibility tested, not implemented on this board:** the OpenCL backend rejected the PowerVR GPU and transferred zero layers. | Pursue a compatible PowerVR backend or other supported device only if offload is a project objective; require log proof of transferred layers and matched CPU/offload measurements. |
| Paged scheduling | **Prototype evaluated negatively:** occupied-page gathering preserved tested outputs but lowered 2B/4B throughput about 2–3% and kept full backing allocation. | Review queued compaction telemetry. A full design needs page allocation/reclamation and mapped attention without the gather-copy cost, followed by fragmented multi-slot tests. |
| Windowed MTP | **Implemented as an opt-in prototype:** at 12k, a 2,048-token draft window saved 68.5 MiB (2B) and 135.3 MiB (4B) peak RSS with exact 128-token full/window output hashes. Speed is based on one long pair per model. | Analyze the queued full/window/window/full 12k repeats and combined RVV+windowed run. Test long-output identity before adopting it for general decoding. |

## 4. Cross-cutting validation

| Measure requested | Current status | What to do next |
| --- | --- | --- |
| Baseline versus optimized prefill, decode, and long context for 2B/4B | **Partial:** the integrated report maps measured effects, but no all-cell matrix spans both weight paths, cache formats, lengths, and concurrency levels. | Build a compact results matrix with one row per measured configuration, explicit blank cells, exact build/settings, client TTFT, prompt/decode rates, end-to-end rate, RSS, and output audit. Prioritize settings worth deploying. |
| Statistical significance or confidence intervals for 1.8%–3.3% gains | **Open:** current small-gain comparisons have too few independent paired launches for a strong inference. | Run balanced paired repeats in alternating order, show each paired difference, and report a confidence interval. Treat the point estimates as provisional until then. |
| Output equality beyond three short greedy prompts | **Partial:** many fixed greedy runs have exact token-hash audits, but direct/MTP output diverges on long code at generated index 179 (2B) and 303 (4B). Arbitrary inputs and sampling settings are unverified. | Finish queued draft-length, target-logit, and rollback diagnostics; fix the divergence. Then test varied prompt families, long outputs, slot reuse, and specified sampling seeds/settings. Assess lossy KV quality separately from exact token equality. |
| One integrated report linking each optimization to its effect | **Present** in the [completed-gates report](2026-09-27-completed-gates.md), with measured gains, negative findings, and limitations. | Update the report after each queued run, preserving raw JSONL/log links and marking unmeasured comparisons clearly. |

## Historical work queue before the 2026-09-27 reboot

1. **Already running on the board:** complete and audit the integrated 4B 12k RVV pair. Serialized behind it are MTP draft-length, page-gather telemetry, 4B long-output KV, target-logit, 12k windowed-MTP, rollback, combined RVV+window, and package-application checks. Do not overlap these board jobs.
2. **Correctness gate:** locate and fix long-code MTP token divergence before recommending speculative decoding for arbitrary long outputs.
3. **Validation gate:** publish the completed 4B 12k and repeated window/KV findings with exact-output and memory checks; keep single-pair speed observations provisional.
4. **Coverage gate:** add actual 16k context measurements, then decide whether 32k/64k runs are feasible from observed time/RAM. Fill the most useful 2B/4B Q4_0/Q8_0 and c1/c2/c4/c8 cells.
5. **Small-effect gate:** replicate the 1.8%–3.3% kernel/server claims and quantify uncertainty.
6. **Research extensions:** full paged allocation plus mapped attention, and a working GPU backend for layered offload. Both require new implementation before a performance claim.

