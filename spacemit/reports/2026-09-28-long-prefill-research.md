# Faster long-context prefill on MUSE-Pi-Pro: GitHub and Google Scholar scan

> Dated campaign snapshot. The measurements apply to the stated workload and
> date. Queued/running statements below are historical. Use the
> [current guide](../DOCS.md) and the [reports index](README.md) for later
> results and for the current status.

Date: 2026-09-28. Scope: the required Qwen3.5 2B/4B GGUFs on the SpaceMiT
K1/X60 board and the official SpaceMiT llama.cpp fork. We located the papers
through Google Scholar and checked them against their primary manuscripts.
We checked the implementations and the failure reports on GitHub. The
external speedups below are **not** measured gains on this board.

## The measured bottleneck

The completed
[2B 32,768-token request](raw/2026-09-25-lifecycle/2B-q4w-f16kv-32768-rvv1-bounded.jsonl)
used Q4_0 weights, F16 K/V, four threads, `-b 32 -ub 32`, and the opt-in
256-bit RVV attention path. Cold TTFT was **3,291.21 s (54 min 51 s)** at
9.96 prompt tokens/s. Peak RSS was 2,768.4 MiB, with no swap and no OOM. The
[server log](raw/2026-09-25-lifecycle/2B-q4w-f16kv-32768-rvv1-bounded.log)
shows each 32-token microbatch rising from **1.38 s near token 256** to
**2.24 s near 8k**, **3.19 s near 16k**, and **5.11 s near 32k**. The roughly
linear per-microbatch increase with processed context makes attention and
history traffic the first profiling target. But these timings alone do not
isolate the operator. The current tiled kernel uses 64 query and 64 KV cells
per tile, while each server microbatch carries only 32 tokens. The
[official config](https://huggingface.co/Qwen/Qwen3.5-2B/blob/main/config.json)
of the model has 256-dimensional full-attention heads and one full-attention
layer in every four.

## Ranked paths

| Priority | Path | Relevance and constraint | First falsifiable test |
| --- | --- | --- | --- |
| 1 for repeated documents | Keep the exact prefix hot in the same server process | The [llama.cpp server documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) says that `cache_prompt=true` evaluates only the unseen suffix. Our [local 2k test](2026-09-25-lifecycle.md) cut second-request TTFT from 110.87 to 0.45 s for 2B, with the same output hash. This is the only already measured order-of-magnitude latency reduction for repeated input. Hybrid recurrent checkpoints complicate reuse: upstream [Qwen3.5 reprocessing](https://github.com/ggml-org/llama.cpp/issues/20225) and [slot-save/restore](https://github.com/ggml-org/llama.cpp/issues/25913) issues show why 2k success cannot be assumed at 32k or across restarts. | Do same-process, same-slot 8k, then 16k, then 32k cold/warm/warm requests with `cache_prompt=true`. Record `cache_n`, the prompt tokens actually evaluated, TTFT, and output token hashes. Test 32k only if the shorter checks reuse correctly. Do not rely on disk slot restore until checkpoint state is verified. |
| 1 for a unique cold document | Send fewer relevant tokens | [LLMLingua-2](https://arxiv.org/abs/2403.12968) reports 2–5× prompt compression and 1.6–2.9× end-to-end latency improvement on its evaluated tasks. Its [public code](https://github.com/microsoft/LLMLingua) is available. For code and multilingual material, a deletion can remove critical details. This approach changes the input and has no exact-token guarantee. Deterministic query-directed retrieval of source spans is the simpler first candidate, and the original document can remain local. | On a held-out set of real user questions, compare the full document against exact-span retrieval at 4k/8k/16k target budgets. Measure recall of required facts, answer correctness, cited source spans, and full request time, including retrieval. Try learned compression only if retrieval misses too much. |
| 2 for a unique full 32k prompt | Profile and retune the exact RVV attention kernel | [FlashAttention for Scalable Vector Architectures](https://arxiv.org/abs/2608.18656) evaluated RVV on a Banana Pi BPI-F3, also a [SpaceMiT K1 board](https://www.banana-pi.org/en/product-news/547.html). Loop reordering, head unrolling, and K/V reuse are relevant to our 256-bit, 256-head tiled path. Its largest reported gains use scalar baselines or simulated wider vectors. On real 256-bit hardware, its prefill advantage was strongest at 64–128 tokens, and an adaptation of its ideas to a newer tiled implementation produced about 5% in that paper. A direct large-context gain here is unproven. Another [RISC-V vector FlashAttention paper](https://arxiv.org/abs/2510.06834) explores blocking and a faster approximate exponential on gem5. Its published acceleration is not a K1 result, and an approximate softmax can alter the output. | Profile the existing 8k and 16k runs by operator. In an isolated build, compare `-ub 32/48/64` at identical prompt, context, and model settings. Then do a kernel-only query/KV tile and loop-order sweep, if attention dominates. Check the full output token IDs and server TTFT. Revert any variant that helps the kernel but hurts end-to-end time. |
| 3, after profiling | Parallel/chunked Gated DeltaNet prefill | The [GDN inverse-approximation paper](https://arxiv.org/abs/2606.06034) reports up to 5× **kernel-level** speedup on Qwen3.5-family models. But it targets NPU-style chunked linear attention, it uses an approximation, and it gives no drop-in K1/llama.cpp path. The [GDN prefill implementation of FlashInfer](https://github.com/flashinfer-ai/flashinfer/blob/main/flashinfer/gdn_prefill.py) requires CUDA. | Pursue only if operator profiling shows that recurrent GDN work is a large fraction of 32k prefill, and an RVV implementation can preserve the required output quality. |

A [Tail-Replay paper](https://arxiv.org/abs/2608.30310), found through Google
Scholar, is specifically relevant to **shared prefixes** in hybrid models. It
reports a 9.1× 32k TTFT speedup for Qwen3.5-4B on its serving setup, with a
5% recurrent-state replay budget. Its LongBench average retained 98.9%, and
RULER 99.9%, of the full-prefill scores. The method caches full-attention KV
and hidden outputs, and then **approximates** the recurrent state from a
recent tail. It requires a new serving implementation, a previously computed
prefix, and quality checks. It cannot accelerate a truly cold first request,
and it cannot guarantee bitwise identical output. Validate the existing exact
in-memory cache reuse first.

## What does not solve this 55-minute cold prefill

- MTP and n-gram speculation affect **decode**. They do not affect the first
  processing of 32k input. Our long-code direct/MTP token mismatch remains
  open.
- Q8_0 weights were slower than Q4_0 on both tested model sizes in the
  [matched board comparison](raw/2026-09-25-lifecycle/lifecycle-weight-compare-2k.jsonl).
- Q4_0 K/V saved memory in the tested 4B run. But it cannot activate the
  current F16-only wide RVV prefill kernel, and it is not a demonstrated 32k
  latency fix.
- The board measured OpenCL path transferred zero layers. We dropped the
  Vulkan route after its
  [driver audit](raw/2026-09-25-lifecycle/vulkaninfo-full.txt). GPU-only
  FlashInfer, CUDA, Triton, and ROCm speedups are not directly portable to
  this PowerVR/K1 setup.

**Decision:** For interactive use, first determine whether the 32k content is
reused or unique. If the content is reused, test same-process cache
correctness at increasing lengths. If the content is unique, benchmark
real-task source retrieval, to reduce the prompt. For a requirement to
process every one of 32k tokens cold, profile the existing RVV attention path
before you implement another kernel. No reviewed paper and no GitHub patch
establishes a guaranteed large speedup for this exact configuration.

## Same-process cache experiment (completed 2026-09-28)

The [gated board runner](../bench/run-prefix-cache-gated-board.sh) sent three
identical requests per context to one 2B server process. Each context started
a fresh server. The [gate](../bench/check-prefix-cache.py) required the full
32-token output, identical token IDs and text, at least 90% cache reuse, and
warm TTFT at most half of cold TTFT, before an advance from 8k to 16k to 32k.
The Q4_0 weights, F16 K/V, four threads, batch and microbatch 32, and the
256-bit RVV path matched the long-prefill configuration.

| Prompt tokens | Cold TTFT | Warm TTFT #1 | Warm TTFT #2 | Cached prompt tokens on both warm runs | Result |
| ---: | ---: | ---: | ---: | ---: | --- |
| 8,192 | 450.54 s | 0.86 s | 0.95 s | 8,188 | PASS |
| 16,384 | 1,140.11 s | 1.52 s | 1.58 s | 16,380 | PASS |
| 32,768 | 3,302.07 s | 2.93 s | 2.83 s | 32,764 | PASS |

The server evaluated four prompt tokens on each warm request. All three
requests at each length produced the same 32 token IDs and text. The raw
[8k](raw/2026-09-25-lifecycle/2B-prefix-cache-8192-rvv1.jsonl),
[16k](raw/2026-09-25-lifecycle/2B-prefix-cache-16384-rvv1.jsonl), and
[32k](raw/2026-09-25-lifecycle/2B-prefix-cache-32768-rvv1.jsonl) records, and
the [driver log](raw/2026-09-25-lifecycle/prefix-cache-gated-driver.log), are
archived.

**Practical decision:** Keep a 2B server process and its prompt cache alive
when users revisit an identical long prefix. This practice removes almost all
repeat-prefill delay, including at 32k. The first request still takes about
55 minutes. This experiment does not establish reuse after a server restart,
after a prefix change, after a slot switch, or for 4B. Those cases are
separate tests. For a unique full 32k input, source retrieval or cold-prefill
profiling remains the relevant next optimization.

## Follow-up: changed question on a cached document

The
[2026-09-29 changed-question test](2026-09-29-shared-document-cache.md)
found a correctness limit that the identical-prompt experiment did not
exercise. The 2B/8k and 4B/8k–16k warm requests reproduced their forced-cold
answers, with large TTFT reductions. But the 2B/16k request first differed at
generated token index 5, despite the cache of 16,373 document tokens. The
gate therefore skipped 2B/32k. Do not generalize the exact repeated-prompt
success at 32k to arbitrary follow-up questions.
