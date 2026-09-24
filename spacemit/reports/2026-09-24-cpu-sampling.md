# CPU-side MTP draft sampling on SpaceMiT X60

Date: 2026-09-24. The official SpaceMiT fork at `6562c22`, plus the opt-in low-acceptance patch with `SPINE_SPEC_LOWACC=0`, was used for both sides of this comparison. The server's default backend draft sampler was compared with `--no-spec-draft-backend-sampling`; no source, model, or other runtime setting changed. The flag uses the existing CPU sampler for MTP draft selection. The mechanism behind the gain was not profiled.

All runs used Qwen3.5 Q4_0 MTP `-dv64k` GGUFs on `musepipro-wg`, spine-tcm in `LD_LIBRARY_PATH`, `SPINE_SPEC_RS=1`, four threads, context 8192, one slot, batch/microbatch 32, flash attention, MTP draft maximum 3, `temperature=0`, seed 42, and `cache_prompt=false`. The n-gram combination used match/min/max 16. Each setting started a fresh server. All paired outputs and draft acceptance counts matched exactly.

Two-run means of server decode tokens/s for 2B:

| Mode and prompt | Backend sampling (default) | CPU sampling | Change |
| --- | ---: | ---: | ---: |
| MTP, English (128 tokens) | 6.486 | 6.671 | +2.85% |
| MTP, code (128) | 5.702 | 5.872 | +2.97% |
| MTP, Chinese (128) | 3.585 | 3.695 | +3.06% |
| N-gram + MTP, C++ near-copy (160) | 10.366 | 10.453 | +0.84% |
| N-gram + MTP, Python edit (160) | 6.981 | 7.149 | +2.41% |
| N-gram + MTP, prose (160) | 5.219 | 5.353 | +2.56% |

For 4B MTP only, one pass of English/code/Chinese moved **3.348/2.829/1.693 → 3.390/2.868/1.711 tokens/s** (about +1.1–1.4%). These smaller 4B differences need repeated confirmation before treating them as stable.

The flag did not add a meaningful gain after the low-acceptance gate disabled drafting on Chinese: 2B 4.264 versus 4.263 tokens/s with the gate alone; 4B 1.928 versus 1.924. This is expected because most of that request then uses direct decoding. Output hashes still matched.

## Reproduce and scope

Use `spacemit/bench/bench-server.py` with `--draft-backend-sampling on` or `off`, the same model, and `--modes mtp --prompt-set frspec --n-predict 128`. For the combined mode use `--modes combined --prompt-set ngram --ngram-min 16 --ngram-max 16 --n-predict 160`. Keep `SPINE_SPEC_RS=1` and the TCM library path as in the integration guide. The new [raw JSONL records](raw/2026-09-24-sampling/) and the [control records](raw/2026-09-24-lowacc/) back the table.

After committing the fallback as `f3e71c9` on the board branch `codex/lowacc-fallback` and rebuilding its normal `~/Projects/spacemit-llama/build/bin/llama-server`, a Chinese-then-English same-server smoke test with both `SPINE_SPEC_LOWACC=1` and CPU draft sampling measured 4.271 and 6.702 tokens/s, respectively, with the expected hashes. The record is `raw/2026-09-24-sampling/deployed-board.jsonl`.

This is a candidate flag for dedicated greedy single-stream workloads on this board. Stochastic sampling and high concurrency were not measured; neither is covered by the recommendation.
