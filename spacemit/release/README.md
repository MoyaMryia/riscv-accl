# K1 infrastructure release

This package reproduces the measured Qwen3.5 2B/4B infrastructure source on
SpaceMiT's llama.cpp revision
`a990751d55a4c54acf2bb77d44282c2093652359`. It includes the integrated wide RVV
F16 attention path and the opt-in Q4_0 IME staging policy. It retains complete
prompts, model weights, quantization and output vocabulary.

The baseline profile enables the existing RVV attention and uses routing 0;
the optimized profile uses the same attention and routing 3. Their comparison
measures incremental routing, matching the October 6 replication. Historical
generic-versus-RVV comparisons use a different baseline; do not multiply or
add those percentages.

Routing remains opt-in: performance and tested output identity are established,
while the overall absolute useful-answer gate remains open due to errors also
present in the baseline. MTP, hybrid SSM, compact layouts and the unsuccessful
K32 specialization are not enabled by this package. ARM/x86 comparison is
outside the release scope, as requested by the user.

## Install and build

Use a separate clean checkout on the K1 board. The older `apply-patches.sh`
targets `5ad05d8` and is a historical package; do not apply both packages to one
checkout.

```bash
git clone https://github.com/spacemit-com/llama.cpp spacemit-release-source
git -C spacemit-release-source checkout --detach a990751d55a4c54acf2bb77d44282c2093652359
python3 /path/to/riscv-accl/spacemit/release/apply-release.py spacemit-release-source
bash /path/to/riscv-accl/spacemit/release/build.sh spacemit-release-source spacemit-release-build
```

The patch helper checks the exact clean revision, original source hashes and
patch checksum, then requires all patched files to match the measured source.
The build blocks with a four-hour compilation limit, four build workers, GCC14,
IME1/SPERT, GPU off by default and the recorded CPU settings. Dependencies are
external: install the matching vendor compiler, SPERT and TCM runtime first.
The board defaults are:

- `K1_CC=$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/gcc-14`
- `K1_CXX=$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14`
- `K1_SPERT_DIR=$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2`
- `K1_TCM_DIR=$HOME/Projects/llm-bench/.toolchain/spine-tcm`

Override these variables for another installation. Keep the TCM shim and SPERT
libraries in the runtime search path; missing runtime dependencies change the
tested execution environment. The package does not claim physical TCM placement.

## Run local inference

Supply a legal local model from the [manifest](manifest.json). The exact tested
GGUF hashes are pinned; model preparation is described in the
[integration guide](../README.md). No weights or credentials are distributed.
Presence of MTP tensors does not enable speculative decoding.

```bash
python3 /path/to/riscv-accl/spacemit/release/run-server.py \
  --server /path/to/spacemit-release-build/bin/llama-server \
  --model /path/to/Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf \
  --runtime "$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:/path/to/spacemit-release-build/bin" \
  --profile baseline
```

Use `--profile optimized` for opt-in routing 3. Repeat with the manifest's 4B
model. Both profiles use four workers, batch/ubatch32, F16 KV, context6144,
one server slot, GPU layers0 and localhost port8080. The launcher verifies the
model hash, clears inherited experimental `SPINE_` settings, and starts plain
direct decoding. The local server accepts OpenAI-compatible chat requests.
It needs no cloud API. Benchmark requests explicitly use seed42, temperature0,
thinking off and zero prompt reuse; the user can supply these chat settings.

## Verification and evidence

The offline clean-archive patch round trip verified all 3,266 pinned source
files and reproduced all three measured patched-file hashes. Reapplication is
rejected. See [clean-apply verification](../reports/raw/release-20261007/clean-apply-verification.json).

Fresh board build and complete-answer verification is running as
`k1-release-check-20261007-125712` through direct SSH `musepipro`, with board and
local collector tmux sessions and a quiet 30-minute monitor. It builds from a
clean checkout, compares 104 production graph cases per routing arm, and runs
four cold naturally completed Unicode code answers across both models. Each
answer must pass 106 held-out checks and each pair must match exactly. This is
a release smoke test, not a new statistical performance or general quality claim.
The final release is published only after these checks pass.

```bash
python3 spacemit/bench/start-k1-release-check.py --board musepipro
python3 spacemit/release/test-release.py
```

Existing matched performance, full-document quality limits and negative results
are in the [submission report](../reports/SUBMISSION-REPORT.md) and
[evidence appendix](../reports/SUBMISSION-EVIDENCE.md). Raw large generated
binary dumps and archives stay in the measurement workspace; Git contains
source, text records and checksum receipts. Reproduce the runner to regenerate
them or obtain the retained files before running strict full-artifact verifiers.
