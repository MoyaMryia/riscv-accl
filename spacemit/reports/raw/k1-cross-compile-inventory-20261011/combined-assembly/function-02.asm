
/home/moyamryia/Projects/riscv-accl/lab/k1-combined-fixture-r5-20261011-122000-work/payload/C/lib/libggml-cpu.so.0.16.0:     file format elf64-littleriscv


Disassembly of section .text:

00000000000e2296 <_ZL24ggml_gdn_decode_step_rvvPfPKfS1_S1_ffflS_>:
   e2296:	0ce05963          	bge	zero,a4,e2368 <_ZL24ggml_gdn_decode_step_rvvPfPKfS1_S1_ffflS_+0xd2>
   e229a:	c22022f3          	csrrs	t0,vlenb,zero
   e229e:	00329313          	slli	t1,t0,0x3
   e22a2:	40610133          	sub	sp,sp,t1
   e22a6:	0d307357          	vsetvli	t1,zero,e32,m8,ta,ma
   e22aa:	5e003457          	vmv.v.i	v8,0
   e22ae:	20f74eb3          	sh2add	t4,a4,a5
   e22b2:	42006c57          	vmv.s.x	v24,zero
   e22b6:	00271e13          	slli	t3,a4,0x2
   e22ba:	e2810427          	vs8r.v	v8,(sp)
   e22be:	e2816807          	vl8re32.v	v16,(sp)
   e22c2:	4881                	c.li	a7,0
   e22c4:	41170833          	sub	a6,a4,a7
   e22c8:	0d387857          	vsetvli	a6,a6,e32,m8,ta,ma
   e22cc:	20a8cf33          	sh2add	t5,a7,a0
   e22d0:	020f6407          	vle32.v	v8,(t5)
   e22d4:	20b8cfb3          	sh2add	t6,a7,a1
   e22d8:	98c2                	c.add	a7,a6
   e22da:	92855457          	vfmul.vf	v8,v8,fa0
   e22de:	020f6427          	vse32.v	v8,(t5)
   e22e2:	020fe007          	vle32.v	v0,(t6)
   e22e6:	b2041857          	vfmacc.vv	v16,v8,v0
   e22ea:	fce8cde3          	blt	a7,a4,e22c4 <_ZL24ggml_gdn_decode_step_rvvPfPKfS1_S1_ffflS_+0x2e>
   e22ee:	0d307357          	vsetvli	t1,zero,e32,m8,ta,ma
   e22f2:	00062787          	flw	fa5,0(a2)
   e22f6:	070c10d7          	vfredusum.vs	v1,v16,v24
   e22fa:	4881                	c.li	a7,0
   e22fc:	e2816807          	vl8re32.v	v16,(sp)
   e2300:	42101757          	vfmv.f.s	fa4,v1
   e2304:	08e7f7d3          	fsub.s	fa5,fa5,fa4
   e2308:	10b7f7d3          	fmul.s	fa5,fa5,fa1
   e230c:	41170833          	sub	a6,a4,a7
   e2310:	0d387857          	vsetvli	a6,a6,e32,m8,ta,ma
   e2314:	20a8cf33          	sh2add	t5,a7,a0
   e2318:	20b8cfb3          	sh2add	t6,a7,a1
   e231c:	020f6407          	vle32.v	v8,(t5)
   e2320:	020fe007          	vle32.v	v0,(t6)
   e2324:	20d8cfb3          	sh2add	t6,a7,a3
   e2328:	98c2                	c.add	a7,a6
   e232a:	b207d457          	vfmacc.vf	v8,fa5,v0
   e232e:	020f6427          	vse32.v	v8,(t5)
   e2332:	020fe007          	vle32.v	v0,(t6)
   e2336:	b2041857          	vfmacc.vv	v16,v8,v0
   e233a:	fce8c9e3          	blt	a7,a4,e230c <_ZL24ggml_gdn_decode_step_rvvPfPKfS1_S1_ffflS_+0x76>
   e233e:	0d307357          	vsetvli	t1,zero,e32,m8,ta,ma
   e2342:	0791                	c.addi	a5,4
   e2344:	070c1857          	vfredusum.vs	v16,v16,v24
   e2348:	9572                	c.add	a0,t3
   e234a:	0611                	c.addi	a2,4
   e234c:	430017d7          	vfmv.f.s	fa5,v16
   e2350:	10c7f7d3          	fmul.s	fa5,fa5,fa2
   e2354:	fef7ae27          	fsw	fa5,-4(a5)
   e2358:	f6fe93e3          	bne	t4,a5,e22be <_ZL24ggml_gdn_decode_step_rvvPfPKfS1_S1_ffflS_+0x28>
   e235c:	c22022f3          	csrrs	t0,vlenb,zero
   e2360:	00329313          	slli	t1,t0,0x3
   e2364:	911a                	c.add	sp,t1
   e2366:	8082                	c.jr	ra
   e2368:	8082                	c.jr	ra
