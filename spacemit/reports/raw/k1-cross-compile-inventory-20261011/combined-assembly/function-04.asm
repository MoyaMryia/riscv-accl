
/home/moyamryia/Projects/riscv-accl/lab/k1-combined-fixture-r5-20261011-122000-work/payload/C/lib/libggml-cpu.so.0.16.0:     file format elf64-littleriscv


Disassembly of section .text:

00000000001494dc <_ZN16spacemit_kernels4ime116gemm_kernel_i8i4EmPKhS2_S2_Pfmmmm>:
  1494dc:	7165                	c.addi16sp	sp,-400
  1494de:	e322                	c.sdsp	s0,384(sp)
  1494e0:	000e4417          	auipc	s0,0xe4
  1494e4:	0d843403          	ld	s0,216(s0) # 22d5b8 <__stack_chk_guard@GLIBC_2.27>
  1494e8:	f66e                	c.sdsp	s11,296(sp)
  1494ea:	00043303          	ld	t1,0(s0)
  1494ee:	ee1a                	c.sdsp	t1,280(sp)
  1494f0:	4301                	c.li	t1,0
  1494f2:	e706                	c.sdsp	ra,392(sp)
  1494f4:	4e0d                	c.li	t3,3
  1494f6:	8dc6                	c.mv	s11,a7
  1494f8:	00455413          	srli	s0,a0,0x4
  1494fc:	28fe6263          	bltu	t3,a5,149780 <END149+0x40>
  149500:	78068363          	beq	a3,zero,149c86 <RESULT_SAVE299+0x8c>
  149504:	5e0801e3          	beq	a6,zero,14a2e6 <RESULT_SAVE453+0x8c>
  149508:	03150533          	mul	a0,a0,a7
  14950c:	e2e2                	c.sdsp	s8,320(sp)
  14950e:	2118ac33          	sh1add	s8,a7,a7
  149512:	fe66                	c.sdsp	s9,312(sp)
  149514:	fea6                	c.sdsp	s1,376(sp)
  149516:	faca                	c.sdsp	s2,368(sp)
  149518:	f6ce                	c.sdsp	s3,360(sp)
  14951a:	f2d2                	c.sdsp	s4,352(sp)
  14951c:	eed6                	c.sdsp	s5,344(sp)
  14951e:	eada                	c.sdsp	s6,336(sp)
  149520:	e6de                	c.sdsp	s7,328(sp)
  149522:	87ba                	c.mv	a5,a4
  149524:	0c12                	c.slli	s8,0x4
  149526:	4f81                	c.li	t6,0
  149528:	4e81                	c.li	t4,0
  14952a:	4881                	c.li	a7,0
  14952c:	4cc1                	c.li	s9,16
  14952e:	0512                	c.slli	a0,0x4
  149530:	41180733          	sub	a4,a6,a7
  149534:	00ecf363          	bgeu	s9,a4,14953a <_ZN16spacemit_kernels4ime116gemm_kernel_i8i4EmPKhS2_S2_Pfmmmm+0x5e>
  149538:	4741                	c.li	a4,16
  14953a:	001ed693          	srli	a3,t4,0x1
  14953e:	96fe                	c.add	a3,t6
  149540:	96b2                	c.add	a3,a2
  149542:	836e                	c.mv	t1,s11
  149544:	012072d7          	vsetvli	t0,zero,e32,m4,tu,mu
  149548:	2fce0e57          	vxor.vv	v28,v28,v28
  14954c:	000072d7          	vsetvli	t0,zero,e8,m1,tu,mu
  149550:	5e01b6d7          	vmv.v.i	v13,3
  149554:	44e1                	c.li	s1,24
  149556:	0004f2d7          	vsetvli	t0,s1,e8,m1,tu,mu
  14955a:	5e0136d7          	vmv.v.i	v13,2
  14955e:	007072d7          	vsetvli	t0,zero,e8,mf2,tu,mu
  149562:	5e00b6d7          	vmv.v.i	v13,1
  149566:	006072d7          	vsetvli	t0,zero,e8,mf4,tu,mu
  14956a:	5e0036d7          	vmv.v.i	v13,0
  14956e:	84b6                	c.mv	s1,a3
  149570:	00868913          	addi	s2,a3,8
  149574:	01068993          	addi	s3,a3,16
  149578:	01868a13          	addi	s4,a3,24
  14957c:	02068b93          	addi	s7,a3,32
  149580:	8aae                	c.mv	s5,a1
  149582:	00c58b13          	addi	s6,a1,12

0000000000149586 <LOOP_K149>:
  149586:	00e072d7          	vsetvli	t0,zero,e16,mf4,tu,mu
  14958a:	0204d207          	vle16.v	v4,(s1)
  14958e:	03048493          	addi	s1,s1,48
  149592:	02095287          	vle16.v	v5,(s2)
  149596:	04890913          	addi	s2,s2,72
  14959a:	0209d307          	vle16.v	v6,(s3)
  14959e:	06098993          	addi	s3,s3,96
  1495a2:	020a5387          	vle16.v	v7,(s4)
  1495a6:	078a0a13          	addi	s4,s4,120
  1495aa:	000aa087          	flw	ft1,0(s5)
  1495ae:	0a91                	c.addi	s5,4
  1495b0:	4a461457          	vfwcvt.f.f.v	v8,v4
  1495b4:	4a5614d7          	vfwcvt.f.f.v	v9,v5
  1495b8:	4a661557          	vfwcvt.f.f.v	v10,v6
  1495bc:	4a7615d7          	vfwcvt.f.f.v	v11,v7
  1495c0:	017072d7          	vsetvli	t0,zero,e32,mf2,tu,mu
  1495c4:	8f22                	c.mv	t5,s0
  1495c6:	2f080857          	vxor.vv	v16,v16,v16
  1495ca:	2f290957          	vxor.vv	v18,v18,v18
  1495ce:	2f4a0a57          	vxor.vv	v20,v20,v20
  1495d2:	2f6b0b57          	vxor.vv	v22,v22,v22
  1495d6:	9280dc57          	vfmul.vf	v24,v8,ft1
  1495da:	9290dcd7          	vfmul.vf	v25,v9,ft1
  1495de:	92a0dd57          	vfmul.vf	v26,v10,ft1
  1495e2:	92b0ddd7          	vfmul.vf	v27,v11,ft1
  1495e6:	137d                	c.addi	t1,-1
  1495e8:	007072d7          	vsetvli	t0,zero,e8,mf2,tu,mu
  1495ec:	020b8087          	vle8.v	v1,(s7)
  1495f0:	000072d7          	vsetvli	t0,zero,e8,m1,tu,mu
  1495f4:	32168457          	vrgather.vv	v8,v1,v13
  1495f8:	02d236d7          	vadd.vi	v13,v13,4
  1495fc:	321684d7          	vrgather.vv	v9,v1,v13
  149600:	02d236d7          	vadd.vi	v13,v13,4
  149604:	32168557          	vrgather.vv	v10,v1,v13
  149608:	02d236d7          	vadd.vi	v13,v13,4
  14960c:	321685d7          	vrgather.vv	v11,v1,v13
  149610:	02da36d7          	vadd.vi	v13,v13,-12

0000000000149614 <LOOP_INNER149>:
  149614:	02048207          	vle8.v	v4,(s1)
  149618:	08048493          	addi	s1,s1,128
  14961c:	02090287          	vle8.v	v5,(s2)
  149620:	08090913          	addi	s2,s2,128
  149624:	02098307          	vle8.v	v6,(s3)
  149628:	08098993          	addi	s3,s3,128
  14962c:	020a0387          	vle8.v	v7,(s4)
  149630:	080a0a13          	addi	s4,s4,128
  149634:	006072d7          	vsetvli	t0,zero,e8,mf4,tu,mu
  149638:	020a8707          	vle8.v	v14,(s5)
  14963c:	0ac1                	c.addi	s5,16
  14963e:	020b0787          	vle8.v	v15,(s6)
  149642:	0b41                	c.addi	s6,16
  149644:	1f7d                	c.addi	t5,-1
  149646:	000072d7          	vsetvli	t0,zero,e8,m1,tu,mu
  14964a:	2647b057          	vand.vi	v0,v4,15
  14964e:	2657b0d7          	vand.vi	v1,v5,15
  149652:	2667b157          	vand.vi	v2,v6,15
  149656:	2677b1d7          	vand.vi	v3,v7,15
  14965a:	a2423257          	vsrl.vi	v4,v4,4
  14965e:	a25232d7          	vsrl.vi	v5,v5,4
  149662:	a2623357          	vsrl.vi	v6,v6,4
  149666:	a27233d7          	vsrl.vi	v7,v7,4
  14966a:	0a040057          	vsub.vv	v0,v0,v8
  14966e:	0a440257          	vsub.vv	v4,v4,v8
  149672:	0a1480d7          	vsub.vv	v1,v1,v9
  149676:	0a5482d7          	vsub.vv	v5,v5,v9
  14967a:	0a250157          	vsub.vv	v2,v2,v10
  14967e:	0a650357          	vsub.vv	v6,v6,v10
  149682:	0a3581d7          	vsub.vv	v3,v3,v11
  149686:	0a7583d7          	vsub.vv	v7,v7,v11
  14968a:	e207382b          	.insn	4, 0xe207382b
  14968e:	e217392b          	.insn	4, 0xe217392b
  149692:	e2273a2b          	.insn	4, 0xe2273a2b
  149696:	e2373b2b          	.insn	4, 0xe2373b2b
  14969a:	e247b82b          	.insn	4, 0xe247b82b
  14969e:	e257b92b          	.insn	4, 0xe257b92b
  1496a2:	e267ba2b          	.insn	4, 0xe267ba2b
  1496a6:	e277bb2b          	.insn	4, 0xe277bb2b
  1496aa:	f60f15e3          	bne	t5,zero,149614 <LOOP_INNER149>
  1496ae:	017072d7          	vsetvli	t0,zero,e32,mf2,tu,mu
  1496b2:	4b019857          	vfcvt.f.x.v	v16,v16
  1496b6:	4b219957          	vfcvt.f.x.v	v18,v18
  1496ba:	4b419a57          	vfcvt.f.x.v	v20,v20
  1496be:	4b619b57          	vfcvt.f.x.v	v22,v22
  1496c2:	00848913          	addi	s2,s1,8
  1496c6:	01048993          	addi	s3,s1,16
  1496ca:	01848a13          	addi	s4,s1,24
  1496ce:	00ca8b13          	addi	s6,s5,12
  1496d2:	b3881e57          	vfmacc.vv	v28,v16,v24
  1496d6:	b3991ed7          	vfmacc.vv	v29,v18,v25
  1496da:	b3aa1f57          	vfmacc.vv	v30,v20,v26
  1496de:	b3bb1fd7          	vfmacc.vv	v31,v22,v27
  1496e2:	02048b93          	addi	s7,s1,32
  1496e6:	ea0310e3          	bne	t1,zero,149586 <LOOP_K149>
  1496ea:	4e41                	c.li	t3,16
  1496ec:	01078493          	addi	s1,a5,16
  1496f0:	02078913          	addi	s2,a5,32
  1496f4:	03078993          	addi	s3,a5,48
  1496f8:	01c74c63          	blt	a4,t3,149710 <ST_TAIL149>
  1496fc:	0207ee27          	vse32.v	v28,(a5)
  149700:	0204eea7          	vse32.v	v29,(s1)
  149704:	02096f27          	vse32.v	v30,(s2)
  149708:	0209efa7          	vse32.v	v31,(s3)
  14970c:	0340006f          	jal	zero,149740 <END149>

0000000000149710 <ST_TAIL149>:
  149710:	017772d7          	vsetvli	t0,a4,e32,mf2,tu,mu
  149714:	40570733          	sub	a4,a4,t0
  149718:	0207ee27          	vse32.v	v28,(a5)
  14971c:	017772d7          	vsetvli	t0,a4,e32,mf2,tu,mu
  149720:	40570733          	sub	a4,a4,t0
  149724:	0204eea7          	vse32.v	v29,(s1)
  149728:	017772d7          	vsetvli	t0,a4,e32,mf2,tu,mu
  14972c:	40570733          	sub	a4,a4,t0
  149730:	02096f27          	vse32.v	v30,(s2)
  149734:	017772d7          	vsetvli	t0,a4,e32,mf2,tu,mu
  149738:	40570733          	sub	a4,a4,t0
  14973c:	0209efa7          	vse32.v	v31,(s3)

0000000000149740 <END149>:
  149740:	08c1                	c.addi	a7,16
  149742:	9eaa                	c.add	t4,a0
  149744:	9fe2                	c.add	t6,s8
  149746:	04078793          	addi	a5,a5,64
  14974a:	df08e3e3          	bltu	a7,a6,149530 <_ZN16spacemit_kernels4ime116gemm_kernel_i8i4EmPKhS2_S2_Pfmmmm+0x54>
  14974e:	74f6                	c.ldsp	s1,376(sp)
  149750:	7956                	c.ldsp	s2,368(sp)
  149752:	79b6                	c.ldsp	s3,360(sp)
  149754:	7a16                	c.ldsp	s4,352(sp)
  149756:	6af6                	c.ldsp	s5,344(sp)
  149758:	6b56                	c.ldsp	s6,336(sp)
  14975a:	6bb6                	c.ldsp	s7,328(sp)
  14975c:	6c16                	c.ldsp	s8,320(sp)
  14975e:	7cf2                	c.ldsp	s9,312(sp)
  149760:	4505                	c.li	a0,1
  149762:	000e4797          	auipc	a5,0xe4
  149766:	e567b783          	ld	a5,-426(a5) # 22d5b8 <__stack_chk_guard@GLIBC_2.27>
  14976a:	6772                	c.ldsp	a4,280(sp)
  14976c:	639c                	c.ld	a5,0(a5)
  14976e:	8fb9                	c.xor	a5,a4
  149770:	4701                	c.li	a4,0
  149772:	36079de3          	bne	a5,zero,14a2ec <RESULT_SAVE453+0x92>
  149776:	60ba                	c.ldsp	ra,392(sp)
  149778:	641a                	c.ldsp	s0,384(sp)
  14977a:	7db2                	c.ldsp	s11,296(sp)
  14977c:	6159                	c.addi16sp	sp,400
  14977e:	8082                	c.jr	ra
  149780:	67da                	c.ldsp	a5,400(sp)
  149782:	e2e2                	c.sdsp	s8,320(sp)
  149784:	00279c13          	slli	s8,a5,0x2
  149788:	70068363          	beq	a3,zero,149e8e <END360+0x22>
  14978c:	2a080263          	beq	a6,zero,149a30 <RESULT_SAVE251+0x9c>
  149790:	03150533          	mul	a0,a0,a7
  149794:	fe66                	c.sdsp	s9,312(sp)
  149796:	87ba                	c.mv	a5,a4
  149798:	2118acb3          	sh1add	s9,a7,a7
  14979c:	0838                	c.addi4spn	a4,sp,24
  14979e:	e6de                	c.sdsp	s7,328(sp)
  1497a0:	fa6a                	c.sdsp	s10,304(sp)
  1497a2:	88a2                	c.mv	a7,s0
  1497a4:	fea6                	c.sdsp	s1,376(sp)
  1497a6:	faca                	c.sdsp	s2,368(sp)
  1497a8:	f6ce                	c.sdsp	s3,360(sp)
  1497aa:	0512                	c.slli	a0,0x4
  1497ac:	f2d2                	c.sdsp	s4,352(sp)
  1497ae:	eed6                	c.sdsp	s5,344(sp)
  1497b0:	eada                	c.sdsp	s6,336(sp)
  1497b2:	0c92                	c.slli	s9,0x4
  1497b4:	4b81                	c.li	s7,0
  1497b6:	4f81                	c.li	t6,0
  1497b8:	4f01                	c.li	t5,0
  1497ba:	e43a                	c.sdsp	a4,8(sp)
  1497bc:	8d62                	c.mv	s10,s8
  1497be:	e02a                	c.sdsp	a0,0(sp)
  1497c0:	842e                	c.mv	s0,a1
  1497c2:	8eb2                	c.mv	t4,a2
  1497c4:	001fd513          	srli	a0,t6,0x1
  1497c8:	955e                	c.add	a0,s7
  1497ca:	41e80733          	sub	a4,a6,t5
  1497ce:	46bd                	c.li	a3,15
  1497d0:	9576                	c.add	a0,t4
  1497d2:	26e6f263          	bgeu	a3,a4,149a36 <RESULT_SAVE251+0xa2>
  1497d6:	013072d7          	vsetvli	t0,zero,e32,m8,tu,mu
  1497da:	2f8c0c57          	vxor.vv	v24,v24,v24
  1497de:	8e6e                	c.mv	t3,s11
  1497e0:	000072d7          	vsetvli	t0,zero,e8,m1,tu,mu
  1497e4:	44e1                	c.li	s1,24
  1497e6:	5e01b0d7          	vmv.v.i	v1,3
  1497ea:	0004f2d7          	vsetvli	t0,s1,e8,m1,tu,mu
  1497ee:	5e0130d7          	vmv.v.i	v1,2
  1497f2:	007072d7          	vsetvli	t0,zero,e8,mf2,tu,mu
  1497f6:	5e00b0d7          	vmv.v.i	v1,1
  1497fa:	006072d7          	vsetvli	t0,zero,e8,mf4,tu,mu
  1497fe:	5e0030d7          	vmv.v.i	v1,0
  149802:	85a2                	c.mv	a1,s0
  149804:	84aa                	c.mv	s1,a0

0000000000149806 <BLOCK_COUNTK_LOOP251>:
  149806:	8aa6                	c.mv	s5,s1
  149808:	02048b13          	addi	s6,s1,32
  14980c:	010b0493          	addi	s1,s6,16
  149810:	02048913          	addi	s2,s1,32
  149814:	04048993          	addi	s3,s1,64
  149818:	06048a13          	addi	s4,s1,96
  14981c:	013072d7          	vsetvli	t0,zero,e32,m8,tu,mu
  149820:	2f080857          	vxor.vv	v16,v16,v16
  149824:	0005a087          	flw	ft1,0(a1)
  149828:	0045a107          	flw	ft2,4(a1)
  14982c:	0085a187          	flw	ft3,8(a1)
  149830:	00c5a207          	flw	ft4,12(a1)
  149834:	05c1                	c.addi	a1,16
  149836:	83c6                	c.mv	t2,a7
  149838:	007072d7          	vsetvli	t0,zero,e8,mf2,tu,mu
  14983c:	020b0587          	vle8.v	v11,(s6)
  149840:	000072d7          	vsetvli	t0,zero,e8,m1,tu,mu
  149844:	32b08657          	vrgather.vv	v12,v11,v1
  149848:	021230d7          	vadd.vi	v1,v1,4
  14984c:	32b086d7          	vrgather.vv	v13,v11,v1
  149850:	021230d7          	vadd.vi	v1,v1,4
  149854:	32b08757          	vrgather.vv	v14,v11,v1
  149858:	021230d7          	vadd.vi	v1,v1,4
  14985c:	32b087d7          	vrgather.vv	v15,v11,v1
  149860:	021a30d7          	vadd.vi	v1,v1,-12

0000000000149864 <BLOCK_INNER_LOOP251>:
  149864:	000072d7          	vsetvli	t0,zero,e8,m1,tu,mu
  149868:	02048307          	vle8.v	v6,(s1)
  14986c:	08048493          	addi	s1,s1,128
  149870:	02090387          	vle8.v	v7,(s2)
  149874:	08090913          	addi	s2,s2,128
  149878:	02098407          	vle8.v	v8,(s3)
  14987c:	08098993          	addi	s3,s3,128
  149880:	020a0487          	vle8.v	v9,(s4)
  149884:	080a0a13          	addi	s4,s4,128
  149888:	2667b157          	vand.vi	v2,v6,15
  14988c:	2677b1d7          	vand.vi	v3,v7,15
  149890:	2687b257          	vand.vi	v4,v8,15
  149894:	2697b2d7          	vand.vi	v5,v9,15
  149898:	a2623357          	vsrl.vi	v6,v6,4
  14989c:	a27233d7          	vsrl.vi	v7,v7,4
  1498a0:	a2823457          	vsrl.vi	v8,v8,4
  1498a4:	a29234d7          	vsrl.vi	v9,v9,4
  1498a8:	02058507          	vle8.v	v10,(a1)
  1498ac:	02058593          	addi	a1,a1,32
  1498b0:	02058587          	vle8.v	v11,(a1)
  1498b4:	02058593          	addi	a1,a1,32
  1498b8:	0a260157          	vsub.vv	v2,v2,v12
  1498bc:	0a660357          	vsub.vv	v6,v6,v12
  1498c0:	0a3681d7          	vsub.vv	v3,v3,v13
  1498c4:	0a7683d7          	vsub.vv	v7,v7,v13
  1498c8:	0a470257          	vsub.vv	v4,v4,v14
  1498cc:	0a870457          	vsub.vv	v8,v8,v14
  1498d0:	0a5782d7          	vsub.vv	v5,v5,v15
  1498d4:	0a9784d7          	vsub.vv	v9,v9,v15
  1498d8:	e225382b          	.insn	4, 0xe225382b
  1498dc:	e235392b          	.insn	4, 0xe235392b
  1498e0:	e2453a2b          	.insn	4, 0xe2453a2b
  1498e4:	e2553b2b          	.insn	4, 0xe2553b2b
  1498e8:	e265b82b          	.insn	4, 0xe265b82b
  1498ec:	e275b92b          	.insn	4, 0xe275b92b
  1498f0:	e285ba2b          	.insn	4, 0xe285ba2b
  1498f4:	e295bb2b          	.insn	4, 0xe295bb2b
  1498f8:	13fd                	c.addi	t2,-1
  1498fa:	f60395e3          	bne	t2,zero,149864 <BLOCK_INNER_LOOP251>
  1498fe:	ff8a8913          	addi	s2,s5,-8
  149902:	008a8993          	addi	s3,s5,8
  149906:	010a8a13          	addi	s4,s5,16
  14990a:	018a8b13          	addi	s6,s5,24
  14990e:	0f000313          	addi	t1,zero,240
  149912:	42036057          	vmv.s.x	v0,t1
  149916:	00e072d7          	vsetvli	t0,zero,e16,mf4,tu,mu
  14991a:	020ad487          	vle16.v	v9,(s5)
  14991e:	0209d587          	vle16.v	v11,(s3)
  149922:	020a5687          	vle16.v	v13,(s4)
  149926:	020b5787          	vle16.v	v15,(s6)
  14992a:	00f072d7          	vsetvli	t0,zero,e16,mf2,tu,mu
  14992e:	00095487          	vle16.v	v9,(s2),v0.t
  149932:	000ad587          	vle16.v	v11,(s5),v0.t
  149936:	0009d687          	vle16.v	v13,(s3),v0.t
  14993a:	000a5787          	vle16.v	v15,(s4),v0.t
  14993e:	4a961257          	vfwcvt.f.f.v	v4,v9
  149942:	4ab612d7          	vfwcvt.f.f.v	v5,v11
  149946:	4ad61357          	vfwcvt.f.f.v	v6,v13
  14994a:	4af613d7          	vfwcvt.f.f.v	v7,v15
  14994e:	010072d7          	vsetvli	t0,zero,e32,m1,tu,mu
  149952:	5e00d157          	vfmv.v.f	v2,ft1
  149956:	5c215157          	vfmerge.vfm	v2,v2,ft2,v0
  14995a:	5e01d1d7          	vfmv.v.f	v3,ft3
  14995e:	5c3251d7          	vfmerge.vfm	v3,v3,ft4,v0
  149962:	92411457          	vfmul.vv	v8,v4,v2
  149966:	924194d7          	vfmul.vv	v9,v4,v3
  14996a:	92511557          	vfmul.vv	v10,v5,v2
  14996e:	925195d7          	vfmul.vv	v11,v5,v3
  149972:	92611657          	vfmul.vv	v12,v6,v2
  149976:	926196d7          	vfmul.vv	v13,v6,v3
  14997a:	92711757          	vfmul.vv	v14,v7,v2
  14997e:	927197d7          	vfmul.vv	v15,v7,v3
  149982:	013072d7          	vsetvli	t0,zero,e32,m8,tu,mu
  149986:	4b019857          	vfcvt.f.x.v	v16,v16
  14998a:	b2881c57          	vfmacc.vv	v24,v16,v8
  14998e:	1e7d                	c.addi	t3,-1
  149990:	e60e1be3          	bne	t3,zero,149806 <BLOCK_COUNTK_LOOP251>

0000000000149994 <RESULT_SAVE251>:
  149994:	85be                	c.mv	a1,a5
  149996:	01a78633          	add	a2,a5,s10
  14999a:	01a606b3          	add	a3,a2,s10
  14999e:	01a68733          	add	a4,a3,s10
  1499a2:	1641                	c.addi	a2,-16
  1499a4:	1741                	c.addi	a4,-16
  1499a6:	0f000313          	addi	t1,zero,240
  1499aa:	42036057          	vmv.s.x	v0,t1
  1499ae:	017072d7          	vsetvli	t0,zero,e32,mf2,tu,mu
  1499b2:	0205ec27          	vse32.v	v24,(a1)
  1499b6:	05c1                	c.addi	a1,16
  1499b8:	0206eca7          	vse32.v	v25,(a3)
  1499bc:	06c1                	c.addi	a3,16
  1499be:	0205ed27          	vse32.v	v26,(a1)
  1499c2:	05c1                	c.addi	a1,16
  1499c4:	0206eda7          	vse32.v	v27,(a3)
  1499c8:	06c1                	c.addi	a3,16
  1499ca:	0205ee27          	vse32.v	v28,(a1)
  1499ce:	05c1                	c.addi	a1,16
  1499d0:	0206eea7          	vse32.v	v29,(a3)
  1499d4:	06c1                	c.addi	a3,16
  1499d6:	0205ef27          	vse32.v	v30,(a1)
  1499da:	0206efa7          	vse32.v	v31,(a3)
  1499de:	010072d7          	vsetvli	t0,zero,e32,m1,tu,mu
  1499e2:	00066c27          	vse32.v	v24,(a2),v0.t
  1499e6:	0641                	c.addi	a2,16
  1499e8:	00076ca7          	vse32.v	v25,(a4),v0.t
  1499ec:	0741                	c.addi	a4,16
  1499ee:	00066d27          	vse32.v	v26,(a2),v0.t
  1499f2:	0641                	c.addi	a2,16
  1499f4:	00076da7          	vse32.v	v27,(a4),v0.t
  1499f8:	0741                	c.addi	a4,16
  1499fa:	00066e27          	vse32.v	v28,(a2),v0.t
  1499fe:	0641                	c.addi	a2,16
  149a00:	00076ea7          	vse32.v	v29,(a4),v0.t
  149a04:	0741                	c.addi	a4,16
  149a06:	00066f27          	vse32.v	v30,(a2),v0.t
  149a0a:	00076fa7          	vse32.v	v31,(a4),v0.t
  149a0e:	6702                	c.ldsp	a4,0(sp)
  149a10:	0f41                	c.addi	t5,16
  149a12:	9be6                	c.add	s7,s9
  149a14:	9fba                	c.add	t6,a4
  149a16:	04078793          	addi	a5,a5,64
  149a1a:	db0f65e3          	bltu	t5,a6,1497c4 <END149+0x84>
  149a1e:	74f6                	c.ldsp	s1,376(sp)
  149a20:	7956                	c.ldsp	s2,368(sp)
  149a22:	79b6                	c.ldsp	s3,360(sp)
  149a24:	7a16                	c.ldsp	s4,352(sp)
  149a26:	6af6                	c.ldsp	s5,344(sp)
  149a28:	6b56                	c.ldsp	s6,336(sp)
  149a2a:	6bb6                	c.ldsp	s7,328(sp)
  149a2c:	7cf2                	c.ldsp	s9,312(sp)
  149a2e:	7d52                	c.ldsp	s10,304(sp)
  149a30:	6c16                	c.ldsp	s8,320(sp)
  149a32:	4511                	c.li	a0,4
  149a34:	b33d                	c.j	149762 <END149+0x22>
  149a36:	6d22                	c.ldsp	s10,8(sp)
  149a38:	04000c13          	addi	s8,zero,64
  149a3c:	013072d7          	vsetvli	t0,zero,e32,m8,tu,mu
  149a40:	2f8c0c57          	vxor.vv	v24,v24,v24
  149a44:	8e6e                	c.mv	t3,s11
  149a46:	000072d7          	vsetvli	t0,zero,e8,m1,tu,mu
  149a4a:	44e1                	c.li	s1,24
  149a4c:	5e01b0d7          	vmv.v.i	v1,3
  149a50:	0004f2d7          	vsetvli	t0,s1,e8,m1,tu,mu
  149a54:	5e0130d7          	vmv.v.i	v1,2
  149a58:	007072d7          	vsetvli	t0,zero,e8,mf2,tu,mu
  149a5c:	5e00b0d7          	vmv.v.i	v1,1
  149a60:	006072d7          	vsetvli	t0,zero,e8,mf4,tu,mu
  149a64:	5e0030d7          	vmv.v.i	v1,0
  149a68:	85a2                	c.mv	a1,s0
  149a6a:	84aa                	c.mv	s1,a0

0000000000149a6c <BLOCK_COUNTK_LOOP299>:
  149a6c:	8aa6                	c.mv	s5,s1
  149a6e:	02048b13          	addi	s6,s1,32
  149a72:	010b0493          	addi	s1,s6,16
  149a76:	02048913          	addi	s2,s1,32
  149a7a:	04048993          	addi	s3,s1,64
  149a7e:	06048a13          	addi	s4,s1,96
  149a82:	013072d7          	vsetvli	t0,zero,e32,m8,tu,mu
  149a86:	2f080857          	vxor.vv	v16,v16,v16
  149a8a:	0005a087          	flw	ft1,0(a1)
  149a8e:	0045a107          	flw	ft2,4(a1)
  149a92:	0085a187          	flw	ft3,8(a1)
  149a96:	00c5a207          	flw	ft4,12(a1)
  149a9a:	05c1                	c.addi	a1,16
  149a9c:	83c6                	c.mv	t2,a7
  149a9e:	007072d7          	vsetvli	t0,zero,e8,mf2,tu,mu
  149aa2:	020b0587          	vle8.v	v11,(s6)
  149aa6:	000072d7          	vsetvli	t0,zero,e8,m1,tu,mu
  149aaa:	32b08657          	vrgather.vv	v12,v11,v1
  149aae:	021230d7          	vadd.vi	v1,v1,4
  149ab2:	32b086d7          	vrgather.vv	v13,v11,v1
  149ab6:	021230d7          	vadd.vi	v1,v1,4
  149aba:	32b08757          	vrgather.vv	v14,v11,v1
  149abe:	021230d7          	vadd.vi	v1,v1,4
  149ac2:	32b087d7          	vrgather.vv	v15,v11,v1
  149ac6:	021a30d7          	vadd.vi	v1,v1,-12

0000000000149aca <BLOCK_INNER_LOOP299>:
  149aca:	000072d7          	vsetvli	t0,zero,e8,m1,tu,mu
  149ace:	02048307          	vle8.v	v6,(s1)
  149ad2:	08048493          	addi	s1,s1,128
  149ad6:	02090387          	vle8.v	v7,(s2)
  149ada:	08090913          	addi	s2,s2,128
  149ade:	02098407          	vle8.v	v8,(s3)
  149ae2:	08098993          	addi	s3,s3,128
  149ae6:	020a0487          	vle8.v	v9,(s4)
  149aea:	080a0a13          	addi	s4,s4,128
  149aee:	2667b157          	vand.vi	v2,v6,15
  149af2:	2677b1d7          	vand.vi	v3,v7,15
  149af6:	2687b257          	vand.vi	v4,v8,15
  149afa:	2697b2d7          	vand.vi	v5,v9,15
  149afe:	a2623357          	vsrl.vi	v6,v6,4
  149b02:	a27233d7          	vsrl.vi	v7,v7,4
  149b06:	a2823457          	vsrl.vi	v8,v8,4
  149b0a:	a29234d7          	vsrl.vi	v9,v9,4
  149b0e:	02058507          	vle8.v	v10,(a1)
  149b12:	02058593          	addi	a1,a1,32
  149b16:	02058587          	vle8.v	v11,(a1)
  149b1a:	02058593          	addi	a1,a1,32
  149b1e:	0a260157          	vsub.vv	v2,v2,v12
  149b22:	0a660357          	vsub.vv	v6,v6,v12
  149b26:	0a3681d7          	vsub.vv	v3,v3,v13
  149b2a:	0a7683d7          	vsub.vv	v7,v7,v13
  149b2e:	0a470257          	vsub.vv	v4,v4,v14
  149b32:	0a870457          	vsub.vv	v8,v8,v14
  149b36:	0a5782d7          	vsub.vv	v5,v5,v15
  149b3a:	0a9784d7          	vsub.vv	v9,v9,v15
  149b3e:	e225382b          	.insn	4, 0xe225382b
  149b42:	e235392b          	.insn	4, 0xe235392b
  149b46:	e2453a2b          	.insn	4, 0xe2453a2b
  149b4a:	e2553b2b          	.insn	4, 0xe2553b2b
  149b4e:	e265b82b          	.insn	4, 0xe265b82b
  149b52:	e275b92b          	.insn	4, 0xe275b92b
  149b56:	e285ba2b          	.insn	4, 0xe285ba2b
  149b5a:	e295bb2b          	.insn	4, 0xe295bb2b
  149b5e:	13fd                	c.addi	t2,-1
  149b60:	f60395e3          	bne	t2,zero,149aca <BLOCK_INNER_LOOP299>
  149b64:	ff8a8913          	addi	s2,s5,-8
  149b68:	008a8993          	addi	s3,s5,8
  149b6c:	010a8a13          	addi	s4,s5,16
  149b70:	018a8b13          	addi	s6,s5,24
  149b74:	0f000313          	addi	t1,zero,240
  149b78:	42036057          	vmv.s.x	v0,t1
  149b7c:	00e072d7          	vsetvli	t0,zero,e16,mf4,tu,mu
  149b80:	020ad487          	vle16.v	v9,(s5)
  149b84:	0209d587          	vle16.v	v11,(s3)
  149b88:	020a5687          	vle16.v	v13,(s4)
  149b8c:	020b5787          	vle16.v	v15,(s6)
  149b90:	00f072d7          	vsetvli	t0,zero,e16,mf2,tu,mu
  149b94:	00095487          	vle16.v	v9,(s2),v0.t
  149b98:	000ad587          	vle16.v	v11,(s5),v0.t
  149b9c:	0009d687          	vle16.v	v13,(s3),v0.t
  149ba0:	000a5787          	vle16.v	v15,(s4),v0.t
  149ba4:	4a961257          	vfwcvt.f.f.v	v4,v9
  149ba8:	4ab612d7          	vfwcvt.f.f.v	v5,v11
  149bac:	4ad61357          	vfwcvt.f.f.v	v6,v13
  149bb0:	4af613d7          	vfwcvt.f.f.v	v7,v15
  149bb4:	010072d7          	vsetvli	t0,zero,e32,m1,tu,mu
  149bb8:	5e00d157          	vfmv.v.f	v2,ft1
  149bbc:	5c215157          	vfmerge.vfm	v2,v2,ft2,v0
  149bc0:	5e01d1d7          	vfmv.v.f	v3,ft3
  149bc4:	5c3251d7          	vfmerge.vfm	v3,v3,ft4,v0
  149bc8:	92411457          	vfmul.vv	v8,v4,v2
  149bcc:	924194d7          	vfmul.vv	v9,v4,v3
  149bd0:	92511557          	vfmul.vv	v10,v5,v2
  149bd4:	925195d7          	vfmul.vv	v11,v5,v3
  149bd8:	92611657          	vfmul.vv	v12,v6,v2
  149bdc:	926196d7          	vfmul.vv	v13,v6,v3
  149be0:	92711757          	vfmul.vv	v14,v7,v2
  149be4:	927197d7          	vfmul.vv	v15,v7,v3
  149be8:	013072d7          	vsetvli	t0,zero,e32,m8,tu,mu
  149bec:	4b019857          	vfcvt.f.x.v	v16,v16
  149bf0:	b2881c57          	vfmacc.vv	v24,v16,v8
  149bf4:	1e7d                	c.addi	t3,-1
  149bf6:	e60e1be3          	bne	t3,zero,149a6c <BLOCK_COUNTK_LOOP299>

0000000000149bfa <RESULT_SAVE299>:
  149bfa:	85ea                	c.mv	a1,s10
  149bfc:	018d0633          	add	a2,s10,s8
  149c00:	018606b3          	add	a3,a2,s8
  149c04:	01868733          	add	a4,a3,s8
  149c08:	1641                	c.addi	a2,-16
  149c0a:	1741                	c.addi	a4,-16
  149c0c:	0f000313          	addi	t1,zero,240
  149c10:	42036057          	vmv.s.x	v0,t1
  149c14:	017072d7          	vsetvli	t0,zero,e32,mf2,tu,mu
  149c18:	0205ec27          	vse32.v	v24,(a1)
  149c1c:	05c1                	c.addi	a1,16
  149c1e:	0206eca7          	vse32.v	v25,(a3)
  149c22:	06c1                	c.addi	a3,16
  149c24:	0205ed27          	vse32.v	v26,(a1)
  149c28:	05c1                	c.addi	a1,16
  149c2a:	0206eda7          	vse32.v	v27,(a3)
  149c2e:	06c1                	c.addi	a3,16
  149c30:	0205ee27          	vse32.v	v28,(a1)
  149c34:	05c1                	c.addi	a1,16
  149c36:	0206eea7          	vse32.v	v29,(a3)
  149c3a:	06c1                	c.addi	a3,16
  149c3c:	0205ef27          	vse32.v	v30,(a1)
  149c40:	0206efa7          	vse32.v	v31,(a3)
  149c44:	010072d7          	vsetvli	t0,zero,e32,m1,tu,mu
  149c48:	00066c27          	vse32.v	v24,(a2),v0.t
  149c4c:	0641                	c.addi	a2,16
  149c4e:	00076ca7          	vse32.v	v25,(a4),v0.t
  149c52:	0741                	c.addi	a4,16
  149c54:	00066d27          	vse32.v	v26,(a2),v0.t
  149c58:	0641                	c.addi	a2,16
  149c5a:	00076da7          	vse32.v	v27,(a4),v0.t
  149c5e:	0741                	c.addi	a4,16
  149c60:	00066e27          	vse32.v	v28,(a2),v0.t
  149c64:	0641                	c.addi	a2,16
  149c66:	00076ea7          	vse32.v	v29,(a4),v0.t
  149c6a:	0741                	c.addi	a4,16
  149c6c:	00066f27          	vse32.v	v30,(a2),v0.t
  149c70:	00076fa7          	vse32.v	v31,(a4),v0.t
  149c74:	6702                	c.ldsp	a4,0(sp)
  149c76:	0f41                	c.addi	t5,16
  149c78:	9be6                	c.add	s7,s9
  149c7a:	9fba                	c.add	t6,a4
  149c7c:	97e2                	c.add	a5,s8
  149c7e:	db0f70e3          	bgeu	t5,a6,149a1e <RESULT_SAVE251+0x8a>
  149c82:	8d62                	c.mv	s10,s8
  149c84:	b681                	c.j	1497c4 <END149+0x84>
  149c86:	66080063          	beq	a6,zero,14a2e6 <RESULT_SAVE453+0x8c>
  149c8a:	03150533          	mul	a0,a0,a7
  149c8e:	e6de                	c.sdsp	s7,328(sp)
  149c90:	e2e2                	c.sdsp	s8,320(sp)
  149c92:	fea6                	c.sdsp	s1,376(sp)
  149c94:	00589c13          	slli	s8,a7,0x5
  149c98:	faca                	c.sdsp	s2,368(sp)
  149c9a:	f6ce                	c.sdsp	s3,360(sp)
  149c9c:	f2d2                	c.sdsp	s4,352(sp)
  149c9e:	eed6                	c.sdsp	s5,344(sp)
  149ca0:	eada                	c.sdsp	s6,336(sp)
  149ca2:	87ba                	c.mv	a5,a4
  149ca4:	4f81                	c.li	t6,0
  149ca6:	4e81                	c.li	t4,0
  149ca8:	4881                	c.li	a7,0
  149caa:	4bc1                	c.li	s7,16
  149cac:	0512                	c.slli	a0,0x4
  149cae:	41180733          	sub	a4,a6,a7
  149cb2:	00ebf363          	bgeu	s7,a4,149cb8 <RESULT_SAVE299+0xbe>
  149cb6:	4741                	c.li	a4,16
  149cb8:	001ed693          	srli	a3,t4,0x1
  149cbc:	96fe                	c.add	a3,t6
  149cbe:	96b2                	c.add	a3,a2
  149cc0:	836e                	c.mv	t1,s11
  149cc2:	012072d7          	vsetvli	t0,zero,e32,m4,tu,mu
  149cc6:	2fce0e57          	vxor.vv	v28,v28,v28
  149cca:	84b6                	c.mv	s1,a3
  149ccc:	00868913          	addi	s2,a3,8
  149cd0:	01068993          	addi	s3,a3,16
  149cd4:	01868a13          	addi	s4,a3,24
  149cd8:	8aae                	c.mv	s5,a1
  149cda:	00c58b13          	addi	s6,a1,12

0000000000149cde <LOOP_K360>:
  149cde:	00e072d7          	vsetvli	t0,zero,e16,mf4,tu,mu
  149ce2:	0204d207          	vle16.v	v4,(s1)
  149ce6:	02048493          	addi	s1,s1,32
  149cea:	02095287          	vle16.v	v5,(s2)
  149cee:	03890913          	addi	s2,s2,56
  149cf2:	0209d307          	vle16.v	v6,(s3)
  149cf6:	05098993          	addi	s3,s3,80
  149cfa:	020a5387          	vle16.v	v7,(s4)
  149cfe:	068a0a13          	addi	s4,s4,104
  149d02:	000aa087          	flw	ft1,0(s5)
  149d06:	0a91                	c.addi	s5,4
  149d08:	4a461457          	vfwcvt.f.f.v	v8,v4
  149d0c:	4a5614d7          	vfwcvt.f.f.v	v9,v5
  149d10:	4a661557          	vfwcvt.f.f.v	v10,v6
  149d14:	4a7615d7          	vfwcvt.f.f.v	v11,v7
  149d18:	017072d7          	vsetvli	t0,zero,e32,mf2,tu,mu
  149d1c:	8f22                	c.mv	t5,s0
  149d1e:	2f080857          	vxor.vv	v16,v16,v16
  149d22:	2f290957          	vxor.vv	v18,v18,v18
  149d26:	2f4a0a57          	vxor.vv	v20,v20,v20
  149d2a:	2f6b0b57          	vxor.vv	v22,v22,v22
  149d2e:	9280dc57          	vfmul.vf	v24,v8,ft1
  149d32:	9290dcd7          	vfmul.vf	v25,v9,ft1
  149d36:	92a0dd57          	vfmul.vf	v26,v10,ft1
  149d3a:	92b0ddd7          	vfmul.vf	v27,v11,ft1
  149d3e:	137d                	c.addi	t1,-1
  149d40:	000072d7          	vsetvli	t0,zero,e8,m1,tu,mu

0000000000149d44 <LOOP_INNER360>:
  149d44:	02048207          	vle8.v	v4,(s1)
  149d48:	08048493          	addi	s1,s1,128
  149d4c:	02090287          	vle8.v	v5,(s2)
  149d50:	08090913          	addi	s2,s2,128
  149d54:	02098307          	vle8.v	v6,(s3)
  149d58:	08098993          	addi	s3,s3,128
  149d5c:	020a0387          	vle8.v	v7,(s4)
  149d60:	080a0a13          	addi	s4,s4,128
  149d64:	006072d7          	vsetvli	t0,zero,e8,mf4,tu,mu
  149d68:	020a8707          	vle8.v	v14,(s5)
  149d6c:	0ac1                	c.addi	s5,16
  149d6e:	020b0787          	vle8.v	v15,(s6)
  149d72:	0b41                	c.addi	s6,16
  149d74:	1f7d                	c.addi	t5,-1
  149d76:	000072d7          	vsetvli	t0,zero,e8,m1,tu,mu
  149d7a:	2647b057          	vand.vi	v0,v4,15
  149d7e:	2657b0d7          	vand.vi	v1,v5,15
  149d82:	2667b157          	vand.vi	v2,v6,15
  149d86:	2677b1d7          	vand.vi	v3,v7,15
  149d8a:	a2423257          	vsrl.vi	v4,v4,4
  149d8e:	a25232d7          	vsrl.vi	v5,v5,4
  149d92:	a2623357          	vsrl.vi	v6,v6,4
  149d96:	a27233d7          	vsrl.vi	v7,v7,4
  149d9a:	020c3057          	vadd.vi	v0,v0,-8
  149d9e:	021c30d7          	vadd.vi	v1,v1,-8
  149da2:	022c3157          	vadd.vi	v2,v2,-8
  149da6:	023c31d7          	vadd.vi	v3,v3,-8
  149daa:	024c3257          	vadd.vi	v4,v4,-8
  149dae:	025c32d7          	vadd.vi	v5,v5,-8
  149db2:	026c3357          	vadd.vi	v6,v6,-8
  149db6:	027c33d7          	vadd.vi	v7,v7,-8
  149dba:	e207382b          	.insn	4, 0xe207382b
  149dbe:	e217392b          	.insn	4, 0xe217392b
  149dc2:	e2273a2b          	.insn	4, 0xe2273a2b
  149dc6:	e2373b2b          	.insn	4, 0xe2373b2b
  149dca:	e247b82b          	.insn	4, 0xe247b82b
  149dce:	e257b92b          	.insn	4, 0xe257b92b
  149dd2:	e267ba2b          	.insn	4, 0xe267ba2b
  149dd6:	e277bb2b          	.insn	4, 0xe277bb2b
  149dda:	f60f15e3          	bne	t5,zero,149d44 <LOOP_INNER360>
  149dde:	017072d7          	vsetvli	t0,zero,e32,mf2,tu,mu
  149de2:	4b019857          	vfcvt.f.x.v	v16,v16
  149de6:	4b219957          	vfcvt.f.x.v	v18,v18
  149dea:	4b419a57          	vfcvt.f.x.v	v20,v20
  149dee:	4b619b57          	vfcvt.f.x.v	v22,v22
  149df2:	00848913          	addi	s2,s1,8
  149df6:	01048993          	addi	s3,s1,16
  149dfa:	01848a13          	addi	s4,s1,24
  149dfe:	00ca8b13          	addi	s6,s5,12
  149e02:	b3881e57          	vfmacc.vv	v28,v16,v24
  149e06:	b3991ed7          	vfmacc.vv	v29,v18,v25
  149e0a:	b3aa1f57          	vfmacc.vv	v30,v20,v26
  149e0e:	b3bb1fd7          	vfmacc.vv	v31,v22,v27
  149e12:	ec0316e3          	bne	t1,zero,149cde <LOOP_K360>
  149e16:	4e41                	c.li	t3,16
  149e18:	01078493          	addi	s1,a5,16
  149e1c:	02078913          	addi	s2,a5,32
  149e20:	03078993          	addi	s3,a5,48
  149e24:	01c74c63          	blt	a4,t3,149e3c <ST_TAIL360>
  149e28:	0207ee27          	vse32.v	v28,(a5)
  149e2c:	0204eea7          	vse32.v	v29,(s1)
  149e30:	02096f27          	vse32.v	v30,(s2)
  149e34:	0209efa7          	vse32.v	v31,(s3)
  149e38:	0340006f          	jal	zero,149e6c <END360>

0000000000149e3c <ST_TAIL360>:
  149e3c:	017772d7          	vsetvli	t0,a4,e32,mf2,tu,mu
  149e40:	40570733          	sub	a4,a4,t0
  149e44:	0207ee27          	vse32.v	v28,(a5)
  149e48:	017772d7          	vsetvli	t0,a4,e32,mf2,tu,mu
  149e4c:	40570733          	sub	a4,a4,t0
  149e50:	0204eea7          	vse32.v	v29,(s1)
  149e54:	017772d7          	vsetvli	t0,a4,e32,mf2,tu,mu
  149e58:	40570733          	sub	a4,a4,t0
  149e5c:	02096f27          	vse32.v	v30,(s2)
  149e60:	017772d7          	vsetvli	t0,a4,e32,mf2,tu,mu
  149e64:	40570733          	sub	a4,a4,t0
  149e68:	0209efa7          	vse32.v	v31,(s3)

0000000000149e6c <END360>:
  149e6c:	08c1                	c.addi	a7,16
  149e6e:	9eaa                	c.add	t4,a0
  149e70:	9fe2                	c.add	t6,s8
  149e72:	04078793          	addi	a5,a5,64
  149e76:	e308ece3          	bltu	a7,a6,149cae <RESULT_SAVE299+0xb4>
  149e7a:	74f6                	c.ldsp	s1,376(sp)
  149e7c:	7956                	c.ldsp	s2,368(sp)
  149e7e:	79b6                	c.ldsp	s3,360(sp)
  149e80:	7a16                	c.ldsp	s4,352(sp)
  149e82:	6af6                	c.ldsp	s5,344(sp)
  149e84:	6b56                	c.ldsp	s6,336(sp)
  149e86:	6bb6                	c.ldsp	s7,328(sp)
  149e88:	6c16                	c.ldsp	s8,320(sp)
  149e8a:	4505                	c.li	a0,1
  149e8c:	b8d9                	c.j	149762 <END149+0x22>
  149e8e:	ba0801e3          	beq	a6,zero,149a30 <RESULT_SAVE251+0x9c>
  149e92:	03150533          	mul	a0,a0,a7
  149e96:	e6de                	c.sdsp	s7,328(sp)
  149e98:	fe66                	c.sdsp	s9,312(sp)
  149e9a:	00589b93          	slli	s7,a7,0x5
  149e9e:	87ba                	c.mv	a5,a4
  149ea0:	0838                	c.addi4spn	a4,sp,24
  149ea2:	fa6a                	c.sdsp	s10,304(sp)
  149ea4:	fea6                	c.sdsp	s1,376(sp)
  149ea6:	8d62                	c.mv	s10,s8
  149ea8:	faca                	c.sdsp	s2,368(sp)
  149eaa:	8c5e                	c.mv	s8,s7
  149eac:	00451c93          	slli	s9,a0,0x4
  149eb0:	e066                	c.sdsp	s9,0(sp)
  149eb2:	f6ce                	c.sdsp	s3,360(sp)
  149eb4:	f2d2                	c.sdsp	s4,352(sp)
  149eb6:	eed6                	c.sdsp	s5,344(sp)
  149eb8:	eada                	c.sdsp	s6,336(sp)
  149eba:	4f01                	c.li	t5,0
  149ebc:	4e81                	c.li	t4,0
  149ebe:	4881                	c.li	a7,0
  149ec0:	e43a                	c.sdsp	a4,8(sp)
  149ec2:	8cae                	c.mv	s9,a1
  149ec4:	8bb2                	c.mv	s7,a2
  149ec6:	001ed513          	srli	a0,t4,0x1
  149eca:	957a                	c.add	a0,t5
  149ecc:	41180733          	sub	a4,a6,a7
  149ed0:	46bd                	c.li	a3,15
  149ed2:	955e                	c.add	a0,s7
  149ed4:	20e6f863          	bgeu	a3,a4,14a0e4 <RESULT_SAVE435+0x9c>
  149ed8:	013072d7          	vsetvli	t0,zero,e32,m8,tu,mu
  149edc:	2f8c0c57          	vxor.vv	v24,v24,v24
  149ee0:	8e6e                	c.mv	t3,s11
  149ee2:	85e6                	c.mv	a1,s9
  149ee4:	84aa                	c.mv	s1,a0

0000000000149ee6 <BLOCK_COUNTK_LOOP435>:
  149ee6:	8aa6                	c.mv	s5,s1
  149ee8:	020a8493          	addi	s1,s5,32
  149eec:	02048913          	addi	s2,s1,32
  149ef0:	04048993          	addi	s3,s1,64
  149ef4:	06048a13          	addi	s4,s1,96
  149ef8:	013072d7          	vsetvli	t0,zero,e32,m8,tu,mu
  149efc:	2f080857          	vxor.vv	v16,v16,v16
  149f00:	0005a087          	flw	ft1,0(a1)
  149f04:	0045a107          	flw	ft2,4(a1)
  149f08:	0085a187          	flw	ft3,8(a1)
  149f0c:	00c5a207          	flw	ft4,12(a1)
  149f10:	05c1                	c.addi	a1,16
  149f12:	83a2                	c.mv	t2,s0

0000000000149f14 <BLOCK_INNER_LOOP435>:
  149f14:	000072d7          	vsetvli	t0,zero,e8,m1,tu,mu
  149f18:	02048307          	vle8.v	v6,(s1)
  149f1c:	08048493          	addi	s1,s1,128
  149f20:	02090387          	vle8.v	v7,(s2)
  149f24:	08090913          	addi	s2,s2,128
  149f28:	02098407          	vle8.v	v8,(s3)
  149f2c:	08098993          	addi	s3,s3,128
  149f30:	020a0487          	vle8.v	v9,(s4)
  149f34:	080a0a13          	addi	s4,s4,128
  149f38:	2667b157          	vand.vi	v2,v6,15
  149f3c:	2677b1d7          	vand.vi	v3,v7,15
  149f40:	2687b257          	vand.vi	v4,v8,15
  149f44:	2697b2d7          	vand.vi	v5,v9,15
  149f48:	a2623357          	vsrl.vi	v6,v6,4
  149f4c:	a27233d7          	vsrl.vi	v7,v7,4
  149f50:	a2823457          	vsrl.vi	v8,v8,4
  149f54:	a29234d7          	vsrl.vi	v9,v9,4
  149f58:	000072d7          	vsetvli	t0,zero,e8,m1,tu,mu
  149f5c:	02058507          	vle8.v	v10,(a1)
  149f60:	02058593          	addi	a1,a1,32
  149f64:	02058587          	vle8.v	v11,(a1)
  149f68:	02058593          	addi	a1,a1,32
  149f6c:	022c3157          	vadd.vi	v2,v2,-8
  149f70:	023c31d7          	vadd.vi	v3,v3,-8
  149f74:	024c3257          	vadd.vi	v4,v4,-8
  149f78:	025c32d7          	vadd.vi	v5,v5,-8
  149f7c:	026c3357          	vadd.vi	v6,v6,-8
  149f80:	027c33d7          	vadd.vi	v7,v7,-8
  149f84:	028c3457          	vadd.vi	v8,v8,-8
  149f88:	029c34d7          	vadd.vi	v9,v9,-8
  149f8c:	e225382b          	.insn	4, 0xe225382b
  149f90:	e235392b          	.insn	4, 0xe235392b
  149f94:	e2453a2b          	.insn	4, 0xe2453a2b
  149f98:	e2553b2b          	.insn	4, 0xe2553b2b
  149f9c:	e265b82b          	.insn	4, 0xe265b82b
  149fa0:	e275b92b          	.insn	4, 0xe275b92b
  149fa4:	e285ba2b          	.insn	4, 0xe285ba2b
  149fa8:	e295bb2b          	.insn	4, 0xe295bb2b
  149fac:	13fd                	c.addi	t2,-1
  149fae:	f60393e3          	bne	t2,zero,149f14 <BLOCK_INNER_LOOP435>
  149fb2:	ff8a8913          	addi	s2,s5,-8
  149fb6:	008a8993          	addi	s3,s5,8
  149fba:	010a8a13          	addi	s4,s5,16
  149fbe:	018a8b13          	addi	s6,s5,24
  149fc2:	0f000313          	addi	t1,zero,240
  149fc6:	42036057          	vmv.s.x	v0,t1
  149fca:	00e072d7          	vsetvli	t0,zero,e16,mf4,tu,mu
  149fce:	020ad487          	vle16.v	v9,(s5)
  149fd2:	0209d587          	vle16.v	v11,(s3)
  149fd6:	020a5687          	vle16.v	v13,(s4)
  149fda:	020b5787          	vle16.v	v15,(s6)
  149fde:	00f072d7          	vsetvli	t0,zero,e16,mf2,tu,mu
  149fe2:	00095487          	vle16.v	v9,(s2),v0.t
  149fe6:	000ad587          	vle16.v	v11,(s5),v0.t
  149fea:	0009d687          	vle16.v	v13,(s3),v0.t
  149fee:	000a5787          	vle16.v	v15,(s4),v0.t
  149ff2:	4a961257          	vfwcvt.f.f.v	v4,v9
  149ff6:	4ab612d7          	vfwcvt.f.f.v	v5,v11
  149ffa:	4ad61357          	vfwcvt.f.f.v	v6,v13
  149ffe:	4af613d7          	vfwcvt.f.f.v	v7,v15
  14a002:	010072d7          	vsetvli	t0,zero,e32,m1,tu,mu
  14a006:	5e00d157          	vfmv.v.f	v2,ft1
  14a00a:	5c215157          	vfmerge.vfm	v2,v2,ft2,v0
  14a00e:	5e01d1d7          	vfmv.v.f	v3,ft3
  14a012:	5c3251d7          	vfmerge.vfm	v3,v3,ft4,v0
  14a016:	92411457          	vfmul.vv	v8,v4,v2
  14a01a:	924194d7          	vfmul.vv	v9,v4,v3
  14a01e:	92511557          	vfmul.vv	v10,v5,v2
  14a022:	925195d7          	vfmul.vv	v11,v5,v3
  14a026:	92611657          	vfmul.vv	v12,v6,v2
  14a02a:	926196d7          	vfmul.vv	v13,v6,v3
  14a02e:	92711757          	vfmul.vv	v14,v7,v2
  14a032:	927197d7          	vfmul.vv	v15,v7,v3
  14a036:	013072d7          	vsetvli	t0,zero,e32,m8,tu,mu
  14a03a:	4b019857          	vfcvt.f.x.v	v16,v16
  14a03e:	b2881c57          	vfmacc.vv	v24,v16,v8
  14a042:	1e7d                	c.addi	t3,-1
  14a044:	ea0e11e3          	bne	t3,zero,149ee6 <BLOCK_COUNTK_LOOP435>

000000000014a048 <RESULT_SAVE435>:
  14a048:	85be                	c.mv	a1,a5
  14a04a:	01a78633          	add	a2,a5,s10
  14a04e:	01a606b3          	add	a3,a2,s10
  14a052:	01a68733          	add	a4,a3,s10
  14a056:	1641                	c.addi	a2,-16
  14a058:	1741                	c.addi	a4,-16
  14a05a:	0f000313          	addi	t1,zero,240
  14a05e:	42036057          	vmv.s.x	v0,t1
  14a062:	017072d7          	vsetvli	t0,zero,e32,mf2,tu,mu
  14a066:	0205ec27          	vse32.v	v24,(a1)
  14a06a:	05c1                	c.addi	a1,16
  14a06c:	0206eca7          	vse32.v	v25,(a3)
  14a070:	06c1                	c.addi	a3,16
  14a072:	0205ed27          	vse32.v	v26,(a1)
  14a076:	05c1                	c.addi	a1,16
  14a078:	0206eda7          	vse32.v	v27,(a3)
  14a07c:	06c1                	c.addi	a3,16
  14a07e:	0205ee27          	vse32.v	v28,(a1)
  14a082:	05c1                	c.addi	a1,16
  14a084:	0206eea7          	vse32.v	v29,(a3)
  14a088:	06c1                	c.addi	a3,16
  14a08a:	0205ef27          	vse32.v	v30,(a1)
  14a08e:	0206efa7          	vse32.v	v31,(a3)
  14a092:	010072d7          	vsetvli	t0,zero,e32,m1,tu,mu
  14a096:	00066c27          	vse32.v	v24,(a2),v0.t
  14a09a:	0641                	c.addi	a2,16
  14a09c:	00076ca7          	vse32.v	v25,(a4),v0.t
  14a0a0:	0741                	c.addi	a4,16
  14a0a2:	00066d27          	vse32.v	v26,(a2),v0.t
  14a0a6:	0641                	c.addi	a2,16
  14a0a8:	00076da7          	vse32.v	v27,(a4),v0.t
  14a0ac:	0741                	c.addi	a4,16
  14a0ae:	00066e27          	vse32.v	v28,(a2),v0.t
  14a0b2:	0641                	c.addi	a2,16
  14a0b4:	00076ea7          	vse32.v	v29,(a4),v0.t
  14a0b8:	0741                	c.addi	a4,16
  14a0ba:	00066f27          	vse32.v	v30,(a2),v0.t
  14a0be:	00076fa7          	vse32.v	v31,(a4),v0.t
  14a0c2:	6702                	c.ldsp	a4,0(sp)
  14a0c4:	08c1                	c.addi	a7,16
  14a0c6:	9f62                	c.add	t5,s8
  14a0c8:	9eba                	c.add	t4,a4
  14a0ca:	04078793          	addi	a5,a5,64
  14a0ce:	9508f8e3          	bgeu	a7,a6,149a1e <RESULT_SAVE251+0x8a>
  14a0d2:	001ed513          	srli	a0,t4,0x1
  14a0d6:	957a                	c.add	a0,t5
  14a0d8:	41180733          	sub	a4,a6,a7
  14a0dc:	46bd                	c.li	a3,15
  14a0de:	955e                	c.add	a0,s7
  14a0e0:	dee6ece3          	bltu	a3,a4,149ed8 <END360+0x6c>
  14a0e4:	6d22                	c.ldsp	s10,8(sp)
  14a0e6:	04000f93          	addi	t6,zero,64
  14a0ea:	013072d7          	vsetvli	t0,zero,e32,m8,tu,mu
  14a0ee:	2f8c0c57          	vxor.vv	v24,v24,v24
  14a0f2:	8e6e                	c.mv	t3,s11
  14a0f4:	85e6                	c.mv	a1,s9
  14a0f6:	84aa                	c.mv	s1,a0

000000000014a0f8 <BLOCK_COUNTK_LOOP453>:
  14a0f8:	8aa6                	c.mv	s5,s1
  14a0fa:	020a8493          	addi	s1,s5,32
  14a0fe:	02048913          	addi	s2,s1,32
  14a102:	04048993          	addi	s3,s1,64
  14a106:	06048a13          	addi	s4,s1,96
  14a10a:	013072d7          	vsetvli	t0,zero,e32,m8,tu,mu
  14a10e:	2f080857          	vxor.vv	v16,v16,v16
  14a112:	0005a087          	flw	ft1,0(a1)
  14a116:	0045a107          	flw	ft2,4(a1)
  14a11a:	0085a187          	flw	ft3,8(a1)
  14a11e:	00c5a207          	flw	ft4,12(a1)
  14a122:	05c1                	c.addi	a1,16
  14a124:	83a2                	c.mv	t2,s0

000000000014a126 <BLOCK_INNER_LOOP453>:
  14a126:	000072d7          	vsetvli	t0,zero,e8,m1,tu,mu
  14a12a:	02048307          	vle8.v	v6,(s1)
  14a12e:	08048493          	addi	s1,s1,128
  14a132:	02090387          	vle8.v	v7,(s2)
  14a136:	08090913          	addi	s2,s2,128
  14a13a:	02098407          	vle8.v	v8,(s3)
  14a13e:	08098993          	addi	s3,s3,128
  14a142:	020a0487          	vle8.v	v9,(s4)
  14a146:	080a0a13          	addi	s4,s4,128
  14a14a:	2667b157          	vand.vi	v2,v6,15
  14a14e:	2677b1d7          	vand.vi	v3,v7,15
  14a152:	2687b257          	vand.vi	v4,v8,15
  14a156:	2697b2d7          	vand.vi	v5,v9,15
  14a15a:	a2623357          	vsrl.vi	v6,v6,4
  14a15e:	a27233d7          	vsrl.vi	v7,v7,4
  14a162:	a2823457          	vsrl.vi	v8,v8,4
  14a166:	a29234d7          	vsrl.vi	v9,v9,4
  14a16a:	000072d7          	vsetvli	t0,zero,e8,m1,tu,mu
  14a16e:	02058507          	vle8.v	v10,(a1)
  14a172:	02058593          	addi	a1,a1,32
  14a176:	02058587          	vle8.v	v11,(a1)
  14a17a:	02058593          	addi	a1,a1,32
  14a17e:	022c3157          	vadd.vi	v2,v2,-8
  14a182:	023c31d7          	vadd.vi	v3,v3,-8
  14a186:	024c3257          	vadd.vi	v4,v4,-8
  14a18a:	025c32d7          	vadd.vi	v5,v5,-8
  14a18e:	026c3357          	vadd.vi	v6,v6,-8
  14a192:	027c33d7          	vadd.vi	v7,v7,-8
  14a196:	028c3457          	vadd.vi	v8,v8,-8
  14a19a:	029c34d7          	vadd.vi	v9,v9,-8
  14a19e:	e225382b          	.insn	4, 0xe225382b
  14a1a2:	e235392b          	.insn	4, 0xe235392b
  14a1a6:	e2453a2b          	.insn	4, 0xe2453a2b
  14a1aa:	e2553b2b          	.insn	4, 0xe2553b2b
  14a1ae:	e265b82b          	.insn	4, 0xe265b82b
  14a1b2:	e275b92b          	.insn	4, 0xe275b92b
  14a1b6:	e285ba2b          	.insn	4, 0xe285ba2b
  14a1ba:	e295bb2b          	.insn	4, 0xe295bb2b
  14a1be:	13fd                	c.addi	t2,-1
  14a1c0:	f60393e3          	bne	t2,zero,14a126 <BLOCK_INNER_LOOP453>
  14a1c4:	ff8a8913          	addi	s2,s5,-8
  14a1c8:	008a8993          	addi	s3,s5,8
  14a1cc:	010a8a13          	addi	s4,s5,16
  14a1d0:	018a8b13          	addi	s6,s5,24
  14a1d4:	0f000313          	addi	t1,zero,240
  14a1d8:	42036057          	vmv.s.x	v0,t1
  14a1dc:	00e072d7          	vsetvli	t0,zero,e16,mf4,tu,mu
  14a1e0:	020ad487          	vle16.v	v9,(s5)
  14a1e4:	0209d587          	vle16.v	v11,(s3)
  14a1e8:	020a5687          	vle16.v	v13,(s4)
  14a1ec:	020b5787          	vle16.v	v15,(s6)
  14a1f0:	00f072d7          	vsetvli	t0,zero,e16,mf2,tu,mu
  14a1f4:	00095487          	vle16.v	v9,(s2),v0.t
  14a1f8:	000ad587          	vle16.v	v11,(s5),v0.t
  14a1fc:	0009d687          	vle16.v	v13,(s3),v0.t
  14a200:	000a5787          	vle16.v	v15,(s4),v0.t
  14a204:	4a961257          	vfwcvt.f.f.v	v4,v9
  14a208:	4ab612d7          	vfwcvt.f.f.v	v5,v11
  14a20c:	4ad61357          	vfwcvt.f.f.v	v6,v13
  14a210:	4af613d7          	vfwcvt.f.f.v	v7,v15
  14a214:	010072d7          	vsetvli	t0,zero,e32,m1,tu,mu
  14a218:	5e00d157          	vfmv.v.f	v2,ft1
  14a21c:	5c215157          	vfmerge.vfm	v2,v2,ft2,v0
  14a220:	5e01d1d7          	vfmv.v.f	v3,ft3
  14a224:	5c3251d7          	vfmerge.vfm	v3,v3,ft4,v0
  14a228:	92411457          	vfmul.vv	v8,v4,v2
  14a22c:	924194d7          	vfmul.vv	v9,v4,v3
  14a230:	92511557          	vfmul.vv	v10,v5,v2
  14a234:	925195d7          	vfmul.vv	v11,v5,v3
  14a238:	92611657          	vfmul.vv	v12,v6,v2
  14a23c:	926196d7          	vfmul.vv	v13,v6,v3
  14a240:	92711757          	vfmul.vv	v14,v7,v2
  14a244:	927197d7          	vfmul.vv	v15,v7,v3
  14a248:	013072d7          	vsetvli	t0,zero,e32,m8,tu,mu
  14a24c:	4b019857          	vfcvt.f.x.v	v16,v16
  14a250:	b2881c57          	vfmacc.vv	v24,v16,v8
  14a254:	1e7d                	c.addi	t3,-1
  14a256:	ea0e11e3          	bne	t3,zero,14a0f8 <BLOCK_COUNTK_LOOP453>

000000000014a25a <RESULT_SAVE453>:
  14a25a:	85ea                	c.mv	a1,s10
  14a25c:	01fd0633          	add	a2,s10,t6
  14a260:	01f606b3          	add	a3,a2,t6
  14a264:	01f68733          	add	a4,a3,t6
  14a268:	1641                	c.addi	a2,-16
  14a26a:	1741                	c.addi	a4,-16
  14a26c:	0f000313          	addi	t1,zero,240
  14a270:	42036057          	vmv.s.x	v0,t1
  14a274:	017072d7          	vsetvli	t0,zero,e32,mf2,tu,mu
  14a278:	0205ec27          	vse32.v	v24,(a1)
  14a27c:	05c1                	c.addi	a1,16
  14a27e:	0206eca7          	vse32.v	v25,(a3)
  14a282:	06c1                	c.addi	a3,16
  14a284:	0205ed27          	vse32.v	v26,(a1)
  14a288:	05c1                	c.addi	a1,16
  14a28a:	0206eda7          	vse32.v	v27,(a3)
  14a28e:	06c1                	c.addi	a3,16
  14a290:	0205ee27          	vse32.v	v28,(a1)
  14a294:	05c1                	c.addi	a1,16
  14a296:	0206eea7          	vse32.v	v29,(a3)
  14a29a:	06c1                	c.addi	a3,16
  14a29c:	0205ef27          	vse32.v	v30,(a1)
  14a2a0:	0206efa7          	vse32.v	v31,(a3)
  14a2a4:	010072d7          	vsetvli	t0,zero,e32,m1,tu,mu
  14a2a8:	00066c27          	vse32.v	v24,(a2),v0.t
  14a2ac:	0641                	c.addi	a2,16
  14a2ae:	00076ca7          	vse32.v	v25,(a4),v0.t
  14a2b2:	0741                	c.addi	a4,16
  14a2b4:	00066d27          	vse32.v	v26,(a2),v0.t
  14a2b8:	0641                	c.addi	a2,16
  14a2ba:	00076da7          	vse32.v	v27,(a4),v0.t
  14a2be:	0741                	c.addi	a4,16
  14a2c0:	00066e27          	vse32.v	v28,(a2),v0.t
  14a2c4:	0641                	c.addi	a2,16
  14a2c6:	00076ea7          	vse32.v	v29,(a4),v0.t
  14a2ca:	0741                	c.addi	a4,16
  14a2cc:	00066f27          	vse32.v	v30,(a2),v0.t
  14a2d0:	00076fa7          	vse32.v	v31,(a4),v0.t
  14a2d4:	6702                	c.ldsp	a4,0(sp)
  14a2d6:	08c1                	c.addi	a7,16
  14a2d8:	9f62                	c.add	t5,s8
  14a2da:	9eba                	c.add	t4,a4
  14a2dc:	97fe                	c.add	a5,t6
  14a2de:	f508f063          	bgeu	a7,a6,149a1e <RESULT_SAVE251+0x8a>
  14a2e2:	8d7e                	c.mv	s10,t6
  14a2e4:	b6cd                	c.j	149ec6 <END360+0x5a>
  14a2e6:	4505                	c.li	a0,1
  14a2e8:	c7aff06f          	jal	zero,149762 <END149+0x22>
  14a2ec:	fea6                	c.sdsp	s1,376(sp)
  14a2ee:	faca                	c.sdsp	s2,368(sp)
  14a2f0:	f6ce                	c.sdsp	s3,360(sp)
  14a2f2:	f2d2                	c.sdsp	s4,352(sp)
  14a2f4:	eed6                	c.sdsp	s5,344(sp)
  14a2f6:	eada                	c.sdsp	s6,336(sp)
  14a2f8:	e6de                	c.sdsp	s7,328(sp)
  14a2fa:	e2e2                	c.sdsp	s8,320(sp)
  14a2fc:	fe66                	c.sdsp	s9,312(sp)
  14a2fe:	fa6a                	c.sdsp	s10,304(sp)
  14a300:	8303d0ef          	jal	ra,87330 <__stack_chk_fail@plt>
