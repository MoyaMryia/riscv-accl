#!/usr/bin/env python3
"""提取没有符号长度的直线汇编函数，遇到分支必须停止。"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('assembly_inventory',HERE.parent/'assembly-inventory.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


def main(args):
    elf = args.elf.resolve()
    tools = {name:Path(str(args.tool_prefix)+name) for name in ('nm','objdump')}
    symbols = subprocess.check_output([tools['nm'],'--defined-only',elf],text=True)
    selected = [line.split() for line in symbols.splitlines() if line.split()[-1] == args.symbol]
    if len(selected) != 1: raise ValueError('符号不唯一')
    start = int(selected[0][0],16)
    text = subprocess.check_output([tools['objdump'],'-d','-z','-M','no-aliases',
        '--start-address='+str(start),'--stop-address='+str(start+2048),elf],text=True)
    limit = None
    for line in text.splitlines():
        match = module.LINE.match(line)
        if not match: continue
        address,word,name,operands = match.groups()
        if name in ('c.jr','jalr') and operands.strip() in ('ra','zero,0(ra)'):
            limit = int(address,16)+len(word)//2; break
        if name.startswith('b') or name in ('jal','c.j','c.jalr','jalr','c.beqz','c.bnez','c.jr'):
            raise ValueError('函数不是直线路径')
    if limit is None: raise ValueError('没有找到明确的返回边界')
    instructions = module.extract(text,start,limit-start)
    result = {'schema':1,'elf':str(elf),'elf_sha256':module.sha(elf),
        'scope':'straight-line function through first return; source range audit required',
        'functions':[{'symbol':args.symbol,'start':start,'size_bytes':limit-start,
            'static_instructions':len(instructions),'instructions':instructions}]}
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'actual.asm').write_text(text)
    (args.output/'inventory.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf',type=Path); parser.add_argument('symbol')
    parser.add_argument('output',type=Path); parser.add_argument('--tool-prefix',type=Path,required=True)
    main(parser.parse_args())
