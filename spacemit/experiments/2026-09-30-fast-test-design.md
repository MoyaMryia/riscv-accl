# Faster K1 optimization test method

See the [documentation guide](../DOCS.md) for related measurements and work.

Design date: 2026-09-30. Implementation update: 2026-10-01.
The `smoke`, `screen`, and gated `confirm-long` modes are now implemented in
[start-k1-fast-test.py](../bench/start-k1-fast-test.py), with the
[board controller](../bench/k1-fast-test.py). The corrected fast screen is
`k1-fast-20261001-224957`. The original layout pilot completed with exact outputs
and only small short-context gains; its protocol remains archived separately.

The sections below retain the design rationale and planning estimates.
Quality generation and cloud scoring use the existing grouped quality runner;
there is no separate fast-runner `quality` mode. The implementation has a
300-second operator budget (revised after the first timing timeout), a 45-minute model-screen budget, and no claim that
one-token requests establish answer quality.

## Objective

Make rejecting a bad optimization cheap. Spend full-model 8k inference and
cloud-judge time only on finalists. Record separate conclusions for kernel
correctness, kernel speed, model speed, and answer quality.

This design applies first to `SPINE_FA_K1_LAYOUT=0/16/32`. Other changes need
their own representative operator cases; recurrent changes must compare final
state as well as output. It does not assume that an attention speedup will
produce a comparable whole-model speedup.

## Why the current tests take so long

- The original quality protocol alternates cold and cached answers. Every
  cold request processes the document again. The new grouped protocol already
  reduces six questions from twelve document passes to seven.
- The completed original layout pilot ran twelve server launches, each with 128- and
  2048-token requests: 24 whole-model requests before any 8k confirmation.
- A kernel-only change still pays for all model layers, recurrent state,
  weights, tokenization, server startup, and generation in those requests.
- Existing observed first cold requests took about 474 seconds for 2B/8k
  and 1275 seconds for 4B/8k. Repeating them for each question is expensive.

The observed times are from the current chat workload, not measurements of
the proposed shorter tests. Queue time and build time are separate costs.

## Test ladder

| Stage | Work | Advancement rule | Planning budget |
| --- | --- | --- | --- |
| 0. Build and provenance | Reuse an isolated build directory; incrementally rebuild changed objects and link. Save source/build/model hashes and flags. | Build succeeds; requested kernel activates. | Build dependent |
| 1. Correctness | Existing 235 boundary/mask cases per layout; add selected 2048/8192-key cases. | Outputs match the control bit for bit for this layout change; no non-finite values or guard damage. | Target under 2 minutes; measure first |
| 2. Operator speed | Direct attention calls with Q=32, head=256, KV=128/2048/8192, actual model head counts and masks, four concurrent workers. Compare control and both candidates. | Rank candidates; retain both if tied within noise. | Cap at 300 seconds |
| 3. Small model screen | 2B, 512 prompt tokens, 1 output token; layouts 0/16/32/32/16/0. | No correctness/activation failure; select a provisional winner. | About 2-5 minutes |
| 4. Model confirmation | Winner vs control: 2B/2048 and 4B/1024, A/B/B/A for each; 1 output token. | Benefit survives full-model tests, with no clear regression on either model. | About 10-20 minutes |
| 5. Long-context pilot | Control and winner, one uncached 8192-token request each on each model; 1 output token. Reverse arm order between models. | No regression or output failure; long-context point estimate recorded. | Roughly 60 minutes plus overhead |
| 6. Quality and release evidence | Natural complete answers, grouped cached questions, targeted cold/cached checks; additional fixed replication if publishing a speed claim. | No quality regression; uncertainty reported; both models validated. | Separate, potentially long |

Stages 1-4 are the normal developer loop. Their initial planning estimate is
15-30 minutes plus build/queue time. These are targets, not measured promises.
Stage 5 alone costs approximately `2 * (474 + 1275) = 3498` seconds using
the old observed TTFTs, or 58 minutes, before overhead. Shortening generation
cannot remove that prefill cost.

Stop after a failed stage. A stopped or timed-out stage is incomplete, not a
pass. Do not start the full quality matrix for every code edit.

## Operator benchmark requirements

The original design called for extending the sequential C++ harness. The
implemented harness now uses four concurrent workers for numerical and timing
cases. Requirements below explain that implementation and future diagnostics.

- Use the same dispatcher, compact scratch, and packing loops as production.
  Check the activation marker for each candidate process.
- Use Q=32 to represent `-ub 32`. Include Q=16 and partial rows as diagnostics.
  Extract query/KV head counts and strides from each model configuration;
  the existing synthetic 6:2 grouping alone is not enough for timing.
- Test NK=8192 directly. This exposes the large KV scan without executing an
  8192-token full-model prefill. Include causal masks and dense attention.
- Start four real workers together with a barrier, using the production row
  partition and independent scratch. Time the slowest worker's completion.
  Record affinity so the runtime's preferred core group can be verified.
- Allocate and fill tensors outside the timed region. Include scratch clears,
  K/V packing, and the attention calculation inside it. Reuse allocations.
- Warm up each shape. Use at least five complete order-balanced timing blocks;
  each arm targets at least 100 ms of accumulated work. Record individual
  block wall times, medians, and spread. Cap the entire stage at 300 seconds;
  missing required blocks yields an incomplete result.
- Rotate deterministic input buffers when practical and report the repeated
  input policy. Repeated operator inputs can become more cache friendly than
  real inference; model confirmation is required.
- Keep the original smaller correctness cases. Add a few long-key cases with
  partial final tiles and grouped heads; size tensor allocation for them.

An operator gain with no model gain is a useful rejection result: the changed
operator is not saving enough of total request time. Measure its model-time
share if choosing the next optimization target. Do not extrapolate a kernel
percentage directly to whole-model latency.

## Full-model measurement rules

For stages 3-5 use deterministic token-ID prompts, `cache_prompt=false`,
temperature 0, the same seed, F16 KV, four threads, batch/microbatch 32,
plain decoding, and identical context allocation within every comparison.
Use one output token to measure prefill and first-token latency. Require that
the stream completes with exactly one returned token, and record its ID/hash.
One-token runs provide no decode-throughput or answer-quality evidence.

Keep a server alive for multiple requests of the same arm where the runner
supports this, but every timed cold request must reset/reprocess its prompt
and recurrent state. Verify zero reused prompt tokens and the expected
processed-token count. Weight pages can remain resident: report this as
uncached prompt inference with resident weights. Save startup timing
separately instead of counting it as kernel speed.

The current layout switch is read once per process. Changing an environment
variable around requests cannot switch arms inside a loaded server. Use
separate server processes for arm switches, and run them serially on the
board. Do not keep multiple model servers resident to reduce startup time.
Incremental builds can reuse object files; baseline timing must still come
from the current matched binary and hardware session.

Capture server prompt time and client TTFT. Compare prompt time as the primary
prefill metric and TTFT as the user-facing check. Neither metric substitutes
for a meaningful decode test when the change affects decoding.

## Decisions and uncertainty

- First estimate the board's baseline variation from repeated controls.
  A 3% improvement is a provisional engineering threshold, not a significance
  test. Promote candidates that exceed both that threshold and the measured
  noise envelope. A smaller result is inconclusive, not proof of no benefit.
- If both compact layouts are tied, compare them at 2B/2048 before choosing.
  Do not pick solely from the lower scratch size. Q16 repeats K/V packing.
- Stage 4 has only two launches per arm/model. Report all launch values;
  treat it as screening. Permit one extra balanced block if needed, within a
  45-minute total model-screen budget. Otherwise stop as inconclusive.
- Early stopping and selecting the best candidate bias the observed gain.
  For a release claim, freeze the winner, prompt, metrics, and repetition
  count; collect new independent confirmation data with no winner selection.
- The existing `paired-stats.py` reports a Welch interval over launches,
  despite its filename. Reuse it only with its stated independence assumptions;
  repeated requests in one process are not independent launches. A true paired
  analysis needs an explicit block-aware implementation.
- A single baseline/candidate 8k pair is a regression pilot and point estimate.
  Replicate before claiming a reliable 8k improvement.

## Quality without the 32-token problem

Speed screening may use one token because its question is how long prefill
takes. A quality answer must finish naturally; use the existing up-to-512-token
allow-EOS workflow. Truncated answers fail the quality gate.

For the finalist, prime each model/document once, ask all six cached questions,
then run the cold checks required for that change. A preliminary cached-only
quality screen costs one document prefill per configuration instead of six;
it is explicitly missing cold-answer equivalence evidence. Full cold/cached
coverage remains the final gate when deploying cache behavior changes.

Use frozen documents and evidence checks before the cloud judge. Check facts,
citations, completeness, and truncation. Judge only complete eligible answers,
with blind arm labels and the same rubric. Reuse existing judge results only
when answer/input hashes, judge configuration, and rubric match. Baseline
quality records cannot establish that a new candidate produces the same answer.

For the compact layout, bitwise operator equivalence is required by design.
Any full-model token divergence triggers investigation of logits/state or
dispatch before quality scoring can justify adoption. Cloud scores supplement
numerical checks; they cannot excuse a memory error or unexplained arithmetic
change in an intended exact layout transformation.

## Runner interface and execution

Available modes: `smoke`, `screen`, and `confirm-long`. `smoke` runs native
correctness. `screen` adds operator timing and model screening, stopping if
no candidate exceeds both 3% and control variation. `confirm-long` executes the
same gated pipeline and runs the 8k pairs only for an eligible winner.
An eligible completed screen may advance with `--resume --mode confirm-long`;
completed stages are reused only after provenance and artifact checks.

For complete-answer generation/judging, use `run-all-document-quality.py`
with its grouped schedule. It is a separate quality gate; the fast runner does
not automatically spend cloud or long-document time after an inconclusive
screen. Candidate-vs-control quality still needs an explicitly matched setup.

Each stage writes inputs, source/model/runtime hashes, activation evidence,
raw timings, outputs, decision, and exit status into its own directory.
Resume only completed stages with matching hashes. Baseline performance is
remeasured in the same session; historic timing is for planning only.

Run one board tmux job under the shared benchmark lock with bounded stage
timeouts and a separate local collector. On timeout, terminate the server and
record failure before releasing the lock. Report initial queue status and
final summary, so the user can wait without an open blocking tool call.

## Implemented components and next work

1. The C++ harness now has persistent concurrent workers for timing and
   concurrent numerical checks. `--long` adds six cases for 241 total per mode.
   Timing reads actual model head counts from GGUF metadata and records CPU
   affinity, slowest-worker and wall time for dense/causal 128/2048/8192-key shapes.
2. The lifecycle runner has `--verify-cold`, exact input-token hashes, and separate
   startup timing. One-token screens require completed streams and matching
   input/output hashes across all expected arms.
3. The controller records source, model, compiler, build, harness and runtime
   fingerprints, stage artifact hashes, raw block timings, decisions and budgets.
   Incomplete stages fail; valid completed stages can resume without rerunning.
4. Five local gate tests and the existing fake-server slot regression passed.
   Native compilation and 241 concurrent numerical cases per layout passed.
   The first operator run exceeded its 90-second budget and failed. The corrected
   run completed all six blocks in 136.21 seconds and the model screen in 214.50
   seconds. Q16/Q32 gains were 0.32%/0.53%, below threshold; total run 507.14 seconds.
5. Model screens retain separate server launches because layout selection is
   cached per process. The current implementation does not keep a server loaded
   across arm switches. It reuses the isolated build and resident weight pages.
6. Record completed screen duration before promising a developer-loop time. Additional
   independent replication and full-answer quality are release gates.

Related: [layout experiment](2026-09-30-k1-attention-layout.md),
[code audit](../reports/2026-09-30-code-optimization-audit.md),
[quality benchmark](../reports/2026-09-30-chat-quality-benchmark.md).

Completed result: [October 2 update](../reports/2026-10-02-prefill-profile.md).
