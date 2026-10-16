#!/usr/bin/env python3
"""建立或核验固定算子模型的标准 Python 便携包。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import tarfile

import model


def build(source, output, model_path, calibration_path, evaluation_path):
    m = json.loads(model_path.read_text())
    calibration = json.loads(calibration_path.read_text())
    plan = json.loads((source/'plan.json').read_text())
    evaluation = json.loads(evaluation_path.read_text())
    model.verify_calibration(calibration, m, plan)
    model.verify(evaluation, 'operator-shape-evaluation')
    if evaluation['model_sha256'] != m['sha256'] or evaluation['calibration_sha256'] != calibration['sha256']:
        raise ValueError('evaluation identity')
    cases = [dict(family=g['family'], shape=g['shape'], thread_count=t, padding=g['padding'])
             for g in plan['groups'] if g['split'] == 'test' for t in g['threads']]
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for name in ['model.py', 'summarize.py', 'model-bundle.py', 'plan.json', 'README.md']:
            shutil.copy2(source/name, root/name)
        for path, name in [(model_path, 'model.json'), (calibration_path, 'calibration.json'), (evaluation_path, 'evaluation.json')]:
            shutil.copy2(path, root/name)
        model.write_new(root/'cases.json', cases)
        model.write_new(root/'predictions.json', model.query(m, plan, calibration, cases))
        model.write_new(root/'manifest.json', {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.iterdir())})
        with output.open('xb') as handle:
            with tarfile.open(fileobj=handle, mode='w:gz') as tar:
                for path in sorted(root.iterdir()):
                    tar.add(path, arcname=path.name)
    return dict(status='created', archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                model_sha256=m['sha256'], calibration_sha256=calibration['sha256'])


def replay(root):
    manifest = json.loads((root/'manifest.json').read_text())
    if any(Path(name).name != name for name in manifest):
        raise ValueError('manifest path')
    for name, expected in manifest.items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != expected:
            raise ValueError('bundle file: '+name)
    m = json.loads((root/'model.json').read_text())
    calibration = json.loads((root/'calibration.json').read_text())
    plan = json.loads((root/'plan.json').read_text())
    cases = json.loads((root/'cases.json').read_text())
    expected = json.loads((root/'predictions.json').read_text())
    result = model.query(m, plan, calibration, cases)
    if result != expected:
        raise ValueError('prediction replay')
    return dict(status='verified', files=len(manifest), cases=len(cases), predictions_sha256=model.digest(result),
                model_sha256=m['sha256'], calibration_sha256=calibration['sha256'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    b = sub.add_parser('build')
    for name in ('model', 'calibration', 'evaluation', 'output'):
        b.add_argument('--'+name, type=Path, required=True)
    r = sub.add_parser('replay')
    r.add_argument('root', type=Path)
    args = p.parse_args()
    result = build(Path(__file__).parent, args.output, args.model, args.calibration, args.evaluation) if args.action == 'build' else replay(args.root)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
