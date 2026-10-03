# Completed staged validation: routing, answers and recurrent state

Run: `k1-validation-20261003-124720`. Completed in 4.16 hours, exit 0.
Execution completion does not mean every acceptance gate passed.
The [summary](raw/k1-validation-20261003-124720/summary.json),
[collection receipt](raw/k1-validation-20261003-124720/collection-receipt.json)
and [verification](raw/k1-validation-20261003-124720/verification.json)
retain every outcome. All 83 collected artifact hashes were verified.
Configuration and predeclared gates are in the [protocol](../experiments/2026-10-03-staged-validation.md).

## Combined routing: actual 8192 input tokens

Mode 0/3/3/0, both models, four threads, Q4_0/F16, batch/microbatch 32,
64 output tokens, uncached inputs, context shifting disabled. All eight
requests have matching input/output hashes and complete counts.

| Model | Mean control prefill | Mean mode-3 prefill | Reduction | Mean control decode | Mean mode-3 decode | Reduction |
| --- | --- | --- | --- | --- | --- | --- |
| 2B | 454.781 s | 434.656 s | 4.43% | 26.775 s | 24.233 s | 9.49% |
| 4B | 1215.184 s | 1144.865 s | 5.79% | 84.530 s | 71.803 s | 15.06% |

Both phases clear the predefined max(3%, control range) gate on both models.
These are two requests per arm, an engineering pilot. Percentages are against
the current optimized baseline and must not be added to historical RVV gains.

## Complete-document answers

All 12 requests stop naturally, send the complete ~4k fixture, and are cold.
Baseline/candidate answer text is identical for each of the six task pairs.
Both models answer routes, tracing and aggregation with the required facts.
4B also includes all required citation markers and passes the pilot.
2B omits the tracing citations in both arms, so its absolute usefulness gate
does not clear. There is no observed candidate regression, but the declared
gate is retained. Citation-marker checks are not a full attribution audit or
a cloud quality score; this pilot is not a RULER/LongBench score.

## Recurrent-state and MTP diagnostics

Each model has 43 native replay records: 18 pass, 18 mismatch and 7 unsupported.
Same-shape reference, full restore into fresh/used contexts, partial restore
with a matching attention prefix, and the supported partial dirty restore
pass their finite, bitwise-logit checks. The mismatches are RS=3 whole-batch
and repeated rollback cases, despite successful tail-removal calls. Maximum
absolute logit differences are 3.3623 (2B) and 3.0377 (4B); argmax differs in
4 and 7 records respectively. Every comparison remains finite. Unsupported
removal cases are not counted as passes. These results require investigation
of this fork's rollback behavior; they do not identify a patch or prove a
universal failure on all MTP requests. Sequence isolation remains untested.

Forced-trajectory M=1 controls exactly reproduce all 512 positions. M=3
changes top-two logits on both models; 2B has two argmax flips, first at index
208, while 4B has none. This isolates shape-dependent differences on the same
token history, independently of the rollback reproducer.

The current 512-output end-to-end checkpoint/RS MTP requests match direct
tokens and text on both models. This bounded sample does not supersede the
historical 4096-output mismatch on another recorded build/configuration or
the native rollback failures. General MTP identity remains uncleared.

## Decision

Retain routing as opt-in. Combined mode has measured 8k performance evidence,
but the overall gate remains closed because 2B tracing lacks citations.
The conditional 4B/32k stage was **skipped**, not attempted or timed out;
4B/32k and 64k remain unmeasured. Do not enable broad MTP exactness claims.
Next work is a minimal RS rollback diagnosis and a separate, predeclared
decision about the baseline citation limitation. No gates or defaults were
changed after observing these results.
