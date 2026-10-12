#!/usr/bin/env python3
"""按实际动态覆盖缺口安排分项标定，不删除候选。"""
import argparse
from collections import Counter
from pathlib import Path
from analyze import load,write,seal,sha
from k1cost import parameters


def diagnose(source,profiles,output):
    output.mkdir(parents=True,exist_ok=False)
    table,_=parameters(profiles);missing=Counter();gaps=Counter();total=0;measured=0
    host=load(source)
    for row in host['records']:
        cost=row['cost'];total+=cost['counts']['instructions'];measured+=cost['counts'].get('measured',0)
        gaps.update(cost['gaps'])
        for thread in cost['scenarios'][1]['threads'].values():
            for key,count in thread['keys'].items():
                p=table.get(key)
                if p is None or any(m['status']!='measured-positive' for m in p['modes'].values()):missing[key]+=count
    records=[dict(key=key,dynamic_instructions=count,fraction_of_all_instructions=count/total)
             for key,count in missing.most_common()]
    result=dict(schema=2,source_sha256=sha(source),instructions=total,measured_instructions=measured,
        missing_components=records,model_gaps=dict(gaps),automatic_action='none',
        priority_basis='dynamic instruction count; not predicted contribution to wall time',
        next_work=['measure frequent scalar address operations and compressed instructions',
                   'measure vector load result readiness and vector stores',
                   'measure cache and shared bandwidth with matched memory access patterns',
                   'measure matched full-operator ROI cycles on independent shapes',
                   'freeze a model before residual calibration and reserve new groups for validation'])
    write(output/'diagnosis.json',result)
    lines=['# K1 模型补齐顺序','','顺序按实际动态指令数量排列，不表示这些指令占据同等比例的耗时。',
        '所有算法候选均保留。','', '| 分项键 | 未直接标定的动态指令数 | 全部指令占比 |',
        '| --- | ---: | ---: |']
    for row in records[:30]:
        key=row['key'].replace('|','\\|')
        lines.append(f'| {key} | {row["dynamic_instructions"]} | {100*row["fraction_of_all_instructions"]:.3f}% |')
    lines+=['','加载结果可用时刻、向量配置切换和线程共享带宽也需要单独标定。',
        '指令覆盖率不能代替周期误差与算法收益误差。','']
    (output/'report.md').write_text('\n'.join(lines));seal(output)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
    p.add_argument('--profiles',type=Path,nargs='+',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();diagnose(a.source,a.profiles,a.output)
