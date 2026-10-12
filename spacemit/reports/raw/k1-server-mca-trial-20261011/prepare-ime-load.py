import collections, hashlib, json, pathlib, re
root=pathlib.Path(__file__).resolve().parent
source=pathlib.Path('lab/k1-quick-screen-final-20261011/ime-schedule.cpp')
text=source.read_text()
blocks={}
for arm,macro in [('control','K1_M1_K32_LOAD'),('candidate','QUICK_M1_LOAD')]:
    chunk=text[text.index('#define '+macro+' '):].split('\n\n',1)[0]
    blocks[arm]=[s.strip() for s in re.findall(r'"([^"\n]+)\\n\\t"',chunk)]
assert collections.Counter(blocks['control'])==collections.Counter(blocks['candidate'])
assert len(blocks['control'])==22
out=root/'ime-load-input'
out.mkdir(exist_ok=False)
functions=[]
for arm,body in blocks.items():
    lines=['.text','.global load_'+arm,'load_'+arm+':','addi sp,sp,-64']
    lines += [f'sd s{i},{(i-1)*8}(sp)' for i in range(1,7)]
    lines += ['vsetvli t0,zero,e8,m1,ta,ma']
    lines += [f'vmv.v.i v{i},0' for i in range(16)]
    lines += [f'addi s{i},a0,{i*128}' for i in range(1,7)]
    lines += body
    for i in [0,1,2,3,4,5,6,7,14,15]:
        lines += [f'vs1r.v v{i},(a1)','addi a1,a1,32']
    lines += [f'sd s{i},{(i-1)*8}(a1)' for i in range(1,7)]
    lines += [f'ld s{i},{(i-1)*8}(sp)' for i in range(1,7)]
    lines += ['addi sp,sp,64','ret']
    functions += lines
    model=['.text','# LLVM-MCA-RISCV-LMUL M1','# LLVM-MCA-RISCV-SEW E8']
    for instruction in body:
        model += [instruction]
        if instruction.startswith('vsetvli'):
            model += ['# LLVM-MCA-RISCV-LMUL '+('MF4' if 'mf4' in instruction else 'M1')]
    (out/(arm+'.s')).write_text('\n'.join(model)+'\n')
(out/'functions.s').write_text('\n'.join(functions)+'\n')
(out/'verify.cpp').write_text(r'''
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
''')
(out/'plan.json').write_text(json.dumps({'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'instructions_per_arm':22,'cases':64,'scope':'isolated load and unpack; no matrix instruction; no full kernel timing','blocks':blocks},indent=2)+'\n')
