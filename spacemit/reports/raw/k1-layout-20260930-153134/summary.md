# K1 compact attention layout pilot

PASS: both layouts match baseline float outputs bit for bit

Two launches per arm at 128/2048 tokens. No long-context result or statistical significance claim.

| Model | Prompt | Query rows | TTFT seconds | Reduction | Prefill tok/s |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2B | 128 | 64 | 5.691 | 0.00% | 22.507 |
| 2B | 128 | 16 | 5.669 | 0.40% | 22.596 |
| 2B | 128 | 32 | 5.676 | 0.28% | 22.569 |
| 2B | 2048 | 64 | 95.357 | 0.00% | 21.501 |
| 2B | 2048 | 16 | 95.055 | 0.32% | 21.569 |
| 2B | 2048 | 32 | 94.513 | 0.89% | 21.693 |
| 4B | 128 | 64 | 14.634 | 0.00% | 8.750 |
| 4B | 128 | 16 | 14.504 | 0.88% | 8.828 |
| 4B | 128 | 32 | 14.445 | 1.29% | 8.863 |
| 4B | 2048 | 64 | 248.249 | 0.00% | 8.260 |
| 4B | 2048 | 16 | 248.970 | -0.29% | 8.235 |
| 4B | 2048 | 32 | 243.327 | 1.98% | 8.426 |
