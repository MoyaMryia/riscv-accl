# GGUF preparation tools

Use the [model guide](../README.md) for artifact identity and source limits.
[Requirements.md](../../../Requirements.md) is the sole current acceptance reference.
These scripts keep the model recipe for the SpaceMiT X60. Supply the model files separately. This repository does not commit GGUF weights. Run the scripts from an official `spacemit-com/llama.cpp` checkout with the source patches applied. Set `LD_LIBRARY_PATH` as described in `spacemit/README.md`.

The [source and reproduction record](../REPRODUCIBILITY.md) separates the historical Unsloth artifacts from the new official-checkpoint recipe.
`reproduce-official.sh` requires fixed official input files and the recorded SpaceMiT source snapshot.
`record-reproduction.py` verifies input identities and records artifact hashes.
The complete official conversion ran on 2026-10-21 for both models. K1 inference remains pending.

## Structure check

`verify-artifact.py` compares two GGUFs. It checks the tensor names, shapes, and types.
It checks the tokenizer count, the token table digest, and the chat template digest.
It writes a JSON receipt. It exits with status 1 on a mismatch.

Use it after a new conversion, and compare the new file with the tested reference:

```bash
python3 spacemit/models/tools/verify-artifact.py \
  --reference models/Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf \
  --candidate lab/official-models/2B-conversion-r1/official-Q4_0-embQ4_0-dv64k.gguf \
  --gguf-py /path/to/llama.cpp/gguf-py \
  --output /tmp/structure-2b.json
```

The tool requires the `gguf` Python package. Use the converter environment.
The tool checks structure only. Add a K1 inference check for numeric behavior.

## Package check

`package-artifact.py` writes one archive with the model and its receipts.
It records the SHA-256 of each member and of the archive.
It refuses an existing target and an unexpected model digest.

```bash
python3 spacemit/models/tools/package-artifact.py \
  --gguf lab/official-models/2B-conversion-r1/official-Q4_0-embQ4_0-dv64k.gguf \
  --receipts lab/official-models/2B-conversion-r1 \
  --name qwen35-2b-official-r1 \
  --output lab/official-models/packages \
  --expect-sha256 <recorded digest>
```

## Fast Q4_0 weights

IME1 accelerates Q4_0, Q4_1, and Q4_K. The tied token embedding/output weight must also be Q4_0. Then the model stays on the accelerated path. Use `quantize-fast.sh` with a BF16 or Q8_0 source GGUF. BF16 avoids a second quantization:

```bash
/path/to/riscv-accl/spacemit/models/tools/quantize-fast.sh \
  ./build/bin/llama-quantize source.gguf models/Qwen3.5-2B-MTP-Q4_0-embQ4_0.gguf
```

The same command applies to the 4B base model with its output name. The command passes `--allow-requantize`, so quantized source GGUFs work. Input quantization quality still matters.

## Prefix draft head

For a 2B MTP model, use layer 24. For a 4B MTP model, use layer 32. The 64k head is the tested production choice. The 32k head is available for controlled comparisons.

```bash
python3 /path/to/riscv-accl/spacemit/models/tools/add-prefix-head.py \
  models/Qwen3.5-2B-MTP-Q4_0-embQ4_0.gguf \
  models/Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf \
  --layer 24 --rows 65536
```

The tool requires Q4_0 token embeddings. It refuses to overwrite an output. The packaged version matched the tested 2B and 4B 64k GGUFs byte-for-byte. SHA-256: 2B `56f0ddd90dfa0e2456af6cb4718ece419678d21a75d65e27353319b5e431a2fa`; 4B `0adf6cce5df53921606033c39a13fae2054543b78af0e7ff98860e86f078ac0f`.

## 4B MTP weights

The tested 4B base GGUF did not contain MTP tensors. Start with a local HF safetensors checkpoint that contains all 15 `mtp.*` tensors. `extract-mtp-safetensors.py` reads only these tensors from indexed or unindexed shards. Its output directory must not already exist.

```bash
python3 /path/to/riscv-accl/spacemit/models/tools/extract-mtp-safetensors.py \
  /path/to/Qwen3.5-4B-safetensors /tmp/mtp-4b
python3 /path/to/riscv-accl/spacemit/models/tools/add-mtp-4b.py \
  models/Qwen3.5-4B-Q4_0-embQ4_0.gguf \
  models/Qwen3.5-4B-MTP-Q4_0-embQ4_0.gguf /tmp/mtp-4b
python3 /path/to/riscv-accl/spacemit/models/tools/add-prefix-head.py \
  models/Qwen3.5-4B-MTP-Q4_0-embQ4_0.gguf \
  models/Qwen3.5-4B-MTP-Q4_0-embQ4_0-dv64k.gguf --layer 32 --rows 65536
```

The 4B assembler converts the BF16 MTP matrices to Q4_0. It adds 1 to the BF16 norm values before it saves F32 GGUF tensors. This matches the tested Qwen3.5 conversion. It refuses to overwrite an output.

The packaged 4B assembler matched the tested MTP GGUF byte-for-byte (SHA-256 `e575502912e015bd3eed928758736a31fd6a0fe5c59d3c49c2682f4569738b2a`). The integration notes record the verification of the tested reference hash.
