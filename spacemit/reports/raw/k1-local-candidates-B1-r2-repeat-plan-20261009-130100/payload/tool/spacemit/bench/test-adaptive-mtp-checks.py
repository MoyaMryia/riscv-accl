#!/usr/bin/env python3
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('checks',Path(__file__).with_name('mtp-quality-checks.py'))
checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)
reference='''def run_spans(text):
    out=[]
    for i,ch in enumerate(text):
        if out and out[-1][0]==ch:
            out[-1]=(ch,out[-1][1],i+1)
        else:
            out.append((ch,i,i+1))
    return out
def expand_spans(spans):
    out=[]
    pos=0
    for item in spans:
        if not isinstance(item,(list,tuple)) or len(item)!=3:
            raise ValueError('item')
        ch,start,end=item
        if not isinstance(ch,str) or len(ch)!=1 or type(start) is not int or type(end) is not int:
            raise ValueError('type')
        if start!=pos or end<=start:
            raise ValueError('offset')
        out.append(ch*(end-start))
        pos=end
    return ''.join(out)
'''
result=checks.check_code('unicode_offsets',reference)
assert result['pass'] and result['checks']>100,result
wrong=checks.check_code('unicode_offsets',reference.replace('start!=pos or end<=start','end<=start'))
assert not wrong['pass'],wrong
print('held-out Unicode offsets: valid code passes, gap/overlap bug fails')
