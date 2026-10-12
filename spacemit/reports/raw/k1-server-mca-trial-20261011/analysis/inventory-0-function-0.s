.text
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_dfb0e:
addi a5,zero,128
.Lpc_dfb12:
addi t0,zero,64
.Lpc_dfb16:
vsetvli zero,t0,e32,m8,ta,ma
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_dfb1a:
addi t0,a0,256
.Lpc_dfb1e:
vle32.v v0,(a0)
.Lpc_dfb22:
vle32.v v8,(t0)
.Lpc_dfb26:
vfmul.vf v0,v0,fa0
.Lpc_dfb2a:
vfmul.vf v8,v8,fa0
.Lpc_dfb2e:
vmv.v.i v16,0
.Lpc_dfb32:
vle32.v v24,(a1)
.Lpc_dfb36:
vfmacc.vv v16,v0,v24
.Lpc_dfb3a:
addi t1,a1,256
.Lpc_dfb3e:
vle32.v v24,(t1)
.Lpc_dfb42:
vfmacc.vv v16,v8,v24
.Lpc_dfb46:
vmv.v.i v24,0
.Lpc_dfb4a:
vfredusum.vs v16,v16,v24
.Lpc_dfb4e:
vfmv.f.s ft0,v16
.Lpc_dfb52:
flw ft1,0(a2)
.Lpc_dfb56:
fsub.s ft1,ft1,ft0
.Lpc_dfb5a:
fmul.s ft1,ft1,fa1
.Lpc_dfb5e:
vle32.v v24,(a1)
.Lpc_dfb62:
vfmacc.vf v0,ft1,v24
.Lpc_dfb66:
vse32.v v0,(a0)
.Lpc_dfb6a:
vmv.v.i v16,0
.Lpc_dfb6e:
vle32.v v24,(a3)
.Lpc_dfb72:
vfmacc.vv v16,v0,v24
.Lpc_dfb76:
addi t1,a1,256
.Lpc_dfb7a:
vle32.v v24,(t1)
.Lpc_dfb7e:
vfmacc.vf v8,ft1,v24
.Lpc_dfb82:
vse32.v v8,(t0)
.Lpc_dfb86:
addi t1,a3,256
.Lpc_dfb8a:
vle32.v v24,(t1)
.Lpc_dfb8e:
vfmacc.vv v16,v8,v24
.Lpc_dfb92:
vmv.v.i v24,0
.Lpc_dfb96:
vfredusum.vs v16,v16,v24
.Lpc_dfb9a:
vfmv.f.s ft0,v16
.Lpc_dfb9e:
fmul.s ft0,ft0,fa2
.Lpc_dfba2:
fsw ft0,0(a4)
.Lpc_dfba6:
addi a0,a0,512
.Lpc_dfbaa:
c.addi a2,4
.Lpc_dfbac:
c.addi a4,4
.Lpc_dfbae:
c.addi a5,-1
.Lpc_dfbb0:
c.bnez a5,.Lpc_dfb1a
.Lpc_dfbb2:
c.jr ra
