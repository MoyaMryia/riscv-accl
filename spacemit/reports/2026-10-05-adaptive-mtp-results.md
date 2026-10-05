# Adaptive MTP infrastructure results

Run: `adaptive-mtp-infra-20261005-153716`, SpaceMiT K1, 2B/4B Q4_0,
F16 KV, four threads, full inputs, RS disabled. Both state gates and all
54 timing requests completed in 16,259.70 seconds (4 h 30 min 59.7 s).
Collection verified 47 artifacts. Three repeats per task/model/arm.

## Infrastructure measurements

| Model | Direct code tok/s | Loaded-off tok/s | Adaptive tok/s | Median paired throughput gain | Median paired wall-time reduction |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2B | 3.608 | 3.426 | 5.422 | 50.74% | 32.43% |
| 4B | 1.415 | 1.367 | 2.165 | 53.35% | 37.22% |

Rates are per-arm medians; percentage columns are medians of the individual
paired changes, not ratios of medians. 2B code emits 1,024 tokens in every arm
and is capped. 4B code stops naturally with 767 direct/loaded-off tokens and
717 adaptive tokens; its wall-time reduction also reflects the shorter answer.
These are workload-specific infrastructure results, not useful-answer gains.

Adaptive prose/QA median paired wall time increases by 5.77%/4.76% on 2B
and 2.97%/3.62% on 4B. Drafting is disabled for these tasks, yet loaded context
cost remains. Loaded-off controls also regress. No measured-cost fallback
triggers during timing; forced and synthetic-cost state diagnostics pass.

## Quality and decision

2B code is incomplete in all three arms. 4B code completes but fails span
reconstruction in all three arms. Capped answers are excluded from cloud grading.
2B has six eligible judged pairs and cannot clear the nine-pair coverage gate.
4B has nine judged pairs and clears relative quality: mean scores 5.00 direct
and 4.89 adaptive, worst pair loss 0.5. Absolute correctness fails regardless
of these high judge marks. Both models fail the overall timing gate and
absolute-usefulness gate. **Candidate qualification is false; defaults stay unchanged.**

Cloud grading initially failed on invalid/truncated JSON. Recovery increases
only the judge response budget from 4,096 to 8,192 tokens, records script/module
hashes, and preserves the frozen rubric, validators, generations and gates.
Recovery completed with collector exit 2 (completed review, not infrastructure
failure). The scheduled follow-up was paused after completion.

Evidence: [final summary](raw/adaptive-mtp-infra-20261005-153716/adaptive-quality-summary.json),
[47-artifact receipt](raw/adaptive-mtp-infra-20261005-153716/collection-receipt.json),
[grading recovery](raw/adaptive-mtp-infra-20261005-153716/adaptive-scoring-recovery.json),
[protocol and preceding failure diagnosis](../experiments/2026-10-05-adaptive-mtp-infrastructure.md).

Next: compare original/optimized direct runtime on identical forced prefixes,
test direct-only versus MTP worker routing with memory/cache controls, then
evaluate correct-answer latency on a predefined executable task set retaining
the failed task. No further board run is dispatched by this report.
