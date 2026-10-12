.text
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_e2296:
bge zero,a4,.Lpc_e2368
.Lpc_e229a:
csrrs t0,vlenb,zero
.Lpc_e229e:
slli t1,t0,0x3
.Lpc_e22a2:
sub sp,sp,t1
.Lpc_e22a6:
vsetvli t1,zero,e32,m8,ta,ma
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_e22aa:
vmv.v.i v8,0
.Lpc_e22ae:
sh2add t4,a4,a5
.Lpc_e22b2:
vmv.s.x v24,zero
.Lpc_e22b6:
slli t3,a4,0x2
.Lpc_e22ba:
vs8r.v v8,(sp)
.Lpc_e22be:
vl8re32.v v16,(sp)
.Lpc_e22c2:
c.li a7,0
.Lpc_e22c4:
sub a6,a4,a7
.Lpc_e22c8:
vsetvli a6,a6,e32,m8,ta,ma
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_e22cc:
sh2add t5,a7,a0
.Lpc_e22d0:
vle32.v v8,(t5)
.Lpc_e22d4:
sh2add t6,a7,a1
.Lpc_e22d8:
c.add a7,a6
.Lpc_e22da:
vfmul.vf v8,v8,fa0
.Lpc_e22de:
vse32.v v8,(t5)
.Lpc_e22e2:
vle32.v v0,(t6)
.Lpc_e22e6:
vfmacc.vv v16,v8,v0
.Lpc_e22ea:
blt a7,a4,.Lpc_e22c4
.Lpc_e22ee:
vsetvli t1,zero,e32,m8,ta,ma
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_e22f2:
flw fa5,0(a2)
.Lpc_e22f6:
vfredusum.vs v1,v16,v24
.Lpc_e22fa:
c.li a7,0
.Lpc_e22fc:
vl8re32.v v16,(sp)
.Lpc_e2300:
vfmv.f.s fa4,v1
.Lpc_e2304:
fsub.s fa5,fa5,fa4
.Lpc_e2308:
fmul.s fa5,fa5,fa1
.Lpc_e230c:
sub a6,a4,a7
.Lpc_e2310:
vsetvli a6,a6,e32,m8,ta,ma
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_e2314:
sh2add t5,a7,a0
.Lpc_e2318:
sh2add t6,a7,a1
.Lpc_e231c:
vle32.v v8,(t5)
.Lpc_e2320:
vle32.v v0,(t6)
.Lpc_e2324:
sh2add t6,a7,a3
.Lpc_e2328:
c.add a7,a6
.Lpc_e232a:
vfmacc.vf v8,fa5,v0
.Lpc_e232e:
vse32.v v8,(t5)
.Lpc_e2332:
vle32.v v0,(t6)
.Lpc_e2336:
vfmacc.vv v16,v8,v0
.Lpc_e233a:
blt a7,a4,.Lpc_e230c
.Lpc_e233e:
vsetvli t1,zero,e32,m8,ta,ma
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_e2342:
c.addi a5,4
.Lpc_e2344:
vfredusum.vs v16,v16,v24
.Lpc_e2348:
c.add a0,t3
.Lpc_e234a:
c.addi a2,4
.Lpc_e234c:
vfmv.f.s fa5,v16
.Lpc_e2350:
fmul.s fa5,fa5,fa2
.Lpc_e2354:
fsw fa5,-4(a5)
.Lpc_e2358:
bne t4,a5,.Lpc_e22be
.Lpc_e235c:
csrrs t0,vlenb,zero
.Lpc_e2360:
slli t1,t0,0x3
.Lpc_e2364:
c.add sp,t1
.Lpc_e2366:
c.jr ra
.Lpc_e2368:
c.jr ra
