"""使用编译默认值启动固定模型，不接收优化配置开关。"""
import argparse
import json
import os
from pathlib import Path
import package

HERE = Path(__file__).resolve().parent


def environment(binary_dir, spert, tcm):
    env = {k: v for k, v in os.environ.items()
        if not k.startswith(('SPINE_', 'SPACEMIT_', 'GGML_', 'LLAMA_', 'OMP_', 'GOMP_', 'KMP_'))
        and k not in ('LD_LIBRARY_PATH', 'LD_PRELOAD', 'LD_AUDIT')}
    env['LD_LIBRARY_PATH'] = ':'.join(str(p.resolve()) for p in (binary_dir, tcm, spert / 'lib'))
    return env


def verify(build, model, spert, tcm):
    manifest = package.manifest()
    receipt = json.loads((build / 'build-receipt.json').read_text())
    if receipt['package'] != manifest['version']:
        raise ValueError('build version differs')
    actual = {p.name for p in (build / 'bin').iterdir() if p.is_file()}
    if actual != set(receipt['binaries']):
        raise ValueError('binary list differs')
    for name, value in receipt['binaries'].items():
        if package.sha(build / 'bin' / name) != value:
            raise ValueError('binary differs: ' + name)
    model_sha = package.sha(model)
    known = [n for n, item in manifest['models'].items() if item['sha256'] == model_sha]
    if len(known) != 1:
        raise ValueError('model differs')
    for name, value in receipt['dependencies'].items():
        paths = [folder / Path(name).name for folder in (tcm, spert / 'lib')]
        if not any(p.is_file() and package.sha(p) == value for p in paths):
            raise ValueError('runtime differs: ' + Path(name).name)
    return known[0], model_sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model', type=Path, required=True)
    p.add_argument('--build', type=Path, default=HERE.parent / 'build')
    p.add_argument('--spert', type=Path, default=Path(os.environ.get('K1_SPERT_DIR',
        str(Path.home() / 'Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2'))))
    p.add_argument('--tcm', type=Path, default=Path(os.environ.get('K1_TCM_DIR',
        str(Path.home() / 'Projects/llm-bench/.toolchain/spine-tcm'))))
    p.add_argument('--port', type=int)
    p.add_argument('--receipt', type=Path)
    p.add_argument('--describe', action='store_true')
    a = p.parse_args()
    try:
        build = a.build.resolve()
        env = environment(build / 'bin', a.spert, a.tcm)
        model, model_sha = verify(build, a.model, a.spert, a.tcm)
        argv = [str(build / 'bin/llama-server'), '-m', str(a.model.resolve()), '--alias', 'local']
        if a.port is not None:
            argv += ['--port', str(a.port)]
        record = dict(version=package.manifest()['version'], model=model, model_sha256=model_sha,
            argv=argv, environment={'LD_LIBRARY_PATH': env['LD_LIBRARY_PATH']},
            compiled_policy=json.loads((HERE / 'default-policy.json').read_text()))
        if a.receipt:
            a.receipt.write_text(json.dumps(record, indent=2) + '\n')
        if a.describe:
            print(json.dumps(record, indent=2))
            return
        if not os.environ.get('TMUX') or os.environ.get('K1_PACKAGE_LOCK_FD') != '9':
            raise ValueError('use with-lock.sh in tmux')
        os.fstat(9)
        os.execve(argv[0], argv, env)
    except (ValueError, OSError) as error:
        p.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
