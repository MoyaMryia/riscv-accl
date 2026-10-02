# Remaining inference optimization opportunities

Follow-up: the [compact K1 layout experiment](../experiments/2026-09-30-k1-attention-layout.md)
implements candidates 1 and 3 behind an opt-in flag. The original pilot and subsequent fast screen completed. Correctness passed;
model gains were below the fast screen threshold, so the compact layout remains
experimental. The [October 2 profile](2026-10-02-prefill-profile.md) investigates
remaining cold-prefill costs. The read-only audit below
describes the source state before that experiment. See the
[current guide](../DOCS.md) for status and the
[faster test design](../experiments/2026-09-30-fast-test-design.md) for the implemented developer loop.

Date: 2026-09-30, Asia/Singapore. Read-only source investigation of
`musepipro-wg:~/Projects/spacemit-llama-integrated` at `a990751`, including
its three existing modified CPU files. No inference implementation was
changed and no new performance experiment was run. The active quality
benchmark continues with its original code.

## What is already working

The current build uses GCC 14, `-O3`, RVV/F16 extensions, and the IME1
backend. The server log reports real TCM and the preferred four-core mask
`f`. The existing wide RVV attention dispatch is enabled for 256-dimensional
F16 heads. During inspection, the performance governor, current frequency,
and frequency limit were all consistent with 1.6 GHz; temperatures were
44-45 degrees C. This snapshot gives no obvious clock-frequency explanation
for the long prefill.

The first forced-cold routes request in each quality configuration took
211.17 s (2B/4k), 474.339 s (2B/8k), 553.112 s (4B/4k), and 1,275.152 s
(4B/8k). These are individual observed requests, including chat overhead,
not new repeated performance comparisons. The grouped benchmark schedule
reduces the number of document passes. Each remaining cold pass still needs
inference optimization.

## Prioritized code candidates

| Priority | Candidate | Source evidence | First useful test |
| --- | --- | --- | --- |
| 1 | Remove redundant attention scratch writes | `ggml/src/ggml-cpu/spacemit/rvv_kernels.cpp:1445,1466-1467` clears full output and K/V scratch, including buffers overwritten by the F16 path | Isolated opt-in change; operator comparison plus same-binary 2k/8k cold requests on both models |
| 2 | Use the existing fused RVV recurrent step during eligible prefill | `ggml/src/ggml-cpu/ops.cpp:10899` restricts the fused routine to `n_tokens == 1`; multi-token input uses separate scale/dot/update/dot sweeps | Compare scalar-gate, K=1 multi-token state and outputs, then full-model timing |
| 3 | Reduce the attention working set for 32-token microbatches | `ggml/src/ggml-cpu/common.h:9-10` defines Q=64/KV=64; scratch is about 288 KiB per worker | Profile cache behavior, then specialize active-row storage without increasing the server microbatch |
| 4 | Tune the QK vector grouping for VLEN=256 | `rvv_kernels.cpp:472-539` uses e16m1/F32m2, processing a 64-key tile in four 16-key segments | Compare an e16m2/F32m4 specialization; check compiler spills and full-model time |
| 5 | Reduce repeated K/V packing across query heads | `rvv_kernels.cpp:1439,1496,1570` maps query heads to shared KV heads but repacks K and copies V inside each query-head tile | First measure packing cost; test stride-aware V loads before shared tile caching |

These are source-based hypotheses. No new speedup percentage is established.

### 1. Attention scratch writes: the smallest first change

For DK=DV=256 and KV=64, the two `rvv_zero_f32` calls clear **128 KiB per
KV tile**. At an 8k history, 128 tiles imply about 16 MiB of scratch zero
writes per query-head/query-tile scan, before accounting for masks and
skipped tiles. This is a byte-count calculation, not measured memory traffic.

The F16 K transpose writes the valid key entries, and the F16 QK helpers
read only `kv_tile` entries. Full-tile K clearing appears redundant.
The F16 V copy also overwrites all full-tile entries. Additionally, all-mask
tiles are detected only after both scratch clears, so moving the clears
after that check can avoid writes for tiles that will be skipped.

**Partial-tile constraint:** the V accumulation calls currently receive
`KV_TILE_SZ` (64), even when `kv_tile` is smaller. Padded probabilities are
zero, but uninitialized V entries could contain NaNs; zero times NaN is
still NaN. Retain initialization of padded V entries or separately validate
a change to the accumulation bound. The F32 fallback also needs its own
padding audit. Do not remove both clears unconditionally.

The output accumulation buffer is cleared for `Q_TILE_SZ * DV`, although
`tile_rows` is at most 32 in the current microbatch. Clearing only its valid
rows is another localized candidate. Test partial query/head/thread chunks,
not just a full 32-token request.

### 2. Recurrent prefill: an existing optimization has a narrow dispatch

`ggml_gdn_decode_step_rvv` already combines gate scaling with the key dot,
and the state update with the query dot. In the generic branch, these are
four separate state sweeps. The fused routine is called inside the token
loop, but the dispatch requires scalar gates, K=1, and a single-token input.

`src/models/delta-net-base.cpp:458-459` routes multi-token input to the fused
GDN op when `fused_gdn_ch` is enabled. The context initially enables that
flag and resolves backend support. Thus there is a plausible route to
reuse the existing per-token RVV step for multi-token prefill, without a
new approximate chunked-attention algorithm.

The first experiment should preserve scalar-gate and K=1 restrictions,
process tokens in their original sequence, and compare both attention
outputs and final recurrent state. K>1 rollback snapshots and vector gates
need their original path. The existing in-place state write-back graph
optimization is also explicitly single-token; expanding that is a separate,
larger change. The rejected register-resident GDN variant in the earlier
report should not be revived merely because this dispatch looks promising.

### 3. Working set and vector grouping

The tiled scratch formula reserves roughly 288 KiB per worker for the
256-dimensional head. Four workers reserve about 1.125 MiB. The board's
sysfs reports 32 KiB private data L1 caches and **512 KiB L2 shared by cores
0-3**. Reservation alone does not prove that all these bytes are hot or
that cache misses dominate; it is a reason to measure active traffic.

The Q=64 allocation was inherited from the wider-vector implementation.
A Q=32 specialization, compact F16 scratch, and valid-row clearing could
reduce traffic without changing `-ub 32`. Every scratch-size calculation
must remain consistent in `ime.cpp`, `ggml-cpu.c`, and the kernel. Changing
the global tile macros alone would affect other dispatch paths.

The current QK helpers walk four 16-key vector segments per 64-key tile.
An e16m2 variant would walk two 32-key segments, but instructions span more
physical vector work and use larger register groups. This is not a claim
of twice the speed; spills or lower scheduling efficiency can erase any
loop-overhead reduction. Preserve the accumulation order for each output
cell and test numerical behavior.

### 4. Repeated packing: larger change after profiling

Grouped query heads map to the same KV head through `ik2 = iq2 / rk2` and
`iv2 = iq2 / rv2`, yet each query-head tile repeats the K transpose and V
copy. A stride-aware V helper might remove one copy. Reusing packed K/V
between query heads requires a deliberate layout and thread ownership;
full-history packed copies can add substantial memory. A bounded tile
design should be evaluated before allocating another packed 8k/16k cache.

## Experiments to avoid repeating without new evidence

- Increasing microbatch size blindly: the earlier M>=64 GEMM scheduling
  cliff made pp128 slower; ubatch 32 versus 48 was nearly neutral or worse.
  A different attention tile is a separate experiment from a larger GEMM batch.
- Increasing thread count blindly: earlier 4/6/8-thread results gave little
  benefit, and the preferred IME group consists of cores 0-3.
- Replacing the already vectorized softmax exponential with another fast
  approximation: `rvv_expf_approx_f32m2` is already used by this attention
  path. Any further approximation needs evidence of both cost and quality.
- Q8 weights, Q4 KV, GPU offload, page gathering, and MTP as a universal
  fix: their measured limitations remain in the existing reports. In
  particular, quantized KV misses the current F16 attention dispatch and
  MTP does not shorten the first full-document prefill.

## Recommended next measurement

After the current benchmark finishes, profile one short cold request per
model to separate FLASH_ATTN_EXT, GATED_DELTA_NET, IME matmul, packing, and
checkpoint costs. `perf` is installed, with `perf_event_paranoid=2`; user-mode
event availability still needs checking. If counters are unavailable, use
opt-in timing around the relevant operators in an isolated build. Sampling
the active comparison would change its measurement conditions.

Start with attention scratch clearing, then eligible recurrent prefill
fusion. Compare each independently, retaining Q4_0 weights, F16 KV, four
threads, batch/microbatch 32, exact inputs, and the same server configuration.
Use bounded 2k checks before 8k confirmation and alternating baseline/candidate
order. Kernel correctness checks should include partial tile lengths,
all-masked tiles, final recurrent state, and target logits. Full-answer
quality checks supplement those checks when greedy outputs diverge.

The larger application opportunity for unique documents remains exact-span
retrieval: `serve/cached-document-chat.py` currently sends the full document
for every question. Retrieval changes the input and requires a separate
fact/citation quality comparison; it is not covered by the kernel candidates.

## Provenance

Source paths and SHA-256 hashes, build settings, and the CPU cache snapshot
are recorded in [the audit manifest](raw/2026-09-30-code-audit/source-manifest.json).
The temporary source copies are in `/tmp/riscv-accl-code-audit-20260930`.
Existing measurement context: [long-prefill research](2026-09-28-long-prefill-research.md),
[local scaling analysis](2026-09-28-local-verification.md), and
[original configuration findings](2026-09-21-final.md).
