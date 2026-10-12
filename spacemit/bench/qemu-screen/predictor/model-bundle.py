#!/usr/bin/env python3
"""建立只依赖 Python 标准库的冻结模型便携包。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

HERE = Path(__file__).resolve().parent
FILES = (
    'analyze.py', 'model.py', 'k1cost.py', 'priority.py', 'cost-evidence.py', 'demo.py',
    'family-model.py', 'family-predict.py', 'family-demo.py', 'load-use-evaluate.py',
    'schedule-family.py', 'schedule-demo.py', 'schedule-neighbor.py', 'neighbor-demo.py',
    'memory-reference.py', 'explain-cost.py', 'shared-cache.py', 'diagnose-cost.py',
    'verify-evidence.py', 'run-examples.py')
DIRECTORIES = ('profiles/k1-cpu0-umode-20261012', 'profiles/k1-memory-20261012',
    'examples/ime-load-64-case', 'examples/conv-family-v3',
    'examples/schedule-family-v5', 'examples/aligned-loop-v6')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(output, include_ime_audit=False):
    output.mkdir(parents=True, exist_ok=False)
    version='v7' if include_ime_audit else 'v6'
    root = output/('k1-models-'+version)
    root.mkdir()
    for name in FILES:
        shutil.copy2(HERE/name, root/name)
    for name in DIRECTORIES:
        shutil.copytree(HERE/name, root/name, ignore=shutil.ignore_patterns('__pycache__'))
    if include_ime_audit:
        for name in ('ime-mix-demo.py','ime-mix-evaluate.py'):
            shutil.copy2(HERE/name,root/name)
        shutil.copytree(HERE/'examples/ime-mix-v7',root/'examples/ime-mix-v7')
    metadata = dict(schema=6, all_candidates_retained=True, automatic_action='none',
        runtime='Python 3 standard library', models={})
    for name in ('conv-family-v3', 'schedule-family-v5', 'aligned-loop-v6'):
        model = json.loads((root/'examples'/name/'model.json').read_text())
        metadata['models'][name] = model['model_sha256']
    if include_ime_audit:
        metadata['schema']=7
        metadata['models']['ime-mix-v7']=json.loads((root/'examples/ime-mix-v7/model.json').read_text())['model_sha256']
    (root/'metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n')
    (root/'README.md').write_text('''# K1 模型便携包

运行环境为 Python 3 标准库。
本包不需要交叉编译器、QEMU 或 LLVM。
请在本目录执行下列命令。
输出目录必须不存在。

```bash
python3 run-examples.py --output ../k1-replay
```

工具先核验包内全部文件的 SHA-256。
工具重放四个范例，并重新计算独立检查的观测覆盖。
结果位于输出目录的 report.md 与 result.json。
主机重放时间不表示 K1 上的运行时间。

固定卷积范例的独立观测覆盖为 9/9 组。
V5 组合斜率范例的独立观测覆盖为 7/9 组。
V6 对齐循环范例的独立观测覆盖为 9/9 组和 27/27 个展开版本。
V5 的原始界限与覆盖缺口均保留。
声明的 95% 覆盖依赖各自固定范围内配置组的可交换性。
这些观测不能确认总体 95% 覆盖率。

分项周期范例用于成本诊断，不提供新算法的预测置信度。
访存范例查询固定模式的实测有效载荷吞吐率。
这些结果不能外推到任意算法、二进制、数据或线程配置。
新算法必须另建适用范围与独立误差校准。
全部候选均保留。
报告用于决定补测与实现的先后顺序。

各范例目录包含模型、原始误差界限与独立检查记录。
本包只提供冻结证据重放。
生成新轨迹与板端标定工具位于仓库 spacemit/bench/qemu-screen/predictor/。
完整证据见 spacemit/reports/2026-10-12-k1-model-v6.md。
''')
    if include_ime_audit:
        (root/'README.md').write_text((root/'README.md').read_text().replace('四个范例','五个范例'))
        with (root/'README.md').open('a') as text:
            text.write('''
## IME 混合循环检查

V7 新增一个 IME 混合循环失败范例。
区间观测覆盖为 9/9 组和 27/27 个展开版本。
点预测方向符号一致性仅为 9/27。
比值误差因子约为 2.12，区间不能确认多数投入顺序。
这些结果不能证明分项模型可以预测任意新 IME 算法。
本包保留宽界限和错误点预测。
最新解释见 spacemit/reports/2026-10-12-k1-model-v7.md。
''')
    paths = sorted(p for p in root.rglob('*') if p.is_file())
    (root/'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(root)}\n' for p in paths))
    subprocess.run([sys.executable, root/'run-examples.py', '--output', output/'self-check'], check=True)
    for cache in root.rglob('__pycache__'):
        shutil.rmtree(cache)
    archive = output/('k1-models-'+version+'.tar.gz')
    with tarfile.open(archive, 'w:gz') as target:
        target.add(root, arcname=root.name)
    (output/(archive.name+'.sha256')).write_text(f'{digest(archive)}  {archive.name}\n')
    print(archive)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--include-ime-audit', action='store_true')
    args=parser.parse_args()
    main(args.output.resolve(),args.include_ime_audit)
