#!/usr/bin/env python3
"""Start a hash-verified local model with the release's matched profiles."""
import argparse
import hashlib
import json
import os
from pathlib import Path

HERE=Path(__file__).resolve().parent


def verify_model(model, manifest):
    expected=next((r['sha256'] for r in manifest['models'].values() if r['filename']==model.name),None)
    if expected is None: raise ValueError('model filename is absent from the release manifest')
    h=hashlib.sha256()
    with model.open('rb') as source:
        for chunk in iter(lambda:source.read(4*1024*1024),b''): h.update(chunk)
    if h.hexdigest()!=expected: raise ValueError('model SHA-256 differs from the measured model')
    return expected


def environment(profile, runtime):
    env={k:v for k,v in os.environ.items() if not k.startswith('SPINE_')}
    env.update(SPINE_FA_WIDE_TILE='1',SPINE_FA_K1_LAYOUT='0',SPINE_K1_GEMM_ROUTE='3' if profile=='optimized' else '0')
    env['LD_LIBRARY_PATH']=runtime
    return env


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server',required=True,type=Path); parser.add_argument('--model',required=True,type=Path)
    parser.add_argument('--profile',choices=('baseline','optimized'),default='baseline')
    parser.add_argument('--runtime',required=True,help='TCM:SPERT:build/bin library directories')
    parser.add_argument('--port',type=int,default=8080)
    args=parser.parse_args()
    try: verify_model(args.model,json.loads((HERE/'manifest.json').read_text()))
    except (ValueError,OSError) as error: parser.exit(1,str(error)+'\n')
    command=[str(args.server.resolve()),'-m',str(args.model.resolve()),'--alias','local',
        '-t','4','-c','6144','--parallel','1','-b','32','-ub','32','-fa','on',
        '-ctk','f16','-ctv','f16','-ngl','0','--no-context-shift','--host','127.0.0.1','--port',str(args.port)]
    os.execve(command[0],command,environment(args.profile,args.runtime))
