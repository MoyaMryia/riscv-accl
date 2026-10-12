#!/usr/bin/env python3
"""生成固定的小内核与样本计划，不生成生产候选代码。"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]


def main(out,compiler=None):
    out.mkdir(parents=True,exist_ok=False)
    records, lines = [],['.text','.option norvc']
    def kernel(group,split,arm,body,expected,kind='arithmetic',preamble=None,finish=None):
        name = 'cal_'+group.replace('-','_')+'_'+arm
        entry = ['mv t5,a0','li t0,0','li t1,0','li t2,0','li t3,0','mv t4,a1',
            'vsetivli zero,8,e32,m1,ta,ma','vmv.v.i v8,0','vmv.v.i v9,1','vmv.v.i v10,1',
            'vmv.v.i v12,0','vmv.v.i v16,0','vmv.v.i v20,0',
            'lui t6,0x3f800','fmv.w.x ft0,t6','vfmv.v.f v9,ft0','vfmv.v.f v10,ft0']
        if preamble: entry += preamble
        body = body+['addi t5,t5,-1','bnez t5,.L'+name]
        end = (finish or ['mv a0,t0'])+['vsetivli zero,8,e32,m1,ta,ma','vse32.v v8,(a2)',
            'addi t6,a2,32','vse32.v v16,(t6)','fence rw,rw']
        lines.extend(['.global '+name,'.type '+name+',@function',name+':',*entry,'.L'+name+':',*body,*end,'ret','.size '+name+',.-'+name])
        records.append({'id':name,'group':group,'split':split,'arm':arm,'symbol':name,
            'expected_per_iteration':expected,'kind':kind,'body':body,
            'scope':'fixed calibration microkernel; no full operator or model prediction'})
    kernel('scalar-dependent','train','single',['addi t0,t0,1']*16,16)
    kernel('scalar-independent','train','single',[f'addi t{i},t{i},1' for _ in range(4) for i in range(4)],16,
           finish=['add t0,t0,t1','add t2,t2,t3','add a0,t0,t2'])
    kernel('rvv-dependent','train','single',['vfmacc.vv v8,v9,v10']*16,16,
           finish=['vfmv.f.s ft1,v8','fcvt.l.s a0,ft1,rtz'])
    kernel('rvv-independent','train','single',[f'vfmacc.vv v{v},v9,v10' for _ in range(4) for v in (8,16,20,24)],16,
           preamble=['vmv.v.i v24,0'],finish=['vfadd.vv v8,v8,v16','vfadd.vv v20,v20,v24',
               'vfadd.vv v8,v8,v20','vfmv.f.s ft1,v8','fcvt.l.s a0,ft1,rtz'])
    for group in ('load-L1','load-L2'):
        kernel(group,'train','single',['ld t4,0(t4)']*16,0,'pointer',finish=['mv a0,t4'])
    independent = ['addi t0,t0,1','vfmacc.vv v20,v9,v10']
    chain = ['vfmacc.vv v8,v9,v10','vfredusum.vs v11,v8,v12','vfmv.f.s ft1,v11',
             'fadd.s ft2,ft1,ft0','vfmv.s.f v16,ft2']
    for arm,body in [('control',chain+independent),('candidate',independent+chain)]:
        kernel('mixed-gdn','test',arm,body,3,finish=['vfmv.f.s ft1,v8','vfmv.f.s ft2,v20',
            'fadd.s ft1,ft1,ft2','fcvt.l.s a0,ft1,rtz','add a0,a0,t0'])
    for group,op in [('mixed-conv','vfmul.vf'),('mixed-attention','vfmacc.vf')]:
        a=['vle32.v v8,(a1)',op+' v8,ft0,v9' if op=='vfmacc.vf' else op+' v8,v8,ft0']
        b=['vle32.v v16,(a1)',op+' v16,ft0,v10' if op=='vfmacc.vf' else op+' v16,v16,ft0']
        tail=['vfadd.vv v8,v8,v16','vfredosum.vs v11,v8,v12','vfmv.f.s ft1,v11',
              'fcvt.l.s t1,ft1,rtz','add t0,t0,t1']
        for arm,body in [('control',a+b+tail),('candidate',[a[0],b[0],a[1],b[1]]+tail)]:
            kernel(group,'test',arm,body,32 if op=='vfmacc.vf' else 16)
    for group,sew in [('mixed-load-control',8),('mixed-load-candidate',16)]:
        a=[f'vle{sew}.v v8,(a1)','vand.vi v8,v8,15','vsrl.vi v8,v8,1']
        b=[f'vle{sew}.v v16,(a1)','vand.vi v16,v16,15','vsrl.vi v16,v16,1']
        tail=['vsetivli zero,8,e32,m1,ta,ma','addi t0,t0,1']
        for arm,body in [('control',a+b+tail),('candidate',[a[0],b[0],a[1],b[1],a[2],b[2]]+tail)]:
            # 每次循环重设元素宽度，结尾恢复 E32。
            kernel(group,'test',arm,[f'vsetivli zero,8,e{sew},m1,ta,ma']+body,1,
                finish=['vsetivli zero,8,e8,m1,ta,ma','vmv.x.s t1,v8','vmv.x.s t2,v16','add a0,t0,t1','add a0,a0,t2'],
                kind='unpack')
    (out/'kernels.s').write_text('\n'.join(lines)+'\n')
    declarations = '\n'.join('extern uint64_t '+r['symbol']+'(uint64_t,void *,void *);' for r in records)
    table = ',\n'.join('{"'+r['id']+'",'+r['symbol']+','+str(r['expected_per_iteration'])+','+
        str({'arithmetic':0,'pointer':1,'unpack':2}[r['kind']])+','+str(32768 if r['group']=='load-L2' else 512)+'}' for r in records)
    template = (HERE/'measure-template.c').read_text()
    (out/'measure.c').write_text(template.replace('/* DECLARATIONS */',declarations).replace('/* TABLE */',table))
    protocol = HERE/'validation-protocol.json'
    plan = {'schema':3,'records':records,'protocol_sha256':hashlib.sha256(protocol.read_bytes()).hexdigest(),
        'counter':{'type':'PERF_TYPE_RAW','config':'0x22','scope':'K1 U-mode cycle event; run counter-audit first'},
        'lengths':[1000,4000,16000],'repetitions':5,'cpu':0,'warmup_iterations':32000,
        'samples':'keep all; no fastest-only selection; failed output or multiplexed counters invalidate the sample',
        'scope':'synthetic instruction mixtures; group names identify instruction classes, not real operator workloads'}
    (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    (out/'validation-protocol.json').write_bytes(protocol.read_bytes())
    if compiler:
        command = [str(compiler.resolve()),'-O2','-static','-march=rv64gcv','-Wall','-Wextra','-Werror',
                   str((out/'measure.c').resolve()),str((out/'kernels.s').resolve()),'-o',str((out/'measure').resolve())]
        (out/'build-command.json').write_text(json.dumps(command,indent=2)+'\n')
        (out/'compiler-version.log').write_text(subprocess.check_output([compiler,'--version'],text=True))
        with (out/'build.log').open('w') as log: subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
        binary_sha = hashlib.sha256((out/'measure').read_bytes()).hexdigest()
        (out/'BINARY-SHA256SUMS').write_text(binary_sha+'  measure\n')
        plan['binary_sha256']=binary_sha
        plan['compiler_sha256']=hashlib.sha256(compiler.read_bytes()).hexdigest()
        (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    (out/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n'
        for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--compiler',type=Path)
    args = parser.parse_args()
    main(args.output,args.compiler)
