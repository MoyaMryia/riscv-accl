# Frequency-ranked 32k MTP draft head (experimental)

This experiment uses Qwen3.5-2B and it dates from 2026-09-23. It follows the draft-vocabulary idea in [FR-Spec](https://aclanthology.org/2025.acl-long.198/). The verifier keeps the full vocabulary. A compact MTP head proposes frequent token IDs. Apply `archive/patches-5ad05d8/patches/0005-frequency-ranked-d2t.patch` after the four official-fork optimization patches.

The input token stream in `corpus-token-ids.txt` contains 809,481 IDs. The exact 2B tokenizer produced these IDs from public llama.cpp docs/tools and the project Chinese benchmark notes. `make-map.py` ranks observed IDs by frequency. It includes IDs 248000–248319, then fills the remaining 32,768 entries in ascending ID order. The script writes `d2t-map32k.bin` deterministically (SHA-256 `19e1f1ca60967da53d1d5c278232960f0ff72ccf8c71d76888a9837f164a23f9`).

From the repository root:

```bash
python3 spacemit/models/frspec/make-map.py
python3 spacemit/models/frspec/add-d2t-2b.py \
  /path/to/Qwen3.5-2B-MTP-Q4_0-embQ4_0.gguf \
  /path/to/Qwen3.5-2B-MTP-Q4_0-embQ4_0-d2t32k.gguf
```

The producer requires Q4_0 token embeddings with width 2048. It refuses to overwrite an output file. Its output matched the tested 1,143,639,552-byte GGUF byte-for-byte (SHA-256 `1295b9835e97181274a40d874486b3ce915cd43583c431617d87dfd48993d563`). Keep that GGUF outside Git.

See `spacemit/reports/2026-09-23-frspec.md` for measured acceptance and speed. The map depends on the corpus. It is not a default model choice.

## Public Chinese domain-map candidate

`make-domain-map.py` can reserve a chosen number of 32k rows for tokens in one or more domain corpora. It then fills the remaining rows from the original 809,481-token corpus. It always includes token IDs 248000–248319. The candidate `d2t-map32k-public-cn.bin` uses `--domain-quota 8192`. The public training text contained only 3,256 distinct IDs, so the tool reserved all of them. The candidate map has SHA-256 `6c197c45ff811caa57e9015432590a8c4e51be2b3f6fbc3d3b8b5ad5223494cb`. It differs from the original map in 1,217 IDs. Training-corpus coverage rose from 90.29% to 100%. That result is not a held-out acceptance or speed result.

The corpus contains [Qwen's public Chinese README](https://github.com/QwenLM/Qwen/blob/main/README_CN.md) (raw-file SHA-256 `1b83f5f8426e25c4e4b9110e926c95c59bf739173422214d57327a4f5cbf10ba`) and then [SpaceMiT's public Chinese llama.cpp documentation](https://github.com/spacemit-com/docs-ai/blob/main/zh/compute_stack/ai_compute_stack/llama.cpp.md) (raw-file SHA-256 `4243eac1574b16f3f3908a3186449b16e2dd0e67c7a33b7ec019698c204cb57c`). These files were concatenated and tokenized with the exact 2B GGUF. The command was `llama-tokenize --ids --no-bos --no-parse-special -f`. The token-ID sequence SHA-256 was `561b93ccfb8e06887b5a1f01c04db8b426cba7e562e0351d5b5471b93121e75f`. This repository does not store the source text or the reconstructable ID sequence.

To rebuild, use a token-ID list that you produced the same way:

```bash
python3 spacemit/models/frspec/make-domain-map.py \
  --domain-ids /path/to/public-cn-token-ids.txt --domain-quota 8192 \
  --output spacemit/models/frspec/d2t-map32k-public-cn.bin
python3 spacemit/models/frspec/add-d2t-2b.py \
  /path/to/Qwen3.5-2B-MTP-Q4_0-embQ4_0.gguf \
  /path/to/Qwen3.5-2B-MTP-Q4_0-embQ4_0-d2t32k-public-cn.gguf \
  --map spacemit/models/frspec/d2t-map32k-public-cn.bin
```

The new GGUF is a separate candidate (SHA-256 d0179857f46fe799c59a0cf27f22dd5175b38a2856c53295fc736bb72cd7c38b). It does not replace the measured original 32k map. A two-pass held-out server A/B found identical draft acceptance and output hashes for English, code, and Chinese. Chinese throughput was 5.051 tokens/s with the original map. It was 5.047 tokens/s with this public-corpus map. See the integrated K1 report. Training-corpus coverage did not produce a held-out gain.
