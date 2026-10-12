# Adaptive checkpoint MTP implementation and gated screen

Quality screen `adaptive-mtp-20261005-070233` completed in 45.25 minutes.
Both state gates passed. 2B repeated code until its cap, and 4B failed span
reconstruction. No timing comparison ran. Collection verified 26 artifacts
after recovery. The [new infrastructure screen](2026-10-05-adaptive-mtp-infrastructure.md)
measures performance while it retains those quality failures. This document
describes the original quality-gated protocol. It claims no adoption result.

Previous attempts are preserved:

- `adaptive-mtp-20261004-182134`: compiled all server units, but the helper
  treated a linker SONAME option as a path. The correction came before the
  subsequent runs.
- `adaptive-mtp-20261004-183900`: forced fallback occurred at token 32, but
  verbosity 3 suppressed the required checkpoint replay evidence.
- `adaptive-mtp-20261004-202501`: both models passed the native state gate
  with verbosity 5. The first 2B standalone code calibration reached its
  1,536-token limit without natural completion. The campaign stopped after
  1,099.75 seconds, before any of the 54 timing requests. Its collector
  verified 21 artifacts. This result is state evidence, not a performance or
  quality result.

The repaired runner freezes a 3,072-token code cap for calibration and for
every comparison arm. Full input, context, task specification, executable
checks, and natural-completion requirements are unchanged. The runner saves
every received response (including rejected text, request, audit, and server
log) to per-model request journals before it applies the gates. It records
model failures independently, so one model cannot suppress the experiment of
the other model. The run accepts no easier replacement task and no capped
answer as quality evidence. The build reuses identical server sources and
objects with recorded hashes, and it relinks and reruns the controller
tests.

## Candidate

The [server patch](2026-10-04-adaptive-mtp.patch) targets `a990751`.
The [generator](../bench/make-adaptive-mtp.py) checks unique source anchors.
The candidate source and the server executable/shared implementation are
isolated from the measured checkout. The build reuses the Ninja compiler and
link commands of that checkout, compiles all 13 server units, and links the
existing inference libraries. The tested CPU routing overlay remains at mode
0 in all arms, and RS is disabled. This experiment tests selection
separately from the production routing optimization.

The new optional `spine_mtp` object supports `on`, `off`, and `auto`. An
omission of the object retains the original server policy. `on` can use the
measured fallback if a direct calibration is supplied. Without a
calibration, `on` is an always-on control, subject to the existing resource
limits. `off` disables new drafts, while the loaded draft context still
maintains state.

`auto` initially selects code requests with an explicit expected length of
at least 256 and a named direct calibration that covers the actual full
prompt length. Other workload hints, unknown lengths, and missing or
out-of-range calibration stay direct. No prompt section is retrieved,
omitted, or shortened.

Example experimental request addition:

```json
{
  "spine_mtp": {
    "mode": "auto",
    "workload": "code",
    "expected_output_tokens": 512,
    "direct_ms_per_token": 280.0,
    "calibration_id": "replace-with-matched-calibration-id",
    "calibrated_prompt_max": 200
  }
}
```

The numeric values above are illustrative. The benchmark measures a fresh
standalone direct response per task and model, and it supplies the measured
cost, the actual prompt count, and the calibration identity. Calibration
metadata is trusted client input in this prototype. A production service
must bind that metadata to verified model, build, and runtime profiles. It
must not accept arbitrary client baselines.

## Fallback and state boundaries

- Each cycle timer starts before draft and checkpoint work, and it persists
  across partial-acceptance checkpoint restores and replay. It ends after
  the commit of the verified tokens. EOS and output limits count only the
  tokens that the server actually emitted.
- After at least 12 completed cycles and 32 committed tokens, compare cycle
  milliseconds per committed token with the direct calibration. Two
  consecutive windows that cost more than 105% of direct switch drafting off
  for the rest of that request. These values remain unqualified tuning
  values.
- A nonempty scheduled draft or replay always goes through target
  verification, even if request eligibility or load would now forbid a new
  draft. The policy changes at a completed cycle boundary. The server does
  not restart an answer and does not clear live KV state.
- A slot reset clears pending draft, index, and checkpoint buffers
  unconditionally, and it resets the policy counters. The next request can
  select another mode.
- `timings.spine_mtp` and `MTP_POLICY` logs record eligibility, complete
  cycles, window cost, and fallback position and reason. The build rejects a
  forced-boundary hook unless `SPINE_MTP_TEST_HOOKS=1`. Enable that flag only
  for state diagnostics.

A stop of the drafts does not remove draft-maintenance and embedding costs,
and it does not release the context memory. The loaded-but-off control is
necessary to measure those costs. That overhead can prevent qualification,
even when the selection itself is correct.

## Verification and stages

Local controller tests pass: eligibility and calibration boundaries, replay
timer retention, two-window fallback, forced boundaries, and reset. The
held-out Unicode-offset checker accepts the reference implementation, and it
rejects a gap/overlap bug. These tests do not substitute for native server
state tests.

1. Build the isolated candidate, and run the same C++ controller checks on
   K1.
2. On both models, reject malformed policy inputs. Test off and on literal
   answers, a forced switch after a real checkpoint replay, a measured-cost
   switch that uses a clearly synthetic state-test baseline, off after
   fallback, cached on after off, natural EOS, output-limit termination, and
   missing-calibration auto. Diagnostic capped answers are state evidence
   only. They are never quality evidence.
3. Measure standalone direct calibration for a held-out Unicode-span code
   task, Chinese policy prose, and a brief question over the same full ~2k
   document. Skip the longer timing stage for a model if its held-out direct
   code fails the executable tests. Preserve that failure. Do not substitute
   an easier task after you see the results.
4. Otherwise run three repeats of three arms, with rotating order: standalone
   direct, MTP loaded with drafts off, and adaptive MTP. This schedule gives
   **54 timing requests**, plus six calibration requests and state
   diagnostics. All timing responses must stop naturally, with valid
   cold-cache, input, and output telemetry. The runner times the whole
   request, including prefill and probe overhead.
5. Collect and verify artifact hashes. Rerun the functional checks locally,
   and use the existing blind cloud judge in both answer orders for the
   adaptive/direct pairs. The key `~/.secret_ai_key` stays on the
   workstation. The runner sends only public/synthetic evidence and
   generated answers. Grading is outside inference.

Predeclared per-model qualification: complete nine-pair coverage; median
paired code time reduction >3%; median prose and brief-QA regressions <=3%;
no new fact, citation, or functional failure in either candidate arm; all
adaptive code and fact checks passed; and the existing mean and worst-pair
relative judge loss limits of 0.25 and 0.5. These pilot gates do not
establish statistical or universal equivalence.

## Commands and artifacts

```bash
g++ -std=c++17 spacemit/bench/test-spine-mtp-policy.cpp -o /tmp/test-mtp-policy
/tmp/test-mtp-policy
python3 spacemit/bench/test-adaptive-mtp-checks.py
python3 spacemit/bench/test-adaptive-mtp-runner.py
python3 spacemit/bench/start-adaptive-mtp.py --run-dir spacemit/reports/raw/adaptive-mtp-NEW-ID
```

Use a new directory name for a new run. The launcher prepares the patch and
the build for a fresh directory. It offloads the build and the test to board
tmux, and collection and cloud scoring to workstation tmux. Collection-only
recovery:

```bash
python3 spacemit/bench/start-adaptive-mtp.py --collect-only \
  --run-dir spacemit/reports/raw/adaptive-mtp-20261005-070233
```

Allow approximately 6–10 hours if all gates advance and the code outputs are
long. This duration is an estimate, not a measured runtime for the revised
campaign. Shorter natural answers or gate failures can finish sooner. Each
request has a one-hour budget. The test driver has a twelve-hour budget
after it acquires the shared lock, including build waiting and model hash
verification. The collector waits up to 24 hours. A request timeout fails
that model. An overall stop ends the campaign. Do not interpret a queued run
as a measured gain.

Read `phase`, `build.log`, `driver.log`, `summary.json`, the per-model
state/calibration/response records, and the `MODEL-requests.jsonl` rejection
journals. Then read `adaptive-quality-summary.json`. The
`collector-exit-status` value 0 means that both models qualify, 2 means that
a completed review is necessary, and 1 means that collection or grading
failed. Generation has its own `exit-status`, and the build has
`build-exit-status`. No serving default and no production checkout changes.
