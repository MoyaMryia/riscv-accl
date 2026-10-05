# Proposed adaptive checkpoint MTP policy

Status: original design; an isolated candidate and gated screen are now
[implemented](2026-10-04-adaptive-mtp-implementation.md). Thresholds and native
switching still require qualification; no inference default change is implied.
Based on the [complete-answer pilot](../reports/2026-10-03-mtp-usefulness-results.md)
and a read of the tested `a990751` server on `musepipro-wg`.

## Objective

Use checkpoint MTP where it reduces complete-task latency without a quality
regression. Keep full prompts and the same model, weights, KV types, sampling
and output requirements. Keep `SPINE_SPEC_RS=0`. Semantic usefulness and
functional correctness supplement token hashes; identity is not required.

## What the current implementation supports

- `tools/server/server-context.cpp::server_slot::can_speculate()` already
  gates drafting by active slot count: `SPINE_SPEC_MAX_ACTIVE` defaults to 1.
  This concurrency policy is present, but our pilot used one slot only.
- `SPINE_SPEC_LOWACC` optionally disables drafting for the rest of a request
  when fewer than 0.75 draft tokens per verification step are accepted over
  12 steps. This measures accepted tokens per step, not accepted/generated
  percentage. The prose cases average roughly 1.6 accepted draft tokens per
  step and thus would not trigger that threshold, despite slowing down.
- The request controls `speculative.n_max` and `speculative.type` in
  `tools/server/server-schema.cpp` are inside `#if 0`. Sending those fields
  is not an implemented request-level switching solution.
- MTP processing and target embedding extraction use the loaded speculative
  context beyond just draft scheduling. Stopping drafts must not be assumed
  to recover the cost or memory footprint of a standalone direct server.

## Layer 1: choose at request start

Add an optional, explicitly experimental request setting:

```json
{
  "spine_mtp": {
    "mode": "auto",
    "workload": "code",
    "expected_output_tokens": 512
  }
}
```

Modes: `off`, `on`, `auto`. Omission preserves the existing server behavior;
the client workflow can opt into `auto` after validation. Reject unknown
values rather than silently accepting ineffective fields. `on` requests MTP
but retains context/load limits and the measured fallback. A separate bench
switch can force always-on behavior for the control arm.

Application hints are preferable to keyword guessing. An output token cap is
only an upper bound; it does not establish that the answer will be long.
Unknown expected length stays conservative.

| Request | Initial proposal | Evidence / qualification |
| --- | --- | --- |
| Validated code task family, expected output >=256 tokens | Start MTP with draft length 3 | Unicode code passes functional tests with lower latency; broad code eligibility still requires validation |
| Brief QA, tracing, arithmetic or expected output <128 | Direct | Tested 8–64-token answers show little benefit or regress after prefill |
| Chinese explanatory prose | Direct | Both tested models slow down with MTP |
| Other prose or unknown task/length | Direct initially | Unmeasured families require promotion through a paired pilot |
| Explicit requirement to reproduce direct greedy output | Direct | Numerical identity is not established for MTP |
| Multiple active requests or context outside the calibrated range | Direct initially | Single-slot results do not calibrate contention or long contexts |

128/256-token boundaries are starting candidates, not measured break-even
points. The 128–255 gap remains direct initially. A user override can explore
unpromoted tasks, but does not label them validated or guarantee correctness.
Do not generalize from one successful Unicode task to all programming tasks.
Do not disable MTP solely because an unrelated direct/MTP pair shared a
quality failure; eligibility needs positive evidence for the intended family.

## Layer 2: measure and fall back during generation

Initial controller: MTP can fall back once per request; it does not re-enable
mid-answer. Reset the policy state at the next request.

1. Account for each complete speculative cycle, including draft generation,
   checkpoint work, target verification, rollback/replay, sampling and commit.
   Count committed output tokens, including the target token, rather than all
   proposed draft tokens. Pending replay costs stay attached to their cycle.
2. Evaluate after at least 12 completed cycles and 32 committed tokens. These
   are candidate windows to tune; avoid conclusions from one draft.
3. Compute `mtp_ms_per_committed_token = total_cycle_ms / committed_tokens`.
   Compare with a direct-decode calibration for the same model, source/library
   hashes, thread/batch settings, GEMM route, context-length band and load.
   Acceptance percentage alone is diagnostic, not the decision criterion.
4. Tentatively request fallback if MTP costs more than 105% of direct for two
   consecutive windows. If no matching calibration exists, `auto` remains
   direct. Calibration should be recent enough to detect load/thermal drift;
   unexplained or noisy comparisons should not promote a new workload.
5. Preserve all verified output and continue direct decoding in the same slot.
   Include the probe's overhead in the end-to-end result. The probe does not
   promise zero slowdown for a new workload.

The 5% margin and window sizes must pass the test below before deployment.
Keep draft length fixed at 3 initially. Changing 3->1->0 adds another tuning
dimension; it is a subsequent experiment, not necessary for the first policy.

### State transition requirements

Separate `may_start_new_draft()` from verification of an existing draft.
A policy/load change must never cause an already scheduled draft to bypass
target verification. Mark fallback pending, finish target restore/replay and
commit accepted tokens, then disable drafting at a clean cycle boundary.

Require empty pending draft/index buffers and consistent committed prompt,
sampler, checkpoint and recurrent state. Do not discard partial replay,
restart the answer, or clear live KV state. The next request must reset the
controller and initialize its MTP state correctly after a direct-only request.

A draft-disabled MTP process may still maintain draft state. Measure that
overhead before optimizing away processing hooks: skipping them requires a
separate state/catch-up design. Do not run two resident model servers merely
to choose between modes without first evaluating their memory/cache costs.

## Telemetry

Save requested and effective mode, eligibility reason, model/build/runtime
identity, prompt/output token counts, committed tokens per window, proposed
and accepted drafts, complete cycle milliseconds, direct calibration identity,
fallback position/reason, finish reason, TTFT, total latency and peak RSS.
Record policy decisions at boundaries; final acceptance counters alone do not
prove that switching worked. Cloud judging remains offline, outside inference.

## Implementation and test sequence

1. Add request parsing and slot policy state, plus decision logs; leave defaults
   unchanged. Keep the target verification loop independent of eligibility.
2. Add complete-cycle accounting and one-way fallback. Do not alter kernels,
   enable RS, remove input sections, or shorten required answers.
3. First verify forced fallback after a rejected draft/checkpoint replay,
   natural EOS, output-limit termination, and alternating MTP/off requests in
   the same slot. Check state cleanup, full prompt processing and completion.
   Token/logit differences remain diagnostics; new correctness failures fail.
4. Compare three runtime arms: standalone direct, MTP-loaded with drafts off,
   and adaptive. Retain always-on MTP results as the reference, repeating a
   matched control where hardware/configuration differs. This reveals draft
   maintenance overhead separately from selection benefit.
5. Use a held-out successful code task and Chinese prose plus a concise QA
   sentinel; repeat at least three alternating pairs on both models, with
   naturally complete outputs. Fix budgets before dispatch; use the staged
   screen to avoid immediately repeating the entire 24-request matrix.
6. Predeclare qualification: code latency reduction >3%, prose/brief-QA
   median regression <=3%, complete coverage, no new functional/fact failures,
   and the existing relative judge thresholds. Report each pair and probe
   overhead; three repeats are still limited evidence. If the initial screen
   fails, revise or stop before a larger quality/context campaign.
7. Only then expand eligibility to additional code/prose tasks, longer
   prompts, prefix reuse and concurrency. Run the accepted production GEMM
   route combination as a separate matched check before using its calibration.

## Adoption decision

The first implementation should be an opt-in infrastructure experiment.
The current measurements justify testing a selective policy; they do not
establish the 128/256 cutoffs, timing thresholds, state transitions, or a
universal rule that code benefits and prose does not. The full-text input and
answer-quality requirements remain unchanged.
