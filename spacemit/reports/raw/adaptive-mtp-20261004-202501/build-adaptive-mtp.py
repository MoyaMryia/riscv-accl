#!/usr/bin/env python3
"""Isolated server-only build using the tested Ninja compiler/link commands."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess

def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def build(root):
    manifest=json.loads((root/'build-run.json').read_text())
    base=Path(manifest['baseline_source']); old=base/'build'; source=root/'source'; output=root/'build'
    (root/'phase').write_text('build isolated adaptive MTP server\n')
    subprocess.run(['git','clone','--shared',str(base),str(source)],check=True)
    if subprocess.check_output(['git','-C',base,'rev-parse','--short=7','HEAD'],text=True).strip()!='a990751':
        raise ValueError('baseline revision differs')
    # Kernel modifications stay in the original checkout and runtime. This
    # candidate changes only server code, links the unchanged measured libraries.
    subprocess.run(['git','apply','--check',str(root/'adaptive-mtp.patch')],cwd=source,check=True)
    subprocess.run(['git','apply',str(root/'adaptive-mtp.patch')],cwd=source,check=True)
    commands=subprocess.check_output(['ninja','-C',str(old),'-t','commands','llama-server'],text=True).splitlines()
    compiled=[]; compile_jobs=[]
    for command in commands:
        argv=shlex.split(command)
        if '-c' not in argv or '-o' not in argv: continue
        src=Path(argv[argv.index('-c')+1])
        if str(src).startswith(str(base/'tools/server')+'/'):
            rebuilt=[]
            for i,arg in enumerate(argv):
                if i>0 and argv[i-1] in ('-o','-MF','-MT'):
                    arg=str(output/arg); Path(arg).parent.mkdir(parents=True,exist_ok=True)
                elif str(base) in arg and str(old) not in arg:
                    arg=arg.replace(str(base),str(source))
                rebuilt.append(arg)
            compile_jobs.append(rebuilt)
            compiled.append(rebuilt[rebuilt.index('-o')+1])
    if len(compile_jobs)!=13: raise ValueError('unexpected server compilation unit count')
    (output/'bin').mkdir(parents=True,exist_ok=True)
    def compile_one(argv):
        print('compile '+Path(argv[argv.index('-c')+1]).name,flush=True)
        subprocess.run(argv,cwd=old,check=True)
    reused=[]
    if manifest.get('reuse_build_root'):
        prior=Path(manifest['reuse_build_root'])
        if digest(prior/'adaptive-mtp.patch')!=digest(root/'adaptive-mtp.patch'):
            raise ValueError('reuse requires identical server patch')
        for argv in compile_jobs:
            src=Path(argv[argv.index('-c')+1]); obj=Path(argv[argv.index('-o')+1])
            old_src=prior/'source'/src.relative_to(source)
            old_obj=prior/'build'/obj.relative_to(output)
            if digest(src)!=digest(old_src):raise ValueError('reused source differs')
            shutil.copyfile(old_obj,obj)
            reused.append({'object':str(old_obj),'sha256':digest(old_obj),'source_sha256':digest(src)})
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            list(executor.map(compile_one,compile_jobs))
    objects=[p for p in compiled if '/server-context.dir/' in p]
    archive=output/'tools/server/libserver-context.a'
    subprocess.run(['/usr/bin/ar','rcs',str(archive),*objects],check=True)
    links=[]
    for suffix in ('bin/libllama-server-impl.so','bin/llama-server'):
        matching=[shlex.split(c) for c in commands if ' -o '+suffix+' ' in c and ' -c ' not in c]
        if len(matching)!=1:raise ValueError('unexpected server link command')
        argv=matching[0]
        start=next(i for i,a in enumerate(argv) if Path(a).name=='g++-14')
        argv=argv[start:]; argv=argv[:argv.index('&&')] if '&&' in argv else argv
        rewritten=[]
        for i,arg in enumerate(argv):
            if i>0 and argv[i-1]=='-o': arg=str(output/arg)
            elif not arg.startswith('-') and (arg.endswith(('.o','.a','.so')) or '.so.' in arg):
                if not Path(arg).is_absolute():
                    arg=str(output/arg) if (output/arg).exists() else str(old/arg)
            rewritten.append(arg)
        links.append(rewritten)
        subprocess.run(rewritten,cwd=old,check=True)
    compiler=compile_jobs[0][0]
    subprocess.run([compiler,'-std=c++17','-O2','-I',str(source/'tools/server'),
        str(root/'test-spine-mtp-policy.cpp'),'-o',str(output/'test-policy')],check=True)
    subprocess.run([str(output/'test-policy')],check=True)
    (root/'build-provenance.json').write_text(json.dumps({
        'baseline_source':str(base),'candidate_source':str(source),'patch_sha256':digest(root/'adaptive-mtp.patch'),
        'compile_commands':compile_jobs,'link_commands':links,
        'reused_objects':reused,
        'candidate_sha256':{str(p):digest(p) for p in (output/'bin').iterdir()},
        'source_sha256':{str(p.relative_to(source)):digest(p) for p in (source/'tools/server').iterdir() if p.is_file()},
        'inference_libraries':'unchanged measured baseline; selected by runtime LD_LIBRARY_PATH',
    },indent=2)+'\n')
    (root/'build-exit-status').write_text('0\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);args=p.parse_args()
    try:build(args.root.resolve())
    except BaseException:
        (args.root/'build-exit-status').write_text('1\n');raise
