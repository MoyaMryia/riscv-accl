#!/usr/bin/env python3
"""准备组合回退分派修订，不构建或派发板端测试。"""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import shutil


OLD = 'spine_k1_flag("SPINE_K1_GDN_REVISION") && n_tokens > 1 && S_v == 128 && __riscv_vsetvlmax_e32m8() == 64'
NEW = 'n_tokens > 1 && S_v == 128 && spine_k1_flag("SPINE_K1_GDN_REVISION") && __riscv_vsetvlmax_e32m8() == 64'
OPS = 'ggml/src/ggml-cpu/ops.cpp'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(parent, output):
    if output.exists():
        raise ValueError('destination exists')
    manifest = json.loads((parent/'manifest.json').read_text())
    if manifest['revision'] != 'combined-r1':
        raise ValueError('parent revision differs')
    for name, expected in manifest['files_sha256'].items():
        if sha(parent/'overlay'/name) != expected:
            raise ValueError('parent source receipt differs: '+name)
    original = (parent/'overlay'/OPS).read_text()
    if original.count(OLD) != 1:
        raise ValueError('dispatch anchor differs')
    revised = original.replace(OLD, NEW)
    output.mkdir(parents=True)
    shutil.copytree(parent/'overlay', output/'overlay')
    (output/'overlay'/OPS).write_text(revised)
    for name in ('test-combined-state.cpp', 'test-gdn-r2.cpp'):
        shutil.copyfile(parent/name, output/name)
    shutil.copyfile(parent/'manifest.json', output/'parent-manifest.json')
    patch = ''.join(difflib.unified_diff(original.splitlines(True), revised.splitlines(True),
                                       fromfile='a/'+OPS, tofile='b/'+OPS))
    (output/'dispatch-only.patch').write_text(patch)
    updated = dict(manifest)
    updated['files_sha256'] = dict(manifest['files_sha256'])
    updated['files_sha256'][OPS] = sha(output/'overlay'/OPS)
    updated.update(revision='combined-dispatch-r2',
                   parent_manifest_sha256=sha(parent/'manifest.json'),
                   dispatch_patch_sha256=sha(output/'dispatch-only.patch'),
                   dispatch_generator_sha256=sha(Path(__file__)),
                   validation_status='local-preparation-only')
    updated.pop('patch_sha256', None)
    (output/'manifest.json').write_text(json.dumps(updated, indent=2)+'\n')
    return updated


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('parent_candidate', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(generate(args.parent_candidate, args.output), indent=2))
