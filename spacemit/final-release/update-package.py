#!/usr/bin/env python3
"""把当前报告、入口页与清单同步到已组装的成果包目录。

用法：python3 spacemit/final-release/update-package.py [--package DIR]
成果包目录必须已存在并含 manifest.json、project/ 与 reports/。
脚本不复制模型权重，不改写 evidence/ 中的原始归档。
"""
import argparse
import hashlib
import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = Path(__file__).resolve().parent
SUBMISSION = TEMPLATES / 'submission'
REPORTS = (
    'SUBMISSION-REPORT.md', 'SUBMISSION-EVIDENCE.md', 'SUBMISSION-REPORT.tex',
    'SUBMISSION-REPORT.pdf', 'SUBMISSION-ZH.md', 'SUBMISSION-ZH.tex', 'SUBMISSION-ZH.pdf',
    '2026-10-14-final-default-comparison.md', '2026-10-16-ultralong-final-comparison.md',
    '2026-10-16-final-release-tcm.md', '2026-10-21-official-conversion.md',
    '2026-10-21-fixed-multi-turn-results.md', '2026-10-21-fixed-multi-turn-v2-results.md',
    '2026-10-21-2b-mtp-docstring-rule-validation.md', '2026-10-21-routing-version-clarification.md',
    '2026-10-22-long-context-natural-results.md',
)
ENTRY_PAGES = {
    'README.md': 'README.md',
    'SUBMISSION-CHECKLIST.md': 'SUBMISSION-CHECKLIST.md',
    'docs/DEPENDENCIES.md': 'DEPENDENCIES.md',
    'docs/DEPLOYMENT.md': 'DEPLOYMENT.md',
    'docs/DESIGN.md': 'DESIGN.md',
    'docs/MODEL-CONVERSION.md': 'MODEL-CONVERSION.md',
}
LINK = re.compile(r'\[([^\]]+)\]\(([^\s)]+)\)')
NOT_IN_SUMS = {'SHA256SUMS', 'report-refresh-receipt.json'}


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def package_text(text, destination):
    prefix = '' if destination == 'README.md' else '../'
    text = text.replace('(../../reports/', f'({prefix}reports/')
    text = text.replace('(../../tcm/README.md)', f'({prefix}tcm/README.md)'
                        if prefix else '(tools/tcm/README.md)')
    if destination == 'README.md':
        for name in ('DEPENDENCIES', 'DEPLOYMENT', 'DESIGN', 'MODEL-CONVERSION'):
            text = text.replace(f']({name}.md)', f'](docs/{name}.md)')
    return text


def local(target):
    return '://' not in target and not target.startswith(('#', '/', 'mailto:', 'app:'))


def copy_entry_pages(package):
    for destination, name in ENTRY_PAGES.items():
        text = (SUBMISSION / name).read_text(encoding='utf-8')
        (package / destination).write_text(
            package_text(text, destination), encoding='utf-8')


def copy_reports(repo, package):
    project = package / 'project'
    reports = package / 'reports'
    queue = [repo / 'spacemit/reports' / name for name in REPORTS]
    seen, missing = set(), []
    while queue:
        source = queue.pop().resolve()
        if source in seen or not source.is_relative_to(repo):
            continue
        seen.add(source)
        if not source.exists():
            missing.append(str(source.relative_to(repo)))
            continue
        destination = project / source.relative_to(repo)
        if source.is_dir():
            if source.relative_to(repo).parts[0] == 'lab':
                continue
            destination.mkdir(parents=True, exist_ok=True)
            if (source / 'README.md').exists():
                queue.append(source / 'README.md')
            continue
        if source.suffix in ('.gguf', '.safetensors'):
            raise SystemExit('成果包不得包含模型权重：' + str(source))
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        if source.suffix == '.md' and 'raw' not in source.parts and 'snapshots' not in source.parts:
            queue += [source.parent / target.partition('#')[0]
                      for _, target in LINK.findall(source.read_text(encoding='utf-8'))
                      if local(target)]
    for name in REPORTS:
        source = repo / 'spacemit/reports' / name
        destination = reports / name
        if source.suffix != '.md':
            shutil.copy2(source, destination)
            continue

        def link(match):
            label, target = match.groups()
            if not local(target):
                return match.group(0)
            path, separator, fragment = target.partition('#')
            mapped = project / (source.parent / path).resolve().relative_to(repo)
            target = os.path.relpath(mapped, reports)
            return f'[{label}]({target}{separator}{fragment})'

        destination.write_text(LINK.sub(link, source.read_text(encoding='utf-8')),
                               encoding='utf-8')
    return seen, missing


def update_manifest(package, receipt):
    path = package / 'manifest.json'
    manifest = json.loads(path.read_text(encoding='utf-8'))
    manifest.update(
        status='verified-limited',
        official_conversion_completed=True,
        converter_commit=receipt['commit'],
        reports=dict(canonical='project/spacemit/reports/SUBMISSION-REPORT.pdf',
                     portable='reports/SUBMISSION-REPORT.pdf',
                     canonical_zh='project/spacemit/reports/SUBMISSION-ZH.pdf',
                     portable_zh='reports/SUBMISSION-ZH.pdf'),
        limits=['External model weights and exact vendor dependencies are required.',
                'Long state correctness and repeat stability remain later acceptance items.',
                'Two pairs at 16k and one pair at 32k per model.'])
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def check_links(package):
    checked = 0
    paths = [package / 'README.md', package / 'SUBMISSION-CHECKLIST.md',
             *sorted((package / 'docs').glob('*.md')),
             *sorted((package / 'reports').glob('*.md')),
             package / 'model-materials/README.md',
             package / 'model-materials/tools/README.md']
    for path in paths:
        for _, target in LINK.findall(path.read_text(encoding='utf-8')):
            if not local(target):
                continue
            resolved = (path.parent / target.partition('#')[0]).resolve()
            if not resolved.is_relative_to(package) or not resolved.exists():
                raise SystemExit(f'成果包链接失效：{path} -> {target}')
            checked += 1
    return checked


def write_sums(package):
    lines = []
    for path in sorted(package.rglob('*')):
        if path.is_file() and not path.is_symlink() and path.name not in NOT_IN_SUMS:
            lines.append(f'{sha(path)}  {path.relative_to(package).as_posix()}\n')
    (package / 'SHA256SUMS').write_text(''.join(lines), encoding='utf-8')
    return len(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, default=ROOT)
    parser.add_argument('--package', type=Path, default=ROOT / 'final-release')
    args = parser.parse_args()
    repo = args.repository.resolve()
    package = args.package.resolve()
    for name in ('manifest.json', 'project', 'reports', 'evidence'):
        if not (package / name).exists():
            raise SystemExit('成果包缺少：' + name)
    source_receipt = json.loads(
        (repo / 'lab/final-default-20261013/release/k1-final-20261013-r3/'
         'model-materials/metadata/converter-source-receipt.json').read_text())
    production_archive = (repo / 'lab/final-default-20261013/release/'
                          'k1-final-20261013-r3.tar.gz')
    if not production_archive.exists():
        raise SystemExit('缺少原生产归档：' + str(production_archive))
    copy_entry_pages(package)
    seen, missing = copy_reports(repo, package)
    update_manifest(package, source_receipt)
    checked = check_links(package)
    files = write_sums(package)
    receipt = {
        'status': 'pass',
        'package': str(package),
        'files': files,
        'package_links_checked': checked,
        'project_paths': len(seen),
        'missing_historical_references': sorted(set(missing)),
        'production_archive_sha256': sha(production_archive),
        'source_commit': source_receipt['commit'],
        'not_in_sum': sorted(NOT_IN_SUMS),
    }
    (package / 'evidence/report-refresh-receipt.json').write_text(
        json.dumps(receipt, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
