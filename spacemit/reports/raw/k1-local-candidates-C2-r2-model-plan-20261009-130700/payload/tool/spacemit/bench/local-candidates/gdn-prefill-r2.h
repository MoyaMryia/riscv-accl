#pragma once

#if defined(__riscv_v_intrinsic)
__attribute__((noinline))
static void spine_k1_gdn_prefill128(float * state, const float * key, const float * value,
        const float * query, float gate, float beta, float scale, float * output) {
    size_t rows = 128;
    asm volatile(
        "li t0, 64\n\t"
        "vsetvli zero, t0, e32, m8, ta, ma\n\t"
        "1:\n\t"
        "addi t0, %[state], 256\n\t"
        "vle32.v v0, (%[state])\n\t"
        "vle32.v v8, (t0)\n\t"
        "vfmul.vf v0, v0, %[gate]\n\t"
        "vfmul.vf v8, v8, %[gate]\n\t"
        "vmv.v.i v16, 0\n\t"
        "vle32.v v24, (%[key])\n\t"
        "vfmacc.vv v16, v0, v24\n\t"
        "addi t1, %[key], 256\n\t"
        "vle32.v v24, (t1)\n\t"
        "vfmacc.vv v16, v8, v24\n\t"
        "vmv.v.i v24, 0\n\t"
        "vfredusum.vs v16, v16, v24\n\t"
        "vfmv.f.s ft0, v16\n\t"
        "flw ft1, 0(%[value])\n\t"
        "fsub.s ft1, ft1, ft0\n\t"
        "fmul.s ft1, ft1, %[beta]\n\t"
        "vle32.v v24, (%[key])\n\t"
        "vfmacc.vf v0, ft1, v24\n\t"
        "vse32.v v0, (%[state])\n\t"
        "vmv.v.i v16, 0\n\t"
        "vle32.v v24, (%[query])\n\t"
        "vfmacc.vv v16, v0, v24\n\t"
        "addi t1, %[key], 256\n\t"
        "vle32.v v24, (t1)\n\t"
        "vfmacc.vf v8, ft1, v24\n\t"
        "vse32.v v8, (t0)\n\t"
        "addi t1, %[query], 256\n\t"
        "vle32.v v24, (t1)\n\t"
        "vfmacc.vv v16, v8, v24\n\t"
        "vmv.v.i v24, 0\n\t"
        "vfredusum.vs v16, v16, v24\n\t"
        "vfmv.f.s ft0, v16\n\t"
        "fmul.s ft0, ft0, %[scale]\n\t"
        "fsw ft0, 0(%[output])\n\t"
        "addi %[state], %[state], 512\n\t"
        "addi %[value], %[value], 4\n\t"
        "addi %[output], %[output], 4\n\t"
        "addi %[rows], %[rows], -1\n\t"
        "bnez %[rows], 1b\n\t"
        : [state] "+&r" (state), [value] "+&r" (value),
          [output] "+&r" (output), [rows] "+&r" (rows)
        : [key] "r" (key), [query] "r" (query), [gate] "f" (gate),
          [beta] "f" (beta), [scale] "f" (scale)
        : "t0", "t1", "ft0", "ft1", "memory",
          "v0", "v1", "v2", "v3", "v4", "v5", "v6", "v7",
          "v8", "v9", "v10", "v11", "v12", "v13", "v14", "v15",
          "v16", "v17", "v18", "v19", "v20", "v21", "v22", "v23",
          "v24", "v25", "v26", "v27", "v28", "v29", "v30", "v31");
}
#endif
