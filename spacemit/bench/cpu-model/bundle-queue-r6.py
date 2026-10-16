#!/usr/bin/env python3
"""发布第六轮固定二进制的标准 Python 重放包。"""
import argparse
from pathlib import Path
import shutil
from common import digest,seal,write
from snapshot import publish

HERE=Path(__file__).resolve().parent


def main(a):
    root=a.work.resolve();portable=root/'portable';portable.mkdir()
    for name in ('common.py','state3.py','state6.py','binary-input.py','replay-queue-r6.py'):
        shutil.copy2(HERE/name,portable/name)
    shutil.copy2(root/'frozen-model.json',portable/'frozen-model.json')
    for name in ('measure','plan.json','prior-model.json','protocol.md'):
        shutil.copy2(root/'payload'/name,portable/name)
    for name in ('frozen-calibration.json','evaluation.json'):
        shutil.copy2(root/name,portable/name)
    seal(portable)
    write(root/'portable-receipt.json',publish(portable,a.output))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);main(p.parse_args())
