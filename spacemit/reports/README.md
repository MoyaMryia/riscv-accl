# Reports index

Document check: October 21, 2026, Asia/Singapore.
[Requirements.md](../../Requirements.md) is the sole current acceptance reference.

- [Complete multi-turn v2 measurement](2026-10-21-fixed-multi-turn-v2-results.md): all 48 requests complete. Independent review finds 15/24 correct answers for 2B and 19/24 for 4B.
- [Local replay and gate audit](2026-10-21-local-multi-turn-gate-audit.md): five of six failed answers remain incorrect on x86. Five probe cases expose errors in the v1 checks. The v2 audit checks 32 saved answers against an independent reference.
- [Fixed multi-turn acceptance](2026-10-21-fixed-multi-turn-results.md): six conversations pass and six fail. The batch completes 32 of 48 planned turns and exits with status 2.
- [Router version check](2026-10-21-routing-version-clarification.md): the model remains `bert-router-v1`. The later gain study uses a prompt rule, not new BERT weights.
- [Official checkpoint conversion](2026-10-21-official-conversion.md): both models converted, quantized, and packaged. Tensors, types, and tokenizer data match the delivered files. The chat template differs.
- [MTP docstring rule](2026-10-21-2b-mtp-docstring-rule-validation.md): a prompt-only rule yields 3.48% net time gain on a code grid. The family-cluster interval is 1.30% to 5.10%. Code requests without a docstring requirement save 12.0% on average.
- [BERT router regression](2026-10-18-2b-bert-router-results.md): 24 complete answers; three code requests select MTP, but total wall time increases 0.105342%.
- [BERT intent classifier](2026-10-18-2b-bert-classifier.md): CPU fine-tune reaches 83/96 correct labels; K1 classification takes 78.879218 ms median and 270.697719 ms P95.
- [2B router end-to-end test](2026-10-18-2b-router-e2e.md): 30 complete answers; automatic selection uses direct for all 12 tasks and adds 0.044487% wall time.
- [2B decoder router](2026-10-18-2b-decoder-router.md): a 161262-byte classifier; 23/24 task labels match, and K1 decision latency has a 3.210042 ms median.
- [2B MTP investigation](2026-10-17-2b-mtp-head-investigation.md): a 64k prefix covers 32.16–34.24% of tokens in three Chinese answers; replay adds target corrections to acceptance counts.
- [r3 MTP first pair](2026-10-17-r3-mtp-first-pair.md): 2B complete-answer time falls 23.32%; both identical 508-token answers pass 106 checks.
- [Final-build capacity extension](2026-10-16-ultralong-final-comparison.md): 12 matched requests at 16k and 32k inputs; ordinary context remains 12288.
- [Final-build TCM trace](2026-10-16-final-release-tcm.md): device access during two short requests, heap fallback, and the user API.
- [Final default comparison](2026-10-14-final-default-comparison.md): one compiled default for both models, original compatibility baseline, 28 matched requests, quality checks, and retained limits.
- [Fixed default delivery](../final-release/README.md): archive identity and normal startup.
- [Current gap report](2026-10-13-requirements-gap.md): each basic, score, advanced, and measurement item maps to evidence and missing checks.
- [Result index](RESULTS.md): baseline, optimized release, independent candidates, and negative results.
- [Deployment guide](../DEPLOYMENT.md) and [test guide](../bench/TESTS.md): callable procedures, locks, and completion records.
- [File organization and checks](2026-10-13-project-file-organization.md): this task and its local check logs.
- [Live inspection and scalar schedule](2026-10-13-k1-live-inspect-and-scalar-schedule.md): existing C1, actual hotspots, exact checks, and a failed performance screen.
- [TCM access audit](2026-10-13-k1-tcm-access.md): ordinary user permissions and successful sudo access to four real blocks.
- [History guide](HISTORY.md): dated exports and earlier source packages.

## K1 performance evaluator

- [Finite fragment timing R4](2026-10-13-k1-fragment-timing-r4.md): complete-call point estimates and 840 native observations. Same-family checks retain a 30.70% maximum cycle error.
- [Complete fragment calls R3](2026-10-12-k1-fragment-call-r3.md): six complete calls include library paths. K1 selects the same vector clear function. Cycle predictions remain unavailable.
- [Fragment source workflow R2](2026-10-12-k1-fragment-source-r2.md): real Q8 payload code, 360 native observations, exact output checks, and WG peer transfer. Full-function predictions remain unavailable.
- [Code fragment evaluator R1](2026-10-12-k1-fragment-evaluator-r1.md): a bounded pair interface, 87 tool checks, and identical replay on two hosts. Two historical misses remain.
- [CPU completion model R8](2026-10-12-k1-cpu-completion-model-r8.md): 312 new functions and 9,360 samples. Mechanism cycle errors improve, but two positive pairs remain missed.
- [CPU model methods R7](2026-10-12-k1-cpu-model-research-r7.md): 482 scalar loops compare LLVM with frozen models. Historical positive direction agreement is 12/36 for LLVM.
- [CPU queue model R6](2026-10-12-k1-cpu-queue-model-r6.md): 9/9 fixed groups covered with a wide bound; gain and rank errors remain.
- [CPU write model R5](2026-10-12-k1-cpu-write-model-r5.md): 168 new functions retain a 2.7143 cycle error factor. Source swaps do not explain the gap.
- [CPU probes R4](2026-10-12-k1-cpu-mechanism-probes-r4.md): 18 fixed scalar pairs improve; write hazards retain large cycle errors.
- [CPU state model R3](2026-10-12-k1-cpu-state-model-r3.md): 306 loops, 13/13 group coverage with a wide bound, and 26 slower candidates.
- [CPU state model R2](2026-10-12-k1-cpu-state-model-r2.md): semantic checks, 12,012 samples, 7/9 group coverage, and 18/18 direction agreement. Gain errors remain.
- [CPU state model R1](2026-10-12-k1-cpu-state-model-r1.md): native probes, frozen state estimates, 7/9 group coverage, and retained prediction failures.

- [Model tools](../bench/qemu-screen/predictor/README.md): portable cost estimates and fixed examples.
- [V7 audit](2026-10-12-k1-model-v7.md): broad bounds and incorrect point directions remain visible.
- [Operator data](2026-10-12-k1-operator-data.md): 32 training configurations, exact paired dumps, and 1,344 observations.
- [Fixed operator shape model](2026-10-12-k1-operator-model-v1.md): frozen models, independent calibration and tests, portable replay, and retained convolution failures.
- [Second operator batch](2026-10-12-k1-operator-data-r2.md): direct access, longer samples, 1,344 more observations, and identical replay on two hosts.
- [Connection interruption](2026-10-12-k1-connection-interruption.md): confirmed access failures, unknown hardware cause, and recovery steps.

All performance candidates remain available. Calibration and test shapes remain separate from the new training data.
Git stores text evidence and receipts. Full archives remain on the local host and the project server.
Archive checks require the retained archives. Portable examples include their own replay data.

For the current work and the commands, use the
[documentation guide](../DOCS.md). A historical queue statement describes the
date of its report.

## Report packages

The English report, appendix, TeX, and PDF include the October 16 supplements to the fixed default delivery.
The complete October 12 report remains in [the snapshot directory](snapshots/2026-10-12/receipts.json).
The new results do not close official model origin, full conversion, long state, or multi-turn acceptance gaps.
Use the [history guide](HISTORY.md) for these limits.

- [Chinese submission draft](SUBMISSION-ZH.md): current requirements, vendor source identity, measured gains, repeat commands, and open acceptance items.
- [PDF report](SUBMISSION-REPORT.pdf): the technical report and evidence appendix.
- [Standalone TeX](SUBMISSION-REPORT.tex): source for the PDF.
- [Report text](SUBMISSION-REPORT.md): editable source of the current English report.
- [Evidence appendix](SUBMISSION-EVIDENCE.md): claim-to-record map and check commands.
- [Export instructions](REPORT-BUILD.md): repeatable document export.
- [Combined stop audit](2026-10-12-combined-stop-audit.md): one decode gate fails; second-round and complete-answer tests do not run.

The fixed default delivery is r3. The October 7 package remains a historical reference.
Later candidates and performance-model work have separate evidence boundaries.
The October 11 snapshots predate the combination stop.
The root `FINAL-REPORT.md` and September TeX/PDF remain historical reports.
No external competition submission is recorded.

## Current measurements and validation

- [K1 model V7](2026-10-12-k1-model-v7.md): an independent IME mixed-loop error audit, broad intervals, wrong point directions, and portable replay on K1.

- [K1 model V6](2026-10-12-k1-model-v6.md): direct loop costs, independent group checks, and a portable model package with identical results on two hosts.

- [K1 model V5](2026-10-12-k1-model-v5.md): mixed sequence estimates, independent interval misses, and a count-cost assumption audit.

- [K1 model V4](2026-10-12-k1-model-v4.md): wait attribution, mixed load-use checks, and reserved group coverage limits.

- [K1 model V3](2026-10-12-k1-model-v3.md): user-mode counter audit, repeated component measurements, a calibrated operator example, and shared memory diagnostics.

- [K1 performance model infrastructure](2026-10-11-k1-model-v2.md): native component costs, portable trace estimates, investment priorities, and explicit accuracy limits.
- [Project progress through October 11](2026-10-11-project-progress.md): matched
  gains from the initial campaign, later candidate results, and limits of a
  cumulative comparison. The later [stop audit](2026-10-12-combined-stop-audit.md) records a failed decode gate.
- [Original and current version comparison](2026-10-11-original-current-comparison.md):
  source boundaries, paired phase times, and a CSV with measured and pending
  values. C0 is an optimized control, not the initial vendor version.

The
[fresh release verification](2026-10-07-release-verification.md) passes the
complete clean build, 104 exact native cases per routing arm, and all four
naturally stopped code answers. Each answer passes 106 held-out checks. The
current [pinned package](../release/README.md) is reproducible. Routing
remains opt-in.

The
[hybrid SSM complete-answer campaign](2026-10-06-ssm-complete-answer-results.md)
is complete. The graph and state checks pass, and all 24 answers stop
naturally. There are 12 identical pairs. The total latency falls 2.92% and
2.13%. The usefulness remains 2/6 and 5/6. The declared adoption gates fail,
and its monitor is paused.

| Report | Scope |
| --- | --- |
| [Fresh release verification](2026-10-07-release-verification.md) | Complete clean build, native dump identity, four passing complete answers, and 35 independently verified artifacts; one pair per model, no new statistical speed claim |
| [Fixed K32 M1 specialization](2026-10-07-ime-m1-k32-results.md) | 480 raw cases, 104 production cases per arm, and six actual FFN/full-output shapes pass exact identity; all 144 operator samples fail advancement, candidate disabled, model stages skipped |
| [Decode and FFN packing results](2026-10-07-decode-packing-results.md) | Eight exact matched requests, four decode profiles, and 104 native cases per arm; duplicate packing only 0.024–0.035% of GEMM worker elapsed, candidate declined; calling-thread sync CPU is not wall savings; 86 artifacts verified |
| [Decode clock/startup repair](2026-10-07-decode-clock-repair.md) | An explicit monotonic perf clock and a separate startup compatibility-probe inventory preserve the strict request audits; a targeted exact-output validation precedes the successful full run |
| [Local clean-reference quality](2026-10-06-local-clean-reference-results.md) | Same GGUFs, prompts, and seed on a clean generic x86 CPU; 11 natural answers and one cap, useful 1/6 and 5/6 against board 2/6 and 5/6; existing arithmetic, citation, and code errors persist; no causal or speed claim across hardware |
| [Hybrid SSM complete answers](2026-10-06-ssm-complete-answer-results.md) | 432 cases per three arms, 32 exact model-state comparisons, and 24 natural answers; unchanged quality, small complete-answer gains below the adoption threshold; 114 artifacts verified |
| [Repaired convolution/RVV screen](2026-10-06-ssm-conv-repaired-results.md) | Four arms pass 432 cases each; 72 operator samples show RVV graph time −73.72%/−78.93% at 32 tokens, but +69.00%/+85.10% at one token; model gates skipped, 97 artifacts verified |
| [SSM history-copy diagnosis](2026-10-06-ssm-history-diagnosis.md) | A dated repair diagnosis. The later graph/state and complete-answer checks pass, but the hybrid candidate misses the adoption gates |
| [Channels-major convolution/RVV screen](2026-10-06-ssm-conv-rvv-results.md) | A correctness failure: layout mode history write-back. The original and control pass 432 cases each. RVV and model timing are skipped. 23 collected artifacts are verified |
| [Next infrastructure methods](2026-10-06-next-infrastructure-methods.md) | A dated source audit. The convolution, decode/packing, and fixed-K32 M1 follow-ups are measured above. Separate load scheduling and worker-barrier work remain optional leads |
| [Measured K1 roofline](2026-10-06-k1-roofline-results.md) | Complete: 150 memory scans, 24 matching direct requests, and two profiles; approximately 7 GB/s and confirmed routing gains; the traffic references are not proof of a hardware limit |
| [Resumed measurements](2026-09-27-resumed-measures.md) | A verified matrix, actual 16k pairs, 2B 32k feasibility, weights, completed diagnostics, and negative GPU findings |
| [Local verification](2026-09-28-local-verification.md) | Matrix reproduction, corrected fractional Welch intervals, and 32k scaling; no new board measurements |
| [Chat quality](2026-09-30-chat-quality-benchmark.md) | A completed 24-pair matrix. 2B/4k requires a review. Three descriptive pilot stages pass |
| [Shared document cache](2026-09-29-shared-document-cache.md) | Changed-question tests. Truncated-answer judge marks are not complete-answer quality evidence |
| [October 2 profile](2026-10-02-prefill-profile.md) | A complete cold-prefill profile, resolved IME GEMM hotspots, and collection recovery |
| [IME scheduling](2026-10-02-ime-scheduling.md) | Five variants pass the native checks. Neither operator screen qualifies for model testing |
| [Recurrent prefill](2026-10-02-recurrent-prefill.md) | Complete: 158 numerical cases pass. Operator time falls 24–28%. The 2B/512 prefill falls 2.38%, below the 3% gate |
| [Attention infrastructure](../experiments/2026-10-02-attention-infrastructure.md) | Complete: direct-V operator gains fail the full-model gates; runtime findings and a completed GEMM staging attribution |
| [October 3 infrastructure research](2026-10-03-infrastructure-research.md) | A complete GitHub/arXiv/Scholar review and GEMM routing tests; verified model gains and remaining unused candidates |
| [October 3 staged validation](2026-10-03-staged-validation-results.md) | The combined routing clears the 8k phase gates. The 2B citation and the RS rollback gates remain open. 4B/32k is skipped |
| [Checkpoint MTP usefulness](2026-10-03-mtp-usefulness-results.md) | 24 complete requests. The relative quality gates pass, and the total latency falls 8.63% and 15.22%. Shared correctness failures and slower prose prevent a general adoption |
| [Adaptive MTP infrastructure](2026-10-05-adaptive-mtp-results.md) | 54 timing requests. Code throughput rises 50.74% and 53.35%. But capped and incorrect code, and non-code overhead, prevent the qualification. Grading recovery completed |
| [October 1 update](2026-10-01-fast-method.md) | Complete layout and quality evidence, and an implementation of the staged fast method |

## Validation plan

[Long-context and MTP validation practice](2026-10-03-validation-practice.md):
a GitHub/Scholar review and prioritized proposed checks. This report has no new
board result.

## Source audits and integration history

- [Code audit](2026-09-30-code-optimization-audit.md): source hypotheses and
  provenance, with later experiment updates.
- [PR #1 review](2026-09-30-pr1-review.md): historical findings. The PR merged,
  and the local fixes are complete.

## Earlier campaign snapshots

- [2026-09-21 baseline](2026-09-21-final.md): short-prompt results, despite the
  historical "final" title.
- [2026-09-23 draft vocabulary](2026-09-23-frspec.md).
- 2026-09-24: [integrated kernels](2026-09-24-integrated-k1.md),
  [ngram](2026-09-24-ngram.md), [spec settings](2026-09-24-spec-sweep.md),
  [low acceptance](2026-09-24-lowacc.md),
  [CPU sampling](2026-09-24-cpu-sampling.md),
  [mapped CPU sampling](2026-09-24-mapped-cpu-sampling.md), and
  [research scan](2026-09-24-research-next.md).
- [2026-09-25 lifecycle](2026-09-25-lifecycle.md): chronological campaign
  notes.
- 2026-09-27: [completed gates](2026-09-27-completed-gates.md),
  [requirements audit](2026-09-27-requirements-audit.md), and
  [original requirements and work plan](2026-09-27-next-steps-and-measures.md).
  The later coverage and diagnostics are in the resumed measurements.
- [2026-09-28 long-prefill research](2026-09-28-long-prefill-research.md):
  research as of that date. The external speedups are not K1 measurements.

`raw/` holds the reproducible artifacts and the generated summaries. The report
numbers stay with their workload, source, and output-length limits.

The [PDF export](k1-llm-inference-optimizations.pdf) and its
[LaTeX source](k1-llm-inference-optimizations.tex) are the 2026-09-24 kernel
campaign report. They do not include the later RVV, long-context,
cache-quality, or compact-layout/GEMM-routing work. Read its speculative
exactness and bandwidth statements with the later corrections in the submission
report. Use the submission package for the current evidence summary.
