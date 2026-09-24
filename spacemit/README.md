# SpaceMiT X60 llama.cpp integration

This directory packages the measured Qwen3.5 2B/4B work on MUSE-Pi-Pro (`musepipro-wg`). Source patches apply to the [official SpaceMiT llama.cpp fork](https://github.com/spacemit-com/llama.cpp) at commit `5ad05d8`. Patches 0001–0004 reproduce the tested `port-gdn` source at `6562c22`; patch 0005 adds the separately measured frequency-ranked 32k MTP prototype; patch 0006 adds an opt-in per-request low-acceptance fallback. For patches 0001–0005, we compared all 12 changed source files byte-for-byte with the board's experimental checkout; patch 0006 was built and benchmarked separately. The base optimization is not a replacement for upstream llama.cpp or a general RISC-V backend.

## Apply and build

Use a clean checkout of the official fork at `5ad05d8`. The helper checks the commit and working tree before applying patches. It changes the supplied checkout but does not create commits there.

```bash
git clone https://github.com/spacemit-com/llama.cpp.git ~/Projects/spacemit-llama/llama.cpp
cd ~/Projects/spacemit-llama/llama.cpp
git checkout 5ad05d8
/path/to/riscv-accl/spacemit/apply-patches.sh "$PWD"
# Add --frspec for the mapped 32k head, --lowacc for the acceptance fallback, or both.
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
  -DLLAMA_OPENSSL=OFF -DLLAMA_CURL=OFF
cmake --build build --target llama-server llama-bench llama-quantize -j4
```

The board's existing build used `LLAMA_BUILD_UI=ON` and `LLAMA_USE_PREBUILT_UI=OFF`; these settings do not control the measured inference path. Before benchmarking, the TCM library **must** be in the runtime search path. Without it, `libspert` silently uses DDR buffers and decode throughput fell about 30% in our measurements:

```bash
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$PWD/build/bin"
```

## Prepare models

The repository contains no model weights. Start with legal local Qwen3.5 GGUFs: the 2B source needs its MTP tensors, while the tested 4B base GGUF required adding its MTP tensors from the corresponding local safetensors checkpoint. Use [the model tools](models/tools/README.md) to quantize the token embedding/output weight to Q4_0, add 4B MTP tensors where needed, and append the 65,536-row draft head. The tools reproduced the tested 2B and 4B prefix-head GGUFs and the 4B MTP GGUF byte-for-byte. [The frequency-ranked prototype](models/frspec/README.md) packages its map and model builder separately.

## Run

For dedicated single-stream, copy-heavy editing with a 2B or 4B `-dv64k` model, the measured candidate is:

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

For a general server with up to eight concurrent requests, use the default checkpoint rollback and speculative gate from patches 0003–0004: omit `SPINE_SPEC_RS=1`, use `--parallel 8 -c 16384`, and start with `--spec-type draft-mtp --spec-draft-n-max 3`. That configuration was measured at 13.85 aggregate tokens/s for 2B at concurrency 8; the single-stream RS setting lost throughput under high concurrency. N-gram-first mode was only measured with one active stream.

After applying optional patch 0006, set `SPINE_SPEC_LOWACC=1` on a dedicated single-stream server to stop drafting for the rest of a request when a 12-step window yields fewer than nine accepted draft tokens. It resets for each new request. On the measured low-acceptance Chinese prompt this raised 2B decode from 3.59 to 4.26 tokens/s and 4B from 1.69 to 1.92, with identical greedy output. English, code, and three combined n-gram/MTP prompts stayed within run-to-run noise. The switch is opt-in because six prompts do not justify changing the general default; the direct-decoding ceiling inside an RS-configured server remains lower than a separately configured direct server.

## Evidence and scope

- [Final 2B/4B baseline and optimization report](reports/2026-09-21-final.md): 2B `llama-bench` tg128 5.19 tokens/s and pp128 22.07 tokens/s; 4B tg128 2.30 and pp128 9.04; model and runtime details.
- [Frequency-ranked MTP experiment](reports/2026-09-23-frspec.md): mapped 32k head improved the three tested prompts versus a prefix 64k head, but direct decoding was faster on the Chinese prompt.
- [N-gram plus MTP experiment](reports/2026-09-24-ngram.md): 2B near-copy C++ editing improved from 7.994 to about 10.36 decode tokens/s with a full 16-token n-gram match; Python edit and prose were effectively tied. The 4B C++ result improved 3.390 to 3.634 tokens/s in one pass.
- [Speculative settings sweep](reports/2026-09-24-spec-sweep.md) rules out longer n-gram bursts and a single global MTP confidence threshold on the tested prompts.
- [Adaptive low-acceptance fallback](reports/2026-09-24-lowacc.md) records paired 2B/4B runs and reset behavior.
- [CPU-side MTP draft sampling](reports/2026-09-24-cpu-sampling.md) records the small measured gain from the existing sampler flag.
- [Benchmark runner](bench/README.md) freezes those prompt families and reports response hashes. The archived reports retain their original board-local paths and historical statements; use this directory for the integrated reproduction steps.

These are measured results on one X60 board and a small set of prompts. The copy-heavy n-gram setting and corpus-dependent 32k map are experimental choices, not universal defaults.
