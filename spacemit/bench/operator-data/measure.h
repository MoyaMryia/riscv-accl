#pragma once
#include <linux/perf_event.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <sys/resource.h>
#include <unistd.h>
#include <sched.h>
#include <cstdint>
#include <ctime>

template<class T> static void operator_dump(FILE *file,const std::vector<T> &data) {
    require(fwrite(data.data(),sizeof(T),data.size(),file)==data.size(),"dump write");
}
static uint64_t operator_ns(clockid_t clock) {
    timespec t{};require(clock_gettime(clock,&t)==0,"clock read");
    return uint64_t(t.tv_sec)*1000000000+t.tv_nsec;
}
static long operator_frequency(int cpu) {
    char path[160];snprintf(path,sizeof(path),"/sys/devices/system/cpu/cpu%d/cpufreq/scaling_cur_freq",cpu);
    FILE *f=fopen(path,"r");long value=-1;
    if(f){if(fscanf(f,"%ld",&value)!=1)value=-1;fclose(f);}return value;
}
struct OperatorCounter {
    int fd=-1,insn=-1;
    struct {uint64_t count,enabled,running,cycles,instructions;} value{};
    void open() {
        if(fd>=0)return;
        perf_event_attr a{};a.size=sizeof(a);a.type=PERF_TYPE_RAW;a.config=0x22;
        a.disabled=1;a.exclude_kernel=1;a.exclude_hv=1;
        a.read_format=PERF_FORMAT_GROUP|PERF_FORMAT_TOTAL_TIME_ENABLED|PERF_FORMAT_TOTAL_TIME_RUNNING;
        fd=syscall(__NR_perf_event_open,&a,0,-1,-1,0);require(fd>=0,"user cycle event");
        a.type=PERF_TYPE_HARDWARE;a.config=PERF_COUNT_HW_INSTRUCTIONS;a.disabled=0;
        insn=syscall(__NR_perf_event_open,&a,0,-1,fd,0);require(insn>=0,"instruction event");
    }
    void begin(){require(ioctl(fd,PERF_EVENT_IOC_RESET,PERF_IOC_FLAG_GROUP)==0,"counter reset");require(ioctl(fd,PERF_EVENT_IOC_ENABLE,PERF_IOC_FLAG_GROUP)==0,"counter enable");}
    void end(){require(ioctl(fd,PERF_EVENT_IOC_DISABLE,PERF_IOC_FLAG_GROUP)==0,"counter disable");require(read(fd,&value,sizeof(value))==sizeof(value),"counter read");require(value.count==2 && value.enabled>0 && value.enabled==value.running && value.cycles>0 && value.instructions>0,"counter coverage");}
    ~OperatorCounter(){if(insn>=0)close(insn);if(fd>=0)close(fd);}
};
struct OperatorSample {
    uint64_t wall=0,cpu=0,wall_ns=0,cpu_ns=0;
    long before=-1,after=-1,voluntary=0,involuntary=0;
    rusage start{};
    void begin(int id){before=operator_frequency(id);getrusage(RUSAGE_THREAD,&start);wall=operator_ns(CLOCK_MONOTONIC);cpu=operator_ns(CLOCK_THREAD_CPUTIME_ID);}
    void end(int id){cpu_ns=operator_ns(CLOCK_THREAD_CPUTIME_ID)-cpu;wall_ns=operator_ns(CLOCK_MONOTONIC)-wall;after=operator_frequency(id);rusage finish{};getrusage(RUSAGE_THREAD,&finish);voluntary=finish.ru_nvcsw-start.ru_nvcsw;involuntary=finish.ru_nivcsw-start.ru_nivcsw;require(sched_getcpu()==id,"worker CPU");}
    void emit(int id,const OperatorCounter &counter) const {
        const auto &v=counter.value;
        printf("{\"cpu\":%d,\"cycles\":%llu,\"instructions\":%llu,\"enabled\":%llu,\"running\":%llu,\"wall_ns\":%llu,\"cpu_ns\":%llu,\"frequency_before_khz\":%ld,\"frequency_after_khz\":%ld,\"voluntary_switches\":%ld,\"involuntary_switches\":%ld}",id,(unsigned long long)v.cycles,(unsigned long long)v.instructions,(unsigned long long)v.enabled,(unsigned long long)v.running,(unsigned long long)wall_ns,(unsigned long long)cpu_ns,before,after,voluntary,involuntary);
    }
};
