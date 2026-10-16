"""从已核验统一源码生成固定默认配置的独立交付源码。"""
import argparse
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
from state_fixture import generate as state_fixture


def load(path):
    spec = importlib.util.spec_from_file_location('reference_package', path / 'package.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def generate(reference_package, source, vendor, policy, output):
    pkg = load(reference_package)
    pkg.verify(source)
    pkg.verify(vendor, clean=True)
    data = json.loads(policy.read_text())
    config = data['config']
    mask, threads, batch = (config[n] for n in ('mask', 'threads', 'ubatch'))
    if mask not in range(8) or threads not in (2, 4) or batch not in (16, 32, 64, 128):
        raise ValueError('policy is outside the frozen search')
    if not data.get('search_converged'):
        raise ValueError('search does not converge')
    if not all(data['quality'][n]['checks'] == 106
        and data['quality'][n]['control'] == data['quality'][n]['selected']
        and re.fullmatch('[0-9a-f]{64}', data['quality'][n]['selected']) for n in ('2B', '4B')):
        raise ValueError('policy quality evidence is incomplete')
    if output.exists():
        raise ValueError('output exists')
    output.mkdir(parents=True)
    target = output / 'source'
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))
    changed = set(pkg.manifest()['files_sha256'])

    def replace(name, old, new):
        path = target / name
        text = path.read_text()
        if text.count(old) != 1:
            raise ValueError('source anchor differs: ' + name)
        path.write_text(text.replace(old, new))
        changed.add(name)

    header = 'ggml/include/spine-k1-defaults.h'
    (target / header).write_text('#pragma once\n'
        '// Fixed K1 defaults from the measured selection.\n'
        f'#define SPINE_K1_DEFAULT_MASK {mask}\n'
        f'#define SPINE_K1_DEFAULT_C1 {3 if mask & 2 else 0}\n'
        f'#define SPINE_K1_DEFAULT_C2 {int(bool(mask & 4))}\n'
        f'#define SPINE_K1_DEFAULT_B1 {int(bool(mask & 1))}\n'
        f'#define SPINE_K1_DEFAULT_THREADS {threads}\n'
        f'#define SPINE_K1_DEFAULT_BATCH {batch}\n'
        '#define SPINE_K1_DEFAULT_CONTEXT 12288\n')
    changed.add(header)
    name = 'src/models/spine-k1-ssm-conv.h'
    replace(name, '// Internal opt-in CPU experiment; this is not a public GGML API extension.',
        '// Private K1 CPU path. This does not change the public GGML API.')
    replace(name, '#include "ggml.h"', '#include "spine-k1-defaults.h"\n#include "ggml.h"')
    replace(name, "    return value && (value[0] == '1' || value[0] == '2' || value[0] == '3') && value[1] == 0\n        ? value[0] - '0' : 0;",
        "    if (!value) return SPINE_K1_DEFAULT_C1;\n    return value[0] >= '0' && value[0] <= '3' && value[1] == 0\n        ? value[0] - '0' : 0;")
    name = 'ggml/src/ggml-cpu/spine-k1-local-attention.h'
    replace(name, '#include <cstdio>', '#include "spine-k1-defaults.h"\n#include <cstdio>')
    replace(name, '    return value && strcmp(value, "1") == 0;',
        '    if (value) return strcmp(value, "1") == 0;\n'
        '    if (strcmp(name, "SPINE_K1_FA_GQA") == 0) return SPINE_K1_DEFAULT_B1;\n'
        '    if (strcmp(name, "SPINE_GDN_PREFILL") == 0) return SPINE_K1_DEFAULT_C2;\n'
        '    if (strcmp(name, "SPINE_K1_GDN_REVISION") == 0) return SPINE_K1_DEFAULT_C2;\n'
        '    return false;')
    name = 'ggml/src/ggml-cpu/ops.cpp'
    replace(name, '(getenv("SPINE_GDN_PREFILL") != nullptr && strcmp(getenv("SPINE_GDN_PREFILL"), "1") == 0)',
        'spine_k1_flag("SPINE_GDN_PREFILL")')
    name = 'ggml/src/ggml-cpu/spacemit/ime.cpp'
    replace(name, "? value[0] - '0' : 0;", "? value[0] - '0' : 3;")
    replace(name, "            return env && env[0] == '1' && env[1] == '\\0';",
        "            return !env || (env[0] == '1' && env[1] == '\\0');")
    name = 'common/common.h'
    replace(name, '#include "llama-cpp.h"', '#include "llama-cpp.h"\n#include "spine-k1-defaults.h"')
    replace(name, 'int      n_threads                   = -1;', 'int      n_threads                   = SPINE_K1_DEFAULT_THREADS;')
    replace(name, 'int32_t n_ctx                 =     0;', 'int32_t n_ctx                 = SPINE_K1_DEFAULT_CONTEXT;')
    replace(name, 'int32_t n_batch               =  2048;', 'int32_t n_batch               = SPINE_K1_DEFAULT_BATCH;')
    replace(name, 'int32_t n_ubatch              =   512;', 'int32_t n_ubatch              = SPINE_K1_DEFAULT_BATCH;')
    replace(name, 'int32_t n_gpu_layers       = -1;', 'int32_t n_gpu_layers       = 0;')
    replace(name, 'bool    fit_params         = true;', 'bool    fit_params         = false;')
    replace(name, 'flash_attn_type   = LLAMA_FLASH_ATTN_TYPE_AUTO;', 'flash_attn_type   = LLAMA_FLASH_ATTN_TYPE_ENABLED;')
    name = 'src/models/qwen35.cpp'
    replace(name, '    if (il == 0) {\n        fprintf(stderr, "K1_SSM_CONV',
        '    const char * k1_trace = std::getenv("SPINE_K1_TRACE");\n'
        '    if (il == 0 && k1_trace && k1_trace[0] == \'1\' && k1_trace[1] == 0) {\n        fprintf(stderr, "K1_SSM_CONV')
    name = 'tools/server/server-context.cpp'
    replace(name, '        n_ctx = llama_n_ctx(ctx_tgt);',
        '        n_ctx = llama_n_ctx(ctx_tgt);\n'
        '        fprintf(stderr, "K1_EFFECTIVE_DEFAULTS threads=%d batch_threads=%d batch=%u ubatch=%u context=%u slots=%d flash=%d gpu=%d key=%s value=%s mask=%d\\n",\n'
        '            llama_n_threads(ctx_tgt), llama_n_threads_batch(ctx_tgt), llama_n_batch(ctx_tgt),\n'
        '            llama_n_ubatch(ctx_tgt), llama_n_ctx(ctx_tgt), params_base.n_parallel,\n'
        '            int(params_base.flash_attn_type == LLAMA_FLASH_ATTN_TYPE_ENABLED), params_base.n_gpu_layers,\n'
        '            ggml_type_name(params_base.cache_type_k), ggml_type_name(params_base.cache_type_v), SPINE_K1_DEFAULT_MASK);')
    patch = ''
    hashes = {}
    for name in sorted(changed):
        old = vendor / name
        new = target / name
        hashes[name] = pkg.sha(new)
        patch += ''.join(difflib.unified_diff(old.read_text().splitlines(True) if old.exists() else [],
            new.read_text().splitlines(True), fromfile='a/' + name if old.exists() else '/dev/null', tofile='b/' + name))
    package = output / 'package'
    package.mkdir()
    for name in ('package.py', 'record-build.py', 'build.sh', 'with-lock.sh', 'vendor-source.json', 'pack.py'):
        shutil.copy2(reference_package / name, package / name)
    shutil.copytree(reference_package / 'tests', package / 'tests',
        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'test_package.py'))
    fixture = Path(__file__).resolve().parents[3] / 'lab/final-default-20261013/test-state-all-masks.cpp'
    shutil.copy2(fixture, package / 'tests/test-state.cpp')
    (package / 'tests/test-default-state.cpp').write_text(state_fixture(fixture.read_text()))
    build_script = (package / 'build.sh').read_text()
    anchor = 'for pkg_probe in attention ssm gdn state route; do'
    if build_script.count(anchor) != 1:
        raise ValueError('probe build anchor differs')
    (package / 'build.sh').write_text(build_script.replace(anchor,
        'for pkg_probe in attention ssm gdn state route default-state; do'))
    shutil.copy2(Path(__file__).parent / 'start_default.py', package / 'start.py')
    shutil.copy2(Path(__file__).parent / 'DELIVERY-README.md', package / 'README.md')
    shutil.copy2(Path(__file__).parent / 'DELIVERY-DEPENDENCIES.md', package / 'DEPENDENCIES.md')
    shutil.copy2(policy, package / 'default-policy.json')
    (package / 'unified.patch').write_text(patch)
    manifest = dict(pkg.manifest(), version=data['version'], source_revision='combined-r1+baked-defaults',
        files_sha256=hashes, patch_sha256=hashlib.sha256(patch.encode()).hexdigest(),
        default_profile='compiled-default', acceptance='pending-final-comparison')
    (package / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    receipt = load(package).verify(target)
    (output / 'generation-receipt.json').write_text(json.dumps(dict(source=receipt, policy=data,
        changed_files=sorted(changed)), indent=2) + '\n')
    return receipt


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('reference-package', 'source', 'vendor', 'policy', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(generate(a.reference_package.resolve(), a.source.resolve(), a.vendor.resolve(),
        a.policy.resolve(), a.output.resolve()), indent=2))
