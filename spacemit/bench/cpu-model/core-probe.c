#define _GNU_SOURCE
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern uint64_t probe_vector(void);
extern void probe_ime(void *);
__asm__(".text\n.option norvc\n.global probe_vector\n.type probe_vector,@function\nprobe_vector:\n"
        "vsetvli a0,zero,e8,m1,ta,ma\nret\n.size probe_vector,.-probe_vector\n"
        ".global probe_ime\n.type probe_ime,@function\nprobe_ime:\n"
        "vsetvli a3,zero,e32,m2,ta,ma\nvmv.v.i v16,0\n"
        "vsetvli a3,zero,e8,m1,ta,ma\nvmv.v.i v0,1\nvmv.v.i v1,1\n"
        ".word 0xe210382b\nvsetvli a3,zero,e32,m2,ta,ma\nvs2r.v v16,(a0)\nret\n.size probe_ime,.-probe_ime\n");
int main(int argc,char **argv) {
    if(argc!=3)return 2;
    int cpu=atoi(argv[1]);if(cpu<0||cpu>=CPU_SETSIZE)return 2;
    cpu_set_t mask;CPU_ZERO(&mask);CPU_SET(cpu,&mask);if(sched_setaffinity(0,sizeof mask,&mask))return 3;
    if(!strcmp(argv[2],"vector")){
        uint64_t vl=probe_vector();printf("{\"cpu\":%d,\"vl_e8_m1\":%lu}\n",sched_getcpu(),(unsigned long)vl);return vl==32?0:4;
    }
    if(strcmp(argv[2],"ime"))return 2;
    uint32_t output[16] __attribute__((aligned(64)));
    memset(output,0,sizeof output);probe_ime(output);
    int valid=1;for(int i=0;i<16;++i)valid&=output[i]==8;
    printf("{\"cpu\":%d,\"valid\":%s,\"output\":[",sched_getcpu(),valid?"true":"false");
    for(int i=0;i<16;++i){printf("%s%u",i?",":"",output[i]);}
    puts("]}");return valid?0:5;
}
