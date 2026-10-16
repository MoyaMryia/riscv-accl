#!/usr/bin/env python3
"""执行配对夹具的完整数值检查与有限轨迹采集，保留模型缺口。"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time
from common import digest,read,seal,write

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('source_fragment_binary',HERE/'binary-input.py')
binary=importlib.util.module_from_spec(spec);spec.loader.exec_module(binary)


def receipts(root):
    root=Path(root).resolve()
    count=0
    for line in (root/'SHA256SUMS').read_text().splitlines():
        expected,name=line.split('  ',1);path=(root/name).resolve()
        if not path.is_relative_to(root) or digest(path)!=expected:
            raise ValueError('夹具或采集收据不同。')
        count+=1
    return count


def audit_trace(path,elf,symbol):
    first,data=binary.function(elf,symbol)
    events=memory=segments=0;previous=None;end=None;stores=loads=0
    for line in Path(path).read_text().splitlines():
        row=json.loads(line)
        if end is not None:raise ValueError('轨迹结束后仍有记录。')
        if row['kind']=='end':end=row;continue
        if row['kind']=='instruction':
            offset=row['pc']-first;size=row['size']
            if row['seq']!=events+1 or size not in (2,4) or not 0<=offset<=len(data)-size:
                raise ValueError('函数轨迹序号或范围无效。')
            if int(row['encoding'],16)!=int.from_bytes(data[offset:offset+size],'little'):
                raise ValueError('动态指令与 ELF 不同。')
            if previous is None or previous['segment']!=row['segment']:
                if row['segment']!=segments+1:raise ValueError('轨迹段不连续。')
                segments+=1
            previous=row;events+=1
        elif row['kind']=='memory':
            if previous is None or row['seq']!=previous['seq'] or type(row['store']) is not bool:
                raise ValueError('访存记录没有对应指令。')
            if not isinstance(row['address'],int) or row['address']<0 or row['bytes'] not in (1,2,4,8,16,32):
                raise ValueError('访存范围无效。')
            memory+=1;stores+=row['store'];loads+=not row['store']
        else:raise ValueError('未知轨迹事件。')
    if not end or end.get('failure') is not False or end.get('truncated') is not False:
        raise ValueError('轨迹没有完整有效结束。')
    if end.get('recorded')!=events or end.get('instructions')!=events or end.get('memory_callbacks')!=memory or not events:
        raise ValueError('轨迹结束计数不同。')
    return dict(instructions=events,memory_callbacks=memory,loads=loads,stores=stores,segments=segments,
                sha256=digest(path),function_bytes=len(data),
                limits=['只核验函数地址范围内的轨迹，不包含范围外被调用函数。','完整轨迹不表示模型覆盖全部指令。'])


def check(payload,qemu,plugin,output):
    payload=Path(payload).resolve();qemu=Path(qemu).resolve();plugin=Path(plugin).resolve()
    receipts(payload);plan=read(payload/'input-plan.json');build=read(payload/'build-receipt.json')
    elf=payload/'fragment'
    if digest(elf)!=build['binary_sha256']:raise ValueError('构建二进制身份不同。')
    out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'dumps').mkdir();(out/'traces').mkdir()
    env=dict(os.environ)
    libraries=str(qemu.parent.parent/'lib')
    env['LD_LIBRARY_PATH']=libraries+((':'+env['LD_LIBRARY_PATH']) if env.get('LD_LIBRARY_PATH') else '')
    common=[str(qemu),'-cpu','max,vlen=256,elen=64,vext_spec=v1.0']
    argv=[*common,str(elf),'check-all',str(out/'dumps')]
    write(out/'numerical-command.json',argv);started=time.perf_counter()
    with (out/'numerical.log').open('x') as log:
        subprocess.run(argv,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
    numerical_seconds=time.perf_counter()-started
    expected={f'{c["id"]}-{k["id"]}-seed{s}.bin' for c in plan['cases'] for k in plan['kernels'] for s in (0,1,17)}
    if {p.name for p in (out/'dumps').iterdir()}!=expected:raise ValueError('完整数值转储数量不同。')
    for case in plan['cases']:
        for seed in (0,1,17):
            data=[(out/'dumps'/f'{case["id"]}-{k["id"]}-seed{seed}.bin').read_bytes() for k in plan['kernels']]
            if len(set(data))!=1:raise ValueError('不同实现的完整数值转储不同。')
    records=[]
    for ki,kernel in enumerate(plan['kernels']):
        first,body=binary.function(elf,kernel['symbol']);prefix=out/'traces'/kernel['id']
        argv=[*common,'-plugin',f'{plugin},start={first},end={first+len(body)},out={prefix},max=200000',
              str(elf),'check','0',str(ki),'17',str(out/f'{kernel["id"]}-trace-dump.bin'),'exact']
        write(out/(kernel['id']+'-trace-command.json'),argv);started=time.perf_counter()
        with (out/(kernel['id']+'-trace.log')).open('x') as log:
            subprocess.run(argv,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=45)
        elapsed=time.perf_counter()-started
        audit=audit_trace(str(prefix)+'-cpu0.jsonl',elf,kernel['symbol'])
        expected_dump=out/'dumps'/f'{plan["cases"][0]["id"]}-{kernel["id"]}-seed17.bin'
        if (out/f'{kernel["id"]}-trace-dump.bin').read_bytes()!=expected_dump.read_bytes():
            raise ValueError('轨迹执行与数值检查输出不同。')
        gap=None
        try:binary.loop(elf,kernel['symbol'])
        except (ValueError,KeyError) as error:gap=str(error)
        records.append(dict(id=kernel['id'],symbol=kernel['symbol'],trace=audit,trace_seconds=elapsed,
                            fixed_loop_adapter_gap=gap,K1_cycles=None,prediction_confidence=None,
                            scope_gap='真实函数含多循环、写入或函数边界；本轮不产生完整函数成本预测。'))
    result=dict(status='numerically-checked-model-gap',binary_sha256=digest(elf),qemu_sha256=digest(qemu),
                plugin_sha256=digest(plugin),numerical_dumps=len(expected),numerical_seconds=numerical_seconds,
                records=records,retained_candidates=[k['id'] for k in plan['kernels']],automatic_full_test=False,
                next_action='small-paired-native-test',prediction_confidence=None,
                limits=['本轮没有完整真实函数的已校准模型。','原生小规模实测用于获取所选配置下的直接证据。'])
    write(out/'result.json',result);seal(out)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload',type=Path,required=True);parser.add_argument('--qemu',type=Path,required=True)
    parser.add_argument('--plugin',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();result=check(a.payload,a.qemu,a.plugin,a.output)
    print(json.dumps(dict(status=result['status'],numerical_dumps=result['numerical_dumps']),ensure_ascii=False))
