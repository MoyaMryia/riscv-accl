#!/usr/bin/env python3
"""从已验证的修订版生成三项组合，保留独立开关。"""
import argparse
import difflib
import json
from pathlib import Path

import prepare


def generate(source, root):
    revision = prepare.module('combined_c2_revision', prepare.HERE/'revise-c2.py')
    revision.generate(source, root)
    base = root/'C'
    parent = json.loads((base/'manifest.json').read_text())
    verified = prepare.REPO/'lab/k1-local-candidates-C2-r2-20261009-063000/C/manifest.json'
    if parent['files_sha256'] != json.loads(verified.read_text())['files_sha256']:
        raise ValueError('C2-r2 source differs from the verified version')
    path = base/'overlay'/prepare.OPS
    text = prepare.attention(path.read_text(), False, True)
    text = prepare.once(text,
        '            spine_k1_fa_shape(params, dst) && neq2 == 4*nek2) {',
        '            spine_k1_fa_shape(params, dst) && neq2 == 4*nek2 &&\n'
        '            (use_split_kv_path || nek2 >= nth)) {')
    anchor = '    if (spine_k1_flag("SPINE_K1_FA_GQA") && !spine_k1_flag("SPINE_K1_FA_DECODE") &&\n'
    text = prepare.once(text, anchor, '''    if (spine_k1_flag("SPINE_K1_TRACE") && spine_k1_flag("SPINE_K1_FA_GQA") &&
            !spine_k1_flag("SPINE_K1_FA_DECODE") && spine_k1_fa_shape(params, dst) &&
            neq2 == 4*nek2 && !use_split_kv_path && nek2 < nth) {
        spine_k1_fa_trace(params, dst, "reference-underfilled-groups", 0, nek1);
    }
''' + anchor)
    text = prepare.once(text,
        'if (n_tokens > 1 && S_v == 128 && __riscv_vsetvlmax_e32m8() == 64) {',
        'if (spine_k1_flag("SPINE_K1_GDN_REVISION") && n_tokens > 1 && S_v == 128 && __riscv_vsetvlmax_e32m8() == 64) {')
    path.write_text(text)
    header = 'ggml/src/ggml-cpu/spine-k1-local-attention.h'
    (base/'overlay'/header).write_bytes((prepare.HERE/'attention.h').read_bytes())
    manifest = dict(parent)
    manifest['files_sha256'] = dict(parent['files_sha256'])
    manifest['files_sha256'][prepare.OPS] = prepare.digest(path.read_bytes())
    manifest['files_sha256'][header] = prepare.digest((base/'overlay'/header).read_bytes())
    changes = []
    for rel in sorted(manifest['files_sha256']):
        old = (source/rel).read_text() if (source/rel).exists() else ''
        new = (base/'overlay'/rel).read_text()
        changes.extend(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
            fromfile='a/'+rel if old else '/dev/null', tofile='b/'+rel))
    (base/'candidate.patch').write_text(''.join(changes))
    probe = (prepare.HERE/'test-b1-state.cpp').read_text()
    selector = '''static void select_arm(int arm) {
    const bool legacy = arm == 8;
    setenv("SPINE_K1_FA_GQA", (arm & 1) ? "1" : "0", 1);
    setenv("SPINE_K1_SSM_CONV", (legacy || (arm & 2)) ? "3" : "0", 1);
    setenv("SPINE_GDN_PREFILL", (legacy || (arm & 4)) ? "1" : "0", 1);
    setenv("SPINE_K1_GDN_REVISION", (arm & 4) ? "1" : "0", 1);
}
'''
    probe = prepare.once(probe, 'static Context context(', selector+'static Context context(')
    probe = probe.replace('B1_STATE', 'COMBO_STATE')
    probe = prepare.once(probe, '    setenv("SPINE_K1_FA_GQA", arm ? "1" : "0", 1);', '    select_arm(arm);')
    probe = prepare.once(probe, 'if (argc != 4)', 'if (argc != 5 && argc != 6)')
    probe = prepare.once(probe, 'usage: b1-state MODEL ARM DUMP', 'usage: combo-state MODEL ARM DUMP PROFILE [rs3]')
    probe = prepare.once(probe, '    const int arm = std::atoi(argv[2]);',
        '    const int arm = std::atoi(argv[2]);\n'
        '    const bool short_profile = std::strcmp(argv[4], "short") == 0;\n'
        '    const bool only_rs3 = argc == 6;')
    probe = prepare.once(probe, '        require(arm == 0 || arm == 1, "arm");',
        '        require(arm == 0 || arm == 1 || arm == 2 || arm == 4 || arm == 6 || arm == 7 || arm == 8, "arm");\n'
        '        require(short_profile || std::strcmp(argv[4], "long") == 0, "profile");\n'
        '        require(!only_rs3 || std::strcmp(argv[5], "rs3") == 0, "RS filter");')
    probe = prepare.once(probe, '        for (unsigned rs : {0u, 3u}) {',
        '        for (unsigned rs : {0u, 3u}) {\n            if (only_rs3 && rs != 3) continue;')
    probe = prepare.once(probe, '            setenv("SPINE_K1_FA_GQA", "0", 1);', '            select_arm(0);')
    probe = prepare.once(probe, '                setenv("SPINE_K1_FA_GQA", "1", 1);', '                select_arm(arm);')
    probe = prepare.once(probe, 'for (int count : {32, 1, 31, 32, 159, 1, 255, 1, 1535, 1})',
        'for (int count : (short_profile ? std::vector<int>{32, 1, 31, 32} : std::vector<int>{32, 1, 31, 32, 159, 1, 255, 1, 1535, 1}))')
    probe = prepare.once(probe, 'decode(candidate.get(), 1, prefix, count, vocab);', 'decode(candidate.get(), arm, prefix, count, vocab);')
    probe = prepare.once(probe, '        require(comparisons == 40, "comparison count");',
        '        require(comparisons == (short_profile ? 16 : 40)/(only_rs3 ? 2 : 1), "comparison count");')
    probe = prepare.once(probe, 'printf("PASS: 40 full-vocabulary records; mixed chunks/reset/RS/long history\\n");',
        'printf("PASS: %d full-vocabulary records; mixed chunks/reset/RS/long history\\n", comparisons);')
    (base/'test-combined-state.cpp').write_text(probe)
    manifest.update(revision='combined-r1', parent_c2_patch_sha256=parent['patch_sha256'],
        patch_sha256=prepare.digest((base/'candidate.patch').read_bytes()),
        combined_generator_sha256=prepare.digest(Path(__file__).read_bytes()),
        combined_probe_sha256=prepare.digest(probe.encode()))
    (base/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    print(json.dumps(generate(args.source.resolve(), args.root.resolve()), indent=2))
