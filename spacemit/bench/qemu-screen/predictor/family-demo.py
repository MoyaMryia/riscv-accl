#!/usr/bin/env python3
"""重放有独立检查记录的完整算子预测示例。"""
import argparse
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();example=HERE/'examples/conv-family-v3'
    subprocess.run([sys.executable,HERE/'family-predict.py',example/'model.json',
        '--features',example/'features.json','--plan',example/'plan.json',
        '--calibration',example/'calibration.json','--output',a.output],check=True)
