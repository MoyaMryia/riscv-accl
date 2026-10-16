#!/usr/bin/env python3
"""从实际 ELF 与完整轨迹生成有范围限制的状态模型输入。"""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import struct
from common import digest,read,write


class CoverageError(ValueError):
    pass


def function(path,symbol):
    data=Path(path).read_bytes()
    if data[:6]!=b'\x7fELF\x02\x01' or len(data)<64:
        raise CoverageError('必须提供 64 位小端 ELF。')
    header=struct.unpack_from('<16sHHIQQQIHHHHHH',data)
    if header[2]!=243:raise CoverageError('ELF 目标不是 RISC-V。')
    offset,size,count=header[6],header[11],header[12]
    if size!=64 or not count or offset+size*count>len(data):
        raise CoverageError('ELF 节表不完整或格式未覆盖。')
    sections=[struct.unpack_from('<IIQQQQIIQQ',data,offset+i*size) for i in range(count)]
    matches=[]
    for section in sections:
        if section[1]!=2:continue
        if section[6]>=len(sections) or section[9]!=24 or section[5]%24:
            raise CoverageError('ELF 符号表格式未覆盖。')
        strings=sections[section[6]]
        names=data[strings[4]:strings[4]+strings[5]]
        for position in range(section[4],section[4]+section[5],24):
            name,info,other,index,address,length=struct.unpack_from('<IBBHQQ',data,position)
            end=names.find(b'\0',name)
            if end<0:raise CoverageError('ELF 符号名不完整。')
            if names[name:end].decode(errors='strict')!=symbol:continue
            if info&15!=2 or not length or index>=len(sections):
                raise CoverageError('符号不是有长度的函数。')
            source=sections[index]
            first=source[4]+address-source[3]
            if not source[2]&4 or address<source[3] or address+length>source[3]+source[5] or first+length>len(data):
                raise CoverageError('函数范围不属于完整可执行节。')
            matches.append((address,data[first:first+length]))
    if len(matches)!=1:raise CoverageError('函数符号缺失或不唯一。')
    return matches[0]


def branch_target(word,pc):
    d=((word>>31)<<12)|(((word>>7)&1)<<11)|(((word>>25)&63)<<5)|(((word>>8)&15)<<1)
    if d&4096:d-=8192
    return pc+d


def decode(word):
    destination=(word>>7)&31;left=(word>>15)&31;right=(word>>20)&31
    def op(kind,reads,writes,**fields):
        return dict(kind=kind,reads=[r for r in reads if r!='x0'],writes=[r for r in writes if r!='x0'],**fields)
    if word&0xfe00707f in (0x33,0x02000033):
        return op('mul' if word&0xfe000000 else 'add',[f'x{left}',f'x{right}'],[f'x{destination}'])
    if word&0x707f==0x3003:
        immediate=word>>20
        if immediate&2048:immediate-=4096
        return op('load',[f'x{left}'],[f'x{destination}'],address_base=f'x{left}',address_offset=immediate,memory_bytes=8)
    if word&0xfe00707f==0x02000057:
        return op('vadd',[f'v{left}',f'v{right}'],[f'v{destination}'])
    if word&0xfff0707f==0x02000007:
        return op('vload',[f'x{left}'],[f'v{destination}'],address_base=f'x{left}',memory_bytes=32)
    if word&0xfe00707f==0xe200302b:
        if destination not in (16,18,20,22) or left!=0 or right!=1:
            raise CoverageError('IME 编码超出已核验的固定操作数组合。')
        return op('ime',[f'v{destination}',f'v{destination+1}',f'v{left}',f'v{right}'],[f'v{destination}',f'v{destination+1}'])
    raise CoverageError(f'未覆盖的指令编码：{word:08x}')


def loop(path,symbol):
    address,data=function(path,symbol)
    candidates=[]
    for offset in range(0,len(data)-3,4):
        word=int.from_bytes(data[offset:offset+4],'little');pc=address+offset
        if word&0x707f!=0x1063:continue
        target=branch_target(word,pc)
        if address<=target<pc:
            candidates.append((target,pc))
    if len(candidates)!=1:raise CoverageError('必须有一个已覆盖的后向条件分支。')
    first,last=candidates[0]
    branch=int.from_bytes(data[last-address:last-address+4],'little')
    counter=(branch>>15)&31
    if (branch>>20)&31 or not counter or first%4 or (last-first)%4:
        raise CoverageError('循环分支或指令对齐未覆盖。')
    decrement=int.from_bytes(data[last-address-4:last-address],'little')
    expected=(0xfff<<20)|(counter<<15)|(counter<<7)|0x13
    if decrement!=expected:raise CoverageError('循环计数不是已覆盖的减一形式。')
    instructions=[];encodings={}
    for pc in range(first,last+4,4):
        word=int.from_bytes(data[pc-address:pc-address+4],'little');encodings[pc]=word
        if pc>=last-4:continue
        item=decode(word);item.update(pc=pc,encoding=f'{word:08x}')
        if f'x{counter}' in item['reads']+item['writes']:
            raise CoverageError('循环体使用计数寄存器。')
        instructions.append(item)
    if not instructions:raise CoverageError('循环体为空。')
    return dict(symbol=symbol,first=first,last=last,encodings=encodings,instructions=instructions,counter=counter)


def trace(path,body,expected_iterations):
    index={row['pc']:row for row in body['instructions']}
    pcs=list(body['encodings']);end=None;previous=None;instructions=[];memory={};segments={}
    for line in Path(path).read_text().splitlines():
        event=json.loads(line)
        if end is not None:raise CoverageError('轨迹结束记录后还有事件。')
        kind=event.get('kind')
        if kind=='end':end=event;continue
        if kind=='instruction':
            if event.get('seq')!=len(instructions)+1:raise CoverageError('轨迹序号不连续。')
            pc=event.get('pc')
            if pc not in body['encodings'] or event.get('size')!=4 or int(event['encoding'],16)!=body['encodings'][pc]:
                raise CoverageError('轨迹与实际 ELF 不一致。')
            segment=event.get('segment')
            if not isinstance(segment,int) or segment<1:raise CoverageError('轨迹段身份无效。')
            if previous is not None and segment<previous['segment']:raise CoverageError('轨迹段顺序反转。')
            current=segments.setdefault(segment,[])
            if current and previous['segment']!=segment:raise CoverageError('轨迹段重复进入。')
            if pc!=pcs[len(current)%len(pcs)]:raise CoverageError('动态路径不是完整循环。')
            row=index.get(pc)
            if row and row['kind'] in ('vadd','vload','ime'):
                if any(event.get(k)!=v for k,v in dict(vl=32,vtype=192,vlenb=32,vstart=0).items()):
                    raise CoverageError('动态向量状态超出 e8 m1 VL32 ta ma。')
            current.append(event);instructions.append(event);previous=event
        elif kind=='memory':
            if previous is None or event.get('seq')!=previous['seq']:raise CoverageError('访存事件缺少对应指令。')
            row=index.get(previous['pc'])
            if row is None or row['kind'] not in ('load','vload') or event.get('store') is not False:
                raise CoverageError('访存行为未覆盖。')
            address,size=event.get('address'),event.get('bytes')
            if not isinstance(address,int) or address<0 or not isinstance(size,int) or not 0<size<=32:
                raise CoverageError('访存范围无效。')
            memory.setdefault(previous['seq'],[]).append((address,size))
        else:raise CoverageError('未知轨迹事件。')
    if not end or end.get('failure') is not False or end.get('truncated') is not False:
        raise CoverageError('轨迹缺少完整有效结束记录。')
    if end.get('recorded')!=len(instructions) or end.get('instructions')!=len(instructions):
        raise CoverageError('轨迹结束计数不同。')
    iterations=[];addresses=set();callbacks=0
    for segment,events in segments.items():
        if len(events)%len(pcs):raise CoverageError('轨迹末段未完成循环。')
        iterations.append(len(events)//len(pcs))
        for event in events:
            row=index.get(event['pc']);access=memory.get(event['seq'],[])
            if row and row['kind'] in ('load','vload'):
                touched=[a+i for a,n in access for i in range(n)]
                if len(touched)!=row['memory_bytes'] or len(set(touched))!=len(touched) or max(touched)-min(touched)+1!=len(touched):
                    raise CoverageError('访存回调不完整或不连续。')
                addresses.update(touched);callbacks+=len(access)
            elif access:raise CoverageError('非加载指令出现访存。')
    if iterations!=expected_iterations:raise CoverageError('实际循环次数与调用声明不同。')
    if end.get('memory_callbacks')!=callbacks:raise CoverageError('访存结束计数不同。')
    return dict(instructions=len(instructions),segments=len(segments),iterations=iterations,memory_callbacks=callbacks,distinct_virtual_bytes=len(addresses),
        limits=['虚拟地址覆盖不是实测缓存状态。','轨迹边界之外的依赖与调用成本未建模。'])


def main(a):
    result=dict(schema=1,elf_sha256=digest(a.elf),symbol=a.symbol,automatic_performance_rejection=False,K1_cycles=None,prediction_confidence=None,
        assumptions=[],limits=['本适配器只覆盖单个固定计数循环与六类指令。','未覆盖指令不产生周期预测。','轨迹核验不是性能精度验证。'])
    try:
        body=loop(a.elf,a.symbol)
        result.update(status='binary-covered-trace-required',loop_range=[body['first'],body['last']+4],instructions=body['instructions'])
        if a.trace:
            result['trace_sha256']=digest(a.trace)
            result['dynamic_audit']=trace(a.trace,body,a.iterations)
            result['status']='binary-and-dynamic-path-covered'
        if a.model and a.trace:
            frozen=read(a.model);engine=Path(a.engine)
            if digest(engine)!=frozen['engine_files'].get(engine.name):raise CoverageError('状态引擎与冻结模型身份不同。')
            if any(row['kind'] in ('load','vload') for row in body['instructions']) and a.memory_scenario!='hot-read-only':
                raise CoverageError('缺少已声明的热只读访存场景。')
            spec=importlib.util.spec_from_file_location('bounded_cpu_engine',engine)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            result['K1_cycles']=module.steady(module.compiled(body),module.prepare_parameters(frozen['parameters']))
            result.update(status='fixed-scope-cycle-estimate',model_sha256=digest(a.model))
            result['assumptions']=['使用训练模型的有效发射、依赖与资源参数。','加载采用已声明的热只读场景，不预测缓存缺失。']
            result['limits'].append('新输入没有独立校准区间，不能使用旧批次界限。')
    except (CoverageError,KeyError,ValueError,struct.error) as error:
        result.update(status='coverage-insufficient',gap=str(error),K1_cycles=None)
    write(a.output,result)
    print(json.dumps(dict(status=result['status'],K1_cycles=result['K1_cycles'],gap=result.get('gap')),ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--elf',type=Path,required=True);p.add_argument('--symbol',required=True)
    p.add_argument('--trace',type=Path);p.add_argument('--iterations',type=int,nargs='+',default=[3,17])
    p.add_argument('--model',type=Path);p.add_argument('--engine',type=Path,default=Path(__file__).with_name('state3.py'))
    p.add_argument('--memory-scenario',choices=['unknown','hot-read-only'],default='unknown')
    p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())
