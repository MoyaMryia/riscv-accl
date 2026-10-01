# Document cache quality benchmark

Constructed public documentation corpus, a small fact-question set, one cloud judge; descriptive pilot only.

Completed answers require finish_reason=stop and no reasoning text. Only completed pairs with verified same-slot cache reuse are judged.

Grouped runs measure all cached answers before cold controls; time/order effects are not counterbalanced. Alternating runs use per-question primers and alternate arm order.

| Configuration | Complete / recorded | Judged | Cold TTFT | Cached TTFT | Cold / cached score | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2B-4096 | 6 / 6 | 6 | 211.11 s | 3.90 s | 4.50 / 4.50 | REVIEW REQUIRED |
| 2B-8192 | 6 / 6 | 6 | 474.31 s | 5.01 s | 4.83 / 4.83 | PILOT PASS |
| 4B-4096 | 6 / 6 | 6 | 551.91 s | 10.80 s | 4.83 / 4.83 | PILOT PASS |
| 4B-8192 | 6 / 6 | 6 | 1271.37 s | 14.65 s | 4.83 / 5.00 | PILOT PASS |

| Question | Position | Cold / cached finish | Cold / cached score | Eligible |
| --- | --- | --- | ---: | --- |
| 2B-4096-routes | beginning | stop / stop | 5.00 / 5.00 | True |
| 2B-4096-batches | beginning | stop / stop | 5.00 / 5.00 | True |
| 2B-4096-cache | middle | stop / stop | 2.00 / 2.00 | True |
| 2B-4096-slot | middle | stop / stop | 5.00 / 5.00 | True |
| 2B-4096-health | end | stop / stop | 5.00 / 5.00 | True |
| 2B-4096-tokenize | end | stop / stop | 5.00 / 5.00 | True |
| 2B-8192-routes | beginning | stop / stop | 5.00 / 5.00 | True |
| 2B-8192-batches | beginning | stop / stop | 5.00 / 5.00 | True |
| 2B-8192-cache | middle | stop / stop | 5.00 / 5.00 | True |
| 2B-8192-slot | middle | stop / stop | 5.00 / 5.00 | True |
| 2B-8192-health | end | stop / stop | 4.00 / 4.00 | True |
| 2B-8192-tokenize | end | stop / stop | 5.00 / 5.00 | True |
| 4B-4096-routes | beginning | stop / stop | 5.00 / 5.00 | True |
| 4B-4096-batches | beginning | stop / stop | 4.00 / 4.00 | True |
| 4B-4096-cache | middle | stop / stop | 5.00 / 5.00 | True |
| 4B-4096-slot | middle | stop / stop | 5.00 / 5.00 | True |
| 4B-4096-health | end | stop / stop | 5.00 / 5.00 | True |
| 4B-4096-tokenize | end | stop / stop | 5.00 / 5.00 | True |
| 4B-8192-routes | beginning | stop / stop | 5.00 / 5.00 | True |
| 4B-8192-batches | beginning | stop / stop | 4.00 / 5.00 | True |
| 4B-8192-cache | middle | stop / stop | 5.00 / 5.00 | True |
| 4B-8192-slot | middle | stop / stop | 5.00 / 5.00 | True |
| 4B-8192-health | end | stop / stop | 5.00 / 5.00 | True |
| 4B-8192-tokenize | end | stop / stop | 5.00 / 5.00 | True |

Pilot gate: all requested pairs complete and judged; no required-fact or citation regression; cached mean no more than 0.5 points below cold; each cached score at least 3/5. Fact matching checks required terms and does not establish correctness by itself.

