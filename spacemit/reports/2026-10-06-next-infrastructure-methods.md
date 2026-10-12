# Next infrastructure methods after the K1 bandwidth campaign

Date: October 6, 2026, Asia/Singapore. Status: the code audit and the
primary-source research are complete. The candidates below are **unmeasured on
K1**. We launched no new inference campaign for this review.

Follow-up: the
[October 7 decode audit](2026-10-07-decode-packing-results.md) now measures
eight matched requests and four decode profiles. Duplicate FFN packing is only
0.024–0.035% of GEMM worker elapsed, so we do not pursue the sharing. The
approximately 20% calling-thread sync CPU share is not removable inference
latency. M1 kernel scheduling and a precise worker-barrier attribution remain
unmeasured implementation leads. The convolution follow-ups are indexed in the
[current documentation guide](../DOCS.md).

## Measured starting point

The
[completed bandwidth campaign](2026-10-06-k1-roofline-results.md) measures
approximately 7 GB/s on the four inference cores. Routing mode 3 reaches 4.48
and 2.06 decode tokens/s on 2B/4B with a 256-token prompt, and 3.83 and 1.62
with a 2,048-token prompt. Those routing gains confirm an existing change. The
streaming reference does not establish a hardware limit or a forecast of the
achievable inference speed.

Separate **prefill** profiles place the SSM convolution at 6.08% and 5.12%,
and SPERT synchronization at approximately 20%, of sampled self CPU work.
These values are not wall-time fractions and not decode profiles. They
identify investigation targets. They do not predict equivalent whole-model
savings.

We inspected the source over SSH. It is the preserved benchmark copy:

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

This copy contains recorded experiment changes. The production checkout has a
different HEAD (`f3e71c9`). The absence claims below apply to the inspected
copy, not to every current upstream or production version. The routing kernel
is preserved as
[candidate-gemm-routing.cpp](raw/k1-gemm-routing-20261003-005740/candidate-gemm-routing.cpp).

## Priority 1: convolution layout and vectorization

A merged downstream change adds a channels-major SSM convolution. It retains
the projection layout, and it concatenates the recurrent history along time.
Its output layout stays unchanged, and CPU support is included. The change
merged into the AMD `gfx11` fork on July 16, 2026. That merge does not
establish an adoption in our SpaceMiT build. The reported gains use different
models, different hardware, and much larger microbatches than our 32-token
setting. See the
[primary patch and measurements](https://github.com/AMD-Ecosystem/llama.cpp/pull/52)
and the
[maintainer layout/concurrency discussion](https://github.com/ggml-org/llama.cpp/discussions/26380).

**Local evidence:** `src/models/delta-net-base.cpp:465` builds the convolution
history. It reshapes the state to `[time, channels, sequences]`, transposes
`qkv_mixed`, and then concatenates on dimension 0. The transpose is a view,
and the concat materializes the destination layout. The proposed saving
concerns that data movement and the convolution access. It does not concern an
assumed standalone transpose kernel. `ggml/src/ggml-cpu/ops.cpp:9557` uses a C
loop over channels and kernel taps. There is no explicit RVV dispatch inside
that function, and the compiler-generated vectorization still needs an
assembly inspection.

**Proposed implementation, in separate steps:**

1. Inspect the generated assembly. Time the existing convolution and concat at
   the actual model shapes. Record the bytes moved and the kernel invocation
   count.
2. Add an optional channels-major CPU mode, and correct the state-copy views.
   Preserve the existing operator as the control and the fallback.
3. Test an explicit RVV channel loop, where adjacent lanes process adjacent
   channels. Retain the FP32 tap accumulation order, and match the
   multiplication and addition contraction of the reference. The existing code
   explicitly avoids a double-precision dot product. A replacement of that
   helper with the double-precision version changes the arithmetic. Compare the
   layout alone, and then the layout plus RVV, separately.
4. Only if the steps above pass, investigate a convolution plus SiLU fusion as
   a separate change. `qwen35.cpp:431–434` currently creates two graph nodes.
   Preserve the original activation formula and the recurrent history. Measure
   whether an avoidance of the intermediate tensor actually saves model time.

Correctness must cover the kernel widths 3, 4, and 9; the model channel
dimensions; the vector tails; one and multiple sequences; one-token decode;
microbatch boundaries; and a second request after a reset. The state history
must match the reference after every tested chunk. RS rollback remains an
unresolved project gate. Keep the unsupported RS paths on the reference
implementation, until they are qualified.

## Priority 2: quantize shared dense activations once

**Local evidence:** the dense Qwen3.5 FFN calls `build_layer_ffn` with parallel
gate and up branches (`qwen35.cpp:509–518`). Both matmuls receive the same F32
activation (`llama-graph.cpp:1602,1622–1625`). The production routing kernel
quantizes its activation operand on each invocation, and it synchronizes
before the matrix work
(`candidate-gemm-routing.cpp:399–430`).

**Inference from the code:** a paired dense gate/up operation could reuse one
packed activation buffer. It could avoid the duplicate quantization and some
dispatch work. Both weight matrices still have to be read and multiplied. No
packing cost and no whole-model benefit has been measured yet. This candidate
is a local design proposal. It is not a claim that a new upstream patch already
solves our case.

Start with per-invocation counters for the quantization calls, the bytes, the
elapsed time, and the barriers. Then introduce an explicit paired operation,
with one scratch lifetime and the existing matrix kernels. Require identical
input dimensions, quantizer, strides, and block types. Do not cache by tensor
pointer across executions. Graph arenas reuse the addresses for later tokens
and requests. Keep both branch outputs, their arithmetic order, and all Q4_0
weights intact.

Screen M=1/4/32, K=2048/2560, and output widths 6144/9216. Include the tails
and the reset and repeated-request cases. Use the actual audited shapes as
authoritative, if they differ. Only after a dense FFN success, consider the
shared QKV/z input. The graph offers also such a pair, but its shapes and state
lifetime differ. MoE activation-cache changes do not apply automatically to
these dense 2B/4B models.

## Priority 3: decode attribution and operator-specific scheduling

The bandwidth campaign has no phase-isolated decode profile. First profile the
direct route-3 decode at 256 and 2,048 prompt tokens, and separate the prefill
and the generation samples. Resolve the assembly symbols, and report the
synchronization, the packing, the output-head, the attention, and the recurrent
work. Record the available memory counter events and their units. Do not
rename the sampled CPU work as DDR usage.

If this analysis shows that small operators pay a substantial dispatch and
synchronization cost, test a per-operator worker policy or a coarser task
dispatch. Preserve the barriers that the packed-input and matrix-output
dependencies require. If the full output head dominates, investigate its
tiling and partitioning, with every output row retained. We have established
neither finding yet.

The one-worker streaming scan exceeds the four-worker scan, while eight workers
reach approximately 8.29 GB/s. Neither result selects the inference threads.
The IME capability differs between the clusters, and the model performs more
than streaming reads. Any worker-policy candidate needs a direct model timing,
rather than a blanket switch to eight threads.

## Fast qualification plan

| Stage | Required evidence | Advance only when |
| --- | --- | --- |
| Source and assembly audit | The exact tested-source hashes, the actual shapes, the instruction and access pattern, and the scratch lifetime | The proposed mechanism exists in this build, and it is not already optimized |
| Native correctness | Reference against candidate outputs, guards, tails, state history, reset, and repeated requests | The numerical and state checks pass; the unsupported cases fall back explicitly |
| Operator timing | Interleaved repetitions at the decode and microbatch-32 shapes, with initialization excluded | The effect exceeds 3% and the observed control spread, with no required-shape regression |
| Short model screen | Cold ABBA route-3 control/candidate, 2B/256, then 2B/2k and 4B/256/2k, with 64 equal output tokens | The input and cache counts and the output identities match; the whole-model gain clears the existing gate |
| Useful-answer validation | The same complete prompts, natural stopping, deterministic fact and code checks, plus a blinded judge | The candidate causes no quality regression; the baseline failures remain visible |

Keep the routing mode, the RVV attention, the microbatch, the precision, and
the full inputs fixed. Use one candidate change per comparison. Start with the
convolution, because it has both a verified local mechanism and a concrete
external implementation. Add the shared packing only after its counters justify
the work. A native loss or a sub-threshold model gain stops the advancement,
before another hours-long campaign. A long board job must use the
established tmux runner, and a quiet 30-minute completion monitor, when you
actually launch a campaign.

## Adoption boundary

These candidates preserve the required models, the full prompts, the weight
precision, and the output vocabulary. They add no measured gains to the
submission yet. The already screened compact attention, recurrent fusion,
direct-V access, and IME scheduling are recorded negative or sub-threshold
results. They are not newly discovered optimizations. Adaptive MTP remains
opt-in and unqualified, because the useful-code checks fail, despite the
higher capped throughput. We have not demonstrated the present hardware limit.

## October 7 fixed K32 M1 follow-up

The [completed M1 specialization pilot](2026-10-07-ime-m1-k32-results.md)
preserves the exact outputs in the raw and the production tests, including both
full output heads. Its 144 operator samples do not clear the preset
gain/control-spread gate. The branch elimination alone therefore stays
disabled. The matched model and useful-answer stages were skipped. Further load
scheduling or dataflow work needs a separate evidenced mechanism and protocol.
This result does not establish a hardware ceiling.
