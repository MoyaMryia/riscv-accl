# Adaptive MTP infrastructure screen

Run: `adaptive-mtp-infra-20261005-153716` on `musepipro-wg`.
Status: completed. Both state gates and 54 timing requests passed; 47 artifacts
verified. Code throughput improves 50.74%/53.35% on 2B/4B, but quality and
overall timing gates fail. Cloud grading recovery completed. See the
[final results](../reports/2026-10-05-adaptive-mtp-results.md).

## Diagnosis of the preceding run

`adaptive-mtp-20261005-070233` ended in 2,715.26 seconds. Both models passed
native state checks; neither advanced to timing. Collection recovered 26
verified artifacts after the workstation collector stopped.

The 2B standalone direct calibration repeats `validate_char` definitions 22
times, never defines `expand_spans`, and reaches 3,072 tokens. Its user input
contains one specification. Temperature is zero, seed 42, thinking disabled,
and the standalone server has no MTP draft context. Increasing the cap therefore
extended an existing generation loop. This establishes that adaptive switching
is not necessary for the observed repetition; it does not identify whether
model weights, greedy decoding or the underlying inference implementation
causes it. A separate controlled runtime comparison is needed for that claim.

The 4B direct answer stops naturally at 767 tokens but reconstructs a span
using `result.append(char)` rather than multiplying by `end-start`. Check 4
expects `aaa` from adjacent spans of lengths one and two; it returns `aa`.
The executable failure is retained. The checker now records the worker's
specific failure instead of reporting only exit code 1.

## Separate performance and usefulness measurements

The explicit `--infrastructure` mode retains the same full task inputs,
greedy sampler, K1 kernel/runtime settings, models and isolated server policy.
It freezes a 1,024-token code ceiling across direct calibration and every arm.
Chinese prose and full-document QA retain their prior ceilings. No retrieval,
input shortening, replacement task or post-hoc repair of generated code.

After native state checks, a baseline functional failure no longer prevents
infrastructure timing. Three repeats of direct / loaded-off / adaptive across
three tasks and two models schedule 54 timing requests. Order rotates as in
the previous protocol. Calibration cost is measured on the same capped task,
and is labelled as timing calibration, without claiming useful code.

For infrastructure timing, natural stop and exact exhaustion of the declared
output ceiling are accepted. Cold-cache, full-input, slot, token-count,
reasoning and policy telemetry requirements still apply. A shortened stream,
transport error or invalid telemetry remains a failure. Model failures are
independent and every response is journaled before applying its gates.

Reports retain finish reason, tokens, TTFT, wall time, decode throughput,
functional/factual checks and adaptive fallback telemetry for every arm.
Code timing uses median paired decode-throughput change. Wall-time differences
are reported alongside output-length differences and cannot establish a
useful-answer speedup when answers differ in length or are incomplete.

Only naturally completed, otherwise valid three-arm pairs reach the two-order
cloud quality judge. Capped answers remain quality-ineligible. Full quality
coverage, deterministic checks, absolute useful-answer checks and the prior
relative-score gates remain required for candidate qualification. The report
can contain infrastructure measurements while qualification remains false.

The screen is bounded, descriptive evidence, not a general equivalence result.
Three repetitions are not a confidence interval. RS stays off; serving defaults
and the production checkout remain unchanged.

## Dispatch and follow-up

```bash
python3 spacemit/bench/start-adaptive-mtp.py \
  --infrastructure \
  --run-dir spacemit/reports/raw/adaptive-mtp-infra-20261005-153716 \
  --reuse-build /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/adaptive-mtp-20261005-070233
```

Board inference and workstation collection/grading run in tmux. Request/overall
budgets remain one/twelve hours. Estimate roughly 3–5 hours if all timing stages
advance; actual finish depends on natural output lengths and speed.

Requested follow-up: check once at 30 minutes, once at 90 minutes, then quietly
wait for collection/grading completion and report final results. Follow-up
must recover a stopped collector if needed, without launching inference again.
