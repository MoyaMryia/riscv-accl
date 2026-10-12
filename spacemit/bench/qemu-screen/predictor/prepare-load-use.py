#!/usr/bin/env python3
"""冻结加载消费调度对照，不把组合成本解释为纯加载延迟。"""
import argparse
from pathlib import Path
import random
import shutil
import subprocess
from analyze import write, sha, seal, load as read_json

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]


def cases():
    result = [dict(id=f'load-use-m{m}-vl{vl}-s{stride}-c{chains}',m=m,vl=vl,stride=stride,chains=chains)
        for m in (1,2,4) for vl in (4*m,8*m) for stride in (0,16) for chains in (2,4)]
    random.Random(20261012).shuffle(result)
    for i,row in enumerate(result):row['split']='calibration' if i<19 else 'test'
    return result


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    groups=read_json(a.groups) if a.groups else cases();rows=[];blocks=[]
    if len({g['id'] for g in groups})!=len(groups):raise ValueError('配置组重复。')
    for g in groups:
        if g['m'] not in (1,2,4) or not 1<=g['vl']<=8*g['m'] or g['chains'] not in (2,4) or g['stride'] not in (0,16) or g['split'] not in ('training','calibration','test'):
            raise ValueError('加载消费配置超出声明范围。')
    for i,group in enumerate(groups):
        m,vl,chains,stride=(group[k] for k in ('m','vl','chains','stride'))
        for arm in (0,1):
            for ops in (8,32,128):
                name=f'k1lu_{i}_{arm}_{ops}'
                entry=['mv t5,a0','mv t4,a2','li t0,0',f'vsetvli t6,zero,e32,m{m},ta,ma']
                entry += [f'vmv.v.i v{16+j*m},0' for j in range(chains)]
                entry += [f'li t6,{vl}',f'vsetvli zero,t6,e32,m{m},ta,ma',f'li t3,{stride}']
                body=[]
                for block in range(ops//chains):
                    loads=[];uses=[]
                    for j in range(chains):
                        v=j*m if arm else 0
                        load=[f'addi t1,a1,{j*256}',f'vlse32.v v{v},(t1),t3' if stride else f'vle32.v v{v},(t1)']
                        use=f'vfadd.vv v{16+j*m},v{16+j*m},v{v}'
                        if arm:loads+=load;uses.append(use)
                        else:body+=load+[use]
                    if arm:body+=loads+uses
                loop=body+['addi t0,t0,1','addi t5,t5,-1',f'bnez t5,.L{name}']
                finish=[]
                for j in range(chains):finish += [f'vs{m}r.v v{16+j*m},(t4)',f'addi t4,t4,{32*m}']
                alignment=[f'.balign {a.loop_alignment}'] if a.loop_alignment else []
                blocks.append([*alignment,f'.global {name}',f'.type {name},@function',name+':',*entry,
                    *alignment,'.L'+name+':',*loop,*finish,'mv a0,t0','fence rw,rw','ret',f'.size {name},.-{name}'])
                rows.append(dict(id=name,group=group['id'],arm=arm,operations=ops,body=loop,**{k:group[k] for k in ('m','vl','chains','stride','split')}))
    if a.layout_seed is not None:random.Random(a.layout_seed).shuffle(blocks)
    assembly=['.text','.option norvc']+[line for block in blocks for line in block]
    (out/'kernels.s').write_text('\n'.join(assembly)+'\n')
    declarations='\n'.join(f'extern uint64_t {r["id"]}(uint64_t,void *,void *);' for r in rows)
    table=',\n'.join('{"%s","%s",%s,%d,%d,%d,%d,%d,%d}'%(r['id'],r['group'],r['id'],r['arm'],r['operations'],r['m'],r['vl'],r['chains'],{'calibration':0,'test':1,'training':2}[r['split']]) for r in rows)
    driver=a.driver_template or HERE/'load-use-measure.c'
    (out/'measure.c').write_text(driver.read_text().replace('/* DECLARATIONS */',declarations).replace('/* TABLE */',table))
    compiler=a.compiler.resolve();argv=list(map(str,[compiler,'-O2','-g','-static','-fno-pie','-no-pie','-march=rv64gcv','-Wall','-Wextra','-Werror',out/'measure.c',out/'kernels.s','-o',out/'measure']))
    write(out/'build-command.json',argv)
    with (out/'build.log').open('w') as log:subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,check=True)
    subprocess.run(['python3',HERE.parent/'assembly-inventory.py',out/'measure',out/'inventory',
        '--symbol-regex','^k1lu_','--tool-prefix',str(compiler).removesuffix('gcc')],check=True)
    write(out/'plan.json',dict(schema=4,groups=groups,records=rows,lengths=[512,2048,8192],trace_lengths=[2,16],
        repetitions=7,binary_sha256=sha(out/'measure'),compiler_sha256=sha(compiler),
        counter=dict(type='PERF_TYPE_RAW',config='0x22',scope='locally audited K1 U-mode cycle event'),
        frozen_component_model_sha256='dd267b9c6d897d0aa025d81d940505a7e34709847eac4fe419f84a4a9ab8b148',
        layout_seed=a.layout_seed,loop_alignment_bytes=a.loop_alignment,
        scope='CPU 0; fixed hot read-only data; e32 vector load and accumulation schedule; separate held-out groups',
        limits=['schedule pair changes input register reuse and instruction order together',
            'combined load-use schedule cost does not isolate pure load latency',
            'active outputs, full inputs and guards are exact; inactive agnostic lanes are not outputs',
            'same binary native and QEMU; native counters exclude output checks',
            'loop slopes remove fixed entry and exit cost; no complete model or shared-thread confidence claim']))
    shutil.copy2(a.board_wrapper or HERE/'run-load-use-board.sh',out/'run-load-use-board.sh')
    seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path)
    p.add_argument('--compiler',type=Path,required=True)
    p.add_argument('--groups',type=Path);p.add_argument('--driver-template',type=Path)
    p.add_argument('--layout-seed',type=int);p.add_argument('--loop-alignment',type=int,choices=[64])
    p.add_argument('--board-wrapper',type=Path);main(p.parse_args())
