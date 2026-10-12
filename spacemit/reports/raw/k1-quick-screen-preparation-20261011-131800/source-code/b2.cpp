#include "b2-fixture.h"
#include "common.h"

static void select_tile(Fixture & f, int tile) {
    const std::string value = std::to_string(tile);
    setenv("SPINE_QUICK_B2_TILE", value.c_str(), 1);
    f.run("0", "1");
}

int main(int argc, char ** argv) {
    const bool bench = argc == 5 && strcmp(argv[1], "--bench") == 0;
    const bool dump_mode = argc == 3 && strcmp(argv[1], "--dump") == 0;
    need(argc == 1 || bench || dump_mode, "usage: b2 [--dump FILE | --bench HISTORY HEADS TILE]");
    FILE * dump = dump_mode ? fopen(argv[2],"wb") : nullptr;
    need(!dump_mode || dump,"dump file");
    ggml_time_init();
    if (bench) {
        const int nk=atoi(argv[2]), heads=atoi(argv[3]), tile=atoi(argv[4]);
        need((nk == 256 || nk == 2048) && (heads == 8 || heads == 16) &&
            (tile == 0 || tile == 8 || tile == 16), "benchmark shape");
        Fixture f(nk,heads,1,0);
        f.run("0","0"); const auto output=f.output; const auto parts=f.segments();
        select_tile(f,tile);
        need(same_bits(f.output,output) && f.segments() == parts, "benchmark identity");
        setenv("SPINE_K1_TRACE", "0", 1);
        char shape[80]; snprintf(shape,sizeof(shape),"K%d-H%d",nk,heads);
        measure("b2",shape,tile,0,[&](int n) { return f.compute(n); },[&] {
            f.check(); need(same_bits(f.output,output) && f.segments() == parts,"timed identity");
        });
    } else {
        int cases=0;
        for (int nk : {1,7,8,9,15,16,17,255,256,511,512,513,2048})
            for (int h : {8,16}) for (int mask : {0,1,2}) for (int pad : {0,13}) {
                Fixture f(nk,h,mask,pad); f.run("0","0");
                const auto output=f.output; const auto parts=f.segments();
                for (int tile : {0,8,16}) {
                    select_tile(f,tile);
                    need(same_bits(f.output,output) && f.segments() == parts,"numeric identity");
                    if (dump) {
                        need(fwrite(f.output.data(),4,f.output.size(),dump)==f.output.size(),"output dump");
                        need(fwrite(parts.data(),1,parts.size(),dump)==parts.size(),"partial dump");
                    }
                }
                ++cases;
            }
        for (int nth : {1,2,8}) {
            Fixture f(513,8,1,13,0,256,0,nth); f.run("0","0"); const auto output=f.output;
            for (int tile : {8,16}) { select_tile(f,tile); need(same_bits(f.output,output),"thread fallback"); }
            ++cases;
        }
        printf("PASS: %d B2 cases; original/B1/B2 output and partials\n",cases);
    }
    if (dump) need(fclose(dump)==0,"dump close");
}
