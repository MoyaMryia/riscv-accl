#include "ime-fixture.h"
#include "common.h"

int main(int argc, char ** argv) {
    const bool bench = argc == 5 && strcmp(argv[1], "--bench") == 0;
    need(argc == 1 || bench,"usage: ime [--bench K N ARM]");
    if (bench) {
        const int k=atoi(argv[2]), n=atoi(argv[3]), arm=atoi(argv[4]);
        need(k>0 && k%32 == 0 && n>0 && n%64 == 0 && arm>=0 && arm<=2,"benchmark shape");
        Data f(32,k/32,n/4,1,false,0);
        f.call(0); f.check(); f.reference(); const auto expected=f.c;
        for (int mode : {1,2}) {
            need(f.call(mode)==1,"processed rows"); f.check(mode);
            need(same_bits(f.c,expected),"benchmark output identity");
        }
        Workers workers(true);
        fprintf(stderr,"QUICK_IME_RAW arm=%d workers=4 columns_per_worker=%d\n",arm,n/4);
        std::array<Data,4> data={f,f,f,f};
        char shape[80]; snprintf(shape,sizeof(shape),"M1-K%d-N%d",k,n);
        measure("ime",shape,arm,0,[&](int count) {
            return workers.run([&](int id) {
                for (int i=0; i<count; ++i) need(data[id].call(arm)==1,"processed rows");
            });
        },[&] {
            for (auto & d : data) { d.check(arm); need(same_bits(d.c,expected),"timed output identity"); }
        });
    } else {
        int cases=0;
        for (int bl : {32,64}) for (int kb : {1,2,7,64}) for (int n : {1,15,16,17,32,48})
            for (int m : {1,2,3,4,7}) for (bool zp : {false,true}) {
                Data f(bl,kb,n,m,zp,cases);
                const auto qa=f.qa, qb=f.qb;
                const auto processed=f.call(0); f.check(); f.reference(); const auto expected=f.c;
                for (int arm : {1,2}) {
                    need(f.call(arm)==processed,"processed rows"); f.check(arm);
                    need(same_bits(f.c,expected) && f.qa == qa && f.qb == qb,"raw identity");
                }
                ++cases;
            }
        printf("PASS: %d IME cases; original/fixed/scheduled output identity\n",cases);
    }
}
