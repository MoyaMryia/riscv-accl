# Channels-major SSM convolution: correctness gate failure

Run: `k1-ssm-conv-20261006-073927`, dispatched October 6, 2026 at 07:39
Asia/Singapore, on SSH `musepipro-wg`. The board stopped after **6m 28s**
(`387.9004` seconds). The board exit status is **1**, and we confirmed it
independently over SSH. Its tmux session has ended. We launched no new
benchmark during this scheduled check.

## Result

| Arm/stage | Observed result |
| --- | --- |
| Original CPU library, mode 0 | **432 cases pass**: exact FP32 reference, history tails, tensor/scratch guards, strides, and repeat execution |
| Private candidate libraries, mode 0 | **432 cases pass**, with the same checks |
| Channels-major graph, mode 1 | **Fails: `history write-back`**; the process exits 1 before it completes its case matrix |
| Channels-major graph plus RVV, mode 2 | Not run: an earlier correctness gate failed |
| Operator timing, including concat/history copies | Not run |
| Actual model chunk/reset and RS fallback comparisons | Not run |
| Cold prefill/decode versus route-3 control | **0 requests**; not run |

All candidate libraries and native harnesses compiled before the numerical
stage. This result is a correctness failure, not a measured performance
regression. The failing check compares the copied history tail against the
independently expected sliding-window contents. The log does not identify the
failing shape, and it does not establish whether the defect is in the graph
construction or in the test fixture. The run does not demonstrate an RVV
arithmetic failure, because mode 1 failed before we attempted mode 2.

The two completed arms passed their reference checks independently. The
controller saves the cross-arm dump hashes only after all four arms complete.
That stage did not finish, so a persisted four-arm identity result is absent.
This run supports no useful-answer, model-state, RS rollback, throughput, or
adoption claim. The production defaults remain unchanged.

## Collection verification

The archive SHA256 is:

```text
af7409e2c37b0d1eb250d9af4f52956e29a9cf155b57ca35eb20a9f3e43a8d78
```

We checked the archive checksum, its exact file list, and **all 23 individual
artifact hashes** against the receipt, both inside the archive and in the
extracted local files. The artifact transfer succeeded.
`collector-exit-status=1` reflects the deliberate rejection of the nonzero
board exit status by the collector wrapper. It does not mean that the
collected artifacts failed their verification.

## Subsequent diagnosis and next step

The [separate native diagnosis](2026-10-06-ssm-history-diagnosis.md)
reproduced the first failing case, and it traced the failure to the CPY
transpose fast path of the fork. A materialization of the small transposed
history tail repairs the native graph: the private-library modes 0, 1, and 2
each pass all 432 cases, with identical output and history dump hashes. The
candidate generator now includes that repair.

The diagnosis does not revise the results of this failed campaign. A fresh
private model-library build and the full original/control/layout/RVV numerical
gates remain necessary, before operator timing, model-state checks, or
inference timing.

The [subsequent repaired campaign](2026-10-06-ssm-conv-repaired-results.md)
completed the fresh build and all four numerical arms. Then it rejected the
unconditional use at the operator gate, because the single-token time
regressed. It did not advance to the model-state or the cold inference checks.

The follow-up of approximately 30 minutes is paused, after this report of the
failure.

## Evidence

- [Protocol and source controls](../experiments/2026-10-06-ssm-conv-rvv.md)
- [Failure summary](raw/k1-ssm-conv-20261006-073927/summary.json)
- [Original numerical log](raw/k1-ssm-conv-20261006-073927/numeric--1.log)
- [Candidate mode-0 log](raw/k1-ssm-conv-20261006-073927/numeric-0.log)
- [Channels-major failure log](raw/k1-ssm-conv-20261006-073927/numeric-1.log)
- [Build provenance](raw/k1-ssm-conv-20261006-073927/provenance.json)
- [Collection receipt](raw/k1-ssm-conv-20261006-073927/collection-receipt.json)
