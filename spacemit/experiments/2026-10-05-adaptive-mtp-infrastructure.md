# Adaptive MTP infrastructure screen

Run: `adaptive-mtp-infra-20261005-153716` on `musepipro-wg`.
Status: completed. Both state gates and 54 timing requests passed, and 47
artifacts are verified. Code throughput improves 50.74%/53.35% on 2B/4B, but
the quality and overall timing gates fail. Cloud grading recovery completed.
See the [final results](../reports/2026-10-05-adaptive-mtp-results.md).

## Diagnosis of the preceding run

`adaptive-mtp-20261005-070233` ended in 2,715.26 seconds. Both models passed
the native state checks. Neither model advanced to timing. The collection
recovered 26 verified artifacts after the workstation collector stopped.

The 2B standalone direct calibration repeats `validate_char` definitions 22
times. It never defines `expand_spans`, and it reaches 3,072 tokens. Its user
input contains one specification. Temperature is zero, seed is 42, thinking
is disabled, and the standalone server has no MTP draft context. An increase
of the cap therefore extended an existing generation loop. This result
establishes that adaptive switching is not necessary for the observed
repetition. It does not identify the cause: model weights, greedy decoding,
or the inference implementation. A separate controlled runtime comparison is
necessary for that claim.

The 4B direct answer stops naturally at 767 tokens. But it reconstructs a
span with `result.append(char)` instead of a multiplication by `end-start`.
Check 4 expects `aaa` from adjacent spans of lengths one and two, and the
answer returns `aa`. We retain the executable failure. The checker now
records the specific failure of the worker instead of exit code 1 only.

## Separate performance and usefulness measurements

The explicit `--infrastructure` mode keeps the same full task inputs, greedy
sampler, K1 kernel/runtime settings, models, and isolated server policy. It
freezes a 1,024-token code ceiling across direct calibration and every arm.
Chinese prose and full-document QA keep their prior ceilings. There is no
retrieval, no input shortening, no replacement task, and no post-hoc repair
of generated code.

After the native state checks, a baseline functional failure no longer
prevents infrastructure timing. Three repeats of direct / loaded-off /
adaptive across three tasks and two models schedule 54 timing requests. The
order rotates as in the previous protocol. The runner measures calibration
cost on the same capped task, and it labels this cost as timing calibration.
It makes no claim of useful code.

For infrastructure timing, natural stop and exact exhaustion of the declared
output ceiling are both accepted. The cold-cache, full-input, slot,
token-count, reasoning, and policy telemetry requirements still apply. A
shortened stream, a transport error, or invalid telemetry remains a failure.
Model failures are independent, and the runner journals every response before
it applies the gates.

Reports retain finish reason, tokens, TTFT, wall time, decode throughput,
functional/factual checks, and adaptive fallback telemetry for every arm.
Code timing uses the median paired decode-throughput change. The runner
reports wall-time differences together with output-length differences. These
values cannot establish a useful-answer speedup when the answers differ in
length or are incomplete.

Only naturally completed, otherwise valid three-arm pairs reach the two-order
cloud quality judge. Capped answers remain quality-ineligible. Full quality
coverage, deterministic checks, absolute useful-answer checks, and the prior
relative-score gates all remain necessary for candidate qualification. A
report can contain infrastructure measurements while qualification remains
false.

This screen is bounded, descriptive evidence. It is not a general
equivalence result. Three repetitions are not a confidence interval. RS stays
off. Serving defaults and the production checkout remain unchanged.

## Dispatch and follow-up

```bash
python3 spacemit/bench/start-adaptive-mtp.py \
  --infrastructure \
  --run-dir spacemit/reports/raw/adaptive-mtp-infra-20261005-153716 \
  --reuse-build /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/adaptive-mtp-20261005-070233
```

Board inference and workstation collection/grading run in tmux. The request
and overall budgets remain one and twelve hours. Estimate roughly 3–5 hours
if all timing stages advance. The actual finish depends on natural output
lengths and speed.

Requested follow-up: check once at 30 minutes and once at 90 minutes. Then
wait quietly for collection and grading completion, and report the final
results. The follow-up must recover a stopped collector if necessary. It must
not launch inference again.
