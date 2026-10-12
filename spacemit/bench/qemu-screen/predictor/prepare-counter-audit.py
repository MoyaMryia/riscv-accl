#!/usr/bin/env python3
"""冻结通用事件和特权级原始事件的计数器核验载荷。"""
import argparse
from pathlib import Path
import subprocess
from analyze import sha,seal,write

HERE=Path(__file__).resolve().parent


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'measure.c').write_bytes((HERE/'counter-audit.c').read_bytes())
    argv=list(map(str,[a.compiler.resolve(),'-O2','-static','-march=rv64gcv','-Wall','-Wextra','-Werror',out/'measure.c','-o',out/'measure']))
    write(out/'build-command.json',argv)
    with (out/'build.log').open('w') as log:subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,check=True)
    (out/'run-board-calibration.sh').write_bytes((HERE/'run-board-calibration.sh').read_bytes())
    (out/'BINARY-SHA256SUMS').write_text(sha(out/'measure')+'  measure\n');seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path)
    p.add_argument('--compiler',type=Path,required=True);main(p.parse_args())
