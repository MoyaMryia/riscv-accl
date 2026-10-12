
/home/moyamryia/Projects/riscv-accl/lab/k1-combined-fixture-r5-20261011-122000-work/payload/C/lib/libggml-cpu.so.0.16.0:     file format elf64-littleriscv


Disassembly of section .text:

000000000014a304 <_ZN16spacemit_kernels4ime116gemm_kernel_i8i8EmPKhS2_S2_Pfmmmm>:
  14a304:	715d                	c.addi16sp	sp,-80
  14a306:	e486                	c.sdsp	ra,72(sp)
  14a308:	468d                	c.li	a3,3
  14a30a:	8eae                	c.mv	t4,a1
  14a30c:	8fb2                	c.mv	t6,a2
  14a30e:	1cf6ef63          	bltu	a3,a5,14a4ec <END554+0x20>
  14a312:	00455313          	srli	t1,a0,0x4
  14a316:	40080463          	beq	a6,zero,14a71e <RESULT_SAVE624+0x8a>
  14a31a:	fc26                	c.sdsp	s1,56(sp)
  14a31c:	f84a                	c.sdsp	s2,48(sp)
  14a31e:	f44e                	c.sdsp	s3,40(sp)
  14a320:	f052                	c.sdsp	s4,32(sp)
  14a322:	ec56                	c.sdsp	s5,24(sp)
  14a324:	e85a                	c.sdsp	s6,16(sp)
  14a326:	e45e                	c.sdsp	s7,8(sp)
  14a328:	4601                	c.li	a2,0
  14a32a:	43c1                	c.li	t2,16
  14a32c:	40c806b3          	sub	a3,a6,a2
  14a330:	00d3f363          	bgeu	t2,a3,14a336 <_ZN16spacemit_kernels4ime116gemm_kernel_i8i8EmPKhS2_S2_Pfmmmm+0x32>
  14a334:	46c1                	c.li	a3,16
  14a336:	00465593          	srli	a1,a2,0x4
  14a33a:	031585b3          	mul	a1,a1,a7
  14a33e:	8546                	c.mv	a0,a7
  14a340:	00459793          	slli	a5,a1,0x4
  14a344:	97ae                	c.add	a5,a1
  14a346:	0796                	c.slli	a5,0x5
  14a348:	97fe                	c.add	a5,t6
  14a34a:	012072d7          	vsetvli	t0,zero,e32,m4,tu,mu
  14a34e:	2fce0e57          	vxor.vv	v28,v28,v28
  14a352:	8bbe                	c.mv	s7,a5
  14a354:	8af6                	c.mv	s5,t4
  14a356:	00ce8b13          	addi	s6,t4,12

000000000014a35a <LOOP_K554>:
  14a35a:	020b8493          	addi	s1,s7,32
  14a35e:	008b8913          	addi	s2,s7,8
  14a362:	010b8993          	addi	s3,s7,16
  14a366:	018b8a13          	addi	s4,s7,24
  14a36a:	00e072d7          	vsetvli	t0,zero,e16,mf4,tu,mu
  14a36e:	020bd207          	vle16.v	v4,(s7)
  14a372:	02095287          	vle16.v	v5,(s2)
  14a376:	0209d307          	vle16.v	v6,(s3)
  14a37a:	020a5387          	vle16.v	v7,(s4)
  14a37e:	220b8b93          	addi	s7,s7,544
  14a382:	000aa087          	flw	ft1,0(s5)
  14a386:	0a91                	c.addi	s5,4
  14a388:	4a461457          	vfwcvt.f.f.v	v8,v4
  14a38c:	4a5614d7          	vfwcvt.f.f.v	v9,v5
  14a390:	4a661557          	vfwcvt.f.f.v	v10,v6
  14a394:	4a7615d7          	vfwcvt.f.f.v	v11,v7
  14a398:	017072d7          	vsetvli	t0,zero,e32,mf2,tu,mu
  14a39c:	8f1a                	c.mv	t5,t1
  14a39e:	2f080857          	vxor.vv	v16,v16,v16
  14a3a2:	2f290957          	vxor.vv	v18,v18,v18
  14a3a6:	2f4a0a57          	vxor.vv	v20,v20,v20
  14a3aa:	2f6b0b57          	vxor.vv	v22,v22,v22
  14a3ae:	9280dc57          	vfmul.vf	v24,v8,ft1
  14a3b2:	9290dcd7          	vfmul.vf	v25,v9,ft1
  14a3b6:	92a0dd57          	vfmul.vf	v26,v10,ft1
  14a3ba:	92b0ddd7          	vfmul.vf	v27,v11,ft1
  14a3be:	157d                	c.addi	a0,-1
  14a3c0:	000072d7          	vsetvli	t0,zero,e8,m1,tu,mu

000000000014a3c4 <LOOP_INNER554>:
  14a3c4:	02048007          	vle8.v	v0,(s1)
  14a3c8:	02048493          	addi	s1,s1,32
  14a3cc:	02048087          	vle8.v	v1,(s1)
  14a3d0:	02048493          	addi	s1,s1,32
  14a3d4:	02048107          	vle8.v	v2,(s1)
  14a3d8:	02048493          	addi	s1,s1,32
  14a3dc:	02048187          	vle8.v	v3,(s1)
  14a3e0:	02048493          	addi	s1,s1,32
  14a3e4:	02048207          	vle8.v	v4,(s1)
  14a3e8:	02048493          	addi	s1,s1,32
  14a3ec:	02048287          	vle8.v	v5,(s1)
  14a3f0:	02048493          	addi	s1,s1,32
  14a3f4:	02048307          	vle8.v	v6,(s1)
  14a3f8:	02048493          	addi	s1,s1,32
  14a3fc:	02048387          	vle8.v	v7,(s1)
  14a400:	02048493          	addi	s1,s1,32
  14a404:	006072d7          	vsetvli	t0,zero,e8,mf4,tu,mu
  14a408:	020a8707          	vle8.v	v14,(s5)
  14a40c:	0ac1                	c.addi	s5,16
  14a40e:	020b0787          	vle8.v	v15,(s6)
  14a412:	0b41                	c.addi	s6,16
  14a414:	1f7d                	c.addi	t5,-1
  14a416:	000072d7          	vsetvli	t0,zero,e8,m1,tu,mu
  14a41a:	e207382b          	.insn	4, 0xe207382b
  14a41e:	e217392b          	.insn	4, 0xe217392b
  14a422:	e2273a2b          	.insn	4, 0xe2273a2b
  14a426:	e2373b2b          	.insn	4, 0xe2373b2b
  14a42a:	e247b82b          	.insn	4, 0xe247b82b
  14a42e:	e257b92b          	.insn	4, 0xe257b92b
  14a432:	e267ba2b          	.insn	4, 0xe267ba2b
  14a436:	e277bb2b          	.insn	4, 0xe277bb2b
  14a43a:	f80f15e3          	bne	t5,zero,14a3c4 <LOOP_INNER554>
  14a43e:	017072d7          	vsetvli	t0,zero,e32,mf2,tu,mu
  14a442:	4b019857          	vfcvt.f.x.v	v16,v16
  14a446:	4b219957          	vfcvt.f.x.v	v18,v18
  14a44a:	4b419a57          	vfcvt.f.x.v	v20,v20
  14a44e:	4b619b57          	vfcvt.f.x.v	v22,v22
  14a452:	00848913          	addi	s2,s1,8
  14a456:	01048993          	addi	s3,s1,16
  14a45a:	01848a13          	addi	s4,s1,24
  14a45e:	00ca8b13          	addi	s6,s5,12
  14a462:	b3881e57          	vfmacc.vv	v28,v16,v24
  14a466:	b3991ed7          	vfmacc.vv	v29,v18,v25
  14a46a:	b3aa1f57          	vfmacc.vv	v30,v20,v26
  14a46e:	b3bb1fd7          	vfmacc.vv	v31,v22,v27
  14a472:	ee0514e3          	bne	a0,zero,14a35a <LOOP_K554>
  14a476:	4e41                	c.li	t3,16
  14a478:	01070493          	addi	s1,a4,16
  14a47c:	02070913          	addi	s2,a4,32
  14a480:	03070993          	addi	s3,a4,48
  14a484:	01c6cc63          	blt	a3,t3,14a49c <ST_TAIL554>
  14a488:	02076e27          	vse32.v	v28,(a4)
  14a48c:	0204eea7          	vse32.v	v29,(s1)
  14a490:	02096f27          	vse32.v	v30,(s2)
  14a494:	0209efa7          	vse32.v	v31,(s3)
  14a498:	0340006f          	jal	zero,14a4cc <END554>

000000000014a49c <ST_TAIL554>:
  14a49c:	0176f2d7          	vsetvli	t0,a3,e32,mf2,tu,mu
  14a4a0:	405686b3          	sub	a3,a3,t0
  14a4a4:	02076e27          	vse32.v	v28,(a4)
  14a4a8:	0176f2d7          	vsetvli	t0,a3,e32,mf2,tu,mu
  14a4ac:	405686b3          	sub	a3,a3,t0
  14a4b0:	0204eea7          	vse32.v	v29,(s1)
  14a4b4:	0176f2d7          	vsetvli	t0,a3,e32,mf2,tu,mu
  14a4b8:	405686b3          	sub	a3,a3,t0
  14a4bc:	02096f27          	vse32.v	v30,(s2)
  14a4c0:	0176f2d7          	vsetvli	t0,a3,e32,mf2,tu,mu
  14a4c4:	405686b3          	sub	a3,a3,t0
  14a4c8:	0209efa7          	vse32.v	v31,(s3)

000000000014a4cc <END554>:
  14a4cc:	0641                	c.addi	a2,16
  14a4ce:	04070713          	addi	a4,a4,64
  14a4d2:	e5066de3          	bltu	a2,a6,14a32c <_ZN16spacemit_kernels4ime116gemm_kernel_i8i8EmPKhS2_S2_Pfmmmm+0x28>
  14a4d6:	4505                	c.li	a0,1
  14a4d8:	74e2                	c.ldsp	s1,56(sp)
  14a4da:	7942                	c.ldsp	s2,48(sp)
  14a4dc:	79a2                	c.ldsp	s3,40(sp)
  14a4de:	7a02                	c.ldsp	s4,32(sp)
  14a4e0:	6ae2                	c.ldsp	s5,24(sp)
  14a4e2:	6b42                	c.ldsp	s6,16(sp)
  14a4e4:	6ba2                	c.ldsp	s7,8(sp)
  14a4e6:	60a6                	c.ldsp	ra,72(sp)
  14a4e8:	6161                	c.addi16sp	sp,80
  14a4ea:	8082                	c.jr	ra
  14a4ec:	e0a2                	c.sdsp	s0,64(sp)
  14a4ee:	00f87413          	andi	s0,a6,15
  14a4f2:	22041c63          	bne	s0,zero,14a72a <RESULT_SAVE624+0x96>
  14a4f6:	67c6                	c.ldsp	a5,80(sp)
  14a4f8:	e45e                	c.sdsp	s7,8(sp)
  14a4fa:	8111                	c.srli	a0,0x4
  14a4fc:	00279b93          	slli	s7,a5,0x2
  14a500:	22080163          	beq	a6,zero,14a722 <RESULT_SAVE624+0x8e>
  14a504:	fc26                	c.sdsp	s1,56(sp)
  14a506:	f84a                	c.sdsp	s2,48(sp)
  14a508:	f44e                	c.sdsp	s3,40(sp)
  14a50a:	f052                	c.sdsp	s4,32(sp)
  14a50c:	ec56                	c.sdsp	s5,24(sp)
  14a50e:	e85a                	c.sdsp	s6,16(sp)
  14a510:	87ba                	c.mv	a5,a4
  14a512:	00445713          	srli	a4,s0,0x4
  14a516:	03170733          	mul	a4,a4,a7
  14a51a:	00471f13          	slli	t5,a4,0x4
  14a51e:	9f3a                	c.add	t5,a4
  14a520:	0f16                	c.slli	t5,0x5
  14a522:	9f7e                	c.add	t5,t6
  14a524:	013072d7          	vsetvli	t0,zero,e32,m8,tu,mu
  14a528:	2f8c0c57          	vxor.vv	v24,v24,v24
  14a52c:	8e46                	c.mv	t3,a7
  14a52e:	85f6                	c.mv	a1,t4
  14a530:	84fa                	c.mv	s1,t5

000000000014a532 <BLOCK_COUNTK_LOOP624>:
  14a532:	8aa6                	c.mv	s5,s1
  14a534:	020a8493          	addi	s1,s5,32
  14a538:	013072d7          	vsetvli	t0,zero,e32,m8,tu,mu
  14a53c:	2f080857          	vxor.vv	v16,v16,v16
  14a540:	0005a087          	flw	ft1,0(a1)
  14a544:	0045a107          	flw	ft2,4(a1)
  14a548:	0085a187          	flw	ft3,8(a1)
  14a54c:	00c5a207          	flw	ft4,12(a1)
  14a550:	05c1                	c.addi	a1,16
  14a552:	83aa                	c.mv	t2,a0

000000000014a554 <BLOCK_INNER_LOOP624>:
  14a554:	000072d7          	vsetvli	t0,zero,e8,m1,tu,mu
  14a558:	02048107          	vle8.v	v2,(s1)
  14a55c:	02048493          	addi	s1,s1,32
  14a560:	02048187          	vle8.v	v3,(s1)
  14a564:	02048493          	addi	s1,s1,32
  14a568:	02048207          	vle8.v	v4,(s1)
  14a56c:	02048493          	addi	s1,s1,32
  14a570:	02048287          	vle8.v	v5,(s1)
  14a574:	02048493          	addi	s1,s1,32
  14a578:	02048307          	vle8.v	v6,(s1)
  14a57c:	02048493          	addi	s1,s1,32
  14a580:	02048387          	vle8.v	v7,(s1)
  14a584:	02048493          	addi	s1,s1,32
  14a588:	02048407          	vle8.v	v8,(s1)
  14a58c:	02048493          	addi	s1,s1,32
  14a590:	02048487          	vle8.v	v9,(s1)
  14a594:	02048493          	addi	s1,s1,32
  14a598:	02058507          	vle8.v	v10,(a1)
  14a59c:	02058593          	addi	a1,a1,32
  14a5a0:	02058587          	vle8.v	v11,(a1)
  14a5a4:	02058593          	addi	a1,a1,32
  14a5a8:	e225382b          	.insn	4, 0xe225382b
  14a5ac:	e235392b          	.insn	4, 0xe235392b
  14a5b0:	e2453a2b          	.insn	4, 0xe2453a2b
  14a5b4:	e2553b2b          	.insn	4, 0xe2553b2b
  14a5b8:	e265b82b          	.insn	4, 0xe265b82b
  14a5bc:	e275b92b          	.insn	4, 0xe275b92b
  14a5c0:	e285ba2b          	.insn	4, 0xe285ba2b
  14a5c4:	e295bb2b          	.insn	4, 0xe295bb2b
  14a5c8:	13fd                	c.addi	t2,-1
  14a5ca:	f80395e3          	bne	t2,zero,14a554 <BLOCK_INNER_LOOP624>
  14a5ce:	ff8a8913          	addi	s2,s5,-8
  14a5d2:	008a8993          	addi	s3,s5,8
  14a5d6:	010a8a13          	addi	s4,s5,16
  14a5da:	018a8b13          	addi	s6,s5,24
  14a5de:	0f000313          	addi	t1,zero,240
  14a5e2:	42036057          	vmv.s.x	v0,t1
  14a5e6:	00e072d7          	vsetvli	t0,zero,e16,mf4,tu,mu
  14a5ea:	020ad487          	vle16.v	v9,(s5)
  14a5ee:	0209d587          	vle16.v	v11,(s3)
  14a5f2:	020a5687          	vle16.v	v13,(s4)
  14a5f6:	020b5787          	vle16.v	v15,(s6)
  14a5fa:	00f072d7          	vsetvli	t0,zero,e16,mf2,tu,mu
  14a5fe:	00095487          	vle16.v	v9,(s2),v0.t
  14a602:	000ad587          	vle16.v	v11,(s5),v0.t
  14a606:	0009d687          	vle16.v	v13,(s3),v0.t
  14a60a:	000a5787          	vle16.v	v15,(s4),v0.t
  14a60e:	4a961457          	vfwcvt.f.f.v	v8,v9
  14a612:	4ab61557          	vfwcvt.f.f.v	v10,v11
  14a616:	4ad61657          	vfwcvt.f.f.v	v12,v13
  14a61a:	4af61757          	vfwcvt.f.f.v	v14,v15
  14a61e:	010072d7          	vsetvli	t0,zero,e32,m1,tu,mu
  14a622:	5e0404d7          	vmv.v.v	v9,v8
  14a626:	5e0505d7          	vmv.v.v	v11,v10
  14a62a:	5e0606d7          	vmv.v.v	v13,v12
  14a62e:	5e0707d7          	vmv.v.v	v15,v14
  14a632:	0f000313          	addi	t1,zero,240
  14a636:	42036057          	vmv.s.x	v0,t1
  14a63a:	017072d7          	vsetvli	t0,zero,e32,mf2,tu,mu
  14a63e:	9280d457          	vfmul.vf	v8,v8,ft1
  14a642:	92a0d557          	vfmul.vf	v10,v10,ft1
  14a646:	92c0d657          	vfmul.vf	v12,v12,ft1
  14a64a:	92e0d757          	vfmul.vf	v14,v14,ft1
  14a64e:	9291d4d7          	vfmul.vf	v9,v9,ft3
  14a652:	92b1d5d7          	vfmul.vf	v11,v11,ft3
  14a656:	92d1d6d7          	vfmul.vf	v13,v13,ft3
  14a65a:	92f1d7d7          	vfmul.vf	v15,v15,ft3
  14a65e:	010072d7          	vsetvli	t0,zero,e32,m1,tu,mu
  14a662:	90815457          	vfmul.vf	v8,v8,ft2,v0.t
  14a666:	90a15557          	vfmul.vf	v10,v10,ft2,v0.t
  14a66a:	90c15657          	vfmul.vf	v12,v12,ft2,v0.t
  14a66e:	90e15757          	vfmul.vf	v14,v14,ft2,v0.t
  14a672:	909254d7          	vfmul.vf	v9,v9,ft4,v0.t
  14a676:	90b255d7          	vfmul.vf	v11,v11,ft4,v0.t
  14a67a:	90d256d7          	vfmul.vf	v13,v13,ft4,v0.t
  14a67e:	90f257d7          	vfmul.vf	v15,v15,ft4,v0.t
  14a682:	013072d7          	vsetvli	t0,zero,e32,m8,tu,mu
  14a686:	4b019857          	vfcvt.f.x.v	v16,v16
  14a68a:	b2881c57          	vfmacc.vv	v24,v16,v8
  14a68e:	1e7d                	c.addi	t3,-1
  14a690:	ea0e11e3          	bne	t3,zero,14a532 <BLOCK_COUNTK_LOOP624>

000000000014a694 <RESULT_SAVE624>:
  14a694:	85be                	c.mv	a1,a5
  14a696:	01778633          	add	a2,a5,s7
  14a69a:	017606b3          	add	a3,a2,s7
  14a69e:	01768733          	add	a4,a3,s7
  14a6a2:	1641                	c.addi	a2,-16
  14a6a4:	1741                	c.addi	a4,-16
  14a6a6:	0f000313          	addi	t1,zero,240
  14a6aa:	42036057          	vmv.s.x	v0,t1
  14a6ae:	017072d7          	vsetvli	t0,zero,e32,mf2,tu,mu
  14a6b2:	0205ec27          	vse32.v	v24,(a1)
  14a6b6:	05c1                	c.addi	a1,16
  14a6b8:	0206eca7          	vse32.v	v25,(a3)
  14a6bc:	06c1                	c.addi	a3,16
  14a6be:	0205ed27          	vse32.v	v26,(a1)
  14a6c2:	05c1                	c.addi	a1,16
  14a6c4:	0206eda7          	vse32.v	v27,(a3)
  14a6c8:	06c1                	c.addi	a3,16
  14a6ca:	0205ee27          	vse32.v	v28,(a1)
  14a6ce:	05c1                	c.addi	a1,16
  14a6d0:	0206eea7          	vse32.v	v29,(a3)
  14a6d4:	06c1                	c.addi	a3,16
  14a6d6:	0205ef27          	vse32.v	v30,(a1)
  14a6da:	0206efa7          	vse32.v	v31,(a3)
  14a6de:	010072d7          	vsetvli	t0,zero,e32,m1,tu,mu
  14a6e2:	00066c27          	vse32.v	v24,(a2),v0.t
  14a6e6:	0641                	c.addi	a2,16
  14a6e8:	00076ca7          	vse32.v	v25,(a4),v0.t
  14a6ec:	0741                	c.addi	a4,16
  14a6ee:	00066d27          	vse32.v	v26,(a2),v0.t
  14a6f2:	0641                	c.addi	a2,16
  14a6f4:	00076da7          	vse32.v	v27,(a4),v0.t
  14a6f8:	0741                	c.addi	a4,16
  14a6fa:	00066e27          	vse32.v	v28,(a2),v0.t
  14a6fe:	0641                	c.addi	a2,16
  14a700:	00076ea7          	vse32.v	v29,(a4),v0.t
  14a704:	0741                	c.addi	a4,16
  14a706:	00066f27          	vse32.v	v30,(a2),v0.t
  14a70a:	00076fa7          	vse32.v	v31,(a4),v0.t
  14a70e:	0441                	c.addi	s0,16
  14a710:	04078793          	addi	a5,a5,64
  14a714:	df046fe3          	bltu	s0,a6,14a512 <END554+0x46>
  14a718:	6406                	c.ldsp	s0,64(sp)
  14a71a:	4511                	c.li	a0,4
  14a71c:	bb75                	c.j	14a4d8 <END554+0xc>
  14a71e:	4505                	c.li	a0,1
  14a720:	b3d9                	c.j	14a4e6 <END554+0x1a>
  14a722:	6406                	c.ldsp	s0,64(sp)
  14a724:	6ba2                	c.ldsp	s7,8(sp)
  14a726:	4511                	c.li	a0,4
  14a728:	bb7d                	c.j	14a4e6 <END554+0x1a>
  14a72a:	00080697          	auipc	a3,0x80
  14a72e:	14668693          	addi	a3,a3,326 # 1ca870 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x4c42>
  14a732:	0007b617          	auipc	a2,0x7b
  14a736:	6fe60613          	addi	a2,a2,1790 # 1c5e30 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x202>
  14a73a:	41900593          	addi	a1,zero,1049
  14a73e:	00080517          	auipc	a0,0x80
  14a742:	14a50513          	addi	a0,a0,330 # 1ca888 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x4c5a>
  14a746:	fc26                	c.sdsp	s1,56(sp)
  14a748:	f84a                	c.sdsp	s2,48(sp)
  14a74a:	f44e                	c.sdsp	s3,40(sp)
  14a74c:	f052                	c.sdsp	s4,32(sp)
  14a74e:	ec56                	c.sdsp	s5,24(sp)
  14a750:	e85a                	c.sdsp	s6,16(sp)
  14a752:	e45e                	c.sdsp	s7,8(sp)
  14a754:	ccd3a0ef          	jal	ra,85420 <ggml_abort@plt>
