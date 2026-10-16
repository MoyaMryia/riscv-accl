"""记录起点兼容构建的源码、工具链、运行库和产物身份。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def record(root):
    if not os.environ.get('TMUX') or os.environ.get('K1_PACKAGE_LOCK_FD') != '9':
        raise ValueError('use with-lock.sh in tmux')
    os.fstat(9)
    source = root / 'baseline-load-source'
    build = root / 'baseline-load-build'
    if (root / 'baseline-load-build-exit-status').read_text().strip() != '0':
        raise ValueError('baseline build does not pass')
    source_receipt = root / 'baseline-load-source-receipt.json'
    data = json.loads(source_receipt.read_text())
    actual = {str(p.relative_to(source)): sha(p) for p in sorted(source.rglob('*')) if p.is_file()}
    if actual != data['files_sha256']:
        raise ValueError('baseline source differs')
    if sha(root / 'baseline-load-compatibility.patch') != data['patch_sha256']:
        raise ValueError('baseline compatibility patch differs')
    original = root / 'baseline-source'
    pins = json.loads((root / 'baseline-source-receipt.json').read_text())['files_sha256']
    if any(sha(original / n) != h for n, h in pins.items()):
        raise ValueError('original source differs')
    changed = sorted(n for n in actual if actual[n] != pins[n])
    if changed != ['ggml/src/ggml-cpu/CMakeLists.txt', 'src/models/qwen35.cpp']:
        raise ValueError('baseline compatibility scope differs')
    original_graph = (original / 'src/models/qwen35.cpp').read_text()
    current_graph = (source / 'src/models/qwen35.cpp').read_text()
    marker = 'std::unique_ptr<llm_graph_context> llama_model_qwen35::build_arch_graph'
    if current_graph[current_graph.index(marker):] != original_graph[original_graph.index(marker):]:
        raise ValueError('baseline graph differs')
    tools = Path.home() / 'Projects/llm-bench/.toolchain'
    compilers = [tools / 'gcc14/usr/bin' / n for n in ('gcc-14', 'g++-14')]
    spert = Path.home() / 'Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2'
    tcm = tools / 'spine-tcm'
    cache = {}
    for line in (build / 'CMakeCache.txt').read_text().splitlines():
        if line and not line.startswith(('#', '//')) and '=' in line:
            name, value = line.split('=', 1)
            cache[name.split(':', 1)[0]] = value
    expected = dict(CMAKE_BUILD_TYPE='Release', GGML_CPU_RISCV64_SPACEMIT='ON',
        GGML_OPENMP='OFF', GGML_RV_ZBA='ON', GGML_NATIVE='OFF', GGML_CPU_REPACK='OFF',
        CMAKE_C_COMPILER=str(compilers[0]), CMAKE_CXX_COMPILER=str(compilers[1]), SPERT_DIR=str(spert))
    if any(cache.get(n) != value for n, value in expected.items()):
        raise ValueError('baseline build configuration differs')
    if not all((build / 'bin' / n).is_file() for n in ('llama-server', 'llama-bench')):
        raise ValueError('baseline binaries are incomplete')
    result = dict(source_commit=data['commit'], source_receipt_sha256=sha(source_receipt),
        compatibility_patch_sha256=data['patch_sha256'], graph_code_unchanged=True,
        binaries={p.name: sha(p) for p in sorted((build / 'bin').iterdir()) if p.is_file()},
        build_files={n: sha(build / n) for n in ('CMakeCache.txt', 'compile_commands.json')},
        build_configuration=expected,
        compilers={str(p): dict(sha256=sha(p), version=subprocess.check_output([str(p), '--version'], text=True))
            for p in compilers},
        dependencies={str(p.absolute()): sha(p) for folder in (tcm, spert / 'lib')
            for p in sorted(folder.glob('*.so*')) if p.is_file()},
        record_tool_sha256=sha(Path(__file__)))
    output = build / 'build-receipt.json'
    if output.exists():
        if json.loads(output.read_text()) != result:
            raise ValueError('existing baseline build receipt differs')
    else:
        output.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS: baseline source, configuration, toolchain, dependencies, and binary receipt')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    record(p.parse_args().root.resolve())
