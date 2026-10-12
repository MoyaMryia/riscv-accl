# Faster K1 optimization test method

See the [documentation guide](../DOCS.md) for related measurements and work.

Design date: 2026-09-30. Implementation update: 2026-10-01.
The `smoke`, `screen`, and gated `confirm-long` modes are now implemented in
[start-k1-fast-test.py](../bench/start-k1-fast-test.py), with the
[board controller](../bench/k1-fast-test.py). The corrected fast screen is
`k1-fast-20261001-224957`. The original layout pilot completed with exact
outputs and only small short-context gains. Its protocol remains archived
separately.

The sections below retain the design rationale and the planning estimates.
Quality generation and cloud scoring use the existing grouped quality runner.
There is no separate fast-runner `quality` mode. The implementation has a
300-second operator budget, which we revised after the first timing timeout.
It has a 45-minute model-screen budget. The design makes no claim that
one-token requests establish answer quality.

## Objective

Make the rejection of a bad optimization cheap. Spend full-model 8k inference
and cloud-judge time only on finalists. Record separate conclusions for kernel
correctness, kernel speed, model speed, and answer quality.

This design applies first to `SPINE_FA_K1_LAYOUT=0/16/32`. Other changes need
their own representative operator cases. Recurrent changes must compare the
final state and the output. The design does not assume that an attention
speedup gives a comparable whole-model speedup.

## Why the current tests take so long

- The original quality protocol alternates cold answers and cached answers.
  Every cold request processes the document again. The new grouped protocol
  already reduces six questions from twelve document passes to seven.
- The completed original layout pilot ran twelve server launches. Each
  launch made 128-token and 2048-token requests: 24 whole-model requests
  before any 8k confirmation.
- A kernel-only change still pays for all model layers, recurrent state,
  weights, tokenization, server startup, and generation in those requests.
- Existing observed first cold requests took about 474 seconds for 2B/8k and
  1275 seconds for 4B/8k. A repeat of each question is expensive.

The observed times come from the current chat workload. They are not
measurements of the proposed shorter tests. Queue time and build time are
separate costs.

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
Stage 5 alone costs approximately `2 * (474 + 1275) = 3498` seconds with the
old observed TTFTs, or 58 minutes, before overhead. Shortening generation
cannot remove that prefill cost.

Stop after a failed stage. A stopped or timed-out stage is incomplete. It is
not a pass. Do not start the full quality matrix for every code edit.

## Operator benchmark requirements

The original design called for an extension of the sequential C++ harness.
The implemented harness now uses four concurrent workers for numerical and
timing cases. The requirements below explain that implementation and future
diagnostics.

- Use the same dispatcher, compact scratch, and packing loops as production.
  Check the activation marker for each candidate process.
- Use Q=32 to represent `-ub 32`. Include Q=16 and partial rows as
  diagnostics. Extract query/KV head counts and strides from each model
  configuration. The existing synthetic 6:2 grouping is not enough on its
  own for timing.
- Test NK=8192 directly. This test exposes the large KV scan without an
  8192-token full-model prefill. Include causal masks and dense attention.
- Start four real workers together with a barrier. Use the production row
  partition and independent scratch. Time the completion of the slowest
  worker. Record affinity, so that you can verify the preferred core group of
  the runtime.
- Allocate and fill tensors outside the timed region. Put scratch clears,
  K/V packing, and the attention calculation inside the timed region. Reuse
  allocations.
- Warm up each shape. Use at least five complete order-balanced timing
  blocks. Each arm must accumulate at least 100 ms of work. Record individual
  block wall times, medians, and spread. Cap the entire stage at 300 seconds.
  A missing required block gives an incomplete result.
- Rotate deterministic input buffers where practical. Report the repeated
  input policy. Repeated operator inputs can become more cache friendly than
  real inference, so model confirmation is necessary.
- Keep the original smaller correctness cases. Add a few long-key cases with
  partial final tiles and grouped heads. Size the tensor allocation for those
  cases.

An operator gain with no model gain is a useful rejection result. The changed
operator does not save enough of the total request time. Measure the
model-time share if you select the next optimization target. Do not
extrapolate a kernel percentage directly to whole-model latency.

## Full-model measurement rules

For stages 3-5, use deterministic token-ID prompts, `cache_prompt=false`,
temperature 0, the same seed, F16 KV, four threads, batch/microbatch 32, plain
decoding, and identical context allocation in every comparison.

Use one output token to measure prefill and first-token latency. The stream
must complete with exactly one returned token. Record its ID and its hash.
One-token runs give no decode-throughput evidence and no answer-quality
evidence.

Keep a server alive for multiple requests of the same arm where the runner
supports this. But every timed cold request must reset and reprocess its
prompt and its recurrent state. Verify zero reused prompt tokens and the
expected processed-token count. Weight pages can remain resident. Report this
case as uncached prompt inference with resident weights. Save startup timing
separately. Do not count startup as kernel speed.

The current layout switch is read once per process. A change to an
environment variable between requests cannot switch arms inside a loaded
server. Use separate server processes for arm switches, and run them serially
on the board. Do not keep multiple model servers resident to reduce startup
time. Incremental builds can reuse object files. Baseline timing must still
come from the current matched binary and hardware session.

Capture server prompt time and client TTFT. Use prompt time as the primary
prefill metric and TTFT as the user-facing check. Neither metric replaces a
meaningful decode test when the change affects decoding.

## Decisions and uncertainty

- First estimate the baseline variation of the board from repeated controls.
  A 3% improvement is a provisional engineering threshold. It is not a
  significance test. Promote the candidates that exceed both that threshold
  and the measured noise envelope. A smaller result is inconclusive. It is
  not proof of no benefit.
- If both compact layouts are tied, compare them at 2B/2048 before you select
  one. Do not select only from the lower scratch size. Q16 repeats K/V
  packing.
- Stage 4 has only two launches per arm/model. Report all launch values and
  treat the stage as screening. Permit one extra balanced block if you need
  it, within a 45-minute total model-screen budget. In all other cases, stop
  as inconclusive.
- Early stopping and the selection of the best candidate bias the observed
  gain. For a release claim, freeze the winner, the prompt, the metrics, and
  the repetition count. Then collect new independent confirmation data with
  no winner selection.
- The existing `paired-stats.py` reports a Welch interval over launches,
  despite its filename. Reuse it only with its stated independence
  assumptions. Repeated requests in one process are not independent launches.
  A true paired analysis needs an explicit block-aware implementation.
- A single baseline/candidate 8k pair is a regression pilot and a point
  estimate. Replicate it before you claim a reliable 8k improvement.

## Quality without the 32-token problem

Speed screening can use one token, because its question is the prefill
duration. A quality answer must finish naturally. Use the existing
up-to-512-token allow-EOS workflow. Truncated answers fail the quality gate.

For the finalist, prime each model/document once. Ask all six cached
questions, and then run the cold checks that the change requires. A
preliminary cached-only quality screen costs one document prefill per
configuration instead of six. This screen gives no cold-answer equivalence
evidence. Full cold/cached coverage remains the final gate for the
deployment of cache behavior changes.

Use frozen documents and evidence checks before the cloud judge. Check facts,
citations, completeness, and truncation. Judge only complete eligible
answers, with blind arm labels and the same rubric. Reuse existing judge
results only when answer/input hashes, judge configuration, and rubric match.
Baseline quality records cannot establish that a new candidate produces the
same answer.

For the compact layout, bitwise operator equivalence is a design
requirement. Investigate logits, state, or dispatch after any full-model
token divergence. Only then can quality scoring justify adoption. Cloud
scores supplement numerical checks. They cannot excuse a memory error or an
unexplained arithmetic change in an intended exact layout transformation.

## Runner interface and execution

Available modes: `smoke`, `screen`, and `confirm-long`. `smoke` runs native
correctness. `screen` adds operator timing and model screening, and it stops
if no candidate exceeds both 3% and control variation. `confirm-long`
executes the same gated pipeline and runs the 8k pairs only for an eligible
winner. An eligible completed screen can advance with
`--resume --mode confirm-long`. The runner reuses completed stages only after
provenance and artifact checks.

For complete-answer generation and judging, use
`run-all-document-quality.py` with its grouped schedule. That schedule is a
separate quality gate. The fast runner does not spend cloud or
long-document time automatically after an inconclusive screen.
Candidate-vs-control quality still needs an explicitly matched setup.

Each stage writes inputs, source/model/runtime hashes, activation evidence,
raw timings, outputs, decision, and exit status into its own directory.
Resume only completed stages with matching hashes. The runner remeasures
baseline performance in the same session. Historic timing is for planning
only.

Run one board tmux job under the shared benchmark lock. Use bounded stage
timeouts and a separate local collector. On a timeout, terminate the server
and record the failure before you release the lock. Report the initial queue
status and the final summary. The user can then wait without an open
blocking tool call.

## Implemented components and next work

1. The C++ harness now has persistent concurrent workers for timing and
   concurrent numerical checks. `--long` adds six cases, for 241 cases in
   total per mode. Timing reads actual model head counts from GGUF metadata.
   It records CPU affinity, slowest-worker time, and wall time for the
   dense/causal 128/2048/8192-key shapes.
2. The lifecycle runner has `--verify-cold`, exact input-token hashes, and
   separate startup timing. One-token screens require completed streams and
   matching input/output hashes in all expected arms.
3. The controller records source, model, compiler, build, harness, and
   runtime fingerprints, stage artifact hashes, raw block timings, decisions,
   and budgets. Incomplete stages fail. Valid completed stages can resume
   without a rerun.
4. Five local gate tests and the existing fake-server slot regression
   passed. Native compilation and 241 concurrent numerical cases per layout
   passed. The first operator run exceeded its 90-second budget and failed.
   The corrected run completed all six blocks in 136.21 seconds and the
   model screen in 214.50 seconds. The Q16/Q32 gains were 0.32%/0.53%, below
   threshold. The total run took 507.14 seconds.
5. Model screens retain separate server launches, because the layout
   selection is cached per process. The current implementation does not keep
   a server loaded across arm switches. It reuses the isolated build and the
   resident weight pages.
6. Record the completed screen duration before you promise a developer-loop
   time. Additional independent replication and full-answer quality are
   release gates.

Related: [layout experiment](2026-09-30-k1-attention-layout.md),
[code audit](../reports/2026-09-30-code-optimization-audit.md),
[quality benchmark](../reports/2026-09-30-chat-quality-benchmark.md).

Completed result: [October 2 update](../reports/2026-10-02-prefill-profile.md).
