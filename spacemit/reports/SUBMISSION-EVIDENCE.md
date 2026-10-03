# Submission evidence appendix

Evidence cutoff: October 3, 2026, Asia/Singapore. This appendix supports the
[submission report](SUBMISSION-REPORT.md). File dates identify campaigns;
historical work queues do not describe current board activity.

## 1. Claim-to-artifact map

| Submission claim | Authoritative records | Verification / implementation |
| --- | --- | --- |
| RVV 2k/8k TTFT improvement on both models | [2k requests](raw/2026-09-25-lifecycle/lifecycle-rvv32.jsonl), [8k requests](raw/2026-09-25-lifecycle/lifecycle-rvv32-long.jsonl) | [Matrix verifier](../bench/verify-results-matrix.py), [RVV patch 0009](../patches/0009-wide-rvv-vlen256.patch) |
| Actual 16k pairs and 2B 32k feasibility | [Resumed measurement matrix](2026-09-27-resumed-measures.md), [lifecycle raw directory](raw/2026-09-25-lifecycle/) | Same matrix verifier; individual server logs and requests are linked in the matrix report |
| New routing model results | [Routing summary](raw/k1-gemm-routing-20261003-005740/summary.json), [individual requests/logs](raw/k1-gemm-routing-20261003-005740/) | [Independent verifier](../bench/verify-k1-gemm-routing.py), [verification output](raw/k1-gemm-routing-20261003-005740/verification.json) |
| Native and operator routing gates | [Operator records](raw/k1-gemm-routing-20261003-005740/operator.jsonl), numerical logs in the same directory | [Production graph harness](../bench/test-k1-gemm-routing.cpp), [controller](../bench/k1-gemm-routing.py) |
| 236 collected artifacts and baseline preservation | [Collection receipt](raw/k1-gemm-routing-20261003-005740/collection-receipt.json), [46-file preservation check](raw/k1-gemm-routing-20261003-005740/baseline-preservation-check.json) | Independent artifact hashing; preservation compares end-of-run board hashes to starting manifests |
| Source/build/model provenance | [Expected baseline](raw/k1-gemm-routing-20261003-005740/expected-provenance.json), [build provenance](raw/k1-gemm-routing-20261003-005740/provenance.json), [tested patch](raw/k1-gemm-routing-20261003-005740/candidate-gemm-routing.patch) | [Generator](../bench/make-k1-gemm-routing.py), [launcher](../bench/start-k1-gemm-routing.py) |
| Q8_0 IME1 and M4 scale results | [September 24 integrated report](2026-09-24-integrated-k1.md), [raw arms](raw/2026-09-24-integrated/) | [Patch 0007](../patches/0007-q8-ime1.patch), [patch 0008](../patches/0008-ime-m4-scale.patch) |
| Corrected small-effect statistics | [Local verification](2026-09-28-local-verification.md) | [Statistics script](../bench/paired-stats.py); fractional Welch degrees of freedom |
| MTP long-code mismatch and bounded decode traces | [Resumed diagnostics](2026-09-27-resumed-measures.md), [long-code traces](raw/2026-09-25-lifecycle/lifecycle-code-long.jsonl) | [Lifecycle auditor](../bench/audit-lifecycle.py); smaller drafts/RS/target-logit/FA-off evidence in the resumed report |
| Complete-answer cache matrix | [Quality report](2026-09-30-chat-quality-benchmark.md), [completed 24-pair summary](raw/document-quality-20260930-full-v2/summary.md) | [Quality runner](../bench/run-all-document-quality.py), [document benchmark](../bench/bench-shared-document-cache.py) |
| Negative compact-layout screen | [Fast method results](2026-10-01-fast-method.md), [completed run](raw/k1-fast-20261001-224957/summary.md) | [Staged test design](../experiments/2026-09-30-fast-test-design.md) |
| Negative IME / recurrent / attention screens | [IME scheduling](2026-10-02-ime-scheduling.md), [recurrent fusion](2026-10-02-recurrent-prefill.md), [attention infrastructure](../experiments/2026-10-02-attention-infrastructure.md) | Their linked native tests, operator records and gated model runs |
| GPU and page-gather boundaries | [Completed gates](2026-09-27-completed-gates.md), [later telemetry and backend findings](2026-09-27-resumed-measures.md) | Zero transferred OpenCL layers; Vulkan dropped; page gathering retains full backing allocation |
| Unused research opportunities | [October 3 GitHub/arXiv/Scholar review](2026-10-03-infrastructure-research.md) | Primary-source links and platform-fit decisions in that review |

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

## 5. Submission document roles

| Material | Use |
| --- | --- |
| [SUBMISSION-REPORT.md](SUBMISSION-REPORT.md) | Current report to submit or adapt to the recipient's template |
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
