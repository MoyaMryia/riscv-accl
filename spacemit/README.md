# SpaceMiT X60 llama.cpp integration

Start with the [documentation guide](DOCS.md) for current status and work.
This page gives deployment commands; dated reports retain campaign evidence.

This directory packages the measured Qwen3.5 2B/4B work on MUSE-Pi-Pro (`musepipro-wg`). Source patches apply to the [official SpaceMiT llama.cpp fork](https://github.com/spacemit-com/llama.cpp) at commit `5ad05d8`. Patches 0001–0004 reproduce the tested `port-gdn` source at `6562c22`; patch 0005 adds the separately measured frequency-ranked 32k MTP prototype; patch 0006 adds an opt-in per-request low-acceptance fallback; patch 0007 adds Q8_0 IME1 kernels; patch 0008 improves the Q4_0 M4 scale path; optional patch 0009 adds the measured 256-bit RVV F16-KV prefill kernel; optional patch 0010 bounds the MTP draft KV history. For patches 0001–0005, we compared all 12 changed source files byte-for-byte with the board's experimental checkout; patch 0006 was built and benchmarked separately. The base optimization is not a replacement for upstream llama.cpp or a general RISC-V backend.

## Apply and build

Use a clean checkout of the official fork at `5ad05d8`. The helper checks the commit and working tree before applying patches. It changes the supplied checkout but does not create commits there.

```bash
git clone https://github.com/spacemit-com/llama.cpp.git ~/Projects/spacemit-llama/llama.cpp
cd ~/Projects/spacemit-llama/llama.cpp
git checkout 5ad05d8
/path/to/riscv-accl/spacemit/apply-patches.sh "$PWD" --m4-scale --rvv256
# Optional: --frspec for the mapped 32k head, --lowacc for the acceptance fallback,
# --q8-ime1 for Q8_0; the command above selects M4 Q4_0 and RVV F16-KV prefill,
# and --windowed-mtp for opt-in draft-KV windowing.
```

On the board, install the matching SpaceMiT `spert` runtime and use a compiler with the IME intrinsics. The measured build used GCC 14 and these key CMake settings (adjust paths to your local checkout):

```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER="$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/gcc-14" \
  -DCMAKE_CXX_COMPILER="$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14" \
  -DGGML_CPU_RISCV64_SPACEMIT=ON \
  -DSPERT_DIR="$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2" \
  -DGGML_OPENMP=OFF -DGGML_RV_ZBA=ON -DGGML_NATIVE=OFF \
  -DGGML_CPU_REPACK=OFF -DLLAMA_BUILD_TESTS=OFF \
  -DLLAMA_OPENSSL=OFF -DLLAMA_CURL=OFF \
  -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF
cmake --build build --target llama-server llama-bench llama-quantize -j4
```

The integrated comparison build disabled the optional UI to avoid repeated offline asset-download timeouts. This setting does not control the measured inference path. Before benchmarking, the TCM library **must** be in the runtime search path. Without it, `libspert` silently uses DDR buffers and decode throughput fell about 30% in our measurements:

```bash
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$PWD/build/bin"
```

## Prepare models

The repository contains no model weights. Start with legal local Qwen3.5 GGUFs: the 2B source needs its MTP tensors, while the tested 4B base GGUF required adding its MTP tensors from the corresponding local safetensors checkpoint. Use [the model tools](models/tools/README.md) to quantize the token embedding/output weight to Q4_0, add 4B MTP tensors where needed, and append the 65,536-row draft head. The tools reproduced the tested 2B and 4B prefix-head GGUFs and the 4B MTP GGUF byte-for-byte. [The frequency-ranked prototype](models/frspec/README.md) packages its map and model builder separately.

## Run

For the current document workflow, start a single-slot server in direct mode:

```bash
SPINE_FA_WIDE_TILE=1 ./build/bin/llama-server \
  -m "$HOME/Projects/spacemit-llama/models/Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf" \
  -t 4 -c 8192 --parallel 1 -b 32 -ub 32 -fa on \
  --host 127.0.0.1 --port 18085
```

Use the corresponding 4B model for 4B. The [document client](serve/README.md)
checks that prompt plus output fits the context. Optional speculative settings
below reproduce earlier workload-specific experiments.

For dedicated single-stream, copy-heavy editing with a 2B or 4B `-dv64k` model, the following is a measured throughput candidate for the short prompts described below. A later 4,096-token fixed-code test found repeatable direct/MTP token differences: the first generated mismatch was at index 179 for 2B and 303 for 4B. Use direct decoding when exact greedy agreement over arbitrary long code is required; the [lifecycle audit](reports/2026-09-27-completed-gates.md) gives the evidence and limits.

```bash
SPINE_SPEC_RS=1 ./build/bin/llama-server \
  -m models/Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf \
  -t 4 -c 8192 --parallel 1 -b 32 -ub 32 -fa on \
  --spec-type ngram-mod,draft-mtp \
  --spec-ngram-mod-n-match 16 --spec-ngram-mod-n-min 16 \
  --spec-ngram-mod-n-max 16 --spec-draft-n-max 3 \
  --no-spec-draft-backend-sampling
```

On six tested 2B greedy single-stream prompts, CPU-side MTP draft sampling (`--no-spec-draft-backend-sampling`) improved decode by 0.8–3.1% with identical outputs; the 4B one-pass gains were about 1%. The flag was not tested for stochastic sampling or high concurrency.

For a general server with up to eight concurrent requests, the default checkpoint rollback and speculative gate from patches 0003–0004 were measured with `--parallel 8 -c 16384 --spec-type draft-mtp --spec-draft-n-max 3`. They reached 13.85 aggregate tokens/s for 2B on the historical short-prompt workload; the single-stream RS setting lost throughput under high concurrency. On the later pinned 4B fixed-code test, MTP was 2.9% slower than direct at concurrency four and 2.4% slower at eight, with exact 128-token outputs. N-gram-first mode was only measured with one active stream. Choose speculative settings for the tested prompt family and output length; direct decoding is the supported choice for long-code token identity.

For repeated questions over one long document, use the [cached-document server and client](serve/README.md). They keep the document prefix stable and send `"cache_prompt": true` to one server slot. The first question pays the cold prefill cost; later changed questions reused roughly 8k–16k tokens in the [shared-document tests](reports/2026-09-29-shared-document-cache.md), with much shorter first-token latency. A warm answer can differ from a cold one, so the workflow does not promise exact token identity. The earlier 2,048-token identical-prefix baseline is in the [lifecycle report](reports/2026-09-25-lifecycle.md).

After applying optional patch 0006, set `SPINE_SPEC_LOWACC=1` on a dedicated single-stream server to stop drafting for the rest of a request when a 12-step window yields fewer than nine accepted draft tokens. It resets for each new request. On the measured low-acceptance Chinese prompt this raised 2B decode from 3.59 to 4.26 tokens/s and 4B from 1.69 to 1.92, with identical greedy output. English, code, and three combined n-gram/MTP prompts stayed within run-to-run noise. The switch is opt-in because six prompts do not justify changing the general default; the direct-decoding ceiling inside an RS-configured server remains lower than a separately configured direct server.

## Integrated K1 kernel result

On the board, optional Q8_0 IME1 patch 0007 raised 4B Q8_0 prefill from 1.117 to 7.472 tokens/s and decode from 0.866 to 1.349 tokens/s. Greedy English, Chinese, and code response hashes matched the saved baseline. Q4_0 remained faster overall. Optional M4 patch 0008 raised 4B Q4_0 prefill from 9.058 to 9.360 tokens/s and 2B mapped-head MTP from 6.944 to 7.066 tokens/s in English and 5.030 to 5.121 in Chinese, with matched hashes in interleaved runs.

Use --q8-ime1 when serving Q8_0, --m4-scale when Q4_0 prefill or small speculative verification matters, and --rvv256 for the opt-in 256-bit wide-head RVV attention kernel. The optional --windowed-mtp patch adds `SPINE_MTP_WINDOW=2048` to bound only the draft cache. At 12k, it saved 68.5/135.3 MiB peak RSS for 2B/4B with exact 128-token hashes against full-history MTP; its speed effect is based on one long pair per model and still needs fixed replication, and MTP is not exact for the separate long-code workload. After building with --rvv256, set `SPINE_FA_WIDE_TILE=1` for the tested Qwen3.5 F16-KV models. The new public Chinese map did not improve held-out acceptance; the experimental timing gate and hybrid IME/RVV dispatch regressed at least one important workload and are not part of the helper. The full A/B data, source links, and limits are in [the integrated K1 report](reports/2026-09-24-integrated-k1.md).

## Evidence and scope

- [Historical 2B/4B short-prompt baseline](reports/2026-09-21-final.md): 2B `llama-bench` tg128 5.19 tokens/s and pp128 22.07 tokens/s; 4B tg128 2.30 and pp128 9.04; model and runtime details.
- [Frequency-ranked MTP experiment](reports/2026-09-23-frspec.md): mapped 32k head improved the three tested prompts versus a prefix 64k head, but direct decoding was faster on the Chinese prompt.
- [N-gram plus MTP experiment](reports/2026-09-24-ngram.md): 2B near-copy C++ editing improved from 7.994 to about 10.36 decode tokens/s with a full 16-token n-gram match; Python edit and prose were effectively tied. The 4B C++ result improved 3.390 to 3.634 tokens/s in one pass.
- [Speculative settings sweep](reports/2026-09-24-spec-sweep.md) rules out longer n-gram bursts and a single global MTP confidence threshold on the tested prompts.
- [Adaptive low-acceptance fallback](reports/2026-09-24-lowacc.md) records paired 2B/4B runs and reset behavior.
- [CPU-side MTP draft sampling](reports/2026-09-24-cpu-sampling.md) records the small measured gain from the existing sampler flag.
- [Mapped 32k head plus CPU draft sampling](reports/2026-09-24-mapped-cpu-sampling.md) records a two-prompt, same-model A/B on the K1, with raw hashes and direct controls.
- [K1 research scan and next measurements](reports/2026-09-24-research-next.md) ranks papers and X60 repositories against the project's measured bottlenecks.
- [Inference lifecycle baseline](reports/2026-09-25-lifecycle.md) records client-observed TTFT, direct prefill/decode curves through 12k for both sizes, memory jitter, and KV overhead. The [completed board gates](reports/2026-09-27-completed-gates.md) measure the activated RVV F16 prefill gain, long generation, concurrency, windowed MTP, KV compression, OpenCL rejection, and page-gather result. The integrated board build contains the opt-in RVV patch; set `SPINE_FA_WIDE_TILE=1` for the tested Qwen3.5 F16-KV models.
- [Long-prefill research scan](reports/2026-09-28-long-prefill-research.md) ranks same-process cache reuse, relevant-span retrieval, and 256-bit RVV attention work for the measured 32k cold-prompt bottleneck.
- [Resumed long-context measures](reports/2026-09-27-resumed-measures.md) adds audited 2B/4B actual 16k RVV pairs, a completed 2B 32k feasibility request, the matched Q4_0/Q8_0 weight comparison, 512-token 4B KV comparison, speculative exactness diagnostics, and page-gather telemetry.
- [Local verification of archived measurements](reports/2026-09-28-local-verification.md) reproduces the results matrix from the raw records, puts Welch intervals on the 1.8–3.3% small-effect claims, and fits the 32k microbatch scaling.
- [Benchmark runner](bench/README.md) freezes those prompt families and reports response hashes. The archived reports retain their original board-local paths and historical statements; use this directory for the integrated reproduction steps.

These are measured results on one X60 board and a small set of prompts. The copy-heavy n-gram setting and corpus-dependent 32k map are experimental choices, not universal defaults.
