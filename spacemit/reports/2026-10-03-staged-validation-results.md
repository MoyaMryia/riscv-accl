# Completed staged validation: routing, answers and recurrent state

Run: `k1-validation-20261003-124720`. It completed in 4.16 hours, with exit 0.
Execution completion does not mean that every acceptance gate passed. The
[summary](raw/k1-validation-20261003-124720/summary.json), the
[collection receipt](raw/k1-validation-20261003-124720/collection-receipt.json),
and the
[verification](raw/k1-validation-20261003-124720/verification.json) retain
every outcome. All 83 collected artifact hashes were verified. The
configuration and the predeclared gates are in the
[protocol](../experiments/2026-10-03-staged-validation.md).

## Combined routing: actual 8192 input tokens

Mode 0/3/3/0, both models, four threads, Q4_0/F16, batch/microbatch 32, 64
output tokens, uncached inputs, and context shifting disabled. All eight
requests have matching input and output hashes, and complete counts.

| Model | Mean control prefill | Mean mode-3 prefill | Reduction | Mean control decode | Mean mode-3 decode | Reduction |
| --- | --- | --- | --- | --- | --- | --- |
| 2B | 454.781 s | 434.656 s | 4.43% | 26.775 s | 24.233 s | 9.49% |
| 4B | 1215.184 s | 1144.865 s | 5.79% | 84.530 s | 71.803 s | 15.06% |

Both phases clear the predefined max(3%, control range) gate on both models.
These results are two requests per arm, an engineering pilot. The percentages
are against the current optimized baseline. Do not add them to the historical
RVV gains.

## Complete-document answers

All 12 requests stop naturally, send the complete ~4k fixture, and are cold.
The baseline and candidate answer text is identical for each of the six task
pairs. Both models answer the routes, the tracing, and the aggregation with
the required facts. 4B also includes all required citation markers, and it
passes the pilot. 2B omits the tracing citations in both arms, so its absolute
usefulness gate does not clear. There is no observed candidate regression, but
we retain the declared gate. The citation-marker checks are not a full
attribution audit and not a cloud quality score. This pilot is not a
RULER/LongBench score.

## Recurrent-state and MTP diagnostics

Each model has 43 native replay records: 18 pass, 18 mismatch, and 7 are
unsupported. The same-shape reference, the full restore into fresh and used
contexts, the partial restore with a matching attention prefix, and the
supported partial dirty restore pass their finite, bitwise-logit checks. The
mismatches are the RS=3 whole-batch and the repeated rollback cases, despite
successful tail-removal calls. The maximum absolute logit differences are
3.3623 (2B) and 3.0377 (4B). The argmax differs in 4 and 7 records. Every
comparison remains finite. We do not count the unsupported removal cases as
passes. These results require an investigation of the rollback behavior of
this fork. They do not identify a patch, and they do not prove a universal
failure on all MTP requests. Sequence isolation remains untested.

The forced-trajectory M=1 controls reproduce all 512 positions exactly. The
M=3 runs change the top-two logits on both models. 2B has two argmax flips,
the first at index 208, and 4B has none. This behavior isolates
shape-dependent differences on the same token history, independently of the
rollback reproducer.

The current 512-output end-to-end checkpoint and RS MTP requests match the
direct tokens and text on both models. This bounded sample does not supersede
the historical 4096-output mismatch on another recorded build and
configuration, and it does not supersede the native rollback failures. General
MTP identity remains uncleared.

## Decision

Retain routing as opt-in. The combined mode has measured 8k performance
evidence, but the overall gate remains closed, because the 2B tracing lacks
citations. We **skipped** the conditional 4B/32k stage. We did not attempt it,
and it did not time out. 4B/32k and 64k remain unmeasured. Do not enable
broad MTP exactness claims. The next work is a minimal RS rollback diagnosis,
and a separate predeclared decision about the baseline citation limitation. We
changed no gate and no default after we observed these results.
