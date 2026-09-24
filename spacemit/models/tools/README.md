# GGUF preparation tools

These scripts preserve the model recipe used on the SpaceMiT X60. Supply model files separately; no GGUF weights are committed here. Run from an official `spacemit-com/llama.cpp` checkout with the source patches applied, and set `LD_LIBRARY_PATH` as described in `spacemit/README.md`.

## Fast Q4_0 weights

IME1 accelerates Q4_0, Q4_1, and Q4_K. The tied token embedding/output weight must also be Q4_0 to stay on the accelerated path. Use `quantize-fast.sh` with a BF16 or Q8_0 source GGUF (BF16 avoids a second quantization):

```bash
/path/to/riscv-accl/spacemit/models/tools/quantize-fast.sh \
  ./build/bin/llama-quantize source.gguf models/Qwen3.5-2B-MTP-Q4_0-embQ4_0.gguf
```

The same command applies to the 4B base model with its corresponding output name. `--allow-requantize` is passed so quantized source GGUFs work; input quantization quality still matters.

## Prefix draft head

For a 2B MTP model, use layer 24. For a 4B MTP model, use layer 32. The 64k head is the tested production choice; 32k is available for controlled comparisons.

```bash
python3 /path/to/riscv-accl/spacemit/models/tools/add-prefix-head.py \
  models/Qwen3.5-2B-MTP-Q4_0-embQ4_0.gguf \
  models/Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf \
  --layer 24 --rows 65536
```

The tool requires Q4_0 token embeddings and refuses to overwrite an output. The packaged version reproduced the tested 2B and 4B 64k GGUFs byte-for-byte. SHA-256: 2B `56f0ddd90dfa0e2456af6cb4718ece419678d21a75d65e27353319b5e431a2fa`; 4B `0adf6cce5df53921606033c39a13fae2054543b78af0e7ff98860e86f078ac0f`.

## 4B MTP weights

The tested 4B base GGUF did not contain MTP tensors. `extract-mtp-safetensors.py` and `add-mtp-4b.py` assemble them from a local BF16 safetensors checkpoint before adding the prefix head. See those scripts' help and `spacemit/README.md` for the order of operations.
