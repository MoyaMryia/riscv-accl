#include "fragment-fixture.h"
#include <string.h>

/* 来源为 0007-q8-ime1.patch 的 16 行 Q8 重排载荷部分。 */
static inline void layout(const uint8_t *restrict input,uint8_t *restrict output,size_t groups,int clear) {
    for(size_t group=0;group<groups;group++) {
        const uint8_t *in=input+group*512;
        uint8_t *out=output+group*512;
        if(clear) memset(out,0,512);
        for(int col=0;col<16;col++) {
            const int acc=col/4,cgrp=col%4;
            const uint8_t *q=in+col*32;
            for(int s=0;s<2;s++) {
                const int base=s*16;
                uint8_t *reg_lo=out+(s*8+acc)*32;
                uint8_t *reg_hi=out+(s*8+acc+4)*32;
                for(int i=0;i<4;i++) {
                    reg_lo[(2*cgrp)*4+i]=q[base+i];
                    reg_lo[(2*cgrp+1)*4+i]=q[base+4+i];
                    reg_hi[(2*cgrp)*4+i]=q[base+8+i];
                    reg_hi[(2*cgrp+1)*4+i]=q[base+12+i];
                }
            }
        }
    }
}
__attribute__((noinline,noclone))
void fragment_baseline(const uint8_t *input,uint8_t *output,size_t groups) {
    layout(input,output,groups,1);
}
__attribute__((noinline,noclone))
void fragment_no_clear(const uint8_t *input,uint8_t *output,size_t groups) {
    layout(input,output,groups,0);
}
__attribute__((noinline,noclone))
void fragment_contiguous(const uint8_t *restrict input,uint8_t *restrict output,size_t groups) {
    for(size_t group=0;group<groups;group++) for(int s=0;s<2;s++) for(int half=0;half<2;half++)
        for(int acc=0;acc<4;acc++) for(int cgrp=0;cgrp<4;cgrp++) {
            const uint8_t *from=input+group*512+(acc*4+cgrp)*32+s*16+half*8;
            uint8_t *to=output+group*512+(s*8+half*4+acc)*32+cgrp*8;
            memcpy(to,from,8);
        }
}
/* 独立参考按输出字节反求输入坐标，不复用候选的循环顺序。 */
void fragment_reference(const uint8_t *input,uint8_t *output,size_t groups) {
    for(size_t group=0;group<groups;group++) for(size_t byte=0;byte<512;byte++) {
        const size_t reg=byte/32,offset=byte%32;
        const size_t step=reg/8,half=reg%8/4,acc=reg%4;
        const size_t col=acc*4+offset/8,k=step*16+half*8+offset%8;
        output[group*512+byte]=input[group*512+col*32+k];
    }
}
