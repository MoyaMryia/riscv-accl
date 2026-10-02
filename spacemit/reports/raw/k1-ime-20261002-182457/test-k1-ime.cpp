#include "ggml.h"
#include "ime_kernels.h"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <pthread.h>
#include <sched.h>
#include <thread>
#include <vector>

extern "C" size_t spine_k1_ime_m4_test(int, size_t, const uint8_t *, const uint8_t *,
                                     const uint8_t *, float *, size_t, size_t, size_t, size_t);
static void require(bool ok, const char * why) {
    if (!ok) { fprintf(stderr, "FAIL: %s\n", why); exit(1); }
}
using Clock = std::chrono::steady_clock;
static double ms(Clock::time_point t) { return std::chrono::duration<double, std::milli>(Clock::now()-t).count(); }

struct Data {
    int bl, kb, n, m, ld;
    bool zp;
    std::vector<float> a, c;
    std::vector<uint8_t> qa, qb;
    static constexpr float guard = 12345.25f;
    Data(int block, int blocks, int cols, int rows, bool zero_point, int seed):
        bl(block), kb(blocks), n(cols), m(rows), ld(cols+13), zp(zero_point),
        a(4*block*blocks), c(64+7*ld, guard), qa(128+4*(block+4)*blocks, 0xa5),
        qb(128+((cols+15)/16)*blocks*(32+(zero_point?16:0)+8*block), 0xa5) {
        uint32_t state=42+seed;
        auto next=[&] { state=state*1664525u+1013904223u; return state; };
        for (auto & f:a) f=((int)(next()>>16)-32768)/32768.0f;
        auto * packed=qa.data()+64;
        if (m>=4) spacemit_kernels::ime1::quantize_a_4row_i8(bl,a.data(),bl*kb,packed);
        else spacemit_kernels::ime1::quantize_a_row_i8(bl,a.data(),bl*kb,packed);
        for (int tile=0;tile<(n+15)/16;++tile) for (int k=0;k<kb;++k) {
            auto * b=qb.data()+64+(tile*kb+k)*(32+(zp?16:0)+8*bl);
            for (int j=0;j<16;++j) {
                const auto h=ggml_fp32_to_fp16((j%3==0?-1.0f:1.0f)*(1u<<(j%4))/128);
                memcpy(b+2*j,&h,2);
            }
            if (zp) for (int j=0;j<16;++j) b[32+j]=next()%16;
            for (int j=0;j<8*bl;++j) b[32+(zp?16:0)+j]=next()>>24;
        }
    }
    size_t call(int mode) {
        return spine_k1_ime_m4_test(mode,bl,qa.data()+64,qb.data()+64,zp?qb.data()+64:nullptr,
                                   c.data()+32,m,n,kb,ld);
    }
    void check() {
        for (int i=0;i<32;++i) require(c[i]==guard,"output prefix guard");
        const int rows=m>=4?4:1;
        for (int r=0;r<7;++r) for (int col=0;col<ld;++col) {
            if (r>=rows || col>=n) require(c[32+r*ld+col]==guard,"output stride guard");
            else if (m<4 || n%16==0) require(std::isfinite(c[32+r*ld+col]),"nonfinite output");
        }
        for (int i=32+7*ld;i<(int)c.size();++i) require(c[i]==guard,"output suffix guard");
    }
};

struct Team {
    pthread_barrier_t barrier;
    std::vector<Data> data;
    std::vector<std::thread> threads;
    std::atomic<bool> quit{false};
    int mode=0, iterations=1;
    double times[4]{};
    int cpus[4]{};
    Team(int k,int n) {
        for (int i=0;i<4;++i) data.emplace_back(32,k/32,n,4,false,100+i);
        require(pthread_barrier_init(&barrier,nullptr,5)==0,"barrier");
        for (int i=0;i<4;++i) threads.emplace_back([&,i] {
            cpu_set_t set; CPU_ZERO(&set); CPU_SET(i,&set);
            require(pthread_setaffinity_np(pthread_self(),sizeof(set),&set)==0,"affinity");
            for (;;) {
                pthread_barrier_wait(&barrier);
                if (quit.load()) break;
                const auto start=Clock::now();
                for (int j=0;j<iterations;++j) data[i].call(mode);
                times[i]=ms(start); cpus[i]=sched_getcpu();
                pthread_barrier_wait(&barrier);
            }
        });
    }
    void run(int m,int it) { mode=m; iterations=it; pthread_barrier_wait(&barrier); pthread_barrier_wait(&barrier); }
    ~Team() { quit.store(true); pthread_barrier_wait(&barrier); for(auto & t:threads)t.join(); pthread_barrier_destroy(&barrier); }
};

int main(int argc,char ** argv) {
    if (argc>2 && strcmp(argv[1],"--bench")==0) {
        const int order[8][4]={{0,1,2,3},{3,2,1,0},{1,0,3,2},{2,3,0,1},
                              {2,1,0,3},{3,0,1,2},{0,3,2,1},{1,2,3,0}};
        for (int ki=2;ki<argc;++ki) for (int n:{16,32}) {
            const int k=atoi(argv[ki]); require(k>0 && k%32==0,"K shape"); Team team(k,n);
            for (int block=0;block<8;++block) for (int mode:order[block]) {
                team.run(mode,1); int it=1;
                do {
                    team.run(mode,it);
                    if (*std::max_element(team.times,team.times+4)>=50) break;
                    it*=2; require(it<=1048576,"calibration limit");
                } while(true);
                for(auto & d:team.data)d.check();
                printf("{\"block\":%d,\"mode\":%d,\"k\":%d,\"n\":%d,\"m\":4,\"iterations\":%d,"
                       "\"slowest_ms\":%.9f,\"ms_per_call\":%.9f,\"cpus\":[%d,%d,%d,%d]}\n",
                       block,mode,k,n,it,*std::max_element(team.times,team.times+4),
                       *std::max_element(team.times,team.times+4)/it,team.cpus[0],team.cpus[1],team.cpus[2],team.cpus[3]);
                fflush(stdout);
            }
        }
        return 0;
    }
    require(argc==1,"usage: test-ime [--bench K ...]");
    int cases=0;
    for(int bl:{32,64}) for(int kb:{1,2,7,64}) for(int n:{1,15,16,17,32,48})
        for(int m:{1,4,7}) for(bool zp:{false,true}) {
            Data control(bl,kb,n,m,zp,cases), candidate=control;
            auto processed=control.call(0); control.check();
            for(int mode:{1,2,3}) {
                candidate=Data(bl,kb,n,m,zp,cases);
                const auto a=candidate.qa, b=candidate.qb;
                require(candidate.call(mode)==processed,"processed rows"); candidate.check();
                require(candidate.qa==a && candidate.qb==b,"input overwritten");
                require(memcmp(control.c.data(),candidate.c.data(),control.c.size()*sizeof(float))==0,"output differs bitwise");
            }
            ++cases;
        }
    printf("PASS: %d cases; three modes bitwise equal; input/stride guards intact\n",cases);
}
