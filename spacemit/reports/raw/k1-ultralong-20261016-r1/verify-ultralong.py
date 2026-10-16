"""独立核对超长补测记录，并计算每个形状的结果。"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

PLAN = [('2B',16384,0,'final'),('2B',16384,0,'baseline'),
        ('4B',16384,0,'baseline'),('4B',16384,0,'final'),
        ('2B',32768,0,'baseline'),('2B',32768,0,'final'),
        ('4B',32768,0,'final'),('4B',32768,0,'baseline'),
        ('4B',16384,1,'final'),('4B',16384,1,'baseline'),
        ('2B',16384,1,'baseline'),('2B',16384,1,'final')]
MODELS = {'2B':'56f0ddd90dfa0e2456af6cb4718ece419678d21a75d65e27353319b5e431a2fa',
          '4B':'0adf6cce5df53921606033c39a13fae2054543b78af0e7ff98860e86f078ac0f'}


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        while chunk:=stream.read(8*1024*1024): h.update(chunk)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def read(path): return json.loads(path.read_text())


def require(condition, message):
    if not condition: raise ValueError(message)


def receipts(root, values):
    for name, expected in values.items():
        p=(root/name).resolve()
        require(p.is_relative_to(root.resolve()) and p.is_file(), 'receipt path differs: '+name)
        require(sha(p)==expected, 'receipt hash differs: '+name)
    return len(values)


def verify(board, task, original):
    results=board/'results'
    require((board/'exit-status').read_text().strip()=='0','controller exit differs')
    summary=read(results/'summary.json')
    labels=[f'{m}-p{n}-r{r}-{k}' for m,n,r,k in PLAN]
    require(summary['status']=='pass' and summary['completed']==labels and summary['failed']==[], 'plan completion differs')
    root_receipts=read(results/'receipts.json')
    count=receipts(results,root_receipts)
    require(set(root_receipts)=={str(p.relative_to(results)) for p in results.rglob('*') if p.is_file() and p!=results/'receipts.json'},'root receipt coverage differs')
    frozen=read(task/'tool-receipt.json')
    require(sha(board/'PROTOCOL.md')==frozen['protocol_sha256']==sha(task/'PROTOCOL.md'),'protocol differs')
    receipts(board,frozen['files'])
    pins=read(results/'identity.json')['inputs']
    require(pins['plan']==[list(x) for x in PLAN],'identity plan differs')
    require(pins['tools']=={Path(n).name:h for n,h in frozen['files'].items()},'frozen tools differ')
    require(pins['protocol_sha256']==frozen['protocol_sha256'],'identity protocol differs')
    for arm,name in (('final','final-r3/build'),('baseline','baseline-load-build')):
        p=original/name/'build-receipt.json'; recorded=read(p)
        require(sha(p)==pins['builds'][arm]['receipt_sha256'],'original receipt differs: '+arm)
        require(recorded['binaries']==pins['builds'][arm]['binaries'],'original binaries differ: '+arm)
    require(pins['builds']['final']['binaries']['llama-server']=='f254f174919c0a97ef34366f116705f6d22574cab4c2bfc39928c0d315b5bfbd','final server differs')
    require({m:pins['models'][m]['sha256'] for m in MODELS}==MODELS,'models differ')
    prompts=read(results/'prompts.json')
    rows=[]; samples_total=0
    for (model,length,repeat,arm),label in zip(PLAN,labels):
        folder=results/label
        local_receipts=read(folder/'receipts.json')
        count+=receipts(folder,local_receipts)
        require(set(local_receipts)=={p.name for p in folder.iterdir() if p.is_file() and p.name!='receipts.json'},'job receipt coverage differs')
        job=read(folder/'job.json'); result=read(folder/'result.json'); payload=read(folder/'request.json')
        context=20480 if length==16384 else 36864
        timeout=28800 if length==16384 else 86400
        expected=dict(model=model,input_tokens=length,output_tokens=65,repeat=repeat,kind=arm,context=context,timeout_s=timeout,identity=digest(pins))
        require(job==expected,'job differs: '+label)
        require(all(result[k]==v for k,v in job.items()),'result identity differs')
        prompt=prompts[model]['tokens'][:length]; forced=prompts[model]['forced_token']
        require(len(prompts[model]['tokens'])==32768 and forced==264,'prompt source differs')
        require(payload==dict(prompt=prompt,n_predict=65,temperature=0,seed=42,cache_prompt=False,stream=True,ignore_eos=True,return_tokens=True,id_slot=0,logit_bias=[[forced,1000.0]]),'request differs')
        require(result['prompt_sha256']==digest(prompt),'prompt hash differs')
        require(result['status']=='pass' and result['error'] is None and result['stop_type']=='limit','completion differs')
        require(result['token_ids']==[forced]*65 and result['tokens_predicted']==65,'output history differs')
        require(result['text']==' a'*65 and result['text_sha256']==hashlib.sha256(result['text'].encode()).hexdigest(),'output text differs')
        timing=result['timings']
        require(timing['cache_n']==0 and timing['prompt_n']==length and timing['predicted_n']==65,'actual computation differs')
        for key in ('prompt_ms','predicted_ms','prompt_per_second','predicted_per_second'):
            require(math.isfinite(timing[key]) and timing[key]>0,'timing is invalid')
        require(math.isclose(length*1000/timing['prompt_ms'],timing['prompt_per_second'],rel_tol=1e-9),'prefill rate differs')
        require(math.isclose(65000/timing['predicted_ms'],timing['predicted_per_second'],rel_tol=1e-9),'decode rate differs')
        require(0<result['ttft_ms']<=result['wall_s']*1000 and result['wall_s']<=timeout,'wall time differs')
        require(timing['prompt_ms']<=result['ttft_ms']+1000 and result['decode_ms']==timing['predicted_ms'],'client or decode timing differs')
        props=read(folder/'properties.json')
        require(props['total_slots']==1 and props['default_generation_settings']['n_ctx']==context,'actual capacity differs')
        require(props['default_generation_settings']['params']['speculative.types']=='none','draft decode differs')
        launch=read(folder/'launch.json'); argv=launch['argv']
        expected_argv=[pins['builds'][arm]['path']+'/bin/llama-server','-m',pins['models'][model]['path'],'--alias','local','--host','127.0.0.1','--port','18443','-c',str(context)]
        if arm=='baseline': expected_argv+=['-t','4','-tb','4','--parallel','1','-b','32','-ub','32','-fa','on','-ctk','f16','-ctv','f16','-ngl','0','--no-context-shift']
        require(argv==expected_argv and launch['optimization_environment']=='absent' and launch['capacity_override']==context,'launch differs')
        log=(folder/'server.log').read_text()
        require(f'n_ctx_slot = {context}' in log and 'n_slots = 1' in log,'capacity log differs')
        if arm=='final':
            expected_defaults=dict(threads='4',batch_threads='4',batch='32',ubatch='32',context=str(context),slots='1',flash='1',gpu='0',key='f16',value='f16',mask='3')
            lines=re.findall(r'^K1_EFFECTIVE_DEFAULTS (.+)$',log,re.M)
            require(len(lines)==1 and dict(x.split('=',1) for x in lines[0].split())==expected_defaults,'effective defaults differ')
            require(read(folder/'effective-defaults.json')==expected_defaults,'default receipt differs')
        for pattern, key, n in ((r'prompt eval time =\s*([\d.]+) ms /\s*(\d+) tokens','prompt_ms',length),
                                (r'\|\s+eval time =\s*([\d.]+) ms /\s*(\d+) tokens','predicted_ms',65)):
            found=re.findall(pattern,log)
            require(len(found)==1 and int(found[0][1])==n and abs(float(found[0][0])-timing[key])<0.02,'server timing log differs')
        samples=read(folder/'memory-samples.json'); samples_total+=len(samples)
        require(len(samples)>1 and all(a['elapsed_s']<b['elapsed_s'] for a,b in zip(samples,samples[1:])),'sample sequence differs')
        rss=[s['rss_kib'] for s in samples if s['rss_kib'] is not None]
        require(rss and min(rss)==result['rss_kib']['min'] and max(rss)==result['rss_kib']['max'],'RSS summary differs')
        available=min(s['mem_available_kib'] for s in samples)
        require(available==result['min_available_kib'] and available>=1024*1024 and max(rss)<=12*1024*1024,'memory boundary differs')
        require((folder/'server-exit-status').read_text().strip() in ('0','-15'),'server exit differs')
        rows.append(dict(label=label,model=model,length=length,repeat=repeat,arm=arm,context=context,
            ttft_s=result['ttft_ms']/1000,prefill_s=timing['prompt_ms']/1000,prefill_tps=timing['prompt_per_second'],
            decode_tps=timing['predicted_per_second'],decode_s=timing['predicted_ms']/1000,wall_s=result['wall_s'],
            peak_rss_mib=max(rss)/1024,min_available_mib=available/1024,samples=len(samples)))
    groups=[]
    keys=('ttft_s','prefill_s','prefill_tps','decode_tps','decode_s','wall_s','peak_rss_mib','min_available_mib')
    for model in MODELS:
        for length in (16384,32768):
            group=dict(model=model,length=length,pairs=2 if length==16384 else 1)
            for arm in ('baseline','final'):
                subset=[r for r in rows if r['model']==model and r['length']==length and r['arm']==arm]
                require(len(subset)==group['pairs'],'sample count differs')
                group[arm]={key:dict(mean=statistics.mean(r[key] for r in subset),min=min(r[key] for r in subset),max=max(r[key] for r in subset)) for key in keys}
            b,f=group['baseline'],group['final']
            group['change_percent']={k:(f[k]['mean']/b[k]['mean']-1)*100 for k in keys}
            groups.append(group)
    return dict(status='pass',requests=12,receipt_checks=count,memory_samples=samples_total,elapsed_s=summary['elapsed_s'],
        models=MODELS,inputs=pins,hardware=read(results/'identity.json')['hardware'],rows=rows,groups=groups,
        limitations=['Two pairs per model at 16384 input tokens.','One pair per model at 32768 input tokens.',
            'Explicit capacity extension; ordinary context remains 12288.','Synthetic fixed output; no long semantic or state acceptance.',
            'RSS samples cover server load and request at a nominal 1 s interval.','No population confidence interval.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    task=Path(__file__).resolve().parent
    parser.add_argument('--board',type=Path,default=task/'board/k1-ultralong-20261014-r1')
    parser.add_argument('--task',type=Path,default=task)
    parser.add_argument('--original',type=Path,default=task.parent/'final-default-20261013/board')
    args=parser.parse_args(); require(not args.output.exists(),'output exists')
    result=verify(args.board,args.task,args.original)
    result['verifier_sha256']=sha(Path(__file__))
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','requests','receipt_checks','memory_samples','elapsed_s')}))
