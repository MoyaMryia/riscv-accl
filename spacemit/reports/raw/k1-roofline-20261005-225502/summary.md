# K1 measured memory and direct-inference roofline

Status: complete

Capped synthetic throughput, not useful-answer quality. Streaming ratios are traffic proxies, not measured DDR utilization or removable overhead. No hardware DDR counters or verified memory clock; raw peak assumes datasheet 2666 MT/s. Three matched repetitions are an engineering screen, not a general performance guarantee.

| Model | Prompt | DDR read proxy GB/s | Weight-only roof tok/s | + one KV pass roof tok/s | Route 0 tok/s | Route 3 tok/s | Paired gain |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2B | 256 | 6.996 | 6.598 | 6.576 | 3.793 | 4.480 | 18.01% |
| 2B | 2048 | 6.996 | 6.598 | 6.442 | 3.307 | 3.832 | 15.47% |
| 4B | 256 | 6.957 | 2.937 | 2.925 | 1.480 | 2.058 | 38.70% |
| 4B | 2048 | 6.957 | 2.937 | 2.855 | 1.221 | 1.619 | 32.36% |

RAM bandwidth is the median of five scans before and five after inference on cores 0–3.
Working sets are predeclared: 1 GiB for 2B and 2.25 GiB for 4B. Source bytes only; initialization and warm-up excluded.
A streaming ratio near one suggests limited bandwidth headroom; a low ratio does not identify the bottleneck.
If inference exceeds this reference, examine access patterns and working-set assumptions; do not claim impossible hardware performance.
CPU profiles are separate optimized 2k/one-output-token diagnostics. CPU shares are not wall-time speedups.
No MTP, retrieval, KV compression, model change or production-default change.
