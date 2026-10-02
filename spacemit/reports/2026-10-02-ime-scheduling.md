# IME M4 scheduling screen

## Implementation

The [completed profile](2026-10-02-prefill-profile.md) resolves three hot
assembly labels to the IME1 int8/int4 GEMM kernel. Its Q4_0 M4 path executes
two iterations per K32 block and repeats a vector configuration instruction.
The existing scale optimization from patch 0008 is already present.

[Candidate generator](../bench/make-k1-ime-candidate.py) adds opt-in modes:

| Mode | Change |
| --- | --- |
| 0 | Original kernel |
| 1 | Load A earlier, interleave B load/unpack/subtract with low dot operations |
| 2 | Unroll the two K32 iterations and remove their loop/configuration overhead |
| 3 | Combine modes 1 and 2 |
| 4 | Load 16 B scales once, widen once, gather B quartets and four A row scales into M4 accumulator order |
| 5 | Combine scale gathering with K32 unrolling |

The arithmetic and each accumulator's dot/scale/FMA order are preserved.
Dispatch changes only M4, K32, no zero points, and complete 16-column tiles.
Other shapes retain the original dispatch. `SPINE_IME_M4_SCHEDULE=1` through
`5` selects a candidate; absent/invalid values use mode 0.

The [controller](../bench/k1-ime-test.py) verifies the completed fast screen's
source, model and runtime hashes, then compiles one new IME object and links a
separate CPU library from the original build objects. The original checkout,
objects and server remain intact. Both model arms load the new library through
an isolated `LD_LIBRARY_PATH` overlay and must log their selected mode.

## Numerical check and harness correction

Initial run `k1-ime-20261002-182457` compiled successfully but failed the finite
output check before any timing. A diagnostic localized it to **mode 0**, K64,
seven blocks, N16, M1, no zero points: row 0, column 2 was infinite.

The test had called `quantize_a_row_i8(64, ...)`. That helper hardcodes
32-value blocks and strides. The harness now constructs generic one-row packed
blocks directly, while M4 uses its existing block-length-aware quantizer.
This corrects the test input; it does not modify the production quantizer.

The corrected [native check](raw/k1-ime-20261002-182457/numeric-debug.log)
passes **288 cases**, comparing all three candidate modes bit for bit against
control, checking unchanged inputs and output guards. Full M4 tiles also match
a scalar dot/scale/FMA reference bit for bit. Unsupported M4 column tails
check unchanged fallback behavior and guards, without asserting computed tail
values: the original M4 routine stores tails to a temporary buffer.

## Completed first screen

Run `k1-ime-20261002-183608` completed with exit 0 in **251.76 seconds**.
The corrected numerical gate passed 288 cases. Eight balanced blocks supplied
256 operator records over K2048/2560/6144/9216 and N16/32.
No candidate advanced; model stages were skipped.

| Mode | Mean reduction across eight shapes | Range across shapes | Clear regressions |
| --- | --- | --- | --- |
| Rescheduled loads, 1 | -9.71% | -14.46% to -1.20% | 7/8 |
| Unrolled, 2 | +0.67% | -0.53% to +1.57% | 0/8 |
| Both, 3 | -9.80% | -13.95% to -0.87% | 7/8 |

Positive reduction means faster. These are warm operator measurements, not
model results. See [summary](raw/k1-ime-20261002-183608/summary.json) and
[raw timing arms](raw/k1-ime-20261002-183608/operator.jsonl).

## Scale-gather follow-up and staged timing

Modes 4/5 reduce repeated scale loads and scalar A-scale loads using RVV
gathers at LMUL2. The packed input/output formats and floating accumulation
order remain the same. A [bounded native diagnostic](raw/k1-ime-20261002-182457/numeric-gather.log)
passes all five modes against control over 288 cases, including the scalar
M4 reference. This establishes correctness for those cases, not speed.

Fresh run: `k1-ime-20261002-184503`.
Board session: `k1_ime_k1-ime-20261002-184503`.
Collector: `k1_ime_collect_k1-ime-20261002-184503`.

1. Verify provenance, build isolated library, repeat the numerical gate.
2. Read the actual embedding/feed-forward K dimensions from both model GGUFs.
   Time M4/N16 and M4/N32 on four persistent workers pinned to cores 0-3.
   Six balanced blocks compare modes 0/4/5, covering all six order permutations.
   The first three candidates retain numerical coverage but are not timed again.
   Each timed arm calibrates to at
   least 50 ms for its slowest worker.
3. Require at least two shapes with mean gain above both 3% and the full control
   timing range, with no clear regression on another shape. Choose the eligible
   candidate with the largest mean gain.
4. Run control/candidate/candidate/control cold 2B/512 requests. Advance only
   after the same gain/noise gate to 2B/2k, then 4B/1k.

Model checks use direct decoding, four threads, batch/microbatch 32, F16 KV,
wide attention enabled, compact layout 0, and one output token. Prompt token
hashes, output tokens/hashes, exact uncached counts and activation markers
must agree. These requests measure prefill speed, not answer quality.

The operator test uses warm DDR tensors and excludes production packing,
staging and SPERT synchronization. Its gains cannot be treated as model gains.
This is an engineering screen, not a significance test. The job has a
45-minute limit after acquiring the shared board lock; its collector verifies
the compressed archive and individual artifact hashes. Long-context and
complete-answer confirmation remain necessary before adoption.

No candidate has qualified for model testing yet. See the new run's `phase` and final
`summary.json` for progress and results.
