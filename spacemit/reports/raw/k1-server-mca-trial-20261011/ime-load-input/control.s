.text
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
vle8.v       v4, (s1)
addi         s1, s1, 128
vle8.v       v5, (s2)
addi         s2, s2, 128
vle8.v       v6, (s3)
addi         s3, s3, 128
vle8.v       v7, (s4)
addi         s4, s4, 128
vsetvli      t0, zero, e8, mf4
# LLVM-MCA-RISCV-LMUL MF4
vle8.v       v14, (s5)
addi         s5, s5, 16
vle8.v       v15, (s6)
addi         s6, s6, 16
vsetvli      t0, zero, e8, m1
# LLVM-MCA-RISCV-LMUL M1
vand.vi      v0, v4, 15
vand.vi      v1, v5, 15
vand.vi      v2, v6, 15
vand.vi      v3, v7, 15
vsrl.vi      v4, v4, 4
vsrl.vi      v5, v5, 4
vsrl.vi      v6, v6, 4
vsrl.vi      v7, v7, 4
