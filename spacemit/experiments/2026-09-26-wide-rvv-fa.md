# Opt-in RVV tiled attention for Qwen3.5 256-dimensional heads

The integrated SpaceMiT CPU backend dispatches its RVV flash-attention kernels only when K and V head dimensions are at most 128. Both measured Qwen3.5 GGUFs declare K and V head dimensions of 256. The measured F16 KV path therefore reaches the generic CPU implementation. The server logs show a 4B 32-token prefill batch taking 3.73 s near context 256 and 21.32 s near 8k; this motivated an isolated attention experiment.

[The candidate patch](2026-09-26-wide-rvv-fa.patch) adds `SPINE_FA_WIDE_TILE=1`. It sends only 256/256 F16 K/V batches with at least 16 query tokens to the existing RVV **tiled** implementation. Single-token and short-tail decoding keep the generic path. The 256-wide one-chunk RVV implementation is deliberately excluded: it contains vector loads with a 128-lane maximum and has not been adapted for 256 elements. The tiled helpers loop across the dimension, and the patch extends only their shape assertion. The wide path uses its per-thread work buffer instead of the shared TCM pointer, avoiding any dependence on TCM capacity or sharing semantics. It also allocates the cache-line padding already used by each tiled worker in both CPU work-size calculations.

This is a candidate, not an adopted optimization. The available local RISC-V GCC 11 lacks `riscv_vector.h`, and local Clang 14 rejects the required `zvfh` extension, so a compatible off-board RVV compile is unavailable. `git apply --check` passed against the exact board checkout at `a990751`. The isolated board worktree build and an off/on/on/off comparison are queued after the lifecycle campaign. Each arm uses the same patched binary, Q4_0 model, F16 KV, 32-token decode, and 128/2048-token prompts on both 2B and 4B. The gate is a completed run without crash, exact greedy token hashes matching off/on, and a reproducible TTFT/prompt-throughput gain. If those gates pass, test an 8k prompt before selecting it for deployment. An environment-off result remains the control.

A follow-up 8k off/on/on/off run is queued after the current board campaign. The [selection tool](../bench/select-wide-fa-long.py) requires all four 128/2048 arms per model to finish at the 32-token limit and return identical token hashes. Each passing model is tested at 8,192 tokens with a 16,384-token cache using the same patched binary and environment toggle. The selector does not require a short-context speed gain, since the long-context attention cost may change the tradeoff.

## Short-context gate result

The board off/on/on/off tests completed at 128 and 2,048 tokens for both 2B
and 4B, with complete identical token hashes per prompt length. Two-pass
mean TTFT changes were small: about 0.2% faster for 2B at 2k and 0.1%
slower for 4B at 2k. Neither enabled server log contained the candidate's
`SPINE_FA_WIDE_TILE` activation marker, although the patched source and
SpaceMiT backend were present. Thus these measurements do not prove the
wide tiled kernel ran. The 8k selection gate now requires the marker in
both enabled arms. Until activation is diagnosed, this candidate cannot be
credited with a prefill gain or selected as an optimization.
