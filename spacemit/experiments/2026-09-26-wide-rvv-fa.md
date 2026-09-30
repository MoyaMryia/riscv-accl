# Opt-in RVV tiled attention for Qwen3.5 256-dimensional heads

> Dated campaign snapshot. Measurements apply to the stated workload and date.
> Queued/running statements below are historical; use the
> [current guide](../DOCS.md) and the [experiments index](README.md) for later results and current status.

The integrated SpaceMiT CPU backend dispatches its RVV flash-attention kernels only when K and V head dimensions are at most 128. Both measured Qwen3.5 GGUFs declare K and V head dimensions of 256. The measured F16 KV path therefore reaches the generic CPU implementation. The server logs show a 4B 32-token prefill batch taking 3.73 s near context 256 and 21.32 s near 8k; this motivated an isolated attention experiment.

[The candidate patch](2026-09-26-wide-rvv-fa.patch) adds `SPINE_FA_WIDE_TILE=1`. It sends only 256/256 F16 K/V batches with at least 16 query tokens to the existing RVV **tiled** implementation. Single-token and short-tail decoding keep the generic path. The 256-wide one-chunk RVV implementation is deliberately excluded: it contains vector loads with a 128-lane maximum and has not been adapted for 256 elements. The tiled helpers loop across the dimension, and the patch extends only their shape assertion. The wide path uses its per-thread work buffer instead of the shared TCM pointer, avoiding any dependence on TCM capacity or sharing semantics. It also allocates the cache-line padding already used by each tiled worker in both CPU work-size calculations.

## Outcome: superseded

The original off/on/on/off tests completed at 128 and 2,048 tokens for both
models with identical complete token hashes per prompt length. Mean 2k TTFT
was about 0.2% lower for 2B and 0.1% higher for 4B. Neither enabled log
contained the activation marker, so those small changes cannot be credited
to the wide attention kernel. The original patch passed an application check
against `a990751`; board compilation and execution alone did not prove dispatch.

The first wide-head dispatcher required 128-byte vectors and did not activate
on this board, which has 32-byte vectors. The nearly identical off/on timings
therefore do not measure an accelerated path. Use the corrected
[256-bit experiment](2026-09-26-wide-rvv-vlen256.md) or packaged patch 0009.
The original patch is retained to explain the failed first experiment; it is
not the current deployment patch.
