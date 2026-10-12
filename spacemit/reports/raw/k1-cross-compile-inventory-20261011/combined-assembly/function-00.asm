
/home/moyamryia/Projects/riscv-accl/lab/k1-combined-fixture-r5-20261011-122000-work/payload/C/lib/libggml-cpu.so.0.16.0:     file format elf64-littleriscv


Disassembly of section .text:

00000000000dfb0e <_ZL23spine_k1_gdn_prefill128PfPKfS1_S1_fffS_>:
   dfb0e:	08000793          	addi	a5,zero,128
   dfb12:	04000293          	addi	t0,zero,64
   dfb16:	0d32f057          	vsetvli	zero,t0,e32,m8,ta,ma
   dfb1a:	10050293          	addi	t0,a0,256
   dfb1e:	02056007          	vle32.v	v0,(a0)
   dfb22:	0202e407          	vle32.v	v8,(t0)
   dfb26:	92055057          	vfmul.vf	v0,v0,fa0
   dfb2a:	92855457          	vfmul.vf	v8,v8,fa0
   dfb2e:	5e003857          	vmv.v.i	v16,0
   dfb32:	0205ec07          	vle32.v	v24,(a1)
   dfb36:	b3801857          	vfmacc.vv	v16,v0,v24
   dfb3a:	10058313          	addi	t1,a1,256
   dfb3e:	02036c07          	vle32.v	v24,(t1)
   dfb42:	b3841857          	vfmacc.vv	v16,v8,v24
   dfb46:	5e003c57          	vmv.v.i	v24,0
   dfb4a:	070c1857          	vfredusum.vs	v16,v16,v24
   dfb4e:	43001057          	vfmv.f.s	ft0,v16
   dfb52:	00062087          	flw	ft1,0(a2)
   dfb56:	0800f0d3          	fsub.s	ft1,ft1,ft0
   dfb5a:	10b0f0d3          	fmul.s	ft1,ft1,fa1
   dfb5e:	0205ec07          	vle32.v	v24,(a1)
   dfb62:	b380d057          	vfmacc.vf	v0,ft1,v24
   dfb66:	02056027          	vse32.v	v0,(a0)
   dfb6a:	5e003857          	vmv.v.i	v16,0
   dfb6e:	0206ec07          	vle32.v	v24,(a3)
   dfb72:	b3801857          	vfmacc.vv	v16,v0,v24
   dfb76:	10058313          	addi	t1,a1,256
   dfb7a:	02036c07          	vle32.v	v24,(t1)
   dfb7e:	b380d457          	vfmacc.vf	v8,ft1,v24
   dfb82:	0202e427          	vse32.v	v8,(t0)
   dfb86:	10068313          	addi	t1,a3,256
   dfb8a:	02036c07          	vle32.v	v24,(t1)
   dfb8e:	b3841857          	vfmacc.vv	v16,v8,v24
   dfb92:	5e003c57          	vmv.v.i	v24,0
   dfb96:	070c1857          	vfredusum.vs	v16,v16,v24
   dfb9a:	43001057          	vfmv.f.s	ft0,v16
   dfb9e:	10c07053          	fmul.s	ft0,ft0,fa2
   dfba2:	00072027          	fsw	ft0,0(a4)
   dfba6:	20050513          	addi	a0,a0,512
   dfbaa:	0611                	c.addi	a2,4
   dfbac:	0711                	c.addi	a4,4
   dfbae:	17fd                	c.addi	a5,-1
   dfbb0:	f7ad                	c.bnez	a5,dfb1a <_ZL23spine_k1_gdn_prefill128PfPKfS1_S1_fffS_+0xc>
   dfbb2:	8082                	c.jr	ra
