# Adaptive checkpoint MTP implementation and gated screen

Quality screen `adaptive-mtp-20261005-070233` completed in 45.25 minutes: both
state gates passed, 2B repeated code until its cap, and 4B failed span
reconstruction. No timing comparisons ran; 26 artifacts were verified after
collector recovery. The [new infrastructure screen](2026-10-05-adaptive-mtp-infrastructure.md)
measures performance while retaining those quality failures. This document
describes the original quality-gated protocol; no adoption result is claimed.

Previous attempts are preserved:

- `adaptive-mtp-20261004-182134`: compiled all server units but the helper
  treated a linker SONAME option as a path; corrected before subsequent runs.
- `adaptive-mtp-20261004-183900`: forced fallback occurred at token 32, but
  verbosity 3 suppressed the required checkpoint replay evidence.
- `adaptive-mtp-20261004-202501`: both models passed the native state gate
  with verbosity 5. The first 2B standalone code calibration reached its
  1,536-token limit without natural completion. The campaign stopped after
  1,099.75 seconds, before any of the 54 timing requests. Its collector verified
  21 artifacts; this is state evidence, not a performance or quality result.

The repaired runner freezes a 3,072-token code cap for calibration and every
comparison arm. Full input, context, task specification, executable checks and
natural-completion requirements are unchanged. It saves every received response
(including rejected text, request, audit and server log) to per-model request
journals before applying gates. Model failures are recorded independently so
one model cannot suppress the other model's experiment. No easier replacement
task or capped answer is accepted as quality evidence. The build reuses identical
server sources/objects with recorded hashes, relinks and reruns controller tests.

## Candidate

The [server patch](2026-10-04-adaptive-mtp.patch) targets `a990751`.
The [generator](../bench/make-adaptive-mtp.py) checks unique source anchors.
The candidate source and server executable/shared implementation are isolated
from the measured checkout. The build reuses its Ninja compiler/link commands,
compiles all 13 server units, and links the existing inference libraries.
The tested CPU routing overlay remains at mode 0 in all arms; RS is disabled.
This tests selection separately from the production routing optimization.

The new optional `spine_mtp` object supports `on`, `off`, and `auto`.
Omitting the object retains the original server policy. `on` can use the
measured fallback if a direct calibration is supplied; without one it is an
always-on control subject to existing resource limits. `off` disables new
drafts, while the loaded draft context still maintains state.

`auto` initially selects code requests with an explicit expected length >=256
and a named direct calibration that covers the actual full prompt length.
Other workload hints, unknown lengths and missing/out-of-range calibration
stay direct. No prompt sections are retrieved, omitted or shortened.

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
standalone direct response per task/model and supplies its measured cost,
actual prompt count and calibration identity. Calibration metadata is trusted
client input in this prototype; a production service should bind it to verified
model/build/runtime profiles rather than accept arbitrary client baselines.

## Fallback and state boundaries

- Each cycle timer starts before draft/checkpoint work and persists across
  partial-acceptance checkpoint restores/replay. It ends after committing the
  verified tokens; EOS/output limits count only tokens actually emitted.
- After at least 12 completed cycles and 32 committed tokens, compare cycle
  milliseconds per committed token with the direct calibration. Two consecutive
  windows costing >105% of direct switch drafting off for the rest of that
  request. These remain unqualified tuning values.
- A nonempty scheduled draft/replay always goes through target verification,
  even if request eligibility or load would now forbid a new draft. The policy
  changes at a completed cycle boundary. No answer restart or live KV clearing.
- Slot reset clears pending draft/index/checkpoint buffers unconditionally and
  resets policy counters. The next request can select another mode.
- `timings.spine_mtp` and `MTP_POLICY` logs record eligibility, complete cycles,
  window cost and fallback position/reason. A forced-boundary hook is rejected
  unless `SPINE_MTP_TEST_HOOKS=1`; it is enabled only for state diagnostics.

Stopping drafts does not remove draft-maintenance/embedding costs or release
its context memory. The loaded-but-off control is necessary to measure those
costs. It may prevent qualification even when selection itself is correct.

## Verification and stages

Local controller tests pass: eligibility/calibration boundaries, replay timer
retention, two-window fallback, forced boundaries and reset. The held-out
Unicode-offset checker accepts the reference implementation and rejects a
gap/overlap bug. These do not substitute for native server state tests.

1. Build the isolated candidate and run the same C++ controller checks on K1.
2. On both models, reject malformed policy inputs; test off/on literal answers,
   a forced switch after real checkpoint replay, a measured-cost switch using
   a clearly synthetic state-test baseline, off after fallback, cached on after
   off, natural EOS, output-limit termination and missing-calibration auto.
   Diagnostic capped answers are state evidence only, never quality evidence.
3. Measure standalone direct calibration for a held-out Unicode-span code task,
   Chinese policy prose and a brief question over the same full ~2k document.
   Skip the longer timing stage for a model if its held-out direct code fails
   executable tests. Preserve the failure rather than substituting an easier
   task after seeing results.
4. Otherwise run three repeats of three arms, rotating their order:
   standalone direct, MTP loaded with drafts off, adaptive MTP. This schedules
   **54 timing requests**, plus six calibration requests and state diagnostics.
   All timing responses must stop naturally with valid cold-cache/input/output
   telemetry. The whole request is timed, including prefill and probe overhead.
5. Collect and verify artifact hashes, rerun functional checks locally, and use
   the existing blind cloud judge in both answer orders for adaptive/direct
   pairs. Key `~/.secret_ai_key` stays on the workstation. Only public/synthetic
   evidence and generated answers are sent; grading is outside inference.

Predeclared per-model qualification: complete nine-pair coverage; median paired
code time reduction >3%; median prose and brief-QA regressions <=3%; no new
fact/citation/functional failure in either candidate arm; all adaptive code/fact
checks pass; existing mean/worst-pair relative judge loss limits 0.25/0.5.
These pilot gates do not establish statistical or universal equivalence.

## Commands and artifacts

```bash
g++ -std=c++17 spacemit/bench/test-spine-mtp-policy.cpp -o /tmp/test-mtp-policy
/tmp/test-mtp-policy
python3 spacemit/bench/test-adaptive-mtp-checks.py
python3 spacemit/bench/test-adaptive-mtp-runner.py
python3 spacemit/bench/start-adaptive-mtp.py --run-dir spacemit/reports/raw/adaptive-mtp-NEW-ID
```

Use a new directory name for a new run. The launcher prepares the patch/build
for a fresh directory, offloads build and test to board tmux, and collection/
cloud scoring to workstation tmux. Collection-only recovery:

```bash
python3 spacemit/bench/start-adaptive-mtp.py --collect-only \
  --run-dir spacemit/reports/raw/adaptive-mtp-20261005-070233
```

Allow approximately 6–10 hours if all gates advance and code outputs are long;
this is an estimate, not a measured runtime for the revised campaign. Shorter
natural answers or gate failures can finish sooner. Each request has a one-hour
budget; the test driver has a twelve-hour budget after acquiring the shared
lock, including build waiting and model hash verification. The collector waits
up to 24 hours. A request timeout fails that model; an overall stop ends the
campaign. Do not interpret a queued run as a measured gain.

Read `phase`, `build.log`, `driver.log`, `summary.json`, per-model state/calibration/
response records and `MODEL-requests.jsonl` rejection journals, then `adaptive-quality-summary.json`. `collector-exit-status`
0 means both models qualify, 2 means completed review is needed, 1 means collection
or grading failed. Generation has its own `exit-status`; build has
`build-exit-status`. No serving default or production checkout is changed.
