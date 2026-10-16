#!/usr/bin/env python3
"""验证统一构建、固定配置、模型状态和匹配请求。"""
import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import socket
import statistics
import subprocess
import sys
import threading
import time
import traceback

import package

HERE=Path(__file__).resolve().parent

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result

launch=module('launch',HERE/'run.py')
life=module('life',HERE/'tests/lifecycle.py')
chat=module('chat',HERE/'tests/chat.py')
quality=module('quality',HERE/'tests/quality.py')


def save(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def require(good,message):
    if not good: raise ValueError(message)


class Run:
    def __init__(self,args):
        self.args=args; self.root=args.output.resolve(); self.build=args.build.resolve()
        self.reference=args.reference.resolve(); self.start=time.monotonic()
        require(not self.root.exists(),'output directory exists')
        self.root.mkdir(parents=True)
        self.summary={'status':'running','stages':{},'requests':[]}
        self.env=launch.environment('optimized',self.build/'bin',args.spert,args.tcm)
        self.models={n:args.models/package.manifest()['models'][n]['filename'] for n in ('2B','4B')}
        self.reference_env=dict(self.env,LD_LIBRARY_PATH=':'.join(map(str,(self.reference,args.tcm,args.spert/'lib'))))

    def phase(self,name):
        (self.root/'phase').write_text(name+'\n'); print(name,flush=True)
        self.summary['elapsed_s']=time.monotonic()-self.start
        save(self.root/'summary.json',self.summary)

    def command(self,argv,label,env=None,timeout=600):
        argv=list(map(str,argv)); selected=env or self.env
        save(self.root/(label+'.command.json'),{'argv':argv,'cwd':str(Path.cwd()),'environment':{k:v for k,v in selected.items() if k.startswith('SPINE_') or k=='LD_LIBRARY_PATH'}})
        with (self.root/(label+'.log')).open('w') as stream:
            proc=subprocess.run(argv,stdout=stream,stderr=subprocess.STDOUT,env=selected,timeout=timeout)
        (self.root/(label+'.exit-status')).write_text(str(proc.returncode)+'\n')
        proc.check_returncode()
        return (self.root/(label+'.log')).read_text()

    def identity(self):
        self.phase('identity')
        require(os.environ.get('TMUX') and os.environ.get('K1_PACKAGE_LOCK_FD')=='9','use with-lock.sh in tmux')
        os.fstat(9)
        package.verify(self.args.source.resolve()); receipt=launch.verify_binaries(self.build)
        models={n:{'path':str(p.resolve()),'sha256':launch.verify_model(p)[1]} for n,p in self.models.items()}
        self.original={str(p):package.sha(p) for p in self.reference.iterdir() if p.is_file()}
        hardware={'uname':subprocess.check_output(['uname','-a'],text=True),'cpuinfo':Path('/proc/cpuinfo').read_text(),
                  'meminfo':Path('/proc/meminfo').read_text(),'uid':os.getuid(),
                  'cpufreq':{str(p):p.read_text() for p in Path('/sys/devices/system/cpu').glob('cpu[0-9]*/cpufreq/scaling_cur_freq')},
                  'thermal':{str(p):p.read_text() for p in Path('/sys/class/thermal').glob('thermal_zone*/temp')}}
        save(self.root/'identity.json',{'hardware':hardware,'models':models,'build':receipt,'reference_files':self.original,
            'code':{str(p.relative_to(HERE)):package.sha(p) for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts},
            'session':os.environ['TMUX'],'cwd':str(Path.cwd()),'lock':str(Path.home()/'Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock')})
        with socket.socket() as sock: require(sock.connect_ex(('127.0.0.1',18413))!=0,'test port occupied')
        require(subprocess.run(['pgrep','-x','llama-server'],stdout=subprocess.DEVNULL).returncode==1,'another server is active')
        self.summary['stages']['identity']='pass'

    def native(self):
        self.phase('native numeric and fallback')
        hashes={}
        for arm in (0,3):
            label='route-'+str(arm); env=dict(self.env,SPINE_K1_GEMM_ROUTE=str(arm))
            log=self.command([self.build/'bin/test-route','--dump',self.root/(label+'.data')],label,env)
            require('PASS: 104' in log,'route count differs')
            hashes[label]=package.sha(self.root/(label+'.data'))
            require(hashes[label]=='e31997719879fb9a858f9e970af7e11ceb68124657d41c53bd3b3f82c4dbd4dc','route dump differs from preserved release')
        values={}
        for name,env in [('reference',self.reference_env),('unified',dict(self.env,SPINE_K1_TRACE='1',SPINE_K1_GDN_REVISION='1'))]:
            for probe,args,count in [('attention',[],95),('ssm',['0'],432),('gdn',[],158)]:
                label=f'{name}-{probe}'; path=self.root/(label+'.data')
                log=self.command([self.build/('bin/test-'+probe),*args,'--dump',path],label,env)
                require('PASS: '+str(count) in log,'native case count differs: '+label)
                values[label]=package.sha(path)
                if name=='unified':
                    require(values[label]==values['reference-'+probe],'reference dump differs: '+probe)
                    if probe=='attention':
                        require('K1_FA path=B1' in log and 'reference-underfilled-groups' in log,'attention paths absent')
                    if probe=='gdn':
                        require('SPINE_GDN_PREFILL_R2: retained two state segments' in log,'GDN revision absent')
                        require(set(re.findall(r'K1_GDN_R2 worker=(\d+) workers=4 state=128',log))==set('0123'),'GDN workers differ')
        label='unified-ssm-c1'; path=self.root/(label+'.data')
        log=self.command([self.build/'bin/test-ssm','3','--dump',path],label,dict(self.env,SPINE_K1_TRACE='1'))
        require('PASS: 432' in log,'C1 case count differs')
        values[label]=package.sha(path)
        require(values[label]==values['reference-ssm'],'C1 output differs')
        label='unified-gdn-legacy'; path=self.root/(label+'.data')
        log=self.command([self.build/'bin/test-gdn','--dump',path],label,dict(self.env,SPINE_K1_GDN_REVISION='0'))
        require('PASS: 158' in log,'legacy GDN count differs')
        values[label]=package.sha(path)
        require(values[label]==values['reference-gdn'],'legacy GDN output differs')
        self.summary['stages']['native']={'status':'pass','route_cases_per_arm':104,'attention':95,'ssm_per_mode':432,'gdn_per_mode':158,'hashes':{**hashes,**values}}

    def state(self):
        self.phase('both models short state and reset')
        records={}
        for model,path in self.models.items():
            expected=None
            for arm in (-1,0,1,2,4,6,7):
                label=f'state-{model}-{arm}'; dump=self.root/(label+'.data')
                env=self.reference_env if arm<0 else dict(self.env,SPINE_K1_TRACE='1')
                self.phase(label)
                log=self.command([self.build/'bin/test-state',path,max(arm,0),dump,'short'],label,env,1200)
                rows=[json.loads(line) for line in log.splitlines() if line.startswith('{')]
                require(len(rows)==16 and 'PASS: 16 full-vocabulary records' in log,'state coverage differs')
                require(all(r['bitwise_equal'] and r['max_abs']==0 for r in rows),'state values differ')
                keys=[(r['rs'],r['reset'],r['prefix']) for r in rows]
                require(keys==[(rs,reset,prefix) for rs in (0,3) for reset in (0,1) for prefix in (32,33,64,96)],'state sequence differs')
                if arm>=0:
                    require('K1_GEMM_ROUTE mode=3' in log,'state route evidence absent')
                    require('SPINE_FA_WIDE_TILE: RVV tiled attention enabled' in log,'state attention evidence absent')
                    spans=re.findall(r'COMBO_STATE begin arm=(\d+)[^\n]*\n(.*?)COMBO_STATE end arm=\1',log,re.S)
                    require(len(spans)==16*(2 if arm else 1),'state span count differs')
                    for active,span in spans:
                        if active=='0':
                            require('K1_GDN_R2 worker=' not in span and 'SPINE_GDN_PREFILL_R2:' not in span and 'K1_FA path=B1 ' not in span,'disabled model path is active')
                    selected='\n'.join(span for active,span in spans if int(active)==arm)
                    markers=re.findall(r'K1_SSM_CONV mode=(\d) layout=(\w+) rs=(\d+) cpu_only=(\d+) tokens=(\d+) requested=(\d+)',selected)
                    require(bool(markers),'model convolution markers absent')
                    requested=3 if arm & 2 else 0
                    for mode,layout,rs,cpu,tokens,req in markers:
                        actual=2 if requested==3 and int(tokens)>=32 and rs=='0' else 0
                        require((int(mode),layout,cpu,int(req))==(actual,'channels' if actual else 'time','1',requested),'model convolution dispatch differs')
                    if arm & 2:
                        seen={(int(m),int(rs),int(t)) for m,lay,rs,cpu,t,req in markers}
                        require({(2,0,32),(0,0,1),(0,0,31),(0,3,32)}<=seen,'model C1 fallback coverage differs')
                    require(('SPINE_GDN_PREFILL_R2:' in selected)==bool(arm & 4),'model GDN revision activation differs')
                    if arm & 4:
                        require(set(re.findall(r'K1_GDN_R2 worker=(\d+) workers=4 state=128',selected))==set('0123'),'model GDN workers differ')
                    if not arm & 1: require('K1_FA path=B1 ' not in selected,'disabled model attention is active')
                digest=package.sha(dump)
                if expected is None: expected=digest
                require(digest==expected,'unified state differs from original release')
                records[label]={'sha256':digest,'rows':rows}
                save(self.root/'state.json',records)
        self.summary['stages']['state']={'status':'pass','records':sum(len(r['rows']) for r in records.values()),'max_prefix':96,'long_state_acceptance':'pending'}

    @contextlib.contextmanager
    def server(self,model,profile,label,build=None):
        build=build or self.build
        argv=[sys.executable,HERE/'run.py','--build',build,'--model',self.models[model],'--profile',profile,
              '--spert',self.args.spert,'--tcm',self.args.tcm,'--port','18413','--receipt',self.root/(label+'.launch.json')]
        # 故意加入污染值，以验证实际启动器清除继承设置。
        polluted=dict(os.environ,SPINE_K1_FA_GQA='1',SPINE_K1_SSM_CONV='3',SPINE_GDN_PREFILL='1',SPINE_K1_TRACE='1',SPACEMIT_CORE_ARCH='invalid-inherited-value')
        if profile=='reference':
            argv=[self.reference/'llama-server','-m',self.models[model],'--alias','local','-t','4','-tb','4',
                  '-c','6144','--parallel','1','-b','32','-ub','32','-fa','on','-ctk','f16','-ctv','f16',
                  '-ngl','0','--no-context-shift','--host','127.0.0.1','--port','18413']
            polluted=self.reference_env
            save(self.root/(label+'.launch.json'),{'profile':'preserved-release-route3','argv':list(map(str,argv)),
                'environment':{k:v for k,v in polluted.items() if k.startswith('SPINE_') or k=='LD_LIBRARY_PATH'}})
        with (self.root/(label+'.server.log')).open('w') as stream:
            proc=subprocess.Popen(list(map(str,argv)),stdout=stream,stderr=subprocess.STDOUT,env=polluted,pass_fds=(9,))
            try:
                life.wait_healthy(proc,'http://127.0.0.1:18413',240)
                yield proc,'http://127.0.0.1:18413'
            finally:
                proc.terminate()
                try: proc.wait(timeout=10)
                except subprocess.TimeoutExpired: proc.kill(); proc.wait()
                (self.root/(label+'.server-exit-status')).write_text(str(proc.returncode)+'\n')

    def answers(self):
        results={}
        for model in self.models:
            prior=json.loads((HERE/f'tests/{model}-answer.json').read_text())
            matched=[]
            for profile in ('baseline','optimized'):
                label=f'answer-{model}-{profile}'; self.phase(label)
                with self.server(model,profile,label) as (proc,url):
                    payload=prior['request']
                    count=chat.count_prompt_tokens(url,payload,120)
                    require(count==prior['prompt_tokens'],'answer prompt differs')
                    answer=chat.complete(url,payload,1800,display=False)
                    answer['code_test']=quality.check_code('unicode_runs',answer['answer'])
                    answer['same_as_preserved']=answer['answer']==prior['answer']
                    save(self.root/(label+'.json'),answer)
                    (self.root/(label+'.md')).write_text(answer['answer']+'\n')
                    require(answer.get('finish_reason')=='stop','answer has no natural stop')
                    require(answer['usage']['prompt_tokens_details']['cached_tokens']==0,'answer reuses prompt')
                    require(answer['usage']['prompt_tokens']==count==answer['timings']['prompt_n'],'answer input differs')
                    require(answer['usage']['completion_tokens']==answer['timings']['predicted_n']<payload['max_tokens'],'answer output differs')
                    require(answer['code_test']['pass'] and answer['code_test']['checks']==106,'answer code check failed')
                    require(not answer.get('reasoning_text'),'unexpected reasoning output')
                    matched.append(answer['answer'])
                    results[label]={'output_tokens':answer['usage']['completion_tokens'],'checks':106,'same_as_preserved':answer['same_as_preserved'],'timings':answer['timings']}
            require(matched[0]==matched[1],'baseline and optimized answers differ')
        self.summary['stages']['answers']={'status':'pass','results':results,'general_quality':'pending'}

    def performance(self):
        rows=[]; comparisons=[]
        for tokens in (512,2048):
            for model in self.models:
                identity=None; grouped={'baseline':[],'optimized':[],'reference':[]}
                for index,profile in enumerate(('reference','baseline','optimized','optimized','baseline','reference')):
                    label=f'cold-{model}-p{tokens}-{index}-{profile}'; self.phase(label)
                    with self.server(model,profile,label) as (proc,url):
                        prompt=life.make_prompt(url,tokens)
                        samples=[]; stop=threading.Event()
                        def sample():
                            while not stop.wait(.2):
                                try:
                                    samples.append({'at':time.monotonic(),'rss_kib':life.vmrss_kib(proc.pid),
                                        'threads':{p.name:(p/'stat').read_text() for p in (Path('/proc')/str(proc.pid)/'task').iterdir()}})
                                except OSError: pass
                        thread=threading.Thread(target=sample);thread.start()
                        try: result=life.complete(url,prompt,65,900,0,True,False,True,True,True)
                        finally: stop.set();thread.join()
                        life.verify_cold(result,tokens)
                        require(result['tokens_predicted']==65 and result['timings']['predicted_n']==65 and not result['error'],'cold completion differs')
                        require(len(result['token_ids'])==65,'token record differs')
                        pair=(prompt,result['token_ids'],result['sha256'])
                        if identity is None: identity=pair
                        require(pair==identity,'matched input or output differs')
                        result['rss_kib']=life.stats([s['rss_kib'] for s in samples if s['rss_kib'] is not None])
                        result.update(model=model,profile=profile,input_tokens=tokens,output_tokens=65,context=6144,threads=4,batch=32,ubatch=32,
                                      prompt=prompt,prompt_sha256=hashlib.sha256(json.dumps(prompt,separators=(',',':')).encode()).hexdigest())
                        save(self.root/(label+'.json'),result);save(self.root/(label+'.threads.json'),samples)
                        rows.append(result);grouped[profile].append(result)
                        self.summary['requests'].append(label)
                for control in ('baseline','reference'):
                    metrics={}
                    for metric,key in [('prefill','prompt_ms'),('decode','predicted_ms'),('ttft',None)]:
                        values={profile:[r['timings'][key] if key else r['ttft_ms'] for r in grouped[profile]] for profile in (control,'optimized')}
                        a=statistics.mean(values[control]); b=statistics.mean(values['optimized'])
                        spread=(max(values[control])-min(values[control]))/a*100
                        change=(b/a-1)*100
                        metrics[metric]={'values_ms':values,'baseline_mean_ms':a,'optimized_mean_ms':b,
                                         'time_reduction_percent':-change,'baseline_range_percent':spread,'clear_regression':change>max(3,spread)}
                    comparisons.append({'model':model,'input_tokens':tokens,'output_tokens':65,'control':control,'candidate':'optimized','metrics':metrics})
                save(self.root/'performance.json',{'requests':len(rows),'comparisons':comparisons})
        self.summary['stages']['performance']={'status':'regression' if any(m['clear_regression'] for c in comparisons for m in c['metrics'].values()) else 'pass',
            'requests':len(rows),'samples_per_arm_shape':2,'comparisons':comparisons,'scope':'limited matched observations'}

    def relocate(self):
        self.phase('relocated binaries and both models')
        relocated=self.root/'relocated-build'; relocated.mkdir()
        shutil.copytree(self.build/'bin',relocated/'bin',symlinks=True)
        shutil.copy2(self.build/'build-receipt.json',relocated/'build-receipt.json')
        env=launch.environment('optimized',relocated/'bin',self.args.spert,self.args.tcm)
        mapping={}
        for binary in (relocated/'bin').iterdir():
            if binary.is_symlink() or not binary.is_file(): continue
            text=self.command(['ldd',binary],'ldd-'+binary.name,env)
            require('not found' not in text,'missing shared library')
            for path in re.findall(r'=> (/\S+)',text):
                p=Path(path).resolve()
                allowed=(relocated.resolve(),self.args.spert.resolve(),self.args.tcm.resolve(),Path('/usr'),Path('/lib'))
                require(any(p==a or a in p.parents for a in allowed),'private build library: '+path)
            mapping[binary.name]=text
        for model in self.models:
            label='relocated-'+model
            with self.server(model,'optimized',label,relocated) as (proc,url):
                response=life.complete(url,life.make_prompt(url,32),8,120,0,True,False,True,True,True)
                life.verify_cold(response,32)
                require(response['tokens_predicted']==8,'relocated inference failed')
                save(self.root/(label+'.json'),response)
        self.summary['stages']['relocation']={'status':'pass','models':['2B','4B'],'library_paths':'package, explicit runtimes, system'}

    def run(self):
        try:
            self.identity();self.native();self.state();self.answers();self.performance();self.relocate()
            launch.verify_binaries(self.build);package.verify(self.args.source.resolve())
            require(self.original=={n:package.sha(n) for n in self.original},'preserved release changed')
            self.summary['status']='verified-limited' if self.summary['stages']['performance']['status']=='pass' else 'performance-regression'
        except BaseException as exc:
            self.summary.update(status='failed',error=f'{type(exc).__name__}: {exc}');traceback.print_exc();raise
        finally:
            self.phase(self.summary['status'])
            hashes={str(p.relative_to(self.root)):package.sha(p) for p in self.root.rglob('*') if p.is_file() and 'relocated-build' not in p.parts and p.name!='receipts.json'}
            save(self.root/'receipts.json',hashes)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--reference',type=Path,required=True,help='Preserved release bin directory')
    parser.add_argument('--models',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--spert',type=Path,default=Path.home()/'Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2')
    parser.add_argument('--tcm',type=Path,default=Path.home()/'Projects/llm-bench/.toolchain/spine-tcm')
    Run(parser.parse_args()).run()
