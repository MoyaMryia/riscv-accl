#!/usr/bin/env python3
"""Verify a clean release build with real graph cases and complete code answers."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent


def module(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    value=importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value


fast=module('k1-fast-test'); life=module('bench-lifecycle'); route=module('k1-gemm-routing')
chat=module('cached-document-chat'); checks=module('mtp-quality-checks')


def audit(result, payload, count):
    usage=result.get('usage',{}); timings=result.get('timings',{})
    return dict(natural_stop=result.get('finish_reason')=='stop',
        cold=usage.get('prompt_tokens_details',{}).get('cached_tokens')==0,
        full_input=usage.get('prompt_tokens')==timings.get('prompt_n')==count,
        complete_output=type(usage.get('completion_tokens')) is int and 0<usage['completion_tokens']<payload['max_tokens']
                        and usage['completion_tokens']==timings.get('predicted_n'),
        correct_slot=result.get('server_slot')==0,
        no_draft=timings.get('draft_n',0)==0,
        no_thinking=not result.get('reasoning_text') and '<think>' not in result.get('answer',''))


def run(root):
    started=time.monotonic(); summary=dict(status='running',requests_completed=0,requests_planned=4,stages={})
    def phase(name): (root/'phase').write_text(name+'\n'); print(name,flush=True)
    def save(): summary['elapsed_s']=time.monotonic()-started; fast.write_json(root/'summary.json',summary)
    def command(args,log,timeout=600,env=None,cwd=None):
        with (root/log).open('w') as out:
            subprocess.run(list(map(str,args)),stdout=out,stderr=subprocess.STDOUT,check=True,timeout=timeout,env=env,cwd=cwd)
    try:
        expected=json.loads((root/'expected-provenance.json').read_text())
        old_source=Path(next(k for k in expected['artifacts_sha256'] if k.endswith('/llama-server'))).parents[2]
        source=root/'source'; build=root/'build'
        phase('clone clean pinned source')
        command(['git','clone','--shared','--no-checkout',old_source,source],'clone.log',180)
        command(['git','-C',source,'checkout','--detach','a990751d55a4c54acf2bb77d44282c2093652359'],'checkout.log',60)
        command([sys.executable,root/'apply-release.py',source],'apply.log',60)
        phase('fresh release configure and build'); save()
        command(['bash',root/'build.sh',source,build],'build.log',14460)
        compiler=os.environ.get('K1_CXX',str(Path.home()/'Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14'))
        spert=os.environ.get('K1_SPERT_DIR',str(Path.home()/'Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2'))
        tcm=os.environ.get('K1_TCM_DIR',str(Path.home()/'Projects/llm-bench/.toolchain/spine-tcm'))
        runtime=tcm+':'+spert+'/lib:'+str(build/'bin')
        base={k:v for k,v in os.environ.items() if not k.startswith('SPINE_')}
        base.update(LD_LIBRARY_PATH=runtime,SPINE_FA_WIDE_TILE='1',SPINE_FA_K1_LAYOUT='0')
        phase('native release graph identity')
        command([compiler,'-O3','-std=c++17','-march=rv64gcv_zfh_zvfh_zicbop_zihintpause_zba','-mabi=lp64d',
            '-I'+str(source/'ggml/include'),'-I'+str(source/'ggml/src'),'-I'+str(source/'ggml/src/ggml-cpu/spacemit'),
            HERE/'test-k1-gemm-routing.cpp','-L'+str(build/'bin'),'-lggml-cpu','-lggml-base','-pthread',
            '-o',root/'test-release-graph'],'native-build.log',180,base)
        hashes={}
        for mode in (0,3):
            env=dict(base,SPINE_K1_GEMM_ROUTE=str(mode)); label='native-'+str(mode)
            command([root/'test-release-graph','--dump',root/(label+'.data')],label+'.log',240,env)
            text=(root/(label+'.log')).read_text(); route.check_activation(text,mode,('prefill','single'))
            if 'PASS: 104 production graph cases;' not in text: raise ValueError('native cases incomplete')
            hashes[str(mode)]=fast.digest(root/(label+'.data'))
        if len(set(hashes.values()))!=1 or next(iter(hashes.values()))!='e31997719879fb9a858f9e970af7e11ceb68124657d41c53bd3b3f82c4dbd4dc':
            raise ValueError('fresh build graph outputs differ from measured baseline')
        summary['stages']['native']=dict(cases_per_arm=104,bitwise_equal=True,sha256=hashes); save()
        phase('complete cold Unicode answers on both models')
        url='http://127.0.0.1:18092'
        with socket.socket() as probe:
            if probe.connect_ex(('127.0.0.1',18092))==0: raise ValueError('release test port occupied')
        release_manifest=json.loads((root/'manifest.json').read_text())
        provenance=dict(source_revision=release_manifest['source_commit'],source_sha256={n:fast.digest(source/n) for n in release_manifest['patched_source_sha256']},
            models=expected['models'],server_sha256=fast.digest(build/'bin/llama-server'),library_sha256=fast.digest(build/'bin/libggml-cpu.so.0.16.0'),
            cmake_cache_sha256=fast.digest(build/'CMakeCache.txt'),compile_commands_sha256=fast.digest(build/'compile_commands.json'),runtime=runtime,
            limitation='Fresh clean build and four natural-answer smoke requests. Descriptive timings, not a new statistically qualified speedup.')
        fast.write_json(root/'provenance.json',provenance)
        pairs={}
        for model in ('2B','4B'):
            info=expected['models'][model]
            if fast.digest(info['path'])!=info['sha256'] or release_manifest['models'][model]['sha256']!=info['sha256']:
                raise ValueError('model differs from release pin')
            prior=json.loads((root/(model+'-frozen-pairs.json')).read_text())['unicode_runs']['control']
            payload=prior['request']; count=None; answers={}
            for mode in ((0,3) if model=='2B' else (3,0)):
                label=f'{model}-route{mode}'; phase(label+' complete answer'); env=dict(base,SPINE_K1_GEMM_ROUTE=str(mode))
                argv=[str(build/'bin/llama-server'),'-m',info['path'],'--alias','local','-t','4','-c','6144','--parallel','1',
                    '-b','32','-ub','32','-fa','on','-ctk','f16','-ctv','f16','-ngl','0','--no-context-shift',
                    '--host','127.0.0.1','--port','18092']
                with (root/(label+'.server.log')).open('w') as log:
                    proc=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,env=env)
                    try:
                        life.wait_healthy(proc,url,180)
                        actual=chat.count_prompt_tokens(url,payload,120)
                        if actual!=prior['prompt_tokens'] or (count is not None and count!=actual): raise ValueError('frozen complete prompt count differs')
                        count=actual; signal.alarm(1800)
                        answer=chat.complete(url,payload,1800,display=False)
                        answer.update(request=payload,prompt_tokens=count,audit=audit(answer,payload,count),code_test=checks.check_code('unicode_runs',answer['answer']),
                            answer_sha256=hashlib.sha256(answer['answer'].encode()).hexdigest(),server_command=argv)
                        answers[str(mode)]=answer
                        fast.write_json(root/(label+'.answer.json'),answer)
                        (root/(label+'.answer.md')).write_text(answer['answer']+'\n')
                        if not all(answer['audit'].values()) or not answer['code_test']['pass'] or answer['code_test']['checks']!=106:
                            raise ValueError('complete useful-code smoke gate failed: '+label)
                        summary['requests_completed']+=1; save()
                    finally:
                        signal.alarm(0); proc.terminate()
                        try: proc.wait(timeout=10)
                        except subprocess.TimeoutExpired: proc.kill(); proc.wait()
                text=(root/(label+'.server.log')).read_text(); route.check_activation(text,mode,('prefill','single'))
                if 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled' not in text: raise ValueError('RVV activation missing')
            if answers['0']['answer']!=answers['3']['answer']: raise ValueError('matched natural answer differs')
            pairs[model]=dict(bitwise_text_equal=True,natural_answers=2,held_out_checks_per_answer=106,
                same_as_prior_control=answers['0']['answer']==prior['answer'],
                baseline=answers['0'],optimized=answers['3'])
            fast.write_json(root/'complete-answer-pairs.json',pairs)
            summary['stages'][model]=dict(text_equal=True,complete=True,checks_per_answer=106,
                output_tokens={q:r['usage']['completion_tokens'] for q,r in answers.items()},
                timings={q:r['timings'] for q,r in answers.items()})
            save()
        summary.update(status='release verified',reason='Clean pinned checkout, full fresh build, exact production graph dumps and four naturally complete useful-code responses pass. No new performance significance claim.')
        save(); phase('release verified')
    except BaseException as error:
        summary.update(status='failed',reason=f'{type(error).__name__}: {error}'); save(); phase('failed'); raise


if __name__=='__main__':
    def interrupted(signum,frame): raise TimeoutError('release test timeout')
    signal.signal(signal.SIGTERM,interrupted); run(Path(sys.argv[1]).resolve())
