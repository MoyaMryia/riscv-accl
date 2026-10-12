#!/usr/bin/env python3
"""Launch isolated recurrent fusion tests and collection in tmux."""
import argparse
import datetime
import importlib.util
from pathlib import Path
from zoneinfo import ZoneInfo

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('launcher',HERE/'start-k1-prefill-profile.py')
launcher=importlib.util.module_from_spec(spec); spec.loader.exec_module(launcher)
FILES=('k1-gdn-test.py','test-k1-gdn.cpp','run-k1-gdn-test-board.sh','k1-ime-test.py',
       'make-k1-ime-candidate.py','bench-lifecycle.py','k1-fast-test.py')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,default=HERE.parent/'reports/raw'/
                       ('k1-gdn-'+datetime.datetime.now(ZoneInfo('Asia/Singapore')).strftime('%Y%m%d-%H%M%S')))
    parser.add_argument('--evidence',type=Path,default=HERE.parent/'reports/raw/k1-fast-20261001-224957')
    parser.add_argument('--collect-only',action='store_true')
    args=parser.parse_args()
    if args.collect_only: launcher.collect(args.run_dir.resolve())
    else: launcher.start(args.run_dir.resolve(),args.evidence.resolve(),FILES,'run-k1-gdn-test-board.sh','k1_gdn_')
