#!/usr/bin/env python3
"""重放有独立后测记录的混合指令模型。"""
import argparse
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();example=HERE/'examples/schedule-family-v5'
    subprocess.run([sys.executable,HERE/'schedule-family.py','predict',
        '--plan',example/'plan.json','--model',example/'model.json',
        '--calibration',example/'calibration.json','--output',a.output],check=True)
