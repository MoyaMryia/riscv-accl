# Infrastructure optimization of Qwen3.5 inference on the SpaceMiT K1

**Project report - evidence cutoff: October 12, 2026, Asia/Singapore**\
Platform: MUSE-Pi-Pro, SpaceMiT K1/X60, 16 GiB RAM\
Models: Qwen3.5 2B and 4B conversational checkpoints\
Implementation: SpaceMiT's open-source llama.cpp fork

## Abstract

This project implements and tests local Qwen3.5 inference on the MUSE-Pi-Pro
with the SpaceMiT K1/X60 and 16 GiB RAM.
The main release retains Q4_0 weights, F16 K/V, complete inputs, and direct decoding.
The 256-bit RVV attention path reduces 8,192-token first-token latency by
49.2% on 2B and 64.0% on 4B.
Separate IME1 routing tests reduce 64-token decode time by 14.40% and 28.62%.
These comparisons use different controls and do not establish a cumulative speedup.

Later candidates improve selected prefill or decode workloads on the optimized baseline.
Their complete-answer tests contain 48 identical pairs, but shared model errors remain.
The three-candidate combination fails one decode gate with a 3.0220477% regression
against the attention-only candidate.
Its second round and complete-answer stages do not run.
The verified October 7 release remains the pinned package; routing stays opt-in.

The project also provides a portable performance evaluator and native operator data.
V7 covers all nine reserved groups with wide intervals, but its point directions
agree with measurements in only 9/27 cases.
The first operator batch contains 1,344 observations across 32 configurations.
These training data do not establish independent prediction accuracy.
K1 remote access fails before a confirmed second batch.
Recovery remains pending; this document does not authorize new board work.

## Report status and evidence levels

| Evidence level | Meaning in this report |
| --- | --- |
| Implemented | Source code or an executable tool exists. This status does not establish a performance gain. |
| Verified | The stated checks pass for the named configuration and records. |
| Failed gate | A measured result does not meet its declared criterion. Later versions do not remove that result. |
| Pending | A measurement or independent check is incomplete. |
| Not implemented | The project does not provide the stated capability. |

This report separates the verified release, later candidates, and performance-model work.
Dated reports describe their original campaigns.
The [evidence appendix](SUBMISSION-EVIDENCE.md) maps claims to records and tools.
The report and appendix form one review package.
No external competition submission is recorded.

## 1. Objective and scope

The task deploys both required Qwen3.5 models locally through the SpaceMiT fork.
It targets prefill, decode, and long-context inference.
Deliverables include baseline comparisons, executable code, and reproducible test results.

The current optimization mission concerns infrastructure. It retains complete
inputs, Q4_0 weights and F16 K/V. Retrieval, prompt shortening, token pruning
and model replacement are excluded. Earlier Q8_0 and speculative experiments
are included as supporting evidence with their separate settings and limits.
All model generation runs locally. An optional cloud judge is used only for
evaluation of completed answers, including cache reuse and MTP comparisons;
inference does not require that judge.

### Requirement coverage

| Requirement | Evidence and boundary |
| --- | --- |
| Both 2B and 4B models | Both have local inference, matched prefill comparisons and routing decode comparisons. |
| SpaceMiT open-source llama.cpp | Current release pins official-fork `a990751` and measured source hashes. The historical patch stack targets `5ad05d8`. |
| Baseline and optimized results | Matched RVV off/on and GEMM staging/bypass tables below; each comparison states its baseline. |
| Quantifiable infrastructure improvement | RVV reduces long-prompt TTFT; the new routing screen improves both phases on both models. |
| Deployment, scripts and tests | Integration guide, patch helper, native harnesses, tmux runners and archived evidence are provided. |
| Generation above 1 token/s | Demonstrated in short/moderate-context decode tests; this is not guaranteed at every long context. |
| Cross-architecture comparison | Excluded from the release requirements at the user’s direction. |

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

For the routing screen, a candidate's mean time reduction must exceed both 3%
and the observed full control range.
Required comparisons must have no clear regression. This is a predeclared engineering gate, not a statistical
significance test. Two samples per arm do not establish a population confidence
interval. Exact output agreement is limited to the tested inputs and settings.

Time reduction and throughput increase use different denominators.
For control time $t_b$ and candidate time $t_c$, the time reduction is

$$R_t = 100\left(1-\frac{t_c}{t_b}\right)\%. $$

For equal output counts, the throughput increase is

$$G_q = 100\left(\frac{t_b}{t_c}-1\right)\%. $$

The tables state whether they use means, medians, or median paired ratios.
A ratio of medians need not equal the median paired ratio.

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
| 3 | Bypass for both | Combined 8k phase gates pass on both models; overall quality gate remains open |

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

These initial routing modes were tested separately. Their gains must not be
added or combined with older RVV percentages to claim cumulative acceleration.
The subsequent [staged validation](2026-10-03-staged-validation-results.md)
completed in 4.16 hours with 83 artifact hashes verified. Combined mode 3 at
8192 input/64 output tokens reduces prefill/decode time by 4.43%/9.49% on 2B
and 5.79%/15.06% on 4B. All eight requests match hashes and cold counts.
The 12 full-document answers stop naturally and match paired baseline text.
Both 2B arms lack required tracing citations, so the overall gate remains open.
The protocol skips 4B/32k. These are bounded engineering pilots.

### 4.3 Independent memory-bandwidth and routing confirmation

The [October 6 campaign](2026-10-06-k1-roofline-results.md) completed 150 native
full-read scans, 24 cold direct-inference requests and two separate prefill
profiles. The four-core model-sized streaming reference is approximately
7 GB/s. Main weight-read proxies, excluding MTP draft tensors, are 1.060 GB
for 2B and 2.369 GB for 4B, giving weight-only references of 6.60/2.94 tok/s.
These are traffic references rather than measured DDR utilization or
attainable inference guarantees.

At 256 prompt tokens, route-0/route-3 decode medians are 3.79/4.48 tok/s for
2B and 1.48/2.06 for 4B; median paired throughput gains are 18.01%/38.70%.
At 2,048 tokens the medians are 3.31/3.83 and 1.22/1.62, with paired gains
15.47%/32.36%. All requests generate the same 64 capped output tokens and
match their paired control. This confirms the existing routing mechanism;
these gains must not be multiplied by previous routing measurements.

The profiles identify convolution and synchronization as investigation
targets, but sampled prefill CPU shares are not wall-time savings or decode
attribution. This campaign adds no useful-answer qualification and does not
demonstrate that the hardware limit has been reached.

## 5. Later candidates and the stopped combination

### 5.1 Independent candidates on the optimized baseline

These comparisons retain the fixed 2B/4B GGUF files, four workers, batch and
microbatch 32, F16 K/V, route 3, temperature 0, and seed 42.
MTP is disabled.
Prefill tests use 512 or 2,048 input tokens.
The ranges below describe observed configurations across two rounds.
They are not population confidence intervals.

| Candidate | Change | Measured model result | Scope |
| --- | --- | --- | --- |
| C1 | Hybrid convolution; original path for small batches | One-output-token TTFT falls 4.26–6.53% | 64 cold requests across two rounds; 24 complete answers |
| C2-r2 | GDN register kernel reduces intermediate state access | One-output-token TTFT falls 4.35–5.95% | 96 cold requests across the screen and two rounds; 24 complete answers |
| C3 | C1 with the older C2 | TTFT falls 8.35–9.73% against its disabled control; 3.53–4.63% against C1 | 128 cold requests across two controls and two rounds; 24 complete answers |
| B1-r2 | Shared attention path with a fallback for small work groups | At 2,048 input/65 output tokens, decode time falls 10.48–10.64% on 2B and 16.95–20.32% on 4B | 64 cold requests across two rounds; 24 complete answers |

GDN means gated delta network, the recurrent-state component in these models.
C3 contains the older C2, not C2-r2.
All four versions complete 96 answers with 48 identical text pairs.
Shared arithmetic, citation, code, and Chinese-language errors remain.
These tests do not show an answer-quality improvement.

C2-r2 increases 4B/512/65 decode time by 2.9480% in its first round.
This result is near the 3% regression gate and is not a decode gain.
The old controller deletes some native dumps before the later review.
Saved logs cannot replace a fresh comparison of those dumps.
Complete-answer requests also lack full operating-system thread snapshots.
The [candidate review](2026-10-09-local-candidate-result-rejudgment.md)
records these limits.

### 5.2 Combined-r1: a valid performance stop

The combination uses one library with independent switches.
C0 disables the three new candidates but retains wide RVV attention and route 3.
B enables B1-r2 only.
P enables C1 and C2-r2.
F enables B1-r2, C1, and C2-r2.
C0 is an optimized control, not the initial vendor source.

The run stops on October 11, 2026, at 18:28 Asia/Singapore with exit code 0
and state `performance-gate-stopped`.
The [October 12 audit](2026-10-12-combined-stop-audit.md) recomputes all
48 comparisons from the first round's 96 requests.
It confirms zero reused prompt tokens, output receipts, input hashes, and saved thread snapshots.
One required comparison fails: F versus B for 4B/2,048 input/65 output tokens.
Decode time rises 3.0220477%, above the declared 3% gate.
The full control range is 0.0726418%.

Each table value is the mean of two requests in that arm.
All times are milliseconds.

| Model / input tokens | B prefill | F prefill | B decode | F decode |
| --- | ---: | ---: | ---: | ---: |
| 2B / 512 | 20959.891 | 18769.821 | 14913.766 | 14920.559 |
| 2B / 2048 | 88041.229 | 79032.342 | 15716.909 | 15714.604 |
| 4B / 512 | 52863.175 | 47537.975 | 30820.230 | 31336.530 |
| 4B / 2048 | 226049.395 | 203459.167 | 33608.751 | 34624.424 |

For the failed configuration, F prefill time falls 9.9935% against B.
F decode time also falls 17.5476% against C0.
Neither result clears the required F-versus-B regression gate.
The second round and complete-answer tests do not run.
The combination does not complete acceptance.

The audit does not recollect or compare all 536 formal state dumps.
It checks saved input and text hashes, not reconstructed inputs or new answers.
Startup thread snapshots allow CPU 0–7 and do not establish worker positions during decode.
This gap does not prove incorrect core placement.
Both failed-comparison arms emit 2,048 shared-attention log lines per request.
The evidence does not establish extra attention logs as the cause.
Logging cost remains part of the measured result.

### 5.3 Local revision and comparison boundary

The local dispatch revision changes one GDN condition order.
It returns single-token and non-128-state calls before it reads the prefill switch.
All 90 dispatch combinations select the same paths.
The cross-compiler syntax check and four local tool checks pass.
Full numerical checks, target assembly, operator tests, and model tests remain pending.
This revision is not a verified fix for the regression.
The stopped combination remains a failed result.

The [original/current comparison](2026-10-11-original-current-comparison.md)
contains historical phase measurements and explicit version identities.
Its October 11 pending entries predate the stop audit.
Use the October 12 audit for the combination's current status.
No matched test compares the initial vendor source directly with a final accepted combination.
The separate RVV, routing, and candidate gains must not be added or multiplied.

## 6. Negative results and correctness limits

| Candidate | Measured outcome | Decision |
| --- | --- | --- |
| Compact attention layouts | Original 2k pilot gains of 0.89% / 1.98%; later fast-screen model gains below 3% | Retain layout 0 |
| Further IME scheduling / scale gathering | Numerical checks pass; operator screens do not qualify | Retain original schedule |
| Hybrid SSM convolution/RVV | Exact graph/state checks and 24 natural answers pass; total latency falls 2.92% / 2.13%, below the adoption gate | Disabled in the release |
| Shared dense FFN activation packing | Duplicate work is only 0.024–0.035% of summed GEMM worker elapsed in the decode audit | Implementation declined |
| Fixed K32 M1 inner-loop specialization | Exact raw/production/full-output checks pass; 144 operator samples fail advancement | Disabled; model stages skipped |
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

The newer 512-output checkpoint/RS samples match direct outputs on both models.
Native RS rollback replay fails strict logit checks.
Each model has 18 mismatches, including argmax changes. Full-state restore and same-shape controls
pass. This newer evidence narrows the next diagnosis and does not establish
general MTP identity or supersede the older long-output traces.

The separate [complete-answer MTP pilot](2026-10-03-mtp-usefulness-results.md)
completed 24 requests with RS disabled. Total paired task latency falls
8.63% on 2B and 15.22% on 4B; both models pass the predeclared relative
fact/code/judge quality gate. The 4B Unicode code differs from direct but
passes all 106 functional checks. Absolute usefulness still fails shared
interval-code errors and 2B arithmetic, while Chinese prose becomes slower.
Checkpoint MTP remains optional. These single-pair task results support
workload-specific usefulness, not universal losslessness or general adoption.

The later [adaptive infrastructure screen](2026-10-05-adaptive-mtp-results.md)
completed 54 timing requests and verified 47 artifacts. Median paired code
throughput rises 50.74% on 2B and 53.35% on 4B. The 2B code is capped.
The 4B code is shorter under adaptive MTP and fails reconstruction in every arm. Prose/QA
wall time increases 5.77%/4.76% on 2B and 2.97%/3.62% on 4B despite disabled
drafting. The relative judge gate passes on 4B, but both models fail absolute
correctness and overall timing gates. This establishes bounded throughput,
not faster useful answers. Adaptive MTP remains unqualified and optional.

Two complete 4,096-token requests per model and direct/MTP mode demonstrated
bounded generation stability, including a roughly 43-minute 4B direct request.
These earlier traces are not a long-duration validation of the new routing
candidate, and they do not establish indefinite service stability.

## 7. Full-input cache reuse: separate supporting evidence

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

One 2B/4k question scores 2/5 in both arms.
The matrix has no universal quality pass.
That question does not show a cache-specific regression.
One judge and six questions per configuration cannot establish general quality
equivalence. These results also do not validate the new GEMM-routing candidate.
Length-capped one-, 32- or 64-token speed samples are not complete-answer evidence.

## 8. Performance evaluator and native operator data

### 8.1 Purpose and accuracy boundary

The evaluator combines actual instruction traces with measured component costs.
Its portable examples retain frozen models, error bounds, and independent test results.
QEMU supplies instruction and numerical evidence; it does not simulate K1 cycle timing.
A component-cost estimate is not a verified full-model latency prediction.
All performance candidates remain available in this evaluator.
Its accuracy checks do not use candidate elimination gates.

The [V7 audit](2026-10-12-k1-model-v7.md) fixes 28 configuration groups before measurements.
It uses 19 groups to calibrate errors and reserves nine groups for independent tests.
The groups include 1, 2, and 4 accumulator chains with 0–9 independent integer instructions.
Each configuration has two arms and 8, 32, or 128 unrolled iterations.
Both arms also change input-register reuse; instruction order is not the only difference.

| V7 check | Recorded result |
| --- | --- |
| Numerical scope | 168 native complete dumps match QEMU for the same ELF; all-one signed 8-bit inputs |
| Actual traces | 336 complete traces; vendor QEMU 10.0.2 executes the IME ELF |
| Native timing | CPU 0; 512/2048/8192 loops; seven repetitions; raw user-cycle event 0x22 |
| Samples | 2,394 calibration samples; 1,134 reserved-test samples |
| Frozen ratio-error factor | 2.1216883936561333 |
| Interval coverage | 9/9 reserved groups and 27/27 unrolled versions |
| Point-direction agreement | 9/27 versions |
| Absolute gain error | Median 29.540 percentage points; maximum 50.990 percentage points |
| Portable replay | Identical key predictions on the local host and K1; 62 tool checks pass |

Five two-chain reserved groups contain 15 versions with an incorrect predicted direction.
The single-chain measurements are near zero and do not establish a statistically supported change.
The reserved set contains no four-chain group.
Wide interval coverage does not establish reliable point predictions or an optimization priority order.
Nine observed groups cannot confirm a population coverage rate of 95%.
The stated coverage requires exchangeable groups within the fixed binary and data scope.
The target is the next paired fixture measurement, not a noise-free hardware mean.

The all-one numerical fixture does not establish correctness for arbitrary data.
Upstream QEMU 11.1.1 rejects the ELF with an illegal instruction; the failure record remains.
Vendor QEMU executes the same ELF with VLEN 256.
Frequency snapshots read 1,600,000 kHz but do not establish a constant frequency during each measurement.
V7 replay takes approximately 0.44 s locally and 8.11 s on K1 after integrity checks.
Those times measure the host tool, not the target algorithm.
V7 server replay remains pending.

V5 retains its 7/9 coverage gap.
V6's 9/9 aligned-loop group coverage does not transfer to mixed IME loops.
Shared-cache traffic, multithread synchronization costs, and full IME operator time remain pending.
A gem5 backend calibrated on K1 is not implemented.
Independent prediction confidence for arbitrary new algorithms is not established.

### 8.2 First native operator training batch

The [operator report](2026-10-12-k1-operator-data.md) records a successful first batch.
The run covers October 12, 2026, 09:24:08–09:25:44 Asia/Singapore.
It holds the shared board lock and exits with code 0.
The local host and project server verify identical summaries and receipts.

| Batch item | Verified scope |
| --- | --- |
| Shape groups | 16 training groups; eight per operator family |
| Configurations | 32; one-thread and four-thread settings per shape |
| Numerical dumps | 64; paired versions match byte for byte |
| Timing observations | 1,344; all retained |
| IME worker observations | 1,680 |
| File receipts | 327 final hashes and 97 hashes fixed before measurements |
| Independent numerical checks | Reference outputs, guards, unchanged inputs, and state write-back pass |
| Calibration and reserved tests | Not measured |

The IME data call the actual M4 kernel with K32 packing.
They exclude production packing, tile scheduling, and backend synchronization.
Four threads retain the work per thread and increase total output columns.
The SSM data measure the complete convolution graph, including layout conversion and state write-back.
They keep total work fixed between one-thread and four-thread settings.
The convolution kernel length is 4 and the sequence count is 1.
Both families reuse warm inputs from fixed numerical fixtures.
These data do not represent the shape frequencies or cache states of full model inference.

The next table first takes the median paired time reduction for each configuration.
It then reports the median and range across the eight configurations in that row.
Positive values mean a faster candidate.
These ranges are observed training results, not prediction confidence intervals.

| Operator scope | Threads | Configurations | Median reduction | Configuration range |
| --- | ---: | ---: | ---: | --- |
| IME M4 kernel slice | 1 | 8 | -12.90% | -14.63% to -10.48% |
| IME M4 kernel slice | 4 | 8 | -12.73% | -19.26% to -1.60% |
| SSM convolution graph | 1 | 8 | 37.68% | 2.36% to 92.00% |
| SSM convolution graph | 4 | 8 | -0.90% | -41.26% to 82.68% |

All 16 IME configurations have negative median reductions.
Convolution results depend on the shape and thread count.
The batch retains all candidates and all observations.
It records 1,853 involuntary IME thread switches.
The generic instruction event's user filter still needs an independent check.
Foreground-thread cycles do not represent all convolution graph threads.

The first batch chooses the common iteration count from the control arm only.
Its shortest formal sample is 0.864482 ms.
Fixed overhead and scheduler variation can affect short samples.
The revised collector probes both versions twice and raises the common count until all four probes reach 10 ms.
This revision has no verified second native batch.
Each operator family reserves 19 calibration shapes and nine independent test shapes.
Thread configurations of one shape remain in one group.
The model must freeze before calibration; its error bounds must freeze before independent tests.
Training observations cannot serve as independent test evidence.

### 8.3 Connection interruption and recovery status

K1 remote access fails during preparation for the second batch.
The available records cannot distinguish power loss, reboot, network failure, or remote-service failure.
They do not confirm a second-batch start.
A client disconnect does not establish that a board task stops.
The [connection report](2026-10-12-k1-connection-interruption.md) retains that uncertainty.

The bounded remote client disables connection reuse and limits the total client wait.
It records unverified board task status as `unknown` and does not dispatch automatic retries.
Six local fake-client tests pass; actual recovery tests remain pending.
Board work waits for the requested physical check.
After access returns, task, tmux, lock, and batch records must be checked before any authorized restart.
This documentation update does not resume the stopped combination or operator collection.

## 9. Reproduction and deliverables

Use the [deployment guide](../README.md) for model preparation and the historical
patch stack. The [current infrastructure release](../release/README.md) pins the later
`a990751` source and packages its measured RVV/routing code with exact source
hashes. The older patch helper targets `5ad05d8`; use separate checkouts.
Routing remains opt-in, and unsuccessful SSM/K32 candidates stay disabled.
The [fresh release verification](2026-10-07-release-verification.md) passes a
complete clean build and 104 exact production graph cases per routing arm.
All four code responses stop naturally and pass 106 held-out checks each.
All 35 archived artifacts and source/build/runtime checks pass; both exit
statuses are zero. The one-pair natural-code observations show 508/521 tokens
with identical baseline/optimized/prior text. They support package verification,
without adding a new statistical speedup or general quality claim.

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

## 10. Release decisions and optional further work

The bounded infrastructure release is verified and reproducible. The current
submission report, evidence appendix, source package and test records form the
completed deliverable. ARM/x86 comparison is excluded from the release scope.

The strongest replicated long-input result is the activated RVV F16 attention
kernel. The opt-in production GEMM routing also improves measured
prefill and bounded decode on both required models while preserving tested
outputs. Its scope is the current board/runtime and the recorded workload;
the release packages the measured mechanisms within that scope. Routing
remains opt-in.

Combined mode has independent 8k phase measurements and a complete-answer
pilot. The release uses direct decoding and keeps routing opt-in. Baseline
citation errors, native RS rollback mismatches and the advanced context cases
remain documented limitations; they require separately declared follow-up
protocols if pursued. Further unused infrastructure leads are
shared K packing across grouped query heads, a Q4_0 RVV lookup-table prototype,
and compiler comparisons for measured hotspots. Their platform fit and primary
research references are in the [October 3 research review](2026-10-03-infrastructure-research.md).
The [October 6 source audit](2026-10-06-next-infrastructure-methods.md) identifies
channels-major SSM convolution with an RVV channel loop and shared dense FFN activation packing.
It also requires separate decode attribution before changes to the worker schedule. The [repaired convolution screen](2026-10-06-ssm-conv-repaired-results.md)
now passes 432 exact graph cases in each of four arms. RVV graph time falls
73.72%/78.93% at 32 tokens for the 2B/4B shapes but rises 69.00%/85.10% at
one token. This rejects unconditional replacement; full-model state and timing
were skipped in that unconditional screen. The subsequent [hybrid complete-answer
pilot](2026-10-06-ssm-complete-answer-results.md) selects RVV only for batches
of at least 32 tokens. Three arms pass 432 graph cases each; both models pass
16 exact mixed-chunk/reset/RS-reference-fallback comparisons. All 24 answers
stop naturally and all 12 pairs are text-identical. Total answer latency falls
2.92%/2.13% for 2B/4B, while absolute usefulness remains 2/6 and 5/6. Shared
model errors and gains below the >3% gate prevent adoption. RS reference
fallback does not resolve rollback qualification. No production defaults change.
The [same-seed clean local reference](2026-10-06-local-clean-reference-results.md)
uses the exact GGUFs and unpatched matching source on generic x86 CPU, without
custom K1 paths, flash attention or MTP. All model/source/request hashes pass.
It reproduces the 2B wrong sum and missing citations, and both models still
fail interval code. Useful answers are 1/6 and 5/6 locally, versus 2/6 and 5/6
on both board arms; one local 4B answer is length-capped. This supports limits
of the tested weights/settings without proving causality for every earlier
optimization across different CPUs. Local timing is not a matched x86/K1
performance comparison.

The [October 7 sustained-decode diagnostic](2026-10-07-decode-packing-results.md)
passes 104 production graph cases in each of three arms and eight matched cold
requests with exact prompt/token/text identity. Four decode profiles and all
86 artifact hashes are verified. Duplicate FFN branch packing costs only
0.024–0.035% of summed GEMM worker elapsed, so a shared-packing implementation
is not pursued. IME assembly accounts for 48.61–66.57% of sampled self CPU;
approximately 20% is calling-thread synchronous waiting, which is not proven
removable wall time. No new acceleration or useful-answer result is claimed.
The [fixed K32 M1 inner-loop specialization](2026-10-07-ime-m1-k32-results.md)
then passed 480 raw cases, 104 production cases per arm and all actual FFN/full
output-head comparisons. Its 144 operator measurements produced no gain above
both 3% and control spread; the candidate remains disabled. Full-model and
useful-answer stages were skipped, so it adds no measured inference speedup.
Separate load scheduling/dataflow, output-head partitioning and dependency-
preserving worker-barrier changes remain unmeasured leads.

Remaining advanced coverage limits include unmeasured 4B/32k and 64k
workloads, unresolved MTP
long-code identity, and unavailable measured GPU offload/full paged scheduling.
These are stated explicitly so the submission represents the completed work.

Validation priorities and primary-source practices for these remaining checks
are documented in the [October 3 validation review](2026-10-03-validation-practice.md).

## 11. Current handover and remaining work

| Area | State at the evidence cutoff | Next evidence needed |
| --- | --- | --- |
| Pinned RVV/routing release | Verified; routing stays opt-in | A new protocol for any broader quality claim |
| Independent B1-r2/C1/C2-r2/C3 candidates | Measured within their stated limits; not production defaults | New release tests before integration |
| Combined-r1 | Failed one declared decode gate; stopped | A separately declared revised-candidate protocol |
| Dispatch revision | Local path checks and syntax check pass | Native numerical, assembly, operator, and model checks |
| V7 evaluator | Portable evidence replay passes; point directions unreliable | Target-algorithm costs and independent error data |
| Operator data | First training batch verified on two hosts | Native checks for longer samples; separate calibration and tests |
| Board access | Remote failure confirmed; physical cause unknown | Physical check and bounded task/lock inspection |
| Initial-to-final speedup | No matched complete comparison | Fixed-source, fixed-model direct regression |

The strongest replicated long-input result remains the RVV attention comparison.
Routing adds measured phase gains on its optimized control.
Later individual gains do not override the combined regression or shared quality failures.
The project retains negative results, unresolved mechanisms, and incomplete measurements.
