// Use one binary for native samples and guest traces.
#include <linux/perf_event.h>
#include <sys/ioctl.h>
#include <sys/resource.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <cstdint>
#include <ctime>
#include "matched-common.h"
#define main unused_quick_main
#include "conv-kernel.cpp"
#undef main

struct Counter {
    int fd = -1, instructions = -1;
    struct Value { uint64_t count, enabled, running, cycles, retired; } value{};
    void open() {
        perf_event_attr a{}; a.size=sizeof a; a.type=PERF_TYPE_RAW;
        a.config=0x22; a.disabled=1; a.exclude_kernel=1; a.exclude_hv=1;
        a.read_format=PERF_FORMAT_GROUP|PERF_FORMAT_TOTAL_TIME_ENABLED|PERF_FORMAT_TOTAL_TIME_RUNNING;
        fd=syscall(__NR_perf_event_open,&a,0,-1,-1,0); need(fd>=0,"cycle counter");
        a.type=PERF_TYPE_HARDWARE; a.config=PERF_COUNT_HW_INSTRUCTIONS; a.disabled=0;
        instructions=syscall(__NR_perf_event_open,&a,0,-1,fd,0); need(instructions>=0,"instruction counter");
    }
    void begin() {
        need(ioctl(fd,PERF_EVENT_IOC_RESET,PERF_IOC_FLAG_GROUP)==0,"counter reset");
        need(ioctl(fd,PERF_EVENT_IOC_ENABLE,PERF_IOC_FLAG_GROUP)==0,"counter enable");
    }
    void end() {
        need(ioctl(fd,PERF_EVENT_IOC_DISABLE,PERF_IOC_FLAG_GROUP)==0,"counter disable");
        need(read(fd,&value,sizeof value)==sizeof value,"counter read");
        need(value.count==2 && value.cycles>0 && value.retired>0 && value.enabled>0 &&
             value.enabled==value.running,"counter coverage");
    }
    ~Counter() { if(instructions>=0) close(instructions); if(fd>=0) close(fd); }
};

static long frequency(int cpu) {
    char path[160]; snprintf(path,sizeof path,"/sys/devices/system/cpu/cpu%d/cpufreq/scaling_cur_freq",cpu);
    FILE *f=fopen(path,"r"); long n=-1;
    if(f) { if(fscanf(f,"%ld",&n)!=1) n=-1; fclose(f); } return n;
}

static void dump(const Conv &f,const char *path) {
    FILE *file=fopen(path,"wbx"); need(file,"dump file");
    for(const auto *v:{&f.history,&f.input,&f.weights,&f.output,&f.state})
        need(fwrite(v->data(),sizeof(float),v->size(),file)==v->size(),"dump write");
    need(fclose(file)==0,"dump close");
}

int main(int argc,char **argv) {
    need(argc==6,"usage: matched trace|bench|bench-roi CHANNELS TOKENS ARM|REPEATS DUMP");
    bool roi=strcmp(argv[1],"bench-roi")==0;
    bool bench=strcmp(argv[1],"bench")==0 || roi;
    need(bench || strcmp(argv[1],"trace")==0,"mode");
    int c=atoi(argv[2]),t=atoi(argv[3]),choice=atoi(argv[4]);
    need(c>=4 && c<=16384 && t>=1 && t<=128,"shape");
    need(bench ? choice>=2 && choice<=31 : choice==0 || choice==1,"arm or repeats");
    Workers pool(bench); Conv f(c,t,1,0),original=f;
    std::vector<float> expected,tail; f.scalar(expected,tail);
    if(!bench) {
        pool.run([&](int id){f.step(pool,id,choice);}); f.check(original,expected,tail);
        dump(f,argv[5]); puts("PASS: full output, state, inputs and guards"); return 0;
    }
    std::array<Counter,4> counters;
    pool.run([&](int id){counters[id].open();});
    int base=1;
    for(;;) {
        double elapsed=pool.run([&](int id){for(int j=0;j<base;++j) f.step(pool,id,0);});
        f.check(original,expected,tail); if(elapsed>=50.0 && base>=2) break;
        need(base<65536,"call limit"); base*=2;
    }
    struct Sample { int cpu; long freq_before,freq_after,voluntary,involuntary; uint64_t wall_ns,cpu_ns; SyncStats sync; };
    std::array<Sample,4> samples{};
    auto run=[&](int arm,int calls,bool phases) {
        return pool.run([&](int id){
            auto &s=samples[id]; auto &counter=counters[id]; struct rusage before{},after{};
            sync_stats={}; sync_measure=phases;
            sync_counter_fd=roi?counter.fd:-1;
            getrusage(RUSAGE_THREAD,&before); s.freq_before=frequency(id);
            uint64_t wall=matched_ns(CLOCK_MONOTONIC),cpu=matched_ns(CLOCK_THREAD_CPUTIME_ID);
            counter.begin();
            for(int j=0;j<calls;++j) f.step(pool,id,arm);
            counter.end();
            sync_counter_fd=-1;
            s.cpu_ns=matched_ns(CLOCK_THREAD_CPUTIME_ID)-cpu; s.wall_ns=matched_ns(CLOCK_MONOTONIC)-wall;
            s.cpu=sched_getcpu(); s.freq_after=frequency(id); getrusage(RUSAGE_THREAD,&after);
            s.voluntary=after.ru_nvcsw-before.ru_nvcsw; s.involuntary=after.ru_nivcsw-before.ru_nivcsw;
            s.sync=sync_stats; sync_measure=false;
            need(s.cpu==id,"worker CPU identity");
            if(phases) need(s.sync.count==uint64_t(calls*(arm==0?2:1)),"barrier call count");
        });
    };
    auto emit=[&](int arm,int calls,int rep,int length,bool phases,double wall) {
        printf("{\"schema\":3,\"counter_scope\":\"%s\",\"workload\":\"conv-C%d-T%d\",\"arm\":%d,\"repeat\":%d,\"length\":%d,\"calls\":%d,\"phases\":%s,\"wall_ms\":%.9f,\"threads\":[",roi?"sync-paused-user-cycles":"full-call-user-cycles",c,t,arm,rep,length,calls,phases?"true":"false",wall);
        for(int id=0;id<4;++id) {
            const auto &s=samples[id]; const auto &v=counters[id].value;
            printf("%s{\"cpu\":%d,\"cycles\":%llu,\"instructions\":%llu,\"enabled\":%llu,\"running\":%llu,\"wall_ns\":%llu,\"cpu_ns\":%llu,\"frequency_before_khz\":%ld,\"frequency_after_khz\":%ld,\"voluntary_switches\":%ld,\"involuntary_switches\":%ld,\"barrier_calls\":%llu,\"barrier_wall_ns\":%llu,\"barrier_cpu_ns\":%llu}",
                id?",":"",s.cpu,(unsigned long long)v.cycles,(unsigned long long)v.retired,
                (unsigned long long)v.enabled,(unsigned long long)v.running,(unsigned long long)s.wall_ns,
                (unsigned long long)s.cpu_ns,s.freq_before,s.freq_after,s.voluntary,s.involuntary,
                (unsigned long long)s.sync.count,(unsigned long long)s.sync.wall_ns,(unsigned long long)s.sync.cpu_ns);
        }
        puts("],\"valid\":true}"); fflush(stdout);
    };
    const int lengths[]={base/2,base,base*2};
    for(int rep=0;rep<choice;++rep) for(int l=0;l<3;++l) for(int a=0;a<2;++a) {
        int arm=(a+rep+l)%2,calls=lengths[(l+rep)%3];
        pool.run([&](int id){f.step(pool,id,arm);});
        double wall=run(arm,calls,false); f.check(original,expected,tail);
        emit(arm,calls,rep,(l+rep)%3,false,wall);
    }
    for(int arm:{0,1}) {
        double wall=run(arm,base,true); f.check(original,expected,tail);
        emit(arm,base,-1,1,true,wall);
    }
    dump(f,argv[5]); return 0;
}
