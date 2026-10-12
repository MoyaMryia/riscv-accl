#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <riscv_vector.h>

#define N 1024
#define REPEATS 64
static float input[N], scratch[N], control[N], candidate[N];

__attribute__((noinline)) void roi_copy(void) {
    for (int repeat = 0; repeat < REPEATS; ++repeat) {
        for (size_t i = 0; i < N;) {
            size_t vl = __riscv_vsetvl_e32m1(N-i);
            __riscv_vse32_v_f32m1(scratch+i, __riscv_vle32_v_f32m1(input+i, vl), vl);
            i += vl;
        }
        for (size_t i = 0; i < N;) {
            size_t vl = __riscv_vsetvl_e32m1(N-i);
            vfloat32m1_t value = __riscv_vle32_v_f32m1(scratch+i, vl);
            __riscv_vse32_v_f32m1(control+i, __riscv_vfmul_vf_f32m1(value, 2.0f, vl), vl);
            i += vl;
        }
        __asm__ volatile("" ::: "memory");
    }
}

__attribute__((noinline)) void roi_direct(void) {
    for (int repeat = 0; repeat < REPEATS; ++repeat) {
        for (size_t i = 0; i < N;) {
            size_t vl = __riscv_vsetvl_e32m1(N-i);
            vfloat32m1_t value = __riscv_vle32_v_f32m1(input+i, vl);
            __riscv_vse32_v_f32m1(candidate+i, __riscv_vfmul_vf_f32m1(value, 2.0f, vl), vl);
            i += vl;
        }
        __asm__ volatile("" ::: "memory");
    }
}

__attribute__((noinline)) void roi_ime(const int8_t *a, const int8_t *b, int32_t *out) {
    __asm__ volatile(
        "vsetvli t0, zero, e32, m2, ta, ma\n\t"
        "vxor.vv v16, v16, v16\n\t"
        "vsetvli t0, zero, e8, m1, ta, ma\n\t"
        "vle8.v v14, (%0)\n\t"
        "vle8.v v0, (%1)\n\t"
        ".word 0xe207382b\n\t"
        ".word 0xe207382b\n\t"
        "vsetvli t0, zero, e32, m2, ta, ma\n\t"
        "vse32.v v16, (%2)\n\t"
        : : "r"(a), "r"(b), "r"(out)
        : "t0", "v0", "v14", "v16", "v17", "memory");
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "ime") == 0) {
        int8_t a[32], b[32]; int32_t out[16];
        for (int seed = 0; seed < 16; ++seed) {
            for (int i = 0; i < 32; ++i) {
                a[i] = (int8_t)((i*17+seed*31)%255-127);
                b[i] = (int8_t)((i*13+seed*7)%255-127);
            }
            roi_ime(a, b, out);
            for (int row = 0; row < 4; ++row) for (int col = 0; col < 4; ++col) {
                int32_t sum = 0;
                for (int k = 0; k < 8; ++k) sum += a[row*8+k]*b[col*8+k];
                if (out[row*4+col] != 2*sum) return 1;
            }
        }
        puts("PASS IME: 16 signed tiles, two accumulations, all 16 outputs");
        return 0;
    }
    if (strcmp(argv[1], "rvv") != 0) return 2;
    for (int i = 0; i < N; ++i) input[i] = (float)(i-512)/8.0f;
    roi_copy(); roi_direct();
    if (memcmp(control, candidate, sizeof control) != 0) return 1;
    for (int i = 0; i < N; ++i) if (candidate[i] != input[i]*2.0f) return 1;
    puts("PASS RVV: full output identity, 1024 elements, 64 calls per arm");
    return 0;
}
