.text
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_1494dc:
c.addi16sp sp,-400
.Lpc_1494de:
c.sdsp s0,384(sp)
.Lpc_1494e0:
auipc s0,0xe4
.Lpc_1494e4:
ld s0,216(s0) # .Lpc_22d5b8
.Lpc_1494e8:
c.sdsp s11,296(sp)
.Lpc_1494ea:
ld t1,0(s0)
.Lpc_1494ee:
c.sdsp t1,280(sp)
.Lpc_1494f0:
c.li t1,0
.Lpc_1494f2:
c.sdsp ra,392(sp)
.Lpc_1494f4:
c.li t3,3
.Lpc_1494f6:
c.mv s11,a7
.Lpc_1494f8:
srli s0,a0,0x4
.Lpc_1494fc:
bltu t3,a5,.Lpc_149780
.Lpc_149500:
beq a3,zero,.Lpc_149c86
.Lpc_149504:
beq a6,zero,.Lpc_14a2e6
.Lpc_149508:
mul a0,a0,a7
.Lpc_14950c:
c.sdsp s8,320(sp)
.Lpc_14950e:
sh1add s8,a7,a7
.Lpc_149512:
c.sdsp s9,312(sp)
.Lpc_149514:
c.sdsp s1,376(sp)
.Lpc_149516:
c.sdsp s2,368(sp)
.Lpc_149518:
c.sdsp s3,360(sp)
.Lpc_14951a:
c.sdsp s4,352(sp)
.Lpc_14951c:
c.sdsp s5,344(sp)
.Lpc_14951e:
c.sdsp s6,336(sp)
.Lpc_149520:
c.sdsp s7,328(sp)
.Lpc_149522:
c.mv a5,a4
.Lpc_149524:
c.slli s8,0x4
.Lpc_149526:
c.li t6,0
.Lpc_149528:
c.li t4,0
.Lpc_14952a:
c.li a7,0
.Lpc_14952c:
c.li s9,16
.Lpc_14952e:
c.slli a0,0x4
.Lpc_149530:
sub a4,a6,a7
.Lpc_149534:
bgeu s9,a4,.Lpc_14953a
.Lpc_149538:
c.li a4,16
.Lpc_14953a:
srli a3,t4,0x1
.Lpc_14953e:
c.add a3,t6
.Lpc_149540:
c.add a3,a2
.Lpc_149542:
c.mv t1,s11
.Lpc_149544:
vsetvli t0,zero,e32,m4,tu,mu
# LLVM-MCA-RISCV-LMUL M4
# LLVM-MCA-RISCV-SEW E32
.Lpc_149548:
vxor.vv v28,v28,v28
.Lpc_14954c:
vsetvli t0,zero,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_149550:
vmv.v.i v13,3
.Lpc_149554:
c.li s1,24
.Lpc_149556:
vsetvli t0,s1,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_14955a:
vmv.v.i v13,2
.Lpc_14955e:
vsetvli t0,zero,e8,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E8
.Lpc_149562:
vmv.v.i v13,1
.Lpc_149566:
vsetvli t0,zero,e8,mf4,tu,mu
# LLVM-MCA-RISCV-LMUL MF4
# LLVM-MCA-RISCV-SEW E8
.Lpc_14956a:
vmv.v.i v13,0
.Lpc_14956e:
c.mv s1,a3
.Lpc_149570:
addi s2,a3,8
.Lpc_149574:
addi s3,a3,16
.Lpc_149578:
addi s4,a3,24
.Lpc_14957c:
addi s7,a3,32
.Lpc_149580:
c.mv s5,a1
.Lpc_149582:
addi s6,a1,12
.Lpc_149586:
vsetvli t0,zero,e16,mf4,tu,mu
# LLVM-MCA-RISCV-LMUL MF4
# LLVM-MCA-RISCV-SEW E16
.Lpc_14958a:
vle16.v v4,(s1)
.Lpc_14958e:
addi s1,s1,48
.Lpc_149592:
vle16.v v5,(s2)
.Lpc_149596:
addi s2,s2,72
.Lpc_14959a:
vle16.v v6,(s3)
.Lpc_14959e:
addi s3,s3,96
.Lpc_1495a2:
vle16.v v7,(s4)
.Lpc_1495a6:
addi s4,s4,120
.Lpc_1495aa:
flw ft1,0(s5)
.Lpc_1495ae:
c.addi s5,4
.Lpc_1495b0:
vfwcvt.f.f.v v8,v4
.Lpc_1495b4:
vfwcvt.f.f.v v9,v5
.Lpc_1495b8:
vfwcvt.f.f.v v10,v6
.Lpc_1495bc:
vfwcvt.f.f.v v11,v7
.Lpc_1495c0:
vsetvli t0,zero,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_1495c4:
c.mv t5,s0
.Lpc_1495c6:
vxor.vv v16,v16,v16
.Lpc_1495ca:
vxor.vv v18,v18,v18
.Lpc_1495ce:
vxor.vv v20,v20,v20
.Lpc_1495d2:
vxor.vv v22,v22,v22
.Lpc_1495d6:
vfmul.vf v24,v8,ft1
.Lpc_1495da:
vfmul.vf v25,v9,ft1
.Lpc_1495de:
vfmul.vf v26,v10,ft1
.Lpc_1495e2:
vfmul.vf v27,v11,ft1
.Lpc_1495e6:
c.addi t1,-1
.Lpc_1495e8:
vsetvli t0,zero,e8,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E8
.Lpc_1495ec:
vle8.v v1,(s7)
.Lpc_1495f0:
vsetvli t0,zero,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_1495f4:
vrgather.vv v8,v1,v13
.Lpc_1495f8:
vadd.vi v13,v13,4
.Lpc_1495fc:
vrgather.vv v9,v1,v13
.Lpc_149600:
vadd.vi v13,v13,4
.Lpc_149604:
vrgather.vv v10,v1,v13
.Lpc_149608:
vadd.vi v13,v13,4
.Lpc_14960c:
vrgather.vv v11,v1,v13
.Lpc_149610:
vadd.vi v13,v13,-12
.Lpc_149614:
vle8.v v4,(s1)
.Lpc_149618:
addi s1,s1,128
.Lpc_14961c:
vle8.v v5,(s2)
.Lpc_149620:
addi s2,s2,128
.Lpc_149624:
vle8.v v6,(s3)
.Lpc_149628:
addi s3,s3,128
.Lpc_14962c:
vle8.v v7,(s4)
.Lpc_149630:
addi s4,s4,128
.Lpc_149634:
vsetvli t0,zero,e8,mf4,tu,mu
# LLVM-MCA-RISCV-LMUL MF4
# LLVM-MCA-RISCV-SEW E8
.Lpc_149638:
vle8.v v14,(s5)
.Lpc_14963c:
c.addi s5,16
.Lpc_14963e:
vle8.v v15,(s6)
.Lpc_149642:
c.addi s6,16
.Lpc_149644:
c.addi t5,-1
.Lpc_149646:
vsetvli t0,zero,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_14964a:
vand.vi v0,v4,15
.Lpc_14964e:
vand.vi v1,v5,15
.Lpc_149652:
vand.vi v2,v6,15
.Lpc_149656:
vand.vi v3,v7,15
.Lpc_14965a:
vsrl.vi v4,v4,4
.Lpc_14965e:
vsrl.vi v5,v5,4
.Lpc_149662:
vsrl.vi v6,v6,4
.Lpc_149666:
vsrl.vi v7,v7,4
.Lpc_14966a:
vsub.vv v0,v0,v8
.Lpc_14966e:
vsub.vv v4,v4,v8
.Lpc_149672:
vsub.vv v1,v1,v9
.Lpc_149676:
vsub.vv v5,v5,v9
.Lpc_14967a:
vsub.vv v2,v2,v10
.Lpc_14967e:
vsub.vv v6,v6,v10
.Lpc_149682:
vsub.vv v3,v3,v11
.Lpc_149686:
vsub.vv v7,v7,v11
.Lpc_1496aa:
bne t5,zero,.Lpc_149614
.Lpc_1496ae:
vsetvli t0,zero,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_1496b2:
vfcvt.f.x.v v16,v16
.Lpc_1496b6:
vfcvt.f.x.v v18,v18
.Lpc_1496ba:
vfcvt.f.x.v v20,v20
.Lpc_1496be:
vfcvt.f.x.v v22,v22
.Lpc_1496c2:
addi s2,s1,8
.Lpc_1496c6:
addi s3,s1,16
.Lpc_1496ca:
addi s4,s1,24
.Lpc_1496ce:
addi s6,s5,12
.Lpc_1496d2:
vfmacc.vv v28,v16,v24
.Lpc_1496d6:
vfmacc.vv v29,v18,v25
.Lpc_1496da:
vfmacc.vv v30,v20,v26
.Lpc_1496de:
vfmacc.vv v31,v22,v27
.Lpc_1496e2:
addi s7,s1,32
.Lpc_1496e6:
bne t1,zero,.Lpc_149586
.Lpc_1496ea:
c.li t3,16
.Lpc_1496ec:
addi s1,a5,16
.Lpc_1496f0:
addi s2,a5,32
.Lpc_1496f4:
addi s3,a5,48
.Lpc_1496f8:
blt a4,t3,.Lpc_149710
.Lpc_1496fc:
vse32.v v28,(a5)
.Lpc_149700:
vse32.v v29,(s1)
.Lpc_149704:
vse32.v v30,(s2)
.Lpc_149708:
vse32.v v31,(s3)
.Lpc_14970c:
jal zero,.Lpc_149740
.Lpc_149710:
vsetvli t0,a4,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_149714:
sub a4,a4,t0
.Lpc_149718:
vse32.v v28,(a5)
.Lpc_14971c:
vsetvli t0,a4,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_149720:
sub a4,a4,t0
.Lpc_149724:
vse32.v v29,(s1)
.Lpc_149728:
vsetvli t0,a4,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_14972c:
sub a4,a4,t0
.Lpc_149730:
vse32.v v30,(s2)
.Lpc_149734:
vsetvli t0,a4,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_149738:
sub a4,a4,t0
.Lpc_14973c:
vse32.v v31,(s3)
.Lpc_149740:
c.addi a7,16
.Lpc_149742:
c.add t4,a0
.Lpc_149744:
c.add t6,s8
.Lpc_149746:
addi a5,a5,64
.Lpc_14974a:
bltu a7,a6,.Lpc_149530
.Lpc_14974e:
c.ldsp s1,376(sp)
.Lpc_149750:
c.ldsp s2,368(sp)
.Lpc_149752:
c.ldsp s3,360(sp)
.Lpc_149754:
c.ldsp s4,352(sp)
.Lpc_149756:
c.ldsp s5,344(sp)
.Lpc_149758:
c.ldsp s6,336(sp)
.Lpc_14975a:
c.ldsp s7,328(sp)
.Lpc_14975c:
c.ldsp s8,320(sp)
.Lpc_14975e:
c.ldsp s9,312(sp)
.Lpc_149760:
c.li a0,1
.Lpc_149762:
auipc a5,0xe4
.Lpc_149766:
ld a5,-426(a5) # .Lpc_22d5b8
.Lpc_14976a:
c.ldsp a4,280(sp)
.Lpc_14976c:
c.ld a5,0(a5)
.Lpc_14976e:
c.xor a5,a4
.Lpc_149770:
c.li a4,0
.Lpc_149772:
bne a5,zero,.Lpc_14a2ec
.Lpc_149776:
c.ldsp ra,392(sp)
.Lpc_149778:
c.ldsp s0,384(sp)
.Lpc_14977a:
c.ldsp s11,296(sp)
.Lpc_14977c:
c.addi16sp sp,400
.Lpc_14977e:
c.jr ra
.Lpc_149780:
c.ldsp a5,400(sp)
.Lpc_149782:
c.sdsp s8,320(sp)
.Lpc_149784:
slli s8,a5,0x2
.Lpc_149788:
beq a3,zero,.Lpc_149e8e
.Lpc_14978c:
beq a6,zero,.Lpc_149a30
.Lpc_149790:
mul a0,a0,a7
.Lpc_149794:
c.sdsp s9,312(sp)
.Lpc_149796:
c.mv a5,a4
.Lpc_149798:
sh1add s9,a7,a7
.Lpc_14979c:
c.addi4spn a4,sp,24
.Lpc_14979e:
c.sdsp s7,328(sp)
.Lpc_1497a0:
c.sdsp s10,304(sp)
.Lpc_1497a2:
c.mv a7,s0
.Lpc_1497a4:
c.sdsp s1,376(sp)
.Lpc_1497a6:
c.sdsp s2,368(sp)
.Lpc_1497a8:
c.sdsp s3,360(sp)
.Lpc_1497aa:
c.slli a0,0x4
.Lpc_1497ac:
c.sdsp s4,352(sp)
.Lpc_1497ae:
c.sdsp s5,344(sp)
.Lpc_1497b0:
c.sdsp s6,336(sp)
.Lpc_1497b2:
c.slli s9,0x4
.Lpc_1497b4:
c.li s7,0
.Lpc_1497b6:
c.li t6,0
.Lpc_1497b8:
c.li t5,0
.Lpc_1497ba:
c.sdsp a4,8(sp)
.Lpc_1497bc:
c.mv s10,s8
.Lpc_1497be:
c.sdsp a0,0(sp)
.Lpc_1497c0:
c.mv s0,a1
.Lpc_1497c2:
c.mv t4,a2
.Lpc_1497c4:
srli a0,t6,0x1
.Lpc_1497c8:
c.add a0,s7
.Lpc_1497ca:
sub a4,a6,t5
.Lpc_1497ce:
c.li a3,15
.Lpc_1497d0:
c.add a0,t4
.Lpc_1497d2:
bgeu a3,a4,.Lpc_149a36
.Lpc_1497d6:
vsetvli t0,zero,e32,m8,tu,mu
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_1497da:
vxor.vv v24,v24,v24
.Lpc_1497de:
c.mv t3,s11
.Lpc_1497e0:
vsetvli t0,zero,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_1497e4:
c.li s1,24
.Lpc_1497e6:
vmv.v.i v1,3
.Lpc_1497ea:
vsetvli t0,s1,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_1497ee:
vmv.v.i v1,2
.Lpc_1497f2:
vsetvli t0,zero,e8,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E8
.Lpc_1497f6:
vmv.v.i v1,1
.Lpc_1497fa:
vsetvli t0,zero,e8,mf4,tu,mu
# LLVM-MCA-RISCV-LMUL MF4
# LLVM-MCA-RISCV-SEW E8
.Lpc_1497fe:
vmv.v.i v1,0
.Lpc_149802:
c.mv a1,s0
.Lpc_149804:
c.mv s1,a0
.Lpc_149806:
c.mv s5,s1
.Lpc_149808:
addi s6,s1,32
.Lpc_14980c:
addi s1,s6,16
.Lpc_149810:
addi s2,s1,32
.Lpc_149814:
addi s3,s1,64
.Lpc_149818:
addi s4,s1,96
.Lpc_14981c:
vsetvli t0,zero,e32,m8,tu,mu
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_149820:
vxor.vv v16,v16,v16
.Lpc_149824:
flw ft1,0(a1)
.Lpc_149828:
flw ft2,4(a1)
.Lpc_14982c:
flw ft3,8(a1)
.Lpc_149830:
flw ft4,12(a1)
.Lpc_149834:
c.addi a1,16
.Lpc_149836:
c.mv t2,a7
.Lpc_149838:
vsetvli t0,zero,e8,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E8
.Lpc_14983c:
vle8.v v11,(s6)
.Lpc_149840:
vsetvli t0,zero,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_149844:
vrgather.vv v12,v11,v1
.Lpc_149848:
vadd.vi v1,v1,4
.Lpc_14984c:
vrgather.vv v13,v11,v1
.Lpc_149850:
vadd.vi v1,v1,4
.Lpc_149854:
vrgather.vv v14,v11,v1
.Lpc_149858:
vadd.vi v1,v1,4
.Lpc_14985c:
vrgather.vv v15,v11,v1
.Lpc_149860:
vadd.vi v1,v1,-12
.Lpc_149864:
vsetvli t0,zero,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_149868:
vle8.v v6,(s1)
.Lpc_14986c:
addi s1,s1,128
.Lpc_149870:
vle8.v v7,(s2)
.Lpc_149874:
addi s2,s2,128
.Lpc_149878:
vle8.v v8,(s3)
.Lpc_14987c:
addi s3,s3,128
.Lpc_149880:
vle8.v v9,(s4)
.Lpc_149884:
addi s4,s4,128
.Lpc_149888:
vand.vi v2,v6,15
.Lpc_14988c:
vand.vi v3,v7,15
.Lpc_149890:
vand.vi v4,v8,15
.Lpc_149894:
vand.vi v5,v9,15
.Lpc_149898:
vsrl.vi v6,v6,4
.Lpc_14989c:
vsrl.vi v7,v7,4
.Lpc_1498a0:
vsrl.vi v8,v8,4
.Lpc_1498a4:
vsrl.vi v9,v9,4
.Lpc_1498a8:
vle8.v v10,(a1)
.Lpc_1498ac:
addi a1,a1,32
.Lpc_1498b0:
vle8.v v11,(a1)
.Lpc_1498b4:
addi a1,a1,32
.Lpc_1498b8:
vsub.vv v2,v2,v12
.Lpc_1498bc:
vsub.vv v6,v6,v12
.Lpc_1498c0:
vsub.vv v3,v3,v13
.Lpc_1498c4:
vsub.vv v7,v7,v13
.Lpc_1498c8:
vsub.vv v4,v4,v14
.Lpc_1498cc:
vsub.vv v8,v8,v14
.Lpc_1498d0:
vsub.vv v5,v5,v15
.Lpc_1498d4:
vsub.vv v9,v9,v15
.Lpc_1498f8:
c.addi t2,-1
.Lpc_1498fa:
bne t2,zero,.Lpc_149864
.Lpc_1498fe:
addi s2,s5,-8
.Lpc_149902:
addi s3,s5,8
.Lpc_149906:
addi s4,s5,16
.Lpc_14990a:
addi s6,s5,24
.Lpc_14990e:
addi t1,zero,240
.Lpc_149912:
vmv.s.x v0,t1
.Lpc_149916:
vsetvli t0,zero,e16,mf4,tu,mu
# LLVM-MCA-RISCV-LMUL MF4
# LLVM-MCA-RISCV-SEW E16
.Lpc_14991a:
vle16.v v9,(s5)
.Lpc_14991e:
vle16.v v11,(s3)
.Lpc_149922:
vle16.v v13,(s4)
.Lpc_149926:
vle16.v v15,(s6)
.Lpc_14992a:
vsetvli t0,zero,e16,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E16
.Lpc_14992e:
vle16.v v9,(s2),v0.t
.Lpc_149932:
vle16.v v11,(s5),v0.t
.Lpc_149936:
vle16.v v13,(s3),v0.t
.Lpc_14993a:
vle16.v v15,(s4),v0.t
.Lpc_14993e:
vfwcvt.f.f.v v4,v9
.Lpc_149942:
vfwcvt.f.f.v v5,v11
.Lpc_149946:
vfwcvt.f.f.v v6,v13
.Lpc_14994a:
vfwcvt.f.f.v v7,v15
.Lpc_14994e:
vsetvli t0,zero,e32,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_149952:
vfmv.v.f v2,ft1
.Lpc_149956:
vfmerge.vfm v2,v2,ft2,v0
.Lpc_14995a:
vfmv.v.f v3,ft3
.Lpc_14995e:
vfmerge.vfm v3,v3,ft4,v0
.Lpc_149962:
vfmul.vv v8,v4,v2
.Lpc_149966:
vfmul.vv v9,v4,v3
.Lpc_14996a:
vfmul.vv v10,v5,v2
.Lpc_14996e:
vfmul.vv v11,v5,v3
.Lpc_149972:
vfmul.vv v12,v6,v2
.Lpc_149976:
vfmul.vv v13,v6,v3
.Lpc_14997a:
vfmul.vv v14,v7,v2
.Lpc_14997e:
vfmul.vv v15,v7,v3
.Lpc_149982:
vsetvli t0,zero,e32,m8,tu,mu
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_149986:
vfcvt.f.x.v v16,v16
.Lpc_14998a:
vfmacc.vv v24,v16,v8
.Lpc_14998e:
c.addi t3,-1
.Lpc_149990:
bne t3,zero,.Lpc_149806
.Lpc_149994:
c.mv a1,a5
.Lpc_149996:
add a2,a5,s10
.Lpc_14999a:
add a3,a2,s10
.Lpc_14999e:
add a4,a3,s10
.Lpc_1499a2:
c.addi a2,-16
.Lpc_1499a4:
c.addi a4,-16
.Lpc_1499a6:
addi t1,zero,240
.Lpc_1499aa:
vmv.s.x v0,t1
.Lpc_1499ae:
vsetvli t0,zero,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_1499b2:
vse32.v v24,(a1)
.Lpc_1499b6:
c.addi a1,16
.Lpc_1499b8:
vse32.v v25,(a3)
.Lpc_1499bc:
c.addi a3,16
.Lpc_1499be:
vse32.v v26,(a1)
.Lpc_1499c2:
c.addi a1,16
.Lpc_1499c4:
vse32.v v27,(a3)
.Lpc_1499c8:
c.addi a3,16
.Lpc_1499ca:
vse32.v v28,(a1)
.Lpc_1499ce:
c.addi a1,16
.Lpc_1499d0:
vse32.v v29,(a3)
.Lpc_1499d4:
c.addi a3,16
.Lpc_1499d6:
vse32.v v30,(a1)
.Lpc_1499da:
vse32.v v31,(a3)
.Lpc_1499de:
vsetvli t0,zero,e32,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_1499e2:
vse32.v v24,(a2),v0.t
.Lpc_1499e6:
c.addi a2,16
.Lpc_1499e8:
vse32.v v25,(a4),v0.t
.Lpc_1499ec:
c.addi a4,16
.Lpc_1499ee:
vse32.v v26,(a2),v0.t
.Lpc_1499f2:
c.addi a2,16
.Lpc_1499f4:
vse32.v v27,(a4),v0.t
.Lpc_1499f8:
c.addi a4,16
.Lpc_1499fa:
vse32.v v28,(a2),v0.t
.Lpc_1499fe:
c.addi a2,16
.Lpc_149a00:
vse32.v v29,(a4),v0.t
.Lpc_149a04:
c.addi a4,16
.Lpc_149a06:
vse32.v v30,(a2),v0.t
.Lpc_149a0a:
vse32.v v31,(a4),v0.t
.Lpc_149a0e:
c.ldsp a4,0(sp)
.Lpc_149a10:
c.addi t5,16
.Lpc_149a12:
c.add s7,s9
.Lpc_149a14:
c.add t6,a4
.Lpc_149a16:
addi a5,a5,64
.Lpc_149a1a:
bltu t5,a6,.Lpc_1497c4
.Lpc_149a1e:
c.ldsp s1,376(sp)
.Lpc_149a20:
c.ldsp s2,368(sp)
.Lpc_149a22:
c.ldsp s3,360(sp)
.Lpc_149a24:
c.ldsp s4,352(sp)
.Lpc_149a26:
c.ldsp s5,344(sp)
.Lpc_149a28:
c.ldsp s6,336(sp)
.Lpc_149a2a:
c.ldsp s7,328(sp)
.Lpc_149a2c:
c.ldsp s9,312(sp)
.Lpc_149a2e:
c.ldsp s10,304(sp)
.Lpc_149a30:
c.ldsp s8,320(sp)
.Lpc_149a32:
c.li a0,4
.Lpc_149a34:
c.j .Lpc_149762
.Lpc_149a36:
c.ldsp s10,8(sp)
.Lpc_149a38:
addi s8,zero,64
.Lpc_149a3c:
vsetvli t0,zero,e32,m8,tu,mu
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_149a40:
vxor.vv v24,v24,v24
.Lpc_149a44:
c.mv t3,s11
.Lpc_149a46:
vsetvli t0,zero,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_149a4a:
c.li s1,24
.Lpc_149a4c:
vmv.v.i v1,3
.Lpc_149a50:
vsetvli t0,s1,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_149a54:
vmv.v.i v1,2
.Lpc_149a58:
vsetvli t0,zero,e8,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E8
.Lpc_149a5c:
vmv.v.i v1,1
.Lpc_149a60:
vsetvli t0,zero,e8,mf4,tu,mu
# LLVM-MCA-RISCV-LMUL MF4
# LLVM-MCA-RISCV-SEW E8
.Lpc_149a64:
vmv.v.i v1,0
.Lpc_149a68:
c.mv a1,s0
.Lpc_149a6a:
c.mv s1,a0
.Lpc_149a6c:
c.mv s5,s1
.Lpc_149a6e:
addi s6,s1,32
.Lpc_149a72:
addi s1,s6,16
.Lpc_149a76:
addi s2,s1,32
.Lpc_149a7a:
addi s3,s1,64
.Lpc_149a7e:
addi s4,s1,96
.Lpc_149a82:
vsetvli t0,zero,e32,m8,tu,mu
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_149a86:
vxor.vv v16,v16,v16
.Lpc_149a8a:
flw ft1,0(a1)
.Lpc_149a8e:
flw ft2,4(a1)
.Lpc_149a92:
flw ft3,8(a1)
.Lpc_149a96:
flw ft4,12(a1)
.Lpc_149a9a:
c.addi a1,16
.Lpc_149a9c:
c.mv t2,a7
.Lpc_149a9e:
vsetvli t0,zero,e8,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E8
.Lpc_149aa2:
vle8.v v11,(s6)
.Lpc_149aa6:
vsetvli t0,zero,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_149aaa:
vrgather.vv v12,v11,v1
.Lpc_149aae:
vadd.vi v1,v1,4
.Lpc_149ab2:
vrgather.vv v13,v11,v1
.Lpc_149ab6:
vadd.vi v1,v1,4
.Lpc_149aba:
vrgather.vv v14,v11,v1
.Lpc_149abe:
vadd.vi v1,v1,4
.Lpc_149ac2:
vrgather.vv v15,v11,v1
.Lpc_149ac6:
vadd.vi v1,v1,-12
.Lpc_149aca:
vsetvli t0,zero,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_149ace:
vle8.v v6,(s1)
.Lpc_149ad2:
addi s1,s1,128
.Lpc_149ad6:
vle8.v v7,(s2)
.Lpc_149ada:
addi s2,s2,128
.Lpc_149ade:
vle8.v v8,(s3)
.Lpc_149ae2:
addi s3,s3,128
.Lpc_149ae6:
vle8.v v9,(s4)
.Lpc_149aea:
addi s4,s4,128
.Lpc_149aee:
vand.vi v2,v6,15
.Lpc_149af2:
vand.vi v3,v7,15
.Lpc_149af6:
vand.vi v4,v8,15
.Lpc_149afa:
vand.vi v5,v9,15
.Lpc_149afe:
vsrl.vi v6,v6,4
.Lpc_149b02:
vsrl.vi v7,v7,4
.Lpc_149b06:
vsrl.vi v8,v8,4
.Lpc_149b0a:
vsrl.vi v9,v9,4
.Lpc_149b0e:
vle8.v v10,(a1)
.Lpc_149b12:
addi a1,a1,32
.Lpc_149b16:
vle8.v v11,(a1)
.Lpc_149b1a:
addi a1,a1,32
.Lpc_149b1e:
vsub.vv v2,v2,v12
.Lpc_149b22:
vsub.vv v6,v6,v12
.Lpc_149b26:
vsub.vv v3,v3,v13
.Lpc_149b2a:
vsub.vv v7,v7,v13
.Lpc_149b2e:
vsub.vv v4,v4,v14
.Lpc_149b32:
vsub.vv v8,v8,v14
.Lpc_149b36:
vsub.vv v5,v5,v15
.Lpc_149b3a:
vsub.vv v9,v9,v15
.Lpc_149b5e:
c.addi t2,-1
.Lpc_149b60:
bne t2,zero,.Lpc_149aca
.Lpc_149b64:
addi s2,s5,-8
.Lpc_149b68:
addi s3,s5,8
.Lpc_149b6c:
addi s4,s5,16
.Lpc_149b70:
addi s6,s5,24
.Lpc_149b74:
addi t1,zero,240
.Lpc_149b78:
vmv.s.x v0,t1
.Lpc_149b7c:
vsetvli t0,zero,e16,mf4,tu,mu
# LLVM-MCA-RISCV-LMUL MF4
# LLVM-MCA-RISCV-SEW E16
.Lpc_149b80:
vle16.v v9,(s5)
.Lpc_149b84:
vle16.v v11,(s3)
.Lpc_149b88:
vle16.v v13,(s4)
.Lpc_149b8c:
vle16.v v15,(s6)
.Lpc_149b90:
vsetvli t0,zero,e16,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E16
.Lpc_149b94:
vle16.v v9,(s2),v0.t
.Lpc_149b98:
vle16.v v11,(s5),v0.t
.Lpc_149b9c:
vle16.v v13,(s3),v0.t
.Lpc_149ba0:
vle16.v v15,(s4),v0.t
.Lpc_149ba4:
vfwcvt.f.f.v v4,v9
.Lpc_149ba8:
vfwcvt.f.f.v v5,v11
.Lpc_149bac:
vfwcvt.f.f.v v6,v13
.Lpc_149bb0:
vfwcvt.f.f.v v7,v15
.Lpc_149bb4:
vsetvli t0,zero,e32,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_149bb8:
vfmv.v.f v2,ft1
.Lpc_149bbc:
vfmerge.vfm v2,v2,ft2,v0
.Lpc_149bc0:
vfmv.v.f v3,ft3
.Lpc_149bc4:
vfmerge.vfm v3,v3,ft4,v0
.Lpc_149bc8:
vfmul.vv v8,v4,v2
.Lpc_149bcc:
vfmul.vv v9,v4,v3
.Lpc_149bd0:
vfmul.vv v10,v5,v2
.Lpc_149bd4:
vfmul.vv v11,v5,v3
.Lpc_149bd8:
vfmul.vv v12,v6,v2
.Lpc_149bdc:
vfmul.vv v13,v6,v3
.Lpc_149be0:
vfmul.vv v14,v7,v2
.Lpc_149be4:
vfmul.vv v15,v7,v3
.Lpc_149be8:
vsetvli t0,zero,e32,m8,tu,mu
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_149bec:
vfcvt.f.x.v v16,v16
.Lpc_149bf0:
vfmacc.vv v24,v16,v8
.Lpc_149bf4:
c.addi t3,-1
.Lpc_149bf6:
bne t3,zero,.Lpc_149a6c
.Lpc_149bfa:
c.mv a1,s10
.Lpc_149bfc:
add a2,s10,s8
.Lpc_149c00:
add a3,a2,s8
.Lpc_149c04:
add a4,a3,s8
.Lpc_149c08:
c.addi a2,-16
.Lpc_149c0a:
c.addi a4,-16
.Lpc_149c0c:
addi t1,zero,240
.Lpc_149c10:
vmv.s.x v0,t1
.Lpc_149c14:
vsetvli t0,zero,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_149c18:
vse32.v v24,(a1)
.Lpc_149c1c:
c.addi a1,16
.Lpc_149c1e:
vse32.v v25,(a3)
.Lpc_149c22:
c.addi a3,16
.Lpc_149c24:
vse32.v v26,(a1)
.Lpc_149c28:
c.addi a1,16
.Lpc_149c2a:
vse32.v v27,(a3)
.Lpc_149c2e:
c.addi a3,16
.Lpc_149c30:
vse32.v v28,(a1)
.Lpc_149c34:
c.addi a1,16
.Lpc_149c36:
vse32.v v29,(a3)
.Lpc_149c3a:
c.addi a3,16
.Lpc_149c3c:
vse32.v v30,(a1)
.Lpc_149c40:
vse32.v v31,(a3)
.Lpc_149c44:
vsetvli t0,zero,e32,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_149c48:
vse32.v v24,(a2),v0.t
.Lpc_149c4c:
c.addi a2,16
.Lpc_149c4e:
vse32.v v25,(a4),v0.t
.Lpc_149c52:
c.addi a4,16
.Lpc_149c54:
vse32.v v26,(a2),v0.t
.Lpc_149c58:
c.addi a2,16
.Lpc_149c5a:
vse32.v v27,(a4),v0.t
.Lpc_149c5e:
c.addi a4,16
.Lpc_149c60:
vse32.v v28,(a2),v0.t
.Lpc_149c64:
c.addi a2,16
.Lpc_149c66:
vse32.v v29,(a4),v0.t
.Lpc_149c6a:
c.addi a4,16
.Lpc_149c6c:
vse32.v v30,(a2),v0.t
.Lpc_149c70:
vse32.v v31,(a4),v0.t
.Lpc_149c74:
c.ldsp a4,0(sp)
.Lpc_149c76:
c.addi t5,16
.Lpc_149c78:
c.add s7,s9
.Lpc_149c7a:
c.add t6,a4
.Lpc_149c7c:
c.add a5,s8
.Lpc_149c7e:
bgeu t5,a6,.Lpc_149a1e
.Lpc_149c82:
c.mv s10,s8
.Lpc_149c84:
c.j .Lpc_1497c4
.Lpc_149c86:
beq a6,zero,.Lpc_14a2e6
.Lpc_149c8a:
mul a0,a0,a7
.Lpc_149c8e:
c.sdsp s7,328(sp)
.Lpc_149c90:
c.sdsp s8,320(sp)
.Lpc_149c92:
c.sdsp s1,376(sp)
.Lpc_149c94:
slli s8,a7,0x5
.Lpc_149c98:
c.sdsp s2,368(sp)
.Lpc_149c9a:
c.sdsp s3,360(sp)
.Lpc_149c9c:
c.sdsp s4,352(sp)
.Lpc_149c9e:
c.sdsp s5,344(sp)
.Lpc_149ca0:
c.sdsp s6,336(sp)
.Lpc_149ca2:
c.mv a5,a4
.Lpc_149ca4:
c.li t6,0
.Lpc_149ca6:
c.li t4,0
.Lpc_149ca8:
c.li a7,0
.Lpc_149caa:
c.li s7,16
.Lpc_149cac:
c.slli a0,0x4
.Lpc_149cae:
sub a4,a6,a7
.Lpc_149cb2:
bgeu s7,a4,.Lpc_149cb8
.Lpc_149cb6:
c.li a4,16
.Lpc_149cb8:
srli a3,t4,0x1
.Lpc_149cbc:
c.add a3,t6
.Lpc_149cbe:
c.add a3,a2
.Lpc_149cc0:
c.mv t1,s11
.Lpc_149cc2:
vsetvli t0,zero,e32,m4,tu,mu
# LLVM-MCA-RISCV-LMUL M4
# LLVM-MCA-RISCV-SEW E32
.Lpc_149cc6:
vxor.vv v28,v28,v28
.Lpc_149cca:
c.mv s1,a3
.Lpc_149ccc:
addi s2,a3,8
.Lpc_149cd0:
addi s3,a3,16
.Lpc_149cd4:
addi s4,a3,24
.Lpc_149cd8:
c.mv s5,a1
.Lpc_149cda:
addi s6,a1,12
.Lpc_149cde:
vsetvli t0,zero,e16,mf4,tu,mu
# LLVM-MCA-RISCV-LMUL MF4
# LLVM-MCA-RISCV-SEW E16
.Lpc_149ce2:
vle16.v v4,(s1)
.Lpc_149ce6:
addi s1,s1,32
.Lpc_149cea:
vle16.v v5,(s2)
.Lpc_149cee:
addi s2,s2,56
.Lpc_149cf2:
vle16.v v6,(s3)
.Lpc_149cf6:
addi s3,s3,80
.Lpc_149cfa:
vle16.v v7,(s4)
.Lpc_149cfe:
addi s4,s4,104
.Lpc_149d02:
flw ft1,0(s5)
.Lpc_149d06:
c.addi s5,4
.Lpc_149d08:
vfwcvt.f.f.v v8,v4
.Lpc_149d0c:
vfwcvt.f.f.v v9,v5
.Lpc_149d10:
vfwcvt.f.f.v v10,v6
.Lpc_149d14:
vfwcvt.f.f.v v11,v7
.Lpc_149d18:
vsetvli t0,zero,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_149d1c:
c.mv t5,s0
.Lpc_149d1e:
vxor.vv v16,v16,v16
.Lpc_149d22:
vxor.vv v18,v18,v18
.Lpc_149d26:
vxor.vv v20,v20,v20
.Lpc_149d2a:
vxor.vv v22,v22,v22
.Lpc_149d2e:
vfmul.vf v24,v8,ft1
.Lpc_149d32:
vfmul.vf v25,v9,ft1
.Lpc_149d36:
vfmul.vf v26,v10,ft1
.Lpc_149d3a:
vfmul.vf v27,v11,ft1
.Lpc_149d3e:
c.addi t1,-1
.Lpc_149d40:
vsetvli t0,zero,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_149d44:
vle8.v v4,(s1)
.Lpc_149d48:
addi s1,s1,128
.Lpc_149d4c:
vle8.v v5,(s2)
.Lpc_149d50:
addi s2,s2,128
.Lpc_149d54:
vle8.v v6,(s3)
.Lpc_149d58:
addi s3,s3,128
.Lpc_149d5c:
vle8.v v7,(s4)
.Lpc_149d60:
addi s4,s4,128
.Lpc_149d64:
vsetvli t0,zero,e8,mf4,tu,mu
# LLVM-MCA-RISCV-LMUL MF4
# LLVM-MCA-RISCV-SEW E8
.Lpc_149d68:
vle8.v v14,(s5)
.Lpc_149d6c:
c.addi s5,16
.Lpc_149d6e:
vle8.v v15,(s6)
.Lpc_149d72:
c.addi s6,16
.Lpc_149d74:
c.addi t5,-1
.Lpc_149d76:
vsetvli t0,zero,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_149d7a:
vand.vi v0,v4,15
.Lpc_149d7e:
vand.vi v1,v5,15
.Lpc_149d82:
vand.vi v2,v6,15
.Lpc_149d86:
vand.vi v3,v7,15
.Lpc_149d8a:
vsrl.vi v4,v4,4
.Lpc_149d8e:
vsrl.vi v5,v5,4
.Lpc_149d92:
vsrl.vi v6,v6,4
.Lpc_149d96:
vsrl.vi v7,v7,4
.Lpc_149d9a:
vadd.vi v0,v0,-8
.Lpc_149d9e:
vadd.vi v1,v1,-8
.Lpc_149da2:
vadd.vi v2,v2,-8
.Lpc_149da6:
vadd.vi v3,v3,-8
.Lpc_149daa:
vadd.vi v4,v4,-8
.Lpc_149dae:
vadd.vi v5,v5,-8
.Lpc_149db2:
vadd.vi v6,v6,-8
.Lpc_149db6:
vadd.vi v7,v7,-8
.Lpc_149dda:
bne t5,zero,.Lpc_149d44
.Lpc_149dde:
vsetvli t0,zero,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_149de2:
vfcvt.f.x.v v16,v16
.Lpc_149de6:
vfcvt.f.x.v v18,v18
.Lpc_149dea:
vfcvt.f.x.v v20,v20
.Lpc_149dee:
vfcvt.f.x.v v22,v22
.Lpc_149df2:
addi s2,s1,8
.Lpc_149df6:
addi s3,s1,16
.Lpc_149dfa:
addi s4,s1,24
.Lpc_149dfe:
addi s6,s5,12
.Lpc_149e02:
vfmacc.vv v28,v16,v24
.Lpc_149e06:
vfmacc.vv v29,v18,v25
.Lpc_149e0a:
vfmacc.vv v30,v20,v26
.Lpc_149e0e:
vfmacc.vv v31,v22,v27
.Lpc_149e12:
bne t1,zero,.Lpc_149cde
.Lpc_149e16:
c.li t3,16
.Lpc_149e18:
addi s1,a5,16
.Lpc_149e1c:
addi s2,a5,32
.Lpc_149e20:
addi s3,a5,48
.Lpc_149e24:
blt a4,t3,.Lpc_149e3c
.Lpc_149e28:
vse32.v v28,(a5)
.Lpc_149e2c:
vse32.v v29,(s1)
.Lpc_149e30:
vse32.v v30,(s2)
.Lpc_149e34:
vse32.v v31,(s3)
.Lpc_149e38:
jal zero,.Lpc_149e6c
.Lpc_149e3c:
vsetvli t0,a4,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_149e40:
sub a4,a4,t0
.Lpc_149e44:
vse32.v v28,(a5)
.Lpc_149e48:
vsetvli t0,a4,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_149e4c:
sub a4,a4,t0
.Lpc_149e50:
vse32.v v29,(s1)
.Lpc_149e54:
vsetvli t0,a4,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_149e58:
sub a4,a4,t0
.Lpc_149e5c:
vse32.v v30,(s2)
.Lpc_149e60:
vsetvli t0,a4,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_149e64:
sub a4,a4,t0
.Lpc_149e68:
vse32.v v31,(s3)
.Lpc_149e6c:
c.addi a7,16
.Lpc_149e6e:
c.add t4,a0
.Lpc_149e70:
c.add t6,s8
.Lpc_149e72:
addi a5,a5,64
.Lpc_149e76:
bltu a7,a6,.Lpc_149cae
.Lpc_149e7a:
c.ldsp s1,376(sp)
.Lpc_149e7c:
c.ldsp s2,368(sp)
.Lpc_149e7e:
c.ldsp s3,360(sp)
.Lpc_149e80:
c.ldsp s4,352(sp)
.Lpc_149e82:
c.ldsp s5,344(sp)
.Lpc_149e84:
c.ldsp s6,336(sp)
.Lpc_149e86:
c.ldsp s7,328(sp)
.Lpc_149e88:
c.ldsp s8,320(sp)
.Lpc_149e8a:
c.li a0,1
.Lpc_149e8c:
c.j .Lpc_149762
.Lpc_149e8e:
beq a6,zero,.Lpc_149a30
.Lpc_149e92:
mul a0,a0,a7
.Lpc_149e96:
c.sdsp s7,328(sp)
.Lpc_149e98:
c.sdsp s9,312(sp)
.Lpc_149e9a:
slli s7,a7,0x5
.Lpc_149e9e:
c.mv a5,a4
.Lpc_149ea0:
c.addi4spn a4,sp,24
.Lpc_149ea2:
c.sdsp s10,304(sp)
.Lpc_149ea4:
c.sdsp s1,376(sp)
.Lpc_149ea6:
c.mv s10,s8
.Lpc_149ea8:
c.sdsp s2,368(sp)
.Lpc_149eaa:
c.mv s8,s7
.Lpc_149eac:
slli s9,a0,0x4
.Lpc_149eb0:
c.sdsp s9,0(sp)
.Lpc_149eb2:
c.sdsp s3,360(sp)
.Lpc_149eb4:
c.sdsp s4,352(sp)
.Lpc_149eb6:
c.sdsp s5,344(sp)
.Lpc_149eb8:
c.sdsp s6,336(sp)
.Lpc_149eba:
c.li t5,0
.Lpc_149ebc:
c.li t4,0
.Lpc_149ebe:
c.li a7,0
.Lpc_149ec0:
c.sdsp a4,8(sp)
.Lpc_149ec2:
c.mv s9,a1
.Lpc_149ec4:
c.mv s7,a2
.Lpc_149ec6:
srli a0,t4,0x1
.Lpc_149eca:
c.add a0,t5
.Lpc_149ecc:
sub a4,a6,a7
.Lpc_149ed0:
c.li a3,15
.Lpc_149ed2:
c.add a0,s7
.Lpc_149ed4:
bgeu a3,a4,.Lpc_14a0e4
.Lpc_149ed8:
vsetvli t0,zero,e32,m8,tu,mu
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_149edc:
vxor.vv v24,v24,v24
.Lpc_149ee0:
c.mv t3,s11
.Lpc_149ee2:
c.mv a1,s9
.Lpc_149ee4:
c.mv s1,a0
.Lpc_149ee6:
c.mv s5,s1
.Lpc_149ee8:
addi s1,s5,32
.Lpc_149eec:
addi s2,s1,32
.Lpc_149ef0:
addi s3,s1,64
.Lpc_149ef4:
addi s4,s1,96
.Lpc_149ef8:
vsetvli t0,zero,e32,m8,tu,mu
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_149efc:
vxor.vv v16,v16,v16
.Lpc_149f00:
flw ft1,0(a1)
.Lpc_149f04:
flw ft2,4(a1)
.Lpc_149f08:
flw ft3,8(a1)
.Lpc_149f0c:
flw ft4,12(a1)
.Lpc_149f10:
c.addi a1,16
.Lpc_149f12:
c.mv t2,s0
.Lpc_149f14:
vsetvli t0,zero,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_149f18:
vle8.v v6,(s1)
.Lpc_149f1c:
addi s1,s1,128
.Lpc_149f20:
vle8.v v7,(s2)
.Lpc_149f24:
addi s2,s2,128
.Lpc_149f28:
vle8.v v8,(s3)
.Lpc_149f2c:
addi s3,s3,128
.Lpc_149f30:
vle8.v v9,(s4)
.Lpc_149f34:
addi s4,s4,128
.Lpc_149f38:
vand.vi v2,v6,15
.Lpc_149f3c:
vand.vi v3,v7,15
.Lpc_149f40:
vand.vi v4,v8,15
.Lpc_149f44:
vand.vi v5,v9,15
.Lpc_149f48:
vsrl.vi v6,v6,4
.Lpc_149f4c:
vsrl.vi v7,v7,4
.Lpc_149f50:
vsrl.vi v8,v8,4
.Lpc_149f54:
vsrl.vi v9,v9,4
.Lpc_149f58:
vsetvli t0,zero,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_149f5c:
vle8.v v10,(a1)
.Lpc_149f60:
addi a1,a1,32
.Lpc_149f64:
vle8.v v11,(a1)
.Lpc_149f68:
addi a1,a1,32
.Lpc_149f6c:
vadd.vi v2,v2,-8
.Lpc_149f70:
vadd.vi v3,v3,-8
.Lpc_149f74:
vadd.vi v4,v4,-8
.Lpc_149f78:
vadd.vi v5,v5,-8
.Lpc_149f7c:
vadd.vi v6,v6,-8
.Lpc_149f80:
vadd.vi v7,v7,-8
.Lpc_149f84:
vadd.vi v8,v8,-8
.Lpc_149f88:
vadd.vi v9,v9,-8
.Lpc_149fac:
c.addi t2,-1
.Lpc_149fae:
bne t2,zero,.Lpc_149f14
.Lpc_149fb2:
addi s2,s5,-8
.Lpc_149fb6:
addi s3,s5,8
.Lpc_149fba:
addi s4,s5,16
.Lpc_149fbe:
addi s6,s5,24
.Lpc_149fc2:
addi t1,zero,240
.Lpc_149fc6:
vmv.s.x v0,t1
.Lpc_149fca:
vsetvli t0,zero,e16,mf4,tu,mu
# LLVM-MCA-RISCV-LMUL MF4
# LLVM-MCA-RISCV-SEW E16
.Lpc_149fce:
vle16.v v9,(s5)
.Lpc_149fd2:
vle16.v v11,(s3)
.Lpc_149fd6:
vle16.v v13,(s4)
.Lpc_149fda:
vle16.v v15,(s6)
.Lpc_149fde:
vsetvli t0,zero,e16,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E16
.Lpc_149fe2:
vle16.v v9,(s2),v0.t
.Lpc_149fe6:
vle16.v v11,(s5),v0.t
.Lpc_149fea:
vle16.v v13,(s3),v0.t
.Lpc_149fee:
vle16.v v15,(s4),v0.t
.Lpc_149ff2:
vfwcvt.f.f.v v4,v9
.Lpc_149ff6:
vfwcvt.f.f.v v5,v11
.Lpc_149ffa:
vfwcvt.f.f.v v6,v13
.Lpc_149ffe:
vfwcvt.f.f.v v7,v15
.Lpc_14a002:
vsetvli t0,zero,e32,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a006:
vfmv.v.f v2,ft1
.Lpc_14a00a:
vfmerge.vfm v2,v2,ft2,v0
.Lpc_14a00e:
vfmv.v.f v3,ft3
.Lpc_14a012:
vfmerge.vfm v3,v3,ft4,v0
.Lpc_14a016:
vfmul.vv v8,v4,v2
.Lpc_14a01a:
vfmul.vv v9,v4,v3
.Lpc_14a01e:
vfmul.vv v10,v5,v2
.Lpc_14a022:
vfmul.vv v11,v5,v3
.Lpc_14a026:
vfmul.vv v12,v6,v2
.Lpc_14a02a:
vfmul.vv v13,v6,v3
.Lpc_14a02e:
vfmul.vv v14,v7,v2
.Lpc_14a032:
vfmul.vv v15,v7,v3
.Lpc_14a036:
vsetvli t0,zero,e32,m8,tu,mu
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a03a:
vfcvt.f.x.v v16,v16
.Lpc_14a03e:
vfmacc.vv v24,v16,v8
.Lpc_14a042:
c.addi t3,-1
.Lpc_14a044:
bne t3,zero,.Lpc_149ee6
.Lpc_14a048:
c.mv a1,a5
.Lpc_14a04a:
add a2,a5,s10
.Lpc_14a04e:
add a3,a2,s10
.Lpc_14a052:
add a4,a3,s10
.Lpc_14a056:
c.addi a2,-16
.Lpc_14a058:
c.addi a4,-16
.Lpc_14a05a:
addi t1,zero,240
.Lpc_14a05e:
vmv.s.x v0,t1
.Lpc_14a062:
vsetvli t0,zero,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a066:
vse32.v v24,(a1)
.Lpc_14a06a:
c.addi a1,16
.Lpc_14a06c:
vse32.v v25,(a3)
.Lpc_14a070:
c.addi a3,16
.Lpc_14a072:
vse32.v v26,(a1)
.Lpc_14a076:
c.addi a1,16
.Lpc_14a078:
vse32.v v27,(a3)
.Lpc_14a07c:
c.addi a3,16
.Lpc_14a07e:
vse32.v v28,(a1)
.Lpc_14a082:
c.addi a1,16
.Lpc_14a084:
vse32.v v29,(a3)
.Lpc_14a088:
c.addi a3,16
.Lpc_14a08a:
vse32.v v30,(a1)
.Lpc_14a08e:
vse32.v v31,(a3)
.Lpc_14a092:
vsetvli t0,zero,e32,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a096:
vse32.v v24,(a2),v0.t
.Lpc_14a09a:
c.addi a2,16
.Lpc_14a09c:
vse32.v v25,(a4),v0.t
.Lpc_14a0a0:
c.addi a4,16
.Lpc_14a0a2:
vse32.v v26,(a2),v0.t
.Lpc_14a0a6:
c.addi a2,16
.Lpc_14a0a8:
vse32.v v27,(a4),v0.t
.Lpc_14a0ac:
c.addi a4,16
.Lpc_14a0ae:
vse32.v v28,(a2),v0.t
.Lpc_14a0b2:
c.addi a2,16
.Lpc_14a0b4:
vse32.v v29,(a4),v0.t
.Lpc_14a0b8:
c.addi a4,16
.Lpc_14a0ba:
vse32.v v30,(a2),v0.t
.Lpc_14a0be:
vse32.v v31,(a4),v0.t
.Lpc_14a0c2:
c.ldsp a4,0(sp)
.Lpc_14a0c4:
c.addi a7,16
.Lpc_14a0c6:
c.add t5,s8
.Lpc_14a0c8:
c.add t4,a4
.Lpc_14a0ca:
addi a5,a5,64
.Lpc_14a0ce:
bgeu a7,a6,.Lpc_149a1e
.Lpc_14a0d2:
srli a0,t4,0x1
.Lpc_14a0d6:
c.add a0,t5
.Lpc_14a0d8:
sub a4,a6,a7
.Lpc_14a0dc:
c.li a3,15
.Lpc_14a0de:
c.add a0,s7
.Lpc_14a0e0:
bltu a3,a4,.Lpc_149ed8
.Lpc_14a0e4:
c.ldsp s10,8(sp)
.Lpc_14a0e6:
addi t6,zero,64
.Lpc_14a0ea:
vsetvli t0,zero,e32,m8,tu,mu
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a0ee:
vxor.vv v24,v24,v24
.Lpc_14a0f2:
c.mv t3,s11
.Lpc_14a0f4:
c.mv a1,s9
.Lpc_14a0f6:
c.mv s1,a0
.Lpc_14a0f8:
c.mv s5,s1
.Lpc_14a0fa:
addi s1,s5,32
.Lpc_14a0fe:
addi s2,s1,32
.Lpc_14a102:
addi s3,s1,64
.Lpc_14a106:
addi s4,s1,96
.Lpc_14a10a:
vsetvli t0,zero,e32,m8,tu,mu
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a10e:
vxor.vv v16,v16,v16
.Lpc_14a112:
flw ft1,0(a1)
.Lpc_14a116:
flw ft2,4(a1)
.Lpc_14a11a:
flw ft3,8(a1)
.Lpc_14a11e:
flw ft4,12(a1)
.Lpc_14a122:
c.addi a1,16
.Lpc_14a124:
c.mv t2,s0
.Lpc_14a126:
vsetvli t0,zero,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_14a12a:
vle8.v v6,(s1)
.Lpc_14a12e:
addi s1,s1,128
.Lpc_14a132:
vle8.v v7,(s2)
.Lpc_14a136:
addi s2,s2,128
.Lpc_14a13a:
vle8.v v8,(s3)
.Lpc_14a13e:
addi s3,s3,128
.Lpc_14a142:
vle8.v v9,(s4)
.Lpc_14a146:
addi s4,s4,128
.Lpc_14a14a:
vand.vi v2,v6,15
.Lpc_14a14e:
vand.vi v3,v7,15
.Lpc_14a152:
vand.vi v4,v8,15
.Lpc_14a156:
vand.vi v5,v9,15
.Lpc_14a15a:
vsrl.vi v6,v6,4
.Lpc_14a15e:
vsrl.vi v7,v7,4
.Lpc_14a162:
vsrl.vi v8,v8,4
.Lpc_14a166:
vsrl.vi v9,v9,4
.Lpc_14a16a:
vsetvli t0,zero,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_14a16e:
vle8.v v10,(a1)
.Lpc_14a172:
addi a1,a1,32
.Lpc_14a176:
vle8.v v11,(a1)
.Lpc_14a17a:
addi a1,a1,32
.Lpc_14a17e:
vadd.vi v2,v2,-8
.Lpc_14a182:
vadd.vi v3,v3,-8
.Lpc_14a186:
vadd.vi v4,v4,-8
.Lpc_14a18a:
vadd.vi v5,v5,-8
.Lpc_14a18e:
vadd.vi v6,v6,-8
.Lpc_14a192:
vadd.vi v7,v7,-8
.Lpc_14a196:
vadd.vi v8,v8,-8
.Lpc_14a19a:
vadd.vi v9,v9,-8
.Lpc_14a1be:
c.addi t2,-1
.Lpc_14a1c0:
bne t2,zero,.Lpc_14a126
.Lpc_14a1c4:
addi s2,s5,-8
.Lpc_14a1c8:
addi s3,s5,8
.Lpc_14a1cc:
addi s4,s5,16
.Lpc_14a1d0:
addi s6,s5,24
.Lpc_14a1d4:
addi t1,zero,240
.Lpc_14a1d8:
vmv.s.x v0,t1
.Lpc_14a1dc:
vsetvli t0,zero,e16,mf4,tu,mu
# LLVM-MCA-RISCV-LMUL MF4
# LLVM-MCA-RISCV-SEW E16
.Lpc_14a1e0:
vle16.v v9,(s5)
.Lpc_14a1e4:
vle16.v v11,(s3)
.Lpc_14a1e8:
vle16.v v13,(s4)
.Lpc_14a1ec:
vle16.v v15,(s6)
.Lpc_14a1f0:
vsetvli t0,zero,e16,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E16
.Lpc_14a1f4:
vle16.v v9,(s2),v0.t
.Lpc_14a1f8:
vle16.v v11,(s5),v0.t
.Lpc_14a1fc:
vle16.v v13,(s3),v0.t
.Lpc_14a200:
vle16.v v15,(s4),v0.t
.Lpc_14a204:
vfwcvt.f.f.v v4,v9
.Lpc_14a208:
vfwcvt.f.f.v v5,v11
.Lpc_14a20c:
vfwcvt.f.f.v v6,v13
.Lpc_14a210:
vfwcvt.f.f.v v7,v15
.Lpc_14a214:
vsetvli t0,zero,e32,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a218:
vfmv.v.f v2,ft1
.Lpc_14a21c:
vfmerge.vfm v2,v2,ft2,v0
.Lpc_14a220:
vfmv.v.f v3,ft3
.Lpc_14a224:
vfmerge.vfm v3,v3,ft4,v0
.Lpc_14a228:
vfmul.vv v8,v4,v2
.Lpc_14a22c:
vfmul.vv v9,v4,v3
.Lpc_14a230:
vfmul.vv v10,v5,v2
.Lpc_14a234:
vfmul.vv v11,v5,v3
.Lpc_14a238:
vfmul.vv v12,v6,v2
.Lpc_14a23c:
vfmul.vv v13,v6,v3
.Lpc_14a240:
vfmul.vv v14,v7,v2
.Lpc_14a244:
vfmul.vv v15,v7,v3
.Lpc_14a248:
vsetvli t0,zero,e32,m8,tu,mu
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a24c:
vfcvt.f.x.v v16,v16
.Lpc_14a250:
vfmacc.vv v24,v16,v8
.Lpc_14a254:
c.addi t3,-1
.Lpc_14a256:
bne t3,zero,.Lpc_14a0f8
.Lpc_14a25a:
c.mv a1,s10
.Lpc_14a25c:
add a2,s10,t6
.Lpc_14a260:
add a3,a2,t6
.Lpc_14a264:
add a4,a3,t6
.Lpc_14a268:
c.addi a2,-16
.Lpc_14a26a:
c.addi a4,-16
.Lpc_14a26c:
addi t1,zero,240
.Lpc_14a270:
vmv.s.x v0,t1
.Lpc_14a274:
vsetvli t0,zero,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a278:
vse32.v v24,(a1)
.Lpc_14a27c:
c.addi a1,16
.Lpc_14a27e:
vse32.v v25,(a3)
.Lpc_14a282:
c.addi a3,16
.Lpc_14a284:
vse32.v v26,(a1)
.Lpc_14a288:
c.addi a1,16
.Lpc_14a28a:
vse32.v v27,(a3)
.Lpc_14a28e:
c.addi a3,16
.Lpc_14a290:
vse32.v v28,(a1)
.Lpc_14a294:
c.addi a1,16
.Lpc_14a296:
vse32.v v29,(a3)
.Lpc_14a29a:
c.addi a3,16
.Lpc_14a29c:
vse32.v v30,(a1)
.Lpc_14a2a0:
vse32.v v31,(a3)
.Lpc_14a2a4:
vsetvli t0,zero,e32,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a2a8:
vse32.v v24,(a2),v0.t
.Lpc_14a2ac:
c.addi a2,16
.Lpc_14a2ae:
vse32.v v25,(a4),v0.t
.Lpc_14a2b2:
c.addi a4,16
.Lpc_14a2b4:
vse32.v v26,(a2),v0.t
.Lpc_14a2b8:
c.addi a2,16
.Lpc_14a2ba:
vse32.v v27,(a4),v0.t
.Lpc_14a2be:
c.addi a4,16
.Lpc_14a2c0:
vse32.v v28,(a2),v0.t
.Lpc_14a2c4:
c.addi a2,16
.Lpc_14a2c6:
vse32.v v29,(a4),v0.t
.Lpc_14a2ca:
c.addi a4,16
.Lpc_14a2cc:
vse32.v v30,(a2),v0.t
.Lpc_14a2d0:
vse32.v v31,(a4),v0.t
.Lpc_14a2d4:
c.ldsp a4,0(sp)
.Lpc_14a2d6:
c.addi a7,16
.Lpc_14a2d8:
c.add t5,s8
.Lpc_14a2da:
c.add t4,a4
.Lpc_14a2dc:
c.add a5,t6
.Lpc_14a2de:
bgeu a7,a6,.Lpc_149a1e
.Lpc_14a2e2:
c.mv s10,t6
.Lpc_14a2e4:
c.j .Lpc_149ec6
.Lpc_14a2e6:
c.li a0,1
.Lpc_14a2e8:
jal zero,.Lpc_149762
.Lpc_14a2ec:
c.sdsp s1,376(sp)
.Lpc_14a2ee:
c.sdsp s2,368(sp)
.Lpc_14a2f0:
c.sdsp s3,360(sp)
.Lpc_14a2f2:
c.sdsp s4,352(sp)
.Lpc_14a2f4:
c.sdsp s5,344(sp)
.Lpc_14a2f6:
c.sdsp s6,336(sp)
.Lpc_14a2f8:
c.sdsp s7,328(sp)
.Lpc_14a2fa:
c.sdsp s8,320(sp)
.Lpc_14a2fc:
c.sdsp s9,312(sp)
.Lpc_14a2fe:
c.sdsp s10,304(sp)
.Lpc_14a300:
jal ra,.Lpc_87330
