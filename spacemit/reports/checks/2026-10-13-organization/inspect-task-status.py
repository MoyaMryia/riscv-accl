#!/usr/bin/env python3
"""只读保存本机与 K1 的任务状态。"""
import datetime
import json
import subprocess
from pathlib import Path
from zoneinfo import ZoneInfo

PROBE = '''import json,os,subprocess
from pathlib import Path
root=Path('/tmp')/('tmux-'+str(os.getuid()))
sockets=sorted(str(p) for p in root.iterdir() if p.is_socket()) if root.exists() else []
checks=[]
for socket in sockets:
 r=subprocess.run(['tmux','-S',socket,'list-sessions','-F','#{session_name} #{session_windows} #{session_path}'],text=True,capture_output=True,timeout=10)
 checks.append({'socket':socket,'exit_status':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
r=subprocess.run(['pgrep','-a','-x','llama-server'],text=True,capture_output=True,timeout=10)
print(json.dumps({'uid':os.getuid(),'socket_directory':str(root),'tmux':checks,'servers':{'exit_status':r.returncode,'stdout':r.stdout,'stderr':r.stderr}}))
'''

if __name__ == '__main__':
    result = {'checked_at': datetime.datetime.now(ZoneInfo('Asia/Singapore')).isoformat(),
              'scope': '只读状态；不启动实机测试，不修改设备或任务。'}
    for name, command in [('local', ['python3', '-']),
                          ('board', ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'musepipro', 'python3 -'])]:
        r = subprocess.run(command, input=PROBE, text=True, capture_output=True, timeout=30)
        result[name] = {'command': command, 'exit_status': r.returncode,
                        'state': json.loads(r.stdout) if r.returncode == 0 else None, 'stderr': r.stderr}
    path = Path(__file__).with_name('task-status.json')
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(path)
