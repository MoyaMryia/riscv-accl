# Document cache quality benchmark

Constructed public documentation corpus, a small fact-question set, one cloud judge; descriptive pilot only.

Completed answers require finish_reason=stop and no reasoning text. Only completed pairs with verified same-slot cache reuse are judged.

| Configuration | Complete / recorded | Judged | Cold TTFT | Cached TTFT | Cold / cached score | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2B-2048 | 1 / 1 | 1 | 101.49 s | 3.45 s | 4.00 / 4.00 | PILOT PASS |

| Question | Position | Cold / cached finish | Cold / cached score | Eligible |
| --- | --- | --- | ---: | --- |
| 2B-2048-cache | middle | stop / stop | 4.00 / 4.00 | True |

Pilot gate: all requested pairs complete and judged; no required-fact or citation regression; cached mean no more than 0.5 points below cold; each cached score at least 3/5. Fact matching checks required terms and does not establish correctness by itself.
