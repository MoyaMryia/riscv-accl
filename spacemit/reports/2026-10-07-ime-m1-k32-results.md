# Fixed K32 M1 IME specialization results

Date: October 7, 2026, Asia/Singapore. Run:
`k1-ime-m1-k32-20261007-121231`. Status: **completed and independently
verified**. The board execution took **18.11 minutes**, and it started at
12:12. The board and collector exit statuses are zero. The
[protocol](../experiments/2026-10-07-ime-m1-k32.md) declared the correctness and
the performance gates before the dispatch.

## Decision

Keep this candidate disabled. The removal of the fixed K32 inner-loop counter
and branches preserves the outputs, but **none of the eight measured shapes
clears the benefit gate**. We launched no longer model test and no
useful-answer test. This result is a completed negative operator screen. It is
not a build failure and not a correctness failure.

The baseline is the preserved route-3 CPU library. The candidate changes only
the eligible single-row Q4_0 K32 calls. All the weights, the quantizer and
scales, the load order, the integer dots, the outer-block FP32 fused
accumulation, and the output tails remain. M2/M3/M4, the zero points, K64, and
Q8 retain their original path. The private candidate is opt-in, with
`SPINE_IME_M1_K32=1`. The production defaults are unchanged.

## Correctness and preservation

- Three local transformation checks passed. The expanded assembly instruction
  trace matches two original iterations, after the removal of the inner-loop
  control. The original fallback bodies and macros remain, and the checks
  refuse source drift.
- **480 raw cases** pass the bitwise original/candidate identity, the
  processed-row counts, the input/output guards, the independent scalar M1
  Q4_0 reference checks, and the original full-tile M4 reference checks, where
  they are supported. The coverage includes K32/K64, four K-block counts,
  M1/2/3/4/7, N tails, and zero points.
- **104 production graph cases in each of three arms** — the preserved
  original, the wrapper control off, and the candidate on — have identical
  collected dumps. The Q8 fallback, the production weight repacking, and the
  input/output/scratch guards pass. The dump SHA is
  `e31997719879fb9a858f9e970af7e11ceb68124657d41c53bd3b3f82c4dbd4dc`.
- Six additional actual FFN and output-head shapes pass in all three arms. Both
  output heads retain and compare **all 248,320 columns**. No vocabulary is
  pruned.
- The decoded machine code contains two consecutive eight-instruction `vmadot`
  groups, one four-instruction FP32 block accumulation, the outer K loop, and
  the original tail stores. The fixed helper has no inner-loop branch. The
  original inner loops remain in the fallback code. The removal of this control
  does not remove the loads, the nibble unpacking, or the matrix dot work, which
  dominate the loop body.
- The recreated original link has the exact preserved route-3 library SHA,
  `43363dad9c500bd71d5ad7cc9d0108efff5c58133b7b8b39d69b3edeb94952ee`. The
  candidate library SHA is
  `cc507e5f44e8de18f57dfc4f1ab8f2e36ace21290a5ea559286a00ffe8e9a987`.
- The archive SHA, the exact file list, and **211 collected artifact hashes**
  pass. Twelve staged code hashes and three frozen collector hashes pass. A
  separate direct SSH preservation check verified **40 source, object,
  library, and code files**, and the board exit status. We checked the exact
  model hashes during the preparation, and they match the frozen baseline
  provenance.

Independent derived evidence is in
[verification.json](raw/k1-ime-m1-analysis-20261007/verification.json), in
[its verifier](raw/k1-ime-m1-analysis-20261007/verify-completion.py), and in
[the remote preservation](raw/k1-ime-m1-analysis-20261007/remote-preservation.json).
These files are additional to the original 211-file receipt.

## Operator measurements

The four workers use the preferred-core mask `f`. The route 3 and the wide
attention are matched. The production graph operators use repeated weights. The
fixture creation, the weight quantization and repacking, and the initial
dispatch are outside each timer. Each of the six samples per arm runs for at
least 100 ms. The arm order reverses on the alternating blocks. There are
**144 measurements** in total.

The table shows the mean milliseconds per graph call. A positive reduction
means less time. "Control" is the candidate library with the new path disabled,
and "original" is the immutable route-3 library. Both comparisons matter,
because the new wrapper and the compiled code placement can affect the timing.

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

The preset gain must exceed both **3% and the observed control range**. Each
model needs also at least one actual M1 win, with no clear regression in any
shape or in the original-versus-wrapper comparison. No shape qualifies. The
apparent 2B output-head improvement over the wrapper control is below 3%, and
it does not improve on the preserved original mean. The noisy 2B down result
fails the benefit gate, but it does not establish a robust regression under the
declared control-spread test. The 4B output-head candidate includes one
61.47 ms sample, and that sample remains in the result. The preset gate set no
clear-regression flag, and that fact does not prove equivalence.

See the [raw operator samples](raw/k1-ime-m1-k32-20261007-121231/operator.jsonl)
and the [frozen summary](raw/k1-ime-m1-k32-20261007-121231/summary.json).

## Skipped stages and interpretation

We **did not run** the full-model chunk/reset/RS snapshots, the cold model
ABBA at 256 and 2,048 prompt tokens, or the naturally complete useful answers,
because the operator gate did not advance. There are no candidate
prefill/decode token rates and no candidate quality scores to report. The
native output identity does not substitute for those tests, and it does not
qualify speculative rollback.

The earlier sampled IME CPU share covers an entire hot loop. It does not
establish that its inner conditional branches are a large removable cost. This
pilot finds no reliable benefit from an elimination of those branches alone. It
does not show that the hardware limit is reached, and it does not show that a
different load/dataflow or output-head partitioning candidate cannot help. Any
such candidate needs a separate declared mechanism, and the same correctness
and performance gates. We closed this run without another benchmark rerun.
