# K1/X60 research scan and next measurements

> Dated campaign snapshot. The measurements apply to the stated workload and
> date. Queued/running statements below are historical. Use the
> [current guide](../DOCS.md) and the [reports index](README.md) for later
> results and for the current status.

Date: 2026-09-24. Target: MUSE-Pi-Pro, SpaceMiT K1/X60, Bianbu 2.3.5, 16 GB.
This document is a research and experiment plan. It links one new targeted
board measurement. The board `~/Projects` directory contains `llm-bench`,
`spacemit-llama`, `spacemit-llama-frspec`, and `ccode`. The measured official
fork is at `~/Projects/spacemit-llama/llama.cpp`, currently on
`codex/lowacc-fallback` (`f3e71c9`). The mapped-head prototype is a separate
checkout with a local modification to `src/models/qwen35.cpp`.

The [integrated K1 follow-up](2026-09-24-integrated-k1.md) builds and
measures the ranked kernel and vocabulary candidates. It tests a timing gate
and hybrid dispatch, and it records why we did not port the long-context
routes for the current 8k workload.

## Current measured position

The [project baseline](2026-09-21-final.md) gives Qwen3.5-2B Q4_0 direct
decode 5.19 tok/s and an eight-stream aggregate 13.85 tok/s with the
checkpoint/gate server. Single-stream MTP with the RS snapshot reached
6.31 tok/s. The [n-gram experiment](2026-09-24-ngram.md) reached 10.36 tok/s
on a near-copy C++ edit, against 7.99 for MTP alone. The results were nearly
tied on a small Python edit and on a prose prompt. The
[mapped 32k head](2026-09-23-frspec.md) improved a tested Chinese prompt
from 3.58 to 4.92 tok/s over the prefix 64k head, but direct decode was
about 5.10 tok/s. These figures have different workloads and settings. They
are not interchangeable.

The base 2B decode is already near the locally measured weight-stream
bandwidth limit. The largest remaining opportunities are a reduction of the
*draft cost per accepted token*, an improvement of the M=4–8
verification/multistream matrix path, and an avoidance of speculation when
its measured request-level cost exceeds direct decode. Do not extrapolate a
kernel-only speedup to end-to-end inference.

A new [same-model A/B](2026-09-24-mapped-cpu-sampling.md) combines the
mapped 32k head with CPU-side MTP draft sampling. English reached
**7.004 tok/s** against 6.812 with backend sampling (+2.8%) and 5.118
direct. Chinese reached 5.075 against 4.938 (+2.8%), but it stayed below
5.115 direct. These are two-run, two-prompt server decode measurements in
the experimental mapped-head checkout.

## Ranked leads

| Priority | Source | Why it fits this project | Next falsifiable test |
| --- | --- | --- | --- |
| 1 | [VocabTrim](https://arxiv.org/abs/2506.22694), [DynaSpec](https://arxiv.org/abs/2510.13847), [SpecVocab](https://arxiv.org/abs/2602.13836) | The 248,320-token Qwen3.5 output head dominates each MTP draft step. The existing mapped 32k prototype proves that head selection matters, especially for Chinese. DynaSpec and SpecVocab address the weakness of a single static corpus-ranked shortlist. | Start with several *static* 32k maps that separate Chinese/code/English corpora train, and one balanced map. Evaluate on held-out prompts. Track draft-head time, accepted tokens per round, total decode tok/s, output hashes, and model RAM. Dynamic per-step routing is a later implementation, and only if corpus specialization wins. |
| 2 | [OpenSolvers X60 IME/RVV study and fork](https://www.opensolvers.com/apps/llamacpp.html), [X60 block-scale kernel study](https://github.com/opensolvers/benchmarks/blob/main/papers/x60-ime-block-scale-optimization.md) | Their X60 tests show that the prefill/decode split can favor different kernels. An isolated Q4_0 M4 scale-build change gains about 5% in GEMM, but it showed no measurable end-to-end prefill improvement. The largest open kernel question in this project is M=4–8 verification and eight-stream throughput, not M1 direct decode. | In an isolated official-fork worktree, compare the original kernel with the selectively ported M4 kernel and dispatch. Use the same 2B/4B GGUF, true `spine-tcm`, CPU affinity, and interleaved `pp128`, `tg128`, verify-M4, and concurrency-8 runs. Require a statistically stable end-to-end gain before adoption. Their RV2 TCM shim regression does not override the measured gain of this MUSE-Pi-Pro from the vendor TCM library. |
| 3 | [llama.cpp Q8_0 IME1 PR #28479](https://github.com/ggml-org/llama.cpp/pull/28479) | The current local 4B Q8_0 is much slower than Q4_0, because the official-fork IME1 path has no Q8_0 kernel. The draft PR reports an 8.9x Q8_0 **prefill** gain on another X60 board. | Port to an isolated checkout only if higher precision is a product goal. Compare the existing 4B Q8_0 artifact against itself, before and after, for `pp128`, `tg128`, and output accuracy. The PR gives no trustworthy token-generation gain. The larger weight stream means that you must not assume that Q8_0 is faster than Q4_0. |
| 4 | [Learning to Draft](https://arxiv.org/abs/2603.01639), [AdaSD](https://arxiv.org/abs/2512.11280) | This project already has an opt-in low-acceptance fallback. A cost-aware controller could select direct, MTP, or n-gram per request. It would use the observed *time per accepted token*, not only an acceptance count. | Instrument per-round draft, verify, and sync times. Replay a policy offline on a held-out mixed workload before a server change. Then compare paired live runs against direct, fixed MTP, and the current fallback. |

## Lower priority for today's 8k-context workload

- [Windowed-MTP](https://arxiv.org/abs/2607.21535) bounds the draft KV read
  at very long contexts. Its reported gains are at roughly a million-token
  context. First measure draft KV traffic at 8k and 16k before a change to
  attention.
- [KVBuffer](https://arxiv.org/abs/2605.19049) and [TreeWY](https://arxiv.org/abs/2608.20961)
  reduce recurrent-state traffic or speculative state snapshots. TreeWY
  targets large hybrid models and memory-limited tree verification. This
  project has implemented checkpoint rollback already and found
  synchronization costly, so a direct port is not a near-term win.
- [upstream speculative modes](https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md)
  and the [Qwen3.5 compact-head issue #29145](https://github.com/ggml-org/llama.cpp/issues/29145)
  are useful integration references. The local prototype implements a `d2t`
  mapping already. The open upstream issue is not proof of a board speedup.

## Measurement gate

Use the existing [benchmark runner](../bench/README.md), the same
official-fork base and model, `LD_LIBRARY_PATH` with `spine-tcm`, a fixed
governor and affinity, alternating A/B order, at least three runs per arm,
and identical greedy output hashes. Report prefill, decode, acceptance, and
latency separately. Include English, Chinese, code, near-copy editing, long
context, and concurrency 1/4/8. The mapped-head CPU-sampling result above is
an encouraging targeted measurement. A broader end-to-end improvement is
still unestablished.
