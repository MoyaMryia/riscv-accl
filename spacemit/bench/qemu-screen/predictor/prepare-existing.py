#!/usr/bin/env python3
"""将既有真实二进制接入统一轨迹接口，不重新编译候选。"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

from analyze import sha, write

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]


def main(args):
    out = args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    prefix = args.qemu_prefix.resolve()
    tools = REPO/'lab/toolchain/toolchain/riscv/bin/riscv64-unknown-linux-gnu-'
    plan = {'schema':1,'qemu':str(prefix/'bin/qemu-riscv64'),'header':str(prefix/'include/qemu-plugin.h'),
        'nm':str(tools)+'nm','cpu':'rv64,v=true,vlen=256,elen=64,zfh=true,zvfh=true',
        'timeout_seconds':180,'sources':{},'cases':[]}
    if args.kind=='conv':
        if not args.conv_plan: raise ValueError('必须提供固定卷积计划')
        original = json.loads(args.conv_plan.read_text())
        plan.update(original,qemu=plan['qemu'],header=plan['header'])
        plan['sources'][str(args.conv_plan.resolve())] = sha(args.conv_plan)
    elif args.kind=='ime':
        root = args.existing.resolve()
        binary = root/'ime-load-run/verify'
        arms = {}
        for arm in ('control','candidate'):
            folder = out/(arm+'-inventory')
            subprocess.run([sys.executable,HERE/'range-inventory.py',binary,'load_'+arm,folder,
                '--tool-prefix',tools],check=True)
            inv = folder/'inventory.json'
            arms[arm] = {'elf':str(binary),'sha256':sha(binary),'symbol':'load_'+arm,'args':['{dump}'],
                'inventory':{'path':str(inv),'sha256':sha(inv)}}
        arms['control']['dump_filename']='complete--.bin'
        plan.update(qemu_args=['-R','4G'],scope='isolated paired load/unpack verifier; no matrix dot timing',
            cases=[dict(id='ime-load-isolated',roi_threads=1,**arms)])
        for path in (root/'ime-load-input').glob('*'):
            if path.is_file(): plan['sources'][str(path)]=sha(path)
    else:
        if not args.loader_control or not args.loader_candidate:
            raise ValueError('必须提供两个臂在 -R 4G 配置下的来宾加载记录')
        root = args.existing.resolve()/'b2-input';arms={}
        for arm,directory,log in [('control','original',args.loader_control),('candidate','b2',args.loader_candidate)]:
            text = log.read_text()
            match = re.search(r'file=libggml-cpu\.so\.0[^\n]*generating link map\s*\n[^\n]*base:\s*(0x[0-9a-f]+)',text)
            if not match: raise ValueError('来宾加载记录没有目标库基址')
            image = root/directory/'libggml-cpu.so.0';binary=root/'test-b2'
            symbols = subprocess.check_output([str(tools)+'nm','-S','--defined-only',image],text=True)
            token = 'flash_attn_ext_f16_one_chunk' if arm=='control' else 'quick_b2_chunkILi'+str(args.tile)+'E'
            matches = [line.split()[-1] for line in symbols.splitlines() if token in line]
            if len(matches)!=1: raise ValueError('实际小块符号不唯一')
            arms[arm] = {'elf':str(binary),'sha256':sha(binary),'image':str(image),'image_sha256':sha(image),
                'load_bias':int(match[1],16),'symbol':matches[0],'args':['--dump','{dump}'],
                'env':{'LD_LIBRARY_PATH':str(image.parent)+':'+str(root/'common'),'SPINE_K1_TRACE':'1'}}
            plan['sources'][str(log.resolve())]=sha(log)
        plan.update(qemu_args=['-R','4G','-L',str(REPO/'lab/toolchain/toolchain/riscv/sysroot')],
            scope='selected actual library functions; bounded trace; no full-workload cost comparison',
            cases=[dict(id='b2-tile'+str(args.tile),roi_thread_policy={'minimum':4,'maximum':8},cache_model=False,**arms)])
        for path in (root/'common').glob('*'):
            if path.is_file(): plan['sources'][str(path)]=sha(path)
    real = prefix/'libexec/qemu-riscv64'
    if real.is_file(): plan['sources'][str(real)] = sha(real)
    plan['sources'][str(HERE/'prepare-existing.py')] = sha(__file__)
    write(out/'plan.json',plan)
    print(out/'plan.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind',choices=['conv','ime','b2']);parser.add_argument('output',type=Path)
    parser.add_argument('--existing',type=Path,default=REPO/'lab/k1-mca-trial-20261011')
    parser.add_argument('--conv-plan',type=Path);parser.add_argument('--tile',type=int,choices=[8,16],default=8)
    parser.add_argument('--loader-control',type=Path);parser.add_argument('--loader-candidate',type=Path)
    parser.add_argument('--qemu-prefix',type=Path,default=REPO/'lab/qemu-host-runtime')
    main(parser.parse_args())
