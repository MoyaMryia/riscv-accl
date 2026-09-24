#!/usr/bin/env python3
"""Extract only Qwen3.5-4B MTP BF16 tensors from local safetensors shards."""

import argparse
import json
import math
import struct
from pathlib import Path

EXPECTED = (
    'mtp.fc.weight',
    'mtp.norm.weight',
    'mtp.pre_fc_norm_embedding.weight',
    'mtp.pre_fc_norm_hidden.weight',
    'mtp.layers.0.input_layernorm.weight',
    'mtp.layers.0.post_attention_layernorm.weight',
    'mtp.layers.0.self_attn.q_proj.weight',
    'mtp.layers.0.self_attn.k_proj.weight',
    'mtp.layers.0.self_attn.v_proj.weight',
    'mtp.layers.0.self_attn.q_norm.weight',
    'mtp.layers.0.self_attn.k_norm.weight',
    'mtp.layers.0.self_attn.o_proj.weight',
    'mtp.layers.0.mlp.gate_proj.weight',
    'mtp.layers.0.mlp.up_proj.weight',
    'mtp.layers.0.mlp.down_proj.weight',
)


def read_header(path):
    with path.open('rb') as stream:
        prefix = stream.read(8)
        if len(prefix) != 8:
            raise ValueError(f'invalid safetensors header: {path}')
        size, = struct.unpack('<Q', prefix)
        if size > 64 * 1024 * 1024:
            raise ValueError(f'implausible safetensors header length: {path}')
        raw = stream.read(size)
        if len(raw) != size:
            raise ValueError(f'truncated safetensors header: {path}')
    return json.loads(raw), 8 + size


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkpoint_dir', type=Path, help='local HF safetensors checkpoint directory')
    parser.add_argument('output_dir', type=Path, help='new directory for BF16 blobs and meta.json')
    args = parser.parse_args()
    root = args.checkpoint_dir.resolve()
    out = args.output_dir.resolve()
    if not root.is_dir():
        parser.error(f'checkpoint directory does not exist: {root}')
    if out.exists():
        parser.error(f'output directory already exists: {out}')

    index_path = root / 'model.safetensors.index.json'
    if index_path.exists():
        weight_map = json.loads(index_path.read_text())['weight_map']
        missing = set(EXPECTED) - set(weight_map)
        if missing:
            raise ValueError(f'MTP tensors missing from index: {sorted(missing)}')
        locations = {name: (root / weight_map[name]).resolve() for name in EXPECTED}
    else:
        locations = {}
        for shard in sorted(root.glob('*.safetensors')):
            header, _ = read_header(shard)
            for name in EXPECTED:
                if name in header:
                    if name in locations:
                        raise ValueError(f'duplicate tensor: {name}')
                    locations[name] = shard.resolve()
        missing = set(EXPECTED) - set(locations)
        if missing:
            raise ValueError(f'MTP tensors missing from shards: {sorted(missing)}')

    for name, path in locations.items():
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f'shard outside checkpoint directory: {name}: {path}')

    out.mkdir(parents=True)
    meta = {}
    headers = {path: read_header(path) for path in set(locations.values())}
    for name in EXPECTED:
        path = locations[name]
        header, data_start = headers[path]
        info = header[name]
        shape = info['shape']
        start, end = info['data_offsets']
        if info['dtype'] != 'BF16' or not shape or any(n <= 0 for n in shape):
            raise ValueError(f'expected BF16 tensor with nonempty shape: {name}')
        if start < 0 or end - start != math.prod(shape) * 2 or data_start + end > path.stat().st_size:
            raise ValueError(f'invalid data span for {name}')
        destination = out / (name + '.bin')
        with path.open('rb') as source, destination.open('xb') as target:
            source.seek(data_start + start)
            remaining = end - start
            while remaining:
                chunk = source.read(min(remaining, 8 * 1024 * 1024))
                if not chunk:
                    raise EOFError(f'truncated tensor: {name}')
                target.write(chunk)
                remaining -= len(chunk)
        meta[name] = {'dtype': 'BF16', 'shape': shape, 'file': str(destination)}
    with (out / 'meta.json').open('x') as stream:
        json.dump(meta, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(f'extracted {len(meta)} MTP tensors to {out}')


if __name__ == '__main__':
    main()
