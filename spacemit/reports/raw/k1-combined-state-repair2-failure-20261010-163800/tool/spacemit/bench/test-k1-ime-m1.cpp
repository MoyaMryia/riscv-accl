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

extern "C" size_t spine_k1_ime_m1_test(int, size_t, const uint8_t *, const uint8_t *,
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
        else {
            // The production one-row helper hardcodes K32 packing. Construct
            // valid generic row blocks here to exercise the K64 fallback too.
            for (int k=0;k<kb;++k) {
                float peak=0;
                for (int j=0;j<bl;++j) peak=std::max(peak,std::fabs(a[k*bl+j]));
                const float scale=peak/127.0f;
                memcpy(packed+k*(bl+4),&scale,4);
                for (int j=0;j<bl;++j) {
                    const int8_t q=(int8_t)std::nearbyint(a[k*bl+j]/scale);
                    memcpy(packed+k*(bl+4)+4+j,&q,1);
                }
            }
        }
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
        return spine_k1_ime_m1_test(mode,bl,qa.data()+64,qb.data()+64,zp?qb.data()+64:nullptr,
                                   c.data()+32,m,n,kb,ld);
    }
    void check(int mode=0) {
        for (int i=0;i<32;++i) require(c[i]==guard,"output prefix guard");
        const int rows=m>=4?4:1;
        for (int r=0;r<7;++r) for (int col=0;col<ld;++col) {
            if (r>=rows || col>=n) require(c[32+r*ld+col]==guard,"output stride guard");
            else if ((m<4 || n%16==0) && !std::isfinite(c[32+r*ld+col])) {
                fprintf(stderr,"case: mode=%d bl=%d kb=%d n=%d m=%d zp=%d row=%d col=%d value=%g\n",
                        mode,bl,kb,n,m,zp,r,col,c[32+r*ld+col]);
                require(false,"nonfinite output");
            }
        }
        for (int i=32+7*ld;i<(int)c.size();++i) require(c[i]==guard,"output suffix guard");
    }
    void reference() {
        // Independently mirror scalar integer dots and block-order FMA for the
        // changed M1 Q4_0 path, plus the original full-tile M4 coverage.
        const bool m1 = m==1 && bl==32 && !zp;
        if (!m1 && (m<4 || n%16)) return;
        for (int r=0;r<(m1?1:4);++r) for (int col=0;col<n;++col) {
            float expected=0;
            for (int k=0;k<kb;++k) {
                const auto * ap=qa.data()+64+k*(m1?1:4)*(bl+4);
                const auto * bp=qb.data()+64+((col/16)*kb+k)*(32+(zp?16:0)+8*bl);
                float as; memcpy(&as,ap+4*r,4);
                const float bs=((col%16)%3==0?-1.0f:1.0f)*(1u<<((col%16)%4))/128;
                int sum=0;
                for (int j=0;j<bl;++j) {
                    const int av=(int8_t)ap[m1?4+j:16+(j/8)*32+r*8+j%8];
                    const uint8_t byte=bp[32+(zp?16:0)+(j/16)*128+((col%16)/4)*32+(col%4)*8+j%8];
                    const int bv=((byte>>(j%16>=8?4:0))&15)-(zp?bp[32+col%16]:8);
                    sum+=av*bv;
                }
                expected=std::fma((float)sum,as*bs,expected);
            }
            const float actual=c[32+r*ld+col];
            if (memcmp(&actual,&expected,4)!=0) {
                fprintf(stderr,"reference: bl=%d kb=%d n=%d m=%d zp=%d r=%d c=%d actual=%g expected=%g\n",
                        bl,kb,n,m,zp,r,col,actual,expected);
                require(false,"scalar reference differs bitwise");
            }
        }
    }
};

int main(int argc,char ** argv) {
    require(argc==1,"usage: test-ime-m1");
    int cases=0;
    for(int bl:{32,64}) for(int kb:{1,2,7,64}) for(int n:{1,15,16,17,32,48})
        for(int m:{1,2,3,4,7}) for(bool zp:{false,true}) {
            Data control(bl,kb,n,m,zp,cases), candidate=control;
            const auto control_a=control.qa, control_b=control.qb;
            auto processed=control.call(0); control.check(); control.reference();
            require(control.qa==control_a && control.qb==control_b,"control input overwritten");
            for(int mode:{1}) {
                candidate=Data(bl,kb,n,m,zp,cases);
                const auto a=candidate.qa, b=candidate.qb;
                require(candidate.call(mode)==processed,"processed rows"); candidate.check(mode);
                require(candidate.qa==a && candidate.qb==b,"input overwritten");
                require(memcmp(control.c.data(),candidate.c.data(),control.c.size()*sizeof(float))==0,"output differs bitwise");
            }
            ++cases;
        }
    printf("PASS: %d cases; fixed K32 mode bitwise equal; scalar M1/M4 reference and input/stride guards intact\n",cases);
}
