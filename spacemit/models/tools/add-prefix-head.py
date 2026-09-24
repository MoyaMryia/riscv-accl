#!/usr/bin/env python3
# Append a truncated draft LM head tensor to a GGUF file.
# new tensor = first N rows of token_embd.weight (Q4_0 prefix slice).
import argparse
import struct, os

parser = argparse.ArgumentParser(description="Append a Q4_0 prefix draft head to a Qwen3.5 MTP GGUF")
parser.add_argument("src", help="input MTP GGUF with Q4_0 token embeddings")
parser.add_argument("dst", help="new output GGUF (must not exist)")
parser.add_argument("--layer", type=int, required=True, help="MTP layer index: 24 for 2B, 32 for 4B")
parser.add_argument("--rows", type=int, default=65536, help="prefix vocabulary rows")
args = parser.parse_args()
SRC = args.src
DST = args.dst
NEW_NAME = f"blk.{args.layer}.nextn.shared_head_head.weight"
EMBD_NAME = "token_embd.weight"
N_ROWS = args.rows
Q4_0 = 2
assert N_ROWS > 0 and args.layer >= 0

def read_string(f):
    (n,) = struct.unpack("<Q", f.read(8))
    return f.read(n).decode()

def skip_value(f, t):
    if t in (0, 1): f.read(1)
    elif t in (2, 3): f.read(2)
    elif t in (4, 5, 6): f.read(4)
    elif t == 7: f.read(1)
    elif t == 8:
        (n,) = struct.unpack("<Q", f.read(8)); f.read(n)
    elif t == 9:
        (et,) = struct.unpack("<I", f.read(4))
        (n,) = struct.unpack("<Q", f.read(8))
        for _ in range(n): skip_value(f, et)
    elif t in (10, 11, 12): f.read(8)
    else: raise ValueError(f"unknown kv type {t}")

f = open(SRC, "rb")
magic = f.read(4); assert magic == b"GGUF"
version, n_tensors, n_kv = struct.unpack("<IQQ", f.read(20))
print(f"version={version} n_tensors={n_tensors} n_kv={n_kv}")

kv_start = f.tell()
align = 32
for _ in range(n_kv):
    key = read_string(f)
    (t,) = struct.unpack("<I", f.read(4))
    if key == "general.alignment":
        (align,) = struct.unpack("<I", f.read(4))
    else:
        skip_value(f, t)
kv_end = f.tell()
print(f"alignment={align} kv_bytes={kv_end-kv_start}")

infos = []
for _ in range(n_tensors):
    name = read_string(f)
    (nd,) = struct.unpack("<I", f.read(4))
    dims = struct.unpack(f"<{nd}Q", f.read(8*nd))
    (tt,) = struct.unpack("<I", f.read(4))
    (off,) = struct.unpack("<Q", f.read(8))
    infos.append((name, nd, dims, tt, off))
infos_end = f.tell()

data_start = (infos_end + align - 1) // align * align
print(f"data_start={data_start}")

embd = None
for name, nd, dims, tt, off in infos:
    if name == EMBD_NAME:
        embd = (dims, tt, off)
assert embd, "token_embd.weight not found"
dims, tt, embd_off = embd
print(f"embd dims={dims} type={tt} off={embd_off}")
assert tt == Q4_0 and dims[0] > 0 and dims[0] % 32 == 0
row_bytes = dims[0] // 32 * 18
assert dims[1] >= N_ROWS
new_data_bytes = row_bytes * N_ROWS
print(f"new tensor rows={N_ROWS} bytes={new_data_bytes}")

# derive each tensor's occupied size from sorted offsets (padding included)
src_size = os.path.getsize(SRC)
sorted_by_off = sorted(infos, key=lambda x: x[4])
sizes = {}
for i, (name, nd, d, tt, o) in enumerate(sorted_by_off):
    if i + 1 < len(sorted_by_off):
        sizes[name] = sorted_by_off[i + 1][4] - o
    else:
        sizes[name] = src_size - data_start - o
last = sorted_by_off[-1]
data_end = last[4] + sizes[last[0]]
new_off = (data_end + align - 1) // align * align

# new info section grows by one entry; all data offsets shift by delta
name_b = NEW_NAME.encode()
entry_size = 8 + len(name_b) + 4 + 8*2 + 4 + 8
new_infos_end = infos_end + entry_size
new_data_start = (new_infos_end + align - 1) // align * align
delta = new_data_start - data_start
print(f"info entry={entry_size} new_data_start={new_data_start} delta={delta} new_off={new_off}")

assert NEW_NAME not in {info[0] for info in infos}, "draft head already exists"
with open(DST, "xb") as o:
    o.write(magic)
    o.write(struct.pack("<IQQ", version, n_tensors + 1, n_kv))
    f.seek(kv_start); o.write(f.read(kv_end - kv_start))
    for name, nd, d, tt, off0 in infos:
        nb = name.encode()
        o.write(struct.pack("<Q", len(nb))); o.write(nb)
        o.write(struct.pack("<I", nd))
        o.write(struct.pack(f"<{nd}Q", *d))
        o.write(struct.pack("<I", tt))
        o.write(struct.pack("<Q", off0))
    o.write(struct.pack("<Q", len(name_b))); o.write(name_b)
    o.write(struct.pack("<I", 2))
    o.write(struct.pack("<QQ", dims[0], N_ROWS))
    o.write(struct.pack("<I", Q4_0))
    o.write(struct.pack("<Q", new_off))
    pad = new_data_start - o.tell()
    assert pad >= 0
    o.write(b"\0" * pad)
    # copy all tensor data to their shifted offsets
    for name, nd, d, tt, off0 in sorted_by_off:
        f.seek(data_start + off0)
        sz = sizes[name]
        cur = new_data_start + off0
        if o.tell() < cur:
            o.write(b"\0" * (cur - o.tell()))
        assert o.tell() == cur, (name, o.tell(), cur)
        remain = sz
        while remain > 0:
            chunk = f.read(min(remain, 8*1024*1024))
            if not chunk: break
            o.write(chunk); remain -= len(chunk)
    # append new tensor: prefix rows of embd
    cur = new_data_start + new_off
    if o.tell() < cur:
        o.write(b"\0" * (cur - o.tell()))
    assert o.tell() == cur
    f.seek(data_start + embd_off)
    remain = new_data_bytes
    while remain > 0:
        chunk = f.read(min(remain, 8*1024*1024))
        o.write(chunk); remain -= len(chunk)
print("done ->", DST, os.path.getsize(DST))
