# K1 cold-prefill profile

Status: complete

Cold request after health/tokenization; one output token included. One diagnostic request per model; no throughput or quality claim.

| Model | Cold prompt time | Samples | Recurrent visible | Attention visible | Matmul visible | Other |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2B | 19.85 s | 19569 | 11.10% | 1.09% | 0.07% | 87.73% |
| 4B | 50.43 s | 49773 | 11.57% | 1.24% | 0.04% | 87.14% |

Sampled CPU shares are not wall-time shares. Missing frames leave work unattributed.
Attention copy samples exclude inlined K transpose and do not measure total packing cost.
Profiling can perturb timings. No optimization speedup or answer-quality claim.


