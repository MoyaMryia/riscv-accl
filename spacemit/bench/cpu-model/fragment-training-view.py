#!/usr/bin/env python3
"""核验完整原生证据，只发布计划指定的训练观测。"""
import argparse
import importlib.util
import json
from pathlib import Path
from common import digest,read,write

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fragment_assess',HERE/'fragment-assess.py')
assessor=importlib.util.module_from_spec(spec);spec.loader.exec_module(assessor)


def extract(payload,qemu,native,output):
    payload,qemu,native=map(Path,(payload,qemu,native))
    for root in (payload,qemu,native):assessor.checker.receipts(root)
    if (native/'exit-status').read_text().strip()!='0':raise ValueError('原生批次未成功结束。')
    plan=read(payload/'input-plan.json');identity=digest(payload/'fragment')
    if identity!=read(qemu/'result.json')['binary_sha256']:raise ValueError('数值与原生载荷 ELF 不同。')
    numerical={p.name for p in (qemu/'dumps').iterdir()}
    if numerical!={p.name for p in (native/'dumps').iterdir()}:raise ValueError('原生转储缺失。')
    for name in numerical:
        if (native/'dumps'/name).read_bytes()!=(qemu/'dumps'/name).read_bytes():raise ValueError('原生与 QEMU 数值不同。')
    chosen=[c for c in plan['cases'] if c.get('split')=='training']
    if not chosen or any(c['offset']!=0 for c in chosen):raise ValueError('训练必须只使用已声明的对齐配置。')
    ids={c['id'] for c in chosen};known={c['id'] for c in plan['cases']};sessions=[]
    for i in (0,1):
        rows=[json.loads(line) for line in (native/f'samples-{i}.jsonl').read_text().splitlines()]
        if len(rows)!=len(plan['cases'])*len(plan['kernels'])*15 or any(r['case'] not in known for r in rows):
            raise ValueError('完整观测数量或配置身份不同。')
        sessions.append([r for r in rows if r['case'] in ids])
    selected=dict(plan,cases=chosen)
    training=assessor.summarize(selected,sessions)
    if training['status']!='paired-observations-verified':raise ValueError('训练观测斜率无效。')
    result=dict(schema=1,split='training',plan_sha256=digest(payload/'input-plan.json'),binary_sha256=identity,
        native_receipt_sha256=digest(native/'SHA256SUMS'),qemu_receipt_sha256=digest(qemu/'SHA256SUMS'),
        records=[dict(case=case['configuration']['id'],kernel=k['id'],cycles_per_call=case['median_cost_per_call'][k['id']]['cycles'])
                 for case in training['cases'] for k in plan['kernels']],
        numerical_dump_pairs=len(numerical),observations=training['observations'],
        validation_observations_published=False,prediction_confidence=None)
    write(output,result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('payload','qemu','native','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();result=extract(a.payload,a.qemu,a.native,a.output)
    print(json.dumps(dict(training_cells=len(result['records']),numerical_dump_pairs=result['numerical_dump_pairs'])))
