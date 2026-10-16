#include "fragment-fixture.h"

#define NOINLINE __attribute__((noinline,noclone))

/* 所有机制探针完整复制输入，不使用已公开的 Q8 片段。 */
static inline void bytes(const uint8_t *input,uint8_t *output,size_t count) {
    const volatile uint8_t *from=input;
    volatile uint8_t *to=output;
    for(size_t i=0;i<count;i++) to[i]=from[i];
}
NOINLINE void probe_byte(const uint8_t *input,uint8_t *output,size_t count) {
    bytes(input,output,count);
}
NOINLINE void probe_unroll4(const uint8_t *input,uint8_t *output,size_t count) {
    const volatile uint8_t *from=input;
    volatile uint8_t *to=output;
    size_t i=0;
    for(;i+4<=count;i+=4) {
        uint8_t a=from[i],b=from[i+1],c=from[i+2],d=from[i+3];
        to[i]=a;to[i+1]=b;to[i+2]=c;to[i+3]=d;
    }
    for(;i<count;i++) to[i]=from[i];
}
NOINLINE void probe_unroll8(const uint8_t *input,uint8_t *output,size_t count) {
    const volatile uint8_t *from=input;
    volatile uint8_t *to=output;
    size_t i=0;
    for(;i+8<=count;i+=8) {
        uint8_t a=from[i],b=from[i+1],c=from[i+2],d=from[i+3];
        uint8_t e=from[i+4],f=from[i+5],g=from[i+6],h=from[i+7];
        to[i]=a;to[i+1]=b;to[i+2]=c;to[i+3]=d;
        to[i+4]=e;to[i+5]=f;to[i+6]=g;to[i+7]=h;
    }
    for(;i<count;i++) to[i]=from[i];
}
NOINLINE void probe_twopass(const uint8_t *input,uint8_t *output,size_t count) {
    bytes(input,output,count);
    bytes(input,output,count);
}
NOINLINE void probe_callee(const uint8_t *input,uint8_t *output,size_t count) {
    for(size_t i=0;i<count;i+=32) {
        size_t n=count-i;
        if(n>32) n=32;
        probe_byte(input+i,output+i,n);
    }
}
NOINLINE void probe_clear_m1(const uint8_t *input,uint8_t *output,size_t count) {
    uint8_t *to=output;
    size_t left=count;
    while(left) {
        size_t vl;
        __asm__ volatile("vsetvli %0,%1,e8,m1,ta,ma\n\t"
                         "vmv.v.i v0,0\n\t"
                         "vse8.v v0,(%2)"
                         : "=&r"(vl) : "r"(left),"r"(to) : "v0","memory");
        to+=vl;left-=vl;
    }
    bytes(input,output,count);
}
NOINLINE void probe_clear_m8(const uint8_t *input,uint8_t *output,size_t count) {
    uint8_t *to=output;
    size_t left=count;
    while(left) {
        size_t vl;
        __asm__ volatile("vsetvli %0,%1,e8,m8,ta,ma\n\t"
                         "vmv.v.i v0,0\n\t"
                         "vse8.v v0,(%2)"
                         : "=&r"(vl) : "r"(left),"r"(to)
                         : "v0","v1","v2","v3","v4","v5","v6","v7","memory");
        to+=vl;left-=vl;
    }
    bytes(input,output,count);
}
void fragment_reference(const uint8_t *input,uint8_t *output,size_t count) {
    for(size_t i=0;i<count;i++) output[i]=input[i];
}
