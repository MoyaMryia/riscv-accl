"""记录隔离监控复现的输入、执行位置和垃圾回收事件。"""

import ast
import faulthandler
import gc
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time


output = Path(os.environ['MONITOR_ATTEMPT'])
source_path = Path(os.environ['MONITOR_ORIGINAL'])
variant = os.environ['MONITOR_VARIANT']
source = source_path.read_text()
trace_fd = os.open(output / 'events.jsonl', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
fault_file = (output / 'python-stack.log').open('w')
faulthandler.enable(file=fault_file, all_threads=True)
faulthandler.register(signal.SIGUSR1, file=fault_file, all_threads=True)
(output / 'faulthandler-ready').touch()
read_text = Path.read_text
blobs = output.parent.parent / 'input-blobs'
blobs.mkdir(exist_ok=True)
counter = 0


def emit(kind, **fields):
    entry = dict(kind=kind, monotonic_ns=time.monotonic_ns(), **fields)
    os.write(trace_fd, (json.dumps(entry, ensure_ascii=False) + '\n').encode())


def captured_text(path, encoding=None, errors=None):
    global counter
    emit('read-start', path=str(path))
    before = path.stat()
    data = path.read_bytes()
    after = path.stat()
    digest = hashlib.sha256(data).hexdigest()
    blob = blobs / digest
    try:
        with blob.open('xb') as stream:
            stream.write(data)
    except FileExistsError:
        pass
    counter += 1
    emit('read-complete', number=counter, path=str(path), sha256=digest,
         size=len(data), before=[before.st_ino, before.st_size, before.st_mtime_ns],
         after=[after.st_ino, after.st_size, after.st_mtime_ns])
    with io.TextIOWrapper(io.BytesIO(data), encoding=encoding, errors=errors) as stream:
        return stream.read()


def trace(frame, event, arg):
    if frame.f_code.co_filename == '<monitor-original>' and event in ('line', 'exception'):
        emit('python-' + event, line=frame.f_lineno,
             exception=str(arg[0].__name__) if event == 'exception' else None)
    return trace


def collection(phase, info):
    emit('gc-' + phase, generation=info['generation'], collected=info.get('collected'),
         uncollectable=info.get('uncollectable'))


def mutate(stop, shadow):
    files = [p for p in shadow.glob('*/summary.json')]
    objects = [json.loads(read_text(p)) for p in files]
    generation = 0
    while not stop.is_set():
        for path, obj in zip(files, objects):
            obj['diagnostic_fixture_generation'] = generation
            temporary = path.with_name('summary.next')
            temporary.write_text(json.dumps(obj))
            temporary.replace(path)
        generation += 1
        stop.wait(0.01)


emit('start', variant=variant, pid=os.getpid(), executable=sys.executable,
     source_sha256=hashlib.sha256(source.encode()).hexdigest(),
     gc_threshold=gc.get_threshold(), affinity=sorted(os.sched_getaffinity(0)),
     version=sys.version, environment={key: os.environ.get(key) for key in
     ('LANG', 'LC_ALL', 'PATH', 'LD_LIBRARY_PATH', 'LD_PRELOAD', 'PYTHONMALLOC', 'PYTHONHASHSEED')})
if variant == 'capture-self-test':
    emit('capture-self-test', signal='SIGUSR2')
    os.kill(os.getpid(), signal.SIGUSR2)
stop = threading.Event()
writer = None
if variant in ('gc-stress', 'guard'):
    shadow = Path(os.environ['MONITOR_SHADOW'])
    tree = ast.parse(source)
    old_base = '/home/moyamryia/Projects/riscv-accl-bench-2026-09-27'
    matches = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and node.value == old_base:
            node.value = str(shadow)
            matches += 1
    if matches != 1:
        raise RuntimeError('隔离输入根目录匹配数量错误')
    code = compile(tree, '<monitor-original>', 'exec')
    if variant == 'gc-stress':
        writer = threading.Thread(target=mutate, args=(stop, shadow), daemon=True)
        writer.start()
        gc.set_threshold(25, 3, 3)
else:
    code = compile(source, '<monitor-original>', 'exec')
Path.read_text = captured_text
sys.settrace(trace)
gc.callbacks.append(collection)
loops = int(os.environ.get('MONITOR_LOOPS', '1'))
if variant == 'guard':
    emit('guard-ready')
    os.kill(os.getpid(), signal.SIGUSR2)
try:
    for index in range(loops):
        emit('iteration-start', iteration=index)
        namespace = {'__name__': '__main__'}
        exec(code, namespace)
        del namespace
        if variant in ('gc-stress', 'guard'):
            gc.collect()
        emit('iteration-complete', iteration=index)
finally:
    stop.set()
    if writer:
        writer.join(timeout=5)
    sys.settrace(None)
    gc.callbacks.remove(collection)
    Path.read_text = read_text
    emit('complete', reads=counter)
    os.close(trace_fd)
