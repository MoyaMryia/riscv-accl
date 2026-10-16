#!/usr/bin/env python3
"""记录源码、工具链、依赖与构建产物身份。"""
import json
from pathlib import Path
import subprocess
import sys
import package
source, build, cc, cxx, spert, tcm = map(Path, sys.argv[1:])
record = dict(package=package.manifest()['version'], source=package.verify(source),
    binaries={p.name: package.sha(p) for p in sorted((build/'bin').iterdir()) if p.is_file()},
    dependencies={str(p.absolute()): package.sha(p) for folder in (spert/'lib',tcm) for p in sorted(folder.glob('*.so*')) if p.is_file()},
    compilers={str(p): {'sha256':package.sha(p),'version':subprocess.check_output([str(p),'--version'],text=True)} for p in (cc,cxx)},
    build_files={n:package.sha(build/n) for n in ('CMakeCache.txt','compile_commands.json')})
(build/'build-receipt.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
