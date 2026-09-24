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
