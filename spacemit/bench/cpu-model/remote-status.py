#!/usr/bin/env python3
"""限时检查远端批次，并保存连接失败状态。"""
import argparse
import datetime
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

REMOTE='''
import json, pathlib, socket, subprocess, sys
root=pathlib.Path(sys.argv[1]);session=sys.argv[2]
records=[]
for stage in ('training','calibration','test'):
    run=root/('run-'+stage)
    if not run.exists():
        records.append(dict(stage=stage,state='not-started'));continue
    fields={}
    for name in ('phase','exit-status','start-time','end-time'):
        path=run/name
        if path.exists():fields[name]=path.read_text().strip()
    fields['complete_sample_lines']=sum(sum(line.endswith('\\n') for line in path.open()) for path in run.glob('samples-*.jsonl'))
    fields['stage']=stage
    fields['state']='complete' if fields.get('exit-status')=='0' else 'failed' if 'exit-status' in fields else 'active-or-interrupted'
    records.append(fields)
tmux=subprocess.run(['tmux','has-session','-t',session],capture_output=True).returncode==0
print(json.dumps(dict(host=socket.gethostname(),root=str(root),session=session,tmux_session_present=tmux,stages=records)))
'''


def inspect(host,root,session):
    argv=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','ConnectionAttempts=1',
          '-o','ServerAliveInterval=5','-o','ServerAliveCountMax=3',host,
          'python3 - '+shlex.quote(str(root))+' '+shlex.quote(session)]
    try:
        result=subprocess.run(argv,input=REMOTE,text=True,capture_output=True,timeout=30)
    except subprocess.TimeoutExpired:
        return dict(connection='failed',reason='local-timeout',timeout_seconds=30)
    if result.returncode:
        return dict(connection='failed',reason='ssh-or-remote-failure',returncode=result.returncode,stderr=result.stderr[-2000:])
    try:
        value=json.loads(result.stdout)
    except json.JSONDecodeError:
        return dict(connection='failed',reason='invalid-status-response')
    return dict(connection='available',remote=value)


def exit_code(value):
    if value['connection']!='available':return 2
    remote=value['remote']
    if any(row.get('state')=='failed' for row in remote.get('stages',[])):return 3
    if not remote.get('tmux_session_present',False) and any(row.get('state')=='active-or-interrupted' for row in remote.get('stages',[])):return 4
    return 0


def main(a):
    if 'reports/raw' in a.output.as_posix():
        raise ValueError('实时状态不能写入封存目录。')
    value=inspect(a.host,a.root,a.session)
    value.update(checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),host_alias=a.host)
    temporary=a.output.with_name(a.output.name+'.partial')
    with temporary.open('x') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,a.output)
    print(json.dumps(value,ensure_ascii=False))
    code=exit_code(value)
    if code:sys.exit(code)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host',choices=['musepipro-wg','server-wg'],required=True)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--session',required=True)
    p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())
