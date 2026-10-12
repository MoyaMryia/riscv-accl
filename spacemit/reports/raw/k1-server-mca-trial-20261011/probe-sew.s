# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW 32
vle32.v v0, (a0)
vfmacc.vv v16,v0,v24
vfredusum.vs v16,v16,v24
vfmv.f.s ft0,v16
