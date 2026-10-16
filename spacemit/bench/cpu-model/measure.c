#define _GNU_SOURCE
#include <errno.h>
#include <inttypes.h>
#include <linux/perf_event.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/resource.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

/* DECLARATIONS */
/* REFERENCES */
typedef uint64_t (*Function)(uint64_t,void *,void *);
typedef void (*Reference)(uint64_t,unsigned char *);
static const struct {const char *id,*group,*split; Function fn; Reference ref;} kernels[]={
/* TABLE */
};
static long frequency(void) {
    FILE *f=fopen("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq","r");long value=-1;
    if(f){if(fscanf(f,"%ld",&value)!=1)value=-1;fclose(f);}return value;
}
static uint64_t ns(clockid_t clock) {
    struct timespec value;if(clock_gettime(clock,&value)){perror("clock");exit(8);}
    return (uint64_t)value.tv_sec*1000000000+value.tv_nsec;
}
static int execute(size_t k,uint64_t n,int fd,int rep,const char *directory) {
    unsigned char input[192] __attribute__((aligned(64)));
    unsigned char output[576] __attribute__((aligned(64)));
    unsigned char expected[576];
    memset(input,1,sizeof input);memset(output,0xa5,sizeof output);memset(expected,0xa5,sizeof expected);
    kernels[k].ref(n,expected+64);
    struct {uint64_t cycles,enabled,running;} v={0};
    struct rusage before={0},after={0};
    long fb=frequency();getrusage(RUSAGE_THREAD,&before);
    uint64_t wall=ns(CLOCK_MONOTONIC_RAW),cpu=ns(CLOCK_THREAD_CPUTIME_ID);
    int rc=0;
    if(fd>=0){rc|=ioctl(fd,PERF_EVENT_IOC_RESET,0);rc|=ioctl(fd,PERF_EVENT_IOC_ENABLE,0);}
    uint64_t result=kernels[k].fn(n,input+64,output+64);
    if(fd>=0){rc|=ioctl(fd,PERF_EVENT_IOC_DISABLE,0);if(read(fd,&v,sizeof v)!=sizeof v)return 6;}
    cpu=ns(CLOCK_THREAD_CPUTIME_ID)-cpu;wall=ns(CLOCK_MONOTONIC_RAW)-wall;
    getrusage(RUSAGE_THREAD,&after);long fa=frequency();
    int valid=result==n&&!memcmp(output,expected,sizeof output);
    for(size_t j=0;j<sizeof input;++j)valid&=input[j]==1;
    if(fd>=0)valid&=!rc&&v.cycles>0&&v.enabled==v.running&&v.enabled>0&&sched_getcpu()==0;
    if(!valid){fprintf(stderr,"FAIL %s n=%"PRIu64"\n",kernels[k].id,n);return 5;}
    if(directory){
        char path[4096];if(snprintf(path,sizeof path,"%s/%s-%"PRIu64".bin",directory,kernels[k].id,n)>=(int)sizeof path)return 7;
        FILE *f=fopen(path,"wbx");if(!f)return 7;
        if(fwrite(input,1,sizeof input,f)!=sizeof input||fwrite(output,1,sizeof output,f)!=sizeof output||fclose(f))return 7;
    }else if(fd>=0){
        printf("{\"id\":\"%s\",\"group\":\"%s\",\"split\":\"%s\",\"repeat\":%d,\"iterations\":%"PRIu64",\"cycles\":%"PRIu64",\"enabled\":%"PRIu64",\"running\":%"PRIu64",\"wall_ns\":%"PRIu64",\"thread_cpu_ns\":%"PRIu64",\"frequency_before_khz\":%ld,\"frequency_after_khz\":%ld,\"involuntary_switches\":%ld,\"voluntary_switches\":%ld,\"cpu\":0,\"valid\":true}\n",kernels[k].id,kernels[k].group,kernels[k].split,rep,n,v.cycles,v.enabled,v.running,wall,cpu,fb,fa,after.ru_nivcsw-before.ru_nivcsw,after.ru_nvcsw-before.ru_nvcsw);
        fflush(stdout);
    }
    return 0;
}
int main(int argc,char **argv) {
    size_t count=sizeof kernels/sizeof kernels[0];
    if(argc==4&&!strcmp(argv[1],"check")){
        for(size_t k=0;k<count;++k)if(!strcmp(argv[2],"all")||!strcmp(argv[2],kernels[k].split)){
            if(execute(k,3,-1,-1,argv[3])||execute(k,17,-1,-1,argv[3]))return 5;
        }
        return 0;
    }
    if(argc!=3||strcmp(argv[1],"bench"))return 2;
    if(strcmp(argv[2],"training")&&strcmp(argv[2],"calibration")&&strcmp(argv[2],"test"))return 2;
    cpu_set_t cpus;CPU_ZERO(&cpus);CPU_SET(0,&cpus);if(sched_setaffinity(0,sizeof cpus,&cpus))return 2;
    struct perf_event_attr a={0};a.size=sizeof a;a.type=PERF_TYPE_RAW;a.config=0x22;
    a.disabled=1;a.exclude_kernel=1;a.exclude_hv=1;
    a.read_format=PERF_FORMAT_TOTAL_TIME_ENABLED|PERF_FORMAT_TOTAL_TIME_RUNNING;
    int fd=syscall(__NR_perf_event_open,&a,0,-1,-1,0);if(fd<0){perror("perf");return 3;}
    const uint64_t lengths[]={8192,32768,131072};
    for(int rep=0;rep<9;++rep)for(size_t offset=0;offset<count;++offset){
        size_t k=rep%2?count-1-offset:offset;if(strcmp(argv[2],kernels[k].split))continue;
        if(execute(k,128,-1,-1,NULL))return 5;
        for(int l=0;l<3;++l){int status=execute(k,lengths[(l+rep)%3],fd,rep,NULL);if(status)return status;}
    }
    close(fd);return 0;
}
