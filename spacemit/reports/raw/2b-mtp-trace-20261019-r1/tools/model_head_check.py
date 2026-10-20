"""GGUF V3 追加草稿头检查器。"""
import hashlib
import os
import struct

_BLOCK_SIZE = 1024 * 1024
_HEAD_SUFFIX = '.nextn.shared_head_head.weight'


class _Reader:
    def __init__(self, stream):
        self.stream = stream
        self.header = bytearray()

    def take(self, size):
        data = self.stream.read(size)
        if len(data) != size:
            raise ValueError('GGUF 文件已截断')
        self.header.extend(data)
        return data

    def unpack(self, fmt):
        return struct.unpack(fmt, self.take(struct.calcsize(fmt)))

    def string(self):
        (size,) = self.unpack('<Q')
        return self.take(size)


def _value(reader, kind):
    sizes = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 4,
             7: 1, 10: 8, 11: 8, 12: 8}
    if kind in sizes:
        return reader.take(sizes[kind])
    if kind == 8:
        return reader.string()
    if kind == 9:
        (element_type,) = reader.unpack('<I')
        (count,) = reader.unpack('<Q')
        return tuple(_value(reader, element_type) for _ in range(count))
    raise ValueError('GGUF metadata 类型无效')


def _read_model(stream):
    file_size = os.fstat(stream.fileno()).st_size
    reader = _Reader(stream)
    if reader.take(4) != b'GGUF':
        raise ValueError('文件不是 GGUF')
    version, tensor_count, kv_count = reader.unpack('<IQQ')
    if version != 3:
        raise ValueError('GGUF 版本必须为 3')
    kv_start = stream.tell()
    alignment = 32
    for _ in range(kv_count):
        key = reader.string().decode('utf-8')
        (kind,) = reader.unpack('<I')
        value = _value(reader, kind)
        if key == 'general.alignment':
            if kind != 4:
                raise ValueError('GGUF 对齐值必须为 UINT32')
            alignment = struct.unpack('<I', value)[0]
    if alignment == 0 or alignment & (alignment - 1):
        raise ValueError('GGUF 对齐值无效')
    kv_end = stream.tell()
    tensors = []
    for _ in range(tensor_count):
        name = reader.string().decode('utf-8')
        (rank,) = reader.unpack('<I')
        dims = reader.unpack('<' + 'Q' * rank) if rank else ()
        tensor_type, offset = reader.unpack('<IQ')
        tensors.append((name, dims, tensor_type, offset))
    infos_end = stream.tell()
    data_start = (infos_end + alignment - 1) // alignment * alignment
    if data_start > file_size:
        raise ValueError('GGUF 数据区对齐无效')
    reader.take(data_start - infos_end)
    return {'size': file_size, 'kv': bytes(reader.header[kv_start:kv_end]),
            'tensors': tensors, 'data_start': data_start, 'header': bytes(reader.header)}


def compare_models(full_path, prefix_path):
    """比较完整模型与调用者已固定身份的前缀模型。"""
    with open(full_path, 'rb') as full_stream, open(prefix_path, 'rb') as prefix_stream:
        full = _read_model(full_stream)
        prefix = _read_model(prefix_stream)
        if full['kv'] != prefix['kv']:
            raise ValueError('两模型 metadata 原始字节不同')
        head = next(item for item in prefix['tensors'] if item[0].endswith(_HEAD_SUFFIX))
        shared = [item for item in prefix['tensors'] if item is not head]
        if full['tensors'] != shared:
            raise ValueError('两模型共享张量信息不同')
        data_length = full['size'] - full['data_start']
        if data_length != head[3]:
            raise ValueError('原模型数据区长度不等于追加头偏移')
        digest = hashlib.sha256()
        digest.update(full['header'])
        remaining = data_length
        while remaining:
            size = min(remaining, _BLOCK_SIZE)
            full_block = full_stream.read(size)
            prefix_block = prefix_stream.read(size)
            if len(full_block) != size or len(prefix_block) != size:
                raise ValueError('GGUF 数据区已截断')
            digest.update(full_block)
            if full_block != prefix_block:
                raise ValueError('两模型共享数据字节不同')
            remaining -= size
    embedding = next(item for item in shared if item[0] == 'token_embd.weight')
    return {'full_path': str(full_path), 'full_bytes': full['size'],
            'full_sha256': digest.hexdigest(), 'shared_tensors': len(shared),
            'shared_data_bytes': data_length,
            'prefix_head': {'name': head[0], 'shape': head[1], 'type': head[2]},
            'vocabulary_rows': embedding[1][1]}
