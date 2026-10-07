# Hybrid SSM: complete useful-answer pilot

Status: **completed; not qualified for adoption** as `k1-ssm-quality-20261006-131234`.
All 24 answers stopped naturally; 12 pairs are text-identical. Exact graph and
full-model state gates pass. Total answer time falls 2.92%/2.13% for 2B/4B,
with usefulness unchanged at 2/6 and 5/6. Both models miss the >3% total-time
and 6/6 usefulness gates. The 30-minute monitor is paused.
See [measured results](../reports/2026-10-06-ssm-complete-answer-results.md),
[passing complete answer](../reports/2026-10-06-ssm-useful-answer-example.md),
and [campaign state](../reports/raw/k1-ssm-quality-campaign.json).

The [unconditional candidate](../reports/2026-10-06-ssm-conv-repaired-results.md)
passes exact graph checks and substantially improves 32-token graph timing,
but regresses single-token graph time. This experiment selects RVV only when
the actual **per-sequence microbatch contains at least 32 tokens**. Shorter
batches, including single-token decode and partial prefill tails, retain the
original convolution graph. Persistent history stays time-major in both paths.

`SPINE_K1_SSM_CONV=3` enables this policy. The state builder and convolution
operator use the same token-based decision. Activation logs record requested
mode, selected mode, token count, layout, CPU-only scheduler and RS setting.
RS configurations and other architectures/backends retain the reference.
All paths are opt-in and use private libraries; production defaults stay unchanged.

## Qualification and tasks

1. Build isolated libraries from the pinned benchmark source/runtime.
2. Original/control/hybrid each run all 432 native graph cases; output and
   history dump hashes must match. Add both actual channel counts at token
   counts 31/32 with two sequences and padded projection inputs.
3. Run 48 alternating-order warm graph timing samples: six blocks, two model
   shapes, tokens 1/32, control/hybrid. Retain the existing 3%/control-spread
   benefit and no-regression gates.
4. Compare all vocabulary logits after chunks **32, 1, 31, 32**, then reset and
   repeat, on both models and RS=0/3. Require 16 exact comparisons/model and
   markers for accelerated full batches, reference decode/partial batches and
   RS reference fallback. This qualifies fallback, not RS rollback.
5. Run **24 naturally stopped responses**: six paired tasks on both 2B/4B.
   Tasks are documented API routes, a multi-section trace, receipt aggregation,
   interval/free-window Python functions, Unicode run coding functions, and a
   detailed Chinese shipping/returns policy with examples. The factual cases
   use the whole approximately 2048-token document; no retrieval or input
   reduction is introduced. Code tasks use held-out functional tests.
6. Verify artifacts locally and score each eligible answer pair in both
   presentation orders using the previously authorized cloud judge,
   `mimo-v2.6-flash` at `https://api.xiaomimimo.com/v1`. The key remains local in
   `~/.secret_ai_key`; it is never copied to the board or serialized.

Both arms use the same private build, route 3, wide RVV attention, direct
generation (MTP off), Q4_0 weights, F16 K/V, four workers, batch/microbatch 32,
one slot, context 6144, and no context shifting. Temperature 0, seed 42,
reasoning disabled and `cache_prompt=false` are identical for each paired task.
Model order is control/hybrid for 2B and hybrid/control for 4B; task order is
reversed in the hybrid arm. This is one pair per task, a descriptive pilot.

## Complete versus useful

The output guard is 512 tokens for brief factual tasks and **2048** for code
and policy prose. There is no ignored EOS or fixed-length generation. An
answer stopped by its guard is retained as an incomplete quality failure;
it cannot pass usefulness. The per-request timeout is 30 minutes, and the
board execution budget is eight hours. These are safety bounds, not target
answer lengths or promised completion times.

Every eligible pair must have naturally stopped nonempty answers, no reasoning
text or drafting, zero cached tokens, matching full prompt counts, the correct
slot, consistent completion counts and positive phase timings. Record full
answers, output lengths, TTFT, prefill/decode time and complete-task wall time.
Exact output text is reported separately; matching text alone cannot make an
incorrect answer useful.

A candidate answer is useful in this pilot only if required facts/citations
and any held-out code checks pass, with mean cloud score at least **4/5**.
Report shared baseline errors and candidate regressions separately. Relative
quality requires no deterministic regression, mean score loss at most 0.25
and worst pair loss at most 0.5. Qualification also requires exact state
identity, the unchanged operator gate and a total complete-task wall-time
reduction greater than 3% for each model. One pair/task does not establish
statistical significance or general equivalence.

Complete-answer collection proceeds after exact state checks even if the
operator performance gate is inconclusive, as explicitly requested for this
quality mission. Such a rejection remains an adoption failure; thresholds
are not relaxed to obtain an answer. Correctness/state failures stop execution.

## Offload, monitoring and recovery

```bash
python3 spacemit/bench/test-k1-ssm-quality.py
python3 spacemit/bench/start-k1-ssm-quality.py

# Recover collection only, with the current run directory.
python3 spacemit/bench/start-k1-ssm-quality.py --collect-only --run-dir RUN
# Recover an interrupted cloud judgment after verified collection.
python3 spacemit/bench/start-k1-ssm-quality.py --score-only --run-dir RUN
```

The board job and local collector/scorer run in tmux. Generation exit,
collection exit and collector/scoring exit have separate markers. A completed
negative quality/performance result is recorded in `ssm-quality-summary.json`
and is not a transport failure. A technical failure receives a supported
repair and fresh isolated run; each such rerun gets a **new** 30-minute
scheduled task, and the old monitor is paused after confirming creation.
Monitoring stays quiet while healthy and incomplete. It reports final results,
technical failures/repairs or required user action.
