# SSM history copy: diagnosis and native repair verification

Date: October 6, 2026. Board: SSH `musepipro-wg`.
Diagnosis directory: `k1-ssm-history-diagnosis-20261006`.

## Finding

The new channels-major graph exposes an incompatible SpaceMiT **CPY transpose
fast path**. The convolution passes its independent reference check in the
small failing case; the subsequent saved history is wrong. This is a concrete
copy-path defect, not evidence of a chip performance limit.

The first failing matrix case is mode 1, **7 channels, kernel width 3, one
token, one sequence, no projection padding**. At sequence 0/channel 1/tap 0,
the expected history value is `-0.795623779`; the copied value is `0`.

The transposed tail is logically `[2, 7, 1]`. The following values are in bytes:

| Property | Required by this view | Existing CPY helper |
| --- | --- | --- |
| Number of source rows separated by the source row stride | 2 | 7 |
| Contiguous elements per source row | 7 | 2 |
| Source row stride | 28 | 28 |
| Destination stride between channels | 8 | 28 |
| Source / destination sequence strides | 84 / 56 | 84 for both |

`ime.cpp` selects `forward_cpy_with_permute` on a stride equality without
checking these layout requirements. Its `m`/`n` arguments are reversed for
this transposed view and its destination stride is derived from the source.
The assembly therefore reads beyond the intended history rows and writes
values into the wrong history positions. Reusing the source sequence stride
for the destination also makes this path unsuitable for cropped multi-sequence
tails. Source excerpts and hashes are retained in the evidence directory.

## Repair

Materialize the small transposed history tail with `ggml_cont` before copying
it into the persistent time-major cache. For these cropped tails, the fork's
CONT stride guard rejects its transpose shortcut and the generic contiguous
conversion honors the view strides. The following CPY reads contiguous state.

The change is applied to both the native fixture and
`spacemit/bench/make-k1-ssm-conv.py`. The existing failed run and libraries are
preserved. A diagnostic environment switch, `SPINE_SSM_DIAG_LEGACY_COPY=1`,
retains the old fixture graph for reproducing the failure; the model candidate
does not expose this switch.

This introduces a small temporary history tensor and copy. At the actual
kernel width 4, its FP32 payload is 72 KiB for 6144 channels and 96 KiB for
8192 channels, per sequence. The cost must be included in operator/model
timing. A general backend transpose repair could avoid this workaround but
needs separate layout/type qualification.

## Board verification

The harness was compiled and run against the **same verified private libraries**
as the failed campaign; no convolution library or arithmetic was changed.

| Check | Result |
| --- | --- |
| Legacy graph, smallest failing case | Exit 1; reproduces the same history mismatch |
| Repaired smallest case, modes 0/1/2 | Pass, including repeat execution |
| Private library, original graph, mode 0 | 432 cases pass |
| Repaired channels-major graph, scalar mode 1 | 432 cases pass |
| Repaired channels-major graph, RVV mode 2 | 432 cases pass |
| Cross-arm output **and saved-history** dumps | Bitwise identical; all three SHA256 hashes match |
| Local controller checks | Six tests pass |
| Collected diagnosis artifacts | All 15 file sizes and SHA256 hashes verified |

Each matrix case executes twice and checks exact ordered FP32 convolution,
history contents, tensor/scratch guards, input immutability and strides. The
matrix retains all 432 original cases, including the failing odd channel
count, channel tails, both actual model channel counts, token counts 1/3/32/33,
kernel widths 3/4/9, one/two sequences and padded projection inputs.

The matching 96,627,720-byte output/history dumps have SHA256:

```text
7e154f0a52c2475581a62a64f549a17c7d342d46c55dae7adf05d09c05001c69
```

## Remaining qualification

Update: the [fresh repaired screen](2026-10-06-ssm-conv-repaired-results.md)
subsequently built the corrected libraries and passed all four native arms.
It stopped at the operator no-regression gate: batch gains were accompanied
by single-token regressions. Model execution remains unqualified.

At the end of this diagnosis:

The rebuilt diagnostic verifies the repaired native graph. The corrected
model graph generator still needs a fresh private model-library build, the
full original/control/scalar/RVV gate, operator timing, model state/reset and
RS fallback checks, then gated cold inference timing. No model speedup or
useful-answer quality result follows from this diagnosis. Production defaults
remain unchanged, and the failed campaign's monitor remains paused.

## Evidence

- [Repair summary and exact commands](raw/k1-ssm-history-diagnosis-20261006/fixed-summary.json)
- [Reproduced failure](raw/k1-ssm-history-diagnosis-20261006/legacy-minimal.log)
- [Scalar matrix](raw/k1-ssm-history-diagnosis-20261006/fixed-matrix-1.log)
- [RVV matrix](raw/k1-ssm-history-diagnosis-20261006/fixed-matrix-2.log)
- [Source excerpts with line numbers](raw/k1-ssm-history-diagnosis-20261006/copy-source-excerpts.txt)
- [Artifact receipt](raw/k1-ssm-history-diagnosis-20261006/diagnosis-receipt.json)
- [Original failed campaign](2026-10-06-ssm-conv-rvv-results.md)
