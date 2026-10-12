#!/usr/bin/env python3
"""Prepare isolated K1 candidates from the fixed source."""
import argparse
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OPS = 'ggml/src/ggml-cpu/ops.cpp'
CPU = 'ggml/src/ggml-cpu/ggml-cpu.c'
OPSH = 'ggml/src/ggml-cpu/ops.h'
PINS = {
    OPS: 'd03e80d18d117047b5f6cc007a277c80cab90e9d6c9f7f97ef4d8002db1a8192',
    OPSH: 'df47df0d864dec502a2bb8886c6644a65ad901703583773510b1a17af6eededd',
    'ggml/src/ggml-cpu/vec.cpp': 'cda0babb53f9c8ff1faa7459b2c49019d15e5970dfe0c613d58e2659e919f524',
    'ggml/src/ggml-cpu/vec.h': '926330bae1c5d003bd654035426e31381fafcdca23ffcc23201d219dbb97cbeb',
    'src/models/delta-net-base.cpp': '0120dd95d56d3eac0e0c3e2cd72af9cf13fc4f894022533d243d6577e5016f0d',
    'src/models/qwen35.cpp': '7643d4ce05ee44fa6f46b47436e82a2b7db171f04189a73fa5b2305fff82b30e',
}
FLAGS = {
    'control': {},
    'A1': {'SPINE_K1_FA_DECODE': '1'},
    'B1': {'SPINE_K1_FA_GQA': '1'},
    'C': {'C0': {}, 'C1': {'SPINE_K1_SSM_CONV': '3'},
          'C2': {'SPINE_GDN_PREFILL': '1'},
          'C3': {'SPINE_K1_SSM_CONV': '3', 'SPINE_GDN_PREFILL': '1'}},
    'D': {'SPINE_K1_SSM_CONV': '3', 'SPINE_K1_CONV_SILU': '1'},
    'test-bundle': {},
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('unexpected source anchor: ' + old[:100])
    return text.replace(old, new, 1)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def state_probe():
    text = (HERE.parent/'test-k1-ssm-state.cpp').read_text()
    helper = '''static void select_arm(int mode) {
    setenv("SPINE_K1_SSM_CONV", mode == 1 || mode == 3 ? "3" : "0", 1);
    setenv("SPINE_GDN_PREFILL", mode == 2 || mode == 3 ? "1" : "0", 1);
}
'''
    text = once(text, 'static void decode(', helper + 'static void decode(')
    for old, new in (
        ('    setenv("SPINE_K1_SSM_CONV",mode==0?"0":mode==1?"1":mode==2?"2":"3",1);', '    select_arm(mode);'),
        ('            setenv("SPINE_K1_SSM_CONV","0",1);', '            select_arm(0);'),
        ('            setenv("SPINE_K1_SSM_CONV",mode==1?"1":mode==2?"2":"3",1);', '            select_arm(mode);'),
        ('const std::vector<int> chunks = mode == 3 ? std::vector<int>{32,1,31,32} : std::vector<int>{3,29,1,3};',
         'const std::vector<int> chunks = {32,1,31,32};'),
    ):
        text = once(text, old, new)
    return text


def attention(text, a, b):
    text = once(text, '// ggml_compute_forward_dup\n',
                '#include "spine-k1-local-attention.h"\n\n// ggml_compute_forward_dup\n')
    name = 'ggml_compute_forward_flash_attn_ext_f16_one_chunk'
    start = text.index('static void ' + name + '(')
    end = text.index('\nstatic void ggml_compute_forward_flash_attn_ext_tiled(', start)
    original = text[start:end]
    if a:
        direct = original.replace(name, 'spine_k1_decode_chunk', 1)
        direct = once(direct, '            kq_vec_dot(DK, &s, 0, k_data, 0, Q_q, 0, 1);',
                      '            spine_k1_dot256((const ggml_fp16_t *) k_data, Q_q, &s);')
        direct = once(direct,
            '    ggml_vec_dot_t    const kq_vec_dot     = ggml_get_type_traits_cpu(k->type)->vec_dot;\n', '')
        direct = once(direct, '    const bool write_partials = (partials != nullptr);', '''    spine_k1_fa_trace(params, dst, "A1", ic_start, ic_end);
    const bool write_partials = (partials != nullptr);''')
        anchor = '    const bool write_partials = (partials != nullptr);'
        routed = once(original, anchor, '''    if (spine_k1_flag("SPINE_K1_FA_DECODE") && !spine_k1_flag("SPINE_K1_FA_GQA") &&
            spine_k1_fa_shape(params, dst)) {
        spine_k1_decode_chunk(params, dst, ir0, ir1, ic_start, ic_end, partials, partial_stride);
        return;
    }
''' + anchor)
        text = text[:start] + direct + '\n' + routed + text[end:]
    if b:
        anchor = '    if (use_split_kv_path) {\n'
        text = once(text, anchor, '''    if (spine_k1_flag("SPINE_K1_FA_GQA") && !spine_k1_flag("SPINE_K1_FA_DECODE") &&
            spine_k1_fa_shape(params, dst) && neq2 == 4*nek2) {
        const int64_t chunk_size = (nek1 + nth - 1)/nth;
        const int64_t first = use_split_kv_path ? ith*chunk_size : 0;
        const int64_t last = use_split_kv_path ? std::min(first + chunk_size, nek1) : nek1;
        spine_k1_fa_trace(params, dst, "B1", first, last);
        if (ith == 0 && spine_k1_flag("SPINE_K1_TRACE")) {
            fprintf(stderr, "K1_FA group=4 stack_bytes=%zu shared=K,V\\n", sizeof(spine_k1_group_scratch));
        }
        if (use_split_kv_path) {
            const int64_t partial_size = 2 + DV;
            float * base = (float *) params->wdata + nth*(DK + 2*DV + CACHE_LINE_SIZE_F32);
            for (int64_t group = 0; group < nek2; ++group) {
                spine_k1_gqa_chunk(params, dst, group, first, last,
                    base + ith*partial_size, nth*partial_size);
            }
            ggml_barrier(params->threadpool);
            ggml_flash_attn_ext_reduce_partials(params, dst, nth, chunk_size);
        } else {
            for (int64_t group = ith; group < nek2; group += nth) {
                spine_k1_gqa_chunk(params, dst, group, 0, nek1, nullptr, 0);
            }
        }
        return;
    }

''' + anchor)
    anchor = '    const bool use_split_kv_path = !use_ref && (neq1 == 1 && neq3 == 1) && kv_is_f32_or_f16 && (k->type == v->type) && q->type == GGML_TYPE_F32 && nek1 >= 512;\n'
    text = once(text, anchor, anchor + '''
    const bool requested_a = spine_k1_flag("SPINE_K1_FA_DECODE");
    const bool requested_b = spine_k1_flag("SPINE_K1_FA_GQA");
    if ((requested_a || requested_b) &&
            (requested_a == requested_b || !spine_k1_fa_shape(params, dst) ||
             (requested_b && neq2 != 4*nek2))) {
        spine_k1_fa_trace(params, dst, "reference", 0, nek1);
    }
''')
    return text


FUSION = '''    if (node->op == GGML_OP_SSM_CONV) {
        const char * diagnostic = getenv("SPINE_K1_CONV_SILU_DIAG");
        if (diagnostic && strcmp(diagnostic, "1") == 0) return 0;
        const char * value = getenv("SPINE_K1_CONV_SILU");
        if (value && strcmp(value, "1") == 0) {
            const enum ggml_op pair[] = { GGML_OP_SSM_CONV, GGML_OP_UNARY };
            const char * reason = "graph";
            if (ggml_can_fuse(cgraph, node_n, pair, 2)) {
                struct ggml_tensor * silu = cgraph->nodes[node_n + 1];
                reason = "shape";
                if (silu->src[0] == node && ggml_get_unary_op(silu) == GGML_UNARY_OP_SILU &&
                        node->op_params[0] == 2 && node->type == GGML_TYPE_F32 &&
                        silu->type == GGML_TYPE_F32 && params->nth == 4 &&
                        node->ne[0] % 64 == 0 && node->ne[1] >= 32 && node->ne[3] == 1 &&
                        ggml_is_contiguous(node) && ggml_is_contiguous(silu)) {
                    spine_k1_conv_silu(params, node, silu);
                    reason = "paired";
                }
            }
            const char * trace = getenv("SPINE_K1_TRACE");
            if (params->ith == 0 && trace && strcmp(trace, "1") == 0) {
                fprintf(stderr, "K1_CONV_SILU node=%d result=%s\\n", node_n, reason);
            }
            if (strcmp(reason, "paired") == 0) return 1;
        }
    }

'''


def conv_diagnostic(text):
    declaration = '''    const char * spine_diag_value = getenv("SPINE_K1_CONV_SILU_DIAG");
    const bool spine_diag = spine_diag_value && strcmp(spine_diag_value, "1") == 0;
    const struct ggml_tensor * spine_last_conv = NULL;
    int64_t spine_conv_end_us = 0;
'''
    before = '''        if (spine_diag && node->op == GGML_OP_UNARY &&
                ggml_get_unary_op(node) == GGML_UNARY_OP_SILU && node->src[0] == spine_last_conv) {
            const int64_t start_us = ggml_time_us();
            fprintf(stderr, "K1_CONV_SILU_DIAG worker=%d node=%d conv_end_us=%lld silu_start_us=%lld between_us=%lld\\n",
                params.ith, node_n, (long long) spine_conv_end_us, (long long) start_us,
                (long long) (start_us - spine_conv_end_us));
        }
'''
    after = '''        if (spine_diag) {
            spine_last_conv = node->op == GGML_OP_SSM_CONV && node->op_params[0] == 2 ? node : NULL;
            spine_conv_end_us = ggml_time_us();
        }
'''
    for anchor in (
        '    for (int node_n = 0; node_n < cgraph->n_nodes; node_n++) {',
        '    for (int node_n = 0; node_n < cgraph->n_nodes && atomic_load_explicit(&tp->abort, memory_order_relaxed) != node_n; node_n++) {',
    ):
        text = once(text, anchor, declaration + anchor)
    anchor = '        const int n_fused = ggml_cpu_try_fuse_ops(cgraph, node_n, &params, cplan);'
    if text.count(anchor) != 2:
        raise ValueError('unexpected graph dispatch count')
    text = text.replace(anchor, before + anchor)
    block = '''        } else {
            ggml_compute_forward(&params, node);
        }
'''
    if text.count(block) != 2:
        raise ValueError('unexpected graph compute count')
    return text.replace(block, block + after)


def generate(source, destination, kind, copy_tree=False):
    release = json.loads((REPO/'spacemit/release/manifest.json').read_text())
    snapshot = REPO/'spacemit/reports/raw/local-reference-quality-20261006-194015/source-verification.json'
    if digest(snapshot.read_bytes()) != release['clean_snapshot_manifest_sha256']:
        raise ValueError('snapshot receipt hash mismatch')
    receipt = json.loads(snapshot.read_text())
    if receipt['commit'] != release['source_commit']:
        raise ValueError('snapshot commit mismatch')
    for path, expected in receipt['files_sha256'].items():
        if digest((source/path).read_bytes()) != expected:
            raise ValueError('snapshot source hash mismatch: ' + path)
    pins = {**PINS, **release['original_source_sha256']}
    for path, expected in pins.items():
        if digest((source/path).read_bytes()) != expected:
            raise ValueError('source hash mismatch: ' + path)
    patch = REPO/'spacemit/release'/release['patch']
    if digest(patch.read_bytes()) != release['patch_sha256']:
        raise ValueError('release patch hash mismatch')
    files = {}
    with tempfile.TemporaryDirectory(prefix='k1-candidate-') as tmp:
        tmp = Path(tmp)
        for relative in release['original_source_sha256']:
            output = tmp/relative
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source/relative, output)
        subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(patch)],
                       cwd=tmp, check=True, capture_output=True)
        for relative, expected in release['patched_source_sha256'].items():
            data = (tmp/relative).read_bytes()
            if digest(data) != expected:
                raise ValueError('release output hash mismatch: ' + relative)
            files[relative] = data.decode()
    files[OPS] = (source/OPS).read_text()
    if kind in ('A1', 'B1', 'test-bundle'):
        files[OPS] = attention(files[OPS], kind != 'B1', kind != 'A1')
        files['ggml/src/ggml-cpu/spine-k1-local-attention.h'] = (HERE/'attention.h').read_text()
    if kind in ('C', 'D', 'test-bundle'):
        ssm = module('local_ssm', HERE.parent/'make-k1-ssm-conv.py')
        for relative in ssm.PATHS:
            files[relative] = ssm.generate(relative, files.get(relative, (source/relative).read_text()))
        files['ggml/src/ggml-cpu/spine-k1-ssm-kernel.h'] = (HERE.parent/'spine-k1-ssm-kernel.h').read_text()
        files['src/models/spine-k1-ssm-conv.h'] = (HERE.parent/'spine-k1-ssm-conv.h').read_text()
    if kind in ('C', 'test-bundle'):
        gdn = module('local_gdn', HERE.parent/'k1-gdn-test.py')
        files[OPS] = gdn.generate(files[OPS])
    if kind in ('D', 'test-bundle'):
        files[OPS] = once(files[OPS], '// ggml_compute_forward_ssm_conv\n',
                         '#include "spine-k1-local-conv-silu.h"\n\n// ggml_compute_forward_ssm_conv\n')
        files['ggml/src/ggml-cpu/spine-k1-local-conv-silu.h'] = (HERE/'conv-silu.h').read_text()
        files[OPSH] = once((source/OPSH).read_text(), 'void ggml_compute_forward_ssm_conv(',
            'void spine_k1_conv_silu(const struct ggml_compute_params * p, struct ggml_tensor * conv, struct ggml_tensor * silu);\n\nvoid ggml_compute_forward_ssm_conv(')
        files[CPU] = once(files[CPU], '    if (node->op == GGML_OP_RMS_NORM) {\n',
                          FUSION + '    if (node->op == GGML_OP_RMS_NORM) {\n')
        files[CPU] = conv_diagnostic(files[CPU])
    if destination.exists():
        raise ValueError('destination exists: ' + str(destination))
    destination.mkdir(parents=True)
    target = destination/('source' if copy_tree else 'overlay')
    if copy_tree:
        shutil.copytree(source, target, ignore=shutil.ignore_patterns('.git', '__pycache__'))
    changes = []
    for relative, new in sorted(files.items()):
        output = target/relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(new)
        old = (source/relative).read_text() if (source/relative).exists() else ''
        changes.extend(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
            fromfile='a/'+relative if old else '/dev/null', tofile='b/'+relative))
    (destination/'candidate.patch').write_text(''.join(changes))
    if kind in ('C', 'test-bundle'):
        (destination/'test-c-state.cpp').write_text(state_probe())
    manifest = {
        'candidate': kind, 'source_commit': release['source_commit'], 'source_sha256': pins,
        'release_patch_sha256': release['patch_sha256'], 'flags': FLAGS[kind],
        'snapshot_manifest_sha256': release['clean_snapshot_manifest_sha256'],
        'defaults': {'SPINE_FA_WIDE_TILE': '1', 'SPINE_FA_K1_LAYOUT': '0', 'SPINE_K1_GEMM_ROUTE': '3'},
        'gqa_stack_bytes_per_worker': 5184 if kind in ('B1', 'test-bundle') else 0,
        'k1_performance': 'unverified',
        'files_sha256': {p: digest(t.encode()) for p, t in sorted(files.items())},
        'patch_sha256': digest((destination/'candidate.patch').read_bytes()),
        'generator_sha256': digest(Path(__file__).read_bytes()),
        'state_probe_sha256': digest(state_probe().encode()) if kind in ('C', 'test-bundle') else None,
    }
    (destination/'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--candidate', choices=FLAGS, required=True)
    parser.add_argument('--copy-tree', action='store_true')
    args = parser.parse_args()
    result = generate(args.source.resolve(), args.destination.resolve(), args.candidate, args.copy_tree)
    print(json.dumps({'candidate': result['candidate'], 'patch_sha256': result['patch_sha256']}))
