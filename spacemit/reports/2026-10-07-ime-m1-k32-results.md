# Fixed K32 M1 IME specialization results

Date: October 7, 2026, Asia/Singapore. Run:
`k1-ime-m1-k32-20261007-121231`. **Completed and independently verified.**
Board execution took **18.11 minutes**, starting at 12:12. Board and collector
exit statuses are zero. The [protocol](../experiments/2026-10-07-ime-m1-k32.md)
declared correctness and performance gates before dispatch.

## Decision

Keep this candidate disabled. Removing the fixed K32 inner-loop counter and
branches preserves outputs, but **none of eight measured shapes clears the
benefit gate**. No longer model or useful-answer tests were launched. This is
a completed negative operator screen, not a build or correctness failure.

The baseline is the preserved route-3 CPU library. The candidate changes only
eligible single-row Q4_0 K32 calls; all weights, quantizer/scales, load order,
integer dots, outer-block FP32 fused accumulation and output tails remain.
M2/M3/M4, zero points, K64 and Q8 retain their original path. The private
candidate is opt-in with `SPINE_IME_M1_K32=1`; production defaults are unchanged.

## Correctness and preservation

- Three local transformation checks passed: the expanded assembly instruction
  trace matches two original iterations after removal of inner-loop control;
  original fallback bodies/macros remain and source drift is refused.
- **480 raw cases** pass bitwise original/candidate identity, processed-row
  counts, input/output guards, independent scalar M1 Q4_0 reference checks and
  original full-tile M4 reference checks where supported. Coverage includes
  K32/K64, four K-block counts, M1/2/3/4/7, N tails and zero points.
- **104 production graph cases in each of three arms**—preserved original,
  wrapper control off, candidate on—have identical collected dumps. Q8 fallback,
  production weight repacking and input/output/scratch guards pass. Dump SHA:
  `e31997719879fb9a858f9e970af7e11ceb68124657d41c53bd3b3f82c4dbd4dc`.
- Six additional actual FFN/output-head shapes pass in all three arms. Both
  output heads retain and compare **all 248,320 columns**; no vocabulary pruning.
- Decoded machine code contains two consecutive eight-instruction `vmadot`
  groups, one four-instruction FP32 block accumulation, the outer K loop and
  original tail stores. The fixed helper has no inner-loop branch; original
  inner loops remain in fallback code. Removing this control did not remove
  the loads, nibble unpacking or matrix dot work that dominate the loop body.
- The recreated original link has the exact preserved route-3 library SHA:
  `43363dad9c500bd71d5ad7cc9d0108efff5c58133b7b8b39d69b3edeb94952ee`.
  Candidate library SHA:
  `cc507e5f44e8de18f57dfc4f1ab8f2e36ace21290a5ea559286a00ffe8e9a987`.
- Archive SHA, exact file list and **211 collected artifact hashes** pass.
  Twelve staged code hashes and three frozen collector hashes pass. A separate
  direct SSH preservation check verified **40 source/object/library/code files**
  and board exit status. Exact model hashes were checked during preparation
  and match the frozen baseline provenance.

Independent derived evidence is in
[verification.json](raw/k1-ime-m1-analysis-20261007/verification.json),
[its verifier](raw/k1-ime-m1-analysis-20261007/verify-completion.py) and
[remote preservation](raw/k1-ime-m1-analysis-20261007/remote-preservation.json).
These files are additional to the original 211-file receipt.

## Operator measurements

Four workers use the preferred-core mask `f`; route 3 and wide attention are
matched. Production graph operators use repeated weights. Fixture creation,
weight quantization/repacking and initial dispatch are outside each timer.
Each of six samples per arm runs for at least 100 ms. Arm order reverses on
alternating blocks. There are **144 measurements** in total.

The table shows mean milliseconds per graph call. A positive reduction means
less time. “Control” is the candidate library with the new path disabled;
“original” is the immutable route-3 library. Both comparisons matter because
the new wrapper and compiled code placement may affect timing.

| Model / operation | M / K / N | Original ms | Control ms | Candidate ms | Reduction vs control | Reduction vs original | Control range |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2B gate/up | 1 / 2048 / 6144 | 1.473 | 1.459 | 1.463 | −0.26% | +0.73% | 9.50% |
| 2B down | 1 / 6144 / 2048 | 1.582 | 1.639 | 1.791 | −9.23% | −13.18% | 26.36% |
| 2B output head | 1 / 2048 / 248320 | 44.496 | 45.005 | 44.585 | +0.93% | −0.20% | 2.54% |
| 4B gate/up | 1 / 2560 / 9216 | 2.300 | 2.281 | 2.290 | −0.42% | +0.43% | 2.08% |
| 4B down | 1 / 9216 / 2560 | 2.338 | 2.382 | 2.351 | +1.31% | −0.56% | 6.72% |
| 4B output head | 1 / 2560 / 248320 | 55.948 | 55.932 | 56.716 | −1.40% | −1.37% | 2.24% |
| 2B unchanged M32 | 32 / 2048 / 6144 | 7.681 | 7.835 | 7.837 | −0.02% | −2.03% | 1.06% |
| 4B unchanged M32 | 32 / 2560 / 9216 | 13.701 | 13.896 | 13.948 | −0.37% | −1.81% | 1.77% |

The preset gain must exceed both **3% and the observed control range**.
Each model also needs at least one actual M1 win, with no clear regression in
any shape or original-versus-wrapper comparison. None qualifies. The apparent
2B output-head improvement over wrapper control is below 3% and does not
improve on the preserved original mean. The noisy 2B down result fails the
benefit gate but does not establish a robust regression under the declared
control-spread test. The 4B output-head candidate includes one 61.47 ms sample;
it remains in the result rather than being discarded. No clear regression
flag was set by the preset gate, which does not prove equivalence.

See [raw operator samples](raw/k1-ime-m1-k32-20261007-121231/operator.jsonl)
and [frozen summary](raw/k1-ime-m1-k32-20261007-121231/summary.json).

## Skipped stages and interpretation

Full-model chunk/reset/RS snapshots, cold model ABBA at 256/2,048 prompt
tokens, and naturally complete useful answers were **not run**, because the
operator gate did not advance. There are no candidate prefill/decode token
rates or candidate quality scores to report. Native output identity does not
substitute for those tests or qualify speculative rollback.

The earlier sampled IME CPU share covers an entire hot loop. It does not
establish that its inner conditional branches are a large removable cost.
This pilot finds no reliable benefit from eliminating those branches alone.
It does not show that the hardware limit has been reached or that a different
load/dataflow or output-head partitioning candidate cannot help. Any such
candidate needs a separate declared mechanism and the same correctness and
performance gates. This run is closed without another benchmark rerun.
