#!/usr/bin/env python3
"""在普通工作站重放实际 IME 加载轨迹，并生成投入优先级报告。"""
import argparse
import importlib.util
from pathlib import Path
import time
from analyze import write,seal
from k1cost import predict
from priority import rank

HERE=Path(__file__).resolve().parent


def main(out):
    out=out.resolve();out.mkdir(parents=True,exist_ok=False)
    profiles=HERE/'profiles/k1-cpu0-umode-20261012'
    profiles=[profiles/name for name in ('components.json','ime.json','reductions.json','scalar.json','gaps.json')]
    results={};start=time.perf_counter()
    for arm in ('control','candidate'):
        target=out/arm;target.mkdir()
        results[arm]=predict(HERE/'examples/ime-load-64-case'/arm,profiles,target);seal(target)
    spec=importlib.util.spec_from_file_location('cost_evidence',HERE/'cost-evidence.py')
    adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    row=adapter.pair_record(results['control'],results['candidate'],'ime-load-example',
                            'ime-load-64-case-ROI','frozen-ime-load-control')
    write(out/'plan.json',dict(schema=2,records=[row]))
    target=out/'priority';target.mkdir();rank(out/'plan.json',target);seal(target)
    write(out/'run.json',dict(elapsed_seconds=time.perf_counter()-start,model_sha256=results['control']['model_sha256'],
        purpose='portable actual-trace example; no algorithm accuracy or full IME speed claim',automatic_action='none'))
    seal(out);print(out/'priority/report.md')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();main(a.output)
