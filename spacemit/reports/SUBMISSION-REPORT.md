# Infrastructure optimization of Qwen3.5 inference on the SpaceMiT K1

**Submission report — evidence cutoff: October 3, 2026, Asia/Singapore**\
Platform: MUSE-Pi-Pro, SpaceMiT K1/X60, 16 GiB RAM\
Models: Qwen3.5 2B and 4B conversational checkpoints\
Implementation: SpaceMiT's open-source llama.cpp fork

## Abstract

This project implements and evaluates local language-model inference improvements
on a physical RISC-V board. Its principal contributions are a 256-bit RVV
attention kernel for F16 K/V and a new policy that selects the existing
direct-memory IME1 matrix path instead of staging eligible Q4_0 operations.
Both preserve the full benchmark inputs and required models. In replicated
8,192-token comparisons, RVV attention reduced client first-token latency by
49.2% on 2B and 64.0% on 4B. Against the later optimized baseline, separate
GEMM-routing modes reduced prefill time by 6.40% on 2B/2k and 7.75% on 4B/1k,
and reduced 64-token decode time by 14.40% and 28.62%, respectively.
All 24 requests in the routing experiment matched their control outputs.
The routing candidate remains isolated and opt-in; longer-context and
complete-answer confirmation are required before default adoption.

The report also records negative results, bounded long-context feasibility,
and the limits of speculative decoding and cache-quality evidence. Performance
is reported for each matched workload; measurements from different campaigns
are not combined into a cumulative speedup.

## 1. Objective and scope

The task is to deploy both required Qwen3.5 models locally through the SpaceMiT
fork, improve prefill, decode or long-context inference, and provide baseline
comparisons, executable code and reproducible test results.

The current optimization mission concerns infrastructure. It retains complete
inputs, Q4_0 weights and F16 K/V. Retrieval, prompt shortening, token pruning
and model replacement are excluded. Earlier Q8_0 and speculative experiments
are included as supporting evidence with their separate settings and limits.
All model generation runs locally. An optional cloud judge is used only for
evaluation of completed cached answers; inference does not require that judge.

### Requirement coverage

| Requirement | Evidence and boundary |
| --- | --- |
| Both 2B and 4B models | Both have local inference, matched prefill comparisons and routing decode comparisons. |
| SpaceMiT open-source llama.cpp | Packaged deployment uses official-fork base `5ad05d8`; later board experiments use `a990751` plus recorded changes. |
| Baseline and optimized results | Matched RVV off/on and GEMM staging/bypass tables below; each comparison states its baseline. |
| Quantifiable infrastructure improvement | RVV reduces long-prompt TTFT; the new routing screen improves both phases on both models. |
| Deployment, scripts and tests | Integration guide, patch helper, native harnesses, tmux runners and archived evidence are provided. |
| Generation above 1 token/s | Demonstrated in short/moderate-context decode tests; this is not guaranteed at every long context. |
| ARM/x86 performance comparison in the competition background | A matched inference-performance comparison is not included. Local x86 mechanism probes do not satisfy this comparison. |

The [original requested checklist](2026-09-27-next-steps-and-measures.md) and
[competition background](../../env/competition-background.md) have different
scopes. This report states the measured coverage rather than treating every
suggested advanced challenge as completed.

## 2. Platform, models and measurement method

The board runs Bianbu 2.3.5 with a RISC-V Linux environment. The evaluated
backend uses RVV and SpaceMiT IME1; four inference workers are used because
the IME-capable cores are 0–3. Build instructions specify GCC 14 and the
matching SPERT runtime. The latest runtime audit records the performance
governor at 1.6 GHz. Runtime libraries and original build flags are preserved
in experiment provenance.

The principal benchmark files are:

- `Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf`
- `Qwen3.5-4B-MTP-Q4_0-embQ4_0-dv64k.gguf`

These are the project's conversational checkpoint derivatives; their filenames
omit the word `Instruct`. MTP tensors are present, but the principal RVV and
routing results use **direct decoding**. Weight and cache precision are
distinct: Q4_0 weights with F16 K/V is the common current configuration.

### Controls and metrics

| Item | Protocol |
| --- | --- |
| Model/runtime controls | Same model and full prompt within each comparison; four workers, batch/microbatch 32, flash attention; direct greedy decoding. |
| Run order | Four cold ABBA requests for each routing comparison: control, candidate, candidate, control. Earlier campaign repetitions are stated separately. |
| Cache isolation | Cold requests require zero reused prompt tokens and the complete intended input count. |
| TTFT | Client time to first token; includes work visible to the requesting client. |
| Prefill time | Server prompt-processing time; a one-token request isolates this phase but does not establish answer quality. |
| Decode rate/time | Server generation measurements after prefill; latest screen captures all 64 requested tokens. |
| Memory | Whole-process RSS is distinguished from estimated KV payload. |
| Correctness | Native finite-output/guard checks plus input, token and text hashes, completion counts and actual kernel activation logs. |

For the latest screen, a candidate's mean time reduction must exceed both 3%
and the observed full control range, with no clear regression in required
comparisons. This is a predeclared engineering gate, not a statistical
significance test. Two samples per arm do not establish a population confidence
interval. Exact output agreement is limited to the tested inputs and settings.

## 3. Implemented optimizations

### 3.1 RVV attention for the K1's vector width

The original wide-vector prototype did not activate on the K1. The subsequent
256-bit implementation enables the F16-KV wide-head prefill path and is
packaged as optional patch 0009. It is enabled with `SPINE_FA_WIDE_TILE=1`;
activation is checked in the server logs. It improves prompt processing and
does not establish a single-token decode gain. Quantized K/V and other model
head shapes are outside its demonstrated dispatch.

### 3.2 Production Q4_0 GEMM routing

Production attribution identified substantial staging-copy work: 9.55% / 9.93%
of summed instrumented prefill worker elapsed time for 2B / 4B. These sums
include overlapping waits and instrumentation overhead, so they are not
removable wall-time estimates. The new code instead tests the existing
direct-memory branch in production `forward_mul_mat`.

Eligibility is restricted to Q4_0 K32/N16 traits using IME1, with K divisible
by 32 and N divisible by 16. The selected buffer is set to null with size zero;
weight packing, activation quantization and IME arithmetic are retained.
The generated library is isolated from the original build.

| `SPINE_K1_GEMM_ROUTE` | Selection | Validation status |
| --- | --- | --- |
| Unset, invalid or 0 | Original staging | Control |
| 1 | Bypass for M > 1 | Numerical, operator and model prefill gates passed |
| 2 | Bypass for M = 1 | Numerical, operator and 64-token model decode gates passed |
| 3 | Bypass for both | Numerical checks only; combined model performance unmeasured |

Mode 2 can affect single-row work during prefill as well as decoding.
The current TCM API reports unavailable/fake/zero geometry, while SPERT
supplies non-null 128 KiB worker buffers. Their physical placement is
unverified; the measured result concerns staging policy under this runtime.

### 3.3 Earlier kernel and runtime work

The packaged work also includes recurrent-state in-place write-back,
microbatch selection, Q8_0 IME1 support, Q4_0 M4 scale construction and
workload-specific speculative policies. Q8_0 IME1 raised 4B pp64 from
1.117 to 7.472 token/s and tg32 from 0.866 to 1.349 token/s in its separate
higher-precision comparison. Q4_0 remained faster overall.

M4 scale construction raised 4B Q4_0 pp128 from 9.058 to 9.360 token/s
(3.34%). Corrected analysis gives a conditional independent-launch Welch
95% interval of +0.095 to +0.511 token/s, with only two launches per arm.
The roughly 1.8% English/Chinese mapped-MTP gains have intervals including
zero. These small effects remain workload-specific. Detailed implementation,
attribution and statistics are linked in the evidence appendix.

## 4. Matched performance results

### 4.1 RVV attention versus the generic attention path

Both arms use the same model and configuration within each comparison,
Q4_0 weights, F16 K/V, direct decoding and 32 generated tokens.
The baseline here has RVV wide attention disabled.

| Model / input tokens | Generic TTFT | RVV TTFT | TTFT reduction | Launches per arm |
| --- | ---: | ---: | ---: | ---: |
| 2B / 2,048 | 113.78 s | 92.45 s | 18.7% | 2 |
| 4B / 2,048 | 343.95 s | 231.54 s | 32.7% | 2 |
| 2B / 8,192 | 862.62 s | 438.05 s | 49.2% | 2 |
| 4B / 8,192 | 3,194.99 s | 1,150.42 s | 64.0% | 2 |
| 2B / 16,384 | 2,808.28 s | 1,124.57 s | 60.0% | 1 |
| 4B / 16,384 | 11,062.98 s | 3,216.23 s | 70.9% | 1 |

All these comparisons have complete matching token/text hashes. The 2k/8k
rows use the isolated build; 16k uses the integrated build. The single-pair
16k observations need replication. Decode and peak RSS were effectively
unchanged within these attention comparisons.

A single RVV-enabled 2B request with an actual 32,768-token prompt completed
at 3,291.21 s TTFT, 9.96 prefill token/s and 2,768.4 MiB peak RSS. Its 32 output
tokens completed; decode was 0.95 token/s. This establishes bounded feasibility,
with no matched 32k control or answer-quality claim. 4B/32k and 64k are unmeasured.

### 4.2 New GEMM routing versus the current optimized baseline

The baseline already includes accepted wide attention and layout 0.
Each row has two launches per arm. Prefill rows use mode 1 and one output token;
decode rows use mode 2, a full 256-token prompt and 64 captured output tokens.

| Model / measured phase | Control mean | Candidate mean | Time reduction |
| --- | ---: | ---: | ---: |
| 2B / 512-token prefill | 22.052917 s | 20.625322 s | 6.47% |
| 4B / 512-token prefill | 56.740043 s | 52.304415 s | 7.82% |
| 2B / 2,048-token prefill | 92.634959 s | 86.709042 s | **6.40%** |
| 4B / 1,024-token prefill | 115.551047 s | 106.596561 s | **7.75%** |
| 2B / 64-token decode | 17.016656 s | 14.566911 s | **14.40%** |
| 4B / 64-token decode | 43.553046 s | 31.087887 s | **28.62%** |

Decode throughput rose from **3.76 to 4.39 token/s** for 2B and **1.47 to
2.06 token/s** for 4B. Mode 2 showed no clear prefill regression. All six
comparisons cleared their declared gates. These are time reductions;
throughput increases have a different percentage denominator.

The board run completed successfully in 38.16 minutes. Validation included
104 real production graph cases per arm across five arms, 144 production
operator records, and 24 model requests. Every model comparison matched
input/output hashes and uncached counts. All 236 collected artifact hashes
were independently verified, and end-of-run checks matched 46 original
source/object/build files. The verifier recomputes the required gates from
individual records.

The two routing modes were tested separately. Their gains must not be added
or combined with older RVV percentages to claim a cumulative acceleration.
Independent long-context and naturally completed answers remain the next
confirmation gate before default adoption.

## 5. Negative results and correctness limits

| Candidate | Measured outcome | Decision |
| --- | --- | --- |
| Compact attention layouts | Original 2k pilot gains of 0.89% / 1.98%; later fast-screen model gains below 3% | Retain layout 0 |
| Further IME scheduling / scale gathering | Numerical checks pass; operator screens do not qualify | Retain original schedule |
| Recurrent prefill fusion | Operator time falls 24–28%; 2B/512 model time falls 2.38%, below gate | Experimental; no advancement |
| Direct V attention access | Operator gains do not become model gains: 2B/2k is 1.67% slower; 4B/1k effectively unchanged | No adoption |
| Larger QK grouping | Operator qualification insufficient | No model advancement |
| Occupied-page gathering | Throughput falls about 2–3%; backing allocation retained; resumed telemetry shows no compacted spans | No speed or full-paged-scheduling claim |
| OpenCL GPU offload | Zero layers transferred; backend rejects the PowerVR device | No GPU acceleration claim |
| Vulkan route | Dropped before measured offload | No GPU acceleration claim |
| Speculative timing gate / hybrid IME-RVV dispatch | Regress tested workloads | Excluded |

Long-code MTP outputs differ from direct outputs beginning at generated index
179 for 2B and 303 for 4B. Smaller draft lengths and RS rollback did not fix
this. Full-vocabulary target verification does not prove numerical identity
between different execution paths. Historical matching 128-token samples
therefore do not justify calling MTP universally lossless. Direct decoding
is used for the principal results here.

Two complete 4,096-token requests per model and direct/MTP mode demonstrated
bounded generation stability, including a roughly 43-minute 4B direct request.
These earlier traces are not a long-duration validation of the new routing
candidate, and they do not establish indefinite service stability.

## 6. Full-input cache reuse: separate supporting evidence

Same-process prefix reuse preserves the complete document and sends changed
questions through a local server slot. It avoids recomputing an unchanged
prefix and is separate from the cold-kernel comparisons. Cached and cold
answers need not be token-identical; usefulness is checked on complete answers.

The original alternating quality protocol evaluated both models, 4k/8k
documents and six questions: 24 naturally completed cached/cold pairs.
An optional MiMo judge scored each pair in both answer orders, supplementing
fact, citation, completion, cache and slot checks.

| Model / document | Cold / cached mean score | Median cold / cached TTFT | Descriptive decision |
| --- | ---: | ---: | --- |
| 2B / 4k | 4.50 / 4.50 out of 5 | 211.11 / 3.90 s | Review required |
| 2B / 8k | 4.83 / 4.83 | 474.31 / 5.01 s | Pilot pass |
| 4B / 4k | 4.83 / 4.83 | 551.91 / 10.80 s | Pilot pass |
| 4B / 8k | 4.83 / 5.00 | 1,271.37 / 14.65 s | Pilot pass |

One 2B/4k question scores 2/5 in both arms, so the matrix has no universal
quality pass and does not show a cache-specific regression on that question.
One judge and six questions per configuration cannot establish general quality
equivalence. These results also do not validate the new GEMM-routing candidate.
Length-capped one-, 32- or 64-token speed samples are not complete-answer evidence.

## 7. Reproduction and deliverables

Use the [deployment guide](../README.md) for the clean official-fork baseline,
model preparation, compiler/runtime settings and server command. The packaged
patch helper and the latest isolated routing experiment target different
recorded source states; the routing candidate is not a default helper option.

From the repository root, the latest checks are:

```bash
python3 spacemit/bench/test-k1-gemm-routing.py
python3 spacemit/bench/test-k1-fast-test.py
python3 spacemit/bench/test-k1-ime-test.py
python3 spacemit/bench/verify-k1-gemm-routing.py \
  spacemit/reports/raw/k1-gemm-routing-20261003-005740
```

To reproduce the board experiment, inspect its [protocol](../experiments/2026-10-03-gemm-routing.md)
and run `python3 spacemit/bench/start-k1-gemm-routing.py` with the matching
board source/runtime/model prerequisites. The launcher runs the benchmark
and collector in tmux under a shared board lock, with explicit time limits.
The [benchmark guide](../bench/README.md) covers the other campaigns.

The [evidence appendix](SUBMISSION-EVIDENCE.md) maps every principal claim to
source code, provenance, raw records and verification commands. No model
weights or private API credentials are included in the report.

## 8. Conclusion and remaining work

The strongest replicated long-input result is the activated RVV F16 attention
kernel. The latest production GEMM-routing prototype also improves measured
prefill and bounded decode on both required models while preserving tested
outputs. Its scope is the current board/runtime and the recorded workload;
the positive screen supports further confirmation rather than automatic
default deployment.

The immediate next step is independent long-context and complete-answer testing
of the routing candidate, including a measured combined mode if both phase
policies are to be enabled together. Further unused infrastructure leads are
shared K packing across grouped query heads, a Q4_0 RVV lookup-table prototype,
and compiler comparisons for measured hotspots. Their platform fit and primary
research references are in the [October 3 research review](2026-10-03-infrastructure-research.md).

Remaining submission coverage limits include the absent matched ARM/x86
performance comparison, unmeasured 4B/32k and 64k workloads, unresolved MTP
long-code identity, and unavailable measured GPU offload/full paged scheduling.
These are stated explicitly so the submission represents the completed work.

Validation priorities and primary-source practices for these remaining checks
are documented in the [October 3 validation review](2026-10-03-validation-practice.md).
