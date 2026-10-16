"""在交付默认值下检查 TCM 设备访问和两模型短推理。"""
from pathlib import Path
import hashlib
import json
import os
import signal
import subprocess
import threading
import time
import urllib.error
import urllib.request
from tcm import Runtime, TCMError


ROOT = Path(__file__).resolve().parent
BUNDLE = Path.home() / 'Projects/riscv-accl-bench-2026-09-27/k1-committee-release-20261016-r1'
LIB = Path.home() / 'Projects/llm-bench/.toolchain/spine-tcm/libspine_tcm.so.3.0.1'
LOCK = Path.home() / 'Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock'
SERVER_SHA = 'f254f174919c0a97ef34366f116705f6d22574cab4c2bfc39928c0d315b5bfbd'
LIB_SHA = 'cafb7ae99e0490e3df2f5b29c44c41e87dc07413a85bf19e7f4e68c0e99c4e2b'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while data := stream.read(8 * 1024 * 1024):
            h.update(data)
    return h.hexdigest()


def save(path, record):
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')


def request(path, data=None):
    payload = None if data is None else json.dumps(data).encode()
    query = urllib.request.Request('http://127.0.0.1:18556' + path, data=payload,
                                   headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(query, timeout=120) as response:
        return json.load(response)


def snapshot(pid, folder, phase):
    maps = Path(f'/proc/{pid}/maps').read_text()
    (folder / (phase + '.maps')).write_text(maps)
    fdinfo = Path(f'/proc/{pid}/fdinfo/9').read_text()
    assert os.stat(f'/proc/{pid}/fd/9').st_ino == LOCK.stat().st_ino
    assert 'FLOCK' in fdinfo and 'WRITE' in fdinfo
    (folder / (phase + '.lock')).write_text(fdinfo)
    return {'phase': phase, 'pid': pid, 'device_maps': [x for x in maps.splitlines() if '/dev/tcm' in x],
            'runtime_maps': [x for x in maps.splitlines() if 'libspine_tcm' in x or 'libspert' in x]}


def main():
    assert os.environ.get('TMUX') and os.environ.get('K1_PACKAGE_LOCK_FD') == '9'
    assert 'FLOCK' in Path('/proc/self/fdinfo/9').read_text()
    assert subprocess.run(['pgrep', '-x', 'llama-server'], stdout=subprocess.DEVNULL).returncode == 1
    assert sha(BUNDLE / 'runtime/build/bin/llama-server') == SERVER_SHA
    assert sha(LIB) == LIB_SHA
    expected = json.loads((ROOT / 'expected-files.json').read_text())
    assert all(sha(BUNDLE / name) == value for name, value in expected.items())
    runtime = Runtime(LIB)
    status = runtime.status()
    save(ROOT / 'runtime-status.json', status)
    try:
        with runtime.acquire(0) as block:
            probe = {'status': 'real-read-pass', 'hex': block.read(16).hex()}
    except TCMError as error:
        probe = {'status': 'explicit-rejection', 'message': str(error)}
    save(ROOT / 'middleware-probe.json', probe)
    checks = []
    for model in ('2B', '4B'):
        folder = ROOT / model
        folder.mkdir()
        model_path = Path.home() / f'Projects/spacemit-llama/models/Qwen3.5-{model}-MTP-Q4_0-embQ4_0-dv64k.gguf'
        argv = ['python3', str(BUNDLE / 'runtime/package/start.py'), '--model', str(model_path),
                '--port', '18556', '--receipt', str(folder / 'launch.json')]
        save(folder / 'controller-command.json', argv)
        with (folder / 'server.log').open('w') as log:
            process = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, pass_fds=(9,), start_new_session=True)
            try:
                deadline = time.monotonic() + 300
                while time.monotonic() < deadline:
                    assert process.poll() is None, '服务在就绪前退出。'
                    try:
                        if request('/health').get('status') == 'ok':
                            break
                    except (urllib.error.URLError, TimeoutError, ConnectionError):
                        pass
                    time.sleep(0.5)
                else:
                    raise TimeoutError('服务就绪超时。')
                assert sha(Path(f'/proc/{process.pid}/exe')) == SERVER_SHA
                props = request('/props')
                save(folder / 'properties.json', props)
                assert props['total_slots'] == 1 and props['default_generation_settings']['n_ctx'] == 12288
                snapshots = [snapshot(process.pid, folder, 'ready')]
                env = Path(f'/proc/{process.pid}/environ').read_bytes().split(b'\0')
                selected = [x.decode() for x in env if x.startswith((b'SPINE_', b'SPACEMIT_', b'GGML_', b'LLAMA_', b'LD_LIBRARY_PATH=', b'LD_PRELOAD='))]
                save(folder / 'effective-environment.json', selected)
                assert not any(x.startswith(('SPINE_', 'SPACEMIT_', 'GGML_', 'LLAMA_', 'LD_PRELOAD=')) for x in selected)
                payload = {'prompt': 'Write the number one.', 'n_predict': 4, 'temperature': 0,
                           'seed': 1, 'cache_prompt': False, 'stream': False}
                save(folder / 'request.json', payload)
                answer, errors = [], []
                def invoke():
                    try:
                        answer.append(request('/completion', payload))
                    except Exception as error:
                        errors.append(repr(error))
                thread = threading.Thread(target=invoke)
                thread.start()
                samples = 0
                while thread.is_alive():
                    snapshots.append(snapshot(process.pid, folder, f'active-{samples:03d}'))
                    samples += 1
                    thread.join(0.5)
                assert not errors, errors
                save(folder / 'response.json', answer[0])
                assert 0 < answer[0]['tokens_predicted'] <= 4
                snapshots.append(snapshot(process.pid, folder, 'complete'))
                save(folder / 'mapping-summary.json', snapshots)
                checks.append({'model': model, 'pid': process.pid, 'short_request_completed': True,
                               'tokens_predicted': answer[0]['tokens_predicted'],
                               'snapshots': len(snapshots), 'device_maps': sum(len(x['device_maps']) for x in snapshots),
                               'runtime_loaded': all(bool(x['runtime_maps']) for x in snapshots)})
            finally:
                if process.poll() is None:
                    os.kill(process.pid, signal.SIGTERM)
                try:
                    code = process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    os.kill(process.pid, signal.SIGKILL)
                    code = process.wait(timeout=10)
                (folder / 'server-exit-status').write_text(str(code) + '\n')
                assert code == 0, code
    save(ROOT / 'summary.json', {'status': 'pass', 'server_sha256': SERVER_SHA,
                                'tcm_library_sha256': LIB_SHA, 'middleware': probe,
                                'runtime': status, 'checks': checks,
                                'performance_claim': False, 'hardware_write_test': False})
    print('两模型短请求与 TCM 调查已完成。', flush=True)


if __name__ == '__main__':
    main()
