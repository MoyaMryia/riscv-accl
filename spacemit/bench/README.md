# X60 server benchmark runner

`bench-server.py` starts the patched `llama-server` once per speculative mode, sends greedy completion requests, and writes one JSON record per result. It checks that all modes on the same model produce identical response text for each prompt. The recorded `tps` is the server's decode rate (`timings.predicted_per_second`), not end-to-end throughput. Server stdout and stderr go to `--log-dir`.

The C++ near-copy prompt includes `fixtures/ngram-mod.cpp`, taken from `common/ngram-mod.cpp` in the official llama.cpp fork at base commit `5ad05d8` (MIT license). The fixture freezes the prompt across subsequent upstream edits. The Python edit and prose prompts are embedded in the runner. The FR-Spec set uses English, code, and Chinese prompts.

On the MUSE-Pi-Pro, after applying the patches and building the official fork:

```bash
cd ~/Projects/spacemit-llama
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$PWD/spert/spine-runtime.riscv64.0.6.2/lib:$PWD/build/bin"
export SPINE_SPEC_RS=1
python3 /path/to/riscv-accl/spacemit/bench/bench-server.py \
  --server "$PWD/build/bin/llama-server" \
  --model "$PWD/models/Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf" \
  --modes mtp combined --prompt-set ngram --ngram-min 16 \
  --output /tmp/ngram-2b.jsonl --log-dir /tmp
```

Use the analogous 4B MTP GGUF for 4B measurements. The default prompt set has `cpp_edit`, `python_edit`, and `prose`. For the frequency-ranked model use `--prompt-set frspec --modes plain mtp` and the mapped 32k GGUF. Run models separately, because output hashes are only compared within one invocation. The runner fixes `-t 4 -c 8192 --parallel 1 -b 32 -ub 32 -fa on`, `temperature=0`, seed 42, and `cache_prompt=false`; by default it requests 160 tokens. Pass `--n-predict 128` for the FR-Spec comparison.

These commands reproduce the configuration and prompt family, but token rates can vary with board load and run order. The archived results are in `../reports/2026-09-23-frspec.md` and `../reports/2026-09-24-ngram.md`. The general single-stream recommendation is based on a near-copy C++ task; do not infer a universal gain from it.
