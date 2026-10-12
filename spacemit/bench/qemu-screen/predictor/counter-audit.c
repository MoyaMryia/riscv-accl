#define _GNU_SOURCE
#include <inttypes.h>
#include <linux/perf_event.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <unistd.h>

extern uint64_t audit_user(uint64_t);
extern uint64_t audit_syscall(uint64_t);
__asm__(".text\n.option norvc\n.global audit_user\n.type audit_user,@function\naudit_user:\n"
    "mv t0,a0\nli t1,0\n1: addi t1,t1,1\naddi t0,t0,-1\nbnez t0,1b\nmv a0,t1\nret\n.size audit_user,.-audit_user\n"
    ".global audit_syscall\n.type audit_syscall,@function\naudit_syscall:\n"
    "mv t0,a0\nli a7,178\n1: ecall\naddi t0,t0,-1\nbnez t0,1b\nret\n.size audit_syscall,.-audit_syscall\n");

int main(int argc,char **argv) {
    int include=argc==2&&!strcmp(argv[1],"--all-modes");
    if(argc!=1&&!include)return 2;
    cpu_set_t mask;CPU_ZERO(&mask);CPU_SET(0,&mask);if(sched_setaffinity(0,sizeof mask,&mask))return 2;
    const uint64_t lengths[]={128,512,2048};
    for(int excluded=include?0:1;excluded<2;++excluded) {
        struct perf_event_attr a={0};a.size=sizeof a;a.type=PERF_TYPE_HARDWARE;
        a.config=PERF_COUNT_HW_CPU_CYCLES;a.disabled=1;a.exclude_kernel=excluded;a.exclude_hv=1;
        a.read_format=PERF_FORMAT_GROUP|PERF_FORMAT_TOTAL_TIME_ENABLED|PERF_FORMAT_TOTAL_TIME_RUNNING;
        int fd=syscall(__NR_perf_event_open,&a,0,-1,-1,0);if(fd<0){perror("cycle counter");return 3;}
        a.config=PERF_COUNT_HW_INSTRUCTIONS;a.disabled=0;
        int child=syscall(__NR_perf_event_open,&a,0,-1,fd,0);if(child<0){perror("instruction counter");return 3;}
        int raw[3];const uint64_t codes[]={0x22,0x21,0x20};
        a.type=PERF_TYPE_RAW;
        for(int j=0;j<3;++j){a.config=codes[j];raw[j]=syscall(__NR_perf_event_open,&a,0,-1,fd,0);if(raw[j]<0){perror("raw counter");return 3;}}
        for(int rep=0;rep<7;++rep)for(int kind=0;kind<2;++kind)for(int l=0;l<3;++l){
            uint64_t n=lengths[(l+rep)%3];
            struct {uint64_t count,enabled,running,cycles,instructions,user_cycles,supervisor_cycles,machine_cycles;} v={0};
            int rc=ioctl(fd,PERF_EVENT_IOC_RESET,PERF_IOC_FLAG_GROUP);
            rc|=ioctl(fd,PERF_EVENT_IOC_ENABLE,PERF_IOC_FLAG_GROUP);
            uint64_t result=kind?audit_syscall(n):audit_user(n);
            rc|=ioctl(fd,PERF_EVENT_IOC_DISABLE,PERF_IOC_FLAG_GROUP);
            ssize_t bytes=read(fd,&v,sizeof v);
            int valid=!rc&&bytes==sizeof v&&v.count==5&&v.cycles>0&&v.instructions>0&&v.user_cycles>0&&v.enabled>0&&v.enabled==v.running&&sched_getcpu()==0;
            valid&=kind?result==(uint64_t)getpid():result==n;
            printf("{\"exclude_kernel_requested\":%s,\"kind\":%d,\"repeat\":%d,\"iterations\":%"PRIu64",\"cycles\":%"PRIu64",\"instructions\":%"PRIu64",\"user_cycles\":%"PRIu64",\"supervisor_cycles\":%"PRIu64",\"machine_cycles\":%"PRIu64",\"enabled\":%"PRIu64",\"running\":%"PRIu64",\"output\":%"PRIu64",\"expected_user_loop_instructions\":%"PRIu64",\"valid\":%s}\n",
                excluded?"true":"false",kind,rep,n,v.cycles,v.instructions,v.user_cycles,v.supervisor_cycles,v.machine_cycles,v.enabled,v.running,result,3*n,valid?"true":"false");
            fflush(stdout);if(!valid)return 4;
        }
        for(int j=0;j<3;++j){close(raw[j]);}
        close(child);close(fd);
    }
    return 0;
}
