# Remaining inference optimization opportunities

Follow-up: the [compact K1 layout experiment](../experiments/2026-09-30-k1-attention-layout.md)
implements candidates 1 and 3 behind an opt-in flag. The original pilot and
the subsequent fast screen completed. Correctness passed, and the model gains
were below the fast screen threshold. The compact layout therefore remains
experimental. The [October 2 profile](2026-10-02-prefill-profile.md)
investigates the remaining cold-prefill costs. The read-only audit below
describes the source state before that experiment. See the
[current guide](../DOCS.md) for the status, and the
[faster test design](../experiments/2026-09-30-fast-test-design.md) for the
implemented developer loop.

Date: 2026-09-30, Asia/Singapore. This report is a read-only source
investigation of `musepipro-wg:~/Projects/spacemit-llama-integrated` at
`a990751`, including its three existing modified CPU files. We changed no
inference implementation, and we ran no new performance experiment. The
active quality benchmark continues with its original code.

## What is already working

Later runtime evidence: the
[October 2 infrastructure audit](../experiments/2026-10-02-attention-infrastructure.md)
reports the TCM API unavailable, with zero geometry and `fake=true`, while
SPERT still provides 128 KiB worker buffers. The older log description below
does not establish current physical TCM placement.

The current build uses GCC 14, `-O3`, RVV/F16 extensions, and the IME1
backend. The server log reports real TCM and the preferred four-core mask
`f`. The existing wide RVV attention dispatch is enabled for the
256-dimensional F16 heads. During the inspection, the performance governor,
the current frequency, and the frequency limit were all consistent with
1.6 GHz. Temperatures were 44–45 degrees C. This snapshot gives no obvious
clock-frequency explanation for the long prefill.

The first forced-cold route request in each quality configuration took
211.17 s (2B/4k), 474.339 s (2B/8k), 553.112 s (4B/4k), and 1,275.152 s
(4B/8k). These values are individual observed requests, and they include
chat overhead. They are not new repeated performance comparisons. The grouped
benchmark schedule reduces the number of document passes. Each remaining cold
pass still needs an inference optimization.

## Prioritized code candidates

| Priority | Candidate | Source evidence | First useful test |
| --- | --- | --- | --- |
| 1 | Remove redundant attention scratch writes | `ggml/src/ggml-cpu/spacemit/rvv_kernels.cpp:1445,1466-1467` clears the full output and K/V scratch, including buffers that the F16 path overwrites | Isolated opt-in change; operator comparison plus same-binary 2k/8k cold requests on both models |
| 2 | Use the existing fused RVV recurrent step during eligible prefill | `ggml/src/ggml-cpu/ops.cpp:10899` restricts the fused routine to `n_tokens == 1`; multi-token input uses separate scale/dot/update/dot sweeps | Compare scalar-gate, K=1 multi-token state and outputs, then full-model timing |
| 3 | Reduce the attention working set for 32-token microbatches | `ggml/src/ggml-cpu/common.h:9-10` defines Q=64/KV=64; scratch is about 288 KiB per worker | Profile cache behavior, then specialize active-row storage without an increase of the server microbatch |
| 4 | Tune the QK vector grouping for VLEN=256 | `rvv_kernels.cpp:472-539` uses e16m1/F32m2, and processes a 64-key tile in four 16-key segments | Compare an e16m2/F32m4 specialization; check compiler spills and full-model time |
| 5 | Reduce repeated K/V packing across query heads | `rvv_kernels.cpp:1439,1496,1570` maps query heads to shared KV heads, but it repacks K and copies V inside each query-head tile | First measure the packing cost; test stride-aware V loads before shared tile caching |

These items are source-based hypotheses. They establish no new speedup
percentage.

### 1. Attention scratch writes: the smallest first change

For DK=DV=256 and KV=64, the two `rvv_zero_f32` calls clear **128 KiB per KV
tile**. At an 8k history, 128 tiles imply about 16 MiB of scratch zero writes
per query-head/query-tile scan, before the code accounts for masks and skipped
tiles. This result is a byte-count calculation, not measured memory traffic.

The F16 K transpose writes the valid key entries, and the F16 QK helpers read
only `kv_tile` entries. The full-tile K clearing therefore appears redundant.
The F16 V copy also overwrites all full-tile entries. In addition, the code
detects all-mask tiles only after both scratch clears. A move of the clears
after that check can avoid the writes for tiles that the code will skip.

**Partial-tile constraint:** the V accumulation calls currently receive
`KV_TILE_SZ` (64), even when `kv_tile` is smaller. Padded probabilities are
zero, but uninitialized V entries can contain NaNs. Zero times NaN is still
NaN. Retain the initialization of the padded V entries, or separately
validate a change to the accumulation bound. The F32 fallback needs also its
own padding audit. Do not remove both clears unconditionally.

The output accumulation buffer is cleared for `Q_TILE_SZ * DV`, although
`tile_rows` is at most 32 in the current microbatch. A clear of only the
valid rows is another localized candidate. Test partial query, head, and
thread chunks, not only a full 32-token request.

### 2. Recurrent prefill: an existing optimization has a narrow dispatch

`ggml_gdn_decode_step_rvv` already combines the gate scaling with the key
dot, and the state update with the query dot. In the generic branch, these
operations are four separate state sweeps. The code calls the fused routine
inside the token loop, but the dispatch requires scalar gates, K=1, and a
single-token input.

`src/models/delta-net-base.cpp:458-459` routes multi-token input to the fused
GDN op, when `fused_gdn_ch` is enabled. The context initially enables that
flag, and it resolves backend support. A plausible route therefore exists to
reuse the existing per-token RVV step for multi-token prefill, without a new
approximate chunked-attention algorithm.

The first experiment must preserve the scalar-gate and K=1 restrictions,
process the tokens in their original sequence, and compare both the attention
outputs and the final recurrent state. K>1 rollback snapshots and vector
gates need their original path. The existing in-place state write-back graph
optimization is also explicitly single-token. An expansion of that
optimization is a separate and larger change. Do not revive the rejected
register-resident GDN variant from the earlier report, merely because this
dispatch looks promising.

### 3. Working set and vector grouping

The tiled scratch formula reserves roughly 288 KiB per worker for the
256-dimensional head. Four workers reserve about 1.125 MiB. The board sysfs
reports 32 KiB private data L1 caches, and **512 KiB L2 shared by cores
0-3**. The reservation alone does not prove that all these bytes are hot, or
that cache misses dominate. It is a reason to measure the active traffic.

The Q=64 allocation was inherited from the wider-vector implementation. A
Q=32 specialization, compact F16 scratch, and valid-row clearing could reduce
the traffic, without a change to `-ub 32`. Every scratch-size calculation
must remain consistent in `ime.cpp`, `ggml-cpu.c`, and the kernel. A change to
the global tile macros alone would affect other dispatch paths.

The current QK helpers walk four 16-key vector segments per 64-key tile. An
e16m2 variant would walk two 32-key segments. But its instructions span more
physical vector work, and they use larger register groups. This change is not
a claim of twice the speed. Spills or a lower scheduling efficiency can
erase any loop-overhead reduction. Preserve the accumulation order for each
output cell, and test the numerical behavior.

### 4. Repeated packing: larger change after profiling

Grouped query heads map to the same KV head through `ik2 = iq2 / rk2` and
`iv2 = iq2 / rv2`. Yet each query-head tile repeats the K transpose and the V
copy. A stride-aware V helper might remove one copy. A reuse of packed K and
V between query heads requires a deliberate layout and thread ownership.
Full-history packed copies can add substantial memory. Evaluate a bounded
tile design before you allocate another packed 8k/16k cache.

## Experiments to avoid repeating without new evidence

- A blind increase of the microbatch size: the earlier M>=64 GEMM scheduling
  cliff made pp128 slower, and ubatch 32 against 48 was nearly neutral or
  worse. A different attention tile is a separate experiment from a larger
  GEMM batch.
- A blind increase of the thread count: the earlier 4/6/8-thread results gave
  little benefit, and the preferred IME group consists of cores 0-3.
- A replacement of the already vectorized softmax exponential with another
  fast approximation: `rvv_expf_approx_f32m2` is in use by this attention
  path already. Any further approximation needs evidence of both its cost
  and its quality.
- Q8 weights, Q4 KV, GPU offload, page gathering, and MTP as a universal fix:
  their measured limitations remain in the existing reports. In particular,
  quantized KV misses the current F16 attention dispatch, and MTP does not
  shorten the first full-document prefill.

## Recommended next measurement

Update of October 3: the originally proposed profiling and operator
attribution have completed. See the
[prefill profile](2026-10-02-prefill-profile.md), the
[recurrent prefill screen](2026-10-02-recurrent-prefill.md), and the
[attention/GEMM attribution](../experiments/2026-10-02-attention-infrastructure.md).
Recurrent fusion and the attention candidates did not clear their full-model
promotion gates. Do not repeat those unchanged proposals.

The [production GEMM routing test](../experiments/2026-10-03-gemm-routing.md)
completed. Separate prefill and single-row bypass modes qualified on both
models, with full inputs and settings retained, and collection verified. The
modes remain opt-in. Independent long-context and complete-answer
confirmation is the next measurement, before a default adoption. The
[October 3 research](2026-10-03-infrastructure-research.md) lists additional
unused infrastructure candidates and their platform limitations. Retrieval
and input shortening are excluded from this mission.

## Provenance

The source paths and SHA-256 hashes, the build settings, and the CPU cache
snapshot are recorded in
[the audit manifest](raw/2026-09-30-code-audit/source-manifest.json). The
temporary source copies are in
`/tmp/riscv-accl-code-audit-20260930`. Existing measurement context:
[long-prefill research](2026-09-28-long-prefill-research.md),
[local scaling analysis](2026-09-28-local-verification.md), and the
[original configuration findings](2026-09-21-final.md).
