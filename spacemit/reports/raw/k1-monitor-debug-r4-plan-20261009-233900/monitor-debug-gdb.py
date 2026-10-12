"""保存诊断进程的信号现场和指针加载检查结果。"""

from collections import deque
import json
import os
from pathlib import Path
import struct
import time

import gdb


out = Path(os.environ['MONITOR_ATTEMPT'])
variant = os.environ['MONITOR_VARIANT']
ring = deque(maxlen=256)
pending = {}
counts = {'loads': 0, 'checks': 0, 'mismatches': 0, 'skipped': 0}
reason = None
exit_code = None
guard_armed = False


def register(name):
    return int(gdb.parse_and_eval('$' + name))


def word(address):
    return int.from_bytes(bytes(gdb.selected_inferior().read_memory(address, 8)), 'little')


def dump(label):
    (out / 'capture-reason.json').write_text(json.dumps(dict(
        reason=label, variant=variant, counts=counts, recent=list(ring)), indent=2) + '\n')
    commands = ['info registers', 'thread apply all bt full', 'info proc mappings',
                'info sharedlibrary', 'info threads', 'x/24i $pc-24', 'x/16gx $sp',
                'x/16gx $s1', 'x/16gx $a0', 'py-bt']
    with (out / 'native-state.log').open('w') as stream:
        for command in commands:
            stream.write('\n' + command + '\n')
            try:
                stream.write(gdb.execute(command, to_string=True))
            except gdb.error as exc:
                stream.write(str(exc) + '\n')
    pid = gdb.selected_inferior().pid
    for name in ('maps', 'status', 'stat', 'limits', 'smaps'):
        try:
            (out / ('proc-' + name + '.txt')).write_bytes(Path('/proc') .joinpath(str(pid), name).read_bytes())
        except OSError as exc:
            (out / ('proc-' + name + '.error')).write_text(str(exc))
    try:
        gdb.execute('generate-core-file ' + str(out / 'captured.core'), to_string=True)
    except gdb.error as exc:
        (out / 'core-error.txt').write_text(str(exc))


class LoadBefore(gdb.Breakpoint):
    def capture(self):
        global reason
        try:
            thread = gdb.selected_thread().global_num
            parent = register('s1')
            if word(parent + 40) != 0x6a00b8:
                counts['skipped'] += 1
                return False
            expected = word(parent + 104)
            pending[thread] = (parent, expected)
            counts['loads'] += 1
        except (gdb.error, gdb.MemoryError) as exc:
            reason = 'guard-read-error: ' + str(exc)
            return True
        return False


class LoadAfter(gdb.Breakpoint):
    def capture(self):
        global reason
        try:
            thread = gdb.selected_thread().global_num
            if thread not in pending:
                return False
            parent, expected = pending.pop(thread)
            actual = register('a0')
            current = word(parent + 104)
            counts['checks'] += 1
            ring.append(dict(parent=hex(parent), before=hex(expected),
                             after_memory=hex(current), register=hex(actual), thread=thread))
            if counts['checks'] % 8 == 0:
                (out / 'guard-progress.json').write_text(json.dumps(dict(counts=counts, recent=list(ring)[-8:])) + '\n')
            if actual != expected or current != expected:
                counts['mismatches'] += 1
                reason = 'load-value-difference'
                return True
        except (KeyError, gdb.error, gdb.MemoryError) as exc:
            reason = 'guard-check-error: ' + str(exc)
            return True
        return False


def exited(event):
    global exit_code
    exit_code = getattr(event, 'exit_code', None)


def stopped(event):
    global reason
    if isinstance(event, gdb.SignalEvent):
        if variant == 'guard' and event.stop_signal == 'SIGUSR2' and not guard_armed:
            ring.append(dict(guard_readiness=True, pc=hex(register('pc'))))
            return
        ring.append(dict(signal=event.stop_signal, pc=hex(register('pc'))))
        if reason is None:
            reason = 'signal:' + event.stop_signal


gdb.events.exited.connect(exited)
gdb.events.stop.connect(stopped)
gdb.execute('set pagination off')
gdb.execute('set confirm off')
gdb.execute('set disable-randomization off')
gdb.execute('set use-coredump-filter off')
gdb.execute('set dump-excluded-mappings on')
for sig in ('SIGSEGV', 'SIGBUS', 'SIGILL', 'SIGABRT', 'SIGUSR2'):
    gdb.execute('handle ' + sig + ' stop print nopass')
gdb.execute('handle SIGUSR1 nostop noprint pass')
if os.environ.get('MONITOR_MALLOC') == 'debug':
    gdb.execute('set environment PYTHONMALLOC debug')
if variant == 'guard':
    # 地址与指令字节必须先匹配原可执行文件。
    executable = Path('/usr/bin/python3.12').read_bytes()
    phoff = struct.unpack_from('<Q', executable, 32)[0]
    phsize, phnum = struct.unpack_from('<HH', executable, 54)
    offset = None
    for index in range(phnum):
        entry = struct.unpack_from('<IIQQQQQQ', executable, phoff + index * phsize)
        kind, flags, file_offset, address, physical, size, memory_size, alignment = entry
        if kind == 1 and address <= 0xa123c < address + size:
            offset = file_offset + 0xa123c - address
    if offset is None or executable[offset:offset+2] != bytes.fromhex('a874'):
        raise RuntimeError('原指令字节不匹配，不能使用固定断点')
source = os.environ['MONITOR_ORIGINAL'] if variant in ('exact', 'malloc-debug') else os.environ['MONITOR_TARGET']
argument = '-X faulthandler ' if variant != 'exact' else ''
gdb.execute('run ' + argument + '- < ' + source)
if variant == 'guard' and reason is None and gdb.selected_inferior().pid:
    if not ring or not ring[-1].get('guard_readiness'):
        raise RuntimeError('指针夹具没有到达准备信号')
    guard_armed = True
    # 导入完成后，只检查原 core 中的函数模块字段。
    before = LoadBefore('*0xa123c', internal=True)
    after = LoadAfter('*0xa123e', internal=True)
    before.condition = '*(unsigned long *)($s1+40) == 0x6a00b8'
    after.condition = before.condition
    for name, breakpoint in [('before', before), ('after', after)]:
        breakpoint.commands = ('silent\npython gdb.set_convenience_variable("monitor_guard_bad", int(' +
                               name + '.capture()))\nif $monitor_guard_bad\n' +
                               'echo Guard stopped.\\n\nelse\ncontinue\nend')
    gdb.execute('continue')
inferior = gdb.selected_inferior()
if inferior.pid:
    frame = gdb.newest_frame()
    if reason is None:
        reason = 'signal-or-unexpected-stop'
    dump(reason)
    if (out / 'faulthandler-ready').exists():
        try:
            gdb.execute('signal SIGUSR1', to_string=True)
        except gdb.error as exc:
            (out / 'python-stack-error.txt').write_text(str(exc))
    if gdb.selected_inferior().pid:
        gdb.execute('kill', to_string=True)
if variant == 'guard' and counts['checks'] == 0 and reason is None:
    reason = 'guard-not-exercised'
result = dict(variant=variant, reason=reason, exit_code=exit_code, counts=counts,
              core_saved=(out / 'captured.core').exists(), time_ns=time.time_ns())
(out / 'debug-result.json').write_text(json.dumps(result, indent=2) + '\n')
gdb.execute('quit ' + ('2' if reason is not None or exit_code != 0 else '0'))
