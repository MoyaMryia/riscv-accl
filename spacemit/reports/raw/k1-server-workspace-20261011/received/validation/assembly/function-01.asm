
/home/moyamryia/Projects/riscv-accl/lab/k1-combined-fixture-r5-20261011-122000-work/payload/C/lib/libggml-cpu.so.0.16.0:     file format elf64-littleriscv


Disassembly of section .text:

00000000000e1cdc <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor>:
   e1cdc:	0985be03          	ld	t3,152(a1)
   e1ce0:	7115                	c.addi16sp	sp,-224
   e1ce2:	e16a                	c.sdsp	s10,128(sp)
   e1ce4:	000e2703          	lw	a4,0(t3)
   e1ce8:	0a05bd03          	ld	s10,160(a1)
   e1cec:	ed86                	c.sdsp	ra,216(sp)
   e1cee:	010e3783          	ld	a5,16(t3)
   e1cf2:	010d3f83          	ld	t6,16(s10)
   e1cf6:	56071663          	bne	a4,zero,e2262 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x586>
   e1cfa:	000d2703          	lw	a4,0(s10)
   e1cfe:	56071263          	bne	a4,zero,e2262 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x586>
   e1d02:	030e3703          	ld	a4,48(t3)
   e1d06:	4611                	c.li	a2,4
   e1d08:	52c71363          	bne	a4,a2,e222e <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x552>
   e1d0c:	030d3603          	ld	a2,48(s10)
   e1d10:	50e61f63          	bne	a2,a4,e222e <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x552>
   e1d14:	0185b883          	ld	a7,24(a1)
   e1d18:	8f2e                	c.mv	t5,a1
   e1d1a:	018e3583          	ld	a1,24(t3)
   e1d1e:	e962                	c.sdsp	s8,144(sp)
   e1d20:	ffff8c13          	addi	s8,t6,-1
   e1d24:	011c0733          	add	a4,s8,a7
   e1d28:	4ce59a63          	bne	a1,a4,e21fc <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x520>
   e1d2c:	018d3703          	ld	a4,24(s10)
   e1d30:	48e79d63          	bne	a5,a4,e21ca <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x4ee>
   e1d34:	010f3703          	ld	a4,16(t5)
   e1d38:	48e79963          	bne	a5,a4,e21ca <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x4ee>
   e1d3c:	020f3703          	ld	a4,32(t5)
   e1d40:	020e3583          	ld	a1,32(t3)
   e1d44:	44e59a63          	bne	a1,a4,e2198 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x4bc>
   e1d48:	030f3583          	ld	a1,48(t5)
   e1d4c:	44c59663          	bne	a1,a2,e2198 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x4bc>
   e1d50:	4150                	c.lw	a2,4(a0)
   e1d52:	4114                	c.lw	a3,0(a0)
   e1d54:	fcee                	c.sdsp	s11,120(sp)
   e1d56:	00c783b3          	add	t2,a5,a2
   e1d5a:	13fd                	c.addi	t2,-1
   e1d5c:	02c3c3b3          	div	t2,t2,a2
   e1d60:	02768db3          	mul	s11,a3,t2
   e1d64:	93ee                	c.add	t2,s11
   e1d66:	4077c063          	blt	a5,t2,e2166 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x48a>
   e1d6a:	0ae05f63          	bge	zero,a4,e1e28 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x14c>
   e1d6e:	002fd793          	srli	a5,t6,0x2
   e1d72:	cd027057          	vsetivli	zero,4,e32,m1,ta,ma
   e1d76:	f556                	c.sdsp	s5,168(sp)
   e1d78:	00479a93          	slli	s5,a5,0x4
   e1d7c:	002d9793          	slli	a5,s11,0x2
   e1d80:	e5a6                	c.sdsp	s1,200(sp)
   e1d82:	f83e                	c.sdsp	a5,48(sp)
   e1d84:	4481                	c.li	s1,0
   e1d86:	003ff793          	andi	a5,t6,3
   e1d8a:	e9a2                	c.sdsp	s0,208(sp)
   e1d8c:	e566                	c.sdsp	s9,136(sp)
   e1d8e:	e1ca                	c.sdsp	s2,192(sp)
   e1d90:	fd4e                	c.sdsp	s3,184(sp)
   e1d92:	f952                	c.sdsp	s4,176(sp)
   e1d94:	f15a                	c.sdsp	s6,160(sp)
   e1d96:	ed5e                	c.sdsp	s7,152(sp)
   e1d98:	4c89                	c.li	s9,2
   e1d9a:	ffcff413          	andi	s0,t6,-4
   e1d9e:	fc3e                	c.sdsp	a5,56(sp)
   e1da0:	86a6                	c.mv	a3,s1
   e1da2:	07105763          	bge	zero,a7,e1e10 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x134>
   e1da6:	0f8e3703          	ld	a4,248(t3)
   e1daa:	038e3583          	ld	a1,56(t3)
   e1dae:	040e3503          	ld	a0,64(t3)
   e1db2:	040f3303          	ld	t1,64(t5)
   e1db6:	038f3603          	ld	a2,56(t5)
   e1dba:	0f8f3983          	ld	s3,248(t5)
   e1dbe:	054f2283          	lw	t0,84(t5)
   e1dc2:	4781                	c.li	a5,0
   e1dc4:	02f58eb3          	mul	t4,a1,a5
   e1dc8:	02a68833          	mul	a6,a3,a0
   e1dcc:	026684b3          	mul	s1,a3,t1
   e1dd0:	9876                	c.add	a6,t4
   e1dd2:	01070eb3          	add	t4,a4,a6
   e1dd6:	02c78933          	mul	s2,a5,a2
   e1dda:	94ca                	c.add	s1,s2
   e1ddc:	94ce                	c.add	s1,s3
   e1dde:	17928863          	beq	t0,s9,e1f4e <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x272>
   e1de2:	1e7dda63          	bge	s11,t2,e1fd6 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x2fa>
   e1de6:	72c2                	c.ldsp	t0,48(sp)
   e1de8:	e44e                	c.sdsp	s3,8(sp)
   e1dea:	896e                	c.mv	s2,s11
   e1dec:	9816                	c.add	a6,t0
   e1dee:	010709b3          	add	s3,a4,a6
   e1df2:	9496                	c.add	s1,t0
   e1df4:	05f04063          	blt	zero,t6,e1e34 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x158>
   e1df8:	0004a023          	sw	zero,0(s1)
   e1dfc:	0905                	c.addi	s2,1
   e1dfe:	0491                	c.addi	s1,4
   e1e00:	0991                	c.addi	s3,4
   e1e02:	ff2399e3          	bne	t2,s2,e1df4 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x118>
   e1e06:	0785                	c.addi	a5,1
   e1e08:	1d17cb63          	blt	a5,a7,e1fde <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x302>
   e1e0c:	020f3703          	ld	a4,32(t5)
   e1e10:	0685                	c.addi	a3,1
   e1e12:	f8e6c8e3          	blt	a3,a4,e1da2 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0xc6>
   e1e16:	644e                	c.ldsp	s0,208(sp)
   e1e18:	64ae                	c.ldsp	s1,200(sp)
   e1e1a:	690e                	c.ldsp	s2,192(sp)
   e1e1c:	79ea                	c.ldsp	s3,184(sp)
   e1e1e:	7a4a                	c.ldsp	s4,176(sp)
   e1e20:	7aaa                	c.ldsp	s5,168(sp)
   e1e22:	7b0a                	c.ldsp	s6,160(sp)
   e1e24:	6bea                	c.ldsp	s7,152(sp)
   e1e26:	6caa                	c.ldsp	s9,136(sp)
   e1e28:	60ee                	c.ldsp	ra,216(sp)
   e1e2a:	6c4a                	c.ldsp	s8,144(sp)
   e1e2c:	7de6                	c.ldsp	s11,120(sp)
   e1e2e:	6d0a                	c.ldsp	s10,128(sp)
   e1e30:	612d                	c.addi16sp	sp,224
   e1e32:	8082                	c.jr	ra
   e1e34:	038d3b83          	ld	s7,56(s10)
   e1e38:	00be82b3          	add	t0,t4,a1
   e1e3c:	f4ba                	c.sdsp	a4,104(sp)
   e1e3e:	8716                	c.mv	a4,t0
   e1e40:	037902b3          	mul	t0,s2,s7
   e1e44:	0f8d3b03          	ld	s6,248(s10)
   e1e48:	00259813          	slli	a6,a1,0x2
   e1e4c:	e842                	c.sdsp	a6,16(sp)
   e1e4e:	00159813          	slli	a6,a1,0x1
   e1e52:	ec42                	c.sdsp	a6,24(sp)
   e1e54:	e0ea                	c.sdsp	s10,64(sp)
   e1e56:	e4ee                	c.sdsp	s11,72(sp)
   e1e58:	ecc6                	c.sdsp	a7,88(sp)
   e1e5a:	e01e                	c.sdsp	t2,0(sp)
   e1e5c:	f03e                	c.sdsp	a5,32(sp)
   e1e5e:	f472                	c.sdsp	t3,40(sp)
   e1e60:	e8b6                	c.sdsp	a3,80(sp)
   e1e62:	f0fa                	c.sdsp	t5,96(sp)
   e1e64:	6842                	c.ldsp	a6,16(sp)
   e1e66:	6d62                	c.ldsp	s10,24(sp)
   e1e68:	7de2                	c.ldsp	s11,56(sp)
   e1e6a:	f00007d3          	fmv.w.x	fa5,zero
   e1e6e:	00291a13          	slli	s4,s2,0x2
   e1e72:	88aa                	c.mv	a7,a0
   e1e74:	92da                	c.add	t0,s6
   e1e76:	0d8cfa63          	bgeu	s9,s8,e1f4a <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x26e>
   e1e7a:	8516                	c.mv	a0,t0
   e1e7c:	005a8f33          	add	t5,s5,t0
   e1e80:	01a986b3          	add	a3,s3,s10
   e1e84:	87ce                	c.mv	a5,s3
   e1e86:	0007a707          	flw	fa4,0(a5)
   e1e8a:	02056187          	vle32.v	v3,(a0)
   e1e8e:	00b78e33          	add	t3,a5,a1
   e1e92:	4207d157          	vfmv.s.f	v2,fa5
   e1e96:	000e2687          	flw	fa3,0(t3)
   e1e9a:	5e0750d7          	vfmv.v.f	v1,fa4
   e1e9e:	0006a707          	flw	fa4,0(a3)
   e1ea2:	00b683b3          	add	t2,a3,a1
   e1ea6:	0003a787          	flw	fa5,0(t2)
   e1eaa:	3e16d0d7          	vfslide1down.vf	v1,v1,fa3
   e1eae:	0541                	c.addi	a0,16
   e1eb0:	97c2                	c.add	a5,a6
   e1eb2:	96c2                	c.add	a3,a6
   e1eb4:	3e1750d7          	vfslide1down.vf	v1,v1,fa4
   e1eb8:	3e17d0d7          	vfslide1down.vf	v1,v1,fa5
   e1ebc:	921190d7          	vfmul.vv	v1,v1,v3
   e1ec0:	0e1110d7          	vfredosum.vs	v1,v1,v2
   e1ec4:	421017d7          	vfmv.f.s	fa5,v1
   e1ec8:	fbe51fe3          	bne	a0,t5,e1e86 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x1aa>
   e1ecc:	87a2                	c.mv	a5,s0
   e1ece:	040d8d63          	beq	s11,zero,e1f28 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x24c>
   e1ed2:	02f586b3          	mul	a3,a1,a5
   e1ed6:	014e8533          	add	a0,t4,s4
   e1eda:	2057c2b3          	sh2add	t0,a5,t0
   e1ede:	0002a687          	flw	fa3,0(t0)
   e1ee2:	00178e13          	addi	t3,a5,1
   e1ee6:	00d50f33          	add	t5,a0,a3
   e1eea:	000f2707          	flw	fa4,0(t5)
   e1eee:	10d77753          	fmul.s	fa4,fa4,fa3
   e1ef2:	00e7f7d3          	fadd.s	fa5,fa5,fa4
   e1ef6:	03fe5963          	bge	t3,t6,e1f28 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x24c>
   e1efa:	96ae                	c.add	a3,a1
   e1efc:	9536                	c.add	a0,a3
   e1efe:	00052687          	flw	fa3,0(a0)
   e1f02:	0042a707          	flw	fa4,4(t0)
   e1f06:	0789                	c.addi	a5,2
   e1f08:	10d77753          	fmul.s	fa4,fa4,fa3
   e1f0c:	00e7f7d3          	fadd.s	fa5,fa5,fa4
   e1f10:	01f7dc63          	bge	a5,t6,e1f28 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x24c>
   e1f14:	9a3a                	c.add	s4,a4
   e1f16:	9a36                	c.add	s4,a3
   e1f18:	000a2707          	flw	fa4,0(s4)
   e1f1c:	0082a687          	flw	fa3,8(t0)
   e1f20:	10d77753          	fmul.s	fa4,fa4,fa3
   e1f24:	00e7f7d3          	fadd.s	fa5,fa5,fa4
   e1f28:	6782                	c.ldsp	a5,0(sp)
   e1f2a:	00f4a027          	fsw	fa5,0(s1)
   e1f2e:	0905                	c.addi	s2,1
   e1f30:	0491                	c.addi	s1,4
   e1f32:	0991                	c.addi	s3,4
   e1f34:	25278763          	beq	a5,s2,e2182 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x4a6>
   e1f38:	037902b3          	mul	t0,s2,s7
   e1f3c:	f00007d3          	fmv.w.x	fa5,zero
   e1f40:	00291a13          	slli	s4,s2,0x2
   e1f44:	92da                	c.add	t0,s6
   e1f46:	f38ceae3          	bltu	s9,s8,e1e7a <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x19e>
   e1f4a:	4781                	c.li	a5,0
   e1f4c:	b759                	c.j	e1ed2 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x1f6>
   e1f4e:	896e                	c.mv	s2,s11
   e1f50:	207ddd63          	bge	s11,t2,e216a <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x48e>
   e1f54:	41238533          	sub	a0,t2,s2
   e1f58:	0d057557          	vsetvli	a0,a0,e32,m1,ta,ma
   e1f5c:	00291813          	slli	a6,s2,0x2
   e1f60:	5e003157          	vmv.v.i	v2,0
   e1f64:	03f05d63          	bge	zero,t6,e1f9e <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x2c2>
   e1f68:	038d3883          	ld	a7,56(s10)
   e1f6c:	038e3583          	ld	a1,56(t3)
   e1f70:	0f8d3283          	ld	t0,248(s10)
   e1f74:	03288333          	mul	t1,a7,s2
   e1f78:	4601                	c.li	a2,0
   e1f7a:	20664733          	sh2add	a4,a2,t1
   e1f7e:	9716                	c.add	a4,t0
   e1f80:	0b176187          	vlse32.v	v3,(a4),a7
   e1f84:	02b60733          	mul	a4,a2,a1
   e1f88:	0605                	c.addi	a2,1
   e1f8a:	9742                	c.add	a4,a6
   e1f8c:	9776                	c.add	a4,t4
   e1f8e:	02076087          	vle32.v	v1,(a4)
   e1f92:	921190d7          	vfmul.vv	v1,v1,v3
   e1f96:	02209157          	vfadd.vv	v2,v2,v1
   e1f9a:	fecf90e3          	bne	t6,a2,e1f7a <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x29e>
   e1f9e:	9826                	c.add	a6,s1
   e1fa0:	02086127          	vse32.v	v2,(a6)
   e1fa4:	992a                	c.add	s2,a0
   e1fa6:	fa7947e3          	blt	s2,t2,e1f54 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x278>
   e1faa:	018f3883          	ld	a7,24(t5)
   e1fae:	0785                	c.addi	a5,1
   e1fb0:	1b17d663          	bge	a5,a7,e215c <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x480>
   e1fb4:	0f8e3703          	ld	a4,248(t3)
   e1fb8:	cd027057          	vsetivli	zero,4,e32,m1,ta,ma
   e1fbc:	038e3583          	ld	a1,56(t3)
   e1fc0:	040e3503          	ld	a0,64(t3)
   e1fc4:	040f3303          	ld	t1,64(t5)
   e1fc8:	038f3603          	ld	a2,56(t5)
   e1fcc:	0f8f3983          	ld	s3,248(t5)
   e1fd0:	054f2283          	lw	t0,84(t5)
   e1fd4:	bbc5                	c.j	e1dc4 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0xe8>
   e1fd6:	0785                	c.addi	a5,1
   e1fd8:	1917df63          	bge	a5,a7,e2176 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x49a>
   e1fdc:	e44e                	c.sdsp	s3,8(sp)
   e1fde:	02a68833          	mul	a6,a3,a0
   e1fe2:	74c2                	c.ldsp	s1,48(sp)
   e1fe4:	e4b6                	c.sdsp	a3,72(sp)
   e1fe6:	e0f2                	c.sdsp	t3,64(sp)
   e1fe8:	00259513          	slli	a0,a1,0x2
   e1fec:	00159a13          	slli	s4,a1,0x1
   e1ff0:	e8fa                	c.sdsp	t5,80(sp)
   e1ff2:	02668b33          	mul	s6,a3,t1
   e1ff6:	66a2                	c.ldsp	a3,8(sp)
   e1ff8:	00980bb3          	add	s7,a6,s1
   e1ffc:	8346                	c.mv	t1,a7
   e1ffe:	88de                	c.mv	a7,s7
   e2000:	8e5a                	c.mv	t3,s6
   e2002:	02f58f33          	mul	t5,a1,a5
   e2006:	02f60eb3          	mul	t4,a2,a5
   e200a:	010f09b3          	add	s3,t5,a6
   e200e:	99ba                	c.add	s3,a4
   e2010:	9ef2                	c.add	t4,t3
   e2012:	027dd363          	bge	s11,t2,e2038 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x35c>
   e2016:	74c2                	c.ldsp	s1,48(sp)
   e2018:	9f46                	c.add	t5,a7
   e201a:	9ea6                	c.add	t4,s1
   e201c:	01d68933          	add	s2,a3,t4
   e2020:	01e704b3          	add	s1,a4,t5
   e2024:	8f6e                	c.mv	t5,s11
   e2026:	03f04363          	blt	zero,t6,e204c <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x370>
   e202a:	00092023          	sw	zero,0(s2)
   e202e:	0f05                	c.addi	t5,1
   e2030:	0911                	c.addi	s2,4
   e2032:	0491                	c.addi	s1,4
   e2034:	ffe399e3          	bne	t2,t5,e2026 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x34a>
   e2038:	0785                	c.addi	a5,1
   e203a:	fc67c4e3          	blt	a5,t1,e2002 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x326>
   e203e:	6f46                	c.ldsp	t5,80(sp)
   e2040:	6e06                	c.ldsp	t3,64(sp)
   e2042:	66a6                	c.ldsp	a3,72(sp)
   e2044:	020f3703          	ld	a4,32(t5)
   e2048:	889a                	c.mv	a7,t1
   e204a:	b3d9                	c.j	e1e10 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x134>
   e204c:	038d3b83          	ld	s7,56(s10)
   e2050:	ec6e                	c.sdsp	s11,24(sp)
   e2052:	0f8d3b03          	ld	s6,248(s10)
   e2056:	037f0db3          	mul	s11,t5,s7
   e205a:	f472                	c.sdsp	t3,40(sp)
   e205c:	e01e                	c.sdsp	t2,0(sp)
   e205e:	e43e                	c.sdsp	a5,8(sp)
   e2060:	e86a                	c.sdsp	s10,16(sp)
   e2062:	f01a                	c.sdsp	t1,32(sp)
   e2064:	f00007d3          	fmv.w.x	fa5,zero
   e2068:	002f1293          	slli	t0,t5,0x2
   e206c:	8e42                	c.mv	t3,a6
   e206e:	9dda                	c.add	s11,s6
   e2070:	0d8cf963          	bgeu	s9,s8,e2142 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x466>
   e2074:	836e                	c.mv	t1,s11
   e2076:	01ba8d33          	add	s10,s5,s11
   e207a:	01448833          	add	a6,s1,s4
   e207e:	87a6                	c.mv	a5,s1
   e2080:	0007a707          	flw	fa4,0(a5)
   e2084:	02036187          	vle32.v	v3,(t1)
   e2088:	00b78eb3          	add	t4,a5,a1
   e208c:	4207d157          	vfmv.s.f	v2,fa5
   e2090:	000ea687          	flw	fa3,0(t4)
   e2094:	5e0750d7          	vfmv.v.f	v1,fa4
   e2098:	00082707          	flw	fa4,0(a6)
   e209c:	00b803b3          	add	t2,a6,a1
   e20a0:	0003a787          	flw	fa5,0(t2)
   e20a4:	3e16d0d7          	vfslide1down.vf	v1,v1,fa3
   e20a8:	0341                	c.addi	t1,16
   e20aa:	97aa                	c.add	a5,a0
   e20ac:	982a                	c.add	a6,a0
   e20ae:	3e1750d7          	vfslide1down.vf	v1,v1,fa4
   e20b2:	3e17d0d7          	vfslide1down.vf	v1,v1,fa5
   e20b6:	921190d7          	vfmul.vv	v1,v1,v3
   e20ba:	0e1110d7          	vfredosum.vs	v1,v1,v2
   e20be:	421017d7          	vfmv.f.s	fa5,v1
   e20c2:	fa6d1fe3          	bne	s10,t1,e2080 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x3a4>
   e20c6:	87a2                	c.mv	a5,s0
   e20c8:	048f8c63          	beq	t6,s0,e2120 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x444>
   e20cc:	02b78833          	mul	a6,a5,a1
   e20d0:	21b7cdb3          	sh2add	s11,a5,s11
   e20d4:	000da687          	flw	fa3,0(s11)
   e20d8:	00178313          	addi	t1,a5,1
   e20dc:	01098eb3          	add	t4,s3,a6
   e20e0:	9e96                	c.add	t4,t0
   e20e2:	000ea707          	flw	fa4,0(t4)
   e20e6:	10d77753          	fmul.s	fa4,fa4,fa3
   e20ea:	00e7f7d3          	fadd.s	fa5,fa5,fa4
   e20ee:	03f35963          	bge	t1,t6,e2120 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x444>
   e20f2:	982e                	c.add	a6,a1
   e20f4:	92ce                	c.add	t0,s3
   e20f6:	92c2                	c.add	t0,a6
   e20f8:	0002a687          	flw	fa3,0(t0)
   e20fc:	004da707          	flw	fa4,4(s11)
   e2100:	0789                	c.addi	a5,2
   e2102:	10d77753          	fmul.s	fa4,fa4,fa3
   e2106:	00e7f7d3          	fadd.s	fa5,fa5,fa4
   e210a:	01f7db63          	bge	a5,t6,e2120 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x444>
   e210e:	92ae                	c.add	t0,a1
   e2110:	0002a687          	flw	fa3,0(t0)
   e2114:	008da707          	flw	fa4,8(s11)
   e2118:	10d77753          	fmul.s	fa4,fa4,fa3
   e211c:	00e7f7d3          	fadd.s	fa5,fa5,fa4
   e2120:	6782                	c.ldsp	a5,0(sp)
   e2122:	00f92027          	fsw	fa5,0(s2)
   e2126:	0f05                	c.addi	t5,1
   e2128:	0911                	c.addi	s2,4
   e212a:	0491                	c.addi	s1,4
   e212c:	01e78d63          	beq	a5,t5,e2146 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x46a>
   e2130:	037f0db3          	mul	s11,t5,s7
   e2134:	f00007d3          	fmv.w.x	fa5,zero
   e2138:	002f1293          	slli	t0,t5,0x2
   e213c:	9dda                	c.add	s11,s6
   e213e:	f38cebe3          	bltu	s9,s8,e2074 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x398>
   e2142:	4781                	c.li	a5,0
   e2144:	b761                	c.j	e20cc <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x3f0>
   e2146:	83be                	c.mv	t2,a5
   e2148:	67a2                	c.ldsp	a5,8(sp)
   e214a:	7302                	c.ldsp	t1,32(sp)
   e214c:	8872                	c.mv	a6,t3
   e214e:	0785                	c.addi	a5,1
   e2150:	6d42                	c.ldsp	s10,16(sp)
   e2152:	6de2                	c.ldsp	s11,24(sp)
   e2154:	7e22                	c.ldsp	t3,40(sp)
   e2156:	ea67c6e3          	blt	a5,t1,e2002 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x326>
   e215a:	b5d5                	c.j	e203e <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x362>
   e215c:	020f3703          	ld	a4,32(t5)
   e2160:	cd027057          	vsetivli	zero,4,e32,m1,ta,ma
   e2164:	b175                	c.j	e1e10 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x134>
   e2166:	83be                	c.mv	t2,a5
   e2168:	b109                	c.j	e1d6a <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x8e>
   e216a:	0785                	c.addi	a5,1
   e216c:	c517cce3          	blt	a5,a7,e1dc4 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0xe8>
   e2170:	020f3703          	ld	a4,32(t5)
   e2174:	b971                	c.j	e1e10 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x134>
   e2176:	020f3783          	ld	a5,32(t5)
   e217a:	0685                	c.addi	a3,1
   e217c:	c4f6c3e3          	blt	a3,a5,e1dc2 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0xe6>
   e2180:	b959                	c.j	e1e16 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x13a>
   e2182:	8546                	c.mv	a0,a7
   e2184:	6382                	c.ldsp	t2,0(sp)
   e2186:	7782                	c.ldsp	a5,32(sp)
   e2188:	7e22                	c.ldsp	t3,40(sp)
   e218a:	6d06                	c.ldsp	s10,64(sp)
   e218c:	6da6                	c.ldsp	s11,72(sp)
   e218e:	66c6                	c.ldsp	a3,80(sp)
   e2190:	7f06                	c.ldsp	t5,96(sp)
   e2192:	68e6                	c.ldsp	a7,88(sp)
   e2194:	7726                	c.ldsp	a4,104(sp)
   e2196:	b985                	c.j	e1e06 <_ZL21spine_k1_ssm_conv_cpuPK19ggml_compute_paramsP11ggml_tensor+0x12a>
   e2198:	000e5697          	auipc	a3,0xe5
   e219c:	f9068693          	addi	a3,a3,-112 # 1c7128 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x14fa>
   e21a0:	000e4617          	auipc	a2,0xe4
   e21a4:	c9060613          	addi	a2,a2,-880 # 1c5e30 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x202>
   e21a8:	45d5                	c.li	a1,21
   e21aa:	000e5517          	auipc	a0,0xe5
   e21ae:	e4e50513          	addi	a0,a0,-434 # 1c6ff8 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x13ca>
   e21b2:	e9a2                	c.sdsp	s0,208(sp)
   e21b4:	e5a6                	c.sdsp	s1,200(sp)
   e21b6:	e1ca                	c.sdsp	s2,192(sp)
   e21b8:	fd4e                	c.sdsp	s3,184(sp)
   e21ba:	f952                	c.sdsp	s4,176(sp)
   e21bc:	f556                	c.sdsp	s5,168(sp)
   e21be:	f15a                	c.sdsp	s6,160(sp)
   e21c0:	ed5e                	c.sdsp	s7,152(sp)
   e21c2:	e566                	c.sdsp	s9,136(sp)
   e21c4:	fcee                	c.sdsp	s11,120(sp)
   e21c6:	a5aa30ef          	jal	ra,85420 <ggml_abort@plt>
   e21ca:	000e5697          	auipc	a3,0xe5
   e21ce:	f2668693          	addi	a3,a3,-218 # 1c70f0 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x14c2>
   e21d2:	000e4617          	auipc	a2,0xe4
   e21d6:	c5e60613          	addi	a2,a2,-930 # 1c5e30 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x202>
   e21da:	45d1                	c.li	a1,20
   e21dc:	000e5517          	auipc	a0,0xe5
   e21e0:	e1c50513          	addi	a0,a0,-484 # 1c6ff8 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x13ca>
   e21e4:	e9a2                	c.sdsp	s0,208(sp)
   e21e6:	e5a6                	c.sdsp	s1,200(sp)
   e21e8:	e1ca                	c.sdsp	s2,192(sp)
   e21ea:	fd4e                	c.sdsp	s3,184(sp)
   e21ec:	f952                	c.sdsp	s4,176(sp)
   e21ee:	f556                	c.sdsp	s5,168(sp)
   e21f0:	f15a                	c.sdsp	s6,160(sp)
   e21f2:	ed5e                	c.sdsp	s7,152(sp)
   e21f4:	e566                	c.sdsp	s9,136(sp)
   e21f6:	fcee                	c.sdsp	s11,120(sp)
   e21f8:	a28a30ef          	jal	ra,85420 <ggml_abort@plt>
   e21fc:	000e5697          	auipc	a3,0xe5
   e2200:	ecc68693          	addi	a3,a3,-308 # 1c70c8 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x149a>
   e2204:	000e4617          	auipc	a2,0xe4
   e2208:	c2c60613          	addi	a2,a2,-980 # 1c5e30 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x202>
   e220c:	45cd                	c.li	a1,19
   e220e:	000e5517          	auipc	a0,0xe5
   e2212:	dea50513          	addi	a0,a0,-534 # 1c6ff8 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x13ca>
   e2216:	e9a2                	c.sdsp	s0,208(sp)
   e2218:	e5a6                	c.sdsp	s1,200(sp)
   e221a:	e1ca                	c.sdsp	s2,192(sp)
   e221c:	fd4e                	c.sdsp	s3,184(sp)
   e221e:	f952                	c.sdsp	s4,176(sp)
   e2220:	f556                	c.sdsp	s5,168(sp)
   e2222:	f15a                	c.sdsp	s6,160(sp)
   e2224:	ed5e                	c.sdsp	s7,152(sp)
   e2226:	e566                	c.sdsp	s9,136(sp)
   e2228:	fcee                	c.sdsp	s11,120(sp)
   e222a:	9f6a30ef          	jal	ra,85420 <ggml_abort@plt>
   e222e:	000e5697          	auipc	a3,0xe5
   e2232:	e5268693          	addi	a3,a3,-430 # 1c7080 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x1452>
   e2236:	000e4617          	auipc	a2,0xe4
   e223a:	bfa60613          	addi	a2,a2,-1030 # 1c5e30 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x202>
   e223e:	45c9                	c.li	a1,18
   e2240:	000e5517          	auipc	a0,0xe5
   e2244:	db850513          	addi	a0,a0,-584 # 1c6ff8 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x13ca>
   e2248:	e9a2                	c.sdsp	s0,208(sp)
   e224a:	e5a6                	c.sdsp	s1,200(sp)
   e224c:	e1ca                	c.sdsp	s2,192(sp)
   e224e:	fd4e                	c.sdsp	s3,184(sp)
   e2250:	f952                	c.sdsp	s4,176(sp)
   e2252:	f556                	c.sdsp	s5,168(sp)
   e2254:	f15a                	c.sdsp	s6,160(sp)
   e2256:	ed5e                	c.sdsp	s7,152(sp)
   e2258:	e962                	c.sdsp	s8,144(sp)
   e225a:	e566                	c.sdsp	s9,136(sp)
   e225c:	fcee                	c.sdsp	s11,120(sp)
   e225e:	9c2a30ef          	jal	ra,85420 <ggml_abort@plt>
   e2262:	000e5697          	auipc	a3,0xe5
   e2266:	d5668693          	addi	a3,a3,-682 # 1c6fb8 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x138a>
   e226a:	000e4617          	auipc	a2,0xe4
   e226e:	bc660613          	addi	a2,a2,-1082 # 1c5e30 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x202>
   e2272:	45c5                	c.li	a1,17
   e2274:	000e5517          	auipc	a0,0xe5
   e2278:	d8450513          	addi	a0,a0,-636 # 1c6ff8 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x13ca>
   e227c:	e9a2                	c.sdsp	s0,208(sp)
   e227e:	e5a6                	c.sdsp	s1,200(sp)
   e2280:	e1ca                	c.sdsp	s2,192(sp)
   e2282:	fd4e                	c.sdsp	s3,184(sp)
   e2284:	f952                	c.sdsp	s4,176(sp)
   e2286:	f556                	c.sdsp	s5,168(sp)
   e2288:	f15a                	c.sdsp	s6,160(sp)
   e228a:	ed5e                	c.sdsp	s7,152(sp)
   e228c:	e962                	c.sdsp	s8,144(sp)
   e228e:	e566                	c.sdsp	s9,136(sp)
   e2290:	fcee                	c.sdsp	s11,120(sp)
   e2292:	98ea30ef          	jal	ra,85420 <ggml_abort@plt>
