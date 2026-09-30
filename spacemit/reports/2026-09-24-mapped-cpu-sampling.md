# Mapped 32k MTP head with CPU draft sampling on K1/X60

> Dated campaign snapshot. Measurements apply to the stated workload and date.
> Queued/running statements below are historical; use the
> [current guide](../DOCS.md) and the [reports index](README.md) for later results and current status.

Date: 2026-09-24. Board: MUSE-Pi-Pro, SpaceMiT K1/X60. This experiment combines the existing frequency-ranked 32k `d2t` MTP head with the existing `--no-spec-draft-backend-sampling` flag. No source or GGUF was changed. It used the separately built `~/Projects/spacemit-llama-frspec/build/bin/llama-server` and `Qwen3.5-2B-MTP-Q4_0-embQ4_0-d2t32k.gguf`, not the general official-fork server build. The mapped checkout has a local modification to `src/models/qwen35.cpp`.

## Result

Two runs per arm, with MTP arm order `backend → CPU → CPU → backend`; direct controls ran twice after those four arms. Each server was restarted. All arms used `SPINE_SPEC_RS=1`, `SPINE_SPEC_LOWACC=0`, the vendor `spine-tcm` library in `LD_LIBRARY_PATH`, `-t 4 -c 8192 --parallel 1 -b 32 -ub 32 -fa on`, MTP draft maximum 3, greedy decoding, seed 42, `cache_prompt=false`, and 128 generated tokens. Rates are **server decode** tokens/s (`timings.predicted_per_second`), not request wall throughput.

| Prompt | Direct | MTP, backend sampling | MTP, CPU sampling | CPU vs backend |
| --- | ---: | ---: | ---: | ---: |
| English: relativity | 5.118 | 6.812 | **7.004** | **+2.8%** |
| Chinese: RISC-V vector explanation | **5.115** | 4.938 | 5.075 | +2.8%, but still 0.8% below direct |

The two CPU-sampling runs were 7.001/7.008 English and 5.076/5.073 Chinese; backend runs were 6.805/6.820 and 4.931/4.945. Accepted/drafted counts were identical between sampling arms: English 83/130, Chinese 66/183. All direct and speculative responses within each prompt had the same SHA-256 output hash. The CPU flag changes draft selection cost here, not the generated greedy text.

## Interpretation

For this English prompt, the combined mapped head and CPU sampler is the fastest configuration measured in this experiment, about 37% above its same-model direct control. The Chinese prompt remains a direct-decoding case despite a clear CPU-sampler gain. This is a two-prompt, two-run result in an experimental checkout; it does not establish a universal 7 tok/s setting, a stochastic-sampling result, or a high-concurrency gain. The earlier [mapped-head report](2026-09-23-frspec.md) tested three prompts and compared head variants; the [CPU-sampling report](2026-09-24-cpu-sampling.md) used the prefix 64k head. Those older numbers should not be mixed into this same-run A/B percentage.

The [raw JSONL](raw/2026-09-24-mapped-cpu-sampling/results.jsonl) records every response rate, draft count, and hash. The established [benchmark runner](../bench/bench-server.py) was copied unchanged to the board's `/tmp` and invoked with `--prompt-set frspec --prompt english --prompt chinese --modes mtp --n-predict 128`, varying `--draft-backend-sampling on|off`. The direct controls used `--modes plain` with the same server, model, and environment.
