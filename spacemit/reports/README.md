# Reports index

For current work and commands, use the [documentation guide](../DOCS.md).
Historical queue statements describe the report's date.

## Submission package

- [SUBMISSION-REPORT.md](SUBMISSION-REPORT.md): current consolidated report, evidence through October 3, 2026.
- [SUBMISSION-EVIDENCE.md](SUBMISSION-EVIDENCE.md): claim-to-artifact map, model/build identities and verification commands.

Submit the report with the appendix. The older root `FINAL-REPORT.md` and
September 24 PDF/LaTeX export retain historical campaign claims; they are not
the current submission. No files have been submitted externally.

## Current measurements and validation

| Report | Scope |
| --- | --- |
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
