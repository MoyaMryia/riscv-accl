# Channels-major SSM convolution: correctness gate failure

Run: `k1-ssm-conv-20261006-073927`, dispatched October 6, 2026 at 07:39
Asia/Singapore on SSH `musepipro-wg`. The board stopped after **6m 28s**
(`387.9004` seconds). Board exit status **1**, independently confirmed over
SSH; its tmux session has ended. No new benchmark was launched during this
scheduled check.

## Result

| Arm/stage | Observed result |
| --- | --- |
| Original CPU library, mode 0 | **432 cases pass** exact FP32 reference, history tails, tensor/scratch guards, strides and repeat execution |
| Private candidate libraries, mode 0 | **432 cases pass** the same checks |
| Channels-major graph, mode 1 | **Fails: `history write-back`**; the process exits 1 before completing its case matrix |
| Channels-major graph plus RVV, mode 2 | Not run: earlier correctness gate failed |
| Operator timing, including concat/history copies | Not run |
| Actual model chunk/reset and RS fallback comparisons | Not run |
| Cold prefill/decode versus route-3 control | **0 requests**; not run |

All candidate libraries and native harnesses compiled before the numerical
stage. This is a correctness failure, not a measured performance regression.
The failing check compares the copied history tail against the independently
expected sliding-window contents. The log does not identify the failing
shape or establish whether the defect is in graph construction or the test
fixture. It does not demonstrate an RVV arithmetic failure: mode 1 failed
before mode 2 was attempted.

The two completed arms independently passed their reference checks. The
controller only saves cross-arm dump hashes after all four arms complete;
that stage did not finish, so a persisted four-arm identity result is absent.
No useful-answer, model-state, RS rollback, throughput or adoption claim is
supported by this run. Production defaults remain unchanged.

## Collection verification

The archive SHA256 is:

```text
af7409e2c37b0d1eb250d9af4f52956e29a9cf155b57ca35eb20a9f3e43a8d78
```

The archive checksum, its exact file list, and **all 23 individual artifact
hashes** were checked against the receipt, both inside the archive and in the
extracted local files. Artifact transfer succeeded. `collector-exit-status=1`
reflects the collector wrapper deliberately rejecting the board's nonzero
exit status; it does not mean those collected artifacts failed verification.

## Subsequent diagnosis and next step

The [separate native diagnosis](2026-10-06-ssm-history-diagnosis.md) reproduced
the first failing case and traced it to the fork's CPY transpose fast path.
Materializing the small transposed history tail repairs the native graph:
private-library modes 0/1/2 each pass all 432 cases with identical output and
history dump hashes. The candidate generator now includes that repair.

The diagnosis does not revise this failed campaign's results. A fresh private
model-library build and the full original/control/layout/RVV numerical gates
remain required before operator timing, model-state checks or inference timing.

The [subsequent repaired campaign](2026-10-06-ssm-conv-repaired-results.md)
completed the fresh build and all four numerical arms, then rejected
unconditional use at the operator gate because single-token time regressed.
It did not advance to model-state or cold inference checks.

The approximately 30-minute follow-up is paused after reporting the failure.

## Evidence

- [Protocol and source controls](../experiments/2026-10-06-ssm-conv-rvv.md)
- [Failure summary](raw/k1-ssm-conv-20261006-073927/summary.json)
- [Original numerical log](raw/k1-ssm-conv-20261006-073927/numeric--1.log)
- [Candidate mode-0 log](raw/k1-ssm-conv-20261006-073927/numeric-0.log)
- [Channels-major failure log](raw/k1-ssm-conv-20261006-073927/numeric-1.log)
- [Build provenance](raw/k1-ssm-conv-20261006-073927/provenance.json)
- [Collection receipt](raw/k1-ssm-conv-20261006-073927/collection-receipt.json)
