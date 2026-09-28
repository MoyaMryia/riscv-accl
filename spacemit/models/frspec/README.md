# Frequency-ranked 32k MTP draft head (experimental)

This is the Qwen3.5-2B experiment from 2026-09-23. It follows the draft-vocabulary idea in [FR-Spec](https://aclanthology.org/2025.acl-long.198/): the verifier remains full-vocabulary, while a compact MTP head proposes frequent token IDs. Apply `patches/0005-frequency-ranked-d2t.patch` after the four official-fork optimization patches.

The input token stream in `corpus-token-ids.txt` contains 809,481 IDs produced with the exact 2B tokenizer from public llama.cpp docs/tools and the project's Chinese benchmark notes. `make-map.py` ranks observed IDs by frequency, includes IDs 248000–248319, then fills the remaining 32,768 entries in ascending ID order. It deterministically writes `d2t-map32k.bin` (SHA-256 `19e1f1ca60967da53d1d5c278232960f0ff72ccf8c71d76888a9837f164a23f9`).

From the repository root:

```bash
python3 spacemit/models/frspec/make-map.py
python3 spacemit/models/frspec/add-d2t-2b.py \
  /path/to/Qwen3.5-2B-MTP-Q4_0-embQ4_0.gguf \
  /path/to/Qwen3.5-2B-MTP-Q4_0-embQ4_0-d2t32k.gguf
```

The producer requires Q4_0 token embeddings with width 2048 and refuses to overwrite an output file. Its output was verified byte-for-byte against the tested 1,143,639,552-byte GGUF (SHA-256 `1295b9835e97181274a40d874486b3ce915cd43583c431617d87dfd48993d563`). Keep that GGUF outside Git.

See `spacemit/reports/2026-09-23-frspec.md` for measured acceptance and speed. The map is corpus-dependent and is not a default model choice.

## Public Chinese domain-map candidate

`make-domain-map.py` can reserve up to a chosen number of 32k rows for tokens in one or more domain corpora, then fill the remaining rows from the original 809,481-token corpus. It always includes token IDs 248000–248319. The candidate `d2t-map32k-public-cn.bin` uses `--domain-quota 8192`; the public training text contained only 3,256 distinct IDs, so it reserved all of them. The candidate map has SHA-256 `6c197c45ff811caa57e9015432590a8c4e51be2b3f6fbc3d3b8b5ad5223494cb` and differs from the original map in 1,217 IDs. Training-corpus coverage rose from 90.29% to 100%; that is not a held-out acceptance or speed result.

The corpus consists of [Qwen's public Chinese README](https://github.com/QwenLM/Qwen/blob/main/README_CN.md) (raw-file SHA-256 `1b83f5f8426e25c4e4b9110e926c95c59bf739173422214d57327a4f5cbf10ba`) followed by [SpaceMiT's public Chinese llama.cpp documentation](https://github.com/spacemit-com/docs-ai/blob/main/zh/compute_stack/ai_compute_stack/llama.cpp.md) (raw-file SHA-256 `4243eac1574b16f3f3908a3186449b16e2dd0e67c7a33b7ec019698c204cb57c`). These files were concatenated and tokenized with the exact 2B GGUF via `llama-tokenize --ids --no-bos --no-parse-special -f`; the token-ID sequence SHA-256 was `561b93ccfb8e06887b5a1f01c04db8b426cba7e562e0351d5b5471b93121e75f`. The source text and reconstructable ID sequence are not stored in this repository.

Rebuild from a token-ID list produced the same way:

```bash
python3 spacemit/models/frspec/make-domain-map.py \
  --domain-ids /path/to/public-cn-token-ids.txt --domain-quota 8192 \
  --output spacemit/models/frspec/d2t-map32k-public-cn.bin
python3 spacemit/models/frspec/add-d2t-2b.py \
  /path/to/Qwen3.5-2B-MTP-Q4_0-embQ4_0.gguf \
  /path/to/Qwen3.5-2B-MTP-Q4_0-embQ4_0-d2t32k-public-cn.gguf \
  --map spacemit/models/frspec/d2t-map32k-public-cn.bin
```

The new GGUF is a separate candidate (SHA-256 d0179857f46fe799c59a0cf27f22dd5175b38a2856c53295fc736bb72cd7c38b); it does not replace the measured original 32k map. A two-pass held-out server A/B found identical English, code, and Chinese draft acceptance and output hashes. Chinese throughput was 5.051 tokens/s with the original map and 5.047 with this public-corpus map; see the integrated K1 report. Training-corpus coverage did not produce a held-out gain.
