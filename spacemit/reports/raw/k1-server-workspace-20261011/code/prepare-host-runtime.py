#!/usr/bin/env python3
"""收集本机 QEMU 和独立运行依赖，不修改系统目录。"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SYSTEM_LIBS = {'libc.so.6', 'libm.so.6', 'libpthread.so.0', 'libdl.so.2',
               'librt.so.1', 'libutil.so.1', 'libresolv.so.2'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(args):
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    sources = {}

    def copy(src, dst):
        src = Path(src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        sources[str(src)] = {'destination': str(dst.relative_to(out)), 'sha256': sha(dst)}

    dependencies = []
    for name in ('qemu-riscv64', 'qemu-system-riscv64'):
        source = args.qemu_prefix/'bin'/name
        copy(source, out/'libexec'/name)
        dependencies.extend((source, args.vendor_root/'bin'/name))
        wrapper = out/'bin'/name
        wrapper.parent.mkdir(parents=True, exist_ok=True)
        wrapper.write_text('#!/usr/bin/env bash\nset -euo pipefail\n'
            'runtime_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)\n'
            'export LD_LIBRARY_PATH="$runtime_root/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"\n'
            'exec "$runtime_root/libexec/'+name+'" "$@"\n')
        wrapper.chmod(0o755)
    copy(args.qemu_prefix/'include/qemu-plugin.h', out/'include/qemu-plugin.h')
    copy(args.qemu_prefix/'share/qemu/opensbi-riscv64-generic-fw_dynamic.bin',
         out/'share/qemu/opensbi-riscv64-generic-fw_dynamic.bin')
    compiler_root = REPO/'lab/toolchain/toolchain/riscv'
    dependencies.extend((compiler_root/'bin/riscv64-unknown-linux-gnu-g++',
                         compiler_root/'libexec/gcc/riscv64-unknown-linux-gnu/16.1.0/cc1',
                         compiler_root/'libexec/gcc/riscv64-unknown-linux-gnu/16.1.0/cc1plus'))
    listing = subprocess.check_output(['ldd', *map(str, dependencies)], text=True, stderr=subprocess.STDOUT)
    (out/'dependency-source.log').write_text(listing)
    if 'not found' in listing:
        raise ValueError('local host dependency is absent')
    for name, source in sorted(set(re.findall(r'^\s*(\S+) => (/\S+) ', listing, re.MULTILINE))):
        if name not in SYSTEM_LIBS:
            copy(source, out/'lib'/name)
    for src, dst in ((Path('/usr/include/glib-2.0'), out/'include/glib-2.0'),
                     (Path('/usr/lib/x86_64-linux-gnu/glib-2.0/include'), out/'lib/glib-2.0/include')):
        for path in sorted(src.rglob('*')):
            if path.is_file():
                copy(path, dst/path.relative_to(src))
    (out/'lib/libglib-2.0.so').symlink_to('libglib-2.0.so.0')
    version = subprocess.check_output(['pkg-config', '--modversion', 'glib-2.0'], text=True).strip()
    pc = out/'lib/pkgconfig/glib-2.0.pc'
    pc.parent.mkdir(parents=True, exist_ok=True)
    pc.write_text('prefix=${pcfiledir}/../..\nlibdir=${prefix}/lib\nincludedir=${prefix}/include\n\n'
        'Name: GLib\nDescription: Core library\nVersion: '+version+'\n'
        'Libs: -L${libdir} -lglib-2.0\n'
        'Cflags: -I${includedir}/glib-2.0 -I${libdir}/glib-2.0/include\n')
    (out/'manifest.json').write_text(json.dumps({'schema': 1, 'sources': sources,
        'host_architecture': 'x86_64', 'glib_version': version,
        'system_libraries': sorted(SYSTEM_LIBS), 'status': 'prepared-not-verified-on-server'}, indent=2)+'\n')
    (out/'symlinks.json').write_text(json.dumps({str(p.relative_to(out)): str(p.readlink())
        for p in out.rglob('*') if p.is_symlink()}, indent=2)+'\n')
    files = sorted(p for p in out.rglob('*') if p.is_file() and not p.is_symlink())
    (out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(out))+'\n' for p in files))
    print(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--qemu-prefix', type=Path, default=Path('/usr/local'))
    parser.add_argument('--vendor-root', type=Path, required=True)
    main(parser.parse_args())
