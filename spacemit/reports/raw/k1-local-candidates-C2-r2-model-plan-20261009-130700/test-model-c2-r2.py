import contextlib,importlib.util,io,json,os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path('spacemit/bench/local-candidates').resolve()))
spec=importlib.util.spec_from_file_location('driver_c2','spacemit/bench/local-candidates/model-c2-r2.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
operator=json.loads(Path('spacemit/reports/raw/k1-local-candidates-C2-r2-result-20261009-130000/summary.json').read_text())
r2='SPINE_GDN_PREFILL_R2: retained two state segments; S=128; VLEN=256\n'+''.join(f'K1_GDN_R2 worker={i} workers=4 state=128\n' for i in range(4))
markers='K1_GEMM_ROUTE mode=3 phase=prefill\nSPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads\nK1_SSM_CONV mode=0 layout=time rs=0 cpu_only=1 tokens=32 requested=0\nK1_SSM_CONV mode=0 layout=time rs=0 cpu_only=1 tokens=1 requested=0\n'
for failure in ['none','state','initial','repeat-1']:
 with tempfile.TemporaryDirectory() as tmp:
  temp=Path(tmp);root=temp/'root';root.mkdir();screen=temp/'screen';(screen/'C/lib').mkdir(parents=True);home=temp/'home';(home/'Projects/riscv-accl-bench-2026-09-27').mkdir(parents=True);(screen/'C/lib/libggml-cpu.so').write_bytes(b'cpu');(screen/'C/lib/libllama.so').write_bytes(b'llama')
  (root/'model-protocol.json').write_text(json.dumps({'repeats':2,'order':['C0','C2','C2','C0'],'fixed_files_sha256':{}}));(screen/'summary.json').write_text(json.dumps(operator));(screen/'baseline-before.json').write_text('{}');(screen/'baseline-check.json').write_text('{"unchanged":true}');(screen/'libraries.json').write_text('{}');expected={'artifacts_sha256':{'/fake/source/build/bin/llama-server':'hash'},'models':{m:{'path':'/'+m+'.gguf','sha256':'hash'} for m in ['2B','4B']},'runtime':{'LD_LIBRARY_PATH':'/fixed/runtime'}};(screen/'expected-provenance.json').write_text(json.dumps(expected));calls=[];collected=[]
  def run(command,**kw):
   argv=list(map(str,command));env=kw['env'];assert env['SPINE_K1_FA_GQA']==env['SPINE_K1_FA_DECODE']==env['SPINE_K1_SSM_CONV']==env['SPINE_K1_CONV_SILU']=='0'
   if '-o' in argv:Path(argv[-1]).write_bytes(b'probe');return
   only_rs3=argv[-1]=='rs3';arm=int(argv[2]);dump=argv[3];name=argv[1];calls.append((name,arm));text=''.join(f'C2_STATE threads=4 batch_threads=4 rs={rs}\n' for rs in ([3] if only_rs3 else [0,3]) for _ in range(2 if arm else 1));rows=[]
   for rs in ([3] if only_rs3 else [0,3]):
    for reset in [0,1]:
     for p in [32,33,64,96]:
      row={'arm':arm,'rs':rs,'reset':reset,'prefix':p,'vocab':1,'bitwise_equal':True,'max_abs':0};rows.append(row)
      for active in ([0,1] if arm else [0]):
       text+=f'C2_STATE begin arm={active}\n'+(r2 if active==1 and len(rows)==1 and not only_rs3 else '')+f'C2_STATE end arm={active}\n'
   text+=(markers.replace('rs=0','rs=3') if only_rs3 else markers)+('SPINE_GDN_PREFILL: scalar-gate K1 RVV fusion enabled\n' if arm and not only_rs3 else '')+'\n'.join(json.dumps(r) for r in rows)+f'\nPASS: {len(rows)} full-vocabulary records;\n';kw['stdout'].write(text);kw['stdout'].flush();Path(dump).write_bytes(b'\x00'*(32 if only_rs3 else 64))
   if failure=='state' and arm:
    kw['stdout'].write('FAIL: candidate logits differ\n');kw['stdout'].flush();raise d.subprocess.CalledProcessError(1,argv)
  phases=[]
  def compare(args,benchmark_lock):
   assert benchmark_lock.fileno()>=0;env=d.prefill.arm_env('C2',args.library);assert env['SPINE_K1_TRACE']=='1' and env['SPINE_GDN_PREFILL']=='1';args.destination.mkdir();(args.destination/'2B-C2-1.server.log').write_text(r2);phase='initial' if not phases else 'repeat-'+str(len(phases));phases.append(phase);return {'status':'stopped' if failure==phase else 'eligible','comparisons':[]}
  def collect(path,*args):
   path.mkdir();collected.append(path)
   for name in ['2B','4B']:(path/(name+'-C2.server.log')).write_text(r2)
  with patch.object(d.Path,'home',return_value=home),patch.object(d.board,'digest',return_value='hash'),patch.object(d.subprocess,'run',side_effect=run),patch.object(d.prefill,'compare',side_effect=compare),patch.object(d.complete_answers,'collect',side_effect=collect),patch.object(sys,'argv',['model-c2-r2',str(root),str(screen)]),contextlib.redirect_stdout(io.StringIO()):assert d.main()==0
  s=json.loads((root/'summary.json').read_text())
  if failure=='state':assert len(calls)==3 and not phases and not collected and s['status']=='state-numeric-stopped'
  elif failure=='initial':assert phases==['initial'] and not collected and s['status']=='initial-gate-stopped'
  elif failure=='repeat-1':assert phases==['initial','repeat-1'] and not collected and s['status']=='repeat-1-gate-stopped'
  else:assert len(calls)==8 and phases==['initial','repeat-1','repeat-2'] and len(collected)==1
  print('PASS: C2-r2 controller case',failure)
# The path check must reject a missing worker and a control that activates C2-r2.
d.prefill.activation(markers+r2+'SPINE_GDN_PREFILL: scalar-gate K1 RVV fusion enabled\n','C2')
for text,arm in [(markers+r2.replace('K1_GDN_R2 worker=3 workers=4 state=128\n','')+'SPINE_GDN_PREFILL: scalar-gate K1 RVV fusion enabled\n','C2'),(markers+r2,'C0')]:
 try:d.prefill.activation(text,arm)
 except ValueError:pass
 else:raise AssertionError('invalid actual path passes')
print('PASS: C2-r2 path check rejects a missing worker and candidate activation in the control')
