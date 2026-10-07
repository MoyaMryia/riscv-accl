import pathlib,json,hashlib,tarfile,importlib.util,datetime,statistics
base=pathlib.Path('/home/moyamryia/Projects/riscv-accl');r=base/'spacemit/reports/raw/local-reference-quality-20261006-194015';run=json.loads((r/'run.json').read_text());s=json.loads((r/'summary.json').read_text())
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def load(name,folder):
 spec=importlib.util.spec_from_file_location(name,folder/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
assert s['status']=='completed' and s['requests_completed']==s['planned_requests']==12
for name in ['exit-status','generation-exit-status']:assert (r/name).read_text().strip()=='0'
assert digest(r/'local-reference-quality.py')==run['runner_sha256']
for name,sha in run['frozen_input_sha256'].items():assert digest(r/name)==sha
board=pathlib.Path(run['board_evidence']);receipt=json.loads((board/'collection-receipt.json').read_text())
for model in ['2B','4B']:
 for kind in ['pairs','cases']:
  name=model+'-'+kind+'.json';assert digest(r/('board-'+name))==receipt['files_sha256'][name]==digest(board/name)
expected=json.loads((r/'board-expected-provenance.json').read_text());models=json.loads((r/'model-verification.json').read_text())
for model,info in models.items():assert digest(pathlib.Path(info['path']))==info['sha256']==expected['models'][model]['sha256']
source=json.loads((r/'source-verification.json').read_text());assert digest(pathlib.Path(run['source_archive']))==source['archive_sha256']
with tarfile.open(run['source_archive']) as tar:
 members=[m for m in tar.getmembers() if m.isfile()];assert len(members)==source['verified_files']==len(source['files_sha256']);assert set(m.name for m in members)==set(source['files_sha256'])
 for m in members:
  sha=hashlib.sha256(tar.extractfile(m).read()).hexdigest();assert sha==source['files_sha256'][m.name]==digest(pathlib.Path(run['source'])/m.name)
build=pathlib.Path(run['build_dir']);v=json.loads((r/'build-verification.json').read_text())
for p,key in [(build/'bin/llama-server','server_sha256'),(build/'CMakeCache.txt','cmake_cache_sha256'),(build/'compile_commands.json','compile_commands_sha256')]:assert digest(p)==v[key]
cache={}
for line in (build/'CMakeCache.txt').read_text().splitlines():
 if '=' in line and ':' in line and not line.startswith(('#','//')):
  key,val=line.split('=',1);cache[key.split(':')[0]]=val
settings=json.loads((r/'build-config.json').read_text())['settings']
for key,val in settings.items():assert cache[key]==val,(key,cache.get(key),val)
compile_commands=json.loads((build/'compile_commands.json').read_text())
for row in compile_commands:
 cmd=row['command'];assert not any(flag in cmd for flag in ['-march=native','-mavx','-mfma','-mf16c','-msse4.2','GGML_USE_CPU_RISCV64_SPACEMIT','GGML_USE_BLAS','GGML_USE_CUDA'])
pilot=load('mtp-quality',board);totals={};answer_count=0;judge_pairs=0
for model in ['2B','4B']:
 config=json.loads((r/(model+'-server-config.json')).read_text());argv=config['command'];assert config['cpu_only'] and not config['flash_attention'] and not config['mtp'] and config['custom_runtime_variables']=={}
 for flag,val in [('-t','4'),('-c','6144'),('-b','32'),('-ub','32'),('-fa','off'),('-ctk','f16'),('-ctv','f16'),('-ngl','0')]:assert argv[argv.index(flag)+1]==val
 assert '--spec-type' not in argv and '--ignore-eos' not in argv and '--no-context-shift' in argv
 rows=json.loads((r/(model+'-reference.json')).read_text());pairs=json.loads((r/('board-'+model+'-pairs.json')).read_text());cases=json.loads((r/('board-'+model+'-cases.json')).read_text())['cases'];grades=[json.loads(l) for l in (r/(model+'-judge.jsonl')).read_text().splitlines()];grade={g['case_id']:g for g in grades};assert len(grade)==len(grades);assert set(rows)=={c['case_id'] for c in cases}
 counts={'natural_stops':0,'length_caps':0,'facts_and_citations_pass':0,'code_pass':0,'code_cases':0,'deterministic_pass':0,'useful':0,'identical_control':0,'identical_hybrid':0,'judged_pairs':len(grades)};scores=[]
 for case in cases:
  name=case['case_id'];row=rows[name];request=row['request'];assert request==pairs[name]['control']['request']==pairs[name]['hybrid']['request'];assert request['seed']==42 and request['temperature']==0 and request['cache_prompt'] is False and request['chat_template_kwargs']=={'enable_thinking':False};sha=hashlib.sha256(json.dumps(request,sort_keys=True,ensure_ascii=False).encode()).hexdigest();assert sha==row['request_sha256']==pairs[name]['control']['request_sha256'];assert row['prompt_tokens']==pairs[name]['control']['prompt_tokens'];assert hashlib.sha256(row['answer'].encode()).hexdigest()==row['answer_sha256'];assert (r/(model+'-reference-'+name+'-answer.md')).read_text()==row['answer']+'\n';audit=pilot.audit_result(row,request,row['prompt_tokens']);audit['draft_disabled']=row['timings'].get('draft_n',0)==0;assert audit==row['audit'];assert all(v for k,v in audit.items() if k!='complete');assert row['finish_reason'] in ['stop','length'];counts['natural_stops']+=row['finish_reason']=='stop';counts['length_caps']+=row['finish_reason']=='length'
  facts=pilot.checks.fact_check(case,row['answer']);assert facts==row['facts'];good=all(facts['facts']) and all(facts['citations']);code={}
  if case['kind']=='code':
   code=pilot.checks.check_code(name,row['answer']);assert code==row['code_test'];counts['code_cases']+=1;counts['code_pass']+=code['pass'];good=good and code['pass']
  else:counts['facts_and_citations_pass']+=good
  counts['deterministic_pass']+=good;counts['identical_control']+=row['answer']==pairs[name]['control']['answer'];counts['identical_hybrid']+=row['answer']==pairs[name]['hybrid']['answer'];answer_count+=1
  item=json.loads((r/(model+'-'+name+'-judge-input.json')).read_text());assert item['cold_answer']==pairs[name]['control']['answer'] and item['warm_answer']==row['answer'] and item['question']==case['question'] and item['evidence']==case['evidence'] and item['required_facts']==case['required_facts']
  rating=grade.get(model+'-'+name)
  if audit['complete']:
   assert rating is not None and rating['input_sha256']==hashlib.sha256(json.dumps(item,sort_keys=True).encode()).hexdigest();assert rating['judge_model']=='mimo-v2.6-flash';assert {tuple(p['order']) for p in rating['passes']}=={('cold','warm'),('warm','cold')};assert len(rating['passes'])==2
   for arm in ['cold','warm']:assert rating[arm+'_mean_score']==statistics.mean(p[arm]['score'] for p in rating['passes'])
   scores.append(rating['warm_mean_score']);counts['useful']+=bool(good and rating['warm_mean_score']>=4);judge_pairs+=1
  else:assert rating is None
 assert counts['useful']==s['models'][model]['reference_useful'];totals[model]=dict(counts,mean_score_on_judged_answers=statistics.mean(scores))
verification={'verified_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'status':'verified','runner_sha256':run['runner_sha256'],'frozen_inputs_verified':len(run['frozen_input_sha256']),'exact_gguf_files_verified':2,'source_archive_sha256':source['archive_sha256'],'source_files_verified':len(source['files_sha256']),'build_flags_and_binary_hashes_verified':True,'complete_request_answer_audits':answer_count,'judge_pairs_verified':judge_pairs,'judge_calls_two_orders':2*judge_pairs,'generation_exit_status':0,'runner_exit_status':0,'reference_tmux_and_server_stopped_independently_confirmed':True,'models':totals}
verification['result_files_sha256']={p.name:digest(p) for p in r.iterdir() if p.is_file() and p.name not in ['completion-verification.json']}
(r/'completion-verification.json').write_text(json.dumps(verification,indent=2,ensure_ascii=False)+'\n');print(json.dumps({k:v for k,v in verification.items() if k!='result_files_sha256'},indent=2))
