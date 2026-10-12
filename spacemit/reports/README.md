# Reports index

## K1 performance evaluator

- [Model tools](../bench/qemu-screen/predictor/README.md): portable cost estimates and fixed examples.
- [V7 audit](2026-10-12-k1-model-v7.md): broad bounds and incorrect point directions remain visible.
- [Operator data](2026-10-12-k1-operator-data.md): 32 training configurations, exact paired dumps, and 1,344 observations.
- [Connection interruption](2026-10-12-k1-connection-interruption.md): confirmed access failures, unknown hardware cause, and recovery steps.

All performance candidates remain available. Calibration and test shapes remain separate from the new training data.
Git stores text evidence and receipts. Full archives remain on the local host and the project server.
Archive checks require the retained archives. Portable examples include their own replay data.

For the current work and the commands, use the
[documentation guide](../DOCS.md). A historical queue statement describes the
date of its report.

## Current report package

Evidence cutoff: October 12, 2026, Asia/Singapore.

- [PDF report](SUBMISSION-REPORT.pdf): the technical report and evidence appendix.
- [Standalone TeX](SUBMISSION-REPORT.tex): source for the PDF.
- [Report text](SUBMISSION-REPORT.md): editable report with current results and limits.
- [Evidence appendix](SUBMISSION-EVIDENCE.md): claim-to-record map and check commands.
- [Export instructions](REPORT-BUILD.md): repeatable document export.
- [Combined stop audit](2026-10-12-combined-stop-audit.md): one decode gate fails; second-round and complete-answer tests do not run.

The pinned release remains the October 7 package.
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
