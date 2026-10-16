#!/usr/bin/env python3
"""重放实际 ELF 与动态轨迹的有限范围接入范例。"""
import argparse
import importlib.util
from pathlib import Path
import time
from common import digest,read,write
import state3

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('binary_input',HERE/'binary-input.py')
binary=importlib.util.module_from_spec(spec);spec.loader.exec_module(binary)


def main(a):
    start=time.perf_counter();root=a.root.resolve()
    for line in (root/'SHA256SUMS').read_text().splitlines():
        want,name=line.split('  ',1);p=(root/name).resolve()
        if not p.is_relative_to(root) or digest(p)!=want:raise ValueError('便携包收据不同。')
    frozen=read(root/'frozen-model.json');examples=read(root/'binary-examples.json')
    if digest(root/'fixture.elf')!=frozen['binary_sha256'] or digest(Path(state3.__file__))!=frozen['engine_files']['state3.py']:
        raise ValueError('实际 ELF 或状态引擎不同。')
    parameters=state3.prepare_parameters(frozen['parameters']);rows=[]
    for name in examples['ids']:
        body=binary.loop(root/'fixture.elf',name)
        path=root/'example-traces'/(name+'.jsonl')
        audit=binary.trace(path,body,examples['iterations'])
        cycles=state3.steady(state3.compiled(body),parameters)
        if cycles!=frozen['predictions'][name]:raise ValueError('实际机器码路径的预测与冻结记录不同。')
        rows.append(dict(id=name,cycles=cycles,dynamic_audit=audit,trace_sha256=digest(path)))
    write(a.output,dict(status='passed',model_sha256=digest(root/'frozen-model.json'),rows=rows,prediction_confidence=None,
        memory_scenario='declared hot read-only input',limits=['只验证已支持固定循环的接入关系。','新算法独立精度仍待验证。','不使用旧校准界限。']))
    print(f'实际 ELF 范例通过：{len(rows)} 个。主机耗时：{time.perf_counter()-start:.6f} s。')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=HERE);p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())
