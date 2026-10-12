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
#include <unistd.h>

/* DECLARATIONS */
typedef uint64_t (*Function)(uint64_t, void *, void *);
static struct { const char *id, *group; Function fn; int arm,ops,m,vl,chains,split; } kernels[]={
/* TABLE */
};
static long frequency(void) {
    FILE *f=fopen("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq","r"); long v=-1;
    if(f){if(fscanf(f,"%ld",&v)!=1)v=-1;fclose(f);}return v;
}
static int execute(size_t k,uint64_t n,int fd,int rep,const char *dump) {
    float input[1056] __attribute__((aligned(64)));
    unsigned char output[768] __attribute__((aligned(64)));
    for(int i=0;i<1056;++i)input[i]=1.0f;
    memset(output,0xa5,sizeof output);
    long fb=-1,fa=-1;struct rusage before={0},after={0};
    struct {uint64_t cycles,enabled,running;} v={0};
    int rc=0;
    if(fd>=0){
        fb=frequency();getrusage(RUSAGE_THREAD,&before);
        rc|=ioctl(fd,PERF_EVENT_IOC_RESET,0);rc|=ioctl(fd,PERF_EVENT_IOC_ENABLE,0);
    }
    uint64_t result=kernels[k].fn(n,input+16,output+64);
    if(fd>=0){
        rc|=ioctl(fd,PERF_EVENT_IOC_DISABLE,0);
        if(read(fd,&v,sizeof v)!=sizeof v)return 6;
        fa=frequency();getrusage(RUSAGE_THREAD,&after);
    }
    int bytes=32*kernels[k].m*kernels[k].chains;
    int valid=result==n;
    for(int i=0;i<1056;++i)valid&=input[i]==1.0f;
    for(int i=0;i<64;++i)valid&=output[i]==0xa5&&output[64+bytes+i]==0xa5;
    for(int c=0;c<kernels[k].chains;++c)for(int j=0;j<kernels[k].vl;++j){
        float actual;memcpy(&actual,output+64+c*32*kernels[k].m+j*4,4);
        valid&=actual==(float)(n*kernels[k].ops/kernels[k].chains);
    }
    if(fd>=0)valid&=!rc&&v.cycles>0&&v.enabled>0&&v.enabled==v.running&&sched_getcpu()==0;
    if(!valid){fprintf(stderr,"FAIL: %s n=%"PRIu64"\n",kernels[k].id,n);return 5;}
    if(dump){
        FILE *f=fopen(dump,"wbx");if(!f)return 7;
        if(fwrite(input,1,sizeof input,f)!=sizeof input)return 7;
        if(fwrite(output,1,64,f)!=64)return 7;
        for(int c=0;c<kernels[k].chains;++c)
            if(fwrite(output+64+c*32*kernels[k].m,4,kernels[k].vl,f)!=(size_t)kernels[k].vl)return 7;
        if(fwrite(output+64+bytes,1,64,f)!=64||fclose(f))return 7;
        puts("PASS: active outputs, full input and guards");
    }else if(fd>=0){
        printf("{\"id\":\"%s\",\"group\":\"%s\",\"arm\":%d,\"unroll\":%d,\"repeat\":%d,\"iterations\":%"PRIu64",\"cycles\":%"PRIu64",\"enabled\":%"PRIu64",\"running\":%"PRIu64",\"output\":%"PRIu64",\"expected\":%"PRIu64",\"cpu\":0,\"frequency_before_khz\":%ld,\"frequency_after_khz\":%ld,\"involuntary_switches\":%ld,\"valid\":true}\n",
            kernels[k].id,kernels[k].group,kernels[k].arm,kernels[k].ops,rep,n,v.cycles,v.enabled,v.running,result,n,fb,fa,after.ru_nivcsw-before.ru_nivcsw);
        fflush(stdout);
    }
    return 0;
}
int main(int argc,char **argv) {
    size_t count=sizeof kernels/sizeof kernels[0];
    if(argc==5&&!strcmp(argv[1],"trace")){
        for(size_t k=0;k<count;++k)if(!strcmp(argv[2],kernels[k].id)){
            uint64_t n=strtoull(argv[3],NULL,10);
            if(!n||n>8192)return 2;
            return execute(k,n,-1,-1,argv[4]);
        }
        return 2;
    }
    if(argc!=3||strcmp(argv[1],"bench"))return 2;
    int split=!strcmp(argv[2],"calibration")?0:!strcmp(argv[2],"test")?1:-1;
    if(split<0)return 2;
    cpu_set_t cpus;CPU_ZERO(&cpus);CPU_SET(0,&cpus);
    if(sched_setaffinity(0,sizeof cpus,&cpus))return 2;
    struct perf_event_attr a={0};a.size=sizeof a;a.type=PERF_TYPE_RAW;a.config=0x22;
    a.disabled=1;a.exclude_kernel=1;a.exclude_hv=1;
    a.read_format=PERF_FORMAT_TOTAL_TIME_ENABLED|PERF_FORMAT_TOTAL_TIME_RUNNING;
    int fd=syscall(__NR_perf_event_open,&a,0,-1,-1,0);
    if(fd<0){fprintf(stderr,"perf errno=%d\n",errno);return 3;}
    const uint64_t lengths[]={512,2048,8192};
    for(int rep=0;rep<7;++rep)for(size_t offset=0;offset<count;++offset){
        size_t k=rep%2?count-1-offset:offset;if(kernels[k].split!=split)continue;
        if(execute(k,512,-1,-1,NULL))return 5;
        for(int l=0;l<3;++l){int result=execute(k,lengths[(l+rep)%3],fd,rep,NULL);if(result)return result;}
    }
    close(fd);return 0;
}
