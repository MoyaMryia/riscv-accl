#!/usr/bin/env python3
"""按冻结 v2 判定器重评旧答案，并与题面独立参考比较。"""
import argparse
import importlib.util
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
here = Path(__file__).resolve().parent
source = here.parent / 'delivery-multiturn-20261021-115000-r2'
spec = importlib.util.spec_from_file_location('frozen_v2', here / 'assessment-v2.py')
assessment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assessment)
cases = {item['conversation_id']: item for item in assessment.read_cases()}
reference = json.loads((here / 'manual-reference-r2.json').read_text())
answers = set(source.glob('batch/attempts/*/result/conversations/*/turn-*/answer.txt'))
paths = [source / row['answer_path'] for row in reference['rows']]
if len(paths) != len(set(paths)) or set(paths) != answers:
    raise ValueError('manual reference must cover every saved answer once')
rows = []
models = {}
for row, path in zip(reference['rows'], paths):
    result = assessment.assess(cases[row['conversation_id']]['turns'][row['turn'] - 1],
                               path.read_text())
    rows.append({**row, 'assessment': result})
    counts = models.setdefault(row['model'], {
        'planned': assessment.planned_turns(list(cases.values())), 'completed': 0,
        'automatic_correct': 0, 'automatic_incorrect': 0, 'automatic_review': 0,
        'manual_correct': 0, 'manual_incorrect': 0, 'manual_unknown': 0})
    counts['completed'] += 1
    automatic = result['passed']
    counts['automatic_' + ('correct' if automatic is True else
                           'incorrect' if automatic is False else 'review')] += 1
    correct = row['correct']
    counts['manual_' + ('correct' if correct is True else
                        'incorrect' if correct is False else 'unknown')] += 1
for counts in models.values():
    counts['unattempted'] = counts['planned'] - counts['completed']
    counts['completed_subset_accuracy'] = counts['manual_correct'] / counts['completed']
    counts['planned_accuracy'] = None
false_positives = [row['answer_path'] for row in rows
                   if row['assessment']['passed'] is True and row['correct'] is False]
false_negatives = [row['answer_path'] for row in rows
                   if row['assessment']['passed'] is False and row['correct'] is True]
summary = {'purpose': 'retrospective_gate_audit', 'assessment_version': assessment.ASSESSMENT_VERSION,
           'new_inference_requests': 0, 'quality_acceptance': None,
           'models': models, 'false_positives': false_positives,
           'false_negatives': false_negatives,
           'reference_file': 'manual-reference-r2.json',
           'excluded_reference_files': ['manual-reference.json']}
args.output.mkdir(parents=True, exist_ok=False)
for name, value in (('rows.json', rows), ('summary.json', summary)):
    with (args.output / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
print(json.dumps(summary, ensure_ascii=False))
if false_positives or false_negatives:
    raise SystemExit(2)
