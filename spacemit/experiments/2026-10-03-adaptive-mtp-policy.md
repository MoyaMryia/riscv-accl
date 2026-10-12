# Proposed adaptive checkpoint MTP policy

Status: original design. An isolated candidate and a gated screen are now
[implemented](2026-10-04-adaptive-mtp-implementation.md). Thresholds and
native switching still require qualification. This document implies no
inference default change. It is based on the
[complete-answer pilot](../reports/2026-10-03-mtp-usefulness-results.md)
and on a read of the tested `a990751` server on `musepipro-wg`.

## Objective

Use checkpoint MTP where it reduces complete-task latency without a quality
regression. Keep full prompts, the same model, the same weights, the same KV
types, the same sampling, and the same output requirements. Keep
`SPINE_SPEC_RS=0`. Semantic usefulness and functional correctness supplement
token hashes. Identity is not required.

## What the current implementation supports

- `tools/server/server-context.cpp::server_slot::can_speculate()` already
  gates drafting by active slot count. `SPINE_SPEC_MAX_ACTIVE` defaults
  to 1. This concurrency policy is present, but our pilot used one slot
  only.
- `SPINE_SPEC_LOWACC` optionally disables drafting for the rest of a request
  when fewer than 0.75 draft tokens per verification step are accepted over
  12 steps. This count measures accepted tokens per step. It does not
  measure an accepted/generated percentage. The prose cases average roughly
  1.6 accepted draft tokens per step, so they would not trigger that
  threshold, despite the slowdown.
- The request controls `speculative.n_max` and `speculative.type` in
  `tools/server/server-schema.cpp` are inside `#if 0`. A send of those
  fields is not an implemented request-level switching solution.
- MTP processing and target embedding extraction use the loaded speculative
  context beyond draft scheduling. Do not assume that a stop of the drafts
  recovers the cost or the memory footprint of a standalone direct server.

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

Modes: `off`, `on`, `auto`. An omission preserves the existing server
behavior. The client workflow can opt into `auto` after validation. Reject
unknown values. Do not silently accept ineffective fields. `on` requests
MTP, but it retains context and load limits and the measured fallback. A
separate bench switch can force always-on behavior for the control arm.

Application hints are preferable to keyword guesses. An output token cap is
an upper bound only. It does not establish a long answer. Keep an unknown
expected length conservative.

| Request | Initial proposal | Evidence / qualification |
| --- | --- | --- |
| Validated code task family, expected output >=256 tokens | Start MTP with draft length 3 | Unicode code passes functional tests with lower latency; broad code eligibility still requires validation |
| Brief QA, tracing, arithmetic or expected output <128 | Direct | Tested 8–64-token answers show little benefit or regress after prefill |
| Chinese explanatory prose | Direct | Both tested models slow down with MTP |
| Other prose or unknown task/length | Direct initially | Unmeasured families require promotion through a paired pilot |
| Explicit requirement to reproduce direct greedy output | Direct | Numerical identity is not established for MTP |
| Multiple active requests or context outside the calibrated range | Direct initially | Single-slot results do not calibrate contention or long contexts |

The 128 and 256 token boundaries are starting candidates. They are not
measured break-even points. The 128–255 gap stays direct initially. A user
override can explore unpromoted tasks, but it does not label them validated
and does not guarantee correctness. Do not generalize from one successful
Unicode task to all programming tasks. Do not disable MTP only because an
unrelated direct/MTP pair shared a quality failure. Eligibility needs
positive evidence for the intended family.

## Layer 2: measure and fall back during generation

Initial controller: MTP can fall back once per request. It does not re-enable
during an answer. Reset the policy state at the next request.

1. Account for each complete speculative cycle: draft generation, checkpoint
   work, target verification, rollback and replay, sampling, and commit.
   Count committed output tokens, including the target token. Do not count
   all proposed draft tokens. Keep pending replay costs attached to their
   cycle.
2. Evaluate after at least 12 completed cycles and 32 committed tokens.
   These windows are candidates to tune. Avoid a conclusion from one draft.
3. Compute `mtp_ms_per_committed_token = total_cycle_ms / committed_tokens`.
   Compare it with a direct-decode calibration for the same model, source
   and library hashes, thread and batch settings, GEMM route,
   context-length band, and load. Acceptance percentage alone is diagnostic.
   It is not the decision criterion.
4. Request fallback tentatively if MTP costs more than 105% of direct for two
   consecutive windows. If no matching calibration exists, `auto` remains
   direct. A calibration must be recent enough to detect load and thermal
   drift. Do not promote a new workload from an unexplained or noisy
   comparison.
5. Preserve all verified output, and continue direct decoding in the same
   slot. Include the overhead of the probe in the end-to-end result. The
   probe does not promise zero slowdown for a new workload.

The 5% margin and the window sizes must pass the test below before
deployment. Keep the draft length fixed at 3 initially. A change from 3 to
1 to 0 adds another tuning dimension. That change is a subsequent
experiment, and it is not necessary for the first policy.

### State transition requirements

Separate `may_start_new_draft()` from the verification of an existing
draft. A policy or load change must never cause an already scheduled draft
to bypass target verification. Mark the fallback pending. Finish the target
restore and replay, commit the accepted tokens, and then disable drafting at
a clean cycle boundary.

Require empty pending draft and index buffers, and consistent committed
prompt, sampler, checkpoint, and recurrent state. Do not discard a partial
replay, restart the answer, or clear live KV state. The next request must
reset the controller and initialize its MTP state correctly after a
direct-only request.

A draft-disabled MTP process can still maintain draft state. Measure that
overhead before you optimize away the processing hooks. A skip of those
hooks requires a separate state and catch-up design. Do not run two resident
model servers only to choose between modes, until you first evaluate their
memory and cache costs.

## Telemetry

Save the requested and effective mode, the eligibility reason, the
model/build/runtime identity, prompt and output token counts, committed
tokens per window, proposed and accepted drafts, complete cycle
milliseconds, direct calibration identity, fallback position and reason,
finish reason, TTFT, total latency, and peak RSS. Record policy decisions at
boundaries. Final acceptance counters alone do not prove that switching
worked. Cloud judging remains offline, outside inference.

## Implementation and test sequence

1. Add request parsing and slot policy state, plus decision logs. Leave the
   defaults unchanged. Keep the target verification loop independent of
   eligibility.
2. Add complete-cycle accounting and one-way fallback. Do not alter kernels,
   enable RS, remove input sections, or shorten required answers.
3. First verify forced fallback after a rejected draft and checkpoint
   replay, natural EOS, output-limit termination, and alternating MTP/off
   requests in the same slot. Check state cleanup, full prompt processing,
   and completion. Token and logit differences remain diagnostics. A new
   correctness failure fails.
4. Compare three runtime arms: standalone direct, MTP loaded with drafts
   off, and adaptive. Retain always-on MTP results as the reference, and
   repeat a matched control where hardware or configuration differs. This
   comparison reveals draft maintenance overhead separately from selection
   benefit.
5. Use a held-out successful code task, Chinese prose, and a concise QA
   sentinel. Repeat at least three alternating pairs on both models, with
   naturally complete outputs. Fix the budgets before dispatch. Use the
   staged screen, and do not immediately repeat the entire 24-request
   matrix.
6. Predeclare qualification: code latency reduction >3%, prose and brief-QA
   median regression <=3%, complete coverage, no new functional or fact
   failures, and the existing relative judge thresholds. Report each pair
   and the probe overhead. Three repeats are still limited evidence. If the
   initial screen fails, revise or stop before a larger quality and context
   campaign.
7. Only then expand eligibility to additional code and prose tasks, longer
   prompts, prefix reuse, and concurrency. Run the accepted production GEMM
   route combination as a separate matched check before you use its
   calibration.

## Adoption decision

The first implementation must be an opt-in infrastructure experiment. The
current measurements justify a test of a selective policy. They do not
establish the 128/256 cutoffs, the timing thresholds, the state transitions,
or a universal rule that code benefits and prose does not. The full-text
input and answer-quality requirements remain unchanged.
