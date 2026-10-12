#!/usr/bin/env python3
"""Prepare B1-r2 with the original path for short, underfilled groups."""
import argparse
import difflib
import json
from pathlib import Path

import prepare


def generate(source, root):
    if root.exists():
        raise ValueError('destination exists: '+str(root))
    for arm in ('control', 'A1', 'B1', 'C', 'D'):
        prepare.generate(source, root/arm, arm)
    base = root/'B1'
    path = base/'overlay'/prepare.OPS
    text = path.read_text()
    anchor = '            spine_k1_fa_shape(params, dst) && neq2 == 4*nek2) {'
    text = prepare.once(text, anchor,
        '            spine_k1_fa_shape(params, dst) && neq2 == 4*nek2 &&\n'
        '            (use_split_kv_path || nek2 >= nth)) {')
    anchor = '    if (spine_k1_flag("SPINE_K1_FA_GQA") && !spine_k1_flag("SPINE_K1_FA_DECODE") &&\n'
    trace = '''    if (spine_k1_flag("SPINE_K1_TRACE") && spine_k1_flag("SPINE_K1_FA_GQA") &&
            !spine_k1_flag("SPINE_K1_FA_DECODE") && spine_k1_fa_shape(params, dst) &&
            neq2 == 4*nek2 && !use_split_kv_path && nek2 < nth) {
        spine_k1_fa_trace(params, dst, "reference-underfilled-groups", 0, nek1);
    }
'''
    text = prepare.once(text, anchor, trace+anchor)
    path.write_text(text)
    manifest = json.loads((base/'manifest.json').read_text())
    old_patch = manifest['patch_sha256']
    changes = []
    for rel in sorted(manifest['files_sha256']):
        new = (base/'overlay'/rel).read_text()
        old = (source/rel).read_text() if (source/rel).exists() else ''
        changes.extend(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
            fromfile='a/'+rel if old else '/dev/null', tofile='b/'+rel))
    (base/'candidate.patch').write_text(''.join(changes))
    manifest['files_sha256'][prepare.OPS] = prepare.digest(path.read_bytes())
    manifest.update(revision='B1-r2', parent_patch_sha256=old_patch,
        revision_generator_sha256=prepare.digest(Path(__file__).read_bytes()),
        patch_sha256=prepare.digest((base/'candidate.patch').read_bytes()),
        short_history_fallback='Original path when split KV is off and KV heads are fewer than workers.')
    (base/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    print(json.dumps(generate(args.source.resolve(), args.root.resolve()), indent=2))
