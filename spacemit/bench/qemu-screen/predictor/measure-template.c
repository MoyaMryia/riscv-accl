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
static struct {const char *name; Function fn; int factor,kind,nodes;} kernels[] = {
/* TABLE */
};

static long frequency(void) {
    FILE *file = fopen("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq","r");
    long value = -1;
    if (file) { if (fscanf(file,"%ld",&value) != 1) value = -1; fclose(file); }
    return value;
}

int main(void) {
    cpu_set_t mask;
    CPU_ZERO(&mask); CPU_SET(0,&mask);
    if (sched_setaffinity(0,sizeof mask,&mask)) return 2;
    struct perf_event_attr attr = {0};
    attr.size = sizeof attr; attr.type = PERF_TYPE_RAW;
    attr.config = 0x22;
    attr.disabled = 1; attr.exclude_kernel = 1; attr.exclude_hv = 1;
    attr.read_format = PERF_FORMAT_TOTAL_TIME_ENABLED | PERF_FORMAT_TOTAL_TIME_RUNNING;
    int fd = syscall(__NR_perf_event_open,&attr,0,-1,-1,0);
    if (fd < 0) { printf("{\"error\":\"perf-open\",\"errno\":%d}\n",errno); return 3; }
    void *allocation = NULL;
    if (posix_memalign(&allocation,64,32768*sizeof(void *))) return 4;
    const uint64_t lengths[] = {1000,4000,16000};
    for (size_t k=0;k<sizeof kernels/sizeof kernels[0];++k) {
        void **nodes = allocation;
        if (kernels[k].kind==1) {
            for (int i=0;i<kernels[k].nodes;++i) nodes[i]=&nodes[(i+1)%kernels[k].nodes];
        } else {
            float *values = allocation;
            for (int i=0;i<16;++i) values[i]=1.0f;
        }
        uint32_t output[16] __attribute__((aligned(64))) = {0};
        volatile uint64_t warm = kernels[k].fn(32000,allocation,output);
        (void)warm;
        for (int rep=0;rep<5;++rep) for (int l=0;l<3;++l) {
            uint64_t n=lengths[(l+rep)%3], expected=n*kernels[k].factor;
            if (kernels[k].kind==1) expected=(uintptr_t)&nodes[(16*n)%kernels[k].nodes];
            /* 拆解输入的最低字节为 0，最终标量值等于循环次数。 */
            struct {uint64_t value,enabled,running;} sample = {0};
            struct rusage before,after;
            getrusage(RUSAGE_THREAD,&before);
            long freq_before = frequency();
            int rc=ioctl(fd,PERF_EVENT_IOC_RESET,0);
            rc |= ioctl(fd,PERF_EVENT_IOC_ENABLE,0);
            uint64_t value=kernels[k].fn(n,allocation,output), checksum=UINT64_C(14695981039346656037);
            for (int i=0;i<16;++i) checksum=(checksum ^ ((volatile uint32_t *)output)[i])*UINT64_C(1099511628211);
            rc |= ioctl(fd,PERF_EVENT_IOC_DISABLE,0);
            ssize_t size=read(fd,&sample,sizeof sample);
            long freq_after = frequency();
            getrusage(RUSAGE_THREAD,&after);
            int valid=!rc && size==sizeof sample && sample.value>0 && sample.enabled>0 &&
                sample.enabled==sample.running && value==expected && sched_getcpu()==0;
            printf("{\"id\":\"%s\",\"repeat\":%d,\"iterations\":%"PRIu64",\"cycles\":%"PRIu64",\"enabled\":%"PRIu64",\"running\":%"PRIu64",\"output\":%"PRIu64",\"expected\":%"PRIu64",\"vector_checksum\":%"PRIu64",\"cpu\":%d,\"frequency_before_khz\":%ld,\"frequency_after_khz\":%ld,\"voluntary_switches\":%ld,\"involuntary_switches\":%ld,\"valid\":%s}\n",
                kernels[k].name,rep,n,sample.value,sample.enabled,sample.running,value,expected,checksum,sched_getcpu(),freq_before,freq_after,
                after.ru_nvcsw-before.ru_nvcsw,after.ru_nivcsw-before.ru_nivcsw,valid ? "true":"false");
            fflush(stdout);
            if (!valid) {close(fd);free(allocation);return 5;}
        }
    }
    close(fd); free(allocation); return 0;
}
