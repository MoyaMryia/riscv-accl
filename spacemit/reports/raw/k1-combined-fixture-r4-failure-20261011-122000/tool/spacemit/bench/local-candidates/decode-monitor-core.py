"""从已封存的原 core 恢复相关函数和字符串字段。"""

import argparse
import hashlib
import json
from pathlib import Path
import struct


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('core', type=Path)
parser.add_argument('executable', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
core = args.core.read_bytes()
executable = args.executable.read_bytes()
assert hashlib.sha256(core).hexdigest() == '19bf24992c34b9d2960a5b86fc8891abbd33c720bbad53f4ddc63c1954029d76'
assert hashlib.sha256(executable).hexdigest() == '630db2135a33fddb6416e77341ef48e5376f903fcb81d3e0fe36a496a4d0e2d0'
offset = struct.unpack_from('<Q', core, 32)[0]
entry_size, count = struct.unpack_from('<HH', core, 54)
segments = [struct.unpack_from('<IIQQQQQQ', core, offset + i * entry_size) for i in range(count)]


def memory(address, size=8):
    for entry in segments:
        if entry[0] == 1 and entry[3] <= address and address + size <= entry[3] + entry[5]:
            offset = entry[2] + address - entry[3]
            return core[offset:offset+size]
    raise ValueError('core 未保存地址：' + hex(address))


def word(address):
    return int.from_bytes(memory(address), 'little')


def unicode(address):
    assert word(address + 8) == 0x607cd0
    length = word(address + 16)
    state = int.from_bytes(memory(address + 32, 4), 'little')
    kind = (state >> 2) & 7
    assert length <= 10000 and (state >> 5) & 1
    start = address + (40 if (state >> 6) & 1 else 56)
    return memory(start, length * kind).decode({1: 'latin1', 2: 'utf-16-le', 4: 'utf-32-le'}[kind])


parent = 0x3f8554eac0
assert word(parent + 8) == 0x5fb3c0
module = word(parent + 104)
wrong = 0x6a0028
record = {'状态': '原 core 字段已恢复；根因仍未定位',
          'core_sha256': hashlib.sha256(core).hexdigest(),
          'executable_sha256': hashlib.sha256(executable).hexdigest(),
          '父对象地址': hex(parent), '父对象类型地址': hex(word(parent + 8)),
          '名称': unicode(word(parent + 32)), '限定名称': unicode(word(parent + 40)),
          '模块字段偏移': 104, '模块字段地址': hex(module), '模块字符串': unicode(module),
          '故障参数地址': hex(wrong), '故障参数类型字段': hex(word(wrong + 8)),
          '两个指针异或': hex(module ^ wrong),
          '解释限制': '字段布局按上游 CPython 3.12.3 与本构建类型地址解释。不是完整调试符号恢复，也不能证明不一致来自硬件。',
          '布局资料': ['https://github.com/python/cpython/blob/v3.12.3/Include/cpython/funcobject.h',
                       'https://github.com/python/cpython/blob/v3.12.3/Include/cpython/unicodeobject.h']}
with args.output.open('x') as stream:
    stream.write(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(record, ensure_ascii=False, indent=2))
