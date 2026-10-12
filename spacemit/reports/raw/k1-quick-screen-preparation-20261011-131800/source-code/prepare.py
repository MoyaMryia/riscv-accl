#!/usr/bin/env python3
"""生成三个隔离原型，不修改来源目录。"""
import argparse
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


parent = module('quick_parent', BENCH/'local-candidates/prepare.py')


def b2_header(text):
    start = text.index('static void spine_k1_gqa_chunk(')
    original = text[start:]
    baseline = original.replace('spine_k1_gqa_chunk(', 'quick_b1_chunk(', 1)
    tiled = original.replace('static void spine_k1_gqa_chunk(',
        'template<int TILE>\nstatic void quick_b2_chunk(', 1)
    tiled = parent.once(tiled, '    spine_k1_group_scratch scratch;', '''    spine_k1_group_scratch scratch;
    struct alignas(64) Tile {
        ggml_fp16_t key[TILE][256];
        ggml_fp16_t value[TILE][256];
    } tile;
    static_assert(sizeof(Tile) == TILE*1024, "tile size");''')
    begin = '    for (int64_t ic = first; ic < last; ++ic) {\n'
    tiled = parent.once(tiled, begin, '''    for (int64_t base = first; base < last; base += TILE) {
        const int count = int(std::min<int64_t>(TILE, last - base));
        for (int j = 0; j < count; ++j) {
            memcpy(tile.key[j], (const char *) k->data + (base+j)*k->nb[1] + group*k->nb[2], 512);
            memcpy(tile.value[j], (const char *) v->data + (base+j)*v->nb[1] + group*v->nb[2], 512);
        }
        for (int j = 0; j < count; ++j) {
        const int64_t ic = base + j;
''')
    tiled = parent.once(tiled,
        'const auto * key = (const ggml_fp16_t *) ((const char *) k->data + ic*k->nb[1] + group*k->nb[2]);',
        'const auto * key = tile.key[j];')
    tiled = parent.once(tiled,
        'const auto * value = (const ggml_fp16_t *) ((const char *) v->data + ic*v->nb[1] + group*v->nb[2]);',
        'const auto * value = tile.value[j];')
    tiled = parent.once(tiled, '        spine_k1_mad4(scratch.value, value, weight, active);\n    }',
        '        spine_k1_mad4(scratch.value, value, weight, active);\n        }\n    }')
    wrapper = '''
static int quick_b2_tile() {
    const char * value = getenv("SPINE_QUICK_B2_TILE");
    if (value && strcmp(value, "8") == 0) return 8;
    if (value && strcmp(value, "16") == 0) return 16;
    return 0;
}
static void spine_k1_gqa_chunk(const ggml_compute_params * p, ggml_tensor * dst,
        int64_t group, int64_t first, int64_t last, float * partials, int64_t stride) {
    const int tile = quick_b2_tile();
    if (spine_k1_flag("SPINE_K1_TRACE")) {
        fprintf(stderr, "QUICK_B2 tile=%d worker=%d workers=%d bytes=%d\\n",
            tile, p->ith, p->nth, tile*1024);
    }
    if (tile == 8) quick_b2_chunk<8>(p, dst, group, first, last, partials, stride);
    else if (tile == 16) quick_b2_chunk<16>(p, dst, group, first, last, partials, stride);
    else quick_b1_chunk(p, dst, group, first, last, partials, stride);
}
'''
    return text[:start] + baseline + '\n' + tiled + wrapper


def ime_source(text):
    patcher = module('quick_ime_parent', BENCH/'make-k1-ime-m1-k32.py')
    text = patcher.generate(text)
    start = text.index('#define K1_M1_K32_LOAD ')
    end = text.index('\nstatic __attribute__((noinline))', start)
    macro = text[start:end]
    lines = macro.splitlines()
    head, instructions = lines[0], lines[1:]
    # 保持向量配置段不变。只交错各权重寄存器的加载与拆解。
    split = next(i for i, line in enumerate(instructions) if 'vsetvli' in line)
    config = next(i for i, line in enumerate(instructions)
                  if 'vsetvli' in line and 'e8, m1' in line)
    loads = instructions[:split]
    operands = instructions[split:config+1]
    unpack = instructions[config+1:]
    if len(loads) != 8 or len(unpack) != 8:
        raise ValueError('IME load group differs')
    reordered = []
    for h in range(4):
        reordered.extend(loads[2*h:2*h+2])
        if h > 0:
            reordered.extend([unpack[h-1], unpack[h+3]])
    reordered.extend([unpack[3], unpack[7]])
    # 原宏末行无续行符，重排后必须重新写入续行符。
    new_lines = [line.rstrip().removesuffix('\\').rstrip() for line in reordered+operands]
    new_macro = head.replace('K1_M1_K32_LOAD', 'QUICK_M1_LOAD')+'\n'
    new_macro += '\n'.join(line + (' \\' if i+1 < len(new_lines) else '')
                           for i, line in enumerate(new_lines))+'\n'
    helper_start = text.index('static __attribute__((noinline)) void k1_m1_k32_fixed')
    helper_end = text.index('\n#undef K1_M1_K32_LOAD', helper_start)
    helper = text[helper_start:helper_end].replace('k1_m1_k32_fixed', 'quick_m1_load_schedule')
    helper = helper.replace('K1_M1_K32_LOAD', 'QUICK_M1_LOAD')
    text = text[:helper_end] + '\n'+new_macro+'\n'+helper+'\n#undef QUICK_M1_LOAD\n' + text[helper_end:]
    anchor = '    if (mode == 1 && k1_m1_k32_eligible(bl, zp, m, n, kb)) {'
    text = parent.once(text, anchor, '''    if (mode == 2 && k1_m1_k32_eligible(bl, zp, m, n, kb)) {
        quick_m1_load_schedule(bl, a, b, c, n, kb, ld);
        return 1;
    }
''' + anchor)
    text = parent.once(text,
        'return value && std::strcmp(value, "1") == 0 ? 1 : 0;',
        'return value && std::strcmp(value, "2") == 0 ? 2 : value && std::strcmp(value, "1") == 0 ? 1 : 0;')
    text = text.replace('SPINE_IME_M1_K32', 'SPINE_QUICK_IME_SCHEDULE')
    return text


def main(source, root):
    if root.exists():
        raise ValueError('destination exists')
    root.mkdir(parents=True)
    # 同一来源检查同时约束原始内核及发布路由。
    parent.generate(source, root/'base', 'control')
    parent.generate(source, root/'B2', 'B1')
    ops = root/'B2/overlay'/parent.OPS
    ops.write_text(parent.once(ops.read_text(),
        '            spine_k1_fa_shape(params, dst) && neq2 == 4*nek2) {',
        '            spine_k1_fa_shape(params, dst) && neq2 == 4*nek2 &&\n'
        '            (use_split_kv_path || nek2 >= nth)) {'))
    text = ops.read_text()
    anchor = '    if (spine_k1_flag("SPINE_K1_FA_GQA") && !spine_k1_flag("SPINE_K1_FA_DECODE") &&\n'
    text = parent.once(text,anchor,'''    if (spine_k1_flag("SPINE_K1_TRACE") && spine_k1_flag("SPINE_K1_FA_GQA") &&
            !spine_k1_flag("SPINE_K1_FA_DECODE") && spine_k1_fa_shape(params, dst) &&
            neq2 == 4*nek2 && !use_split_kv_path && nek2 < nth) {
        spine_k1_fa_trace(params, dst, "reference-underfilled-groups", 0, nek1);
    }
''' + anchor)
    ops.write_text(text)
    header = root/'B2/overlay/ggml/src/ggml-cpu/spine-k1-local-attention.h'
    header.write_text(b2_header(header.read_text()))
    bmanifest=json.loads((root/'B2/manifest.json').read_text())
    patch=[]
    for relative in bmanifest['files_sha256']:
        new=(root/'B2/overlay'/relative).read_text()
        old=(source/relative).read_text() if (source/relative).exists() else ''
        patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),
            fromfile='a/'+relative if old else '/dev/null',tofile='b/'+relative))
        bmanifest['files_sha256'][relative]=parent.digest(new.encode())
    (root/'B2/candidate.patch').write_text(''.join(patch))
    bmanifest.update(candidate='B2-quick',patch_sha256=parent.digest(''.join(patch).encode()),
        k1_performance='unverified',tile_lengths=[8,16],tile_bytes_per_worker=[8192,16384])
    (root/'B2/manifest.json').write_text(json.dumps(bmanifest,indent=2)+'\n')
    rel = 'ggml/src/ggml-cpu/spacemit/ime1_kernels.cpp'
    (root/'ime-schedule.cpp').write_text(ime_source((source/rel).read_text()))
    fixture = (BENCH/'local-candidates/test-attention.cpp').read_text()
    fixture = parent.once(fixture,'        pool = ggml_threadpool_new(&p);', '''#if defined(SPINE_K1_BOARD)
        if (nth == 4) {
            for (int cpu=0; cpu<4; ++cpu) p.cpumask[cpu] = true;
            p.strict_cpu = true;
        }
#endif
        pool = ggml_threadpool_new(&p);''')
    (root/'b2-fixture.h').write_text(fixture[:fixture.index('int main(')])
    fixture = (BENCH/'test-k1-ime-m1.cpp').read_text()
    (root/'ime-fixture.h').write_text(fixture[:fixture.index('int main(')])
    shutil.copyfile(BENCH/'test-k1-ime-m1-graph.cpp',root/'ime-graph.cpp')
    for name in ('common.h', 'conv.cpp', 'b2.cpp', 'ime.cpp', 'run.py', 'run-board.sh', 'README.md'):
        shutil.copyfile(HERE/name, root/name)
    files = {str(p.relative_to(root)): parent.digest(p.read_bytes())
             for p in sorted(root.rglob('*')) if p.is_file()}
    manifest = {'status': 'prepared', 'k1_performance': 'unverified',
        'source_files_sha256': json.loads((root/'base/manifest.json').read_text())['source_sha256'],
        'ime_original_sha256': parent.digest((source/rel).read_bytes()),
        'files_sha256': files, 'generator_sha256': parent.digest(Path(__file__).read_bytes()),
        'gate': {'blocks': 6, 'minimum_ms_per_arm_block': 100, 'gain_percent': 3,
                 'scope': 'Operator screen only. No model gate or automatic model dispatch.'}}
    (root/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({'root': str(root), 'files': len(files), 'status': 'prepared'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    main(args.source.resolve(), args.output.resolve())
