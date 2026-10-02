# K1 cold-prefill profile

Status: failed

Cold request after health/tokenization; one output token included. One diagnostic request per model; no throughput or quality claim.

| Model | Cold prompt time | Samples | Recurrent visible | Attention visible | Matmul visible | Other |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |

Sampled CPU shares are not wall-time shares. Missing frames leave work unattributed.
Attention copy samples exclude inlined K transpose and do not measure total packing cost.
Profiling can perturb timings. No optimization speedup or answer-quality claim.

RuntimeError: perf control acknowledgment missing
