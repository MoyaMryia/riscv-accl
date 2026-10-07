#!/usr/bin/env python3
"""Generate a CPU-only Qwen3.5 channels-major convolution experiment."""
import argparse
import difflib
from pathlib import Path

PATHS = ('ggml/src/ggml-cpu/ops.cpp', 'src/models/delta-net-base.cpp', 'src/models/qwen35.cpp')


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('unexpected baseline anchor: ' + old[:80])
    return text.replace(old, new, 1)


def generate(relative, text):
    if 'spine_k1_ssm' in text:
        raise ValueError('candidate already applied')
    if relative == PATHS[0]:
        text = replace_once(text, '// ggml_compute_forward_ssm_conv\n',
            '#include "spine-k1-ssm-kernel.h"\n\n// ggml_compute_forward_ssm_conv\n')
        anchor = '''void ggml_compute_forward_ssm_conv(
        const ggml_compute_params * params,
        ggml_tensor * dst) {
'''
        return replace_once(text, anchor, anchor + '''    if (dst->op_params[0] == 1 || dst->op_params[0] == 2) {
        spine_k1_ssm_conv_cpu(params, dst);
        return;
    }
''')
    text = replace_once(text, '#include "models.h"\n',
        '#include "models.h"\n#include "spine-k1-ssm-conv.h"\n')
    if relative == PATHS[1]:
        anchor = '''    qkv_mixed = ggml_transpose(ctx0, qkv_mixed);
    cb(qkv_mixed, "qkv_mixed_transposed", il);
'''
        return replace_once(text, anchor, '''    // CPU-only dense Qwen3.5, RS=0. Persistent state stays time-major.
    // Other architectures/backends and rollback configurations retain reference.
    if (arch == LLM_ARCH_QWEN35 && spine_k1_ssm_cpu_only(sched) &&
            cparams.n_rs_seq == 0 && spine_k1_ssm_conv_mode_for_tokens(qkv_mixed->ne[1]) != 0) {
        ggml_tensor * history = ggml_cont(ctx0, ggml_transpose(ctx0, conv_states));
        ggml_tensor * input = ggml_concat(ctx0, history, qkv_mixed, 1);
        cb(input, "conv_input_channels_major", il);
        const int64_t row_count = (conv_kernel_size - 1) * conv_channels;
        const size_t row_size = ggml_row_size(conv_states_all->type, row_count);
        const int64_t start = input->ne[1] - (conv_kernel_size - 1);
        ggml_tensor * tail = ggml_view_3d(ctx0, input,
            conv_channels, conv_kernel_size - 1, n_seqs,
            input->nb[1], input->nb[2], start*input->nb[1]);
        ggml_tensor * update = ggml_view_2d(ctx0, conv_states_all,
            row_count, n_seqs, conv_states_all->nb[1], kv_head*row_size);
        // The fork's CPY transpose fast path assumes incompatible dimensions
        // and equal batch strides. CONT respects this cropped history view;
        // the subsequent cache copy reads a contiguous time-major tensor.
        ggml_tensor * tail_time_major = ggml_cont(ctx0, ggml_transpose(ctx0, tail));
        ggml_build_forward_expand(gf, ggml_cpy(ctx0, tail_time_major, update));
        return input;
    }
''' + anchor)
    if relative == PATHS[2]:
        old = '    ggml_tensor * conv_output_proper = ggml_ssm_conv(ctx0, conv_input, conv_kernel);'
        return replace_once(text, old, '''    const int conv_mode = spine_k1_ssm_cpu_only(sched) && cparams.n_rs_seq == 0
        ? spine_k1_ssm_conv_mode_for_tokens(n_seq_tokens) : 0;
    ggml_tensor * conv_output_proper = conv_mode
        ? spine_k1_ssm_conv_channels_major(ctx0, conv_input, conv_kernel, conv_mode)
        : ggml_ssm_conv(ctx0, conv_input, conv_kernel);
    if (il == 0) {
        fprintf(stderr, "K1_SSM_CONV mode=%d layout=%s rs=%u cpu_only=%d tokens=%lld requested=%d\\n", conv_mode,
            conv_mode ? "channels" : "time", cparams.n_rs_seq, spine_k1_ssm_cpu_only(sched),
            (long long) n_seq_tokens, spine_k1_ssm_conv_mode());
    }''')
    raise ValueError('unsupported source: ' + relative)


def write_candidate(source, root):
    patch = []
    for relative in PATHS:
        old = (source/relative).read_text()
        new = generate(relative, old)
        output = root/'candidate'/relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(new)
        patch.extend(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
            fromfile='a/'+relative, tofile='b/'+relative))
    (root/'candidate-ssm-conv.patch').write_text(''.join(patch))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('root', type=Path)
    args = p.parse_args(); write_candidate(args.source, args.root)
