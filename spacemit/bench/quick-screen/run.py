#!/usr/bin/env python3
"""持锁构建三个原型，并保存短筛选记录。"""
import hashlib
import fcntl
import json
import math
import os
from pathlib import Path
import shlex
import subprocess
import sys
import traceback


class NumericStop(Exception):
    pass


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def gate(base, candidate):
    if len(base) != 6 or len(candidate) != 6:
        raise ValueError('six blocks are required')
    if any(not math.isfinite(x) or x <= 0 for x in base+candidate):
        raise ValueError('invalid samples')
    mean = sum(base)/6
    gain = (1-sum(candidate)/6/mean)*100
    spread = (max(base)-min(base))/mean*100
    return {'reduction_percent': gain, 'control_range_percent': spread,
            'advance': gain > 3 and gain > spread, 'clear_regression': -gain > max(3,spread)}


def compile_args(command, source, output, include):
    words = shlex.split(command)
    result = []; i = 0
    while i < len(words):
        if words[i] in ('-o','-c','-MT','-MF','-MQ'):
            i += 2; continue
        if words[i] in ('-MD','-MMD'):
            i += 1; continue
        result.append(words[i]); i += 1
    return [result[0], '-I'+str(include), *result[1:], '-c', str(source), '-o', str(output)]


def link_args(command, output, replacements):
    pieces = command.split(' && ')
    if len(pieces) != 3 or pieces[0] != ':' or pieces[-1] != ':':
        raise ValueError('link recipe differs')
    words = shlex.split(pieces[1]); counts = dict.fromkeys(replacements,0)
    for i, word in enumerate(words):
        if i and words[i-1] == '-o': words[i] = str(output)
        for suffix, path in replacements.items():
            if word.endswith(suffix): words[i] = str(path); counts[suffix] += 1
    if any(count != 1 for count in counts.values()): raise ValueError('object match differs')
    return words


class Screen:
    def __init__(self, root, provenance):
        self.root=root; self.out=root/'run'; self.out.mkdir(exist_ok=True)
        self.manifest=json.loads((root/'manifest.json').read_text())
        self.expected=json.loads(provenance.read_text())
        self.server=next(Path(p) for p in self.expected['artifacts_sha256'] if p.endswith('/llama-server'))
        self.source=self.server.parents[2]; self.build=self.source/'build'
        self.recipes=json.loads((self.build/'compile_commands.json').read_text())
        self.link=subprocess.check_output(['ninja','-C',self.build,'-t','commands','bin/libggml-cpu.so.0.16.0'],text=True).splitlines()[-1]
        self.compiler=next(shlex.split(r['command'])[0] for r in self.recipes if r['file'].endswith('/ops.cpp'))
        self.commands=[]; self.baseline={}; self.rows=[]
        self.summary={'status':'running','scope':'operator-prototypes','models':'not-run','candidates':{}}
        self.env={k:v for k,v in os.environ.items() if not k.startswith('SPINE_')}
        self.env.update(LD_LIBRARY_PATH=self.expected['runtime']['LD_LIBRARY_PATH'],
            SPINE_K1_GEMM_ROUTE='3',SPINE_FA_WIDE_TILE='1',SPINE_FA_K1_LAYOUT='0',SPINE_K1_TRACE='1')

    def save(self):
        (self.out/'summary.json').write_text(json.dumps(self.summary,indent=2)+'\n')

    def phase(self, text):
        (self.out/'phase').write_text(text+'\n'); print(text,flush=True); self.save()

    def command(self, args, label, arm=None, updates=None, timeout=300):
        env=dict(self.env); env.update(updates or {})
        if arm: env['LD_LIBRARY_PATH']=str(self.out/arm/'lib')+':'+env['LD_LIBRARY_PATH']
        args=list(map(str,args))
        self.commands.append({'argv':args,'cwd':str(self.build),'log':label+'.log',
            'environment':{k:v for k,v in env.items() if k.startswith('SPINE_') or k=='LD_LIBRARY_PATH'}})
        (self.out/'commands.json').write_text(json.dumps(self.commands,indent=2)+'\n')
        with (self.out/(label+'.log')).open('w') as stream:
            result=subprocess.run(args,cwd=self.build,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=timeout)
        if result.returncode:
            text=(self.out/(label+'.log')).read_text(errors='replace')
            if 'FAIL:' in text and any(word in text for word in (
                    'identity','differs','guard','reference','nonfinite','overwritten','processed rows')):
                raise NumericStop('numeric check stopped: '+label)
            raise subprocess.CalledProcessError(result.returncode,args)
        return (self.out/(label+'.log')).read_text(errors='replace')

    def verify(self):
        self.phase('verify')
        for rel, value in self.manifest['files_sha256'].items():
            if sha(self.root/rel) != value: raise ValueError('payload differs: '+rel)
        pins={**self.manifest['source_files_sha256'],**self.expected['source_sha256']}
        pins['ggml/src/ggml-cpu/spacemit/ime1_kernels.cpp']=self.manifest['ime_original_sha256']
        self.baseline={str(self.source/rel):value for rel,value in pins.items()}
        self.baseline.update({p:v for p,v in self.expected['artifacts_sha256'].items()
            if '/build/' in p or '/.toolchain/' in p or '/spert/' in p})
        for word in shlex.split(self.link.split(' && ')[1]):
            if word.endswith('.o'): self.baseline[str((self.build/word).resolve())]=sha(self.build/word)
        self.check_baseline()
        (self.out/'baseline-before.json').write_text(json.dumps(self.baseline,indent=2)+'\n')

    def check_baseline(self):
        bad=[p for p,value in self.baseline.items() if sha(p)!=value]
        (self.out/'baseline-check.json').write_text(json.dumps({'unchanged':not bad,'different':bad},indent=2)+'\n')
        if bad: raise ValueError('baseline differs: '+str(bad))

    def obj(self, relative, source, label):
        matches=[r for r in self.recipes if Path(r['file'])==self.source/relative]
        if len(matches)!=1: raise ValueError('compile recipe differs: '+relative)
        output=self.out/(label+'.o')
        argv=compile_args(matches[0]['command'],source,output,(self.source/relative).parent)
        argv.insert(1,'-I'+str(source.parent))
        self.command(argv,label+'-build')
        return output

    def library(self, arm, replacements):
        directory=self.out/arm/'lib'; directory.mkdir(parents=True)
        output=directory/'libggml-cpu.so.0.16.0'
        self.command(link_args(self.link,output,replacements),arm+'-link')
        for suffix in ('.so','.so.0'): (directory/('libggml-cpu'+suffix)).symlink_to(output.name)
        return output

    def harness(self, name, source, arm=None, extra=()):
        output=self.out/('test-'+name)
        includes=[self.root,self.source/'ggml/include',self.source/'ggml/src',self.source/'include',
            self.source/'ggml/src/ggml-cpu',self.source/'ggml/src/ggml-cpu/spacemit']
        argv=[self.compiler,'-O3','-std=c++17','-ffp-contract=off','-march=rv64gcv_zfh_zvfh_zicbop_zihintpause_zba',
            '-mabi=lp64d','-DSPINE_K1_BOARD',*('-I'+str(p) for p in includes),source]
        if arm: argv += ['-L'+str(self.out/arm/'lib'),'-L'+str(self.server.parent),'-lggml-cpu','-lggml-base']
        argv += [*extra,'-pthread','-o',output]
        self.command(argv,name+'-build',arm)
        return output

    def samples(self, name, binary, shapes, arms, arm_library=None):
        rows=[]
        for index, shape in enumerate(shapes):
            for block in range(6):
                for arm in (arms if block%2==0 else arms[::-1]):
                    label=f'{name}-shape{index}-block{block}-arm{arm}'
                    text=self.command([binary,'--bench',*shape,arm],label,arm_library)
                    records=[json.loads(line) for line in text.splitlines() if line.startswith('{')]
                    if len(records)!=1: raise ValueError('sample count differs')
                    row=records[0]
                    if row['arm']!=arm or row['wall_ms']<100 or not math.isfinite(row['wall_ms']):
                        raise ValueError('sample budget or arm differs')
                    row.update(block=block,shape_index=index)
                    rows.append(row); self.rows.append(row)
                    (self.out/'samples.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in self.rows))
        return rows

    def comparisons(self, rows, shapes, base, candidate):
        return [dict(shape=list(shape),**gate(
            [r['ms_per_call'] for r in rows if r['shape_index']==i and r['arm']==base],
            [r['ms_per_call'] for r in rows if r['shape_index']==i and r['arm']==candidate]))
            for i,shape in enumerate(shapes)]

    def conv(self):
        self.phase('conv-build-numeric')
        binary=self.harness('conv',self.root/'conv.cpp')
        text=self.command([binary],'conv-numeric')
        if 'PASS: 60 convolution cases;' not in text: raise ValueError('conv cases differ')
        shapes=[(6144,32),(8192,32),(6144,8),(8192,8)]
        rows=self.samples('conv',binary,shapes,[0,1])
        results=self.comparisons(rows,shapes,0,1)
        eligible=all(r['advance'] for r in results[:2]) and not any(r['clear_regression'] for r in results)
        return {'status':'promising' if eligible else 'stopped','numeric_cases':60,'comparisons':results,
            'limitation':'Standalone chain. GGML graph, alias rules and model state remain unverified.'}

    def b2(self):
        self.phase('b2-build-numeric')
        ops=self.obj('ggml/src/ggml-cpu/ops.cpp',self.root/'B2/overlay/ggml/src/ggml-cpu/ops.cpp','b2-ops')
        self.library('b2',{'/ops.cpp.o':ops,'/ime.cpp.o':self.route})
        binary=self.harness('b2',self.root/'b2.cpp','b2')
        hashes={}
        for arm in (None,'base','b2'):
            label='b2-numeric-'+str(arm); dump=self.out/(label+'.bin')
            text=self.command([binary,'--dump',dump],label,arm)
            if 'PASS: 159 B2 cases;' not in text: raise ValueError('B2 cases differ')
            if arm=='b2':
                for tile in (8,16):
                    for worker in range(4):
                        if f'QUICK_B2 tile={tile} worker={worker} workers=4' not in text:
                            raise ValueError('B2 activation differs')
            hashes[str(arm)]=sha(dump)
        if len(set(hashes.values()))!=1: raise NumericStop('original B2 dumps differ')
        shapes=[(2048,8),(2048,16),(256,8),(256,16)]
        results={}
        # 两种实现分别判定，不用另一种实现的收益掩盖失败。
        for tile in (8,16):
            rows=self.samples('b2-'+str(tile),binary,shapes,[0,tile],'b2')
            values=self.comparisons(rows,shapes,0,tile)
            eligible=all(r['advance'] for r in values[:2]) and not any(r['clear_regression'] for r in values)
            results[str(tile)]={'status':'promising' if eligible else 'stopped','comparisons':values}
        return {'status':'promising' if any(r['status']=='promising' for r in results.values()) else 'stopped',
            'numeric_cases':159,'dump_sha256':hashes,'tiles':results,'models':'unverified'}

    def ime(self):
        self.phase('ime-build-numeric')
        obj=self.obj('ggml/src/ggml-cpu/spacemit/ime1_kernels.cpp',self.root/'ime-schedule.cpp','ime-schedule')
        self.library('ime',{'/ime1_kernels.cpp.o':obj,'/ime.cpp.o':self.route})
        binary=self.harness('ime',self.root/'ime.cpp','ime')
        text=self.command([binary],'ime-numeric','ime')
        if 'PASS: 480 IME cases;' not in text: raise ValueError('IME cases differ')
        graph=self.harness('ime-graph',self.root/'ime-graph.cpp','ime')
        hashes={}
        for mode in (-1,0,1,2):
            dump=self.out/f'ime-graph-{mode}.bin'
            text=self.command([graph,'--dump',dump],f'ime-graph-{mode}',None if mode==-1 else 'ime',
                {'SPINE_QUICK_IME_SCHEDULE':str(max(0,mode))})
            if 'PASS: 104 production graph cases;' not in text: raise ValueError('IME graph cases differ')
            if mode>=0 and f'SPINE_QUICK_IME_SCHEDULE: mode={mode}' not in text:
                raise ValueError('IME graph activation differs')
            hashes[str(mode)]=sha(dump)
        if len(set(hashes.values()))!=1: raise NumericStop('original IME graph dumps differ')
        shapes=[(2048,6144),(6144,2048),(2560,9216),(9216,2560),(2048,248320),(2560,248320)]
        rows=self.samples('ime',binary,shapes,[0,1,2],'ime')
        original=self.comparisons(rows,shapes,0,2); fixed=self.comparisons(rows,shapes,1,2)
        eligible=not any(r['clear_regression'] for r in original+fixed)
        eligible &= all(any(original[i]['advance'] and fixed[i]['advance'] for i in group)
                        for group in ((0,1,4),(2,3,5)))
        return {'status':'promising' if eligible else 'stopped','numeric_cases':480,'graph_cases_per_arm':104,
            'dump_sha256':hashes,'versus_original':original,'versus_fixed':fixed,
            'limitation':'Warm raw kernel. Full-size production graph timing and model gates remain unverified.'}

    def run(self):
        self.verify()
        self.route=self.obj('ggml/src/ggml-cpu/spacemit/ime.cpp',
            self.root/'base/overlay/ggml/src/ggml-cpu/spacemit/ime.cpp','route')
        self.library('base',{'/ime.cpp.o':self.route})
        for name in ('conv','b2','ime'):
            try:
                self.summary['candidates'][name]=getattr(self,name)()
            except NumericStop:
                (self.out/(name+'-numerical-stop.txt')).write_text(traceback.format_exc())
                self.summary['candidates'][name]={'status':'numeric-stopped','models':'not-run'}
            except Exception:
                (self.out/(name+'-failure.txt')).write_text(traceback.format_exc())
                self.summary['candidates'][name]={'status':'fault','models':'not-run'}
            self.check_baseline(); self.save()
        self.summary['status']='complete-with-faults' if any(r['status']=='fault'
            for r in self.summary['candidates'].values()) else 'complete'
        self.phase(self.summary['status'])
        libraries={str(p.relative_to(self.out)):sha(p) for p in self.out.glob('*/lib/*.so.*') if p.is_file()}
        (self.out/'libraries.json').write_text(json.dumps(libraries,indent=2)+'\n')


if __name__ == '__main__':
    if len(sys.argv)!=3: raise SystemExit('usage: run.py PAYLOAD EXPECTED_PROVENANCE')
    if not os.environ.get('TMUX'): raise SystemExit('tmux is required')
    if os.uname().machine != 'riscv64': raise SystemExit('native K1 execution is required')
    # 文件描述符由外层脚本持锁，并传给本进程。
    os.fstat(9)
    lock=Path('/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock')
    if Path('/proc/self/fd/9').resolve() != lock: raise SystemExit('shared lock differs')
    fcntl.flock(9,fcntl.LOCK_EX | fcntl.LOCK_NB)
    with (Path(sys.argv[1]).resolve()/'run/execution-started').open('x') as marker:
        marker.write(str(os.getpid())+'\n')
    screen=Screen(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
    try:
        screen.run()
    except Exception:
        screen.summary['status']='fault'; screen.save()
        (screen.out/'failure.txt').write_text(traceback.format_exc())
        raise
