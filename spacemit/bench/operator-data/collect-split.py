#!/usr/bin/env python3
"""复用训练批次的二进制，在冻结模型后采集校准或后测分组。"""
import json
from pathlib import Path
import shutil
import sys
import traceback

import collect
import model
import summarize


def prepare_frozen():
    request = json.loads(Path('stage-request.json').read_text())
    source = Path(request['source_batch'])
    frozen = json.loads(Path('model.json').read_text())
    plan = json.loads(Path('plan.json').read_text())
    model.verify(frozen, 'operator-shape-model')
    model.check_plan(plan)
    if request['model_sha256'] != frozen['sha256'] or model.digest(plan) != frozen['plan_sha256']:
        raise ValueError('frozen model or plan')
    if request['split'] == 'test':
        bounds = json.loads(Path('calibration.json').read_text())
        model.verify_calibration(bounds, frozen, plan)
        if request['calibration_sha256'] != bounds['sha256']:
            raise ValueError('frozen calibration')
    summary = summarize.summarize(source)
    if model.digest(summary) not in frozen['training_summaries_sha256']:
        raise ValueError('source is not a model training batch')
    if model.execution_identity(source) != frozen['execution_identity']:
        raise ValueError('source binary identity')
    for family in ('ime', 'conv'):
        shutil.copytree(source/family, Path(family), symlinks=True)
    if model.execution_identity(Path.cwd()) != frozen['execution_identity']:
        raise ValueError('copied binary identity')
    Path('numeric').mkdir()
    Path('timing').mkdir()
    collect.save('host.json', collect.snapshot())
    collect.save('source-batch.json', dict(path=str(source), summary_sha256=model.digest(summary),
                                          frozen_artifacts_sha256=collect.digest(source/'frozen-artifacts.json')))
    files = {str(p.relative_to(Path.cwd())): collect.digest(p) for p in Path.cwd().rglob('*')
             if p.is_file() and p.name not in ['commands.jsonl', 'driver.log', 'state.json']}
    collect.save('frozen-artifacts.json', files)
    return collect.digest(Path('frozen-artifacts.json'))


if __name__ == '__main__':
    try:
        request = json.loads(Path('stage-request.json').read_text())
        if request['split'] not in ('calibration', 'test'):
            raise ValueError('stage split')
        collect.main(request['split'], prepare_frozen)
    except BaseException as error:
        if Path('state.json').exists():
            state = json.loads(Path('state.json').read_text())
            state.update(status='failed', error=str(error), failed=collect.now())
            collect.save('state.json', state)
        traceback.print_exc()
        sys.exit(1)
