#!/usr/bin/env python3
"""Full-answer direct/checkpoint-MTP usefulness pilot on both required K1 models."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import threading
import time

HERE = Path(__file__).resolve().parent
def module(name):
    path = HERE / (name + '.py')
    if name == 'cached-document-chat' and not path.is_file():
        path = HERE.parent / 'serve' / 'cached-document-chat.py'
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
fast, bench, chat, quality, checks = [module(n) for n in ('k1-fast-test', 'bench-lifecycle',
    'cached-document-chat', 'document_quality_suite', 'mtp-quality-checks')]
ACCEPTANCE = re.compile(r'draft acceptance =\s*[0-9.]+\s*\(\s*(\d+) accepted /\s*(\d+) generated\), mean len =\s*([0-9.]+)')


def audit_result(result, payload, count, ctx=6144):
    usage = result.get('usage', {}); timing = result.get('timings', {})
    complete = result.get('finish_reason') == 'stop' and bool(result.get('answer', '').strip())
    return {'complete': complete, 'cold': usage.get('prompt_tokens_details', {}).get('cached_tokens') == 0,
            'prompt_count_valid': usage.get('prompt_tokens') == count and timing.get('prompt_n') == count,
            'slot_valid': result.get('server_slot') == 0,
            'output_count_valid': type(usage.get('completion_tokens')) is int and 0 < usage['completion_tokens'] <= payload['max_tokens']
                                  and usage['completion_tokens'] == timing.get('predicted_n'),
            'reasoning_disabled': not result.get('reasoning_text') and '<think>' not in result.get('answer', ''),
            'full_input_fits': count + payload['max_tokens'] <= ctx,
            'cache_disabled': payload.get('cache_prompt') is False}


def task_cases(document, base_cases):
    cases = []
    for case in base_cases:
        cases.append(dict(case, kind='facts', evidence=document, system=chat.SYSTEM_INSTRUCTION,
            user=f"Document:\n{document}\n\nQuestion: {case['question']}", max_tokens=512))
    for case_id, spec in checks.CODE_SPECS.items():
        cases.append({'case_id': case_id, 'kind': 'code', 'question': spec, 'evidence': spec,
            'required_facts': ['a correct implementation satisfying every stated boundary condition'],
            'system': 'Implement the requested Python functions. Give code directly without reasoning tags. '
                      'Use Python builtins only and no imports or classes.', 'user': spec, 'max_tokens':1536})
    evidence = ('测试资料：海松公司的仓库每天16:00停止接受当日发货订单。16:00之后收到的订单在下一个工作日发货。'
        '周六和周日不是工作日。标准配送从发货后的下一个工作日起需要三个工作日。'
        '加急配送需要一个工作日。标准运费20元，加急运费50元。单笔商品金额满200元免标准运费，'
        '但加急运费仍然收取50元。退款政策：未发货可免费取消；发货后可在收到商品起14天内退货，'
        '商品须未使用，消费者承担退回运费。仓库不提供周末发货服务。没有其他政策信息。')
    question = ('请只根据资料，用中文为客户写一份约450至600汉字的说明，分段覆盖截单时间、工作日、'
        '两种配送方式的时间和收费、免运费条件、取消和退货。举两个注明下单时间、订单金额和配送方式的例子，'
        '明确区分发货与送达；如无法确定具体日期，说明原因。不要编造额外政策。')
    cases.append({'case_id':'chinese_policy','kind':'facts','question':question,'evidence':evidence,
        'required_facts':['16:00 cutoff; later orders ship next business day','no weekend shipping',
            'standard three business days after shipment, costs 20','express one business day, costs 50',
            '200 threshold waives standard fee only','free cancellation before shipment',
            'unused returns within 14 days of receipt; customer pays return postage'],
        'fact_patterns':[r'16[:：]00',r'(?:周末|周六|周日)',r'(?:三|3).*工作日',r'20',r'(?:一|1).*工作日',r'50',r'200',r'14'],
        'system':'只根据提供的资料回答。直接给出中文答案，不要输出推理标签。',
        'user':f'资料：\n{evidence}\n\n问题：{question}','max_tokens':1536})
    return cases


def doc_blocks(readme):
    blocks = quality.evidence_cases(readme)
    blocks[0]['evidence'] += '\nReceipt A: 17 units.'
    blocks[1]['evidence'] = '[S2] Synthetic trace: job orion uses route maple.'
    blocks[2]['evidence'] = '[S3] Synthetic receipt B: 23 units.'
    blocks[3]['evidence'] = '[S4] Synthetic trace: route maple reaches cabinet cedar.'
    blocks[4]['evidence'] = '[S5] Synthetic receipt C: 38 units.'
    blocks[5]['evidence'] = '[S6] Synthetic trace: cabinet cedar has color cobalt.'
    return blocks, [dict(blocks[0],citations=['S1']),
        dict(blocks[5],case_id='trace',question='Follow job orion through its route and cabinet. What color is the cabinet? '
            'Answer briefly and cite [S2], [S4], [S6].',fact_patterns=[r'\bcobalt\b'],required_facts=['cobalt'],citations=['S2','S4','S6']),
        dict(blocks[4],case_id='aggregation',question='Add receipts A, B and C. Give the total and cite [S1], [S3], [S5].',
             fact_patterns=[r'\b78\b'],required_facts=['78'],citations=['S1','S3','S5'])]


class Run:
    def __init__(self, root):
        self.root = root; self.started = time.monotonic(); self.interrupted = False
        self.expected = json.loads((root/'expected-provenance.json').read_text())
        self.prior = json.loads((root/'validation-provenance.json').read_text())
        self.prior_run = json.loads((root/'validation-run.json').read_text())
        self.summary = {'status':'running','models':{},'planned_requests':24,
            'protocol':{'models':['2B','4B'],'mode':'checkpoint MTP vs direct','SPINE_SPEC_RS':'0',
                'routing':0,'threads':4,'batch':32,'ubatch':32,'weights':'Q4_0','kv':'F16',
                'context':6144,'document_budget':2048,'requests_per_task_arm':1,
                'order':{'2B':['direct','mtp'],'4B':['mtp','direct']},'case_order':'reverse in MTP arm',
                'per_request_budget_s':1800,'overall_budget_s':21600,'token_equality_required':False},
            'limitations':'One pair per task/model, six tasks; descriptive usefulness pilot, not general equivalence. RS path excluded. No default is changed.'}
    def phase(self,text):
        (self.root/'phase').write_text(text+'\n'); print(text,flush=True)
    def save(self):
        self.summary['elapsed_s']=time.monotonic()-self.started
        fast.write_json(self.root/'summary.json',self.summary)
    def env(self):
        env={k:v for k,v in os.environ.items() if not k.startswith(('SPINE_','SPACEMIT_'))}
        env.update(LD_LIBRARY_PATH=str(self.overlay)+':'+self.expected['runtime']['LD_LIBRARY_PATH'],
            SPINE_FA_WIDE_TILE='1',SPINE_FA_K1_LAYOUT='0',SPINE_K1_GEMM_ROUTE='0',SPINE_SPEC_RS='0')
        return env
    def prepare(self):
        self.phase('verify fixed runtime and model hashes')
        self.server=next(Path(p) for p in self.expected['artifacts_sha256'] if p.endswith('/llama-server'))
        self.source=self.server.parents[2]
        if subprocess.check_output(['git','-C',self.source,'rev-parse','--short=7','HEAD'],text=True).strip()!='a990751':
            raise ValueError('source revision changed')
        changed=set(subprocess.check_output(['git','-C',self.source,'diff','HEAD','--name-only'],text=True).splitlines())
        if changed!=set(self.expected['source_sha256']): raise ValueError('source changes differ')
        for path, digest in self.prior['verified_sha256'].items():
            if fast.digest(path)!=digest: raise ValueError('provenance changed: '+path)
        self.overlay=self.root/'lib'; self.overlay.mkdir()
        library=Path(self.prior_run['remote_root'])/'lib/libggml-cpu.so.0.16.0'
        if fast.digest(library)!=self.prior['candidate_library_sha256']: raise ValueError('CPU library changed')
        shutil.copyfile(library,self.overlay/library.name)
        for name in ('libggml-cpu.so','libggml-cpu.so.0'): (self.overlay/name).symlink_to(library.name)
        fast.write_json(self.root/'provenance.json',{'verified_sha256':self.prior['verified_sha256'],
            'candidate_library_sha256':fast.digest(self.overlay/library.name),
            'source_revision':'a990751','runtime':{k:v for k,v in self.env().items() if k.startswith('SPINE_') or k=='LD_LIBRARY_PATH'},
            'code_sha256':{p.name:fast.digest(p) for p in HERE.iterdir() if p.suffix in ('.py','.sh')}})
    def model(self, model):
        url='http://127.0.0.1:18085'; document=None; cases=None; pairs={}; counts={}
        with socket.socket() as probe:
            if probe.connect_ex(('127.0.0.1',18085))==0: raise ValueError('benchmark port occupied')
        readme=(self.source/'tools/server/README.md').read_text(); blocks,base_cases=doc_blocks(readme)
        configs={}
        for arm in (('direct','mtp') if model=='2B' else ('mtp','direct')):
            name=f'{model}-{arm}'; argv=[str(self.server),'-m',self.expected['models'][model]['path'],'--alias','local',
                '-t','4','-c','6144','--parallel','1','-b','32','-ub','32','-fa','on','-ctk','f16','-ctv','f16',
                '-ngl','0','--no-context-shift','--host','127.0.0.1','--port','18085']
            if arm=='mtp': argv+=['--spec-type','draft-mtp','--spec-draft-n-max','3']
            configs[arm]={'command':argv,'runtime':{k:v for k,v in self.env().items() if k.startswith('SPINE_') or k=='LD_LIBRARY_PATH'}}
            fast.write_json(self.root/(model+'-configs.json'),configs)
            logpath=self.root/(name+'.server.log')
            with logpath.open('w') as log:
                proc=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,env=self.env())
                stop=threading.Event(); samples=[]
                sampler=threading.Thread(target=bench.sample_rss,args=(proc.pid,stop,samples,1)); sampler.start()
                try:
                    bench.wait_healthy(proc,url,120)
                    if document is None:
                        document, doc_tokens=quality.make_document(url,chat,blocks,readme,2048,120)
                        (self.root/(model+'-document.txt')).write_text(document)
                        cases=task_cases(document,base_cases)
                        fast.write_json(self.root/(model+'-cases.json'),{'cases':cases,'blocks':blocks,'document_tokens':doc_tokens})
                    order=cases if arm=='direct' else list(reversed(cases))
                    for case in order:
                        self.phase(f'{model} {arm} {case["case_id"]}')
                        payload=chat.request_body([{'role':'system','content':case['system']},{'role':'user','content':case['user']}],'local',0,case['max_tokens'])
                        payload.update(cache_prompt=False,stream_options={'include_usage':True},verbose=True)
                        result={'case_id':case['case_id'],'arm':arm,'model':model,'request':payload,
                                'request_sha256':hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()}
                        sample_start=len(samples); log_start=logpath.stat().st_size
                        try:
                            count=chat.count_prompt_tokens(url,payload,120)
                            if count+case['max_tokens']>6144: raise ValueError('full input plus output does not fit')
                            if case['case_id'] in counts and counts[case['case_id']]!=count: raise ValueError('prompt count changed')
                            counts[case['case_id']]=count
                            signal.alarm(1800)
                            answer=chat.complete(url,payload,1800,display=False)
                            result.update(answer,prompt_tokens=count,audit=audit_result(answer,payload,count))
                            result['facts']=checks.fact_check(case,answer['answer'])
                            if case['kind']=='code': result['code_test']=checks.check_code(case['case_id'],answer['answer'])
                        except Exception as error:
                            if self.interrupted: raise
                            result['error']=type(error).__name__+': '+str(error)[:200]
                        finally: signal.alarm(0)
                        request_log=logpath.read_bytes()[log_start:].decode(errors='replace')
                        acceptance=ACCEPTANCE.findall(request_log)
                        result['draft_acceptance']=[{'accepted':int(a),'generated':int(g),'mean_len':float(n)} for a,g,n in acceptance]
                        result['rss_kib']=bench.stats([r[1] for r in samples[sample_start:]])
                        result['mem_available_kib']=bench.stats([r[2] for r in samples[sample_start:] if r[2] is not None])
                        pairs.setdefault(case['case_id'],{})[arm]=result
                        fast.write_json(self.root/(model+'-pairs.json'),pairs)
                        self.summary['models'][model]={'requests_completed':sum(len(v) for v in pairs.values()),'planned':12}
                        self.save()
                        if result.get('error'):
                            # A timed-out server may still be busy; stop this arm
                            # rather than send the next request into that state.
                            break
                finally:
                    stop.set(); sampler.join(timeout=3); proc.terminate()
                    try: proc.wait(timeout=10)
                    except subprocess.TimeoutExpired: proc.kill(); proc.wait()
            markers=re.findall(r'K1_GEMM_ROUTE mode=(\d) phase=(prefill|single) eligible=(\d) bypass=(\d) buffer_size=(\d+)',logpath.read_text())
            if {m[1] for m in markers}!={'prefill','single'} or any(m[0]!='0' or m[2:]!=('1','0','131072') for m in markers):
                raise ValueError('routing baseline activation differs')
            if arm=='mtp' and not ACCEPTANCE.search(logpath.read_text()): raise ValueError('no actual MTP draft activity recorded')
        self.summary['models'][model]={'requests_completed':sum(len(v) for v in pairs.values()),'planned':12,
            'status':'complete' if len(pairs)==6 and all(set(p)=={'direct','mtp'} for p in pairs.values()) else 'incomplete'}
        self.save()
    def run(self):
        def interrupted(signum,frame):
            self.interrupted=True; raise TimeoutError('overall board budget expired')
        def request_timeout(signum,frame): raise TimeoutError('request budget expired')
        signal.signal(signal.SIGTERM,interrupted); signal.signal(signal.SIGALRM,request_timeout)
        try:
            self.prepare(); self.save()
            for model in ('2B','4B'): self.model(model)
            self.summary['status']='generation completed; collection and judging pending'; self.save(); self.phase(self.summary['status'])
        except BaseException as error:
            self.summary.update(status='failed',reason=type(error).__name__+': '+str(error)[:200]); self.save(); self.phase('failed'); raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('root',type=Path)
    Run(parser.parse_args().root.resolve()).run()
