"""为委员会交付包创建受共用锁保护的部署会话。"""
import argparse
from datetime import datetime
import json
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import sys


def plan(root, model, session, runs, spert=None, tcm=None, port=8080):
    root = root.resolve()
    model = model.resolve(strict=True)
    if not model.is_file():
        raise ValueError('模型路径必须是文件。')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', session):
        raise ValueError('会话名只能含字母、数字、下划线或连字符。')
    if not 1 <= port <= 65535:
        raise ValueError('端口必须在 1～65535 内。')
    runtime = root / 'runtime'
    for name in ('package/with-lock.sh', 'package/start.py', 'build/build-receipt.json',
                 'build/bin/llama-server'):
        if not (runtime / name).is_file():
            raise ValueError('交付文件缺失：' + name)
    run = runs.resolve() / session
    argv = ['bash', str(runtime / 'package/with-lock.sh'), sys.executable,
            str(runtime / 'package/start.py'), '--model', str(model),
            '--port', str(port), '--receipt', str(run / 'launch.json')]
    for name, value in (('--spert', spert), ('--tcm', tcm)):
        if value is not None:
            argv.extend((name, str(value.resolve(strict=True))))
    shell = (shlex.join(argv) + ' > ' + shlex.quote(str(run / 'server.log')) + ' 2>&1; '
             'deploy_status=$?; printf "%s\\n" "$deploy_status" > '
             + shlex.quote(str(run / 'exit-status')) + '; exit "$deploy_status"')
    return {'bundle': str(root), 'model': str(model), 'session': session,
            'run': str(run), 'argv': argv, 'shell': shell,
            'context': 12288, 'performance_flags': [],
            'lock': str(Path.home() / 'Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model', type=Path)
    parser.add_argument('--bundle-root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--session', default='k1_final_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    parser.add_argument('--runs', type=Path, default=Path.home() / 'Projects/k1-final-release-runs')
    parser.add_argument('--spert', type=Path)
    parser.add_argument('--tcm', type=Path)
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--describe', action='store_true')
    args = parser.parse_args()
    try:
        record = plan(args.bundle_root, args.model, args.session, args.runs,
                      args.spert, args.tcm, args.port)
        if args.describe:
            print(json.dumps(record, ensure_ascii=False, indent=2))
            return
        if platform.system() != 'Linux' or platform.machine() != 'riscv64':
            raise ValueError('实际部署必须在 K1 的 Linux RISC-V 64 位用户空间执行。')
        if not shutil.which('tmux') or not shutil.which('flock'):
            raise ValueError('缺少 tmux 或 flock。')
        check = subprocess.run(['tmux', 'has-session', '-t', '=' + args.session],
                               capture_output=True, text=True)
        if check.returncode == 0:
            raise ValueError('同名会话已存在，必须先查看原会话。')
        if check.returncode != 1:
            raise ValueError('无法检查 tmux 会话：' + check.stderr.strip())
        run = Path(record['run'])
        run.mkdir(parents=True, exist_ok=False)
        (run / 'deployment.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        lock = Path(record['lock'])
        lock.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['tmux', 'new-session', '-d', '-s', args.session,
                        '-c', record['bundle'], record['shell']], check=True)
        print('部署会话已创建：' + args.session)
        print('日志目录：' + str(run))
        print('服务就绪状态必须通过 /health 核对；创建会话不表示模型加载成功。')
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
