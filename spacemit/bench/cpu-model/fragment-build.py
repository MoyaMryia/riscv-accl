#!/usr/bin/env python3
"""固定源码、构建参数与片段夹具，不自动启动原生性能批次。"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
from common import digest,read,seal,write

HERE=Path(__file__).resolve().parent
IDENTIFIER=re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def validate(plan):
    if plan.get('schema')!=1 or not plan.get('id'):
        raise ValueError('片段构建身份无效。')
    for group in ('cases','kernels'):
        rows=plan[group]
        if not rows or len({r['id'] for r in rows})!=len(rows):
            raise ValueError('片段配置身份缺失或重复。')
        if any(not IDENTIFIER.fullmatch(r['id']) for r in rows):
            raise ValueError('配置身份只能使用 C 标识符。')
    for row in plan['cases']:
        for field in ('work_units','input_bytes','output_bytes'):
            if type(row[field]) is not int or not 0<row[field]<=64*1024*1024:
                raise ValueError('工作量或缓冲区大小无效。')
        if type(row['offset']) is not int or not 0<=row['offset']<64:
            raise ValueError('偏移必须在 0 至 63 字节内。')
    if any(not IDENTIFIER.fullmatch(row['symbol']) for row in plan['kernels']):
        raise ValueError('函数符号无效。')
    if len({row['symbol'] for row in plan['kernels']})!=len(plan['kernels']):
        raise ValueError('函数符号不能重复。')
    if plan['baseline'] not in {row['id'] for row in plan['kernels']}:
        raise ValueError('缺少基线。')
    if not isinstance(plan['contract'],dict) or not plan['contract'].get('boundary'):
        raise ValueError('缺少片段测量边界。')
    return plan


def build(plan_path,compiler,output):
    plan_path=Path(plan_path).resolve();root=plan_path.parent
    plan=validate(read(plan_path));compiler=Path(compiler).absolute()
    out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    source=out/'source';source.mkdir()
    copied=[]
    for record in plan['sources']:
        original=(root/record['path']).resolve()
        if digest(original)!=record['sha256']:
            raise ValueError('待构建源码身份不同。')
        target=source/original.name
        if target.exists():raise ValueError('源文件名重复。')
        shutil.copy2(original,target);copied.append(target)
    for name in ('fragment-fixture.h','fragment-measure.c'):
        if (source/name).exists():raise ValueError('源码覆盖夹具保留文件。')
        shutil.copy2(HERE/name,source/name)
    lines=['#include "fragment-fixture.h"']
    for row in plan['kernels']:
        lines.append(f'extern void {row["symbol"]}(const uint8_t *,uint8_t *,size_t);')
    lines.append('const struct fragment_kernel fragment_kernels[]={')
    lines.extend(f'{{"{row["id"]}",{row["symbol"]}}},' for row in plan['kernels'])
    lines+=['};','const size_t fragment_kernel_count=sizeof fragment_kernels/sizeof fragment_kernels[0];',
            'const struct fragment_case fragment_cases[]={']
    for row in plan['cases']:
        lines.append('{'+','.join([json.dumps(row['id'])]+[str(row[key]) for key in ('work_units','input_bytes','output_bytes','offset')])+'},')
    lines+=['};','const size_t fragment_case_count=sizeof fragment_cases/sizeof fragment_cases[0];']
    (source/'fragment-config.c').write_text('\n'.join(lines)+'\n')
    flags=plan['compiler_flags']
    if not isinstance(flags,list) or any(not isinstance(flag,str) for flag in flags):
        raise ValueError('编译参数必须为字符串数组。')
    argv=[str(compiler),*flags,'-I'+str(source),*[str(path) for path in copied],
          str(source/'fragment-config.c'),str(source/'fragment-measure.c'),'-o',str(out/'fragment')]
    write(out/'input-plan.json',plan);write(out/'build-command.json',argv)
    started=time.perf_counter()
    with (out/'build.log').open('x') as log:
        subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
    elapsed=time.perf_counter()-started
    shutil.copy2(HERE/'run-fragment-board.sh',out/'run-fragment-board.sh')
    write(out/'build-receipt.json',dict(schema=1,plan_sha256=digest(plan_path),compiler_sha256=digest(compiler),
          binary_sha256=digest(out/'fragment'),build_seconds=elapsed,
          sources={path.name:digest(path) for path in sorted(source.iterdir())},
          limits=['夹具提取改变调用边界；原位置性能仍需单独核验。','构建成功不证明数值或预测精度。']))
    seal(out)
    return dict(binary=str(out/'fragment'),binary_sha256=digest(out/'fragment'),build_seconds=elapsed)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan',type=Path);parser.add_argument('--compiler',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(build(args.plan,args.compiler,args.output),ensure_ascii=False))
