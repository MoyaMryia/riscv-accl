"""读写实验资料并计算文件身份。"""
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def seal(root):
    root = Path(root)
    with (root / 'SHA256SUMS').open('x') as stream:
        for path in sorted(root.rglob('*')):
            if path.is_file() and path.name != 'SHA256SUMS':
                stream.write(f'{digest(path)}  {path.relative_to(root)}\n')
