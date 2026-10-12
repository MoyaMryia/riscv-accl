#!/usr/bin/env python3
"""补测卷积热点中的存储、加载、配置和常量写入成本。"""
import argparse
from pathlib import Path
import struct
import subprocess
from analyze import sha,write,seal

HERE=Path(__file__).resolve().parent


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    assembly=['.text'];records=[];expected={};counts=[8,32,128]
    ops=('lw','c.lw','flw','fsw','vse32.v','vmv.v.i','vsetvli')
    for index,op in enumerate(ops):
        vector=op.startswith('v');key=dict(op=op,sew=32 if vector else 0,lmul=1 if vector else 0,
            vl=8 if vector else 0,stride=0,footprint=0)
        for mode,chains in (('dependent',1),('independent',8 if op=='vmv.v.i' else 4)):
            for count in counts:
                name=f'k1gap_{index}_{mode}_{count}';regs=['a0','a3','a4','a5'][:min(chains,4)]
                entry=['mv t5,a0','mv t4,a2','li t0,0','li t6,8','lui t1,0x3f800','fmv.w.x ft0,t1']
                finish=[];body=[];want=bytearray();mask=bytearray()
                if vector:
                    entry+=['vsetvli t2,zero,e32,m1,tu,mu']
                    for v in range(chains):entry.append(f'vfmv.v.f v{v},ft0' if op=='vse32.v' else f'vmv.v.i v{v},0')
                    entry+=['vsetvli t2,t6,e32,m1,ta,ma']
                if op in ('lw','c.lw','flw','fsw'):
                    for j in range(count):
                        r=regs[j%len(regs)];f='ft'+str(j%len(regs))
                        if op=='fsw' and f!='ft0' and j<len(regs):entry.append(f'fmv.s {f},ft0')
                        body.append(f'{op} {f if op in ("flw","fsw") else r},0(a1)')
                    if op in ('flw','fsw'):
                        if op=='fsw':finish+=['flw ft0,0(a1)']
                        outchains=1 if op=='fsw' else chains
                        for j in range(outchains):finish.append(f'fsw ft{j},{j*4}(t4)')
                        want=bytearray(struct.pack('<f',1.0)*outchains)
                    else:
                        for j,r in enumerate(regs):finish.append(f'sd {r},{j*8}(t4)')
                        want=bytearray(struct.pack('<Q',0x3f800000)*chains)
                elif op=='vse32.v':
                    body=[f'vse32.v v{j%chains},(a1)' for j in range(count)]
                    finish+=['vl1re32.v v24,(a1)','vs1r.v v24,(t4)'];want=bytearray(struct.pack('<f',1.0)*8)
                elif op=='vmv.v.i':
                    body=[f'vmv.v.i v{j%chains},5' for j in range(count)]
                    for j in range(chains):finish += [f'vs1r.v v{j},(t4)','addi t4,t4,32']
                    want=bytearray(struct.pack('<I',5)*8*chains)
                else:
                    for r in regs:entry.append(f'li {r},8')
                    body=[f'vsetvli {regs[j%chains]},{regs[j%chains] if mode=="dependent" else "t6"},e32,m1,ta,ma' for j in range(count)]
                    for j,r in enumerate(regs):finish.append(f'sd {r},{j*8}(t4)')
                    want=bytearray(struct.pack('<Q',8)*chains)
                mask=bytearray([255]*len(want))
                assembly += ['.option norvc',f'.global {name}',f'.type {name},@function',name+':',*entry,
                    '.L'+name+':','.option rvc' if op.startswith('c.') else '.option norvc',*body,
                    '.option norvc','addi t0,t0,1','addi t5,t5,-1',f'bnez t5,.L{name}',*finish,'mv a0,t0','fence rw,rw','ret',f'.size {name},.-{name}']
                dependency=('store-address-reuse-no-RAW' if op in ('fsw','vse32.v') else
                    'destination-reuse-no-RAW' if op in ('lw','c.lw','flw','vmv.v.i') else 'RAW-chain')
                records.append(dict(id=name,key=key,mode=mode,chains=chains,operations=count,
                    dependency=dependency,body=body+['addi t0,t0,1','addi t5,t5,-1',f'bnez t5,.L{name}'],
                    store=op in ('fsw','vse32.v'),output_bytes=len(want)))
                expected[name]=want
    (out/'kernels.s').write_text('\n'.join(assembly)+'\n')
    declarations='\n'.join(f'extern uint64_t {r["id"]}(uint64_t,void *,void *);' for r in records)
    table=',\n'.join('{"%s",%s,%d,%d,{%s}}'%(r['id'],r['id'],r['store'],r['output_bytes'],','.join(str(b) for b in expected[r['id']])) for r in records)
    driver=r'''
#define _GNU_SOURCE
#include <inttypes.h>
#include <linux/perf_event.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/resource.h>
#include <sys/syscall.h>
#include <unistd.h>
DECLARATIONS
typedef uint64_t (*Function)(uint64_t,void *,void *);
static struct {const char *id;Function fn;int store,bytes;uint8_t expected[256];} kernels[]={TABLE};
static long frequency(void) {
    FILE *f=fopen("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq","r");long v=-1;
    if(f){if(fscanf(f,"%ld",&v)!=1)v=-1;fclose(f);}return v;
}
int main(void) {
    cpu_set_t cpus;CPU_ZERO(&cpus);CPU_SET(0,&cpus);if(sched_setaffinity(0,sizeof cpus,&cpus))return 2;
    struct perf_event_attr a={0};a.size=sizeof a;a.type=PERF_TYPE_RAW;a.config=0x22;
    a.disabled=1;a.exclude_kernel=1;a.exclude_hv=1;a.read_format=PERF_FORMAT_TOTAL_TIME_ENABLED|PERF_FORMAT_TOTAL_TIME_RUNNING;
    int fd=syscall(__NR_perf_event_open,&a,0,-1,-1,0);if(fd<0)return 3;
    const uint64_t lengths[]={512,2048,8192};
    for(int rep=0;rep<7;++rep)for(size_t offset=0;offset<sizeof kernels/sizeof kernels[0];++offset) {
        size_t k=rep%2?sizeof kernels/sizeof kernels[0]-1-offset:offset;
        float input[1056] __attribute__((aligned(64)));uint8_t output[384] __attribute__((aligned(64)));
        for(int j=0;j<1056;++j)input[j]=1.0f;
        kernels[k].fn(8192,input+16,output+64);
        for(int l=0;l<3;++l){
            uint64_t n=lengths[(l+rep)%3];memset(output,0xa5,sizeof output);
            for(int j=0;j<1056;++j)input[j]=1.0f;
            if(kernels[k].store)memset(input+16,0,32);
            struct rusage before,after;getrusage(RUSAGE_THREAD,&before);long fb=frequency();
            struct {uint64_t cycles,enabled,running;} v={0};
            int rc=ioctl(fd,PERF_EVENT_IOC_RESET,0);rc|=ioctl(fd,PERF_EVENT_IOC_ENABLE,0);
            uint64_t result=kernels[k].fn(n,input+16,output+64);
            rc|=ioctl(fd,PERF_EVENT_IOC_DISABLE,0);ssize_t size=read(fd,&v,sizeof v);
            long fa=frequency();getrusage(RUSAGE_THREAD,&after);
            int valid=!rc&&size==sizeof v&&v.cycles>0&&v.enabled>0&&v.enabled==v.running&&result==n&&sched_getcpu()==0;
            valid&=!memcmp(output+64,kernels[k].expected,kernels[k].bytes);
            for(int j=0;j<64;++j)valid&=output[j]==0xa5&&output[64+kernels[k].bytes+j]==0xa5;
            for(int j=0;j<1056;++j){float want=kernels[k].store&&j>=16&&j<24 ? (kernels[k].bytes==4&&j>16?0.0f:1.0f):1.0f;valid&=input[j]==want;}
            printf("{\"id\":\"%s\",\"repeat\":%d,\"iterations\":%"PRIu64",\"cycles\":%"PRIu64",\"enabled\":%"PRIu64",\"running\":%"PRIu64",\"output\":%"PRIu64",\"expected\":%"PRIu64",\"frequency_before_khz\":%ld,\"frequency_after_khz\":%ld,\"cpu\":%d,\"involuntary_switches\":%ld,\"valid\":%s}\n",
                kernels[k].id,rep,n,v.cycles,v.enabled,v.running,result,n,fb,fa,sched_getcpu(),after.ru_nivcsw-before.ru_nivcsw,valid?"true":"false");
            fflush(stdout);if(!valid)return 5;
        }
    }
    close(fd);return 0;
}
'''
    (out/'measure.c').write_text(driver.replace('DECLARATIONS',declarations).replace('TABLE',table))
    compiler=a.compiler.resolve();argv=list(map(str,[compiler,'-O2','-static','-march=rv64gcv','-Wall','-Wextra','-Werror',out/'measure.c',out/'kernels.s','-o',out/'measure']))
    write(out/'build-command.json',argv)
    with (out/'build.log').open('w') as log:subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,check=True)
    write(out/'plan.json',dict(schema=3,records=records,lengths=[512,2048,8192],repetitions=7,cpu=0,
        counter=dict(type='PERF_TYPE_RAW',config='0x22',scope='K1 U-mode cycle event; run counter-audit first'),
        binary_sha256=sha(out/'measure'),protocol=dict(scope='CPU 0; fixed hot address; full VL e32 m1 only',
            limits='load result readiness is not isolated; repeated stores use one address; immediate move has no RAW input')))
    (out/'BINARY-SHA256SUMS').write_text(sha(out/'measure')+'  measure\n')
    (out/'run-board-calibration.sh').write_bytes((HERE/'run-board-calibration.sh').read_bytes());seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path)
    p.add_argument('--compiler',type=Path,required=True);main(p.parse_args())
