#!/usr/bin/env python3
# Append Qwen3.5-4B MTP tensors (extracted from HF safetensors) to the 4B Q4_0 GGUF.
# - 8 weight matrices BF16 -> Q4_0; 7 norms BF16 -> F32; add nextn_predict_layers=1
import argparse
import struct, os, json

parser = argparse.ArgumentParser(description="Add Qwen3.5-4B MTP tensors to a fast-Q4_0 GGUF")
parser.add_argument("src", help="4B base GGUF with Q4_0 token embeddings")
parser.add_argument("dst", help="new 4B MTP GGUF (must not exist)")
parser.add_argument("mtp_dir", help="directory with BF16 mtp.* blobs and meta.json")
args = parser.parse_args()
SRC = args.src
DST = args.dst
MTP_DIR = args.mtp_dir
IL = 32
F32, Q4_0 = 0, 2

MAP = [  # (hf_name, gguf_name, target_type)
    ("mtp.fc.weight",                              "blk.%d.nextn.eh_proj.weight" % IL,        Q4_0),
    ("mtp.norm.weight",                            "blk.%d.nextn.shared_head_norm.weight" % IL, F32),
    ("mtp.pre_fc_norm_embedding.weight",           "blk.%d.nextn.enorm.weight" % IL,          F32),
    ("mtp.pre_fc_norm_hidden.weight",              "blk.%d.nextn.hnorm.weight" % IL,          F32),
    ("mtp.layers.0.input_layernorm.weight",        "blk.%d.attn_norm.weight" % IL,            F32),
    ("mtp.layers.0.post_attention_layernorm.weight", "blk.%d.post_attention_norm.weight" % IL, F32),
    ("mtp.layers.0.self_attn.q_proj.weight",       "blk.%d.attn_q.weight" % IL,               Q4_0),
    ("mtp.layers.0.self_attn.k_proj.weight",       "blk.%d.attn_k.weight" % IL,               Q4_0),
    ("mtp.layers.0.self_attn.v_proj.weight",       "blk.%d.attn_v.weight" % IL,               Q4_0),
    ("mtp.layers.0.self_attn.q_norm.weight",       "blk.%d.attn_q_norm.weight" % IL,          F32),
    ("mtp.layers.0.self_attn.k_norm.weight",       "blk.%d.attn_k_norm.weight" % IL,          F32),
    ("mtp.layers.0.self_attn.o_proj.weight",       "blk.%d.attn_output.weight" % IL,          Q4_0),
    ("mtp.layers.0.mlp.gate_proj.weight",          "blk.%d.ffn_gate.weight" % IL,             Q4_0),
    ("mtp.layers.0.mlp.up_proj.weight",            "blk.%d.ffn_up.weight" % IL,               Q4_0),
    ("mtp.layers.0.mlp.down_proj.weight",          "blk.%d.ffn_down.weight" % IL,             Q4_0),
]

def bf16_to_f32(data):
    n = len(data) // 2
    u16 = struct.unpack("<%dH" % n, data)
    out = bytearray(4 * n)
    struct.pack_into("<%dI" % n, out, 0, *[v << 16 for v in u16])
    return out

def f32_to_f16(x):
    return struct.pack("<e", x)

def quant_q4_0(f32data, ne0, ne1):
    # ggml quantize_row_q4_0: per row of ne0, blocks of 32: fp16 d + 16 packed bytes
    nb = ne0 // 32
    out = bytearray()
    for r in range(ne1):
        row = struct.unpack_from("<%df" % ne0, f32data, r * ne0 * 4)
        for b in range(nb):
            blk = row[b*32:(b+1)*32]
            amax, vmax = 0.0, 0.0
            for x in blk:
                if abs(x) > amax: amax, vmax = abs(x), x
            d = vmax / -8.0
            idq = 1.0 / d if d != 0.0 else 0.0
            out += f32_to_f16(d)
            qs = []
            for x in blk:
                q = int(round(x * idq)) + 8
                qs.append(0 if q < 0 else (15 if q > 15 else q))
            for i in range(16):
                out.append(qs[i] | (qs[i+16] << 4))
    return bytes(out)

def read_string(f):
    (n,) = struct.unpack("<Q", f.read(8))
    return f.read(n).decode()

def skip_value(f, t):
    if t in (0, 1, 7): f.read(1)
    elif t in (2, 3): f.read(2)
    elif t in (4, 5, 6): f.read(4)
    elif t == 8:
        (n,) = struct.unpack("<Q", f.read(8)); f.read(n)
    elif t == 9:
        (et,) = struct.unpack("<I", f.read(4))
        (n,) = struct.unpack("<Q", f.read(8))
        for _ in range(n): skip_value(f, et)
    elif t in (10, 11, 12): f.read(8)
    else: raise ValueError("unknown kv type %d" % t)

meta = json.load(open(os.path.join(MTP_DIR, "meta.json")))

# ---- prepare new tensor payloads
new_tensors = []  # (name, dims, type, payload)
for hf, gg, tt in MAP:
    m = meta[hf]
    shape = m["shape"]
    raw = open(m["file"], "rb").read()
    f32 = bf16_to_f32(raw)
    dims = tuple(reversed(shape))
    if tt == F32:
        # Qwen3.5 conversion zero-centers all norm weights: ggml expects (1 + w)
        # (conversion/qwen.py: name.endswith("norm.weight") -> data + 1)
        n = len(f32) // 4
        vals = struct.unpack("<%df" % n, f32)
        payload = struct.pack("<%df" % n, *[v + 1.0 for v in vals])
    else:
        assert dims[0] % 32 == 0, hf
        payload = quant_q4_0(f32, dims[0], dims[1])
    new_tensors.append((gg, dims, tt, payload))
    print("%-42s dims=%-16s type=%d bytes=%d" % (gg, dims, tt, len(payload)))

# ---- parse source
f = open(SRC, "rb")
magic = f.read(4); assert magic == b"GGUF"
version, n_tensors, n_kv = struct.unpack("<IQQ", f.read(20))
kv_start = f.tell()
align = 32
kv_spans = []   # (key, raw_bytes_including_name_and_value)
block_count = None
for _ in range(n_kv):
    e0 = f.tell()
    key = read_string(f)
    (t,) = struct.unpack("<I", f.read(4))
    if key == "general.alignment":
        (align,) = struct.unpack("<I", f.read(4))
    elif key == "qwen35.block_count":
        (block_count,) = struct.unpack("<I", f.read(4))
    else:
        skip_value(f, t)
    e1 = f.tell()
    f.seek(e0)
    kv_spans.append((key, f.read(e1 - e0)))
kv_end = f.tell()
assert block_count == IL, "expected block_count=%d, got %s" % (IL, block_count)
infos = []
for _ in range(n_tensors):
    name = read_string(f)
    (nd,) = struct.unpack("<I", f.read(4))
    dims = struct.unpack("<%dQ" % nd, f.read(8*nd))
    (tt,) = struct.unpack("<I", f.read(4))
    (off,) = struct.unpack("<Q", f.read(8))
    infos.append((name, nd, dims, tt, off))
infos_end = f.tell()
data_start = (infos_end + align - 1) // align * align
print("src: n_tensors=%d n_kv=%d align=%d data_start=%d" % (n_tensors, n_kv, align, data_start))

# occupied sizes from sorted offsets
src_size = os.path.getsize(SRC)
srt = sorted(infos, key=lambda x: x[4])
sizes = {}
for i, (name, nd, d, tt, o) in enumerate(srt):
    sizes[name] = (srt[i+1][4] - o) if i+1 < len(srt) else (src_size - data_start - o)

# ---- build new file
new_kv = b"qwen35.nextn_predict_layers"
kv_extra = struct.pack("<Q", len(new_kv)) + new_kv + struct.pack("<II", 4, 1)  # u32 1
# block_count must count the MTP layer (2B-MTP convention: 24 trunk -> block_count 25)
bc_name = b"qwen35.block_count"
kv_bc = struct.pack("<Q", len(bc_name)) + bc_name + struct.pack("<II", 4, IL + 1)

n_tensors_new = n_tensors + len(new_tensors)
n_kv_new = n_kv + 1
head = magic + struct.pack("<IQQ", version, n_tensors_new, n_kv_new)

f.seek(kv_start)
kv_blob = b"".join(kv_bc if k == "qwen35.block_count" else raw for k, raw in kv_spans)

# tensor info section: existing + new (offsets recomputed after we know data_start)
def write_infos(fout, entries):
    for name, nd, dims, tt, off in entries:
        nb = name.encode()
        fout.write(struct.pack("<Q", len(nb)) + nb)
        fout.write(struct.pack("<I", nd))
        fout.write(struct.pack("<%dQ" % nd, *dims))
        fout.write(struct.pack("<I", tt))
        fout.write(struct.pack("<Q", off))

# two-pass: compute data_start_new
import io
tmp = io.BytesIO()
tmp.write(head); tmp.write(kv_blob); tmp.write(kv_extra)
dummy = [(n, nd, d, t, 0) for (n, nd, d, t, o) in infos] + \
        [(n, len(d), d, t, 0) for (n, d, t, p) in new_tensors]
write_infos(tmp, dummy)
data_start_new = (tmp.tell() + align - 1) // align * align

# assign offsets: existing tensors keep RELATIVE layout (shifted), new ones appended
# simplest: keep existing order, then new tensors, each aligned to 32
entries = []
off = 0
for (name, nd, d, t, o) in infos:
    off = (off + align - 1) // align * align
    entries.append((name, nd, d, t, off))
    off += sizes[name]
for (name, d, t, p) in new_tensors:
    off = (off + align - 1) // align * align
    entries.append((name, len(d), d, t, off))
    off += len(p)

tmp = io.BytesIO()
tmp.write(head); tmp.write(kv_blob); tmp.write(kv_extra)
write_infos(tmp, entries)
pad = data_start_new - tmp.tell()
tmp.write(b"\0" * pad)

with open(DST, "xb") as fout:
    fout.write(tmp.getbuffer())
    # copy each existing tensor's data from src at (data_start + old_off)
    for (name, nd, d, t, o) in infos:
        f.seek(data_start + o)
        blob = f.read(sizes[name])
        cur = data_start_new + dict((e[0], e[4]) for e in entries)[name]
        fout.seek(cur)
        fout.write(blob)
    for (name, d, t, p) in new_tensors:
        cur = data_start_new + dict((e[0], e[4]) for e in entries)[name]
        fout.seek(cur)
        fout.write(p)

print("wrote", DST, os.path.getsize(DST), "bytes")
