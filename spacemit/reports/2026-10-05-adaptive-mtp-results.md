# Adaptive MTP infrastructure results

Run: `adaptive-mtp-infra-20261005-153716`, SpaceMiT K1, 2B/4B Q4_0, F16 KV,
four threads, full inputs, RS disabled. Both state gates and all 54 timing
requests completed in 16,259.70 seconds (4 h 30 min 59.7 s). Collection
verified 47 artifacts. Three repeats per task, model, and arm.

## Infrastructure measurements

| Model | Direct code tok/s | Loaded-off tok/s | Adaptive tok/s | Median paired throughput gain | Median paired wall-time reduction |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2B | 3.608 | 3.426 | 5.422 | 50.74% | 32.43% |
| 4B | 1.415 | 1.367 | 2.165 | 53.35% | 37.22% |

The rates are per-arm medians. The percentage columns are medians of the
individual paired changes, not ratios of medians. 2B code emits 1,024 tokens in
every arm, and it is capped. 4B code stops naturally, with 767 direct and
loaded-off tokens, and 717 adaptive tokens. Its wall-time reduction reflects
also the shorter answer. These results are workload-specific infrastructure
results, not useful-answer gains.

The adaptive prose and QA median paired wall time increases by 5.77% and 4.76%
on 2B, and by 2.97% and 3.62% on 4B. Drafting is disabled for these tasks, yet
the loaded context cost remains. The loaded-off controls also regress. No
measured-cost fallback triggers during the timing. The forced and synthetic-cost
state diagnostics pass.

## Quality and decision

2B code is incomplete in all three arms. 4B code completes, but it fails span
reconstruction in all three arms. Capped answers are excluded from cloud
grading. 2B has six eligible judged pairs, and it cannot clear the nine-pair
coverage gate. 4B has nine judged pairs, and it clears the relative quality
gate: mean scores 5.00 direct and 4.89 adaptive, with a worst pair loss of
0.5. Absolute correctness fails, regardless of these high judge marks. Both
models fail the overall timing gate and the absolute-usefulness gate.
**Candidate qualification is false; the defaults stay unchanged.**

Cloud grading initially failed on invalid and truncated JSON. The recovery
increases only the judge response budget, from 4,096 to 8,192 tokens. It
records the script and module hashes, and it preserves the frozen rubric, the
validators, the generations, and the gates. The recovery completed with
collector exit 2 (a completed review, not an infrastructure failure). We
paused the scheduled follow-up after the completion.

Evidence:
[final summary](raw/adaptive-mtp-infra-20261005-153716/adaptive-quality-summary.json),
[47-artifact receipt](raw/adaptive-mtp-infra-20261005-153716/collection-receipt.json),
[grading recovery](raw/adaptive-mtp-infra-20261005-153716/adaptive-scoring-recovery.json),
[protocol and preceding failure diagnosis](../experiments/2026-10-05-adaptive-mtp-infrastructure.md).

Next: compare the original and the optimized direct runtime on identical
forced prefixes. Test direct-only against MTP worker routing, with memory and
cache controls. Then evaluate the correct-answer latency on a predefined
executable task set, and retain the failed task in that set. This report
dispatches no further board run.
