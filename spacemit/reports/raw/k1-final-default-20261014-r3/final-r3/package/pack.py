#!/usr/bin/env python3
"""生成包含源码、二进制、入口与证据的确定性归档。"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

import package

HERE=Path(__file__).resolve().parent


def copy_directory(source,destination):
    shutil.copytree(source,destination,symlinks=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.git'))


def pack(args):
    version=package.manifest()['version']; output=args.output.resolve()
    if output.exists(): raise ValueError('output directory exists')
    package.verify(args.source.resolve())
    output.mkdir(parents=True)
    root=output/version;root.mkdir()
    copy_directory(args.source,root/'source')
    copy_directory(HERE,root/'package')
    build=root/'build';build.mkdir()
    copy_directory(args.build/'bin',build/'bin')
    for n in ('build-receipt.json','CMakeCache.txt','compile_commands.json'):
        shutil.copy2(args.build/n,build/n)
    record=json.loads((build/'build-receipt.json').read_text())
    for n,h in record['binaries'].items():
        if package.sha(build/'bin'/n)!=h: raise ValueError('binary differs: '+n)
    copy_directory(args.evidence,root/'evidence')
    (root/'evidence/relocated-build').exists() and shutil.rmtree(root/'evidence/relocated-build')
    shutil.copy2(args.requirements,root/'Requirements.md')
    shutil.copy2(args.report,root/'VALIDATION.md')
    shutil.copy2(HERE/'README.md',root/'README.md')
    if args.materials: copy_directory(args.materials,root/'model-materials')
    if args.reference: copy_directory(args.reference,root/'reference-release')
    (root/'VERSION').write_text(version+'\n')
    links={}
    for p in root.rglob('*'):
        if p.is_symlink():
            target=p.readlink()
            if target.is_absolute() or root not in p.resolve().parents: raise ValueError('external link: '+str(p))
            links[str(p.relative_to(root))]=str(target)
    (root/'SYMLINKS.json').write_text(json.dumps(links,indent=2)+'\n')
    files=[p for p in sorted(root.rglob('*')) if p.is_file() and not p.is_symlink()]
    (root/'SHA256SUMS').write_text(''.join(package.sha(p)+'  '+str(p.relative_to(root))+'\n' for p in files))
    archive=output/(version+'.tar.gz')
    with archive.open('wb') as raw:
        with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as gz:
            with tarfile.open(fileobj=gz,mode='w',format=tarfile.PAX_FORMAT) as tar:
                for path in [root,*sorted(root.rglob('*'))]:
                    info=tar.gettarinfo(str(path),arcname=str(path.relative_to(output)))
                    info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
                    info.mode=0o755 if path.is_dir() or path.stat().st_mode & 0o111 else 0o644
                    info.pax_headers={}
                    if info.isfile():
                        with path.open('rb') as f: tar.addfile(info,f)
                    else: tar.addfile(info)
    digest=package.sha(archive)
    (output/(archive.name+'.sha256')).write_text(digest+'  '+archive.name+'\n')
    print(json.dumps({'archive':str(archive),'sha256':digest,'files':len(files)+1,'version':version},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','build','evidence','requirements','report','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--materials',type=Path);p.add_argument('--reference',type=Path)
    pack(p.parse_args())
