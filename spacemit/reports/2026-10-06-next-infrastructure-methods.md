# Next infrastructure methods after the K1 bandwidth campaign

Date: October 6, 2026, Asia/Singapore. Status: code audit and primary-source
research completed; candidates below are **unmeasured on K1**. No new inference
campaign was launched for this review.

## Measured starting point

The [completed bandwidth campaign](2026-10-06-k1-roofline-results.md) measures
approximately 7 GB/s on the four inference cores. Routing mode 3 reaches
4.48/2.06 decode tokens/s on 2B/4B with a 256-token prompt, and 3.83/1.62
with a 2,048-token prompt. Those routing gains confirm an existing change.
The streaming reference does not establish a hardware limit or a forecast
of achievable inference speed.

Separate **prefill** profiles place SSM convolution at 6.08%/5.12% and SPERT
synchronization at approximately 20% of sampled self CPU work. These are not
wall-time fractions or decode profiles. They identify investigation targets;
they do not predict equivalent whole-model savings.

The source inspected over SSH is the preserved benchmark copy:

```text
/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-layout-20260930-153134/source
Git base: a990751d55a4c54acf2bb77d44282c2093652359
ggml/src/ggml-cpu/ops.cpp:
  d03e80d18d117047b5f6cc007a277c80cab90e9d6c9f7f97ef4d8002db1a8192
src/llama-graph.cpp:
  fc5037613eee32a4912ebbaef0489dc1936eed6eccf01c192e922f8b6a77a5e5
src/models/qwen35.cpp:
  7643d4ce05ee44fa6f46b47436e82a2b7db171f04189a73fa5b2305fff82b30e
```

This copy contains recorded experiment changes. The production checkout has
a different HEAD (`f3e71c9`); absence claims below apply to the inspected
copy, not every current upstream or production version. The routing kernel
is preserved as [candidate-gemm-routing.cpp](raw/k1-gemm-routing-20261003-005740/candidate-gemm-routing.cpp).

## Priority 1: convolution layout and vectorization

A merged downstream change adds channels-major SSM convolution, retaining
the projection layout and concatenating recurrent history along time.
Its output layout stays unchanged. CPU support is included. It merged into
AMD's `gfx11` fork on July 16, 2026; this does not establish adoption in our
SpaceMiT build. Reported gains use different models, hardware and much larger
microbatches than our 32-token setting.
[Primary patch and measurements](https://github.com/AMD-Ecosystem/llama.cpp/pull/52),
[maintainer layout/concurrency discussion](https://github.com/ggml-org/llama.cpp/discussions/26380).

**Local evidence:** `src/models/delta-net-base.cpp:465` builds convolution
history by reshaping state to `[time, channels, sequences]`, transposing
`qkv_mixed`, then concatenating on dimension 0. The transpose is a view;
concat materializes the destination layout. The proposed saving concerns
that data movement and convolution access, not an assumed standalone
transpose kernel. `ggml/src/ggml-cpu/ops.cpp:9557` uses a C loop over channels
and kernel taps. There is no explicit RVV dispatch inside this function;
compiler-generated vectorization still needs assembly inspection.

**Proposed implementation, in separate steps:**

1. Inspect generated assembly and time the existing convolution and concat
   at the actual model shapes. Record bytes moved and kernel invocation count.
2. Add an optional channels-major CPU mode and correct state-copy views.
   Preserve the existing operator as control and fallback.
3. Test an explicit RVV channel loop, where adjacent lanes process adjacent
   channels. Retain the FP32 tap accumulation order and match the reference's
   multiplication/addition contraction. The existing code explicitly avoids
   a double-precision dot product; replacing it with that helper changes
   arithmetic. Compare layout alone and layout plus RVV separately.
4. Only if the above passes, investigate convolution plus SiLU as a separate
   fusion. `qwen35.cpp:431–434` currently creates two graph nodes. Preserve
   the original activation formula and recurrent history; measure whether
   avoiding the intermediate tensor actually saves model time.

Correctness must cover kernel widths 3/4/9, model channel dimensions, vector
tails, one and multiple sequences, one-token decode, microbatch boundaries,
and a second request after reset. State history must match the reference
after every tested chunk. RS rollback remains an unresolved project gate;
keep unsupported RS paths on the reference implementation until qualified.

## Priority 2: quantize shared dense activations once

**Local evidence:** the dense Qwen3.5 FFN calls `build_layer_ffn` with parallel
gate/up branches (`qwen35.cpp:509–518`). Both matmuls receive the same F32
activation (`llama-graph.cpp:1602,1622–1625`). The production routing kernel
quantizes its activation operand on each invocation and synchronizes before
matrix work (`candidate-gemm-routing.cpp:399–430`).

**Inference from the code:** a paired dense gate/up operation could reuse one
packed activation buffer and avoid duplicate quantization and some dispatch
work. Both weight matrices still have to be read and multiplied. No packing
cost or whole-model benefit has yet been measured. This is a local design
candidate, not a claim that a new upstream patch already solves our case.

Start with per-invocation counters for quantization calls, bytes, elapsed
time and barriers. Then introduce an explicit paired operation with one
scratch lifetime and the existing matrix kernels. Require identical input
dimensions, quantizer, strides and block types. Do not cache by tensor pointer
across executions: graph arenas reuse addresses for later tokens and requests.
Keep both branch outputs, their arithmetic order and all Q4_0 weights intact.

Screen M=1/4/32, K=2048/2560, and output widths 6144/9216, including tails and
reset/repeated-request cases. Use the actual audited shapes as authoritative
if they differ. Only after dense FFN success consider the shared QKV/z input;
the graph also offers such a pair, but its shapes and state lifetime differ.
MoE activation-cache changes are not automatically applicable to these dense
2B/4B models.

## Priority 3: decode attribution and operator-specific scheduling

The bandwidth campaign has no phase-isolated decode profile. First profile
direct route-3 decode at 256 and 2,048 prompt tokens, separating prefill and
generation samples. Resolve assembly symbols and report synchronization,
packing, output-head, attention and recurrent work. Record available memory
counter events and their units; do not rename sampled CPU work as DDR usage.

If this shows small operators paying substantial dispatch/synchronization
cost, test a per-operator worker policy or coarser task dispatch. Preserve
barriers required by packed-input and matrix-output dependencies. If the full
output head dominates, investigate its tiling/partitioning with every output
row retained. Neither finding has yet been established.

The one-worker streaming scan exceeds the four-worker scan, while eight
workers reach approximately 8.29 GB/s. Neither result selects inference
threads: IME capability differs between clusters, and the model performs
more than streaming reads. Any worker-policy candidate needs direct model
timing, rather than a blanket switch to eight threads.

## Fast qualification plan

| Stage | Required evidence | Advance only when |
| --- | --- | --- |
| Source and assembly audit | Exact tested-source hashes, actual shapes, instruction/access pattern, scratch lifetime | The proposed mechanism exists in this build and is not already optimized |
| Native correctness | Reference versus candidate outputs, guards, tails, state history, reset and repeated requests | Numerical/state checks pass; unsupported cases fall back explicitly |
| Operator timing | Interleaved repetitions at decode and microbatch-32 shapes; initialization excluded | Effect exceeds 3% and observed control spread, with no required-shape regression |
| Short model screen | Cold ABBA route-3 control/candidate, 2B/256 then 2B/2k and 4B/256/2k, 64 equal output tokens | Input/cache counts and output identities match; whole-model gain clears the existing gate |
| Useful-answer validation | Same complete prompts, natural stopping, deterministic fact/code checks plus blinded judge | Candidate causes no quality regression; baseline failures remain visible |

Keep routing mode, RVV attention, microbatch, precision and full inputs fixed.
Use one candidate change per comparison. Start with convolution because it has
both a verified local mechanism and a concrete external implementation; add
shared packing only after its counters justify the work. A native loss or
sub-threshold model gain stops advancement before another hours-long campaign.
Long board work should use the established tmux runner and a roughly
30-minute quiet completion monitor when a campaign is actually launched.

## Adoption boundary

These candidates preserve the required models, full prompts, weight precision
and output vocabulary. They do not add measured gains to the submission yet.
Already screened compact attention, recurrent fusion, direct-V access and IME
scheduling are recorded negative/sub-threshold results, not newly discovered
optimizations. Adaptive MTP remains opt-in and unqualified because useful-code
checks fail despite higher capped throughput. The present hardware limit has
not been demonstrated.
