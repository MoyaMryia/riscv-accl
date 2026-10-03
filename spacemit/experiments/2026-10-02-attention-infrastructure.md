# Attention infrastructure attribution and layout screen

Status: attention screen completed with exit 0 in 1665.97 seconds (27.77 minutes)
on 2026-10-02, Asia/Singapore. Final status is inconclusive: no candidate
qualified for adoption. The corrected GEMM diagnostic also completed; see below.
Run: `k1-attention-infra-20261002-205454`.

## Scope

Keep both required Qwen3.5 models, Q4_0 weights, F16 KV, complete input prompts,
four workers, batch/microbatch 32, direct decoding, wide RVV attention and layout
0. Retrieval and input shortening are outside this infrastructure experiment.
The earlier Q16/Q32 compact layouts remain inconclusive and are not retested.

The generator modifies only the verified `rvv_kernels.cpp` in an isolated CPU
library. It preserves the existing source checkout/build. Each process selects
`SPINE_FA_K1_INFRA=0/1/2`; `SPINE_FA_K1_PROFILE=1` selects separate instrumented
template instances. Timers are compiled out of ordinary speed/model arms.

| Mode | Change |
| --- | --- |
| 0 | Original arithmetic/packing, diagnostic dispatch available |
| 1 | Full F16 tiles read V directly with its byte stride, skipping V copy and redundant V scratch clear |
| 2 | QK uses e16m2/F32m4 instead of e16m1/F32m2, preserving each cell's accumulation order |

Mode 1 retains the original packed/initialized path on partial V tiles, so
all 64 PV operations and padding behavior remain. Both candidates require
VLEN=256, F32 Q, F16 K/V and 256-dimensional heads; other shapes and compact
layouts retain their original dispatch. No weight or KV format changes.

## Runtime audit

Query the loaded TCM library's version, availability, block geometry and fake
backend flag. Record device availability/access, kernel, CPU governors/frequency
and temperatures without changing OS settings. A separate cold 2B/32 request
uses the original library and `SPINE_TCM_DEBUG=1` to record the actual SPERT
compute-buffer pointers/sizes. It is diagnostic and is not a speed comparison.

The missing `/dev/tcm_sync_mem` causes shared barrier allocation to fall back
to heap in the inspected source. That alone does not establish compute-buffer
placement. `/dev/tcm` exists but is root-only in the initial inventory. The
wide attention dispatcher explicitly passes no TCM buffer; GEMM obtains its
buffer through the SPERT tile context. Query each path separately.

## Predeclared gates

1. Compile one RVV object and an isolated library with the baseline build flags.
   Verify original source, objects, models and runtime hashes.
2. Compare 289 numerical cases per arm against the **original library**, not
   just the generated mode 0. Require bitwise output equality, unchanged inputs,
   finite outputs and scratch/output guards. Cover partial tiles, NaN scratch,
   padded K/V strides, sinks/softcap, masks, grouped heads and two sequences.
3. Attribute stage time on actual attention head counts at 2k/8k/16k history,
   Q32 and dense/causal masks with four pinned workers. Stages: setup/Q packing,
   scratch/mask, K packing, QK, softmax, V packing, PV and output. Diagnostic
   stage sums are active worker time, not full-model wall shares. Clock overhead
   is included. These calls omit production SPERT synchronization.
4. Time direct V only if V packing is at least 1% of mean long causal active
   time; time larger QK groups only if QK is at least 20%. These are screening
   priorities, not predicted model gains. Six balanced blocks compare original
   library, generated mode 0 and eligible candidates. Timing uses repeated
   deterministic tensors, with setup outside the timed region and at least
   100 ms for the slowest worker. The operator stage has a ten-minute budget.
5. Generated mode 0 must not clearly regress against the original library on
   any shape. A candidate needs at least two of four long causal shapes above
   both 3% gain and the full control range, and no clear regression on any shape.
6. Run cold ABBA 2B/2k and 4B/1k model comparisons. Both must clear the same
   model gate. There is no 512-token prerequisite for this attention experiment.
7. Only then run one 8k control/candidate pair per model, reversing arm order
   between models. These are long-context regression pilots, not replication.

Model requests require exact input/output hashes, uncached prompt counts,
activation markers and one returned token. One-token requests do not establish
decode throughput or answer quality. Fresh independent confirmation and
complete-answer checks remain required before adoption.

All workload is serialized under the shared board lock in tmux. The board
limit is two hours after lock acquisition; the lock wait is separate. The local
tmux collector verifies a compressed archive and every collected artifact hash.
Numeric binary dumps and build objects stay on the board.

## Commands

```bash
python3 spacemit/bench/start-k1-attention-infra.py
python3 spacemit/bench/start-k1-attention-infra.py --collect-only \
  --run-dir /absolute/path/to/existing/run
python3 spacemit/bench/test-k1-attention-infra.py
```

## Follow-up decisions

Shared packed K/V between grouped query heads requires measured packing cost,
bounded storage and explicit thread ownership; it is not implemented here.
A separate production GEMM diagnostic uses the same lock. Its initial run,
`k1-gemm-audit-20261002-205004`, failed during compilation; the corrected run,
`k1-gemm-audit-20261002-221714`, completed. It instruments only the verified
Q4_0 `forward_mul_mat` calls in an isolated `ime.cpp` object. It records
activation quantization, staging-copy bytes/time, GEMM, grid wait and paired
barrier wait on complete 256-token cold prompts for both models. One original
and one instrumented request per model must have matching output hashes and
uncached input counts. These are diagnostics, not speed comparisons. Summed
worker elapsed times include overlapping waits; their percentages cannot be
subtracted from model wall latency. The two output tokens across each model's
requests do not establish sustained decode throughput.

The GEMM job has a separate 30-minute limit after acquiring the lock. Launch
with `python3 spacemit/bench/start-k1-gemm-audit.py`; collection-only recovery
uses the same `--collect-only --run-dir` arguments as the attention launcher.
This run does not repeat the five rejected IME scheduling/gathering variants.

## Initial build repairs

The first run, `k1-attention-infra-20261002-204256`, exited 1 during RVV
compilation: the generator changed intrinsic suffixes but initially missed
vector type names. The second run, `k1-attention-infra-20261002-204558`, compiled
and linked the candidate library but exited 1 during harness compilation due
to a missing internal GGML include directory. Neither ran inference tests.
Their original logs and failure status remain archived. The third run, `k1-attention-infra-20261002-204948`, compiled the library and
harness and completed the runtime probe. Its original-library numerical arm
then stopped on `GGML_ASSERT(mask)`: an extra dense fixture requested ALiBi bias
without a mask. The fixture now requests bias only when its mask exists;
dense extra cases still exercise softcap/sinks. No candidate numerical pass
or speed result from that run is claimed. The corrected fresh run above
includes all three repairs; verify its gates from the collected artifacts.

## Completed runtime observations

The third run's runtime audit and cold 2B/32 diagnostic completed before the
numerical fixture failure. The loaded `.toolchain/spine-tcm/libspine_tcm.so.3.0.1`
reports `available=0`, zero blocks/size, `fake=true`, and a successful geometry
query status. `/dev/tcm` exists with mode 0600 and is inaccessible to UID 1000;
`/dev/tcm_sync_mem` and `/dev/hugetlb_1g` do not exist. All CPU frequency readings
were 1.6 GHz with the performance governor; temperatures were 35 C.

The actual original-library GEMM debug records show four non-null SPERT
shared buffers of **131072 bytes** each, plus heap fallback for the shared
barrier. The SPERT buffer observation does not establish physical TCM
placement. Do not claim that the measured build uses hardware TCM based on
library path or buffer presence alone. No permissions, driver, frequency or
memory-backend settings were changed. The next runtime investigation is the
relationship between SPERT's buffers, the TCM runtime and the device driver.

Evidence: `reports/raw/k1-attention-infra-20261002-204948/runtime-audit.json`
and `runtime-2B-32.server.log` in that run directory.

## Completed attention result

Run `k1-attention-infra-20261002-205454` completed. Its archive and all **349**
collected artifact hashes were verified locally. All 289 cases per arm matched
the original library bit for bit, including unchanged inputs and output/scratch
guards. Twelve diagnostic records and all 288 operator arms completed.

Mean long causal active-worker attribution: PV 41.35%, QK 23.13%, scratch/mask
14.32%, K packing 13.64%, softmax 3.79% and V packing 3.69%. This is isolated
attention attribution, not a distribution of full-model wall time.

| Model head shape | History | Direct-V operator reduction | Larger-QK-group reduction |
| --- | ---: | ---: | ---: |
| 2B | 8192 | 5.93% | -1.06% |
| 2B | 16384 | 12.95% | 4.31% |
| 4B | 8192 | 13.49% | 4.40% |
| 4B | 16384 | 7.35% | 2.90% |

Direct V qualified three of four long causal shapes; larger QK grouping
qualified only one and did not advance. The generated mode 0 had no clear
regression against the original library on any tested operator shape.

The direct-V candidate then completed four ABBA cold requests per model:

| Model / prompt | Control mean prefill | Direct-V mean prefill | Time change |
| --- | ---: | ---: | ---: |
| 2B / 2048 | 92.903453 s | 94.459168 s | +1.67% (slower) |
| 4B / 1024 | 115.420622 s | 115.520340 s | +0.09% |

All eight requests had matching input/output hashes and exact uncached counts.
Neither model cleared the predeclared improvement gate; 8k and complete-answer
stages were skipped. Keep original V packing and QK grouping. Warm repeated
operator gains did not translate into gains in these full-model pilots.
No speedup, sustained decode or quality claim follows.

Evidence: [summary](../reports/raw/k1-attention-infra-20261002-205454/summary.json),
[attribution](../reports/raw/k1-attention-infra-20261002-205454/attribution.jsonl),
[operator arms](../reports/raw/k1-attention-infra-20261002-205454/operator.jsonl),
and [collection receipt](../reports/raw/k1-attention-infra-20261002-205454/collection-receipt.json).

## GEMM diagnostic repair

`k1-gemm-audit-20261002-205004` stopped during compilation with exit 1 after
205.20 seconds; it has no inference attribution. The relocated `ime.cpp`
selected generic CPU `repack.h` ahead of its SpaceMiT sibling with the same
name. The isolated compile helper now puts the original source directory first
in the include search list, preserving the original quoted-header resolution.
The previous source/build remains intact and its failure artifacts are retained.

Corrected fresh run: `k1-gemm-audit-20261002-221714`. It completed with exit 0
in 429.15 seconds (7.15 minutes). On October 3, SSH confirmed both jobs had
finished and no benchmark tmux session or llama-server process remained.
All 29 collected GEMM artifact hashes and all 349 attention artifact hashes
matched their collection receipts. Three isolated-recipe checks and four
attention-gate checks pass locally after the repair.

## Completed GEMM attribution

Both models' original and instrumented requests had matching output hashes
and verified uncached 256-token prompts. The following shares are of summed
instrumented worker elapsed time, including overlapping waits and clock
overhead; they are **not full-model wall-time shares or predicted savings**.

| Model | Prefill records | Quantization | Staging copies | GEMM | Grid wait | Pair wait | Copied bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2B | 8184 | 1.71% | 9.55% | 83.76% | 0.25% | 3.24% | 8,815,177,728 |
| 4B | 10912 | 1.32% | 9.93% | 84.23% | 0.17% | 3.15% | 22,578,315,264 |

All observed staging buffers were 128 KiB. The twelve single-row records per
model attributed 40.86% / 42.95% to staging copies, but cover only first-token
work and cannot establish sustained decode behavior. No optimized GEMM
candidate was enabled in this diagnostic.

The next candidate is to compare production Q4_0 staging with the existing
direct-memory path, after checking earlier board experiments for overlapping
tests. Verify actual dispatch, bitwise operator outputs and cold model
latency before enabling it. Buffer presence alone does not establish hardware
TCM placement, and bypassing copies can also lose useful locality.

Evidence: [GEMM summary](../reports/raw/k1-gemm-audit-20261002-221714/summary.json)
and [collection receipt](../reports/raw/k1-gemm-audit-20261002-221714/collection-receipt.json).
