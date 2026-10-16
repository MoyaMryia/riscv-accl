"""独立检查 TCM 调查的身份、完整短请求、映射和设备失败记录。"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
BOARD = ROOT / 'board/k1-tcm-final-release-20261016-r1'
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    assert (ROOT / 'local-tests-exit-status').read_text().strip() == '0'
    assert 'Ran 10 tests' in (ROOT / 'local-tests.log').read_text()
    assert (BOARD / 'exit-status').read_text().strip() == '0'
    for name in ('audit.py', 'expected-files.json', 'run.sh'):
        assert sha(ROOT / name) == sha(BOARD / name), name
    middleware = ROOT.parents[1] / 'spacemit/tcm/tcm.py'
    assert sha(middleware) == sha(BOARD / 'tcm.py')
    source = json.loads((ROOT / 'source-audit.json').read_text())
    assert len(source) == 4 and all(x['identical'] for x in source.values())
    summary = json.loads((BOARD / 'summary.json').read_text())
    assert summary['status'] == 'pass' and not summary['performance_claim']
    assert not summary['hardware_write_test']
    status = json.loads((BOARD / 'runtime-status.json').read_text())
    assert status['uid'] == 1000 and status['fake'] and not status['available']
    assert status['block_size'] == status['block_count'] == 0
    assert status['devices']['/dev/tcm']['mode'] == '0o600'
    assert not status['devices']['/dev/tcm_sync_mem']['exists']
    assert json.loads((BOARD / 'middleware-probe.json').read_text())['status'] == 'explicit-rejection'
    trace = (BOARD / 'syscalls.log').read_text().splitlines()
    checks = []
    expected_defaults = 'K1_EFFECTIVE_DEFAULTS threads=4 batch_threads=4 batch=32 ubatch=32 context=12288 slots=1 flash=1 gpu=0 key=f16 value=f16 mask=3'
    for row in summary['checks']:
        folder = BOARD / row['model']
        launch = json.loads((folder / 'launch.json').read_text())
        assert launch['argv'][1:] == ['-m', str(Path('/home/moyamryia/Projects/spacemit-llama/models') / f"Qwen3.5-{row['model']}-MTP-Q4_0-embQ4_0-dv64k.gguf"), '--alias', 'local', '--port', '18556']
        assert launch['compiled_policy']['config']['mask'] == 3
        assert (folder / 'server-exit-status').read_text().strip() == '0'
        response = json.loads((folder / 'response.json').read_text())
        assert response['tokens_predicted'] == 4 and response['tokens_evaluated'] == 5
        log = (folder / 'server.log').read_text()
        assert expected_defaults in log and 'falling back to heap' in log
        for phase in ('prefill', 'single'):
            assert f'K1_GEMM_ROUTE mode=3 phase={phase} eligible=1 bypass=1 buffer_size=131072' in log
        maps = list(folder.glob('*.maps'))
        assert len(maps) == row['snapshots']
        for path in maps:
            contents = path.read_text()
            assert '/dev/tcm' not in contents
            assert 'libspine_tcm.so.3.0.1' in contents and 'libspert.so' in contents
            assert 'FLOCK' in path.with_suffix('.lock').read_text()
        own = [line for line in trace if re.match(str(row['pid']) + r'\s', line)]
        dev = [line for line in own if '"/dev/tcm"' in line]
        sync = [line for line in own if '"/dev/tcm_sync_mem"' in line]
        assert dev and all('= -1 EACCES' in line for line in dev)
        assert sync and all('= -1 ENOENT' in line for line in sync)
        checks.append({'model': row['model'], 'pid': row['pid'], 'mapping_snapshots': len(maps),
                       'tcm_open_eacces': len(dev), 'sync_open_enoent': len(sync),
                       'input_tokens': 5, 'output_tokens': 4, 'server_exit': 0})
    assert {x['model'] for x in checks} == {'2B', '4B'}
    device_opens = [line for line in trace if '"/dev/tcm"' in line and 'openat(' in line]
    assert all('= -1 EACCES' in line for line in device_opens)
    files = {str(p.relative_to(BOARD)): sha(p) for p in sorted(BOARD.rglob('*'))
             if p.is_file() and '__pycache__' not in p.parts}
    record = {'status': 'pass', 'checks': checks, 'board_files': files,
              'source_files_identical_to_vendor': 4, 'local_mock_tests': 10,
              'middleware_sha256': sha(middleware), 'hardware_tcm_in_tested_inference': False,
              'hardware_read_write_verified': False, 'performance_claim': False}
    (ROOT / 'verification.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: v for k, v in record.items() if k != 'board_files'}))

if __name__ == '__main__':
    main()
