# Current documentation guide

Document check: October 22, 2026, Asia/Singapore.
[Requirements.md](../Requirements.md) is the sole current acceptance reference.
Use the [deployment guide](DEPLOYMENT.md), [test guide](bench/TESTS.md), and [result index](reports/RESULTS.md).
The [current gap report](reports/2026-10-13-requirements-gap.md) maps each requirement to evidence.
This guide records completed evidence and pending work at this check.
Dated queue statements do not establish current board activity.

## Read the reports

| Document | Purpose |
| --- | --- |
| [Chinese submission draft](reports/SUBMISSION-ZH.md) | Current requirements and bounded results |
| [Result index](reports/RESULTS.md) | Release profiles, candidate status, and raw evidence |
| [PDF report](reports/SUBMISSION-REPORT.pdf) | October 16 report with the evidence appendix |
| [TeX source](reports/SUBMISSION-REPORT.tex) | Standalone PDF source |
| [Report text](reports/SUBMISSION-REPORT.md) | Editable technical report |
| [Evidence appendix](reports/SUBMISSION-EVIDENCE.md) | Claim-to-record map, source identities, and check commands |
| [Export instructions](reports/REPORT-BUILD.md) | Document update rules and repeatable export |
| [Report topic index](reports/TOPICS.md) | 109 dated reports grouped by topic |
| [Documentation map](../docs/README.md) | Repository-wide document entry |
| [Archive inventory](../archive/README.md) | Archived and in-place historical materials |
| [Technical guide](../docs/technical-guide/technical-guide-en.md) | Platform, kernels, benchmarks, and scoring |
| [Chinese technical guide](../docs/technical-guide/technical-guide-zh.md) | Chinese version of the guide |

The English report, appendix, TeX, and PDF include the October 16 supplements to the fixed default delivery.
The [capacity extension](reports/2026-10-16-ultralong-final-comparison.md) records 12 matched requests at 16k and 32k inputs.
The [final-build TCM trace](reports/2026-10-16-final-release-tcm.md) records device access during two short requests.
The complete October 12 snapshot remains in `reports/snapshots/2026-10-12/`.
Use the [fixed default package](final-release/README.md) and [matched original comparison](reports/2026-10-14-final-default-comparison.md).
Use the [history guide](reports/HISTORY.md) for their limits.
The [October 13 board inspection](reports/2026-10-13-k1-live-inspect-and-scalar-schedule.md) confirms access and the C1 path.
The [TCM audit](reports/2026-10-13-k1-tcm-access.md) confirms four real blocks through sudo.
These diagnostics do not establish a new model speedup.

## Current decisions

| Area | Status | Evidence and limit |
| --- | --- | --- |
| Code fragment evaluator scope | Auxiliary tool; implementation remains incomplete | [Scope](experiments/2026-10-12-k1-code-fragment-evaluator-scope.md): single-thread code fragment costs and gains. Task models and detailed simulators are deferred. |
| Code fragment interface R1 | Bounded pair interface and portable replay verified | [R1](reports/2026-10-12-k1-fragment-evaluator-r1.md): four historical pairs and two retained misses. New fragment accuracy remains unverified. |
| Fragment source workflow R2 | Source and native pair workflow verified | [R2](reports/2026-10-12-k1-fragment-source-r2.md): Q8 payload gains depend on the configuration. Full-function predictions remain unavailable. |
| Complete fragment calls R3 | Selected full paths verified | [R3](reports/2026-10-12-k1-fragment-call-r3.md): library vector clear paths and a K1 target probe. Cycle predictions remain unavailable. |
| Finite fragment timing R4 | Mechanism point estimates verified | [R4](reports/2026-10-13-k1-fragment-timing-r4.md): 840 native observations and 14 same-family check cells. Maximum cycle error remains 30.70%. |
| Fixed default r3 | Verified within the frozen scope | [Final comparison](reports/2026-10-14-final-default-comparison.md): one production build, true original compatibility baseline, two models, short and long inputs. |
| October 7 reference | Verified; RVV attention and routing remain opt-in | [Release guide](release/README.md); [October 7 checks](reports/2026-10-07-release-verification.md): clean build, 104 native cases per arm, four complete code answers with 106 checks each |
| Long-input attention | Matched gains on 2B and 4B | [Measurement matrix](reports/2026-09-27-resumed-measures.md): replicated 2k/8k; single-pair 16k; 2B/32k feasibility without a matched control |
| Routing | Phase gains on the optimized baseline | [Routing results](reports/2026-10-03-infrastructure-research.md); [independent confirmation](reports/2026-10-06-k1-roofline-results.md); no cumulative project speedup |
| Independent later candidates | Selected workload gains; not release defaults | [Candidate review](reports/2026-10-09-local-candidate-result-rejudgment.md); 96 complete answers, 48 identical pairs, shared model errors remain |
| Combined-r1 | Stopped after one failed decode gate | [October 12 stop audit](reports/2026-10-12-combined-stop-audit.md): F versus B increases 4B/2048/65 decode time by 3.0220477%; later stages do not run |
| Dispatch revision | Local checks only | [Revision protocol](experiments/2026-10-12-combined-dispatch-r2-local-protocol.md); native and model checks pending |
| CPU queue model R6 | Fixed loop tools work; general evaluator remains incomplete | [R6](reports/2026-10-12-k1-cpu-queue-model-r6.md): 9/9 group coverage with a wide bound. Gain and rank errors remain. [R5](reports/2026-10-12-k1-cpu-write-model-r5.md) retains regressions. |
| CPU model methods R7 | Historical baseline comparison is complete | [R7](reports/2026-10-12-k1-cpu-model-research-r7.md): LLVM covers 482 scalar loops. Its direction agreement is 12/36 on historical positive pairs. |
| CPU completion model R8 | Scalar candidate and checks are complete | [R8](reports/2026-10-12-k1-cpu-completion-model-r8.md): 312 new functions. Mechanism errors improve, but two gains remain missed. |
| Performance evaluator V7 | Portable replay verified; point directions unreliable | [V7 audit](reports/2026-10-12-k1-model-v7.md): 9/9 group interval coverage, 9/27 point-direction agreement |
| Operator training data | Two batches verified on two hosts | [Second batch](reports/2026-10-12-k1-operator-data-r2.md): 32 distinct configurations and 2,688 training observations; later calibration and tests have separate records |
| Operator shape evaluator V1 | Fixed versions have independent tests; errors remain | [Shape model report](reports/2026-10-12-k1-operator-model-v1.md): IME direction agreement 18/18; convolution 16/18 and group coverage 8/9; no bound adjustment |
| Board access and C1 | Verified for the October 13 inspection | [Live inspection](reports/2026-10-13-k1-live-inspect-and-scalar-schedule.md); C1 also has earlier independent model checks. |
| IME scalar schedule | Exact native checks pass; performance screen fails | [Inspection and screen](reports/2026-10-13-k1-live-inspect-and-scalar-schedule.md); no new candidate model timing; release keeps the original kernel. |
| TCM access | Sudo identifies and maps four real blocks | [TCM audit](reports/2026-10-13-k1-tcm-access.md); ordinary user access fails on permissions. No bandwidth or inference gain follows. |
| 2B MTP head | Measured on three Chinese answers | [Head investigation](reports/2026-10-17-2b-mtp-head-investigation.md): a 64k prefix covers 32.16–34.24% of tokens; replay adds target corrections. |
| r3 MTP first pair | Complete answer passes 106 checks | [First pair](reports/2026-10-17-r3-mtp-first-pair.md): 2B complete-answer time falls 23.32%; both 508-token answers are identical. |
| 2B BERT router | Classifier and end-to-end runs measured | [Classifier](reports/2026-10-18-2b-bert-classifier.md): 83/96 labels correct and 78.879218 ms median; [end-to-end](reports/2026-10-18-2b-router-e2e.md): direct on all 12 tasks with 0.044487% added wall time. |
| MTP docstring rule | Prompt-only rule measured on a code grid | [Rule validation](reports/2026-10-21-2b-mtp-docstring-rule-validation.md): 3.48% net time gain with a 1.30% to 5.10% family-cluster interval. |
| Official checkpoint conversion | Both models converted and packaged | [Conversion](reports/2026-10-21-official-conversion.md): tensors, types, and tokenizer data match the delivered files; the chat template differs. |
| Fixed multi-turn v2 | 48 of 48 requests complete | [v2 results](reports/2026-10-21-fixed-multi-turn-v2-results.md): 15/24 correct for 2B and 19/24 for 4B; the user accepted the measured quality with the retained errors. |
| Natural long context | 12 of 12 answers correct | [Long-context results](reports/2026-10-22-long-context-natural-results.md): short, 16k, and 32k inputs on both models. |

The October 11 [progress snapshot](reports/2026-10-11-project-progress.md) and
[version comparison](reports/2026-10-11-original-current-comparison.md) predate the combination stop.
Use the October 12 stop audit for its later decision.
The documentation task does not resume board tests or establish automatic retries.

## Use the code and records

| Task | Guide |
| --- | --- |
| Reproduce the pinned release | [Release source, patch, and launchers](release/README.md) |
| Prepare models and apply the older patch stack | [Integration guide](README.md); [model tools](models/tools/README.md) |
| Run native and model benchmarks | [Benchmark guide](bench/README.md) |
| Use full-document cache reuse | [Local document service](serve/README.md) |
| Replay portable performance examples | [Evaluator guide](bench/qemu-screen/predictor/README.md) |
| Inspect operator data and collector limits | [Operator tools](bench/operator-data/README.md) |
| Find a dated result | [Reports index](reports/README.md) |
| Find a predeclared experiment | [Experiments index](experiments/README.md) |
| Find a dated report by topic | [Report topic index](reports/TOPICS.md) |
| Find archived material | [Archive inventory](../archive/README.md) |

The release pins official-fork `a990751` and exact measured source hashes.
The older [archived patch helper](../archive/patches-5ad05d8/apply-patches.sh) targets `5ad05d8`.
Use separate source checkouts for these packages.
The release guide supplies the current launch commands.

## Evidence rules

1. Keep the source, model, workload, precision, thread count, and cache state with each measurement.
2. Compare only matched arms from the stated campaign.
3. Keep time reductions separate from throughput increases.
4. Keep operator results separate from full-model results.
5. Use naturally complete answers to assess complete-answer quality.
6. Keep failed gates and pending checks visible.
7. Preserve every file in `reports/raw/`.

The common inference configuration uses Q4_0 weights, F16 K/V, four workers, and batch/microbatch 32.
Principal RVV and routing results use direct decoding.
MTP long-code identity remains unresolved.
Full-vocabulary verification does not establish universal numerical identity.
The optional cloud judge supplements local answer checks; inference remains local.

## Negative results and open limits

- [SSM complete answers](reports/2026-10-06-ssm-complete-answer-results.md): exact states and 24 natural answers pass; 2.92%/2.13% gains miss adoption gates.
- [Decode and packing audit](reports/2026-10-07-decode-packing-results.md): duplicate FFN packing is 0.024–0.035% of summed worker elapsed time; no implementation follows.
- [Fixed K32 M1 screen](reports/2026-10-07-ime-m1-k32-results.md): numerical checks pass; 144 operator samples do not qualify; model stages do not run.
- [Adaptive MTP](reports/2026-10-05-adaptive-mtp-results.md): code throughput gains do not establish faster useful answers; absolute correctness and overall time gates fail.
- [Cache quality](reports/2026-09-30-chat-quality-benchmark.md): 24 complete pairs; 2B/4k needs review; no universal quality pass.
- [GPU and page checks](reports/2026-09-27-resumed-measures.md): zero transferred OpenCL layers; no measured GPU or full paged-scheduler gain.

4B/32k and 64k performance remain unmeasured.
Sudo can identify and map real TCM.
Actual inference buffer placement and its performance effect remain unverified.
The missing `/dev/tcm_sync_mem` interface is a separate issue.
Sampled CPU shares and traffic references do not establish removable wall time or a hardware performance limit.
A matched initial-vendor-to-final-combination regression does not exist.
The report retains further numerical, quality, and archive limits.
