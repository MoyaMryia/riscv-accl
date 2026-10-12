.text
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a304:
c.addi16sp sp,-80
.Lpc_14a306:
c.sdsp ra,72(sp)
.Lpc_14a308:
c.li a3,3
.Lpc_14a30a:
c.mv t4,a1
.Lpc_14a30c:
c.mv t6,a2
.Lpc_14a30e:
bltu a3,a5,.Lpc_14a4ec
.Lpc_14a312:
srli t1,a0,0x4
.Lpc_14a316:
beq a6,zero,.Lpc_14a71e
.Lpc_14a31a:
c.sdsp s1,56(sp)
.Lpc_14a31c:
c.sdsp s2,48(sp)
.Lpc_14a31e:
c.sdsp s3,40(sp)
.Lpc_14a320:
c.sdsp s4,32(sp)
.Lpc_14a322:
c.sdsp s5,24(sp)
.Lpc_14a324:
c.sdsp s6,16(sp)
.Lpc_14a326:
c.sdsp s7,8(sp)
.Lpc_14a328:
c.li a2,0
.Lpc_14a32a:
c.li t2,16
.Lpc_14a32c:
sub a3,a6,a2
.Lpc_14a330:
bgeu t2,a3,.Lpc_14a336
.Lpc_14a334:
c.li a3,16
.Lpc_14a336:
srli a1,a2,0x4
.Lpc_14a33a:
mul a1,a1,a7
.Lpc_14a33e:
c.mv a0,a7
.Lpc_14a340:
slli a5,a1,0x4
.Lpc_14a344:
c.add a5,a1
.Lpc_14a346:
c.slli a5,0x5
.Lpc_14a348:
c.add a5,t6
.Lpc_14a34a:
vsetvli t0,zero,e32,m4,tu,mu
# LLVM-MCA-RISCV-LMUL M4
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a34e:
vxor.vv v28,v28,v28
.Lpc_14a352:
c.mv s7,a5
.Lpc_14a354:
c.mv s5,t4
.Lpc_14a356:
addi s6,t4,12
.Lpc_14a35a:
addi s1,s7,32
.Lpc_14a35e:
addi s2,s7,8
.Lpc_14a362:
addi s3,s7,16
.Lpc_14a366:
addi s4,s7,24
.Lpc_14a36a:
vsetvli t0,zero,e16,mf4,tu,mu
# LLVM-MCA-RISCV-LMUL MF4
# LLVM-MCA-RISCV-SEW E16
.Lpc_14a36e:
vle16.v v4,(s7)
.Lpc_14a372:
vle16.v v5,(s2)
.Lpc_14a376:
vle16.v v6,(s3)
.Lpc_14a37a:
vle16.v v7,(s4)
.Lpc_14a37e:
addi s7,s7,544
.Lpc_14a382:
flw ft1,0(s5)
.Lpc_14a386:
c.addi s5,4
.Lpc_14a388:
vfwcvt.f.f.v v8,v4
.Lpc_14a38c:
vfwcvt.f.f.v v9,v5
.Lpc_14a390:
vfwcvt.f.f.v v10,v6
.Lpc_14a394:
vfwcvt.f.f.v v11,v7
.Lpc_14a398:
vsetvli t0,zero,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a39c:
c.mv t5,t1
.Lpc_14a39e:
vxor.vv v16,v16,v16
.Lpc_14a3a2:
vxor.vv v18,v18,v18
.Lpc_14a3a6:
vxor.vv v20,v20,v20
.Lpc_14a3aa:
vxor.vv v22,v22,v22
.Lpc_14a3ae:
vfmul.vf v24,v8,ft1
.Lpc_14a3b2:
vfmul.vf v25,v9,ft1
.Lpc_14a3b6:
vfmul.vf v26,v10,ft1
.Lpc_14a3ba:
vfmul.vf v27,v11,ft1
.Lpc_14a3be:
c.addi a0,-1
.Lpc_14a3c0:
vsetvli t0,zero,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_14a3c4:
vle8.v v0,(s1)
.Lpc_14a3c8:
addi s1,s1,32
.Lpc_14a3cc:
vle8.v v1,(s1)
.Lpc_14a3d0:
addi s1,s1,32
.Lpc_14a3d4:
vle8.v v2,(s1)
.Lpc_14a3d8:
addi s1,s1,32
.Lpc_14a3dc:
vle8.v v3,(s1)
.Lpc_14a3e0:
addi s1,s1,32
.Lpc_14a3e4:
vle8.v v4,(s1)
.Lpc_14a3e8:
addi s1,s1,32
.Lpc_14a3ec:
vle8.v v5,(s1)
.Lpc_14a3f0:
addi s1,s1,32
.Lpc_14a3f4:
vle8.v v6,(s1)
.Lpc_14a3f8:
addi s1,s1,32
.Lpc_14a3fc:
vle8.v v7,(s1)
.Lpc_14a400:
addi s1,s1,32
.Lpc_14a404:
vsetvli t0,zero,e8,mf4,tu,mu
# LLVM-MCA-RISCV-LMUL MF4
# LLVM-MCA-RISCV-SEW E8
.Lpc_14a408:
vle8.v v14,(s5)
.Lpc_14a40c:
c.addi s5,16
.Lpc_14a40e:
vle8.v v15,(s6)
.Lpc_14a412:
c.addi s6,16
.Lpc_14a414:
c.addi t5,-1
.Lpc_14a416:
vsetvli t0,zero,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_14a43a:
bne t5,zero,.Lpc_14a3c4
.Lpc_14a43e:
vsetvli t0,zero,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a442:
vfcvt.f.x.v v16,v16
.Lpc_14a446:
vfcvt.f.x.v v18,v18
.Lpc_14a44a:
vfcvt.f.x.v v20,v20
.Lpc_14a44e:
vfcvt.f.x.v v22,v22
.Lpc_14a452:
addi s2,s1,8
.Lpc_14a456:
addi s3,s1,16
.Lpc_14a45a:
addi s4,s1,24
.Lpc_14a45e:
addi s6,s5,12
.Lpc_14a462:
vfmacc.vv v28,v16,v24
.Lpc_14a466:
vfmacc.vv v29,v18,v25
.Lpc_14a46a:
vfmacc.vv v30,v20,v26
.Lpc_14a46e:
vfmacc.vv v31,v22,v27
.Lpc_14a472:
bne a0,zero,.Lpc_14a35a
.Lpc_14a476:
c.li t3,16
.Lpc_14a478:
addi s1,a4,16
.Lpc_14a47c:
addi s2,a4,32
.Lpc_14a480:
addi s3,a4,48
.Lpc_14a484:
blt a3,t3,.Lpc_14a49c
.Lpc_14a488:
vse32.v v28,(a4)
.Lpc_14a48c:
vse32.v v29,(s1)
.Lpc_14a490:
vse32.v v30,(s2)
.Lpc_14a494:
vse32.v v31,(s3)
.Lpc_14a498:
jal zero,.Lpc_14a4cc
.Lpc_14a49c:
vsetvli t0,a3,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a4a0:
sub a3,a3,t0
.Lpc_14a4a4:
vse32.v v28,(a4)
.Lpc_14a4a8:
vsetvli t0,a3,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a4ac:
sub a3,a3,t0
.Lpc_14a4b0:
vse32.v v29,(s1)
.Lpc_14a4b4:
vsetvli t0,a3,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a4b8:
sub a3,a3,t0
.Lpc_14a4bc:
vse32.v v30,(s2)
.Lpc_14a4c0:
vsetvli t0,a3,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a4c4:
sub a3,a3,t0
.Lpc_14a4c8:
vse32.v v31,(s3)
.Lpc_14a4cc:
c.addi a2,16
.Lpc_14a4ce:
addi a4,a4,64
.Lpc_14a4d2:
bltu a2,a6,.Lpc_14a32c
.Lpc_14a4d6:
c.li a0,1
.Lpc_14a4d8:
c.ldsp s1,56(sp)
.Lpc_14a4da:
c.ldsp s2,48(sp)
.Lpc_14a4dc:
c.ldsp s3,40(sp)
.Lpc_14a4de:
c.ldsp s4,32(sp)
.Lpc_14a4e0:
c.ldsp s5,24(sp)
.Lpc_14a4e2:
c.ldsp s6,16(sp)
.Lpc_14a4e4:
c.ldsp s7,8(sp)
.Lpc_14a4e6:
c.ldsp ra,72(sp)
.Lpc_14a4e8:
c.addi16sp sp,80
.Lpc_14a4ea:
c.jr ra
.Lpc_14a4ec:
c.sdsp s0,64(sp)
.Lpc_14a4ee:
andi s0,a6,15
.Lpc_14a4f2:
bne s0,zero,.Lpc_14a72a
.Lpc_14a4f6:
c.ldsp a5,80(sp)
.Lpc_14a4f8:
c.sdsp s7,8(sp)
.Lpc_14a4fa:
c.srli a0,0x4
.Lpc_14a4fc:
slli s7,a5,0x2
.Lpc_14a500:
beq a6,zero,.Lpc_14a722
.Lpc_14a504:
c.sdsp s1,56(sp)
.Lpc_14a506:
c.sdsp s2,48(sp)
.Lpc_14a508:
c.sdsp s3,40(sp)
.Lpc_14a50a:
c.sdsp s4,32(sp)
.Lpc_14a50c:
c.sdsp s5,24(sp)
.Lpc_14a50e:
c.sdsp s6,16(sp)
.Lpc_14a510:
c.mv a5,a4
.Lpc_14a512:
srli a4,s0,0x4
.Lpc_14a516:
mul a4,a4,a7
.Lpc_14a51a:
slli t5,a4,0x4
.Lpc_14a51e:
c.add t5,a4
.Lpc_14a520:
c.slli t5,0x5
.Lpc_14a522:
c.add t5,t6
.Lpc_14a524:
vsetvli t0,zero,e32,m8,tu,mu
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a528:
vxor.vv v24,v24,v24
.Lpc_14a52c:
c.mv t3,a7
.Lpc_14a52e:
c.mv a1,t4
.Lpc_14a530:
c.mv s1,t5
.Lpc_14a532:
c.mv s5,s1
.Lpc_14a534:
addi s1,s5,32
.Lpc_14a538:
vsetvli t0,zero,e32,m8,tu,mu
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a53c:
vxor.vv v16,v16,v16
.Lpc_14a540:
flw ft1,0(a1)
.Lpc_14a544:
flw ft2,4(a1)
.Lpc_14a548:
flw ft3,8(a1)
.Lpc_14a54c:
flw ft4,12(a1)
.Lpc_14a550:
c.addi a1,16
.Lpc_14a552:
c.mv t2,a0
.Lpc_14a554:
vsetvli t0,zero,e8,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E8
.Lpc_14a558:
vle8.v v2,(s1)
.Lpc_14a55c:
addi s1,s1,32
.Lpc_14a560:
vle8.v v3,(s1)
.Lpc_14a564:
addi s1,s1,32
.Lpc_14a568:
vle8.v v4,(s1)
.Lpc_14a56c:
addi s1,s1,32
.Lpc_14a570:
vle8.v v5,(s1)
.Lpc_14a574:
addi s1,s1,32
.Lpc_14a578:
vle8.v v6,(s1)
.Lpc_14a57c:
addi s1,s1,32
.Lpc_14a580:
vle8.v v7,(s1)
.Lpc_14a584:
addi s1,s1,32
.Lpc_14a588:
vle8.v v8,(s1)
.Lpc_14a58c:
addi s1,s1,32
.Lpc_14a590:
vle8.v v9,(s1)
.Lpc_14a594:
addi s1,s1,32
.Lpc_14a598:
vle8.v v10,(a1)
.Lpc_14a59c:
addi a1,a1,32
.Lpc_14a5a0:
vle8.v v11,(a1)
.Lpc_14a5a4:
addi a1,a1,32
.Lpc_14a5c8:
c.addi t2,-1
.Lpc_14a5ca:
bne t2,zero,.Lpc_14a554
.Lpc_14a5ce:
addi s2,s5,-8
.Lpc_14a5d2:
addi s3,s5,8
.Lpc_14a5d6:
addi s4,s5,16
.Lpc_14a5da:
addi s6,s5,24
.Lpc_14a5de:
addi t1,zero,240
.Lpc_14a5e2:
vmv.s.x v0,t1
.Lpc_14a5e6:
vsetvli t0,zero,e16,mf4,tu,mu
# LLVM-MCA-RISCV-LMUL MF4
# LLVM-MCA-RISCV-SEW E16
.Lpc_14a5ea:
vle16.v v9,(s5)
.Lpc_14a5ee:
vle16.v v11,(s3)
.Lpc_14a5f2:
vle16.v v13,(s4)
.Lpc_14a5f6:
vle16.v v15,(s6)
.Lpc_14a5fa:
vsetvli t0,zero,e16,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E16
.Lpc_14a5fe:
vle16.v v9,(s2),v0.t
.Lpc_14a602:
vle16.v v11,(s5),v0.t
.Lpc_14a606:
vle16.v v13,(s3),v0.t
.Lpc_14a60a:
vle16.v v15,(s4),v0.t
.Lpc_14a60e:
vfwcvt.f.f.v v8,v9
.Lpc_14a612:
vfwcvt.f.f.v v10,v11
.Lpc_14a616:
vfwcvt.f.f.v v12,v13
.Lpc_14a61a:
vfwcvt.f.f.v v14,v15
.Lpc_14a61e:
vsetvli t0,zero,e32,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a622:
vmv.v.v v9,v8
.Lpc_14a626:
vmv.v.v v11,v10
.Lpc_14a62a:
vmv.v.v v13,v12
.Lpc_14a62e:
vmv.v.v v15,v14
.Lpc_14a632:
addi t1,zero,240
.Lpc_14a636:
vmv.s.x v0,t1
.Lpc_14a63a:
vsetvli t0,zero,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a63e:
vfmul.vf v8,v8,ft1
.Lpc_14a642:
vfmul.vf v10,v10,ft1
.Lpc_14a646:
vfmul.vf v12,v12,ft1
.Lpc_14a64a:
vfmul.vf v14,v14,ft1
.Lpc_14a64e:
vfmul.vf v9,v9,ft3
.Lpc_14a652:
vfmul.vf v11,v11,ft3
.Lpc_14a656:
vfmul.vf v13,v13,ft3
.Lpc_14a65a:
vfmul.vf v15,v15,ft3
.Lpc_14a65e:
vsetvli t0,zero,e32,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a662:
vfmul.vf v8,v8,ft2,v0.t
.Lpc_14a666:
vfmul.vf v10,v10,ft2,v0.t
.Lpc_14a66a:
vfmul.vf v12,v12,ft2,v0.t
.Lpc_14a66e:
vfmul.vf v14,v14,ft2,v0.t
.Lpc_14a672:
vfmul.vf v9,v9,ft4,v0.t
.Lpc_14a676:
vfmul.vf v11,v11,ft4,v0.t
.Lpc_14a67a:
vfmul.vf v13,v13,ft4,v0.t
.Lpc_14a67e:
vfmul.vf v15,v15,ft4,v0.t
.Lpc_14a682:
vsetvli t0,zero,e32,m8,tu,mu
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a686:
vfcvt.f.x.v v16,v16
.Lpc_14a68a:
vfmacc.vv v24,v16,v8
.Lpc_14a68e:
c.addi t3,-1
.Lpc_14a690:
bne t3,zero,.Lpc_14a532
.Lpc_14a694:
c.mv a1,a5
.Lpc_14a696:
add a2,a5,s7
.Lpc_14a69a:
add a3,a2,s7
.Lpc_14a69e:
add a4,a3,s7
.Lpc_14a6a2:
c.addi a2,-16
.Lpc_14a6a4:
c.addi a4,-16
.Lpc_14a6a6:
addi t1,zero,240
.Lpc_14a6aa:
vmv.s.x v0,t1
.Lpc_14a6ae:
vsetvli t0,zero,e32,mf2,tu,mu
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a6b2:
vse32.v v24,(a1)
.Lpc_14a6b6:
c.addi a1,16
.Lpc_14a6b8:
vse32.v v25,(a3)
.Lpc_14a6bc:
c.addi a3,16
.Lpc_14a6be:
vse32.v v26,(a1)
.Lpc_14a6c2:
c.addi a1,16
.Lpc_14a6c4:
vse32.v v27,(a3)
.Lpc_14a6c8:
c.addi a3,16
.Lpc_14a6ca:
vse32.v v28,(a1)
.Lpc_14a6ce:
c.addi a1,16
.Lpc_14a6d0:
vse32.v v29,(a3)
.Lpc_14a6d4:
c.addi a3,16
.Lpc_14a6d6:
vse32.v v30,(a1)
.Lpc_14a6da:
vse32.v v31,(a3)
.Lpc_14a6de:
vsetvli t0,zero,e32,m1,tu,mu
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_14a6e2:
vse32.v v24,(a2),v0.t
.Lpc_14a6e6:
c.addi a2,16
.Lpc_14a6e8:
vse32.v v25,(a4),v0.t
.Lpc_14a6ec:
c.addi a4,16
.Lpc_14a6ee:
vse32.v v26,(a2),v0.t
.Lpc_14a6f2:
c.addi a2,16
.Lpc_14a6f4:
vse32.v v27,(a4),v0.t
.Lpc_14a6f8:
c.addi a4,16
.Lpc_14a6fa:
vse32.v v28,(a2),v0.t
.Lpc_14a6fe:
c.addi a2,16
.Lpc_14a700:
vse32.v v29,(a4),v0.t
.Lpc_14a704:
c.addi a4,16
.Lpc_14a706:
vse32.v v30,(a2),v0.t
.Lpc_14a70a:
vse32.v v31,(a4),v0.t
.Lpc_14a70e:
c.addi s0,16
.Lpc_14a710:
addi a5,a5,64
.Lpc_14a714:
bltu s0,a6,.Lpc_14a512
.Lpc_14a718:
c.ldsp s0,64(sp)
.Lpc_14a71a:
c.li a0,4
.Lpc_14a71c:
c.j .Lpc_14a4d8
.Lpc_14a71e:
c.li a0,1
.Lpc_14a720:
c.j .Lpc_14a4e6
.Lpc_14a722:
c.ldsp s0,64(sp)
.Lpc_14a724:
c.ldsp s7,8(sp)
.Lpc_14a726:
c.li a0,4
.Lpc_14a728:
c.j .Lpc_14a4e6
.Lpc_14a72a:
auipc a3,0x80
.Lpc_14a72e:
addi a3,a3,326 # .Lpc_1ca870
.Lpc_14a732:
auipc a2,0x7b
.Lpc_14a736:
addi a2,a2,1790 # .Lpc_1c5e30
.Lpc_14a73a:
addi a1,zero,1049
.Lpc_14a73e:
auipc a0,0x80
.Lpc_14a742:
addi a0,a0,330 # .Lpc_1ca888
.Lpc_14a746:
c.sdsp s1,56(sp)
.Lpc_14a748:
c.sdsp s2,48(sp)
.Lpc_14a74a:
c.sdsp s3,40(sp)
.Lpc_14a74c:
c.sdsp s4,32(sp)
.Lpc_14a74e:
c.sdsp s5,24(sp)
.Lpc_14a750:
c.sdsp s6,16(sp)
.Lpc_14a752:
c.sdsp s7,8(sp)
.Lpc_14a754:
jal ra,.Lpc_85420
