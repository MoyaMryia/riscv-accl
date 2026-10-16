"""为起始源码添加 K1 构建和未启用 MTP 张量加载的兼容处理。"""
import difflib
import hashlib
import json
from pathlib import Path
import shutil

root = Path(__file__).resolve().parent
original = root / 'baseline-source'
source = root / 'baseline-load-source'
pins = json.loads((root / 'baseline-source-receipt.json').read_text())['files_sha256']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert all(sha(original / n) == h for n, h in pins.items())
assert not source.exists()
shutil.copytree(original, source)
cmake = source / 'ggml/src/ggml-cpu/CMakeLists.txt'
line = '                ggml-cpu/spacemit/ime2_kernels.cpp\n'
text = cmake.read_text()
assert text.count(line) == 1
cmake.write_text(text.replace(line, ''))
path = source / 'src/models/qwen35.cpp'
text = path.read_text()
anchor = '    tok_embd = create_tensor(tn(LLM_TENSOR_TOKEN_EMBD, "weight"), { n_embd, n_vocab }, 0);'
assert text.count(anchor) == 1
text = text.replace(anchor,
    '    // Load the draft map. The main decoder does not use this tensor.\n'
    '    if (const ggml_tensor * meta = ml.get_tensor_meta("d2t")) {\n'
    '        GGML_ASSERT(meta->type == GGML_TYPE_I64);\n'
    '        GGML_ASSERT(meta->ne[0] > 0 && meta->ne[0] <= n_vocab);\n'
    '        d2t = create_tensor(tn(LLM_TENSOR_D2T), { meta->ne[0] }, 0);\n'
    '    }\n\n' + anchor)
anchor = '        layer.nextn.shared_head_head = create_tensor(tn(LLM_TENSOR_NEXTN_SHARED_HEAD_HEAD, "weight", il), { n_embd, n_vocab },     TENSOR_NOT_REQUIRED);'
assert text.count(anchor) == 1
text = text.replace(anchor,
    '        // Use the stored draft head width. Keep the main output head unchanged.\n'
    '        const std::string head_name = tn(LLM_TENSOR_NEXTN_SHARED_HEAD_HEAD, "weight", il).str();\n'
    '        const ggml_tensor * head_meta = ml.get_tensor_meta(head_name.c_str());\n'
    '        const int64_t head_vocab = head_meta ? head_meta->ne[1] : n_vocab;\n'
    '        GGML_ASSERT(head_vocab > 0 && head_vocab <= n_vocab);\n'
    '        layer.nextn.shared_head_head = create_tensor(tn(LLM_TENSOR_NEXTN_SHARED_HEAD_HEAD, "weight", il), { n_embd, head_vocab }, TENSOR_NOT_REQUIRED);')
original_text = (original / 'src/models/qwen35.cpp').read_text()
graph = 'std::unique_ptr<llm_graph_context> llama_model_qwen35::build_arch_graph'
assert text[text.index(graph):] == original_text[original_text.index(graph):]
path.write_text(text)
actual = {str(p.relative_to(source)): sha(p) for p in sorted(source.rglob('*')) if p.is_file()}
assert set(actual) == set(pins)
changed = sorted(n for n in actual if actual[n] != pins[n])
assert changed == ['ggml/src/ggml-cpu/CMakeLists.txt', 'src/models/qwen35.cpp']
delta = ''.join(''.join(difflib.unified_diff((original / n).read_text().splitlines(True),
    (source / n).read_text().splitlines(True), fromfile='a/' + n, tofile='b/' + n)) for n in changed)
(root / 'baseline-load-compatibility.patch').write_text(delta)
(root / 'baseline-load-source-receipt.json').write_text(json.dumps(dict(
    commit='5ad05d8796cb094ee23a3a0152874f8a2b3060f8', compatibility_only=changed,
    graph_code_unchanged=True, speculative_decode=False, files_sha256=actual,
    patch_sha256=hashlib.sha256(delta.encode()).hexdigest()), indent=2) + '\n')
