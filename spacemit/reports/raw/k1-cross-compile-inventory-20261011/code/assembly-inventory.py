#!/usr/bin/env python3
"""从目标二进制提取函数汇编清单，不推断板端耗时。"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PREFIX = REPO/'lab/toolchain/toolchain/riscv/bin/riscv64-unknown-linux-gnu-'
LINE = re.compile(r'^\s*([0-9a-f]+):\s+([0-9a-f]+)\s+([A-Za-z_.][\w.]*)\s*(.*)$')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def family(mnemonic):
    if mnemonic == 'ime.signed-vmadot':
        return 'ime-known-encoding'
    if mnemonic.startswith('.'):
        return 'unresolved-encoding'
    if mnemonic.startswith('vset'):
        return 'vector-configuration'
    if mnemonic.startswith(('vfred', 'vred', 'vwred')):
        return 'vector-reduction'
    if mnemonic.startswith(('vle', 'vse', 'vlse', 'vsse', 'vlux', 'vsux', 'vlox', 'vsox', 'vlseg', 'vsseg')) or re.match(r'v[ls][1248]r', mnemonic):
        return 'vector-memory'
    if mnemonic.startswith(('vfmv', 'vmv')):
        return 'vector-transfer'
    if mnemonic.startswith('v'):
        return 'vector-other'
    if mnemonic.startswith(('f', 'c.f')):
        return 'scalar-float-or-memory'
    return 'scalar-other'


def extract(text, first, size):
    instructions = []
    for line in text.splitlines():
        match = LINE.match(line)
        if not match:
            continue
        address, encoded, mnemonic, operands = match.groups()
        address = int(address, 16)
        if not first <= address < first+size:
            continue
        original = mnemonic
        if len(encoded) == 8 and int(encoded, 16) & 0xfe00707f == 0xe200302b:
            mnemonic = 'ime.signed-vmadot'
        instructions.append({'address': address, 'bytes': len(encoded)//2, 'encoding': encoded,
            'mnemonic': mnemonic, 'objdump_mnemonic': original, 'operands': operands,
            'family': family(mnemonic)})
    cursor = first
    for instruction in instructions:
        if instruction['address'] != cursor:
            raise ValueError('disassembly coverage has a gap or overlap')
        cursor += instruction['bytes']
    if cursor != first+size:
        raise ValueError('disassembly coverage differs from symbol size')
    return instructions


def main(args):
    elf, out = args.elf.resolve(), args.output.resolve()
    pattern = re.compile(args.symbol_regex)
    out.mkdir(parents=True, exist_ok=False)
    commands = []

    def run(argv, name):
        argv = list(map(str, argv))
        commands.append(argv)
        value = subprocess.check_output(argv, text=True, stderr=subprocess.STDOUT, timeout=120)
        (out/name).write_text(value)
        return value

    tools = {name: Path(str(args.tool_prefix)+name).resolve() for name in ('nm', 'objdump', 'readelf')}
    header = run([tools['readelf'], '-h', elf], 'elf-header.log')
    if not re.search(r'Machine:\s+RISC-V', header):
        raise ValueError('ELF machine is not RISC-V')
    run([tools['readelf'], '-A', elf], 'elf-attributes.log')
    run([tools['objdump'], '--version'], 'objdump-version.log')
    symbols = run([tools['nm'], '-S', '--defined-only', elf], 'symbols.log')
    selected = []
    for line in symbols.splitlines():
        words = line.split()
        if len(words) == 4 and words[2] in ('t', 'T', 'w', 'W') and pattern.search(words[3]):
            first, size = int(words[0], 16), int(words[1], 16)
            if size:
                selected.append((first, size, words[3]))
    if not selected:
        raise ValueError('no function matches the symbol expression')
    result = {'schema': 1, 'elf': str(elf), 'elf_sha256': sha(elf), 'symbol_regex': args.symbol_regex,
        'scope': 'static function bodies; callees excluded; counts are not execution frequencies',
        'K1_performance': 'unverified', 'dependencies': 'not analyzed',
        'ime_decoder': 'only signed vmadot encoding fe00707f/e200302b',
        'source_sha256': sha(__file__), 'tool_sha256': {key: sha(path) for key, path in tools.items()},
        'functions': []}
    for index, (first, size, name) in enumerate(sorted(selected)):
        assembly = run([tools['objdump'], '-d', '-z', '-M', 'no-aliases',
            '--start-address='+hex(first), '--stop-address='+hex(first+size), elf], f'function-{index:02d}.asm')
        instructions = extract(assembly, first, size)
        mnemonics = Counter(item['mnemonic'] for item in instructions)
        pairs = Counter(a['mnemonic']+' -> '+b['mnemonic'] for a, b in zip(instructions, instructions[1:]))
        record = {'symbol': name, 'start': first, 'size_bytes': size,
            'assembly': f'function-{index:02d}.asm', 'static_instructions': len(instructions),
            'mnemonics': dict(mnemonics.most_common()),
            'families': dict(Counter(item['family'] for item in instructions).most_common()),
            'vector_configurations': [item for item in instructions if item['family'] == 'vector-configuration'],
            'stack_reference_hints': [item for item in instructions if '(sp)' in item['operands']],
            'stack_reference_limit': 'references can be ABI saves or arguments; they do not prove a spill',
            'static_neighbor_pairs': dict(pairs.most_common()),
            'neighbor_limit': 'address neighbors are not dynamic pairs or proven dependencies',
            'unresolved': [item for item in instructions if item['family'] == 'unresolved-encoding'],
            'instructions': instructions}
        result['functions'].append(record)
    (out/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
    (out/'inventory.json').write_text(json.dumps(result, indent=2)+'\n')
    (out/'SHA256SUMS').write_text(''.join(sha(path)+'  '+path.name+'\n' for path in sorted(out.iterdir())
        if path.is_file() and path.name != 'SHA256SUMS'))
    print(out/'inventory.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--symbol-regex', required=True)
    parser.add_argument('--tool-prefix', type=Path, default=PREFIX)
    main(parser.parse_args())
