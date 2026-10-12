// Measure memory patterns with one or four pinned workers.
#include <linux/perf_event.h>
#include <sys/ioctl.h>
#include <sys/resource.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <cstdint>
#include "common.h"

struct Counter {
    int fd=-1,child=-1;
    struct Value { uint64_t count,enabled,running,cycles,instructions; } value{};
    void open() {
        perf_event_attr a{};a.size=sizeof a;a.type=PERF_TYPE_RAW;a.config=0x22;
        a.disabled=1;a.exclude_kernel=1;a.exclude_hv=1;
        a.read_format=PERF_FORMAT_GROUP|PERF_FORMAT_TOTAL_TIME_ENABLED|PERF_FORMAT_TOTAL_TIME_RUNNING;
        fd=syscall(__NR_perf_event_open,&a,0,-1,-1,0);need(fd>=0,"cycle counter");
        a.type=PERF_TYPE_HARDWARE;a.config=PERF_COUNT_HW_INSTRUCTIONS;a.disabled=0;
        child=syscall(__NR_perf_event_open,&a,0,-1,fd,0);need(child>=0,"instruction counter");
    }
    void begin() {
        need(ioctl(fd,PERF_EVENT_IOC_RESET,PERF_IOC_FLAG_GROUP)==0,"counter reset");
        need(ioctl(fd,PERF_EVENT_IOC_ENABLE,PERF_IOC_FLAG_GROUP)==0,"counter enable");
    }
    void end() {
        need(ioctl(fd,PERF_EVENT_IOC_DISABLE,PERF_IOC_FLAG_GROUP)==0,"counter disable");
        need(read(fd,&value,sizeof value)==sizeof value,"counter read");
        need(value.count==2&&value.cycles>0&&value.instructions>0&&value.enabled==value.running,"counter coverage");
    }
    ~Counter(){if(child>=0)close(child);if(fd>=0)close(fd);}
};

static long frequency(int cpu) {
    char name[160];snprintf(name,sizeof name,"/sys/devices/system/cpu/cpu%d/cpufreq/scaling_cur_freq",cpu);
    FILE *f=fopen(name,"r");long v=-1;if(f){if(fscanf(f,"%ld",&v)!=1)v=-1;fclose(f);}return v;
}

struct Buffers {
    float *x=nullptr,*w=nullptr,*y=nullptr;size_t bytes=0;
    void allocate(size_t n) {
        bytes=n;
        need(posix_memalign((void **)&x,64,n+128)==0,"input allocation");
        need(posix_memalign((void **)&w,64,4*n+128)==0,"weight allocation");
        need(posix_memalign((void **)&y,64,n+128)==0,"output allocation");
        reset();
    }
    void reset() {
        std::fill(x,x+bytes/4+32,1.0f);std::fill(w,w+bytes+32,1.0f);
        std::fill(y,y+bytes/4+32,-123.0f);
    }
    void check(int mode) {
        for(size_t j=0;j<bytes/4+32;++j)need(x[j]==1.0f,"input identity");
        for(size_t j=0;j<bytes+32;++j)need(w[j]==1.0f,"weight identity");
        for(size_t j=0;j<bytes/4+32;++j) {
            bool active=j>=16&&j<16+bytes/4;
            need(y[j]==(active&&(mode==1||mode==2||mode==4)?1.0f:-123.0f),"output or guard");
        }
    }
    ~Buffers(){free(x);free(w);free(y);}
};

static __attribute__((noinline,noclone)) void stream(Buffers &b,int mode,int passes) {
    for(int pass=0;pass<passes;++pass) {
        const float *x=b.x+16,*w=b.w+16;float *y=b.y+16;size_t n=b.bytes/32;
        if(mode==0) {
            __asm__ volatile("li t6,8\n\tvsetvli zero,t6,e32,m1,ta,ma\n\t1:\n\tvle32.v v0,(%0)\n\taddi %0,%0,32\n\taddi %1,%1,-1\n\tbnez %1,1b\n\tvs1r.v v0,(%2)"
                : "+&r"(x),"+&r"(n) : "r"(y) : "t6","v0","memory");
        } else if(mode==1) {
            __asm__ volatile("li t6,8\n\tvsetvli zero,t6,e32,m1,ta,ma\n\tvle32.v v0,(%2)\n\t1:\n\tvse32.v v0,(%0)\n\taddi %0,%0,32\n\taddi %1,%1,-1\n\tbnez %1,1b"
                : "+&r"(y),"+&r"(n) : "r"(x) : "t6","v0","memory");
        } else if(mode==2) {
            __asm__ volatile("li t6,8\n\tvsetvli zero,t6,e32,m1,ta,ma\n\t1:\n\tvle32.v v0,(%0)\n\tvse32.v v0,(%1)\n\taddi %0,%0,32\n\taddi %1,%1,32\n\taddi %2,%2,-1\n\tbnez %2,1b"
                : "+&r"(x),"+&r"(y),"+&r"(n) : : "t6","v0","memory");
        } else if(mode==3) {
            __asm__ volatile("li t6,8\n\tvsetvli zero,t6,e32,m1,ta,ma\n\tli t6,16\n\t1:\n\tvlse32.v v0,(%0),t6\n\taddi %0,%0,128\n\taddi %1,%1,-1\n\tbnez %1,1b\n\tvs1r.v v0,(%2)"
                : "+&r"(w),"+&r"(n) : "r"(y) : "t6","v0","memory");
        } else {
            __asm__ volatile("li t6,8\n\tvsetvli zero,t6,e32,m1,ta,ma\n\tli t6,16\n\t1:\n\tvle32.v v0,(%0)\n\tvlse32.v v1,(%1),t6\n\tvfmul.vv v2,v0,v1\n\tvse32.v v2,(%2)\n\taddi %0,%0,32\n\taddi %1,%1,128\n\taddi %2,%2,32\n\taddi %3,%3,-1\n\tbnez %3,1b"
                : "+&r"(x),"+&r"(w),"+&r"(y),"+&r"(n) : : "t6","v0","v1","v2","memory");
        }
        __asm__ volatile("fence rw,rw" ::: "memory");
    }
}

int main() {
    Workers pool(true);std::array<Counter,4> counters;
    pool.run([&](int id){counters[id].open();});
    const size_t sizes[]={4096,32768,131072,524288,2097152,8388608};
    for(size_t size:sizes) {
        std::array<Buffers,4> buffers;pool.run([&](int id){buffers[id].allocate(size);});
        for(int active:{1,4}) for(int mode=0;mode<5;++mode) {
            int passes=1;
            for(;;) {
                double wall=pool.run([&](int id){if(id<active)stream(buffers[id],mode,passes);});
                if(wall>=25.0)break;need(passes<1048576,"pass limit");passes*=2;
            }
            std::array<long,4> fb{},fa{},switches{};
            for(int rep=0;rep<7;++rep) {
                pool.run([&](int id){buffers[id].reset();});
                double wall=pool.run([&](int id){
                    if(id>=active)return;
                    struct rusage before{},after{};getrusage(RUSAGE_THREAD,&before);fb[id]=frequency(id);
                    counters[id].begin();stream(buffers[id],mode,passes);counters[id].end();
                    fa[id]=frequency(id);getrusage(RUSAGE_THREAD,&after);switches[id]=after.ru_nivcsw-before.ru_nivcsw;
                    need(sched_getcpu()==id,"worker CPU identity");
                });
                for(int id=0;id<active;++id) {
                    if(mode==0||mode==3) {
                        for(int j=16;j<24;++j)need(buffers[id].y[j]==1.0f,"load result");
                        std::fill(buffers[id].y+16,buffers[id].y+24,-123.0f);
                    }
                    buffers[id].check(mode);
                }
                uint64_t payload=uint64_t(size)*passes*active*(mode==2?2:mode==4?3:1);
                printf("{\"schema\":3,\"mode\":%d,\"active_threads\":%d,\"span_bytes_per_buffer\":%zu,\"passes\":%d,\"repeat\":%d,\"wall_ms\":%.9f,\"payload_bytes\":%llu,\"threads\":[",mode,active,size,passes,rep,wall,(unsigned long long)payload);
                for(int id=0;id<active;++id) {
                    const auto &v=counters[id].value;
                    printf("%s{\"cpu\":%d,\"cycles\":%llu,\"instructions\":%llu,\"enabled\":%llu,\"running\":%llu,\"frequency_before_khz\":%ld,\"frequency_after_khz\":%ld,\"involuntary_switches\":%ld}",id?",":"",id,
                        (unsigned long long)v.cycles,(unsigned long long)v.instructions,(unsigned long long)v.enabled,(unsigned long long)v.running,fb[id],fa[id],switches[id]);
                }
                puts("],\"valid\":true}");fflush(stdout);
            }
        }
    }
    return 0;
}
