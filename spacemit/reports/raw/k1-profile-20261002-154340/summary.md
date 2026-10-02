# K1 cold-prefill profile

Status: complete

Cold request after health/tokenization; one output token included. One diagnostic request per model; no throughput or quality claim.

| Model | Cold prompt time | Samples | Recurrent visible | Attention visible | Matmul visible | Other |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2B | 93.19 s | 92292 | 7.20% | 3.23% | 0.09% | 89.48% |
| 4B | 240.11 s | 237893 | 7.46% | 3.36% | 0.07% | 89.11% |

Sampled CPU shares are not wall-time shares. Missing frames leave work unattributed.
Attention copy samples exclude inlined K transpose and do not measure total packing cost.
Profiling can perturb timings. No optimization speedup or answer-quality claim.


