#!/usr/bin/env python3
"""核对转换工具及重新训练后的存档一致性。"""
import argparse
import json
from pathlib import Path

from bert_train import sha256


def verify_converter(archive, reference):
    expected = json.loads(reference.read_text())['converter_snapshot']['sha256']
    if sha256(archive) != expected:
        raise ValueError('converter snapshot hash differs')


def verify_result(result, artifacts_path, training_path):
    expected = json.loads(artifacts_path.read_text())
    training = json.loads((result / 'training.json').read_text())
    original = json.loads(training_path.read_text())
    files = {'encoder_safetensors': result / 'encoder/model.safetensors',
             'head': result / 'head.json', 'gguf': result / 'encoder-f32.gguf'}
    artifacts = {}
    for name, path in files.items():
        digest = sha256(path)
        size = path.stat().st_size
        if digest != expected[name]['sha256'] or size != expected[name]['bytes']:
            raise ValueError('reproduced artifact differs: ' + name)
        artifacts[name] = {'sha256': digest, 'bytes': size}
    for key in ('configuration', 'versions', 'parameters', 'split_counts', 'best_epoch'):
        if training[key] != original[key]:
            raise ValueError('training record differs: ' + key)
    for split in ('best_dev', 'test', 'regression'):
        if training['metrics'][split]['confusion'] != original['metrics'][split]['confusion']:
            raise ValueError('classification results differ: ' + split)
    return {'artifacts': artifacts, 'best_epoch': training['best_epoch'],
            'test_accuracy': training['metrics']['test']['accuracy'],
            'regression_accuracy': training['metrics']['regression']['accuracy']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='mode', required=True)
    converter = subparsers.add_parser('converter')
    converter.add_argument('--archive', type=Path, required=True)
    converter.add_argument('--artifacts', type=Path, required=True)
    result = subparsers.add_parser('result')
    for name in ('result', 'artifacts', 'training', 'output'):
        result.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    if args.mode == 'converter':
        verify_converter(args.archive, args.artifacts)
    else:
        report = verify_result(args.result, args.artifacts, args.training)
        with args.output.open('x') as target:
            json.dump(report, target, indent=2)
            target.write('\n')
        print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
