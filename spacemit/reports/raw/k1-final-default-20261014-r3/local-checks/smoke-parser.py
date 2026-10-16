"""在最终构建中核验没有性能参数的解析器初始化。"""
import json
import os
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent
assert os.environ.get('TMUX') and os.environ.get('K1_PACKAGE_LOCK_FD') == '9'
os.fstat(9)
output = root / 'parser-r2'
assert not output.exists()
output.mkdir()
env = {k: v for k, v in os.environ.items()
    if not k.startswith(('SPINE_', 'SPACEMIT_', 'GGML_', 'LLAMA_', 'OMP_', 'GOMP_', 'KMP_'))
    and k not in ('LD_LIBRARY_PATH', 'LD_PRELOAD', 'LD_AUDIT')}
env['LD_LIBRARY_PATH'] = ':'.join(map(str, (root / 'final-r2/build/bin',
    Path.home() / 'Projects/llm-bench/.toolchain/spine-tcm',
    Path.home() / 'Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib')))
argv = [str(root / 'final-r2/build/bin/llama-server'), '--help']
(output / 'command.json').write_text(json.dumps(dict(argv=argv, environment=dict(LD_LIBRARY_PATH=env['LD_LIBRARY_PATH'])), indent=2) + '\n')
with (output / 'server.log').open('w') as log:
    result = subprocess.run(argv, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=120, pass_fds=(9,))
(output / 'exit-status').write_text(str(result.returncode) + '\n')
result.check_returncode()
assert '--gpu-layers' in (output / 'server.log').read_text()
print('PASS: numeric CPU default permits argument parser initialization')
