# riscv-accl

Local Qwen3.5 inference on the SpaceMiT K1/X60 RISC-V platform.
The project contains optimization code, native tests, measurement records, and a portable performance evaluator.

## Project report

Evidence cutoff: October 12, 2026, Asia/Singapore.

- [PDF report](spacemit/reports/SUBMISSION-REPORT.pdf): the report with its evidence appendix.
- [TeX source](spacemit/reports/SUBMISSION-REPORT.tex): a standalone source file for the PDF.
- [Report text](spacemit/reports/SUBMISSION-REPORT.md) and [evidence appendix](spacemit/reports/SUBMISSION-EVIDENCE.md): editable source documents.
- [Export instructions](spacemit/reports/REPORT-BUILD.md): commands to reproduce the TeX and PDF.

The verified release contains wide RVV attention and opt-in GEMM routing.
Later individual candidates have bounded gains, but their three-part combination fails one decode gate.
V7 retains incorrect point predictions and wide error intervals.
The first operator training batch passes its recorded checks; independent prediction accuracy remains unverified.
Board recovery remains pending after the recorded access failure.

## Project documents

| Need | Entry point |
| --- | --- |
| Current status and document map | [Documentation guide](spacemit/DOCS.md) |
| Pinned source and launch commands | [Infrastructure release](spacemit/release/README.md) |
| Model preparation and historical patches | [Integration guide](spacemit/README.md) |
| Native benchmarks and evidence collection | [Benchmark guide](spacemit/bench/README.md) |
| Performance evaluator and fixed examples | [Evaluator guide](spacemit/bench/qemu-screen/predictor/README.md) |
| Native operator data | [Operator tools](spacemit/bench/operator-data/README.md) |
| Dated measurements | [Reports index](spacemit/reports/README.md) |
| Experiment protocols | [Experiments index](spacemit/experiments/README.md) |

`FINAL-REPORT.md`, the September TeX/PDF, and `lab/` notes describe historical campaigns.
Their dates and configurations limit their claims.
Files in `spacemit/reports/raw/` are unchanged evidence, not editable report prose.
