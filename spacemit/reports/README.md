# Reports index

For current work and commands, use the [documentation guide](../DOCS.md).
Historical queue statements describe the report's date.

## Submission package

- [SUBMISSION-REPORT.md](SUBMISSION-REPORT.md): current consolidated report, evidence through October 7, 2026.
- [SUBMISSION-EVIDENCE.md](SUBMISSION-EVIDENCE.md): claim-to-artifact map, model/build identities and verification commands.

Submit the report with the appendix. The older root `FINAL-REPORT.md` and
September 24 PDF/LaTeX export retain historical campaign claims; they are not
the current submission. No files have been submitted externally.

## Current measurements and validation

The [fresh release verification](2026-10-07-release-verification.md) passes the
complete clean build, 104 exact native cases per routing arm and all four
naturally stopped code answers, each passing 106 held-out checks. The current
[pinned package](../release/README.md) is reproducible; routing remains opt-in.

The [hybrid SSM complete-answer campaign](2026-10-06-ssm-complete-answer-results.md)
is completed. Graph/state checks pass and all 24 answers stop naturally, with
12 identical pairs. Total latency falls 2.92%/2.13%; usefulness remains 2/6
and 5/6. The declared adoption gates fail; its monitor is paused.

| Report | Scope |
| --- | --- |
| [Fresh release verification](2026-10-07-release-verification.md) | Complete clean build, native dump identity, four passing complete answers and 35 independently verified artifacts; one pair per model, no new statistical speed claim |
| [Fixed K32 M1 specialization](2026-10-07-ime-m1-k32-results.md) | 480 raw cases, 104 production cases per arm and six actual FFN/full-output shapes pass exact identity; all 144 operator samples fail advancement, candidate disabled, model stages skipped |
| [Decode and FFN packing results](2026-10-07-decode-packing-results.md) | Eight exact matched requests, four decode profiles and 104 native cases per arm; duplicate packing only 0.024–0.035% of GEMM worker elapsed, candidate declined; calling-thread sync CPU is not wall savings; 86 artifacts verified |
| [Decode clock/startup repair](2026-10-07-decode-clock-repair.md) | Explicit monotonic perf clock and separate startup compatibility-probe inventory preserve strict request audits; targeted exact-output validation precedes the successful full run |
| [Local clean-reference quality](2026-10-06-local-clean-reference-results.md) | Same GGUFs/prompts/seed on clean generic x86 CPU; 11 natural answers and one cap, useful 1/6 and 5/6 versus board 2/6 and 5/6; existing arithmetic/citation/code errors persist; no causal or speed claim across hardware |
| [Hybrid SSM complete answers](2026-10-06-ssm-complete-answer-results.md) | 432 cases per three arms, 32 exact model-state comparisons, 24 natural answers; unchanged quality, small complete-answer gains below adoption threshold; 114 artifacts verified |
| [Repaired convolution/RVV screen](2026-10-06-ssm-conv-repaired-results.md) | Four arms pass 432 cases each; 72 operator samples show RVV graph time -73.72%/-78.93% at 32 tokens but +69.00%/+85.10% at one token; model gates skipped, 97 artifacts verified |
| [SSM history-copy diagnosis](2026-10-06-ssm-history-diagnosis.md) | Dated repair diagnosis; later graph/state and complete-answer checks pass, but the hybrid candidate misses adoption gates |
| [Channels-major convolution/RVV screen](2026-10-06-ssm-conv-rvv-results.md) | Correctness failure: layout mode history write-back; original/control pass 432 cases each, RVV and model timing skipped; 23 collected artifacts verified |
| [Next infrastructure methods](2026-10-06-next-infrastructure-methods.md) | Dated source audit; convolution, decode/packing and fixed-K32 M1 follow-ups measured above; separate load scheduling and worker-barrier work remain optional leads |
| [Measured K1 roofline](2026-10-06-k1-roofline-results.md) | Completed: 150 memory scans, 24 matching direct requests and two profiles; approximately 7 GB/s and confirmed routing gains; traffic references are not hardware-limit proof |
| [Resumed measurements](2026-09-27-resumed-measures.md) | Verified matrix, actual 16k pairs, 2B 32k feasibility, weights, completed diagnostics and negative GPU findings |
| [Local verification](2026-09-28-local-verification.md) | Matrix reproduction, corrected fractional Welch intervals, 32k scaling; no new board measurements |
| [Chat quality](2026-09-30-chat-quality-benchmark.md) | Completed 24-pair matrix; 2B/4k requires review; three descriptive pilot passes |
| [Shared document cache](2026-09-29-shared-document-cache.md) | Changed-question tests; truncated-answer judge marks are not complete-answer quality evidence |
| [October 2 profile](2026-10-02-prefill-profile.md) | Completed cold-prefill profile, resolved IME GEMM hotspots and collection recovery |
| [IME scheduling](2026-10-02-ime-scheduling.md) | Five variants pass native checks; neither operator screen qualifies for model testing |
| [Recurrent prefill](2026-10-02-recurrent-prefill.md) | Completed: 158 numerical cases pass; operator time falls 24-28%, 2B/512 prefill falls 2.38%, below the 3% gate |
| [Attention infrastructure](../experiments/2026-10-02-attention-infrastructure.md) | Completed: direct-V operator gains fail full-model gates; runtime findings and completed GEMM staging attribution |
| [October 3 infrastructure research](2026-10-03-infrastructure-research.md) | Completed GitHub/arXiv/Scholar review and GEMM routing tests; verified model gains and remaining unused candidates |
| [October 3 staged validation](2026-10-03-staged-validation-results.md) | Combined routing clears 8k phase gates; 2B citation and RS rollback gates remain open; 4B/32k skipped |
| [Checkpoint MTP usefulness](2026-10-03-mtp-usefulness-results.md) | 24 complete requests; relative quality gates pass and total latency falls 8.63%/15.22%. Shared correctness failures and slower prose prevent general adoption. |
| [Adaptive MTP infrastructure](2026-10-05-adaptive-mtp-results.md) | 54 timing requests; code throughput +50.74%/+53.35%, but capped/incorrect code and non-code overhead prevent qualification; grading recovery completed. |
| [October 1 update](2026-10-01-fast-method.md) | Completed layout/quality evidence and implementation of the staged fast method |

## Validation plan

[Long-context and MTP validation practice](2026-10-03-validation-practice.md):
GitHub/Scholar review and prioritized proposed checks; no new board result.

## Source audits and integration history

- [Code audit](2026-09-30-code-optimization-audit.md): source hypotheses and provenance, with later experiment updates.
- [PR #1 review](2026-09-30-pr1-review.md): historical findings; PR merged and local fixes completed.

## Earlier campaign snapshots

- [2026-09-21 baseline](2026-09-21-final.md): short-prompt results, despite the historical "final" title.
- [2026-09-23 draft vocabulary](2026-09-23-frspec.md).
- 2026-09-24: [integrated kernels](2026-09-24-integrated-k1.md),
  [ngram](2026-09-24-ngram.md), [spec settings](2026-09-24-spec-sweep.md),
  [low acceptance](2026-09-24-lowacc.md), [CPU sampling](2026-09-24-cpu-sampling.md),
  [mapped CPU sampling](2026-09-24-mapped-cpu-sampling.md),
  [research scan](2026-09-24-research-next.md).
- [2026-09-25 lifecycle](2026-09-25-lifecycle.md): chronological campaign notes.
- 2026-09-27: [completed gates](2026-09-27-completed-gates.md),
  [requirements audit](2026-09-27-requirements-audit.md),
  [original requirements and work plan](2026-09-27-next-steps-and-measures.md).
  Later coverage and diagnostics are in the resumed measurements.
- [2026-09-28 long-prefill research](2026-09-28-long-prefill-research.md):
  research as of that date; external speedups are not K1 measurements.

`raw/` holds reproducible artifacts and generated summaries. Report numbers
are preserved with their workload, source, and output-length limits.

The [PDF export](k1-llm-inference-optimizations.pdf) and its
[LaTeX source](k1-llm-inference-optimizations.tex) are the 2026-09-24 kernel
campaign report. They do not include later RVV, long-context, cache-quality,
or compact-layout/GEMM-routing work. Its speculative exactness and bandwidth
statements must be read with the later corrections in the submission report.
Use the submission package for the current evidence summary.
