#!/usr/bin/env python3
"""检查文档链接、章节锚点、主题索引覆盖、归档残留引用与原始记录。

规则：
- 只扫描活动文档。`spacemit/reports/raw/`、`spacemit/reports/snapshots/`
  与不随 Git 分发的目录不参与扫描。
- 失效链接按 `tools/doc_links_baseline.json` 判定。基线只能缩小：
  清单外的新失效链接失败，清单中已修复的条目也失败，需运行 `--prune`。
- 每次运行先用 `1` 覆盖退出状态文件，进程崩溃时该文件保持失败。
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / 'tools/doc_links_baseline.json'
FROZEN_TREES = ('spacemit/reports/raw', 'spacemit/reports/snapshots')
SKIP_ROOT_DIRS = {'.git', 'lab', 'bianbu', 'TinyLlama', 'llamacpp-conv', 'final-release'}
SKIP_ANY_DIRS = {'__pycache__'}
ARCHIVE_PREFIX = 'archive/'
RECORD = 'spacemit/reports/2026-10-22-project-file-organization.md'
LINK = re.compile(r'\[[^\]\n]*\]\(([^)\n]+?)(?:\s+"[^"]*")?\)')
DATED = re.compile(r'^2026-\d{2}-\d{2}-.+\.md$')
STALE_TOKENS = ('spacemit/patches/', 'spacemit/apply-patches.sh',
                'k1-llm-inference-optimizations-old', 'TECHNICAL-GUIDE-')
TEXT_SUFFIXES = {'.md', '.tex', '.sh', '.py'}
# 本脚本定义检索标记，必须写出这些旧路径。
EXEMPT_STALE = {'tools/check-docs.py'}
REQUIRED = (
    'docs/README.md', 'docs/technical-guide/technical-guide-zh.md',
    'docs/technical-guide/technical-guide-zh.tex', 'docs/technical-guide/technical-guide-zh.pdf',
    'docs/technical-guide/technical-guide-en.md', 'docs/technical-guide/technical-guide-en.tex',
    'docs/technical-guide/technical-guide-en.pdf', 'archive/README.md',
    'archive/patches-5ad05d8/apply-patches.sh',
    'archive/reports/k1-llm-inference-optimizations-2026-09-24.tex',
    'archive/reports/k1-llm-inference-optimizations-2026-09-24.pdf',
    'spacemit/reports/TOPICS.md', 'lab/README.md',
)


def prose(text):
    return re.sub(r'^```.*?^```[^\n]*$', '', text, flags=re.M | re.S)


def slug(heading):
    text = re.sub(r'<[^>]*>', '', heading).replace('`', '').lower()
    keep = ''.join(c for c in text
                   if c in '_- ' or c.isalnum() or unicodedata.category(c).startswith('L'))
    return keep.replace(' ', '-')


def skipped(rel):
    return any(rel == tree or rel.startswith(tree + '/') for tree in FROZEN_TREES)


def live_files(suffixes):
    for base, dirs, files in os.walk(ROOT):
        rel = os.path.relpath(base, ROOT).replace(os.sep, '/')
        if rel == '.':
            rel = ''
        if rel == '':
            dirs[:] = [d for d in dirs if d not in SKIP_ROOT_DIRS]
        dirs[:] = [d for d in dirs if d not in SKIP_ANY_DIRS]
        if skipped(rel):
            dirs[:] = []
            continue
        for name in files:
            if Path(name).suffix in suffixes:
                yield Path(base) / name
    if '.md' in suffixes and (ROOT / 'lab/README.md').exists():
        yield ROOT / 'lab/README.md'


def not_distributed(target):
    """目标不在 Git 分发范围内时返回 True：仓库外路径或被 .gitignore 排除的路径。"""
    try:
        rel = target.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return True
    ignored = subprocess.run(['git', '-C', str(ROOT), 'check-ignore', '-q', '--no-index', rel],
                             capture_output=True)
    return ignored.returncode == 0


def check_links():
    errors, documents, checked = [], 0, 0
    for path in sorted(live_files({'.md'})):
        rel = path.relative_to(ROOT).as_posix()
        documents += 1
        text = prose(path.read_text(encoding='utf-8'))
        for match in LINK.finditer(text):
            href = match.group(1).strip().strip('<>')
            if re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:', href):
                continue
            local, _, anchor = unquote(href).partition('#')
            target = path.parent / local if local else path
            checked += 1
            if not target.exists():
                if not not_distributed(target):
                    errors.append({'file': rel, 'link': href, 'error': 'target absent'})
            elif anchor and target.suffix == '.md':
                headings = re.findall(r'^#{1,6}\s+(.+?)\s*#*$',
                                      prose(target.read_text(encoding='utf-8')), re.M)
                if anchor not in {slug(h) for h in headings}:
                    errors.append({'file': rel, 'link': href, 'error': 'anchor absent'})
    return documents, checked, errors


def check_topics():
    index = ROOT / 'spacemit/reports/TOPICS.md'
    linked = re.findall(r'\]\((2026-\d{2}-\d{2}-[^)]+\.md)\)', index.read_text(encoding='utf-8'))
    files = sorted(f for f in os.listdir(ROOT / 'spacemit/reports') if DATED.match(f))
    return {'dated_reports': len(files), 'links': len(linked),
            'missing': [f for f in files if f not in linked],
            'duplicated': sorted({f for f in linked if linked.count(f) > 1}),
            'unknown': sorted({f for f in linked if f not in files})}


def check_stale():
    hits = []
    for path in sorted(live_files(TEXT_SUFFIXES)):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(ARCHIVE_PREFIX) or rel == RECORD or rel in EXEMPT_STALE:
            continue
        text = prose(path.read_text(encoding='utf-8'))
        hits += [{'file': rel, 'token': token} for token in STALE_TOKENS if token in text]
    return hits


def check_required():
    absent = [name for name in REQUIRED if not (ROOT / name).exists()]
    tracked = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '--error-unmatch', 'lab/README.md'],
                             capture_output=True).returncode == 0
    return {'required': len(REQUIRED), 'absent': absent, 'lab_readme_tracked': tracked}


def check_frozen(before, staged):
    if staged:
        command = ['git', '-C', str(ROOT), 'diff', '--cached', '--name-only', '--', *FROZEN_TREES]
    else:
        command = ['git', '-C', str(ROOT), 'status', '--porcelain', '--', *FROZEN_TREES]
    status = subprocess.run(command, check=True, capture_output=True, text=True).stdout.strip()
    lines = [line.strip() for line in status.splitlines() if line.strip()]
    result = {'mode': 'staged' if staged else 'worktree',
              'changed_paths': lines, 'changed_count': len(lines),
              'manifest_compared': before is not None}
    if before is None:
        return result
    files = json.loads(Path(before).read_text())['files']
    changed = []
    for name, expected in files.items():
        path = ROOT / name
        if expected.startswith('symlink:'):
            if not path.is_symlink() or os.readlink(path) != expected[len('symlink:'):]:
                changed.append(name)
        elif not path.is_file():
            changed.append(name)
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            changed.append(name)
    result.update({'frozen_files': len(files), 'changed_or_missing': sorted(changed),
                   'manifest_sha256': hashlib.sha256(
                       json.dumps(files, sort_keys=True).encode()).hexdigest()})
    return result


def base_baseline(ref):
    """读取基准提交中的基线条目；该提交没有基线文件时返回 None。"""
    try:
        text = subprocess.run(['git', '-C', str(ROOT), 'show', f'{ref}:tools/doc_links_baseline.json'],
                              check=True, capture_output=True, text=True).stdout
    except subprocess.CalledProcessError:
        return None
    return {(e['file'], e['link'], e['error']) for e in json.loads(text)['errors']}


def load_baseline():
    return {(e['file'], e['link'], e['error'])
            for e in json.loads(BASELINE.read_text())['errors']}


def dump_baseline(entries):
    rows = [dict(file=f, link=l, error=e) for f, l, e in sorted(entries)]
    BASELINE.write_text(json.dumps({'version': 1, 'errors': rows},
                                   ensure_ascii=False, indent=1) + '\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', help='整理前的原始记录哈希清单')
    parser.add_argument('--json', metavar='DIR', help='把结果写入该目录的 links.json 与 summary.json')
    parser.add_argument('--prune', action='store_true', help='删除基线中已修复的条目')
    parser.add_argument('--staged', action='store_true', help='按暂存区判定原始记录改动')
    parser.add_argument('--base-ref', metavar='REF', help='基线条目多于该提交时失败')
    args = parser.parse_args(argv)

    if args.json:
        out = Path(args.json)
        out.mkdir(parents=True, exist_ok=True)
        (out / 'exit-status').write_text('1\n')

    baseline = load_baseline()
    documents, checked, errors = check_links()
    found = {(e['file'], e['link'], e['error']) for e in errors}
    new = sorted(found - baseline)
    fixed = sorted(baseline - found)
    topics = check_topics()
    stale = check_stale()
    frozen = check_frozen(args.before, args.staged)
    required = check_required()
    base = base_baseline(args.base_ref) if args.base_ref else None
    grown = sorted(baseline - base) if base is not None else []

    if args.prune:
        dump_baseline(found - {e for e in new})
        print(f'已删除 {len(fixed)} 条失效链接基线')
        return 0

    failed = bool(new or fixed or grown or topics['missing'] or topics['duplicated']
                  or topics['unknown'] or stale or frozen['changed_paths']
                  or frozen.get('changed_or_missing') or required['absent']
                  or not required['lab_readme_tracked'])
    summary = {'links': {'documents': documents, 'local_links': checked,
                         'baseline_entries': len(baseline), 'new_errors': len(new),
                         'fixed_errors': len(fixed)},
               'topics': topics, 'stale_references': stale, 'frozen': frozen,
               'required': required, 'baseline_growth': len(grown), 'failed': failed}
    if args.json:
        out = Path(args.json)
        (out / 'links.json').write_text(json.dumps(
            {'documents': documents, 'local_links': checked,
             'baseline_entries': len(baseline),
             'new_errors': [dict(file=f, link=l, error=e) for f, l, e in new],
             'fixed_errors': [dict(file=f, link=l, error=e) for f, l, e in fixed]},
            ensure_ascii=False, indent=1) + '\n')
        (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1) + '\n')
        (out / 'frozen.json').write_text(json.dumps(frozen, ensure_ascii=False, indent=1) + '\n')
        (out / 'exit-status').write_text(('1' if failed else '0') + '\n')
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    for item in new:
        print(f"new: {item[0]} | {item[1]} | {item[2]}", file=sys.stderr)
    for item in fixed:
        print(f"fixed: {item[0]} | {item[1]} | 基线条目已修复，运行 --prune", file=sys.stderr)
    for item in grown:
        print(f"grown: {item[0]} | {item[1]} | 基线新增，禁止扩大", file=sys.stderr)
    for item in stale:
        print(f"stale: {item['file']} | {item['token']}", file=sys.stderr)
    for name in frozen['changed_paths']:
        print(f"frozen: {name}", file=sys.stderr)
    for name in required['absent']:
        print(f"absent: {name}", file=sys.stderr)
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
