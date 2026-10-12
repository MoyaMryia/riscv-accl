#!/usr/bin/env python3
"""Prepare C2-r2 with two state segments in RVV registers."""
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
    base = root/'C'
    path = base/'overlay'/prepare.OPS
    text = path.read_text()
    text = prepare.once(text, 'static void ggml_compute_forward_gated_delta_net_one_chunk(',
                        '#include "spine-k1-gdn-prefill-r2.h"\n\nstatic void ggml_compute_forward_gated_delta_net_one_chunk(')
    call = '                ggml_gdn_decode_step_rvv(s_out, k_d, v_d, q_d, expf(g_d[0]), beta_val, scale, S_v, attn_data);'
    replacement = '''                if (n_tokens > 1 && S_v == 128 && __riscv_vsetvlmax_e32m8() == 64) {
                    static const bool r2_logged = [] {
                        fprintf(stderr, "SPINE_GDN_PREFILL_R2: retained two state segments; S=128; VLEN=256\\n");
                        return true;
                    }();
                    (void) r2_logged;
                    spine_k1_gdn_prefill128(s_out, k_d, v_d, q_d, expf(g_d[0]), beta_val, scale, attn_data);
                } else {
''' + call + '''
                }'''
    text = prepare.once(text, call, replacement)
    path.write_text(text)
    header = 'ggml/src/ggml-cpu/spine-k1-gdn-prefill-r2.h'
    (base/'overlay'/header).write_text((prepare.HERE/'gdn-prefill-r2.h').read_text())
    manifest = json.loads((base/'manifest.json').read_text())
    parent_patch = manifest['patch_sha256']
    manifest['files_sha256'][prepare.OPS] = prepare.digest(path.read_bytes())
    manifest['files_sha256'][header] = prepare.digest((base/'overlay'/header).read_bytes())
    patch = []
    for rel in sorted(manifest['files_sha256']):
        old = (source/rel).read_text() if (source/rel).exists() else ''
        new = (base/'overlay'/rel).read_text()
        patch.extend(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                     fromfile='a/'+rel if old else '/dev/null', tofile='b/'+rel))
    (base/'candidate.patch').write_text(''.join(patch))
    fixture = (prepare.HERE.parent/'test-k1-gdn.cpp').read_text()
    fixture = prepare.once(fixture, '    require(argc==1,"usage: test-gdn [--bench]");',
        '    require(argc==1 || (argc==3 && strcmp(argv[1],"--dump")==0), "usage: test-gdn [--bench|--dump FILE]");\n'
        '    FILE * dump = argc==3 ? fopen(argv[2],"wb") : nullptr;\n'
        '    require(argc==1 || dump, "dump file");')
    fixture = prepare.once(fixture, '        f.reset(); f.run(1); f.check();',
        '        if (dump) {\n'
        '            require(fwrite(control.data(),sizeof(float),control.size(),dump)==control.size(), "output dump");\n'
        '            require(fwrite(state0.data(),sizeof(float),state0.size(),dump)==state0.size(), "state dump");\n'
        '        }\n'
        '        f.reset(); f.run(1); f.check();')
    fixture = prepare.once(fixture, '    printf("PASS: %d cases;',
                           '    if (dump) require(fclose(dump)==0, "dump close");\n    printf("PASS: %d cases;')
    (base/'test-gdn-r2.cpp').write_text(fixture)
    manifest.update(revision='C2-r2', parent_patch_sha256=parent_patch,
        revision_generator_sha256=prepare.digest(Path(__file__).read_bytes()),
        fixture_sha256=prepare.digest(fixture.encode()),
        patch_sha256=prepare.digest((base/'candidate.patch').read_bytes()),
        scope='Keep two 64-element state segments in registers during eligible S128 prefill.')
    (base/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    print(json.dumps(generate(args.source.resolve(), args.root.resolve()), indent=2))
