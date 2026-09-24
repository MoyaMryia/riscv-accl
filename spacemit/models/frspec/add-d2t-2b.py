import argparse
import io
import os
import struct
from pathlib import Path

parser = argparse.ArgumentParser(description='Add the frequency-ranked 32k MTP head to a Qwen3.5-2B GGUF')
parser.add_argument('src', type=Path, help='base MTP Q4_0 GGUF with Q4_0 token embeddings')
parser.add_argument('dst', type=Path, help='new GGUF path (must not already exist)')
parser.add_argument('--map', type=Path, default=Path(__file__).resolve().parent / 'd2t-map32k.bin')
args = parser.parse_args()
src = args.src
dst = args.dst
map_data = args.map.read_bytes()
token_ids = struct.unpack('<32768q', map_data)
head_name = 'blk.24.nextn.shared_head_head.weight'
map_name = 'd2t'
n_rows = len(token_ids)
align_up = lambda x, a: ((x + a - 1) // a) * a

def read_exact(f, n):
    data = f.read(n)
    if len(data) != n:
        raise EOFError
    return data

def read_string(f):
    n, = struct.unpack('<Q', read_exact(f, 8))
    return read_exact(f, n).decode()

def skip_value(f, t):
    if t in (0, 1, 7):
        f.seek(1, 1)
    elif t in (2, 3):
        f.seek(2, 1)
    elif t in (4, 5, 6):
        f.seek(4, 1)
    elif t == 8:
        n, = struct.unpack('<Q', read_exact(f, 8))
        f.seek(n, 1)
    elif t == 9:
        et, = struct.unpack('<I', read_exact(f, 4))
        n, = struct.unpack('<Q', read_exact(f, 8))
        for _ in range(n):
            skip_value(f, et)
    elif t in (10, 11, 12):
        f.seek(8, 1)
    else:
        raise ValueError(t)

def write_info(o, name, dims, typ, off):
    b = name.encode()
    o.write(struct.pack('<Q', len(b)))
    o.write(b)
    o.write(struct.pack('<I', len(dims)))
    o.write(struct.pack('<%dQ' % len(dims), *dims))
    o.write(struct.pack('<IQ', typ, off))

with src.open('rb') as f:
    magic = read_exact(f, 4)
    version, n_tensors, n_kv = struct.unpack('<IQQ', read_exact(f, 20))
    assert magic == b'GGUF' and version == 3
    kv_start = f.tell()
    align = 32
    for _ in range(n_kv):
        key = read_string(f)
        typ, = struct.unpack('<I', read_exact(f, 4))
        if key == 'general.alignment':
            assert typ == 4
            align, = struct.unpack('<I', read_exact(f, 4))
        else:
            skip_value(f, typ)
    kv_end = f.tell()
    f.seek(kv_start)
    kv_blob = read_exact(f, kv_end - kv_start)

    infos = []
    for _ in range(n_tensors):
        name = read_string(f)
        nd, = struct.unpack('<I', read_exact(f, 4))
        dims = struct.unpack('<%dQ' % nd, read_exact(f, 8 * nd))
        typ, off = struct.unpack('<IQ', read_exact(f, 12))
        infos.append((name, dims, typ, off))
    old_data_start = align_up(f.tell(), align)
    assert head_name not in {e[0] for e in infos}
    assert map_name not in {e[0] for e in infos}
    embd = next(e for e in infos if e[0] == 'token_embd.weight')
    assert embd[2] == 2 and embd[1][0] == 2048 and embd[1][1] == 248320
    assert len(set(token_ids)) == n_rows and min(token_ids) >= 0 and max(token_ids) < embd[1][1]
    row_bytes = embd[1][0] // 32 * 18
    head_bytes = n_rows * row_bytes
    old_data_bytes = os.path.getsize(src) - old_data_start
    head_off = align_up(old_data_bytes, align)
    map_off = align_up(head_off + head_bytes, align)

    header = io.BytesIO()
    header.write(magic)
    header.write(struct.pack('<IQQ', version, n_tensors + 2, n_kv))
    header.write(kv_blob)
    for name, dims, typ, off in infos:
        write_info(header, name, dims, typ, off)
    write_info(header, head_name, (embd[1][0], n_rows), 2, head_off)
    write_info(header, map_name, (n_rows,), 27, map_off)
    new_data_start = align_up(header.tell(), align)
    header.write(bytes(new_data_start - header.tell()))

    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open('xb') as o:
        o.write(header.getvalue())
        f.seek(old_data_start)
        remain = old_data_bytes
        while remain:
            chunk = read_exact(f, min(remain, 8 * 1024 * 1024))
            o.write(chunk)
            remain -= len(chunk)
        o.write(bytes(new_data_start + head_off - o.tell()))
        embd_start = old_data_start + embd[3]
        for tid in token_ids:
            f.seek(embd_start + tid * row_bytes)
            o.write(read_exact(f, row_bytes))
        o.write(bytes(new_data_start + map_off - o.tell()))
        o.write(map_data)
    assert os.path.getsize(dst) == new_data_start + map_off + len(map_data)
print({'src':str(src),'dst':str(dst),'n_tensors':n_tensors+2,'head_bytes':head_bytes,'map_bytes':len(map_data),'file_bytes':os.path.getsize(dst)})
