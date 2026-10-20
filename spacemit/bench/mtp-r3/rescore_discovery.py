#!/usr/bin/env python3
"""用指定的质量检查器重评已保存的代码答案。只读批次目录。"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

import diagnostic

COMPLETED = {'complete', 'quality'}
LEGACY = 'legacy_unicode_runs'


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, Path(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def attempts(batch):
    """按目录名顺序返回有完整记录的尝试。"""
    rows = []
    for folder in sorted((batch / 'attempts').iterdir()):
        outcome_path, result_path = folder / 'outcome.json', folder / 'result.json'
        if not folder.is_dir() or not outcome_path.exists() or not result_path.exists():
            continue
        outcome = json.loads(outcome_path.read_text())
        status = folder / 'status.json'
        if status.exists() and json.loads(status.read_text()).get('status') not in ('passed', 'incomplete'):
            continue
        rows.append((folder, outcome, json.loads(result_path.read_text())))
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--assessment', type=Path, required=True)
    parser.add_argument('--quality', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    assessor = load_module('rescore_assessor', args.assessment)
    checker = load_module('rescore_quality', args.quality)
    cases = {case['case_id']: case for case in json.loads(args.cases.read_text())}
    records, skipped = [], 0
    for folder, outcome, row in attempts(args.batch):
        if outcome.get('reason') not in COMPLETED or row.get('category') != 'code':
            skipped += 1
            continue
        answer = (folder / 'answer.txt').read_text()
        case = cases.get(row['case_id'])
        if case is None:
            if row['case_id'] != LEGACY:
                raise ValueError('case is absent from the frozen plan: ' + row['case_id'])
            judged = checker.check_code('unicode_runs', answer)
            if judged.get('checks') != diagnostic.CODE_CHECKS:
                raise ValueError('legacy control check coverage differs')
            record = {'attempt': folder.name, 'case_id': row['case_id'], 'arm': row['arm'],
                      'kind': 'legacy_control', 'original_passed': row['quality']['passed'],
                      'rescored_passed': judged.get('pass') is True,
                      'checks': judged.get('checks'), 'detail': 'legacy control check'}
        else:
            rescored = assessor.assess(case, answer, args.quality)
            record = {'attempt': folder.name, 'case_id': row['case_id'], 'arm': row['arm'],
                      'kind': 'frozen_case', 'original_passed': row['quality']['passed'],
                      'rescored_passed': rescored['passed'], 'checks': rescored['result']['checks'],
                      'detail': rescored['result']['detail']}
        records.append(record)
    changed = [row for row in records if row['original_passed'] != row['rescored_passed']]
    summary = {'records': len(records), 'skipped_attempts': skipped,
               'original_failures': sum(row['original_passed'] is False for row in records),
               'rescored_failures': sum(row['rescored_passed'] is False for row in records),
               'changed': len(changed), 'changes': changed, 'rows': records}
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'rescore.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n',
                                              encoding='utf-8')
    print(json.dumps({key: summary[key] for key in
                      ('records', 'original_failures', 'rescored_failures', 'changed')}))


if __name__ == '__main__':
    sys.exit(main())
