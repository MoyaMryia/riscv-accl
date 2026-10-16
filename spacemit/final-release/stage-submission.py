"""复制已验证材料，生成待冻结的委员会成果目录。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            result.update(chunk)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    repo = args.repository.resolve()
    output = args.output.resolve()
    if output.exists():
        parser.error('输出目录已存在，禁止覆盖。')
    original = repo / 'lab/final-default-20261013/release/k1-final-20261013-r3'
    vendor = repo / 'lab/local-reference/source-a990751-clean'
    templates = repo / 'spacemit/final-release'
    materials = original / 'model-materials'
    receipt = json.loads((materials / 'metadata/converter-source-receipt.json').read_text())
    for name, expected in receipt['files_sha256'].items():
        if sha(vendor / name) != expected:
            parser.error('转换源码身份不同：' + name)
    server_sha = 'f254f174919c0a97ef34366f116705f6d22574cab4c2bfc39928c0d315b5bfbd'
    if sha(original / 'build/bin/llama-server') != server_sha:
        parser.error('原生产服务器身份不同。')
    output.mkdir(parents=True)
    runtime = output / 'runtime'
    runtime.mkdir()
    ignore = shutil.ignore_patterns('__pycache__', '*.pyc', '.git')
    for name in ('source', 'build', 'package'):
        shutil.copytree(original / name, runtime / name, symlinks=True, ignore=ignore)
    for name in ('Requirements.md', 'VALIDATION.md'):
        shutil.copy2(original / name, runtime / name)
    shutil.copytree(vendor, output / 'converter-source', symlinks=True, ignore=ignore)
    shutil.copytree(materials, output / 'model-materials', symlinks=True, ignore=ignore)
    for name in ('deploy.sh', 'deploy.py'):
        shutil.copy2(templates / name, output / name)
    docs = output / 'docs'
    docs.mkdir()
    for name in ('DEPLOYMENT.md', 'MODEL-CONVERSION.md', 'DESIGN.md', 'DEPENDENCIES.md'):
        shutil.copy2(templates / 'submission' / name, docs / name)
    shutil.copy2(templates / 'submission/README.md', output / 'README.md')
    shutil.copy2(repo / 'Requirements.md', output / 'Requirements.md')
    reports = output / 'reports'
    reports.mkdir()
    for name in ('SUBMISSION-REPORT.md', 'SUBMISSION-REPORT.tex', 'SUBMISSION-REPORT.pdf',
                 'SUBMISSION-ZH.md', 'SUBMISSION-ZH.tex', 'SUBMISSION-ZH.pdf',
                 'SUBMISSION-EVIDENCE.md', '2026-10-14-final-default-comparison.md'):
        shutil.copy2(repo / 'spacemit/reports' / name, reports / name)
    evidence = output / 'evidence'
    evidence.mkdir()
    for name in ('archive-receipt.json', 'report-receipt.json'):
        shutil.copy2(templates / name, evidence / ('original-r3-' + name))
    manifest = {
        'status': 'draft-not-for-submission', 'production_version': 'k1-final-20261013-r3',
        'server_sha256': server_sha, 'converter_commit': receipt['commit'],
        'converter_verified_files': len(receipt['files_sha256']),
        'official_conversion_completed': False,
        'pending': ['ultralong-independent-verification', 'updated-reports-and-pdf',
                    'evidence-archives', 'portable-report-links', 'board-deploy-smoke',
                    'submission-checklist', 'final-checksums', 'final-archive-verification']}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (output / 'DRAFT.md').write_text('# 待冻结目录\n\n本目录尚未完成最终收尾，不得作为最终成果发送。\n'
        '待处理内容见 `manifest.json`。\n原 r3 源码、二进制和转换工具已复制；性能报告尚待补测更新。\n')
    print(json.dumps({'status': manifest['status'], 'directory': str(output),
                      'server_sha256': sha(runtime / 'build/bin/llama-server')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
