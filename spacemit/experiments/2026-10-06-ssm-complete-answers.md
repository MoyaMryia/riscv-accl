# Hybrid SSM: complete useful-answer pilot

Status: **completed; not qualified for adoption** as
`k1-ssm-quality-20261006-131234`. All 24 answers stopped naturally, and 12
pairs are text-identical. The exact graph and full-model state gates pass.
Total answer time falls 2.92%/2.13% for 2B/4B, and usefulness is unchanged
at 2/6 and 5/6. Both models miss the >3% total-time gate and the 6/6
usefulness gate. The 30-minute monitor is paused. See the
[measured results](../reports/2026-10-06-ssm-complete-answer-results.md),
the [passing complete answer](../reports/2026-10-06-ssm-useful-answer-example.md),
and the [campaign state](../reports/raw/k1-ssm-quality-campaign.json).

The [unconditional candidate](../reports/2026-10-06-ssm-conv-repaired-results.md)
passes the exact graph checks and substantially improves 32-token graph
timing, but it regresses single-token graph time. This experiment selects
RVV only when the actual **per-sequence microbatch contains at least 32
tokens**. Shorter batches, including single-token decode and partial prefill
tails, retain the original convolution graph. Persistent history stays
time-major in both paths.

`SPINE_K1_SSM_CONV=3` enables this policy. The state builder and the
convolution operator use the same token-based decision. Activation logs
record the requested mode, the selected mode, the token count, the layout,
the CPU-only scheduler, and the RS setting. RS configurations and other
architectures and backends retain the reference. All paths are opt-in and
use private libraries. Production defaults stay unchanged.

## Qualification and tasks

1. Build isolated libraries from the pinned benchmark source and runtime.
2. Run all 432 native graph cases on each of the original, control, and
   hybrid arms. The output and history dump hashes must match. Add both
   actual channel counts at token counts 31 and 32, with two sequences and
   padded projection inputs.
3. Run 48 alternating-order warm graph timing samples: six blocks, two
   model shapes, tokens 1 and 32, control and hybrid. Retain the existing
   3%/control-spread benefit gate and the no-regression gates.
4. Compare all vocabulary logits after chunks **32, 1, 31, 32**. Then reset
   and repeat on both models and at RS=0/3. Require 16 exact comparisons per
   model, and markers for accelerated full batches, reference decode and
   partial batches, and RS reference fallback. This stage qualifies the
   fallback. It does not qualify RS rollback.
5. Run **24 naturally stopped responses**: six paired tasks on both 2B and
   4B. The tasks are documented API routes, a multi-section trace, receipt
   aggregation, interval and free-window Python functions, Unicode run
   coding functions, and a detailed Chinese shipping and returns policy with
   examples. The factual cases use the whole approximately 2048-token
   document. No retrieval and no input reduction is introduced. The code
   tasks use held-out functional tests.
6. Verify the artifacts locally, and score each eligible answer pair in both
   presentation orders with the previously authorized cloud judge,
   `mimo-v2.6-flash` at `https://api.xiaomimimo.com/v1`. The key remains
   local in `~/.secret_ai_key`. Never copy it to the board, and never
   serialize it.

Both arms use the same private build, route 3, wide RVV attention, direct
generation (MTP off), Q4_0 weights, F16 K/V, four workers,
batch/microbatch 32, one slot, context 6144, and no context shifting.
Temperature 0, seed 42, reasoning disabled, and `cache_prompt=false` are
identical for each paired task. Model order is control/hybrid for 2B and
hybrid/control for 4B. The hybrid arm reverses the task order. This stage
has one pair per task, and it is a descriptive pilot.

## Complete versus useful

The output guard is 512 tokens for brief factual tasks and **2048** for code
and policy prose. There is no ignored EOS and no fixed-length generation.
The run retains an answer that its guard stopped, as an incomplete quality
failure. Such an answer cannot pass usefulness. The per-request timeout is
30 minutes, and the board execution budget is eight hours. These values are
safety bounds. They are not target answer lengths and not promised
completion times.

Every eligible pair must have naturally stopped nonempty answers, no
reasoning text, no drafting, zero cached tokens, matching full prompt
counts, the correct slot, consistent completion counts, and positive phase
timings. Record full answers, output lengths, TTFT, prefill time, decode
time, and complete-task wall time. Report exact output text separately.
Matching text alone cannot make an incorrect answer useful.

A candidate answer is useful in this pilot only if the required facts and
citations and any held-out code checks pass, and the mean cloud score is at
least **4/5**. Report shared baseline errors and candidate regressions
separately. Relative quality requires no deterministic regression, a mean
score loss of at most 0.25, and a worst pair loss of at most 0.5.
Qualification requires also exact state identity, the unchanged operator
gate, and a total complete-task wall-time reduction greater than 3% for
each model. One pair per task does not establish statistical significance or
general equivalence.

The runner collects complete answers after the exact state checks, even if
the operator performance gate is inconclusive. The quality mission requested
this order explicitly. Such a rejection remains an adoption failure, and the
run does not relax the thresholds to obtain an answer. Correctness and state
failures stop execution.

## Offload, monitoring and recovery

```bash
python3 spacemit/bench/test-k1-ssm-quality.py
python3 spacemit/bench/start-k1-ssm-quality.py

# Recover collection only, with the current run directory.
python3 spacemit/bench/start-k1-ssm-quality.py --collect-only --run-dir RUN
# Recover an interrupted cloud judgment after verified collection.
python3 spacemit/bench/start-k1-ssm-quality.py --score-only --run-dir RUN
```

The board job and the local collector/scorer run in tmux. Generation exit,
collection exit, and collector/scoring exit have separate markers. A
completed negative quality or performance result is recorded in
`ssm-quality-summary.json`. Such a result is not a transport failure. A
technical failure receives a supported repair and a fresh isolated run.
Each such rerun gets a **new** 30-minute scheduled task, and the runner
pauses the old monitor after it confirms the creation. Monitoring stays
quiet while the run is healthy and incomplete. It reports final results,
technical failures and repairs, or a required user action.
