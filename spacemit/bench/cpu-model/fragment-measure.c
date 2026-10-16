#define _GNU_SOURCE
#include "fragment-fixture.h"
#include <errno.h>
#include <inttypes.h>
#include <linux/perf_event.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/resource.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

static volatile uint64_t sink;
static uint64_t now(clockid_t clock) {
    struct timespec t;
    if(clock_gettime(clock,&t)) { perror("clock"); exit(8); }
    return (uint64_t)t.tv_sec*1000000000+(uint64_t)t.tv_nsec;
}
static long frequency(void) {
    long result=-1;
    FILE *f=fopen("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq","r");
    if(f) { if(fscanf(f,"%ld",&result)!=1) result=-1; fclose(f); }
    return result;
}
static void *buffer(size_t bytes) {
    void *p=NULL;
    if(bytes>SIZE_MAX-192 || posix_memalign(&p,64,bytes+192)) exit(8);
    memset(p,0xa5,bytes+192);
    return p;
}
static void initialize(uint8_t *p,size_t bytes,unsigned seed) {
    uint64_t state=UINT64_C(0x9e3779b97f4a7c15) ^ seed;
    for(size_t i=0;i<bytes;i++) {
        state^=state<<13; state^=state>>7; state^=state<<17;
        p[i]=seed==0 ? (uint8_t)i : (uint8_t)state;
    }
}
__attribute__((noinline,noclone))
void fragment_repeat(void (*function)(const uint8_t *,uint8_t *,size_t),
                     const uint8_t *input,uint8_t *output,size_t work,uint64_t count) {
    for(uint64_t i=0;i<count;i++) function(input,output,work);
}
static int check(size_t ci,size_t ki,unsigned seed,const char *dump,uint64_t repeats) {
    const struct fragment_case *c=&fragment_cases[ci];
    uint8_t *ib=buffer(c->input_bytes),*ob=buffer(c->output_bytes),*rb=buffer(c->output_bytes);
    uint8_t *input=ib+64+c->offset,*output=ob+64+c->offset,*reference=rb+64+c->offset;
    initialize(input,c->input_bytes,seed);
    fragment_reference(input,reference,c->work_units);
    if(repeats) fragment_repeat(fragment_kernels[ki].function,input,output,c->work_units,repeats);
    else fragment_kernels[ki].function(input,output,c->work_units);
    int valid=!memcmp(ob,rb,c->output_bytes+192);
    uint8_t *copy=buffer(c->input_bytes);
    initialize(copy+64+c->offset,c->input_bytes,seed);
    valid&=!memcmp(ib,copy,c->input_bytes+192);
    if(!valid) { fprintf(stderr,"numerical failure: %s %s seed=%u\n",c->id,fragment_kernels[ki].id,seed); return 5; }
    if(dump) {
        FILE *f=fopen(dump,"wbx");
        if(!f) return 7;
        if(fwrite(ib,1,c->input_bytes+192,f)!=c->input_bytes+192 ||
           fwrite(ob,1,c->output_bytes+192,f)!=c->output_bytes+192 || fclose(f)) return 7;
    }
    free(ib);free(ob);free(rb);free(copy);
    return 0;
}
static uint64_t calls(size_t ci,size_t ki,uint64_t count,uint8_t *input,uint8_t *output) {
    const struct fragment_case *c=&fragment_cases[ci];
    uint64_t start=now(CLOCK_MONOTONIC_RAW);
    fragment_repeat(fragment_kernels[ki].function,input,output,c->work_units,count);
    uint64_t elapsed=now(CLOCK_MONOTONIC_RAW)-start;
    sink+=output[0]+output[c->output_bytes-1];
    return elapsed;
}
static int bench(void) {
    cpu_set_t cpus;CPU_ZERO(&cpus);CPU_SET(0,&cpus);
    if(sched_setaffinity(0,sizeof cpus,&cpus)) return 2;
    struct perf_event_attr a={0};a.size=sizeof a;a.type=PERF_TYPE_RAW;a.config=0x22;
    a.disabled=1;a.exclude_kernel=1;a.exclude_hv=1;
    a.read_format=PERF_FORMAT_TOTAL_TIME_ENABLED|PERF_FORMAT_TOTAL_TIME_RUNNING;
    int fd=syscall(__NR_perf_event_open,&a,0,-1,-1,0);
    if(fd<0) { perror("perf"); return 3; }
    for(size_t ci=0;ci<fragment_case_count;ci++) {
        const struct fragment_case *c=&fragment_cases[ci];
        uint8_t *ib=buffer(c->input_bytes),*ob=buffer(c->output_bytes);
        uint8_t *input=ib+64+c->offset,*output=ob+64+c->offset;
        initialize(input,c->input_bytes,17);
        uint64_t base=1;
        for(;;) {
            uint64_t minimum=UINT64_MAX;
            for(size_t ki=0;ki<fragment_kernel_count;ki++) {
                uint64_t elapsed=calls(ci,ki,base,input,output);
                if(elapsed<minimum) minimum=elapsed;
            }
            if(minimum>=10000000) break;
            if(base>=1048576) { fprintf(stderr,"pilot count limit\n"); return 9; }
            base*=2;
        }
        fprintf(stderr,"pilot %s base=%"PRIu64"\n",c->id,base);
        for(unsigned rep=0;rep<5;rep++) for(unsigned level=0;level<3;level++) {
            uint64_t count=base*(UINT64_C(1)<<level);
            for(size_t order=0;order<fragment_kernel_count;order++) {
                size_t ki=(order+rep+level)%fragment_kernel_count;
                struct rusage before,after;getrusage(RUSAGE_THREAD,&before);
                long fb=frequency();
                struct {uint64_t value,enabled,running;} cycles={0};
                if(ioctl(fd,PERF_EVENT_IOC_RESET,0) || ioctl(fd,PERF_EVENT_IOC_ENABLE,0)) return 6;
                uint64_t cpu=now(CLOCK_THREAD_CPUTIME_ID);
                uint64_t wall=calls(ci,ki,count,input,output);
                cpu=now(CLOCK_THREAD_CPUTIME_ID)-cpu;
                if(ioctl(fd,PERF_EVENT_IOC_DISABLE,0) || read(fd,&cycles,sizeof cycles)!=sizeof cycles) return 6;
                long fa=frequency();getrusage(RUSAGE_THREAD,&after);
                if(!cycles.value || !cycles.enabled || cycles.enabled!=cycles.running || sched_getcpu()!=0) return 6;
                printf("{\"case\":\"%s\",\"kernel\":\"%s\",\"repeat\":%u,\"calls\":%"PRIu64",\"work_units\":%zu,\"wall_ns\":%"PRIu64",\"thread_cpu_ns\":%"PRIu64",\"cycles\":%"PRIu64",\"enabled\":%"PRIu64",\"running\":%"PRIu64",\"cpu\":0,\"frequency_before_khz\":%ld,\"frequency_after_khz\":%ld,\"voluntary_switches\":%ld,\"involuntary_switches\":%ld}\n",
                       c->id,fragment_kernels[ki].id,rep,count,c->work_units,wall,cpu,cycles.value,cycles.enabled,cycles.running,fb,fa,
                       after.ru_nvcsw-before.ru_nvcsw,after.ru_nivcsw-before.ru_nivcsw);
                fflush(stdout);
            }
        }
        free(ib);free(ob);
    }
    close(fd);return 0;
}
int main(int argc,char **argv) {
    if(argc==2 && !strcmp(argv[1],"bench")) return bench();
    if(argc==7 && !strcmp(argv[1],"check")) {
        size_t ci=strtoul(argv[2],NULL,10),ki=strtoul(argv[3],NULL,10);
        unsigned seed=(unsigned)strtoul(argv[4],NULL,10);
        if(ci>=fragment_case_count || ki>=fragment_kernel_count || strcmp(argv[6],"exact")) return 2;
        return check(ci,ki,seed,argv[5],0);
    }
    if(argc==8 && !strcmp(argv[1],"trace")) {
        size_t ci=strtoul(argv[2],NULL,10),ki=strtoul(argv[3],NULL,10);
        unsigned seed=(unsigned)strtoul(argv[4],NULL,10);
        uint64_t repeats=strtoull(argv[5],NULL,10);
        if(ci>=fragment_case_count || ki>=fragment_kernel_count || !repeats || repeats>64 || strcmp(argv[7],"exact")) return 2;
        return check(ci,ki,seed,argv[6],repeats);
    }
    if(argc==3 && !strcmp(argv[1],"check-all")) {
        const unsigned seeds[]={0,1,17};
        for(size_t ci=0;ci<fragment_case_count;ci++) for(size_t ki=0;ki<fragment_kernel_count;ki++) for(size_t si=0;si<3;si++) {
            char path[4096];
            if(snprintf(path,sizeof path,"%s/%s-%s-seed%u.bin",argv[2],fragment_cases[ci].id,fragment_kernels[ki].id,seeds[si])>=(int)sizeof path) return 7;
            int rc=check(ci,ki,seeds[si],path,0);if(rc) return rc;
        }
        return 0;
    }
    return 2;
}
