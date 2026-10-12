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
typedef uint64_t (*Function)(uint64_t,void *,void *);
static struct {const char *id;Function fn;int kind,chains,operations,sew,lmul,vl,footprint,output_bytes;} kernels[]={
/* TABLE */
};

static long frequency(void) {
    FILE *f=fopen("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq","r");
    long value=-1;
    if(f){if(fscanf(f,"%ld",&value)!=1)value=-1;fclose(f);}
    return value;
}

static uint64_t power(uint64_t base,uint64_t n) {
    uint64_t value=1;
    while(n){if(n&1)value*=base;base*=base;n>>=1;}
    return value;
}

int main(void) {
    cpu_set_t cpus;CPU_ZERO(&cpus);CPU_SET(0,&cpus);
    if(sched_setaffinity(0,sizeof cpus,&cpus))return 2;
    struct perf_event_attr attr={0};attr.size=sizeof attr;attr.type=PERF_TYPE_RAW;
    attr.config=0x22;attr.disabled=1;attr.exclude_kernel=1;attr.exclude_hv=1;
    attr.read_format=PERF_FORMAT_TOTAL_TIME_ENABLED|PERF_FORMAT_TOTAL_TIME_RUNNING;
    int fd=syscall(__NR_perf_event_open,&attr,0,-1,-1,0);
    if(fd<0){fprintf(stderr,"perf errno=%d\n",errno);return 3;}
    void *data=NULL; if(posix_memalign(&data,64,8388608))return 4;
    uint32_t *order=malloc(131072*sizeof(uint32_t));if(!order)return 4;
    const uint64_t lengths[]={512,2048,8192};
    /* 全局轮次交换内核顺序，保留全部测量值。 */
    for(int rep=0;rep<7;++rep)for(size_t offset=0;offset<sizeof kernels/sizeof kernels[0];++offset) {
        size_t k=rep%2 ? sizeof kernels/sizeof kernels[0]-1-offset : offset;
        const int kind=kernels[k].kind,chains=kernels[k].chains,ops=kernels[k].operations;
        int nodes=kernels[k].footprint/64;
        void *input=data;
        if(kind==9){
            for(int i=0;i<nodes;++i)order[i]=(uint32_t)i;
            uint32_t rng=42;
            for(int i=nodes-1;i>0;--i){rng=rng*1664525u+1013904223u;int j=rng%(i+1);uint32_t v=order[i];order[i]=order[j];order[j]=v;}
            for(int i=0;i<nodes;++i)*(void **)((char *)data+order[i]*64)=(char *)data+order[(i+1)%nodes]*64;
            input=(char *)data+order[0]*64;
        }else if(kind==13){memset(data,1,4096);}
        else{for(int i=0;i<1024;++i)((float *)data)[i]=1.0f;}
        uint8_t output[2176] __attribute__((aligned(64)));
        memset(output,0xa5,sizeof output);
        volatile uint64_t warm=kernels[k].fn(8192,input,output+64);(void)warm;
        for(int l=0;l<3;++l){
            uint64_t n=lengths[(l+rep)%3];
            memset(output,0xa5,sizeof output);
            struct rusage before,after;getrusage(RUSAGE_THREAD,&before);
            long freq_before=frequency();
            struct {uint64_t cycles,enabled,running;} sample={0};
            int rc=ioctl(fd,PERF_EVENT_IOC_RESET,0);rc|=ioctl(fd,PERF_EVENT_IOC_ENABLE,0);
            uint64_t value=kernels[k].fn(n,input,output+64);
            uint64_t checksum=UINT64_C(14695981039346656037);
            for(int i=0;i<kernels[k].output_bytes;++i)checksum=(checksum^((volatile uint8_t *)output)[64+i])*UINT64_C(1099511628211);
            rc|=ioctl(fd,PERF_EVENT_IOC_DISABLE,0);
            ssize_t size=read(fd,&sample,sizeof sample);
            long freq_after=frequency();getrusage(RUSAGE_THREAD,&after);
            int valid=!rc&&size==sizeof sample&&sample.cycles>0&&sample.enabled==sample.running&&sample.enabled>0&&sched_getcpu()==0;
            uint64_t expected=kind==9 ? (uintptr_t)((char *)data+order[(n*ops)%nodes]*64) : n;
            valid&=value==expected;
            for(int i=0;i<64;++i)valid&=output[i]==0xa5&&output[64+kernels[k].output_bytes+i]==0xa5;
            if(kind>=1&&kind<=8){
                for(int c=0;c<chains;++c)for(int lane=0;lane<kernels[k].vl;++lane){
                    const uint8_t *p=output+64+c*32*kernels[k].lmul+lane*kernels[k].sew/8;
                    if(kind<=3||kind==7||kind==8){float actual;memcpy(&actual,p,4);float want=kind==3||kind>=7 ? 1.0f : (float)(n*ops/chains);valid&=actual==want;}
                    else{uint32_t actual=0;memcpy(&actual,p,kernels[k].sew/8);uint32_t mask=kernels[k].sew==32 ? UINT32_MAX : (1u<<kernels[k].sew)-1;uint32_t want=kind==4 ? (uint32_t)(n*ops/chains)&mask : kind==5 ? 15 : 0;valid&=actual==want;}
                }
            }else if(kind==14||kind==15){
                for(int c=0;c<chains;++c){float actual;memcpy(&actual,output+64+c*32*kernels[k].lmul,4);valid&=actual==(float)(n*ops/chains*kernels[k].vl);}
            }else if(kind==13){
                for(int c=0;c<chains;++c)for(int lane=0;lane<16;++lane){int32_t actual;memcpy(&actual,output+64+c*64+lane*4,4);valid&=actual==(int32_t)(n*ops/chains*8);}
            }else if(kind>=10){
                for(int c=0;c<chains;++c){uint64_t actual;memcpy(&actual,output+64+c*8,8);uint64_t steps=n*ops/chains;
                    uint64_t want=kind==10 ? 1+steps : kind==11 ? (1^((steps&1)?3:0)) : power(3,steps);valid&=actual==want;}
            }
            printf("{\"id\":\"%s\",\"repeat\":%d,\"iterations\":%"PRIu64",\"cycles\":%"PRIu64",\"enabled\":%"PRIu64",\"running\":%"PRIu64",\"output\":%"PRIu64",\"expected\":%"PRIu64",\"checksum\":%"PRIu64",\"frequency_before_khz\":%ld,\"frequency_after_khz\":%ld,\"cpu\":%d,\"voluntary_switches\":%ld,\"involuntary_switches\":%ld,\"valid\":%s}\n",kernels[k].id,rep,n,sample.cycles,sample.enabled,sample.running,value,expected,checksum,freq_before,freq_after,sched_getcpu(),after.ru_nvcsw-before.ru_nvcsw,after.ru_nivcsw-before.ru_nivcsw,valid?"true":"false");
            fflush(stdout);if(!valid)return 5;
        }
    }
    close(fd);free(order);free(data);return 0;
}
