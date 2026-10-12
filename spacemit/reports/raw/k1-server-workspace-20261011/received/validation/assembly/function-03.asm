
/home/moyamryia/Projects/riscv-accl/lab/k1-combined-fixture-r5-20261011-122000-work/payload/C/lib/libggml-cpu.so.0.16.0:     file format elf64-littleriscv


Disassembly of section .text:

00000000000e2e2e <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl>:
   e2e2e:	d8010113          	addi	sp,sp,-640
   e2e32:	26813823          	sd	s0,624(sp)
   e2e36:	e03e                	c.sdsp	a5,0(sp)
   e2e38:	6dc0                	c.ld	s0,152(a1)
   e2e3a:	7ddc                	c.ld	a5,184(a1)
   e2e3c:	26913423          	sd	s1,616(sp)
   e2e40:	0014a497          	auipc	s1,0x14a
   e2e44:	7784b483          	ld	s1,1912(s1) # 22d5b8 <__stack_chk_guard@GLIBC_2.27>
   e2e48:	27213023          	sd	s2,608(sp)
   e2e4c:	25313c23          	sd	s3,600(sp)
   e2e50:	25513423          	sd	s5,584(sp)
   e2e54:	25613023          	sd	s6,576(sp)
   e2e58:	23913423          	sd	s9,552(sp)
   e2e5c:	26113c23          	sd	ra,632(sp)
   e2e60:	25413823          	sd	s4,592(sp)
   e2e64:	23713c23          	sd	s7,568(sp)
   e2e68:	23813823          	sd	s8,560(sp)
   e2e6c:	23a13023          	sd	s10,544(sp)
   e2e70:	21b13c23          	sd	s11,536(sp)
   e2e74:	f922                	c.sdsp	s0,176(sp)
   e2e76:	0004b303          	ld	t1,0(s1)
   e2e7a:	f71a                	c.sdsp	t1,424(sp)
   e2e7c:	4301                	c.li	t1,0
   e2e7e:	fd2a                	c.sdsp	a0,184(sp)
   e2e80:	e13a                	c.sdsp	a4,128(sp)
   e2e82:	f542                	c.sdsp	a6,168(sp)
   e2e84:	e93e                	c.sdsp	a5,144(sp)
   e2e86:	89c6                	c.mv	s3,a7
   e2e88:	0a05bc83          	ld	s9,160(a1)
   e2e8c:	0a85b903          	ld	s2,168(a1)
   e2e90:	0b05b883          	ld	a7,176(a1)
   e2e94:	8ab2                	c.mv	s5,a2
   e2e96:	8b36                	c.mv	s6,a3
   e2e98:	20040ae3          	beq	s0,zero,e38ac <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xa7e>
   e2e9c:	6c1c                	c.ld	a5,24(s0)
   e2e9e:	7c14                	c.ld	a3,56(s0)
   e2ea0:	6438                	c.ld	a4,72(s0)
   e2ea2:	e53e                	c.sdsp	a5,136(sp)
   e2ea4:	701c                	c.ld	a5,32(s0)
   e2ea6:	f5b6                	c.sdsp	a3,232(sp)
   e2ea8:	6034                	c.ld	a3,64(s0)
   e2eaa:	ed3e                	c.sdsp	a5,152(sp)
   e2eac:	01043d03          	ld	s10,16(s0)
   e2eb0:	7404                	c.ld	s1,40(s0)
   e2eb2:	781c                	c.ld	a5,48(s0)
   e2eb4:	f9b6                	c.sdsp	a3,240(sp)
   e2eb6:	f1ba                	c.sdsp	a4,224(sp)
   e2eb8:	1e0c81e3          	beq	s9,zero,e389a <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xa6c>
   e2ebc:	010cb703          	ld	a4,16(s9)
   e2ec0:	020cbd83          	ld	s11,32(s9)
   e2ec4:	030cbc03          	ld	s8,48(s9)
   e2ec8:	f03a                	c.sdsp	a4,32(sp)
   e2eca:	028cb703          	ld	a4,40(s9)
   e2ece:	ec3a                	c.sdsp	a4,24(sp)
   e2ed0:	038cb703          	ld	a4,56(s9)
   e2ed4:	e43a                	c.sdsp	a4,8(sp)
   e2ed6:	040cb703          	ld	a4,64(s9)
   e2eda:	e6ba                	c.sdsp	a4,328(sp)
   e2edc:	048cb703          	ld	a4,72(s9)
   e2ee0:	fe3a                	c.sdsp	a4,312(sp)
   e2ee2:	1a0903e3          	beq	s2,zero,e3888 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xa5a>
   e2ee6:	01093703          	ld	a4,16(s2)
   e2eea:	e4ba                	c.sdsp	a4,72(sp)
   e2eec:	02093703          	ld	a4,32(s2)
   e2ef0:	f83a                	c.sdsp	a4,48(sp)
   e2ef2:	02893703          	ld	a4,40(s2)
   e2ef6:	fc3a                	c.sdsp	a4,56(sp)
   e2ef8:	03093703          	ld	a4,48(s2)
   e2efc:	f43a                	c.sdsp	a4,40(sp)
   e2efe:	03893703          	ld	a4,56(s2)
   e2f02:	e83a                	c.sdsp	a4,16(sp)
   e2f04:	04093703          	ld	a4,64(s2)
   e2f08:	eaba                	c.sdsp	a4,336(sp)
   e2f0a:	04893703          	ld	a4,72(s2)
   e2f0e:	e2ba                	c.sdsp	a4,320(sp)
   e2f10:	6d98                	c.ld	a4,24(a1)
   e2f12:	6990                	c.ld	a2,16(a1)
   e2f14:	7194                	c.ld	a3,32(a1)
   e2f16:	e33a                	c.sdsp	a4,384(sp)
   e2f18:	7d98                	c.ld	a4,56(a1)
   e2f1a:	0305bb83          	ld	s7,48(a1)
   e2f1e:	61a0                	c.ld	s0,64(a1)
   e2f20:	faba                	c.sdsp	a4,368(sp)
   e2f22:	6726                	c.ldsp	a4,72(sp)
   e2f24:	0485ba03          	ld	s4,72(a1)
   e2f28:	24e61be3          	bne	a2,a4,e397e <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xb50>
   e2f2c:	672a                	c.ldsp	a4,136(sp)
   e2f2e:	2ae690e3          	bne	a3,a4,e39ce <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xba0>
   e2f32:	e8be                	c.sdsp	a5,80(sp)
   e2f34:	77ca                	c.ldsp	a5,176(sp)
   e2f36:	ecae                	c.sdsp	a1,88(sp)
   e2f38:	e0c6                	c.sdsp	a7,64(sp)
   e2f3a:	4388                	c.lw	a0,0(a5)
   e2f3c:	a64a10ef          	jal	ra,841a0 <ggml_type_size@plt>
   e2f40:	67c6                	c.ldsp	a5,80(sp)
   e2f42:	6886                	c.ldsp	a7,64(sp)
   e2f44:	65e6                	c.ldsp	a1,88(sp)
   e2f46:	1aa793e3          	bne	a5,a0,e38ec <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xabe>
   e2f4a:	000ca503          	lw	a0,0(s9)
   e2f4e:	e8ae                	c.sdsp	a1,80(sp)
   e2f50:	e0c6                	c.sdsp	a7,64(sp)
   e2f52:	a4ea10ef          	jal	ra,841a0 <ggml_type_size@plt>
   e2f56:	6886                	c.ldsp	a7,64(sp)
   e2f58:	65c6                	c.ldsp	a1,80(sp)
   e2f5a:	32ac12e3          	bne	s8,a0,e3a7e <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xc50>
   e2f5e:	00092503          	lw	a0,0(s2)
   e2f62:	e8ae                	c.sdsp	a1,80(sp)
   e2f64:	e0c6                	c.sdsp	a7,64(sp)
   e2f66:	a3aa10ef          	jal	ra,841a0 <ggml_type_size@plt>
   e2f6a:	77a2                	c.ldsp	a5,40(sp)
   e2f6c:	6886                	c.ldsp	a7,64(sp)
   e2f6e:	65c6                	c.ldsp	a1,80(sp)
   e2f70:	2aa79fe3          	bne	a5,a0,e3a2e <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xc00>
   e2f74:	7782                	c.ldsp	a5,32(sp)
   e2f76:	3ba794e3          	bne	a5,s10,e3b1e <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xcf0>
   e2f7a:	4791                	c.li	a5,4
   e2f7c:	34fb99e3          	bne	s7,a5,e3ace <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xca0>
   e2f80:	7756                	c.ldsp	a4,368(sp)
   e2f82:	478d                	c.li	a5,3
   e2f84:	48e7f8e3          	bgeu	a5,a4,e3c14 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xde6>
   e2f88:	42e46de3          	bltu	s0,a4,e3bc2 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xd94>
   e2f8c:	3e8a62e3          	bltu	s4,s0,e3b70 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xd42>
   e2f90:	676a                	c.ldsp	a4,152(sp)
   e2f92:	bfca                	c.fsdsp	fs2,504(sp)
   e2f94:	20813427          	fsd	fs0,520(sp)
   e2f98:	03b747b3          	div	a5,a4,s11
   e2f9c:	20913027          	fsd	fs1,512(sp)
   e2fa0:	bbce                	c.fsdsp	fs3,496(sp)
   e2fa2:	abde                	c.fsdsp	fs7,464(sp)
   e2fa4:	a7e2                	c.fsdsp	fs8,456(sp)
   e2fa6:	4df4                	c.lw	a3,92(a1)
   e2fa8:	f00007d3          	fmv.w.x	fa5,zero
   e2fac:	4da0                	c.lw	s0,88(a1)
   e2fae:	f0068953          	fmv.w.x	fs2,a3
   e2fb2:	fdbe                	c.sdsp	a5,248(sp)
   e2fb4:	49fc                	c.lw	a5,84(a1)
   e2fb6:	863e                	c.mv	a2,a5
   e2fb8:	d43e                	c.swsp	a5,40(sp)
   e2fba:	67e2                	c.ldsp	a5,24(sp)
   e2fbc:	02f4c7b3          	div	a5,s1,a5
   e2fc0:	e23e                	c.sdsp	a5,256(sp)
   e2fc2:	77c2                	c.ldsp	a5,48(sp)
   e2fc4:	02f747b3          	div	a5,a4,a5
   e2fc8:	e63e                	c.sdsp	a5,264(sp)
   e2fca:	77e2                	c.ldsp	a5,56(sp)
   e2fcc:	02f4c7b3          	div	a5,s1,a5
   e2fd0:	ea3e                	c.sdsp	a5,272(sp)
   e2fd2:	a0f927d3          	feq.s	a5,fs2,fa5
   e2fd6:	08078ae3          	beq	a5,zero,e386a <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xa3c>
   e2fda:	67ea                	c.ldsp	a5,152(sp)
   e2fdc:	e0ae                	c.sdsp	a1,64(sp)
   e2fde:	ec46                	c.sdsp	a7,24(sp)
   e2fe0:	d2178553          	fcvt.d.wu	fa0,a5
   e2fe4:	0007849b          	addiw	s1,a5,0
   e2fe8:	f0040453          	fmv.w.x	fs0,s0
   e2fec:	e25a10ef          	jal	ra,84e10 <log2@plt>
   e2ff0:	e91a30ef          	jal	ra,86e80 <floor@plt>
   e2ff4:	c21517d3          	fcvt.wu.d	a5,fa0,rtz
   e2ff8:	f00407d3          	fmv.w.x	fa5,s0
   e2ffc:	4685                	c.li	a3,1
   e2ffe:	00f697bb          	sllw	a5,a3,a5
   e3002:	d017f4d3          	fcvt.s.wu	fs1,a5
   e3006:	20f795d3          	fsgnjn.s	fa1,fa5,fa5
   e300a:	000e9717          	auipc	a4,0xe9
   e300e:	b9e72987          	flw	fs3,-1122(a4) # 1cbba8 <__func__.1+0x98>
   e3012:	f6be                	c.sdsp	a5,360(sp)
   e3014:	1895f5d3          	fdiv.s	fa1,fa1,fs1
   e3018:	21398553          	fsgnj.s	fa0,fs3,fs3
   e301c:	ac5a00ef          	jal	ra,83ae0 <powf@plt>
   e3020:	000e9797          	auipc	a5,0xe9
   e3024:	b387a787          	flw	fa5,-1224(a5) # 1cbb58 <__func__.1+0x48>
   e3028:	20a50bd3          	fsgnj.s	fs7,fa0,fa0
   e302c:	21398553          	fsgnj.s	fa0,fs3,fs3
   e3030:	10f475d3          	fmul.s	fa1,fs0,fa5
   e3034:	1895f5d3          	fdiv.s	fa1,fa1,fs1
   e3038:	aa9a00ef          	jal	ra,83ae0 <powf@plt>
   e303c:	000ca503          	lw	a0,0(s9)
   e3040:	20a50c53          	fsgnj.s	fs8,fa0,fa0
   e3044:	99ca40ef          	jal	ra,871e0 <ggml_get_type_traits_cpu@plt>
   e3048:	4908                	c.lw	a0,16(a0)
   e304a:	996a40ef          	jal	ra,871e0 <ggml_get_type_traits_cpu@plt>
   e304e:	87aa                	c.mv	a5,a0
   e3050:	6380                	c.ld	s0,0(a5)
   e3052:	000ca503          	lw	a0,0(s9)
   e3056:	ee22                	c.sdsp	s0,280(sp)
   e3058:	988a40ef          	jal	ra,871e0 <ggml_get_type_traits_cpu@plt>
   e305c:	87aa                	c.mv	a5,a0
   e305e:	679c                	c.ld	a5,8(a5)
   e3060:	00092503          	lw	a0,0(s2)
   e3064:	f83e                	c.sdsp	a5,48(sp)
   e3066:	a7aa20ef          	jal	ra,852e0 <ggml_get_type_traits@plt>
   e306a:	751c                	c.ld	a5,40(a0)
   e306c:	68e2                	c.ldsp	a7,24(sp)
   e306e:	6586                	c.ldsp	a1,64(sp)
   e3070:	fc3e                	c.sdsp	a5,56(sp)
   e3072:	0c0406e3          	beq	s0,zero,e393e <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xb10>
   e3076:	00092783          	lw	a5,0(s2)
   e307a:	7a079463          	bne	a5,zero,e3822 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x9f4>
   e307e:	77ea                	c.ldsp	a5,184(sp)
   e3080:	4394                	c.lw	a3,0(a5)
   e3082:	376adb63          	bge	s5,s6,e33f8 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x5ca>
   e3086:	652a                	c.ldsp	a0,136(sp)
   e3088:	7782                	c.ldsp	a5,32(sp)
   e308a:	415b0b3b          	subw	s6,s6,s5
   e308e:	0295073b          	mulw	a4,a0,s1
   e3092:	095b043b          	add.uw	s0,s6,s5
   e3096:	07c1                	c.addi	a5,16
   e3098:	b7d2                	c.fsdsp	fs4,488(sp)
   e309a:	b3d6                	c.fsdsp	fs5,480(sp)
   e309c:	afda                	c.fsdsp	fs6,472(sp)
   e309e:	f222                	c.sdsp	s0,288(sp)
   e30a0:	19712c27          	fsw	fs7,408(sp)
   e30a4:	00299413          	slli	s0,s3,0x2
   e30a8:	000e9617          	auipc	a2,0xe9
   e30ac:	a8c62a87          	flw	fs5,-1396(a2) # 1cbb34 <__func__.1+0x24>
   e30b0:	000e9617          	auipc	a2,0xe9
   e30b4:	af062a07          	flw	fs4,-1296(a2) # 1cbba0 <__func__.1+0x90>
   e30b8:	fa3a                	c.sdsp	a4,304(sp)
   e30ba:	6726                	c.ldsp	a4,72(sp)
   e30bc:	000f2617          	auipc	a2,0xf2
   e30c0:	98c61b07          	flh	fs6,-1652(a2) # 1d4a48 <_ZTSN4ggml3cpu17extra_buffer_typeE+0x90>
   e30c4:	20840bd3          	fsgnj.s	fs7,fs0,fs0
   e30c8:	20f727b3          	sh1add	a5,a4,a5
   e30cc:	02d787b3          	mul	a5,a5,a3
   e30d0:	86ba                	c.mv	a3,a4
   e30d2:	0706                	c.slli	a4,0x1
   e30d4:	00068b1b          	addiw	s6,a3,0
   e30d8:	feba                	c.sdsp	a4,376(sp)
   e30da:	00269713          	slli	a4,a3,0x2
   e30de:	f8ba                	c.sdsp	a4,112(sp)
   e30e0:	f622                	c.sdsp	s0,296(sp)
   e30e2:	0005041b          	addiw	s0,a0,0
   e30e6:	a3e6                	c.fsdsp	fs9,448(sp)
   e30e8:	bf6a                	c.fsdsp	fs10,440(sp)
   e30ea:	96be                	c.add	a3,a5
   e30ec:	03598733          	mul	a4,s3,s5
   e30f0:	078a                	c.slli	a5,0x2
   e30f2:	edbe                	c.sdsp	a5,216(sp)
   e30f4:	67ea                	c.ldsp	a5,152(sp)
   e30f6:	068a                	c.slli	a3,0x2
   e30f8:	bb6e                	c.fsdsp	fs11,432(sp)
   e30fa:	e8d6                	c.sdsp	s5,80(sp)
   e30fc:	e9a2                	c.sdsp	s0,208(sp)
   e30fe:	eb36                	c.sdsp	a3,400(sp)
   e3100:	8dda                	c.mv	s11,s6
   e3102:	02a787b3          	mul	a5,a5,a0
   e3106:	e72e                	c.sdsp	a1,392(sp)
   e3108:	e5be                	c.sdsp	a5,200(sp)
   e310a:	00270793          	addi	a5,a4,2
   e310e:	772a                	c.ldsp	a4,168(sp)
   e3110:	20e7c7b3          	sh2add	a5,a5,a4
   e3114:	f4be                	c.sdsp	a5,104(sp)
   e3116:	6742                	c.ldsp	a4,16(sp)
   e3118:	678a                	c.ldsp	a5,128(sp)
   e311a:	02f70733          	mul	a4,a4,a5
   e311e:	f2ba                	c.sdsp	a4,352(sp)
   e3120:	6722                	c.ldsp	a4,8(sp)
   e3122:	02f707b3          	mul	a5,a4,a5
   e3126:	eebe                	c.sdsp	a5,344(sp)
   e3128:	66c6                	c.ldsp	a3,80(sp)
   e312a:	67ae                	c.ldsp	a5,200(sp)
   e312c:	7652                	c.ldsp	a2,304(sp)
   e312e:	f00007d3          	fmv.w.x	fa5,zero
   e3132:	02f6c7b3          	div	a5,a3,a5
   e3136:	215a89d3          	fsgnj.s	fs3,fs5,fs5
   e313a:	0007871b          	addiw	a4,a5,0
   e313e:	02c787bb          	mulw	a5,a5,a2
   e3142:	666a                	c.ldsp	a2,152(sp)
   e3144:	ecba                	c.sdsp	a4,88(sp)
   e3146:	02c70733          	mul	a4,a4,a2
   e314a:	662a                	c.ldsp	a2,136(sp)
   e314c:	40f687bb          	subw	a5,a3,a5
   e3150:	02c70733          	mul	a4,a4,a2
   e3154:	40e68733          	sub	a4,a3,a4
   e3158:	02c746b3          	div	a3,a4,a2
   e315c:	674e                	c.ldsp	a4,208(sp)
   e315e:	02e6873b          	mulw	a4,a3,a4
   e3162:	f136                	c.sdsp	a3,160(sp)
   e3164:	2681                	c.addiw	a3,0
   e3166:	e0b6                	c.sdsp	a3,64(sp)
   e3168:	9f99                	c.subw	a5,a4
   e316a:	f0be                	c.sdsp	a5,96(sp)
   e316c:	a17797d3          	flt.s	a5,fa5,fs7
   e3170:	c385                	c.beqz	a5,e3190 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x362>
   e3172:	7736                	c.ldsp	a4,360(sp)
   e3174:	ec46                	c.sdsp	a7,24(sp)
   e3176:	54e6f463          	bgeu	a3,a4,e36be <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x890>
   e317a:	0016879b          	addiw	a5,a3,1
   e317e:	d017f5d3          	fcvt.s.wu	fa1,a5
   e3182:	19812507          	flw	fa0,408(sp)
   e3186:	95ba00ef          	jal	ra,83ae0 <powf@plt>
   e318a:	20a509d3          	fsgnj.s	fs3,fa0,fa0
   e318e:	68e2                	c.ldsp	a7,24(sp)
   e3190:	77ea                	c.ldsp	a5,184(sp)
   e3192:	666e                	c.ldsp	a2,216(sp)
   e3194:	00092703          	lw	a4,0(s2)
   e3198:	6b9c                	c.ld	a5,16(a5)
   e319a:	fcc6                	c.sdsp	a7,120(sp)
   e319c:	86be                	c.mv	a3,a5
   e319e:	00c68bb3          	add	s7,a3,a2
   e31a2:	76c6                	c.ldsp	a3,112(sp)
   e31a4:	e1be                	c.sdsp	a5,192(sp)
   e31a6:	4785                	c.li	a5,1
   e31a8:	00db8b33          	add	s6,s7,a3
   e31ac:	2176a6b3          	sh1add	a3,a3,s7
   e31b0:	ec36                	c.sdsp	a3,24(sp)
   e31b2:	4ef70f63          	beq	a4,a5,e36b0 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x882>
   e31b6:	7646                	c.ldsp	a2,112(sp)
   e31b8:	4581                	c.li	a1,0
   e31ba:	855e                	c.mv	a0,s7
   e31bc:	f74a30ef          	jal	ra,86930 <memset@plt>
   e31c0:	78e6                	c.ldsp	a7,120(sp)
   e31c2:	4a01                	c.li	s4,0
   e31c4:	02088e63          	beq	a7,zero,e3200 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x3d2>
   e31c8:	6686                	c.ldsp	a3,64(sp)
   e31ca:	0208b783          	ld	a5,32(a7)
   e31ce:	0288b703          	ld	a4,40(a7)
   e31d2:	0488b603          	ld	a2,72(a7)
   e31d6:	02f6e7b3          	rem	a5,a3,a5
   e31da:	66e6                	c.ldsp	a3,88(sp)
   e31dc:	0408b583          	ld	a1,64(a7)
   e31e0:	0f88ba03          	ld	s4,248(a7)
   e31e4:	02e6e733          	rem	a4,a3,a4
   e31e8:	0388b683          	ld	a3,56(a7)
   e31ec:	02c70733          	mul	a4,a4,a2
   e31f0:	7606                	c.ldsp	a2,96(sp)
   e31f2:	02b787b3          	mul	a5,a5,a1
   e31f6:	02d606b3          	mul	a3,a2,a3
   e31fa:	97ba                	c.add	a5,a4
   e31fc:	97b6                	c.add	a5,a3
   e31fe:	9a3e                	c.add	s4,a5
   e3200:	6766                	c.ldsp	a4,88(sp)
   e3202:	6792                	c.ldsp	a5,256(sp)
   e3204:	76ee                	c.ldsp	a3,248(sp)
   e3206:	7806                	c.ldsp	a6,96(sp)
   e3208:	02f74433          	div	s0,a4,a5
   e320c:	77ca                	c.ldsp	a5,176(sp)
   e320e:	7602                	c.ldsp	a2,32(sp)
   e3210:	65e2                	c.ldsp	a1,24(sp)
   e3212:	7fe8                	c.ld	a0,248(a5)
   e3214:	6786                	c.ldsp	a5,64(sp)
   e3216:	fcc6                	c.sdsp	a7,120(sp)
   e3218:	02d7cd33          	div	s10,a5,a3
   e321c:	66d2                	c.ldsp	a3,272(sp)
   e321e:	2401                	c.addiw	s0,0
   e3220:	02d749b3          	div	s3,a4,a3
   e3224:	66b2                	c.ldsp	a3,264(sp)
   e3226:	2d01                	c.addiw	s10,0
   e3228:	02d7c4b3          	div	s1,a5,a3
   e322c:	76ce                	c.ldsp	a3,240(sp)
   e322e:	2981                	c.addiw	s3,0
   e3230:	02d787b3          	mul	a5,a5,a3
   e3234:	768e                	c.ldsp	a3,224(sp)
   e3236:	2481                	c.addiw	s1,0
   e3238:	02d706b3          	mul	a3,a4,a3
   e323c:	772e                	c.ldsp	a4,232(sp)
   e323e:	03070733          	mul	a4,a4,a6
   e3242:	97b6                	c.add	a5,a3
   e3244:	97ba                	c.add	a5,a4
   e3246:	953e                	c.add	a0,a5
   e3248:	67f2                	c.ldsp	a5,280(sp)
   e324a:	9782                	c.jalr	a5
   e324c:	660a                	c.ldsp	a2,128(sp)
   e324e:	6782                	c.ldsp	a5,0(sp)
   e3250:	002026f3          	csrrs	a3,frm,zero
   e3254:	78e6                	c.ldsp	a7,120(sp)
   e3256:	54f65a63          	bge	a2,a5,e37aa <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x97c>
   e325a:	6796                	c.ldsp	a5,320(sp)
   e325c:	0c107c57          	vsetvli	s8,zero,e8,m2,ta,ma
   e3260:	65b6                	c.ldsp	a1,328(sp)
   e3262:	214a0d53          	fsgnj.s	fs10,fs4,fs4
   e3266:	02f98733          	mul	a4,s3,a5
   e326a:	77f2                	c.ldsp	a5,312(sp)
   e326c:	f0000dd3          	fmv.w.x	fs11,zero
   e3270:	8ada                	c.mv	s5,s6
   e3272:	001c199b          	slliw	s3,s8,0x1
   e3276:	8b62                	c.mv	s6,s8
   e3278:	02f40433          	mul	s0,s0,a5
   e327c:	7796                	c.ldsp	a5,352(sp)
   e327e:	973e                	c.add	a4,a5
   e3280:	67d6                	c.ldsp	a5,336(sp)
   e3282:	02bd0d33          	mul	s10,s10,a1
   e3286:	02f484b3          	mul	s1,s1,a5
   e328a:	67f6                	c.ldsp	a5,344(sp)
   e328c:	97a2                	c.add	a5,s0
   e328e:	9d3e                	c.add	s10,a5
   e3290:	8432                	c.mv	s0,a2
   e3292:	94ba                	c.add	s1,a4
   e3294:	1e0a0063          	beq	s4,zero,e3474 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x646>
   e3298:	214427b3          	sh1add	a5,s0,s4
   e329c:	0007d783          	lhu	a5,0(a5)
   e32a0:	f40787d3          	fmv.h.x	fa5,a5
   e32a4:	40278453          	fcvt.s.h	fs0,fa5
   e32a8:	11347453          	fmul.s	fs0,fs0,fs3
   e32ac:	a14427d3          	feq.s	a5,fs0,fs4
   e32b0:	2e079a63          	bne	a5,zero,e35a4 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x776>
   e32b4:	0f8cb683          	ld	a3,248(s9)
   e32b8:	67e2                	c.ldsp	a5,24(sp)
   e32ba:	5502                	c.lwsp	a0,32(sp)
   e32bc:	7342                	c.ldsp	t1,48(sp)
   e32be:	4885                	c.li	a7,1
   e32c0:	4801                	c.li	a6,0
   e32c2:	96ea                	c.add	a3,s10
   e32c4:	4701                	c.li	a4,0
   e32c6:	4601                	c.li	a2,0
   e32c8:	134c                	c.addi4spn	a1,sp,420
   e32ca:	9302                	c.jalr	t1
   e32cc:	f00007d3          	fmv.w.x	fa5,zero
   e32d0:	1a412507          	flw	fa0,420(sp)
   e32d4:	02812707          	flw	fa4,40(sp)
   e32d8:	a0f927d3          	feq.s	a5,fs2,fa5
   e32dc:	10a77553          	fmul.s	fa0,fa4,fa0
   e32e0:	e789                	c.bnez	a5,e32ea <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x4bc>
   e32e2:	c5fa00ef          	jal	ra,83f40 <tanhf@plt>
   e32e6:	11257553          	fmul.s	fa0,fa0,fs2
   e32ea:	00a47453          	fadd.s	fs0,fs0,fa0
   e32ee:	0f893503          	ld	a0,248(s2)
   e32f2:	00092703          	lw	a4,0(s2)
   e32f6:	4785                	c.li	a5,1
   e32f8:	00950c33          	add	s8,a0,s1
   e32fc:	1a812227          	fsw	fs0,420(sp)
   e3300:	16f70d63          	beq	a4,a5,e347a <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x64c>
   e3304:	a08d17d3          	flt.s	a5,fs10,fs0
   e3308:	2e079363          	bne	a5,zero,e35ee <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x7c0>
   e330c:	09a47553          	fsub.s	fa0,fs0,fs10
   e3310:	e91a10ef          	jal	ra,851a0 <expf@plt>
   e3314:	77e2                	c.ldsp	a5,56(sp)
   e3316:	002026f3          	csrrs	a3,frm,zero
   e331a:	20a504d3          	fsgnj.s	fs1,fa0,fa0
   e331e:	34078463          	beq	a5,zero,e3666 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x838>
   e3322:	6626                	c.ldsp	a2,72(sp)
   e3324:	8562                	c.mv	a0,s8
   e3326:	85d6                	c.mv	a1,s5
   e3328:	9782                	c.jalr	a5
   e332a:	002026f3          	csrrs	a3,frm,zero
   e332e:	215a8cd3          	fsgnj.s	fs9,fs5,fs5
   e3332:	13b05263          	bge	zero,s11,e3456 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x628>
   e3336:	4701                	c.li	a4,0
   e3338:	40ed87bb          	subw	a5,s11,a4
   e333c:	0d37f7d7          	vsetvli	a5,a5,e32,m8,ta,ma
   e3340:	21774633          	sh2add	a2,a4,s7
   e3344:	215745b3          	sh2add	a1,a4,s5
   e3348:	02066807          	vle32.v	v16,(a2)
   e334c:	0205e407          	vle32.v	v8,(a1)
   e3350:	9f3d                	c.addw	a4,a5
   e3352:	a304d457          	vfmadd.vf	v8,fs1,v16
   e3356:	02066427          	vse32.v	v8,(a2)
   e335a:	fdb74fe3          	blt	a4,s11,e3338 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x50a>
   e335e:	67c2                	c.ldsp	a5,16(sp)
   e3360:	0405                	c.addi	s0,1
   e3362:	49bcfdc3          	fmadd.s	fs11,fs9,fs11,fs1
   e3366:	94be                	c.add	s1,a5
   e3368:	67a2                	c.ldsp	a5,8(sp)
   e336a:	9d3e                	c.add	s10,a5
   e336c:	6782                	c.ldsp	a5,0(sp)
   e336e:	f28793e3          	bne	a5,s0,e3294 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x466>
   e3372:	00092703          	lw	a4,0(s2)
   e3376:	4785                	c.li	a5,1
   e3378:	78e6                	c.ldsp	a7,120(sp)
   e337a:	24f70363          	beq	a4,a5,e35c0 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x792>
   e337e:	67ca                	c.ldsp	a5,144(sp)
   e3380:	cb85                	c.beqz	a5,e33b0 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x582>
   e3382:	678a                	c.ldsp	a5,128(sp)
   e3384:	e795                	c.bnez	a5,e33b0 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x582>
   e3386:	67ca                	c.ldsp	a5,144(sp)
   e3388:	770a                	c.ldsp	a4,160(sp)
   e338a:	ec46                	c.sdsp	a7,24(sp)
   e338c:	7ffc                	c.ld	a5,248(a5)
   e338e:	20f747bb          	sh2add.uw	a5,a4,a5
   e3392:	0007a487          	flw	fs1,0(a5)
   e3396:	a09d17d3          	flt.s	a5,fs10,fs1
   e339a:	42079963          	bne	a5,zero,e37cc <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x99e>
   e339e:	09a4f553          	fsub.s	fa0,fs1,fs10
   e33a2:	dffa10ef          	jal	ra,851a0 <expf@plt>
   e33a6:	00adfdd3          	fadd.s	fs11,fs11,fa0
   e33aa:	002026f3          	csrrs	a3,frm,zero
   e33ae:	68e2                	c.ldsp	a7,24(sp)
   e33b0:	77aa                	c.ldsp	a5,168(sp)
   e33b2:	32078c63          	beq	a5,zero,e36ea <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x8bc>
   e33b6:	76a6                	c.ldsp	a3,104(sp)
   e33b8:	7746                	c.ldsp	a4,112(sp)
   e33ba:	8f5e                	c.mv	t5,s7
   e33bc:	ffa6ac27          	fsw	fs10,-8(a3)
   e33c0:	ffb6ae27          	fsw	fs11,-4(a3)
   e33c4:	0c3777d7          	vsetvli	a5,a4,e8,m8,ta,ma
   e33c8:	020f0407          	vle8.v	v8,(t5)
   e33cc:	8f1d                	c.sub	a4,a5
   e33ce:	9f3e                	c.add	t5,a5
   e33d0:	02068427          	vse8.v	v8,(a3)
   e33d4:	96be                	c.add	a3,a5
   e33d6:	f77d                	c.bnez	a4,e33c4 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x596>
   e33d8:	7726                	c.ldsp	a4,104(sp)
   e33da:	76b2                	c.ldsp	a3,296(sp)
   e33dc:	67c6                	c.ldsp	a5,80(sp)
   e33de:	9736                	c.add	a4,a3
   e33e0:	f4ba                	c.sdsp	a4,104(sp)
   e33e2:	7712                	c.ldsp	a4,288(sp)
   e33e4:	0785                	c.addi	a5,1
   e33e6:	e8be                	c.sdsp	a5,80(sp)
   e33e8:	d4f710e3          	bne	a4,a5,e3128 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x2fa>
   e33ec:	3a3e                	c.fldsp	fs4,488(sp)
   e33ee:	3a9e                	c.fldsp	fs5,480(sp)
   e33f0:	2b7e                	c.fldsp	fs6,472(sp)
   e33f2:	2c9e                	c.fldsp	fs9,448(sp)
   e33f4:	3d7a                	c.fldsp	fs10,440(sp)
   e33f6:	3dda                	c.fldsp	fs11,432(sp)
   e33f8:	0014a797          	auipc	a5,0x14a
   e33fc:	1c07b783          	ld	a5,448(a5) # 22d5b8 <__stack_chk_guard@GLIBC_2.27>
   e3400:	773a                	c.ldsp	a4,424(sp)
   e3402:	639c                	c.ld	a5,0(a5)
   e3404:	8fb9                	c.xor	a5,a4
   e3406:	4701                	c.li	a4,0
   e3408:	60079b63          	bne	a5,zero,e3a1e <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xbf0>
   e340c:	27813083          	ld	ra,632(sp)
   e3410:	27013403          	ld	s0,624(sp)
   e3414:	20813407          	fld	fs0,520(sp)
   e3418:	20013487          	fld	fs1,512(sp)
   e341c:	397e                	c.fldsp	fs2,504(sp)
   e341e:	39de                	c.fldsp	fs3,496(sp)
   e3420:	2bde                	c.fldsp	fs7,464(sp)
   e3422:	2c3e                	c.fldsp	fs8,456(sp)
   e3424:	26813483          	ld	s1,616(sp)
   e3428:	26013903          	ld	s2,608(sp)
   e342c:	25813983          	ld	s3,600(sp)
   e3430:	25013a03          	ld	s4,592(sp)
   e3434:	24813a83          	ld	s5,584(sp)
   e3438:	24013b03          	ld	s6,576(sp)
   e343c:	23813b83          	ld	s7,568(sp)
   e3440:	23013c03          	ld	s8,560(sp)
   e3444:	22813c83          	ld	s9,552(sp)
   e3448:	22013d03          	ld	s10,544(sp)
   e344c:	21813d83          	ld	s11,536(sp)
   e3450:	28010113          	addi	sp,sp,640
   e3454:	8082                	c.jr	ra
   e3456:	000e8797          	auipc	a5,0xe8
   e345a:	6de7ac87          	flw	fs9,1758(a5) # 1cbb34 <__func__.1+0x24>
   e345e:	67c2                	c.ldsp	a5,16(sp)
   e3460:	0405                	c.addi	s0,1
   e3462:	49bcfdc3          	fmadd.s	fs11,fs9,fs11,fs1
   e3466:	94be                	c.add	s1,a5
   e3468:	67a2                	c.ldsp	a5,8(sp)
   e346a:	9d3e                	c.add	s10,a5
   e346c:	6782                	c.ldsp	a5,0(sp)
   e346e:	e28793e3          	bne	a5,s0,e3294 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x466>
   e3472:	b701                	c.j	e3372 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x544>
   e3474:	f0000453          	fmv.w.x	fs0,zero
   e3478:	bd35                	c.j	e32b4 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x486>
   e347a:	a08d17d3          	flt.s	a5,fs10,fs0
   e347e:	1c078163          	beq	a5,zero,e3640 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x812>
   e3482:	088d7553          	fsub.s	fa0,fs10,fs0
   e3486:	d1ba10ef          	jal	ra,851a0 <expf@plt>
   e348a:	413007bb          	subw	a5,zero,s3
   e348e:	00fdf7b3          	and	a5,s11,a5
   e3492:	002026f3          	csrrs	a3,frm,zero
   e3496:	20a50cd3          	fsgnj.s	fs9,fa0,fa0
   e349a:	440577d3          	fcvt.h.s	fa5,fa0
   e349e:	30f05063          	bge	zero,a5,e379e <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x970>
   e34a2:	00199813          	slli	a6,s3,0x1
   e34a6:	0cab7057          	vsetvli	zero,s6,e16,m4,ta,ma
   e34aa:	8756                	c.mv	a4,s5
   e34ac:	001b1893          	slli	a7,s6,0x1
   e34b0:	4581                	c.li	a1,0
   e34b2:	02075207          	vle16.v	v4,(a4)
   e34b6:	9247d257          	vfmul.vf	v4,v4,fa5
   e34ba:	02075227          	vse16.v	v4,(a4)
   e34be:	00e88633          	add	a2,a7,a4
   e34c2:	02065207          	vle16.v	v4,(a2)
   e34c6:	9247d257          	vfmul.vf	v4,v4,fa5
   e34ca:	02065227          	vse16.v	v4,(a2)
   e34ce:	00b985bb          	addw	a1,s3,a1
   e34d2:	9742                	c.add	a4,a6
   e34d4:	fcf5cfe3          	blt	a1,a5,e34b2 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x684>
   e34d8:	0bb7dd63          	bge	a5,s11,e3592 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x764>
   e34dc:	863e                	c.mv	a2,a5
   e34de:	40cd873b          	subw	a4,s11,a2
   e34e2:	0ca77757          	vsetvli	a4,a4,e16,m4,ta,ma
   e34e6:	215625b3          	sh1add	a1,a2,s5
   e34ea:	0205d207          	vle16.v	v4,(a1)
   e34ee:	9e39                	c.addw	a2,a4
   e34f0:	9247d257          	vfmul.vf	v4,v4,fa5
   e34f4:	0205d227          	vse16.v	v4,(a1)
   e34f8:	ffb643e3          	blt	a2,s11,e34de <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x6b0>
   e34fc:	256b07d3          	fsgnj.h	fa5,fs6,fs6
   e3500:	215a84d3          	fsgnj.s	fs1,fs5,fs5
   e3504:	001b1893          	slli	a7,s6,0x1
   e3508:	04f05363          	bge	zero,a5,e354e <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x720>
   e350c:	0cab7057          	vsetvli	zero,s6,e16,m4,ta,ma
   e3510:	00199f93          	slli	t6,s3,0x1
   e3514:	8662                	c.mv	a2,s8
   e3516:	8756                	c.mv	a4,s5
   e3518:	4801                	c.li	a6,0
   e351a:	02065407          	vle16.v	v8,(a2)
   e351e:	02075207          	vle16.v	v4,(a4)
   e3522:	b287d257          	vfmacc.vf	v4,fa5,v8
   e3526:	02075227          	vse16.v	v4,(a4)
   e352a:	011705b3          	add	a1,a4,a7
   e352e:	00c88533          	add	a0,a7,a2
   e3532:	0205d207          	vle16.v	v4,(a1)
   e3536:	02055407          	vle16.v	v8,(a0)
   e353a:	b287d257          	vfmacc.vf	v4,fa5,v8
   e353e:	0205d227          	vse16.v	v4,(a1)
   e3542:	0138083b          	addw	a6,a6,s3
   e3546:	967e                	c.add	a2,t6
   e3548:	977e                	c.add	a4,t6
   e354a:	fcf848e3          	blt	a6,a5,e351a <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x6ec>
   e354e:	03b7d563          	bge	a5,s11,e3578 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x74a>
   e3552:	40fd873b          	subw	a4,s11,a5
   e3556:	0ca77757          	vsetvli	a4,a4,e16,m4,ta,ma
   e355a:	2157a633          	sh1add	a2,a5,s5
   e355e:	2187a5b3          	sh1add	a1,a5,s8
   e3562:	02065207          	vle16.v	v4,(a2)
   e3566:	0205d407          	vle16.v	v8,(a1)
   e356a:	9fb9                	c.addw	a5,a4
   e356c:	b287d257          	vfmacc.vf	v4,fa5,v8
   e3570:	02065227          	vse16.v	v4,(a2)
   e3574:	fdb7cfe3          	blt	a5,s11,e3552 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x724>
   e3578:	67c2                	c.ldsp	a5,16(sp)
   e357a:	0405                	c.addi	s0,1
   e357c:	49bcfdc3          	fmadd.s	fs11,fs9,fs11,fs1
   e3580:	94be                	c.add	s1,a5
   e3582:	67a2                	c.ldsp	a5,8(sp)
   e3584:	20840d53          	fsgnj.s	fs10,fs0,fs0
   e3588:	9d3e                	c.add	s10,a5
   e358a:	6782                	c.ldsp	a5,0(sp)
   e358c:	d08794e3          	bne	a5,s0,e3294 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x466>
   e3590:	b3cd                	c.j	e3372 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x544>
   e3592:	000f1717          	auipc	a4,0xf1
   e3596:	4b671787          	flh	fa5,1206(a4) # 1d4a48 <_ZTSN4ggml3cpu17extra_buffer_typeE+0x90>
   e359a:	000e8717          	auipc	a4,0xe8
   e359e:	59a72487          	flw	fs1,1434(a4) # 1cbb34 <__func__.1+0x24>
   e35a2:	b7bd                	c.j	e3510 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x6e2>
   e35a4:	67c2                	c.ldsp	a5,16(sp)
   e35a6:	0405                	c.addi	s0,1
   e35a8:	94be                	c.add	s1,a5
   e35aa:	67a2                	c.ldsp	a5,8(sp)
   e35ac:	9d3e                	c.add	s10,a5
   e35ae:	6782                	c.ldsp	a5,0(sp)
   e35b0:	cef414e3          	bne	s0,a5,e3298 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x46a>
   e35b4:	00092703          	lw	a4,0(s2)
   e35b8:	4785                	c.li	a5,1
   e35ba:	78e6                	c.ldsp	a7,120(sp)
   e35bc:	dcf711e3          	bne	a4,a5,e337e <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x550>
   e35c0:	67a6                	c.ldsp	a5,72(sp)
   e35c2:	daf05ee3          	bge	zero,a5,e337e <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x550>
   e35c6:	678e                	c.ldsp	a5,192(sp)
   e35c8:	675a                	c.ldsp	a4,400(sp)
   e35ca:	65a6                	c.ldsp	a1,72(sp)
   e35cc:	865e                	c.mv	a2,s7
   e35ce:	973e                	c.add	a4,a5
   e35d0:	0cf5f7d7          	vsetvli	a5,a1,e16,mf2,ta,ma
   e35d4:	02075107          	vle16.v	v2,(a4)
   e35d8:	8d9d                	c.sub	a1,a5
   e35da:	20e7a733          	sh1add	a4,a5,a4
   e35de:	4a2610d7          	vfwcvt.f.f.v	v1,v2
   e35e2:	020660a7          	vse32.v	v1,(a2)
   e35e6:	20c7c633          	sh2add	a2,a5,a2
   e35ea:	f1fd                	c.bnez	a1,e35d0 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x7a2>
   e35ec:	bb49                	c.j	e337e <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x550>
   e35ee:	088d7553          	fsub.s	fa0,fs10,fs0
   e35f2:	bafa10ef          	jal	ra,851a0 <expf@plt>
   e35f6:	002026f3          	csrrs	a3,frm,zero
   e35fa:	20a50cd3          	fsgnj.s	fs9,fa0,fa0
   e35fe:	17b05563          	bge	zero,s11,e3768 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x93a>
   e3602:	4701                	c.li	a4,0
   e3604:	40ed87bb          	subw	a5,s11,a4
   e3608:	0d37f7d7          	vsetvli	a5,a5,e32,m8,ta,ma
   e360c:	21774633          	sh2add	a2,a4,s7
   e3610:	02066407          	vle32.v	v8,(a2)
   e3614:	9f3d                	c.addw	a4,a5
   e3616:	928cd457          	vfmul.vf	v8,v8,fs9
   e361a:	02066427          	vse32.v	v8,(a2)
   e361e:	ffb743e3          	blt	a4,s11,e3604 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x7d6>
   e3622:	77e2                	c.ldsp	a5,56(sp)
   e3624:	cfc5                	c.beqz	a5,e36dc <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x8ae>
   e3626:	6626                	c.ldsp	a2,72(sp)
   e3628:	8562                	c.mv	a0,s8
   e362a:	85d6                	c.mv	a1,s5
   e362c:	9782                	c.jalr	a5
   e362e:	002026f3          	csrrs	a3,frm,zero
   e3632:	20840d53          	fsgnj.s	fs10,fs0,fs0
   e3636:	000e8797          	auipc	a5,0xe8
   e363a:	4fe7a487          	flw	fs1,1278(a5) # 1cbb34 <__func__.1+0x24>
   e363e:	b9e5                	c.j	e3336 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x508>
   e3640:	09a47553          	fsub.s	fa0,fs0,fs10
   e3644:	215a8cd3          	fsgnj.s	fs9,fs5,fs5
   e3648:	21ad0453          	fsgnj.s	fs0,fs10,fs10
   e364c:	b55a10ef          	jal	ra,851a0 <expf@plt>
   e3650:	413007bb          	subw	a5,zero,s3
   e3654:	002026f3          	csrrs	a3,frm,zero
   e3658:	20a504d3          	fsgnj.s	fs1,fa0,fa0
   e365c:	440577d3          	fcvt.h.s	fa5,fa0
   e3660:	00fdf7b3          	and	a5,s11,a5
   e3664:	b545                	c.j	e3504 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x6d6>
   e3666:	dfb058e3          	bge	zero,s11,e3456 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x628>
   e366a:	000e8797          	auipc	a5,0xe8
   e366e:	4ca7ac87          	flw	fs9,1226(a5) # 1cbb34 <__func__.1+0x24>
   e3672:	4701                	c.li	a4,0
   e3674:	40ed87bb          	subw	a5,s11,a4
   e3678:	0d37f7d7          	vsetvli	a5,a5,e32,m8,ta,ma
   e367c:	21774633          	sh2add	a2,a4,s7
   e3680:	218745b3          	sh2add	a1,a4,s8
   e3684:	02066807          	vle32.v	v16,(a2)
   e3688:	0205e407          	vle32.v	v8,(a1)
   e368c:	9f3d                	c.addw	a4,a5
   e368e:	a304d457          	vfmadd.vf	v8,fs1,v16
   e3692:	02066427          	vse32.v	v8,(a2)
   e3696:	fdb74fe3          	blt	a4,s11,e3674 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x846>
   e369a:	67c2                	c.ldsp	a5,16(sp)
   e369c:	0405                	c.addi	s0,1
   e369e:	49bcfdc3          	fmadd.s	fs11,fs9,fs11,fs1
   e36a2:	94be                	c.add	s1,a5
   e36a4:	67a2                	c.ldsp	a5,8(sp)
   e36a6:	9d3e                	c.add	s10,a5
   e36a8:	6782                	c.ldsp	a5,0(sp)
   e36aa:	be8795e3          	bne	a5,s0,e3294 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x466>
   e36ae:	b1d1                	c.j	e3372 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x544>
   e36b0:	7676                	c.ldsp	a2,376(sp)
   e36b2:	4581                	c.li	a1,0
   e36b4:	855a                	c.mv	a0,s6
   e36b6:	a7aa30ef          	jal	ra,86930 <memset@plt>
   e36ba:	78e6                	c.ldsp	a7,120(sp)
   e36bc:	b619                	c.j	e31c2 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x394>
   e36be:	40e687bb          	subw	a5,a3,a4
   e36c2:	0017979b          	slliw	a5,a5,0x1
   e36c6:	2785                	c.addiw	a5,1
   e36c8:	d017f5d3          	fcvt.s.wu	fa1,a5
   e36cc:	218c0553          	fsgnj.s	fa0,fs8,fs8
   e36d0:	c10a00ef          	jal	ra,83ae0 <powf@plt>
   e36d4:	20a509d3          	fsgnj.s	fs3,fa0,fa0
   e36d8:	68e2                	c.ldsp	a7,24(sp)
   e36da:	bc5d                	c.j	e3190 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x362>
   e36dc:	20840d53          	fsgnj.s	fs10,fs0,fs0
   e36e0:	000e8797          	auipc	a5,0xe8
   e36e4:	4547a487          	flw	fs1,1108(a5) # 1cbb34 <__func__.1+0x24>
   e36e8:	b769                	c.j	e3672 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x844>
   e36ea:	f00007d3          	fmv.w.x	fa5,zero
   e36ee:	a0fda7d3          	feq.s	a5,fs11,fa5
   e36f2:	ebcd                	c.bnez	a5,e37a4 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x976>
   e36f4:	000e8797          	auipc	a5,0xe8
   e36f8:	4407a787          	flw	fa5,1088(a5) # 1cbb34 <__func__.1+0x24>
   e36fc:	19b7f7d3          	fdiv.s	fa5,fa5,fs11
   e3700:	00269073          	csrrw	zero,frm,a3
   e3704:	03b05263          	bge	zero,s11,e3728 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x8fa>
   e3708:	4701                	c.li	a4,0
   e370a:	40ed87bb          	subw	a5,s11,a4
   e370e:	217746b3          	sh2add	a3,a4,s7
   e3712:	0d37f7d7          	vsetvli	a5,a5,e32,m8,ta,ma
   e3716:	0206e407          	vle32.v	v8,(a3)
   e371a:	9f3d                	c.addw	a4,a5
   e371c:	9287d457          	vfmul.vf	v8,v8,fa5
   e3720:	0206e427          	vse32.v	v8,(a3)
   e3724:	ffb743e3          	blt	a4,s11,e370a <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x8dc>
   e3728:	672a                	c.ldsp	a4,136(sp)
   e372a:	67e6                	c.ldsp	a5,88(sp)
   e372c:	669a                	c.ldsp	a3,384(sp)
   e372e:	7606                	c.ldsp	a2,96(sp)
   e3730:	02e787b3          	mul	a5,a5,a4
   e3734:	75d6                	c.ldsp	a1,368(sp)
   e3736:	673a                	c.ldsp	a4,392(sp)
   e3738:	8f5e                	c.mv	t5,s7
   e373a:	7f78                	c.ld	a4,248(a4)
   e373c:	02d787b3          	mul	a5,a5,a3
   e3740:	02d60633          	mul	a2,a2,a3
   e3744:	6686                	c.ldsp	a3,64(sp)
   e3746:	97b6                	c.add	a5,a3
   e3748:	86ae                	c.mv	a3,a1
   e374a:	97b2                	c.add	a5,a2
   e374c:	02b787b3          	mul	a5,a5,a1
   e3750:	97ba                	c.add	a5,a4
   e3752:	0c36f757          	vsetvli	a4,a3,e8,m8,ta,ma
   e3756:	020f0407          	vle8.v	v8,(t5)
   e375a:	8e99                	c.sub	a3,a4
   e375c:	9f3a                	c.add	t5,a4
   e375e:	02078427          	vse8.v	v8,(a5)
   e3762:	97ba                	c.add	a5,a4
   e3764:	f6fd                	c.bnez	a3,e3752 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x924>
   e3766:	b98d                	c.j	e33d8 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x5aa>
   e3768:	77e2                	c.ldsp	a5,56(sp)
   e376a:	cb89                	c.beqz	a5,e377c <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x94e>
   e376c:	6626                	c.ldsp	a2,72(sp)
   e376e:	18d12e23          	sw	a3,412(sp)
   e3772:	8562                	c.mv	a0,s8
   e3774:	85d6                	c.mv	a1,s5
   e3776:	9782                	c.jalr	a5
   e3778:	19c12683          	lw	a3,412(sp)
   e377c:	000e8797          	auipc	a5,0xe8
   e3780:	3b87a487          	flw	fs1,952(a5) # 1cbb34 <__func__.1+0x24>
   e3784:	67c2                	c.ldsp	a5,16(sp)
   e3786:	0405                	c.addi	s0,1
   e3788:	49bcfdc3          	fmadd.s	fs11,fs9,fs11,fs1
   e378c:	94be                	c.add	s1,a5
   e378e:	67a2                	c.ldsp	a5,8(sp)
   e3790:	20840d53          	fsgnj.s	fs10,fs0,fs0
   e3794:	9d3e                	c.add	s10,a5
   e3796:	6782                	c.ldsp	a5,0(sp)
   e3798:	ae879ee3          	bne	a5,s0,e3294 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x466>
   e379c:	bed9                	c.j	e3372 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x544>
   e379e:	d3b7cfe3          	blt	a5,s11,e34dc <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x6ae>
   e37a2:	bfe9                	c.j	e377c <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x94e>
   e37a4:	f00007d3          	fmv.w.x	fa5,zero
   e37a8:	bfa1                	c.j	e3700 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x8d2>
   e37aa:	00092703          	lw	a4,0(s2)
   e37ae:	4785                	c.li	a5,1
   e37b0:	10f70863          	beq	a4,a5,e38c0 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xa92>
   e37b4:	67ca                	c.ldsp	a5,144(sp)
   e37b6:	c391                	c.beqz	a5,e37ba <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x98c>
   e37b8:	c269                	c.beqz	a2,e387a <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xa4c>
   e37ba:	77aa                	c.ldsp	a5,168(sp)
   e37bc:	d7e5                	c.beqz	a5,e37a4 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x976>
   e37be:	000e8797          	auipc	a5,0xe8
   e37c2:	3e27ad07          	flw	fs10,994(a5) # 1cbba0 <__func__.1+0x90>
   e37c6:	f0000dd3          	fmv.w.x	fs11,zero
   e37ca:	b6f5                	c.j	e33b6 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x588>
   e37cc:	089d7553          	fsub.s	fa0,fs10,fs1
   e37d0:	9d1a10ef          	jal	ra,851a0 <expf@plt>
   e37d4:	68e2                	c.ldsp	a7,24(sp)
   e37d6:	4701                	c.li	a4,0
   e37d8:	0fb05e63          	bge	zero,s11,e38d4 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xaa6>
   e37dc:	40ed87bb          	subw	a5,s11,a4
   e37e0:	0d37f7d7          	vsetvli	a5,a5,e32,m8,ta,ma
   e37e4:	217746b3          	sh2add	a3,a4,s7
   e37e8:	0206e407          	vle32.v	v8,(a3)
   e37ec:	9f3d                	c.addw	a4,a5
   e37ee:	92855457          	vfmul.vf	v8,v8,fa0
   e37f2:	0206e427          	vse32.v	v8,(a3)
   e37f6:	ffb743e3          	blt	a4,s11,e37dc <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x9ae>
   e37fa:	000e8797          	auipc	a5,0xe8
   e37fe:	33a7a707          	flw	fa4,826(a5) # 1cbb34 <__func__.1+0x24>
   e3802:	77aa                	c.ldsp	a5,168(sp)
   e3804:	20948d53          	fsgnj.s	fs10,fs1,fs1
   e3808:	71b57dc3          	fmadd.s	fs11,fa0,fs11,fa4
   e380c:	ba0795e3          	bne	a5,zero,e33b6 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x588>
   e3810:	f00007d3          	fmv.w.x	fa5,zero
   e3814:	a0fda7d3          	feq.s	a5,fs11,fa5
   e3818:	ee0798e3          	bne	a5,zero,e3708 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x8da>
   e381c:	19b777d3          	fdiv.s	fa5,fa4,fs11
   e3820:	b5e5                	c.j	e3708 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x8da>
   e3822:	77e2                	c.ldsp	a5,56(sp)
   e3824:	84079de3          	bne	a5,zero,e307e <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x250>
   e3828:	0014a797          	auipc	a5,0x14a
   e382c:	d907b783          	ld	a5,-624(a5) # 22d5b8 <__stack_chk_guard@GLIBC_2.27>
   e3830:	773a                	c.ldsp	a4,424(sp)
   e3832:	639c                	c.ld	a5,0(a5)
   e3834:	8fb9                	c.xor	a5,a4
   e3836:	4701                	c.li	a4,0
   e3838:	b7d2                	c.fsdsp	fs4,488(sp)
   e383a:	b3d6                	c.fsdsp	fs5,480(sp)
   e383c:	afda                	c.fsdsp	fs6,472(sp)
   e383e:	a3e6                	c.fsdsp	fs9,448(sp)
   e3840:	bf6a                	c.fsdsp	fs10,440(sp)
   e3842:	bb6e                	c.fsdsp	fs11,432(sp)
   e3844:	1e079363          	bne	a5,zero,e3a2a <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xbfc>
   e3848:	6589                	c.lui	a1,0x2
   e384a:	16958593          	addi	a1,a1,361 # 2169 <_ZSt15__once_callable+0x20a1>
   e384e:	000e4697          	auipc	a3,0xe4
   e3852:	9da68693          	addi	a3,a3,-1574 # 1c7228 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x15fa>
   e3856:	000e2617          	auipc	a2,0xe2
   e385a:	5da60613          	addi	a2,a2,1498 # 1c5e30 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x202>
   e385e:	000e3517          	auipc	a0,0xe3
   e3862:	5ea50513          	addi	a0,a0,1514 # 1c6e48 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x121a>
   e3866:	bbba10ef          	jal	ra,85420 <ggml_abort@plt>
   e386a:	f00607d3          	fmv.w.x	fa5,a2
   e386e:	1927f7d3          	fdiv.s	fa5,fa5,fs2
   e3872:	02f12427          	fsw	fa5,40(sp)
   e3876:	f64ff06f          	jal	zero,e2fda <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x1ac>
   e387a:	000e8797          	auipc	a5,0xe8
   e387e:	3267ad07          	flw	fs10,806(a5) # 1cbba0 <__func__.1+0x90>
   e3882:	f0000dd3          	fmv.w.x	fs11,zero
   e3886:	b601                	c.j	e3386 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x558>
   e3888:	ea82                	c.sdsp	zero,336(sp)
   e388a:	e802                	c.sdsp	zero,16(sp)
   e388c:	f402                	c.sdsp	zero,40(sp)
   e388e:	fc02                	c.sdsp	zero,56(sp)
   e3890:	f802                	c.sdsp	zero,48(sp)
   e3892:	e482                	c.sdsp	zero,72(sp)
   e3894:	e282                	c.sdsp	zero,320(sp)
   e3896:	e7aff06f          	jal	zero,e2f10 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xe2>
   e389a:	e682                	c.sdsp	zero,328(sp)
   e389c:	e402                	c.sdsp	zero,8(sp)
   e389e:	4c01                	c.li	s8,0
   e38a0:	ec02                	c.sdsp	zero,24(sp)
   e38a2:	4d81                	c.li	s11,0
   e38a4:	f002                	c.sdsp	zero,32(sp)
   e38a6:	fe02                	c.sdsp	zero,312(sp)
   e38a8:	e3aff06f          	jal	zero,e2ee2 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xb4>
   e38ac:	f982                	c.sdsp	zero,240(sp)
   e38ae:	f582                	c.sdsp	zero,232(sp)
   e38b0:	4781                	c.li	a5,0
   e38b2:	4481                	c.li	s1,0
   e38b4:	ed02                	c.sdsp	zero,152(sp)
   e38b6:	e502                	c.sdsp	zero,136(sp)
   e38b8:	4d01                	c.li	s10,0
   e38ba:	f182                	c.sdsp	zero,224(sp)
   e38bc:	dfcff06f          	jal	zero,e2eb8 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x8a>
   e38c0:	67a6                	c.ldsp	a5,72(sp)
   e38c2:	eef059e3          	bge	zero,a5,e37b4 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x986>
   e38c6:	000e8797          	auipc	a5,0xe8
   e38ca:	2da7ad07          	flw	fs10,730(a5) # 1cbba0 <__func__.1+0x90>
   e38ce:	f0000dd3          	fmv.w.x	fs11,zero
   e38d2:	b9d5                	c.j	e35c6 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x798>
   e38d4:	000e8797          	auipc	a5,0xe8
   e38d8:	2607a787          	flw	fa5,608(a5) # 1cbb34 <__func__.1+0x24>
   e38dc:	77aa                	c.ldsp	a5,168(sp)
   e38de:	20948d53          	fsgnj.s	fs10,fs1,fs1
   e38e2:	79b57dc3          	fmadd.s	fs11,fa0,fs11,fa5
   e38e6:	ac0798e3          	bne	a5,zero,e33b6 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x588>
   e38ea:	bd3d                	c.j	e3728 <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0x8fa>
   e38ec:	0014a797          	auipc	a5,0x14a
   e38f0:	ccc7b783          	ld	a5,-820(a5) # 22d5b8 <__stack_chk_guard@GLIBC_2.27>
   e38f4:	773a                	c.ldsp	a4,424(sp)
   e38f6:	639c                	c.ld	a5,0(a5)
   e38f8:	8fb9                	c.xor	a5,a4
   e38fa:	4701                	c.li	a4,0
   e38fc:	20813427          	fsd	fs0,520(sp)
   e3900:	20913027          	fsd	fs1,512(sp)
   e3904:	bfca                	c.fsdsp	fs2,504(sp)
   e3906:	bbce                	c.fsdsp	fs3,496(sp)
   e3908:	b7d2                	c.fsdsp	fs4,488(sp)
   e390a:	b3d6                	c.fsdsp	fs5,480(sp)
   e390c:	afda                	c.fsdsp	fs6,472(sp)
   e390e:	abde                	c.fsdsp	fs7,464(sp)
   e3910:	a7e2                	c.fsdsp	fs8,456(sp)
   e3912:	a3e6                	c.fsdsp	fs9,448(sp)
   e3914:	bf6a                	c.fsdsp	fs10,440(sp)
   e3916:	bb6e                	c.fsdsp	fs11,432(sp)
   e3918:	10079963          	bne	a5,zero,e3a2a <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xbfc>
   e391c:	6589                	c.lui	a1,0x2
   e391e:	13858593          	addi	a1,a1,312 # 2138 <_ZSt15__once_callable+0x2070>
   e3922:	000e4697          	auipc	a3,0xe4
   e3926:	86668693          	addi	a3,a3,-1946 # 1c7188 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x155a>
   e392a:	000e2617          	auipc	a2,0xe2
   e392e:	50660613          	addi	a2,a2,1286 # 1c5e30 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x202>
   e3932:	000e3517          	auipc	a0,0xe3
   e3936:	51650513          	addi	a0,a0,1302 # 1c6e48 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x121a>
   e393a:	ae7a10ef          	jal	ra,85420 <ggml_abort@plt>
   e393e:	0014a797          	auipc	a5,0x14a
   e3942:	c7a7b783          	ld	a5,-902(a5) # 22d5b8 <__stack_chk_guard@GLIBC_2.27>
   e3946:	773a                	c.ldsp	a4,424(sp)
   e3948:	639c                	c.ld	a5,0(a5)
   e394a:	8fb9                	c.xor	a5,a4
   e394c:	4701                	c.li	a4,0
   e394e:	b7d2                	c.fsdsp	fs4,488(sp)
   e3950:	b3d6                	c.fsdsp	fs5,480(sp)
   e3952:	afda                	c.fsdsp	fs6,472(sp)
   e3954:	a3e6                	c.fsdsp	fs9,448(sp)
   e3956:	bf6a                	c.fsdsp	fs10,440(sp)
   e3958:	bb6e                	c.fsdsp	fs11,432(sp)
   e395a:	ebe1                	c.bnez	a5,e3a2a <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xbfc>
   e395c:	6589                	c.lui	a1,0x2
   e395e:	16858593          	addi	a1,a1,360 # 2168 <_ZSt15__once_callable+0x20a0>
   e3962:	000e4697          	auipc	a3,0xe4
   e3966:	89668693          	addi	a3,a3,-1898 # 1c71f8 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x15ca>
   e396a:	000e2617          	auipc	a2,0xe2
   e396e:	4c660613          	addi	a2,a2,1222 # 1c5e30 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x202>
   e3972:	000e3517          	auipc	a0,0xe3
   e3976:	4d650513          	addi	a0,a0,1238 # 1c6e48 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x121a>
   e397a:	aa7a10ef          	jal	ra,85420 <ggml_abort@plt>
   e397e:	0014a797          	auipc	a5,0x14a
   e3982:	c3a7b783          	ld	a5,-966(a5) # 22d5b8 <__stack_chk_guard@GLIBC_2.27>
   e3986:	773a                	c.ldsp	a4,424(sp)
   e3988:	639c                	c.ld	a5,0(a5)
   e398a:	8fb9                	c.xor	a5,a4
   e398c:	4701                	c.li	a4,0
   e398e:	20813427          	fsd	fs0,520(sp)
   e3992:	20913027          	fsd	fs1,512(sp)
   e3996:	bfca                	c.fsdsp	fs2,504(sp)
   e3998:	bbce                	c.fsdsp	fs3,496(sp)
   e399a:	b7d2                	c.fsdsp	fs4,488(sp)
   e399c:	b3d6                	c.fsdsp	fs5,480(sp)
   e399e:	afda                	c.fsdsp	fs6,472(sp)
   e39a0:	abde                	c.fsdsp	fs7,464(sp)
   e39a2:	a7e2                	c.fsdsp	fs8,456(sp)
   e39a4:	a3e6                	c.fsdsp	fs9,448(sp)
   e39a6:	bf6a                	c.fsdsp	fs10,440(sp)
   e39a8:	bb6e                	c.fsdsp	fs11,432(sp)
   e39aa:	e3c1                	c.bnez	a5,e3a2a <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xbfc>
   e39ac:	6589                	c.lui	a1,0x2
   e39ae:	13458593          	addi	a1,a1,308 # 2134 <_ZSt15__once_callable+0x206c>
   e39b2:	000e3697          	auipc	a3,0xe3
   e39b6:	7b668693          	addi	a3,a3,1974 # 1c7168 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x153a>
   e39ba:	000e2617          	auipc	a2,0xe2
   e39be:	47660613          	addi	a2,a2,1142 # 1c5e30 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x202>
   e39c2:	000e3517          	auipc	a0,0xe3
   e39c6:	48650513          	addi	a0,a0,1158 # 1c6e48 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x121a>
   e39ca:	a57a10ef          	jal	ra,85420 <ggml_abort@plt>
   e39ce:	0014a797          	auipc	a5,0x14a
   e39d2:	bea7b783          	ld	a5,-1046(a5) # 22d5b8 <__stack_chk_guard@GLIBC_2.27>
   e39d6:	773a                	c.ldsp	a4,424(sp)
   e39d8:	639c                	c.ld	a5,0(a5)
   e39da:	8fb9                	c.xor	a5,a4
   e39dc:	4701                	c.li	a4,0
   e39de:	20813427          	fsd	fs0,520(sp)
   e39e2:	20913027          	fsd	fs1,512(sp)
   e39e6:	bfca                	c.fsdsp	fs2,504(sp)
   e39e8:	bbce                	c.fsdsp	fs3,496(sp)
   e39ea:	b7d2                	c.fsdsp	fs4,488(sp)
   e39ec:	b3d6                	c.fsdsp	fs5,480(sp)
   e39ee:	afda                	c.fsdsp	fs6,472(sp)
   e39f0:	abde                	c.fsdsp	fs7,464(sp)
   e39f2:	a7e2                	c.fsdsp	fs8,456(sp)
   e39f4:	a3e6                	c.fsdsp	fs9,448(sp)
   e39f6:	bf6a                	c.fsdsp	fs10,440(sp)
   e39f8:	bb6e                	c.fsdsp	fs11,432(sp)
   e39fa:	eb85                	c.bnez	a5,e3a2a <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xbfc>
   e39fc:	6589                	c.lui	a1,0x2
   e39fe:	13558593          	addi	a1,a1,309 # 2135 <_ZSt15__once_callable+0x206d>
   e3a02:	000e3697          	auipc	a3,0xe3
   e3a06:	77668693          	addi	a3,a3,1910 # 1c7178 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x154a>
   e3a0a:	000e2617          	auipc	a2,0xe2
   e3a0e:	42660613          	addi	a2,a2,1062 # 1c5e30 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x202>
   e3a12:	000e3517          	auipc	a0,0xe3
   e3a16:	43650513          	addi	a0,a0,1078 # 1c6e48 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x121a>
   e3a1a:	a07a10ef          	jal	ra,85420 <ggml_abort@plt>
   e3a1e:	b7d2                	c.fsdsp	fs4,488(sp)
   e3a20:	b3d6                	c.fsdsp	fs5,480(sp)
   e3a22:	afda                	c.fsdsp	fs6,472(sp)
   e3a24:	a3e6                	c.fsdsp	fs9,448(sp)
   e3a26:	bf6a                	c.fsdsp	fs10,440(sp)
   e3a28:	bb6e                	c.fsdsp	fs11,432(sp)
   e3a2a:	907a30ef          	jal	ra,87330 <__stack_chk_fail@plt>
   e3a2e:	0014a797          	auipc	a5,0x14a
   e3a32:	b8a7b783          	ld	a5,-1142(a5) # 22d5b8 <__stack_chk_guard@GLIBC_2.27>
   e3a36:	773a                	c.ldsp	a4,424(sp)
   e3a38:	639c                	c.ld	a5,0(a5)
   e3a3a:	8fb9                	c.xor	a5,a4
   e3a3c:	4701                	c.li	a4,0
   e3a3e:	20813427          	fsd	fs0,520(sp)
   e3a42:	20913027          	fsd	fs1,512(sp)
   e3a46:	bfca                	c.fsdsp	fs2,504(sp)
   e3a48:	bbce                	c.fsdsp	fs3,496(sp)
   e3a4a:	b7d2                	c.fsdsp	fs4,488(sp)
   e3a4c:	b3d6                	c.fsdsp	fs5,480(sp)
   e3a4e:	afda                	c.fsdsp	fs6,472(sp)
   e3a50:	abde                	c.fsdsp	fs7,464(sp)
   e3a52:	a7e2                	c.fsdsp	fs8,456(sp)
   e3a54:	a3e6                	c.fsdsp	fs9,448(sp)
   e3a56:	bf6a                	c.fsdsp	fs10,440(sp)
   e3a58:	bb6e                	c.fsdsp	fs11,432(sp)
   e3a5a:	fbe1                	c.bnez	a5,e3a2a <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xbfc>
   e3a5c:	6589                	c.lui	a1,0x2
   e3a5e:	13a58593          	addi	a1,a1,314 # 213a <_ZSt15__once_callable+0x2072>
   e3a62:	000e3697          	auipc	a3,0xe3
   e3a66:	76668693          	addi	a3,a3,1894 # 1c71c8 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x159a>
   e3a6a:	000e2617          	auipc	a2,0xe2
   e3a6e:	3c660613          	addi	a2,a2,966 # 1c5e30 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x202>
   e3a72:	000e3517          	auipc	a0,0xe3
   e3a76:	3d650513          	addi	a0,a0,982 # 1c6e48 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x121a>
   e3a7a:	9a7a10ef          	jal	ra,85420 <ggml_abort@plt>
   e3a7e:	0014a797          	auipc	a5,0x14a
   e3a82:	b3a7b783          	ld	a5,-1222(a5) # 22d5b8 <__stack_chk_guard@GLIBC_2.27>
   e3a86:	773a                	c.ldsp	a4,424(sp)
   e3a88:	639c                	c.ld	a5,0(a5)
   e3a8a:	8fb9                	c.xor	a5,a4
   e3a8c:	4701                	c.li	a4,0
   e3a8e:	20813427          	fsd	fs0,520(sp)
   e3a92:	20913027          	fsd	fs1,512(sp)
   e3a96:	bfca                	c.fsdsp	fs2,504(sp)
   e3a98:	bbce                	c.fsdsp	fs3,496(sp)
   e3a9a:	b7d2                	c.fsdsp	fs4,488(sp)
   e3a9c:	b3d6                	c.fsdsp	fs5,480(sp)
   e3a9e:	afda                	c.fsdsp	fs6,472(sp)
   e3aa0:	abde                	c.fsdsp	fs7,464(sp)
   e3aa2:	a7e2                	c.fsdsp	fs8,456(sp)
   e3aa4:	a3e6                	c.fsdsp	fs9,448(sp)
   e3aa6:	bf6a                	c.fsdsp	fs10,440(sp)
   e3aa8:	bb6e                	c.fsdsp	fs11,432(sp)
   e3aaa:	f3c1                	c.bnez	a5,e3a2a <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xbfc>
   e3aac:	6589                	c.lui	a1,0x2
   e3aae:	13958593          	addi	a1,a1,313 # 2139 <_ZSt15__once_callable+0x2071>
   e3ab2:	000e3697          	auipc	a3,0xe3
   e3ab6:	6f668693          	addi	a3,a3,1782 # 1c71a8 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x157a>
   e3aba:	000e2617          	auipc	a2,0xe2
   e3abe:	37660613          	addi	a2,a2,886 # 1c5e30 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x202>
   e3ac2:	000e3517          	auipc	a0,0xe3
   e3ac6:	38650513          	addi	a0,a0,902 # 1c6e48 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x121a>
   e3aca:	957a10ef          	jal	ra,85420 <ggml_abort@plt>
   e3ace:	0014a797          	auipc	a5,0x14a
   e3ad2:	aea7b783          	ld	a5,-1302(a5) # 22d5b8 <__stack_chk_guard@GLIBC_2.27>
   e3ad6:	773a                	c.ldsp	a4,424(sp)
   e3ad8:	639c                	c.ld	a5,0(a5)
   e3ada:	8fb9                	c.xor	a5,a4
   e3adc:	4701                	c.li	a4,0
   e3ade:	20813427          	fsd	fs0,520(sp)
   e3ae2:	20913027          	fsd	fs1,512(sp)
   e3ae6:	bfca                	c.fsdsp	fs2,504(sp)
   e3ae8:	bbce                	c.fsdsp	fs3,496(sp)
   e3aea:	b7d2                	c.fsdsp	fs4,488(sp)
   e3aec:	b3d6                	c.fsdsp	fs5,480(sp)
   e3aee:	afda                	c.fsdsp	fs6,472(sp)
   e3af0:	abde                	c.fsdsp	fs7,464(sp)
   e3af2:	a7e2                	c.fsdsp	fs8,456(sp)
   e3af4:	a3e6                	c.fsdsp	fs9,448(sp)
   e3af6:	bf6a                	c.fsdsp	fs10,440(sp)
   e3af8:	bb6e                	c.fsdsp	fs11,432(sp)
   e3afa:	fb85                	c.bnez	a5,e3a2a <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xbfc>
   e3afc:	6589                	c.lui	a1,0x2
   e3afe:	14358593          	addi	a1,a1,323 # 2143 <_ZSt15__once_callable+0x207b>
   e3b02:	000e2697          	auipc	a3,0xe2
   e3b06:	4b668693          	addi	a3,a3,1206 # 1c5fb8 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x38a>
   e3b0a:	000e2617          	auipc	a2,0xe2
   e3b0e:	32660613          	addi	a2,a2,806 # 1c5e30 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x202>
   e3b12:	000e3517          	auipc	a0,0xe3
   e3b16:	33650513          	addi	a0,a0,822 # 1c6e48 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x121a>
   e3b1a:	907a10ef          	jal	ra,85420 <ggml_abort@plt>
   e3b1e:	0014a797          	auipc	a5,0x14a
   e3b22:	a9a7b783          	ld	a5,-1382(a5) # 22d5b8 <__stack_chk_guard@GLIBC_2.27>
   e3b26:	773a                	c.ldsp	a4,424(sp)
   e3b28:	639c                	c.ld	a5,0(a5)
   e3b2a:	8fb9                	c.xor	a5,a4
   e3b2c:	4701                	c.li	a4,0
   e3b2e:	20813427          	fsd	fs0,520(sp)
   e3b32:	20913027          	fsd	fs1,512(sp)
   e3b36:	bfca                	c.fsdsp	fs2,504(sp)
   e3b38:	bbce                	c.fsdsp	fs3,496(sp)
   e3b3a:	b7d2                	c.fsdsp	fs4,488(sp)
   e3b3c:	b3d6                	c.fsdsp	fs5,480(sp)
   e3b3e:	afda                	c.fsdsp	fs6,472(sp)
   e3b40:	abde                	c.fsdsp	fs7,464(sp)
   e3b42:	a7e2                	c.fsdsp	fs8,456(sp)
   e3b44:	a3e6                	c.fsdsp	fs9,448(sp)
   e3b46:	bf6a                	c.fsdsp	fs10,440(sp)
   e3b48:	bb6e                	c.fsdsp	fs11,432(sp)
   e3b4a:	ee0790e3          	bne	a5,zero,e3a2a <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xbfc>
   e3b4e:	6589                	c.lui	a1,0x2
   e3b50:	13c58593          	addi	a1,a1,316 # 213c <_ZSt15__once_callable+0x2074>
   e3b54:	000e3697          	auipc	a3,0xe3
   e3b58:	69468693          	addi	a3,a3,1684 # 1c71e8 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x15ba>
   e3b5c:	000e2617          	auipc	a2,0xe2
   e3b60:	2d460613          	addi	a2,a2,724 # 1c5e30 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x202>
   e3b64:	000e3517          	auipc	a0,0xe3
   e3b68:	2e450513          	addi	a0,a0,740 # 1c6e48 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x121a>
   e3b6c:	8b5a10ef          	jal	ra,85420 <ggml_abort@plt>
   e3b70:	0014a797          	auipc	a5,0x14a
   e3b74:	a487b783          	ld	a5,-1464(a5) # 22d5b8 <__stack_chk_guard@GLIBC_2.27>
   e3b78:	773a                	c.ldsp	a4,424(sp)
   e3b7a:	639c                	c.ld	a5,0(a5)
   e3b7c:	8fb9                	c.xor	a5,a4
   e3b7e:	4701                	c.li	a4,0
   e3b80:	20813427          	fsd	fs0,520(sp)
   e3b84:	20913027          	fsd	fs1,512(sp)
   e3b88:	bfca                	c.fsdsp	fs2,504(sp)
   e3b8a:	bbce                	c.fsdsp	fs3,496(sp)
   e3b8c:	b7d2                	c.fsdsp	fs4,488(sp)
   e3b8e:	b3d6                	c.fsdsp	fs5,480(sp)
   e3b90:	afda                	c.fsdsp	fs6,472(sp)
   e3b92:	abde                	c.fsdsp	fs7,464(sp)
   e3b94:	a7e2                	c.fsdsp	fs8,456(sp)
   e3b96:	a3e6                	c.fsdsp	fs9,448(sp)
   e3b98:	bf6a                	c.fsdsp	fs10,440(sp)
   e3b9a:	bb6e                	c.fsdsp	fs11,432(sp)
   e3b9c:	e80797e3          	bne	a5,zero,e3a2a <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xbfc>
   e3ba0:	6589                	c.lui	a1,0x2
   e3ba2:	14658593          	addi	a1,a1,326 # 2146 <_ZSt15__once_callable+0x207e>
   e3ba6:	000e2697          	auipc	a3,0xe2
   e3baa:	44a68693          	addi	a3,a3,1098 # 1c5ff0 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x3c2>
   e3bae:	000e2617          	auipc	a2,0xe2
   e3bb2:	28260613          	addi	a2,a2,642 # 1c5e30 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x202>
   e3bb6:	000e3517          	auipc	a0,0xe3
   e3bba:	29250513          	addi	a0,a0,658 # 1c6e48 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x121a>
   e3bbe:	863a10ef          	jal	ra,85420 <ggml_abort@plt>
   e3bc2:	0014a797          	auipc	a5,0x14a
   e3bc6:	9f67b783          	ld	a5,-1546(a5) # 22d5b8 <__stack_chk_guard@GLIBC_2.27>
   e3bca:	773a                	c.ldsp	a4,424(sp)
   e3bcc:	639c                	c.ld	a5,0(a5)
   e3bce:	8fb9                	c.xor	a5,a4
   e3bd0:	4701                	c.li	a4,0
   e3bd2:	20813427          	fsd	fs0,520(sp)
   e3bd6:	20913027          	fsd	fs1,512(sp)
   e3bda:	bfca                	c.fsdsp	fs2,504(sp)
   e3bdc:	bbce                	c.fsdsp	fs3,496(sp)
   e3bde:	b7d2                	c.fsdsp	fs4,488(sp)
   e3be0:	b3d6                	c.fsdsp	fs5,480(sp)
   e3be2:	afda                	c.fsdsp	fs6,472(sp)
   e3be4:	abde                	c.fsdsp	fs7,464(sp)
   e3be6:	a7e2                	c.fsdsp	fs8,456(sp)
   e3be8:	a3e6                	c.fsdsp	fs9,448(sp)
   e3bea:	bf6a                	c.fsdsp	fs10,440(sp)
   e3bec:	bb6e                	c.fsdsp	fs11,432(sp)
   e3bee:	e2079ee3          	bne	a5,zero,e3a2a <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xbfc>
   e3bf2:	6589                	c.lui	a1,0x2
   e3bf4:	14558593          	addi	a1,a1,325 # 2145 <_ZSt15__once_callable+0x207d>
   e3bf8:	000e2697          	auipc	a3,0xe2
   e3bfc:	3e868693          	addi	a3,a3,1000 # 1c5fe0 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x3b2>
   e3c00:	000e2617          	auipc	a2,0xe2
   e3c04:	23060613          	addi	a2,a2,560 # 1c5e30 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x202>
   e3c08:	000e3517          	auipc	a0,0xe3
   e3c0c:	24050513          	addi	a0,a0,576 # 1c6e48 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x121a>
   e3c10:	811a10ef          	jal	ra,85420 <ggml_abort@plt>
   e3c14:	0014a797          	auipc	a5,0x14a
   e3c18:	9a47b783          	ld	a5,-1628(a5) # 22d5b8 <__stack_chk_guard@GLIBC_2.27>
   e3c1c:	773a                	c.ldsp	a4,424(sp)
   e3c1e:	639c                	c.ld	a5,0(a5)
   e3c20:	8fb9                	c.xor	a5,a4
   e3c22:	4701                	c.li	a4,0
   e3c24:	20813427          	fsd	fs0,520(sp)
   e3c28:	20913027          	fsd	fs1,512(sp)
   e3c2c:	bfca                	c.fsdsp	fs2,504(sp)
   e3c2e:	bbce                	c.fsdsp	fs3,496(sp)
   e3c30:	b7d2                	c.fsdsp	fs4,488(sp)
   e3c32:	b3d6                	c.fsdsp	fs5,480(sp)
   e3c34:	afda                	c.fsdsp	fs6,472(sp)
   e3c36:	abde                	c.fsdsp	fs7,464(sp)
   e3c38:	a7e2                	c.fsdsp	fs8,456(sp)
   e3c3a:	a3e6                	c.fsdsp	fs9,448(sp)
   e3c3c:	bf6a                	c.fsdsp	fs10,440(sp)
   e3c3e:	bb6e                	c.fsdsp	fs11,432(sp)
   e3c40:	de0795e3          	bne	a5,zero,e3a2a <_ZL49ggml_compute_forward_flash_attn_ext_f16_one_chunkPK19ggml_compute_paramsP11ggml_tensoriillPfl+0xbfc>
   e3c44:	6589                	c.lui	a1,0x2
   e3c46:	14458593          	addi	a1,a1,324 # 2144 <_ZSt15__once_callable+0x207c>
   e3c4a:	000e2697          	auipc	a3,0xe2
   e3c4e:	38668693          	addi	a3,a3,902 # 1c5fd0 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x3a2>
   e3c52:	000e2617          	auipc	a2,0xe2
   e3c56:	1de60613          	addi	a2,a2,478 # 1c5e30 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x202>
   e3c5a:	000e3517          	auipc	a0,0xe3
   e3c5e:	1ee50513          	addi	a0,a0,494 # 1c6e48 <_ZSt24__is_ios_failure_handlerPKN10__cxxabiv117__class_type_infoE+0x121a>
   e3c62:	fbea10ef          	jal	ra,85420 <ggml_abort@plt>
