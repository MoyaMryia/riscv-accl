#!/usr/bin/env python3
"""用标准 Python 记录固定重放的时间与峰值内存。"""
import argparse
import importlib.util
from pathlib import Path
import os
import socket
import resource
import sys
import time

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','output','runtime'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();sys.path.insert(0,str(a.root))
    from common import digest,write
    start=time.perf_counter()
    spec=importlib.util.spec_from_file_location('portable_replay',a.root/'replay-write-r5.py')
    replay=importlib.util.module_from_spec(spec);spec.loader.exec_module(replay)
    result=replay.replay(a.root);elapsed=time.perf_counter()-start
    write(a.output,result)
    write(a.runtime,dict(replay_seconds=elapsed,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        python=sys.version,host=socket.gethostname(),platform=list(os.uname()),prediction_sha256=result['prediction_sha256'],
        wrapper_sha256=digest(__file__),limits=['时间包含导入、二进制解析与模型计算。','时间不包含构建、轨迹采集与结果文件写入。','峰值内存来自 Linux ru_maxrss。']))
