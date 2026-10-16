#!/usr/bin/env python3
"""核验一次完整调用的 ELF 指令、控制路径与访存回调。"""
import argparse
from collections import Counter
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import struct
from common import digest, write

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('invocation_binary', HERE / 'binary-input.py')
binary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binary)


class CoverageError(ValueError):
    pass


def signed(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def operation(name, reads=(), writes=(), control='next', **fields):
    return dict(name=name, reads=[r for r in reads if r != 'x0'],
                writes=[r for r in writes if r != 'x0'], control=control, **fields)


@lru_cache(maxsize=8192)
def decode(word, size):
    """只解码明确列出的 RV64 指令，不以默认算术类型代替未知编码。"""
    rd, a, b = (word >> 7) & 31, (word >> 15) & 31, (word >> 20) & 31
    d, x, y = f'x{rd}', f'x{a}', f'x{b}'
    opcode, f3, f7 = word & 127, (word >> 12) & 7, word >> 25
    if size == 4 and word & 3 == 3 and word & 31 != 31:
        if opcode in (0x37, 0x17):
            return operation('lui' if opcode == 0x37 else 'auipc', writes=[d])
        if opcode in (0x13, 0x1b):
            wide = opcode == 0x1b
            names = {0: 'addi', 2: 'slti', 3: 'sltiu', 4: 'xori', 6: 'ori', 7: 'andi'}
            if f3 in names and (not wide or f3 == 0):
                return operation(names[f3] + ('w' if wide else ''), [x], [d])
            shift = word >> (25 if wide else 26)
            if f3 == 1 and shift == 0:
                return operation('slliw' if wide else 'slli', [x], [d])
            if f3 == 5 and shift in (0, 0x20 if wide else 0x10):
                return operation(('sra' if shift else 'srl') + ('iw' if wide else 'i'), [x], [d])
        if opcode in (0x33, 0x3b):
            wide = opcode == 0x3b
            names = {0: 'add', 1: 'sll', 2: 'slt', 3: 'sltu', 4: 'xor', 5: 'srl', 6: 'or', 7: 'and'}
            if f7 == 0 and (not wide or f3 in (0, 1, 5)):
                return operation(names[f3] + ('w' if wide else ''), [x, y], [d])
            if f7 == 0x20 and f3 in (0, 5):
                return operation(('sub' if f3 == 0 else 'sra') + ('w' if wide else ''), [x, y], [d])
            if f7 == 1 and (not wide or f3 in (0, 4, 5, 6, 7)):
                names = ('mul', 'mulh', 'mulhsu', 'mulhu', 'div', 'divu', 'rem', 'remu')
                return operation(names[f3] + ('w' if wide else ''), [x, y], [d])
        if opcode == 3 and f3 in range(7):
            return operation(('lb', 'lh', 'lw', 'ld', 'lbu', 'lhu', 'lwu')[f3], [x], [d],
                             memory_bytes=(1, 2, 4, 8, 1, 2, 4)[f3], store=False)
        if opcode == 0x23 and f3 < 4:
            return operation(('sb', 'sh', 'sw', 'sd')[f3], [x, y],
                             memory_bytes=1 << f3, store=True)
        if opcode == 0x63 and f3 in (0, 1, 4, 5, 6, 7):
            offset = ((word >> 31) << 12) | (((word >> 7) & 1) << 11)
            offset |= ((word >> 25) & 63) << 5 | ((word >> 8) & 15) << 1
            return operation({0:'beq', 1:'bne', 4:'blt', 5:'bge', 6:'bltu', 7:'bgeu'}[f3],
                             [x, y], control='branch', offset=signed(offset, 13))
        if opcode == 0x6f:
            offset = ((word >> 31) << 20) | (((word >> 12) & 255) << 12)
            offset |= ((word >> 20) & 1) << 11 | ((word >> 21) & 1023) << 1
            return operation('jal', writes=[d], control='direct', offset=signed(offset, 21), link=rd)
        if opcode == 0x67 and f3 == 0:
            return operation('jalr', [x], [d], control='indirect', link=rd, base=a,
                             offset=signed(word >> 20, 12))
        if opcode == 0x57 and f3 == 7 and word >> 31 == 0:
            return operation('vsetvli', [x], [d, 'vl', 'vtype'], vtype=(word >> 20) & 2047)
        if opcode == 0x57 and word >> 26 == 23 and ((word >> 25) & 1) == 1 and b == 0 and f3 in (3, 4):
            return operation('vmv.v.i' if f3 == 3 else 'vmv.v.x',
                             ['vl', 'vtype'] + ([x] if f3 == 4 else []), vector_register=rd, vector_write=True)
        if opcode == 0x27 and word >> 26 == 0 and ((word >> 25) & 1) == 1 and b == 0 and f3 == 0:
            return operation('vse8.v', [x, 'vl', 'vtype'], memory_bytes='vl', store=True,
                             vector_register=rd, vector_write=False)
    if size == 2 and word < 65536 and word & 3 != 3:
        quadrant, top = word & 3, word >> 13
        crd, rs2 = (word >> 7) & 31, (word >> 2) & 31
        dest, source = f'x{crd}', f'x{rs2}'
        ca, cb = f'x{8 + ((word >> 7) & 7)}', f'x{8 + ((word >> 2) & 7)}'
        immediate = ((word >> 2) & 31) | ((word >> 12) & 1) << 5
        if quadrant == 0:
            if top == 0 and word & 0x1fe0:
                return operation('c.addi4spn', ['x2'], [cb])
            if top in (2, 3):
                return operation('c.lw' if top == 2 else 'c.ld', [ca], [cb],
                                 memory_bytes=4 if top == 2 else 8, store=False)
            if top in (6, 7):
                return operation('c.sw' if top == 6 else 'c.sd', [ca, cb],
                                 memory_bytes=4 if top == 6 else 8, store=True)
        if quadrant == 1:
            if top == 0:
                return operation('c.addi', [dest], [dest])
            if top == 1 and crd:
                return operation('c.addiw', [dest], [dest])
            if top == 2:
                return operation('c.li', writes=[dest])
            if top == 3 and crd and immediate:
                return operation('c.addi16sp' if crd == 2 else 'c.lui', ['x2'] if crd == 2 else [], [dest])
            if top == 4:
                mode = (word >> 10) & 3
                if mode < 3:
                    return operation(('c.srli', 'c.srai', 'c.andi')[mode], [ca], [ca])
                mode = (word >> 5) & 3
                if not word & 4096 or mode < 2:
                    name = ('c.sub', 'c.xor', 'c.or', 'c.and')[mode] if not word & 4096 else ('c.subw', 'c.addw')[mode]
                    return operation(name, [ca, cb], [ca])
            if top == 5:
                offset = ((word >> 12) & 1) << 11 | ((word >> 11) & 1) << 4
                offset |= ((word >> 9) & 3) << 8 | ((word >> 8) & 1) << 10
                offset |= ((word >> 7) & 1) << 6 | ((word >> 6) & 1) << 7
                offset |= ((word >> 3) & 7) << 1 | ((word >> 2) & 1) << 5
                return operation('c.j', control='direct', offset=signed(offset, 12), link=0)
            if top in (6, 7):
                offset = ((word >> 12) & 1) << 8 | ((word >> 10) & 3) << 3
                offset |= ((word >> 5) & 3) << 6 | ((word >> 3) & 3) << 1 | ((word >> 2) & 1) << 5
                return operation('c.beqz' if top == 6 else 'c.bnez', [ca],
                                 control='branch', offset=signed(offset, 9))
        if quadrant == 2:
            if top == 0:
                return operation('c.slli', [dest], [dest])
            if top in (2, 3) and crd:
                return operation('c.lwsp' if top == 2 else 'c.ldsp', ['x2'], [dest],
                                 memory_bytes=4 if top == 2 else 8, store=False)
            if top in (6, 7):
                return operation('c.swsp' if top == 6 else 'c.sdsp', ['x2', source],
                                 memory_bytes=4 if top == 6 else 8, store=True)
            if top == 4 and crd:
                high = bool(word & 4096)
                if not rs2:
                    return operation('c.jalr' if high else 'c.jr', [dest], ['x1'] if high else [],
                                     control='indirect', link=1 if high else 0, base=crd, offset=0)
                return operation('c.add' if high else 'c.mv', [dest, source] if high else [source], [dest])
    raise CoverageError(f'未覆盖的指令：{size} 字节，{word:0{size*2}x}。')


def executable_sections(path):
    data = Path(path).read_bytes()
    if data[:6] != b'\x7fELF\x02\x01' or len(data) < 64:
        raise CoverageError('ELF 必须为 64 位小端格式。')
    h = struct.unpack_from('<16sHHIQQQIHHHHHH', data)
    if h[2] != 243 or h[11] != 64 or not h[12] or h[6] + 64*h[12] > len(data):
        raise CoverageError('ELF 目标或节表不完整。')
    sections = []
    for i in range(h[12]):
        s = struct.unpack_from('<IIQQQQIIQQ', data, h[6] + 64*i)
        if not s[2] & 4:
            continue
        if s[1] != 1 or s[4] + s[5] > len(data):
            raise CoverageError('可执行节没有完整文件内容。')
        sections.append((s[3], data[s[4]:s[4]+s[5]]))
    sections.sort()
    if not sections or any(a + len(body) > b for (a, body), (b, _) in zip(sections, sections[1:])):
        raise CoverageError('可执行节缺失或重叠。')
    return sections


def validate_vector(row, op):
    if op['name'] == 'vsetvli' or 'vector_register' not in op:
        return op
    vl, vtype, vlenb, start = (row.get(k) for k in ('vl', 'vtype', 'vlenb', 'vstart'))
    if any(type(x) is not int for x in (vl, vtype, vlenb, start)):
        raise CoverageError('向量指令缺少动态状态。')
    # 当前只接入未掩码、e8、整数 LMUL 的移动与连续写入。
    lmul = vtype & 7
    if vtype & ~255 or (vtype >> 3) & 7 or lmul > 3 or start != 0 or vlenb <= 0 or vlenb & (vlenb-1):
        raise CoverageError('向量状态超出当前 e8 与整数 LMUL 范围。')
    count = 1 << lmul
    register = op['vector_register']
    if not 0 <= vl <= vlenb*count or register % count or register + count > 32:
        raise CoverageError('向量长度或寄存器组无效。')
    op = dict(op, reads=list(op['reads']), writes=list(op['writes']))
    op['writes' if op['vector_write'] else 'reads'].extend(f'v{i}' for i in range(register, register+count))
    if op.get('memory_bytes') == 'vl':
        op['memory_bytes'] = vl
    return op


def audit(path, elf, symbol):
    first, body = binary.function(elf, symbol)
    sections = executable_sections(elf)
    instructions, begin, end = [], None, None
    callbacks = Counter()
    for line in Path(path).read_text().splitlines():
        row = json.loads(line)
        if end is not None:
            raise CoverageError('结束后仍有轨迹事件。')
        kind = row.get('kind')
        if kind == 'begin' and begin is None and not instructions:
            if row.get('entry') != first or type(row.get('return_pc')) is not int or row['return_pc'] <= 0:
                raise CoverageError('调用入口或返回地址不同。')
            begin = row
        elif kind == 'instruction' and begin:
            if row.get('seq') != len(instructions)+1 or row.get('cpu') != begin.get('cpu') or row.get('size') not in (2, 4):
                raise CoverageError('指令序号、处理器或长度无效。')
            pc, size = row['pc'], row['size']
            if pc == begin['return_pc']:
                raise CoverageError('轨迹包含调用返回后的指令。')
            matches = [data[pc-base:pc-base+size] for base, data in sections if base <= pc and pc+size <= base+len(data)]
            if len(matches) != 1 or int(row['encoding'], 16) != int.from_bytes(matches[0], 'little'):
                raise CoverageError('完整调用指令与 ELF 不同。')
            op = validate_vector(row, decode(int(row['encoding'], 16), size))
            instructions.append(dict(row, operation=op, memory=[]))
        elif kind == 'memory' and instructions:
            if row.get('seq') != len(instructions) or type(row.get('store')) is not bool:
                raise CoverageError('访存没有对应指令。')
            if type(row.get('address')) is not int or row['address'] < 0 or row['address'] >= 2**64:
                raise CoverageError('访存地址无效。')
            size = row.get('bytes')
            if type(size) is not int or size not in (1, 2, 4, 8, 16, 32, 64) or row['address']+size > 2**64:
                raise CoverageError('访存长度无效。')
            instructions[-1]['memory'].append(row)
            callbacks['store' if row['store'] else 'load'] += 1
        elif kind == 'end' and begin:
            end = row
        else:
            raise CoverageError('轨迹事件顺序或类型无效。')
    if not instructions or not end or any(end.get(k) is not value for k, value in dict(closed=True, truncated=False, failure=False).items()):
        raise CoverageError('调用没有完整返回。')
    if end.get('instructions') != len(instructions) or end.get('recorded') != len(instructions) or end.get('memory_callbacks') != sum(callbacks.values()):
        raise CoverageError('调用结束计数不同。')
    if instructions[0]['pc'] != first:
        raise CoverageError('首条指令不是函数入口。')
    counts, edges, bytes_count, touches = Counter(), Counter(), Counter(), {'load':set(), 'store':set()}
    outside, vector_states, indirect_targets = 0, Counter(), Counter()
    stack = [begin['return_pc']]
    for index, row in enumerate(instructions):
        pc, size, op, memory = row['pc'], row['size'], row['operation'], row['memory']
        target = instructions[index+1]['pc'] if index+1 < len(instructions) else begin['return_pc']
        control = op['control']
        if control == 'next' and target != pc+size:
            raise CoverageError('非控制指令后出现轨迹空档。')
        if control in ('direct', 'branch'):
            allowed = [pc+op['offset']] + ([pc+size] if control == 'branch' else [])
            if target not in allowed:
                raise CoverageError('实际跳转与指令编码不同。')
        if control != 'next':
            edges[f'{control}:{"taken" if target != pc+size else "fallthrough"}'] += 1
        if control == 'indirect':
            indirect_targets[f'{pc:x}:{target:x}'] += 1
        if op.get('link') in (1, 5):
            stack.append(pc+size)
        elif control == 'indirect' and op.get('link') == 0 and op.get('base') in (1, 5) and op.get('offset') == 0:
            if not stack or stack.pop() != target:
                raise CoverageError('调用返回栈与实际路径不同。')
        if 'memory_bytes' in op:
            addresses = [item['address']+i for item in memory for i in range(item['bytes'])]
            expected = op['memory_bytes']
            if len(addresses) != expected or len(set(addresses)) != expected or (addresses and max(addresses)-min(addresses)+1 != expected):
                raise CoverageError('访存回调不完整、重叠或不连续。')
            if any(item['store'] != op['store'] for item in memory):
                raise CoverageError('访存方向与指令不同。')
            direction = 'store' if op['store'] else 'load'
            touches[direction].update(addresses)
            bytes_count[direction] += expected
        elif memory:
            raise CoverageError('非访存指令出现访存回调。')
        counts[op['name']] += 1
        outside += not first <= pc < first+len(body)
        if 'vector_register' in op:
            vector_states[f'vl={row["vl"]},vtype={row["vtype"]},vlenb={row["vlenb"]},vstart={row["vstart"]}'] += 1
    if stack:
        raise CoverageError('轨迹结束时调用栈仍未返回。')
    result = dict(status='complete-invocation-audited', trace_sha256=digest(path), binary_sha256=digest(elf),
        symbol=symbol, entry=first, return_pc=begin['return_pc'], instructions=len(instructions),
        instructions_outside_symbol=outside, compressed_instructions=sum(r['size']==2 for r in instructions),
        instruction_counts=dict(sorted(counts.items())), control_edges=dict(sorted(edges.items())),
        indirect_targets=dict(sorted(indirect_targets.items())), vector_states=dict(sorted(vector_states.items())),
        memory_callbacks=dict(callbacks), memory_bytes=dict(bytes_count),
        distinct_virtual_bytes={key:len(value) for key,value in touches.items()},
        K1_cycles=None, prediction_confidence=None, automatic_performance_rejection=False,
        limits=['完整调用轨迹不是性能精度证明。', '虚拟访存字节数不是缓存流量。',
                '间接目标来自实际轨迹，没有独立重放全部寄存器值。',
                '当前调用栈检查只覆盖 x1 与 x5 的标准调用和返回形式。',
                '首次调用轨迹不证明热重复调用具有相同路径或向量状态。'])
    return result, instructions


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--elf', type=Path, required=True)
    p.add_argument('--trace', type=Path, required=True)
    p.add_argument('--symbol', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result, _ = audit(a.trace, a.elf, a.symbol)
    write(a.output, result)
    print(json.dumps(result, ensure_ascii=False))
