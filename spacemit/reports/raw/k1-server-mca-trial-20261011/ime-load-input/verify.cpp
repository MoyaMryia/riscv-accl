
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
extern "C" void load_control(const uint8_t *,uint8_t *);
extern "C" void load_candidate(const uint8_t *,uint8_t *);
int main(int argc,char **argv) {
    if(argc!=2) return 2;
    FILE *file=fopen(argv[1],"wb"); if(!file) return 3;
    for(int seed=0;seed<64;++seed) {
        alignas(32) std::array<uint8_t,2048> input;
        for(size_t i=0;i<input.size();++i) input[i]=(i*73+seed*31)%256;
        const auto original=input;
        alignas(32) std::array<uint8_t,400> a,b; a.fill(0xa5); b=a;
        load_control(input.data(),a.data()+16);
        load_candidate(input.data(),b.data()+16);
        if(a!=b || input!=original) return 4;
        for(int i=0;i<16;++i) if(a[i]!=0xa5 || a[384+i]!=0xa5) return 5;
        for(int group=0;group<4;++group) for(int i=0;i<32;++i) {
            const auto value=input[(group+1)*128+i];
            if(a[16+group*32+i]!=(value&15) || a[16+(group+4)*32+i]!=(value>>4)) return 6;
        }
        for(int group=0;group<2;++group) for(int i=0;i<8;++i)
            if(a[16+(8+group)*32+i]!=input[(5+group)*128+i]) return 7;
        for(int i=0;i<6;++i) {
            uintptr_t pointer; memcpy(&pointer,a.data()+16+320+i*8,8);
            if(pointer!=reinterpret_cast<uintptr_t>(input.data())+(i+1)*128+(i<4?128:16)) return 8;
        }
        if(fwrite(input.data(),1,input.size(),file)!=input.size()) return 9;
        if(fwrite(a.data(),1,a.size(),file)!=a.size()) return 10;
        if(fwrite(b.data(),1,b.size(),file)!=b.size()) return 11;
    }
    if(fclose(file)) return 12;
    puts("PASS: 64 load cases; complete paired vectors, pointers, inputs and guards");
}
