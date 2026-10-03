# Infrastructure research: unused paths for the K1

Research date: October 3, 2026, Asia/Singapore. Scope: both required Qwen3.5
models, complete prompts, current SpaceMiT fork and K1 IME1/RVV hardware.
Retrieval, token pruning, model replacement and changing weight precision are
excluded. Published gains on other chips are not predictions for this board.

## Search coverage

Reviewed GitHub projects, arXiv papers and Google Scholar. Direct Scholar
requests through the web tool failed, but the in-app browser successfully
loaded [RISC-V LLM inference optimization](https://scholar.google.com/scholar?q=RISC-V+LLM+inference+optimization).
The first results page included the many-tiny-core paper, V-Seek,
Latency-Critical Quantized Inference, VectorWeaver and AUTOACC. Scholar was
used for discovery; technical conclusions below use the primary sources.
The initial more restrictive V-Seek/T-MAC query surfaced a hardware survey.
This is a targeted review, not a systematic literature review.

## Candidates and platform fit

| Primary source | Technique and relevance | Current decision |
| --- | --- | --- |
| [OpenSolvers K1 study](https://www.opensolvers.com/apps/llamacpp.html) | Separate prefill/decode routing; staging loses on its RV2 setup. Current board attribution finds substantial copy traffic. | **Tested:** separate M>1/M=1 staging bypass improves both models; remains opt-in. Older local real-TCM tests differ from the current runtime. |
| [IME scale-build study](https://github.com/opensolvers/benchmarks/blob/main/papers/x60-ime-block-scale-optimization.md) | Combines block scales using fewer RVV instructions; operator benefit did not reliably become model benefit. | Already represented by patch 0008. Five further schedule/gather variants were screened locally and did not qualify; do not repeat unchanged. |
| [V-Seek](https://arxiv.org/abs/2503.17422), [full text](https://arxiv.org/html/2503.17422v1) | Quantized kernels, compiler choice and NUMA-aware execution on SG2042/RVV 0.7. | Compiler comparison remains possible; K1 uses RVV 1.0 and four IME cores. No direct NUMA-policy or reported-speedup transfer. Existing block quantization and core binding overlap. |
| [T-MAC paper](https://arxiv.org/abs/2407.00088), [code](https://github.com/microsoft/T-MAC) | LUT mixed-precision matrix multiplication avoids ordinary dequantization; implementation targets ARM/Intel and includes four-bit formats. | **Unused research path:** RVV LUT port preserving Q4_0 block scales. Requires new kernels, layout/dispatch and numerical validation; no ready K1/IME1 integration was established. |
| [Vec-LUT paper](https://arxiv.org/abs/2512.06443), [code](https://github.com/OpenBitSys/vlut.cpp) | Vector-oriented LUT layout and streamed lookup exploit parallel tokens. Public model workflow supports ternary formats and I1/I2 packing. | Useful layout research, but adopting its supplied models changes the mission. A Q4_0/RVV port is substantial new work, not a configuration switch. |
| [VectorWeaver contributor description](https://github.com/HorizonChaser), [publisher record](https://dl.acm.org/doi/10.1145/3799719) | Contributor confirms stage- and memory-access-aware RVV kernels and optimization search. | Separate prefill/decode gates are applicable. Publisher full text returned 403; no implementation or detailed tuning algorithm was verified, so no claimed direct port or speedup. |
| [Latency-Critical Quantized Inference](https://ieeexplore.ieee.org/document/10964275/) | Quantized linear-layer and cache optimization for ARM/RISC-V decoder inference. | Supports prioritizing matrix data movement. Abstract verified; full-text download was blocked by a bot challenge. No specific unverified kernel is proposed as a drop-in. |
| [Many-tiny-core inference](https://arxiv.org/abs/2405.19284) | Operand streaming, instruction repetition, specialized DMA and distributed softmax on a different RISC-V architecture. | K1 compatibility was not established for those hardware facilities. Local software tiling can borrow locality principles; hardware speedups cannot be transplanted. |
| [AUTOACC conference record](https://www.cmsworkshops.com/ICASSP2026/view_paper.php?PaperNum=7398), [publisher record](https://ieeexplore.ieee.org/document/11460664/) | Scholar surfaced irregular-operator optimization; the official conference confirms the paper. | Full technical text/code not verified; publisher required bot verification. Discovery lead only, not performance evidence. |

## Local evidence changes the priority

The production GEMM diagnostic completed in 7.15 minutes and matched original
outputs on both models. Staging copies consumed 9.55% / 9.93% of summed
instrumented prefill worker elapsed time and copied 8.82 / 22.58 billion bytes
on each 256-token prompt. Single-row records showed larger copy fractions,
but only twelve records per model were captured; sustained decode was not
established. Worker sums include overlapping waits and timer overhead, so
these fractions are not model wall-time shares or expected removable savings.
See the [completed attribution](../experiments/2026-10-02-attention-infrastructure.md).

Earlier board reports rejected removing pair barriers and enlarging copy
chunks under an older real-TCM configuration. They also corrected an erroneous
50–55 GB/s bandwidth claim down to an approximately 6 GB/s single-cluster
streaming measurement. Do not use the older bandwidth claim or count paired
copy/barrier CPU time as fully exposed wall time. Those changes are distinct
from selecting the existing direct-memory route under today's runtime.

The current TCM API says unavailable/fake/zero geometry, while production
SPERT supplies non-null 128 KiB buffers. Buffer pointers alone do not prove
physical placement. The new experiment keeps this uncertainty explicit and
measures actual graph/model behavior without changing device permissions.

## Code and tests completed

New scripts:

- [Generator](../bench/make-k1-gemm-routing.py): opt-in route selection only
  in eligible production Q4_0 K32/N16 `forward_mul_mat` calls.
- [Native harness](../bench/test-k1-gemm-routing.cpp): actual GGML graph,
  backend weight repacking, 104 numerical cases per arm, guarded outputs and
  workspace, unchanged weights/activations, plus production operator timing.
- [Controller](../bench/k1-gemm-routing.py): original-library comparison,
  six balanced operator blocks, independent prefill/decode gates and cold
  ABBA model tests. Decode uses 64 captured output tokens if qualified.
- [Launcher](../bench/start-k1-gemm-routing.py): board tmux, shared lock and
  local tmux collector with artifact verification.
- [Result verifier](../bench/verify-k1-gemm-routing.py): independently
  recalculates all required operator/model gates and checks actual workload,
  runtime activation and collected artifact hashes.

The [protocol](../experiments/2026-10-03-gemm-routing.md) was written before
launch. Local validation passed two routing checks, six fast-method checks
(including incomplete/mismatched 64-token output rejection), three isolated
build-recipe checks and Bash syntax checks.

## Completed results

Run `k1-gemm-routing-20261003-005740` completed with exit status **0** in
**38.16 minutes**. Both phase-specific modes qualified. The comparison is
against the **current optimized baseline**, including accepted wide attention
and layout 0. Each comparison contains four cold ABBA requests, two per arm.

### Prefill: mode 1, M > 1

Full input prompts and one output token:

| Model / full prompt | Control mean prefill | Bypass mean prefill | Time reduction | Control range |
| --- | ---: | ---: | ---: | ---: |
| 2B / 512 tokens | 22.052917 s | 20.625322 s | 6.47% | 0.05% |
| 4B / 512 tokens | 56.740043 s | 52.304415 s | 7.82% | 0.17% |
| 2B / 2048 tokens | 92.634959 s | 86.709042 s | **6.40%** | 0.27% |
| 4B / 1024 tokens | 115.551047 s | 106.596561 s | **7.75%** | 0.26% |

### Single-row/decode: mode 2, M = 1

Full 256-token input prompts and all 64 requested output tokens captured:

| Model | Control mean decode | Bypass mean decode | Time reduction | Throughput, control → bypass | Control range |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2B | 17.016656 s | 14.566911 s | **14.40%** | 3.76 → 4.39 token/s | 0.59% |
| 4B | 43.553046 s | 31.087887 s | **28.62%** | 1.47 → 2.06 token/s | 1.75% |

Mode 2 can also affect single-row work during prefill. Neither model showed
clear prefill regression in these requests. All six model comparisons passed
the predeclared time-reduction gate. These are engineering screens with two
samples per arm; they do not establish a population confidence interval.
Mode 3 passed numerical checks only; combined-mode model performance was not
tested, and the separate gains must not be added together.

### Verification and evidence boundary

- All **24 model requests** passed matching input and output text/token hashes,
  full requested token counts, uncached counts and actual phase activation.
  Models, Q4_0 weights, F16 KV, four workers and batch/microbatch 32 were verified.
- **104 native production graph cases per arm**, across five arms, gave identical
  output hashes, unchanged input/packed weights and intact output/workspace guards.
- **144 operator records**, six balanced blocks across eight production shapes,
  qualified every candidate shape. Generated mode 0 had no clear regression
  against the original library. Operator gains are not model speed estimates.
- **236 collected artifact hashes** passed an independent verifier, which also
  recalculated all required gates from individual records. End-of-run hashes
  matched all **46 baseline source/object/build files** checked.
- This run's lifecycle environment allowlist omitted `SPINE_K1_GEMM_ROUTE`.
  Mandatory actual kernel markers independently prove each arm's mode,
  eligibility and bypass. The verifier checks those markers and rejects a
  conflicting environment value when recorded. Future runs also capture the
  routing environment field; original raw records were preserved.

Evidence: [raw summary](raw/k1-gemm-routing-20261003-005740/summary.json),
[independent verification](raw/k1-gemm-routing-20261003-005740/verification.json),
[collection receipt](raw/k1-gemm-routing-20261003-005740/collection-receipt.json),
[baseline preservation](raw/k1-gemm-routing-20261003-005740/baseline-preservation-check.json).

The candidate remains **isolated and opt-in**. Independent long-context and
complete-answer confirmation is required before default adoption. The
64-token decode test establishes bounded throughput and exact agreement for
these outputs; it does not establish complete-answer quality.

## Other unused opportunities, ordered after this test

1. **Shared K packing across grouped query heads.** Long causal isolated
   attention attributed about 13.64% to K packing and 14.32% to scratch/mask.
   Sharing requires bounded per-worker storage, safe ownership and measured
   full-model benefit. Direct V won in operators but failed both model gates;
   that result warns against adopting an operator-only gain.
2. **A Q4_0 RVV LUT prototype.** Keep original per-block scales and models;
   evaluate one production-size operator before considering a full port.
   Current IME already computes low-bit matrix products, so avoiding generic
   dequantization does not guarantee a gain over this baseline.
3. **Compiler comparison for measured hotspots.** Build only isolated eligible
   objects with another compatible toolchain, preserving IME encoding and
   RVV 1.0 requirements. V-Seek is motivation, not K1 performance evidence.

These are identified opportunities, not promises of improvement. No search
can establish that all possible optimizations have been exhausted.

## Completion audit

GitHub, arXiv and Scholar discovery are documented above with primary-source
platform checks. The new production routing code and tests ran on the K1;
numerical, operator and both model phases passed. Full inputs and required
model/runtime settings were verified, artifacts independently checked and
current documentation updated. This completes the research, prototype and
measurement task. Additional opportunities above remain research leads;
default deployment is a separate step after independent confirmation.
