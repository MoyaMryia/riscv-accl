# Integrated K1/X60 result: draft maps, IME kernels, and fallback policy

> Dated campaign snapshot. Measurements apply to the stated workload and date.
> Queued/running statements below are historical; use the
> [current guide](../DOCS.md) and the [reports index](README.md) for later results and current status.

Date: 2026-09-24. Board: MUSE-Pi-Pro, SpaceMiT K1/X60, Bianbu 2.3.5, 16 GiB RAM. Source: official SpaceMiT llama.cpp base 5ad05d8 plus project patches 0001–0006, with the mapped-head prototype and the two kernel candidates tested in an isolated worktree. The final tested source matches the complete packaged patch set byte for byte and is committed on the isolated board branch codex/k1-integrated at a990751 (~/Projects/spacemit-llama-integrated). The experimental cost gate and hybrid dispatch were removed from the final build.

All rate figures below are tokens/s. Server figures use greedy decoding, seed 42, an 8192-token context, one slot, four threads, batch and microbatch 32, flash attention, SPINE_SPEC_RS=1, the vendor spine-tcm library, and 128 requested tokens except for the explicitly marked Q8 correctness check. Kernel figures use llama-bench with four threads, batch and microbatch 32, flash attention, and the exact model named in each table. Every model/server arm starts in a separate process. Raw JSONL and fallback events are under [raw/2026-09-24-integrated](raw/2026-09-24-integrated/).

## Recommended changes

| Change | Observed result | Decision |
| --- | --- | --- |
| [Q8_0 IME1 patch 0007](../patches/0007-q8-ime1.patch), adapted from [llama.cpp PR #28479](https://github.com/ggml-org/llama.cpp/pull/28479) | 4B Q8_0 pp64 1.117 → 7.472 (6.69×); tg32 0.866 → 1.349 (+55.8%). Three server greedy responses kept identical hashes. | Offer for deployments that need Q8_0. Q4_0 remains faster and smaller. |
| [M4 scale patch 0008](../patches/0008-ime-m4-scale.patch), from the [OpenSolvers X60 study](https://github.com/opensolvers/benchmarks/blob/main/papers/x60-ime-block-scale-optimization.md) | 4B Q4_0 pp128 9.058 → 9.360 (+3.3%); 2B mapped MTP English 6.944 → 7.066 (+1.8%), Chinese 5.030 → 5.121 (+1.8%). | Offer for Q4_0 prefill and MTP verification. |
| Existing mapped 32k head plus CPU draft sampling | With patch 0008, 2B English 7.066 and Chinese 5.121 in the paired M4 test. | Keep the existing mapped head and CPU sampling flag as workload-specific choices. |

The Q8_0 patch is an upstream draft. Its 4B improvement is real on this board, but 4B Q4_0 still decodes at about 2.32 tok/s against 1.35 for Q8_0. The Q8_0 result is a better higher-precision path, not the fastest overall path.

## Detailed A/B evidence

### Q8_0 IME1

The 4B Q8_0 model is the same 4,482,403,488-byte GGUF before and after the source patch. llama-bench used pp64 and tg32, two repetitions per arm. The Q4_0 model was a control for unintended kernel changes.

| Model and test | Before | After Q8 patch |
| --- | ---: | ---: |
| 4B Q8_0 pp64 | 1.117 | 7.472 |
| 4B Q8_0 tg32 | 0.866 | 1.349 |
| 4B Q4_0 pp128 control | 8.939 | 9.039 |
| 4B Q4_0 tg32 control | 2.294 | 2.319 |

The server correctness check requested 32 tokens. English was 0.896 → 1.404 tok/s, Chinese 0.895 → 1.401 tok/s, and code 0.892 → 1.401 tok/s. Each patched response had the same SHA-256 text hash as its saved baseline response. This checks greedy text for three prompts; it is not a full numerical equivalence test. See [Q8 benchmark records](raw/2026-09-24-integrated/q8-baseline.jsonl), [patched records](raw/2026-09-24-integrated/q8-ime.jsonl), and [response hashes](raw/2026-09-24-integrated/q8-accuracy.jsonl) and [code response](raw/2026-09-24-integrated/q8-code-accuracy.jsonl).

### M4 scale construction

With the Q8 patch held constant, an interleaved baseline → scale → scale → baseline test used 4B Q4_0, pp128/tg32, one repetition per process. Mean pp128 rose 9.058 → 9.360; tg32 stayed 2.317 → 2.319. The individual pp128 values were 9.047/9.068 baseline and 9.387/9.334 with the scale patch. [Raw kernel arms](raw/2026-09-24-integrated/).

The same interleaved order on the 2B mapped-head server gave:

| Prompt | Baseline MTP | M4 scale MTP | Accepted/drafted |
| --- | ---: | ---: | ---: |
| English | 6.944 | 7.066 | 83/130 |
| Chinese | 5.030 | 5.121 | 66/183 |

Both passes in each arm produced the same greedy hash for each prompt. The patch improved the measured verification workload but did not change draft acceptance. This is a two-pass single-stream result; concurrency 4/8 and stochastic sampling remain unmeasured. See [server records](raw/2026-09-24-integrated/scale-mtp-abba.jsonl).

## Vocabulary selection

The [public Chinese domain-map generator](../models/frspec/make-domain-map.py) reserves 3,256 unique IDs from the public Qwen Chinese README and SpaceMiT Chinese llama.cpp documentation, then fills the 32k head from the existing frequency ranking. Its map differs from the existing map in 1,217 IDs. The new GGUF was built separately from the same 2B MTP source; the public training text is not in this repository.

A two-pass original → new → new → original server comparison used held-out English, code, and Chinese prompts, CPU draft sampling, and 128 tokens:

| Prompt | Original map | Public Chinese map | Accepted/drafted |
| --- | ---: | ---: | ---: |
| English | 6.963 | 6.962 | 83/130 |
| Code | 5.960 | 6.011 | 76/153 |
| Chinese | 5.051 | 5.047 | 66/183 |

All output hashes matched. The code difference is small and the original arm drifted between passes; the new map did not improve Chinese acceptance or speed. Training-corpus token coverage of 100% did not predict held-out gain. Keep the new map as a reproducible candidate, not a deployment default. Dynamic vocabulary routing from [VocabTrim](https://arxiv.org/abs/2506.22694), [DynaSpec](https://arxiv.org/abs/2510.13847), and [SpecVocab](https://arxiv.org/abs/2602.13836) needs a stronger per-domain signal before adding model copies or routing overhead. See [map records](raw/2026-09-24-integrated/map-abba.jsonl).

## Cost-aware fallback experiment

The [experimental timing gate](../experiments/2026-09-24-cost-gate.patch) used a measured direct server rate supplied as SPINE_SPEC_DIRECT_TPS. It timed complete draft-plus-verification rounds, compared emitted tokens/s with 95% of direct throughput after 12 rounds, and disabled speculation when slower. It preserved greedy output hashes, but made a bad early decision on the mapped Chinese prompt. It is deliberately absent from apply-patches.sh and the final board build.

| Chinese 2B model | Direct | Fixed MTP | Timing gate | Existing acceptance gate |
| --- | ---: | ---: | ---: | ---: |
| Prefix 64k head | 5.087 | 3.736 | 4.246 | Previously about 4.26 |
| Mapped 32k head | about 5.09 | 5.117 | 4.409 | 4.409 |

For the mapped head, the first 12 timed rounds were only 3.891 tok/s, while the full fixed run reached 5.117; the timing gate disabled a beneficial mode. The existing acceptance gate waited longer but also disabled it. On the prefix head the timing gate improved fixed MTP by about 14%, but direct decoding remained faster and the existing gate already achieved similar throughput. [Raw results](raw/2026-09-24-integrated/cost-abba.jsonl), [mapped comparison](raw/2026-09-24-integrated/cost-mapped.jsonl), and [gate events](raw/2026-09-24-integrated/cost-gate-events.txt) show the decision. A future controller needs stable per-request exploration or re-enabling, not a one-way early threshold. [Learning to Draft](https://arxiv.org/abs/2603.01639) motivates optimizing full-cycle latency; the acceptance modification in [AdaSD](https://arxiv.org/abs/2512.11280) was not used because greedy output exactness is required here.

## Hybrid dispatch and long-context routes

The [OpenSolvers hybrid IME/RVV prototype](https://github.com/opensolvers/benchmarks/blob/main/ime/apply-hybrid.py) compiled and ran with SPACEMIT_HYBRID=1. In an interleaved two-pass 2B Q4_0 comparison, pp64 fell 22.763 → 21.529 and tg32 fell 5.149 → 2.006 tok/s. The script also keeps native and IME-tiled weight copies, increasing weight RAM. The hybrid change was removed from the final checkout. [Raw hybrid arms](raw/2026-09-24-integrated/).

The local 2B and 4B GGUF metadata both declare a 262,144-token maximum context, while the measured server used 8,192. With f16 attention K/V, their block count, KV heads, head length, and full-attention interval imply approximately 96/256 MiB of attention KV at 8k tokens for 2B/4B, and 192/512 MiB at 16k. This estimate excludes recurrent state, draft buffers, and allocator overhead. The exact metadata and calculation are [recorded here](raw/2026-09-24-integrated/gguf-context-metadata.txt). At one million tokens the same attention KV alone would be about 11.4/30.5 GiB, beyond the models' declared context and, for 4B, beyond this board's RAM.

[Windowed-MTP](https://arxiv.org/abs/2607.21535) targets much longer draft attention histories than the present 8k workload. [KVBuffer](https://arxiv.org/abs/2605.19049) addresses recurrent-state traffic; no such bottleneck was isolated in these board runs. [TreeWY](https://arxiv.org/abs/2608.20961) targets tree verification and state handling, while this server uses linear MTP drafts of at most three tokens and already has RS rollback. None was ported because the measured workload does not exercise their primary bottleneck. A long-context or tree workload with a measured bottleneck would be needed before implementation.

## Reproduce and limits

Run apply-patches.sh against a clean official-fork 5ad05d8 checkout with --frspec --lowacc --q8-ime1 --m4-scale, then build with the GCC 14, SpaceMiT backend, spert, and spine-tcm settings in [the integration guide](../README.md). The helper was tested from a fresh detached worktree with all four options, and the resulting changed files matched the final board checkout byte for byte. The Q8 and M4 flags can be selected independently; SPINE_SPEC_LOWACC defaults off.

These are small, fixed-prompt board measurements. The kernel A/B is stronger than an isolated inner-loop result, but it does not establish gains at concurrency 4/8, long contexts, other quantizations, or stochastic decoding.
