#!/usr/bin/env python3
"""比较两个 GGUF 的张量结构、词元器身份与对话模板。

本工具只读文件，不改模型。
比较结果写入 JSON 收据；不一致时以状态 1 退出。
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

STRUCTURE_KEYS = ('gguf_version', 'tensor_count')


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def read_structure(path, gguf_module):
    """读取 GGUF 的结构字段。缺少 gguf 包时立即失败。"""
    reader = gguf_module.GGUFReader(str(path))
    fields = reader.fields
    tensors = [{'name': tensor.name,
                'shape': [int(v) for v in tensor.shape],
                'dtype': str(tensor.tensor_type)} for tensor in reader.tensors]
    tokenizer = {}
    token_field = fields.get('tokenizer.ggml.tokens')
    if token_field is not None:
        items = token_field.data
        digest = hashlib.sha256()
        for item in items:
            digest.update(item if isinstance(item, bytes) else bytes(item))
            digest.update(b'\0')
        tokenizer = {'count': len(items), 'tokens_sha256': digest.hexdigest()}
    template = fields.get('tokenizer.chat_template')
    return {
        'path': str(path),
        'sha256': sha256(path),
        'gguf_version': int(getattr(reader, 'gguf_version', 0)),
        'tensor_count': len(tensors),
        'tensors': sorted(tensors, key=lambda item: item['name']),
        'tokenizer_model': str(getattr(fields.get('tokenizer.ggml.model'), 'contents', '')),
        'tokenizer': tokenizer,
        'chat_template_sha256': hashlib.sha256(str(getattr(template, 'contents', '')).encode()).hexdigest(),
    }


def compare_structures(reference, candidate, ignore=()):
    """比较两个结构记录，返回逐项检查结果。"""
    ignore = set(ignore)
    checks, failures = [], []

    def record(name, passed, detail=None):
        checks.append({'check': name, 'passed': bool(passed),
                       **({'detail': detail} if detail is not None else {})})
        if not passed:
            failures.append(name)

    for key in STRUCTURE_KEYS:
        record(key, reference[key] == candidate[key],
               {'reference': reference[key], 'candidate': candidate[key]})
    record('file_sha256', reference['sha256'] == candidate['sha256'],
           {'reference': reference['sha256'], 'candidate': candidate['sha256']})
    reference_tensors = {t['name']: t for t in reference['tensors']
                         if t['name'] not in ignore}
    candidate_tensors = {t['name']: t for t in candidate['tensors']
                         if t['name'] not in ignore}
    record('tensor_names', set(reference_tensors) == set(candidate_tensors),
           {'missing': sorted(set(reference_tensors) - set(candidate_tensors)),
            'extra': sorted(set(candidate_tensors) - set(reference_tensors))})
    for name in sorted(set(reference_tensors) & set(candidate_tensors)):
        record('shape:' + name, reference_tensors[name]['shape'] == candidate_tensors[name]['shape'],
               {'reference': reference_tensors[name]['shape'],
                'candidate': candidate_tensors[name]['shape']})
        record('dtype:' + name, reference_tensors[name]['dtype'] == candidate_tensors[name]['dtype'],
               {'reference': reference_tensors[name]['dtype'],
                'candidate': candidate_tensors[name]['dtype']})
    record('tokenizer_model', reference['tokenizer_model'] == candidate['tokenizer_model'],
           {'reference': reference['tokenizer_model'],
            'candidate': candidate['tokenizer_model']})
    record('tokenizer_count', reference['tokenizer'].get('count') == candidate['tokenizer'].get('count'),
           {'reference': reference['tokenizer'].get('count'),
            'candidate': candidate['tokenizer'].get('count')})
    record('tokenizer_tokens', reference['tokenizer'].get('tokens_sha256')
           == candidate['tokenizer'].get('tokens_sha256'))
    record('chat_template', reference['chat_template_sha256'] == candidate['chat_template_sha256'])
    return {'checks': checks, 'failures': failures, 'passed': not failures}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ignore-tensor', action='append', default=[])
    parser.add_argument('--gguf-py', type=Path,
                        help='包含 gguf 包的目录；省略时使用当前环境')
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error('output already exists')
    if args.gguf_py is not None:
        sys.path.insert(0, str(args.gguf_py))
    try:
        import gguf
    except ImportError as error:
        parser.error('gguf package is not available: ' + str(error))
    for path in (args.reference, args.candidate):
        if not path.is_file():
            parser.error('missing artifact: ' + str(path))
    reference = read_structure(args.reference, gguf)
    candidate = read_structure(args.candidate, gguf)
    result = compare_structures(reference, candidate, args.ignore_tensor)
    result.update(reference=reference, candidate=candidate,
                  ignored_tensors=sorted(args.ignore_tensor),
                  tool=Path(__file__).name)
    args.output.write_text(json.dumps(result, indent=1))
    print('STRUCTURE_OK' if result['passed'] else 'STRUCTURE_MISMATCH',
          len(result['checks']), 'checks')
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
