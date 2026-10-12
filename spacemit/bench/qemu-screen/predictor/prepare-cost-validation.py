#!/usr/bin/env python3
"""建立无计数器的旧内核轨迹夹具，并核验函数字节。"""
import argparse
from pathlib import Path
import subprocess
import sys
from analyze import load,write,sha,seal

HERE=Path(__file__).resolve().parent


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    plan=load(a.board/'plan.json');old=load(a.inventory)
    if old['elf_sha256']!=sha(a.board/'measure'):raise ValueError('旧标定二进制身份不同。')
    prefix=(a.board/'measure.c').read_text().split('static long frequency(void)')[0]
    driver=r'''
int main(int argc,char **argv) {
    if(argc!=4)return 2;
    int k=atoi(argv[1]);uint64_t n=strtoull(argv[2],NULL,10);
    if(k<0||k>=(int)(sizeof kernels/sizeof kernels[0])||n==0||n>4096)return 2;
    void *data=NULL;if(posix_memalign(&data,64,32768*sizeof(void *)))return 3;
    void **nodes=data;
    if(kernels[k].kind==1){for(int i=0;i<kernels[k].nodes;++i)nodes[i]=&nodes[(i+1)%kernels[k].nodes];}
    else{for(int i=0;i<16;++i)((float *)data)[i]=1.0f;}
    uint32_t output[16] __attribute__((aligned(64)))={0};
    uint64_t value=kernels[k].fn(n,data,output),expected=n*kernels[k].factor;
    if(kernels[k].kind==1)expected=(uintptr_t)&nodes[(16*n)%kernels[k].nodes];
    if(value!=expected)return 4;
    FILE *file=fopen(argv[3],"wb");if(!file)return 5;
    int ok=fwrite(output,1,sizeof output,file)==sizeof output;
    ok&=fclose(file)==0;free(data);return ok?0:6;
}
'''
    (out/'driver.c').write_text(prefix+driver)
    (out/'kernels.s').write_bytes((a.board/'kernels.s').read_bytes())
    compiler=str(a.compiler.resolve())
    argv=[compiler,'-O2','-static','-march=rv64gcv','-Wall','-Wextra','-Werror',str(out/'driver.c'),str(out/'kernels.s'),'-o',str(out/'driver')]
    write(out/'build-command.json',argv)
    with (out/'build.log').open('w') as log:subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,check=True)
    subprocess.run([sys.executable,HERE.parent/'assembly-inventory.py',out/'driver',out/'inventory',
                    '--symbol-regex','^cal_','--tool-prefix',str(a.compiler).removesuffix('gcc')],check=True)
    new=load(out/'inventory/inventory.json');functions={f['symbol']:f for f in new['functions']}
    for f in old['functions']:
        before=[(i['bytes'],i['encoding']) for i in f['instructions']]
        after=[(i['bytes'],i['encoding']) for i in functions[f['symbol']]['instructions']]
        if before!=after:raise ValueError('新夹具改变了旧标定函数字节。')
    write(out/'plan.json',dict(schema=2,records=plan['records'],lengths=[16,128],
        binary_sha256=sha(out/'driver'),old_binary_sha256=sha(a.board/'measure'),
        old_plan_sha256=sha(a.board/'plan.json'),old_samples_sha256=sha(a.board/'samples.jsonl'),
        identity_check='all actual function bytes equal the native calibration binary',
        limit='retrospective microkernel check; not independent unseen full-operator validation'))
    seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('board',type=Path)
    p.add_argument('--inventory',type=Path,required=True);p.add_argument('--compiler',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);main(p.parse_args())
