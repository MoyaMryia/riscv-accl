# Submission evidence appendix

Evidence cutoff: October 12, 2026, Asia/Singapore. This appendix supports the
[submission report](SUBMISSION-REPORT.md). File dates identify campaigns;
historical work queues do not describe current board activity.

## 1. Claim-to-artifact map

| Submission claim | Authoritative records | Verification / implementation |
| --- | --- | --- |
| RVV 2k/8k TTFT improvement on both models | [2k requests](raw/2026-09-25-lifecycle/lifecycle-rvv32.jsonl), [8k requests](raw/2026-09-25-lifecycle/lifecycle-rvv32-long.jsonl) | [Matrix verifier](../bench/verify-results-matrix.py), [RVV patch 0009](../patches/0009-wide-rvv-vlen256.patch) |
| Actual 16k pairs and 2B 32k feasibility | [Resumed measurement matrix](2026-09-27-resumed-measures.md), [lifecycle raw directory](raw/2026-09-25-lifecycle/) | Same matrix verifier; individual server logs and requests are linked in the matrix report |
| New routing model results | [Routing summary](raw/k1-gemm-routing-20261003-005740/summary.json), [individual requests/logs](raw/k1-gemm-routing-20261003-005740/) | [Independent verifier](../bench/verify-k1-gemm-routing.py), [verification output](raw/k1-gemm-routing-20261003-005740/verification.json) |
| Combined routing at 8k, complete-answer pilot and RS replay failures | [Staged validation results](2026-10-03-staged-validation-results.md), [summary](raw/k1-validation-20261003-124720/summary.json), [83-artifact receipt](raw/k1-validation-20261003-124720/collection-receipt.json) | [Validation verifier](../bench/verify-k1-validation.py), [verification output](raw/k1-validation-20261003-124720/verification.json); 4B/32k explicitly skipped |
| Native and operator routing gates | [Operator records](raw/k1-gemm-routing-20261003-005740/operator.jsonl), numerical logs in the same directory | [Production graph harness](../bench/test-k1-gemm-routing.cpp), [controller](../bench/k1-gemm-routing.py) |
| 236 collected artifacts and baseline preservation | [Collection receipt](raw/k1-gemm-routing-20261003-005740/collection-receipt.json), [46-file preservation check](raw/k1-gemm-routing-20261003-005740/baseline-preservation-check.json) | Independent artifact hashing; preservation compares end-of-run board hashes to starting manifests |
| Source/build/model provenance | [Expected baseline](raw/k1-gemm-routing-20261003-005740/expected-provenance.json), [build provenance](raw/k1-gemm-routing-20261003-005740/provenance.json), [tested patch](raw/k1-gemm-routing-20261003-005740/candidate-gemm-routing.patch) | [Generator](../bench/make-k1-gemm-routing.py), [launcher](../bench/start-k1-gemm-routing.py) |
| Q8_0 IME1 and M4 scale results | [September 24 integrated report](2026-09-24-integrated-k1.md), [raw arms](raw/2026-09-24-integrated/) | [Patch 0007](../patches/0007-q8-ime1.patch), [patch 0008](../patches/0008-ime-m4-scale.patch) |
| Corrected small-effect statistics | [Local verification](2026-09-28-local-verification.md) | [Statistics script](../bench/paired-stats.py); fractional Welch degrees of freedom |
| MTP long-code mismatch and bounded decode traces | [Resumed diagnostics](2026-09-27-resumed-measures.md), [long-code traces](raw/2026-09-25-lifecycle/lifecycle-code-long.jsonl) | [Lifecycle auditor](../bench/audit-lifecycle.py); smaller drafts/RS/target-logit/FA-off evidence in the resumed report |
| Complete-answer checkpoint MTP usefulness | [Results](2026-10-03-mtp-usefulness-results.md), [quality summary](raw/mtp-quality-20261003-173915/quality-summary.json), [21-artifact receipt](raw/mtp-quality-20261003-173915/collection-receipt.json) | [Protocol](../experiments/2026-10-03-mtp-usefulness.md), [functional checks](../bench/mtp-quality-checks.py), [scoring recovery](raw/mtp-quality-20261003-173915/scoring-recovery.json); relative gates pass, absolute usefulness fails |
| Adaptive MTP bounded infrastructure screen | [Results](2026-10-05-adaptive-mtp-results.md), [final summary](raw/adaptive-mtp-infra-20261005-153716/adaptive-quality-summary.json), [47-artifact receipt](raw/adaptive-mtp-infra-20261005-153716/collection-receipt.json) | [Protocol](../experiments/2026-10-05-adaptive-mtp-infrastructure.md), [grading recovery](raw/adaptive-mtp-infra-20261005-153716/adaptive-scoring-recovery.json); throughput positive, overall candidate unqualified |
| Complete-answer cache matrix | [Quality report](2026-09-30-chat-quality-benchmark.md), [completed 24-pair summary](raw/document-quality-20260930-full-v2/summary.md) | [Quality runner](../bench/run-all-document-quality.py), [document benchmark](../bench/bench-shared-document-cache.py) |
| Negative compact-layout screen | [Fast method results](2026-10-01-fast-method.md), [completed run](raw/k1-fast-20261001-224957/summary.md) | [Staged test design](../experiments/2026-09-30-fast-test-design.md) |
| Negative IME / recurrent / attention screens | [IME scheduling](2026-10-02-ime-scheduling.md), [recurrent fusion](2026-10-02-recurrent-prefill.md), [attention infrastructure](../experiments/2026-10-02-attention-infrastructure.md) | Their linked native tests, operator records and gated model runs |
| GPU and page-gather boundaries | [Completed gates](2026-09-27-completed-gates.md), [later telemetry and backend findings](2026-09-27-resumed-measures.md) | Zero transferred OpenCL layers; Vulkan dropped; page gathering retains full backing allocation |
| Independent bandwidth and routing confirmation | [October 6 results](2026-10-06-k1-roofline-results.md), [summary](raw/k1-roofline-20261005-225502/summary.json), [150-artifact receipt](raw/k1-roofline-20261005-225502/collection-receipt.json) | [Protocol](../experiments/2026-10-05-k1-roofline.md), [compressed evidence storage](raw/k1-roofline-20261005-225502/ARCHIVE.md); traffic references are not hardware-limit proof |
| Same-seed local clean-reference quality | [Results](2026-10-06-local-clean-reference-results.md), [summary](raw/local-reference-quality-20261006-194015/summary.json), [verification](raw/local-reference-quality-20261006-194015/completion-verification.json) | [Protocol](../experiments/2026-10-06-local-clean-reference.md), exact GGUF/source/request hashes, 12 audits and 11 two-order judgment pairs; errors persist, cross-backend causal/speed claims excluded |
| Hybrid SSM complete useful answers | [Measured results](2026-10-06-ssm-complete-answer-results.md), [final quality summary](raw/k1-ssm-quality-20261006-131234/ssm-quality-summary.json), [114-artifact receipt](raw/k1-ssm-quality-20261006-131234/collection-receipt.json) | [Completion verification](raw/k1-ssm-quality-20261006-131234/completion-verification.json), [passing answer](2026-10-06-ssm-useful-answer-example.md); exact graph/state pass, 24 natural answers, adoption gates fail; local scoring files additional to receipt |
| Sustained decode and negative shared-packing priority | [October 7 results](2026-10-07-decode-packing-results.md), [summary](raw/k1-decode-audit-20261007-074314/summary.json), [86-artifact receipt](raw/k1-decode-audit-20261007-074314/collection-receipt.json) | [Independent verifier](raw/k1-decode-analysis-20261007/verify-completion.py), [verification](raw/k1-decode-analysis-20261007/verification.json); eight exact matched requests, four decode profiles, native identity; packing declined, CPU shares are not wall-time savings |
| Unused research opportunities | [October 3 GitHub/arXiv/Scholar review](2026-10-03-infrastructure-research.md), [October 6 source audit](2026-10-06-next-infrastructure-methods.md) | Dated primary-source/source reviews; convolution and decode packing subsequently measured; M1 kernel scheduling and worker-barrier implementation remain unqualified |

## 2. Baseline identities

| Source state | Role |
| --- | --- |
| Official SpaceMiT fork `5ad05d8` | Clean starting point for the packaged patch helper |
| `6562c22` plus separately selected options | Earlier recurrent/MTP integration state |
| `a990751` plus recorded wide-RVV source changes | Later board baseline; build-specific provenance is required |
| Original library versus generated mode 0 | Routing operator control for unintended effects of the isolated library build |
| Generated mode 0 versus mode 1 or 2 | Routing model comparisons; the baseline already has wide attention/layout 0 |

Historical documentation values with different quantization, model derivative,
prompt length or runtime state are not matched baseline arms. In particular,
the old Q4_1 documentation rates must not be used to calculate a controlled
Q4_0 optimization percentage. Baselines from different campaigns must not be
treated as one continuous cumulative curve.

## 3. Latest model identity

The routing run hashes the exact local files; model preparation is described
in the [model tools guide](../models/tools/README.md).

| Model file | SHA-256 |
| --- | --- |
| `Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf` | `56f0ddd90dfa0e2456af6cb4718ece419678d21a75d65e27353319b5e431a2fa` |
| `Qwen3.5-4B-MTP-Q4_0-embQ4_0-dv64k.gguf` | `0adf6cce5df53921606033c39a13fae2054543b78af0e7ff98860e86f078ac0f` |

Model weights remain outside this repository. The current kernel comparisons
do not replace the model, alter its Q4_0 weights or trim input tokens.

## 4. Re-run local verification

From the repository root:

```bash
python3 spacemit/bench/verify-results-matrix.py \
  spacemit/reports/2026-09-27-resumed-measures.md \
  spacemit/reports/raw/2026-09-25-lifecycle
python3 spacemit/bench/verify-k1-gemm-routing.py \
  spacemit/reports/raw/k1-gemm-routing-20261003-005740
python3 spacemit/bench/test-k1-gemm-routing.py
python3 spacemit/bench/test-k1-fast-test.py
python3 spacemit/bench/test-k1-ime-test.py
```

The matrix verifier checks 21 rows / 105 numeric cells. The routing verifier
checks archived hashes, numerical logs, operator and model gates, input/output
counts, actual runtime configuration and per-phase kernel markers.
The three local regression scripts contain 2, 6 and 3 checks respectively.
These local tests supplement the board runs; they do not substitute for them.

The routing run's environment telemetry allowlist omitted
`SPINE_K1_GEMM_ROUTE`. Actual mandatory kernel markers record mode, eligibility
and bypass for each phase and establish activation independently. The verifier
requires those markers and checks the environment value if recorded. Future
runs also capture the environment field. Original raw records were preserved.

The 236-artifact receipt covers collected board evidence. The independently
generated local verification and preservation records are additional files,
not members of that original collection count. Native binary output dumps
remain on the board; numerical logs and summaries record their identical
SHA-256 values. End-of-run board hashing independently confirmed those dumps.

## Fixed K32 M1 screen: negative evidence

The [October 7 M1 specialization results](2026-10-07-ime-m1-k32-results.md)
have the following evidence: the [frozen summary](raw/k1-ime-m1-k32-20261007-121231/summary.json),
[144 operator samples](raw/k1-ime-m1-k32-20261007-121231/operator.jsonl),
[211-artifact receipt](raw/k1-ime-m1-k32-20261007-121231/collection-receipt.json),
[independent verifier](raw/k1-ime-m1-analysis-20261007/verify-completion.py),
[verification output](raw/k1-ime-m1-analysis-20261007/verification.json) and
[40-file remote preservation check](raw/k1-ime-m1-analysis-20261007/remote-preservation.json).
Both exit statuses are zero. All 480 raw cases, 104 production cases per arm
and six actual FFN/full-248320-column shapes per arm pass exact outputs and
guards. Recreated route-3 baseline hash is exact; generated assembly removes
the inner counter/branches while retaining dot/load/FMA order and fallbacks.
No operator clears both 3% and control spread. Full-model state, cold ABBA and
useful-answer stages were skipped. Candidate disabled; no new inference or
quality gain enters the submission. Independent analysis files are outside
the original 211-artifact receipt.

## 5. Submission document roles

The [October 6 repaired SSM screen](2026-10-06-ssm-conv-repaired-results.md)
is supported by [its summary](raw/k1-ssm-conv-20261006-115459/summary.json),
[operator samples](raw/k1-ssm-conv-20261006-115459/operator.jsonl) and
[97-artifact receipt](raw/k1-ssm-conv-20261006-115459/collection-receipt.json).
All four arms pass 432 exact output/history cases. Warm graph gains at
32 tokens accompany single-token regressions, so model-state and inference
timing stages were skipped. These measurements support no full-model gain.

| Material | Use |
| --- | --- |
| [SUBMISSION-REPORT.md](SUBMISSION-REPORT.md) | Current report; edit this file before a new export |
| [SUBMISSION-REPORT.tex](SUBMISSION-REPORT.tex) | Standalone TeX export of the report and this appendix |
| [SUBMISSION-REPORT.pdf](SUBMISSION-REPORT.pdf) | PDF export for review |
| [REPORT-BUILD.md](REPORT-BUILD.md) | Export commands and document update rules |
| This appendix | Evidence and reproduction references accompanying the report |
| [Current documentation guide](../DOCS.md) | Operational status and navigation |
| [Integration guide](../README.md) / [benchmark guide](../bench/README.md) | Deployment and executable procedures |
| Dated reports and experiments | Campaign-specific details and historical decisions |
| `raw/` | Reproducibility records; preserve original measurements |
| [September 24 LaTeX](k1-llm-inference-optimizations.tex) and [PDF](k1-llm-inference-optimizations.pdf) | Historical export; predates later findings and is not the current submission |
| [Root FINAL-REPORT.md](../../FINAL-REPORT.md) | Historical short-prompt campaign, with later annotations; not the current submission |

No required final-report template, author list or external submission destination
has been supplied. The report is organized for review; it has not been
submitted externally.

## Current release package

The [release manifest](../release/manifest.json) pins the exact source revision, patch and measured files, model hashes and matched route0/3 profiles. [Offline clean-source verification](raw/release-20261007/clean-apply-verification.json) checks the 3,266-file snapshot and exact patch round trip. The [fresh full board build and complete-answer verification](2026-10-07-release-verification.md) passes in `k1-release-check-20261007-125712`. It checks 104 exact production graph cases per routing arm. All four Unicode code answers stop naturally and pass 106 held-out checks each. All 35 archived artifacts, 18 staged code files and three collector files pass checksum verification; post-run source, binary, compiler and vendor-runtime checks pass. Board/collector exit statuses are zero. The [independent result](raw/release-20261007/verification.json) records exact paired/prior text identity and the descriptive natural-answer timings. ARM/x86 comparison is excluded by user instruction. Release smoke timings do not add a new statistical speedup claim.

## 6. Evidence added after October 7

| Claim | Records | Tools and limits |
| --- | --- | --- |
| Independent C1, C2-r2, C3, and B1-r2 results | [Candidate review](2026-10-09-local-candidate-result-rejudgment.md), [progress snapshot](2026-10-11-project-progress.md), [phase comparison CSV](2026-10-11-original-current-comparison.csv) | [Version comparison](2026-10-11-original-current-comparison.md); C0 already has RVV attention and route 3; no cumulative speedup |
| Combined-r1 fails one decode gate | [Stop audit](2026-10-12-combined-stop-audit.md), [saved original summary](raw/k1-combined-stop-audit-20261012/input/summary.json), [independent audit](raw/k1-combined-stop-audit-20261012/local-audit.json) | [Audit tool](../bench/local-candidates/audit-combined-stop.py); 96 first-round requests and 48 comparisons; no second round or complete-answer stage |
| Dispatch revision remains local | [Protocol](../experiments/2026-10-12-combined-dispatch-r2-local-protocol.md), [manifest](raw/k1-combined-stop-audit-20261012/dispatch-manifest.json), [local checks](raw/k1-combined-stop-audit-20261012/tests.log) | Full numerical, target assembly, operator, and model checks remain pending |
| V7 wide intervals and incorrect point directions | [V7 report](2026-10-12-k1-model-v7.md), [evaluation](raw/k1-model-v7-20261012/evaluation.json), [calibration](raw/k1-model-v7-20261012/calibration.json), [cross-host check](raw/k1-model-v7-20261012/cross-host-check.json) | [Evaluator guide](../bench/qemu-screen/predictor/README.md); 9/9 group coverage does not establish reliable point predictions |
| First native operator training batch | [Operator report](2026-10-12-k1-operator-data.md), [plan](raw/k1-operator-data-20261012-r1/plan.json), [observations](raw/k1-operator-data-20261012-r1/observations.jsonl), [summary](raw/k1-operator-data-20261012-r1/summary.json) | [Operator tools](../bench/operator-data/README.md), [numerical receipts](raw/k1-operator-data-20261012-r1/numeric-receipts.json), [transfer receipt](raw/k1-operator-data-20261012-r1/transfer-receipt.json); training only |
| Access failure and unknown second-batch state | [Connection report](2026-10-12-k1-connection-interruption.md) | [Bounded client](../bench/operator-data/remote.py); no automatic retry or new board task |

The October 11 progress report and comparison CSV retain their original snapshots.
The October 12 stop audit supplies the later combination decision.
A saved summary is not a new independent comparison of the 536 formal state dumps.
The report retains that evidence gap.

## 7. Portable evaluator replay

Run these commands from the repository root.
The output directory must not exist.

```bash
python3 spacemit/bench/qemu-screen/predictor/model-bundle.py \
  --include-ime-audit --output lab/k1-portable-v7
```

Check the generated archive against its external SHA-256 receipt.
Extract the archive.
Run this command from its `k1-models-v7/` directory.

```bash
python3 run-examples.py --output ../k1-replay
```

The replay checks fixed evidence and frozen model identities.
It does not collect new native measurements or qualify a new algorithm.
Complete archives and binary dumps remain outside Git.
Full archive checks require those retained files.
The portable examples include the data needed for their own replay.
