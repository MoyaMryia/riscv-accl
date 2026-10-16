#!/usr/bin/env python3
"""记录模型输入身份、转换源码和加工产物。"""

import argparse
import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path


def hashes(path):
    size = path.stat().st_size
    sha256 = hashlib.sha256()
    blob = hashlib.sha1(f'blob {size}\0'.encode())
    with path.open('rb') as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            sha256.update(chunk)
            blob.update(chunk)
    return {'bytes': size, 'sha256': sha256.hexdigest(), 'git_blob_sha1': blob.hexdigest()}


def checked_file(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f'文件缺失或位于指定目录外：{name}')
    return path


def snapshot(root, metadata, model):
    root = root.resolve()
    if metadata.get('id') != f'Qwen/Qwen3.5-{model}':
        raise ValueError('官方模型仓库标识不匹配')
    revision = metadata['sha']
    if len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('模型修订必须为完整提交标识')
    required = metadata['siblings']
    expected_names = {item['rfilename'] for item in required}
    actual_names = {str(path.relative_to(root)) for path in root.rglob('*')
                    if path.is_file() and not {'.cache', '.git'}.intersection(path.relative_to(root).parts)}
    extra = actual_names - expected_names
    if extra:
        raise ValueError(f'检查点包含未记录文件：{sorted(extra)}')
    records = {}
    for item in required:
        name = item['rfilename']
        path = checked_file(root, name)
        value = hashes(path)
        lfs = item.get('lfs')
        if lfs:
            if value['sha256'] != lfs['sha256'] or value['bytes'] != lfs['size']:
                raise ValueError(f'官方大文件身份不匹配：{name}')
        elif value['git_blob_sha1'] != item['blobId']:
            raise ValueError(f'官方配置文件身份不匹配：{name}')
        records[name] = value
    config = json.loads(checked_file(root, 'config.json').read_text())
    text = config.get('text_config', config)
    layers = {'2B': 24, '4B': 32}[model]
    if config.get('architectures') != ['Qwen3_5ForConditionalGeneration']:
        raise ValueError('模型架构不匹配')
    if text.get('num_hidden_layers') != layers or text.get('mtp_num_hidden_layers') != 1:
        raise ValueError('主模型层数或 MTP 层数不匹配')
    index = json.loads(checked_file(root, 'model.safetensors.index.json').read_text())
    weight_map = index['weight_map']
    if not weight_map:
        raise ValueError('模型分片索引为空')
    headers = {}
    for name in sorted(set(weight_map.values())):
        if name not in records or not name.endswith('.safetensors'):
            raise ValueError(f'分片未通过官方身份检查：{name}')
        path = checked_file(root, name)
        with path.open('rb') as stream:
            prefix = stream.read(8)
            if len(prefix) != 8:
                raise ValueError(f'分片头不完整：{name}')
            size, = struct.unpack('<Q', prefix)
            if size > 64 * 1024 * 1024:
                raise ValueError(f'分片头超过限制：{name}')
            headers[name] = json.loads(stream.read(size))
    for name, shard in weight_map.items():
        if name not in headers[shard]:
            raise ValueError(f'索引张量不存在：{name}')
    mtp = sorted(name for name in weight_map if name.startswith(('mtp.', 'model.mtp.')))
    if len(mtp) != 15:
        raise ValueError(f'MTP 张量数量不匹配：{len(mtp)}')
    return {'status': 'input-identity-verified', 'repo_id': metadata['id'],
            'revision': revision, 'checkpoint': str(root), 'files': records,
            'tensor_count': len(weight_map), 'mtp_tensors': mtp,
            'limits': ['仅核验来源文件和分片索引，尚未验证转换数值或模型输出。']}


def source(root, receipt):
    root = root.resolve()
    if receipt['commit'] != 'a990751d55a4c54acf2bb77d44282c2093652359':
        raise ValueError('转换源码修订不匹配')
    records = {}
    for name, expected in receipt['files_sha256'].items():
        value = hashes(checked_file(root, name))
        if value['sha256'] != expected:
            raise ValueError(f'源码身份不匹配：{name}')
        records[name] = value['sha256']
    return {'status': 'source-identity-verified', 'commit': receipt['commit'],
            'source': str(root), 'verified_files': len(records), 'files_sha256': records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    snap = commands.add_parser('snapshot', help='核验官方检查点输入')
    snap.add_argument('--model', choices=['2B', '4B'], required=True)
    snap.add_argument('--checkpoint', type=Path, required=True)
    snap.add_argument('--metadata', type=Path, required=True)
    src = commands.add_parser('source', help='核验固定转换源码')
    src.add_argument('--root', type=Path, required=True)
    src.add_argument('--receipt', type=Path, required=True)
    files = commands.add_parser('artifacts', help='记录产物和工具文件身份')
    files.add_argument('paths', nargs='+', type=Path)
    for command in (snap, src, files):
        command.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('输出记录已存在，禁止覆盖')
    if args.command == 'snapshot':
        result = snapshot(args.checkpoint, json.loads(args.metadata.read_text()), args.model)
        result['metadata_file'] = str(args.metadata.resolve())
        result['metadata_sha256'] = hashes(args.metadata)['sha256']
    elif args.command == 'source':
        result = source(args.root, json.loads(args.receipt.read_text()))
        result['receipt_sha256'] = hashes(args.receipt)['sha256']
    else:
        result = {'status': 'artifact-identity-recorded',
                  'files': {str(path.resolve()): hashes(path) for path in args.paths},
                  'limits': ['文件哈希不能替代结构、数值、推理和性能验证。']}
    result['recorded_at'] = datetime.now(timezone.utc).isoformat()
    result['recorder_sha256'] = hashes(Path(__file__))['sha256']
    with args.output.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
