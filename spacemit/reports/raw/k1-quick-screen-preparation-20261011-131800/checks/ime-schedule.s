	.file	"ime-schedule.cpp"
	.option pic
	.attribute arch, "rv64i2p1_m2p0_a2p1_f2p2_d2p2_c2p0_v1p0_zicbop1p0_zicsr2p0_zifencei2p0_zihintpause2p0_zmmul1p0_zaamo1p0_zalrsc1p0_zfh1p0_zfhmin1p0_zca1p0_zcd1p0_zve32f1p0_zve32x1p0_zve64d1p0_zve64f1p0_zve64x1p0_zvfh1p0_zvl128b1p0_zvl32b1p0_zvl64b1p0"
	.attribute unaligned_access, 0
	.attribute stack_align, 16
	.text
	.align	1
	.type	_ZN16spacemit_kernels12_GLOBAL__N_1L22quick_m1_load_scheduleEmPKhS2_Pfmmm.constprop.0, @function
_ZN16spacemit_kernels12_GLOBAL__N_1L22quick_m1_load_scheduleEmPKhS2_Pfmmm.constprop.0:
.LFB4348:
	.cfi_startproc
	beq	a3,zero,.L11
	addi	sp,sp,-48
	.cfi_def_cfa_offset 48
	sd	s1,40(sp)
	sd	s2,32(sp)
	sd	s3,24(sp)
	sd	s4,16(sp)
	sd	s5,8(sp)
	sd	s6,0(sp)
	.cfi_offset 9, -8
	.cfi_offset 18, -16
	.cfi_offset 19, -24
	.cfi_offset 20, -32
	.cfi_offset 21, -40
	.cfi_offset 22, -48
	slli	t6,a4,5
	li	t1,0
	li	a7,0
	li	t5,16
.L4:
	slli	a5,t1,4
	srli	a5,a5,1
	add	a5,a5,t1
	sub	a6,a3,a7
	add	a5,a1,a5
	mv	t4,a4
	bleu	a6,t5,.L3
	li	a6,16
.L3:
#APP
# 1218 "/home/moyamryia/Projects/riscv-accl/lab/k1-quick-screen-final-20261011/ime-schedule.cpp" 1
	vsetvli      t0, zero, e32, m4       
	vxor.vv      v28, v28, v28           
	addi         s1, a5, 0             
	addi         s2, a5, 8             
	addi         s3, a5, 16            
	addi         s4, a5, 24            
	addi         s5, a0, 0             
	addi         s6, a0, 12            
	LOOP_K38:                            
	vsetvli      t0, zero, e16, mf4      
	vle16.v      v4, (s1)                
	addi         s1, s1, 32              
	vle16.v      v5, (s2)                
	addi         s2, s2, 56              
	vle16.v      v6, (s3)                
	addi         s3, s3, 80              
	vle16.v      v7, (s4)                
	addi         s4, s4, 104             
	flw          f1, (s5)                
	addi         s5, s5, 4               
	vfwcvt.f.f.v v8, v4                  
	vfwcvt.f.f.v v9, v5                  
	vfwcvt.f.f.v v10, v6                 
	vfwcvt.f.f.v v11, v7                 
	vsetvli      t0, zero, e32, mf2      
	vxor.vv      v16, v16, v16           
	vxor.vv      v18, v18, v18           
	vxor.vv      v20, v20, v20           
	vxor.vv      v22, v22, v22           
	vfmul.vf     v24, v8, f1             
	vfmul.vf     v25, v9, f1             
	vfmul.vf     v26, v10, f1            
	vfmul.vf     v27, v11, f1            
	addi         t4, t4, -1      
	vsetvli      t0, zero, e8, m1        
	vle8.v       v4, (s1)                
	addi         s1, s1, 128             
	vle8.v       v5, (s2)                
	addi         s2, s2, 128             
	vand.vi      v0, v4, 15              
	vsrl.vi      v4, v4, 4               
	vle8.v       v6, (s3)                
	addi         s3, s3, 128             
	vand.vi      v1, v5, 15              
	vsrl.vi      v5, v5, 4               
	vle8.v       v7, (s4)                
	addi         s4, s4, 128             
	vand.vi      v2, v6, 15              
	vsrl.vi      v6, v6, 4               
	vand.vi      v3, v7, 15              
	vsrl.vi      v7, v7, 4               
	vsetvli      t0, zero, e8, mf4       
	vle8.v       v14, (s5)               
	addi         s5, s5, 16              
	vle8.v       v15, (s6)               
	addi         s6, s6, 16              
	vsetvli      t0, zero, e8, m1        
	vadd.vi      v0, v0, -8              
	vadd.vi      v1, v1, -8              
	vadd.vi      v2, v2, -8              
	vadd.vi      v3, v3, -8              
	vadd.vi      v4, v4, -8              
	vadd.vi      v5, v5, -8              
	vadd.vi      v6, v6, -8              
	vadd.vi      v7, v7, -8              
	vmadot       v16, v14, v0            
	vmadot       v18, v14, v1            
	vmadot       v20, v14, v2            
	vmadot       v22, v14, v3            
	vmadot       v16, v15, v4            
	vmadot       v18, v15, v5            
	vmadot       v20, v15, v6            
	vmadot       v22, v15, v7            
	vle8.v       v4, (s1)                
	addi         s1, s1, 128             
	vle8.v       v5, (s2)                
	addi         s2, s2, 128             
	vand.vi      v0, v4, 15              
	vsrl.vi      v4, v4, 4               
	vle8.v       v6, (s3)                
	addi         s3, s3, 128             
	vand.vi      v1, v5, 15              
	vsrl.vi      v5, v5, 4               
	vle8.v       v7, (s4)                
	addi         s4, s4, 128             
	vand.vi      v2, v6, 15              
	vsrl.vi      v6, v6, 4               
	vand.vi      v3, v7, 15              
	vsrl.vi      v7, v7, 4               
	vsetvli      t0, zero, e8, mf4       
	vle8.v       v14, (s5)               
	addi         s5, s5, 16              
	vle8.v       v15, (s6)               
	addi         s6, s6, 16              
	vsetvli      t0, zero, e8, m1        
	vadd.vi      v0, v0, -8              
	vadd.vi      v1, v1, -8              
	vadd.vi      v2, v2, -8              
	vadd.vi      v3, v3, -8              
	vadd.vi      v4, v4, -8              
	vadd.vi      v5, v5, -8              
	vadd.vi      v6, v6, -8              
	vadd.vi      v7, v7, -8              
	vmadot       v16, v14, v0            
	vmadot       v18, v14, v1            
	vmadot       v20, v14, v2            
	vmadot       v22, v14, v3            
	vmadot       v16, v15, v4            
	vmadot       v18, v15, v5            
	vmadot       v20, v15, v6            
	vmadot       v22, v15, v7            
	vsetvli      t0, zero, e32, mf2      
	vfcvt.f.x.v  v16,  v16               
	vfcvt.f.x.v  v18,  v18               
	vfcvt.f.x.v  v20,  v20               
	vfcvt.f.x.v  v22,  v22               
	addi         s2, s1, 8               
	addi         s3, s1, 16              
	addi         s4, s1, 24              
	addi         s6, s5, 12              
	vfmacc.vv    v28, v16, v24           
	vfmacc.vv    v29, v18, v25           
	vfmacc.vv    v30, v20, v26           
	vfmacc.vv    v31, v22, v27           
	bnez         t4, LOOP_K38        
	addi         t3, zero, 16            
	addi         s1, a2, 16            
	addi         s2, a2, 32            
	addi         s3, a2, 48            
	blt          a6, t3, ST_TAIL38 
	vse32.v      v28, (a2)             
	vse32.v      v29, (s1)               
	vse32.v      v30, (s2)               
	vse32.v      v31, (s3)               
	jal          x0, END38               
	ST_TAIL38:                           
	vsetvli      t0, a6, e32, mf2  
	sub          a6, a6, t0  
	vse32.v      v28, (a2)             
	vsetvli      t0, a6, e32, mf2  
	sub          a6, a6, t0  
	vse32.v      v29, (s1)               
	vsetvli      t0, a6, e32, mf2  
	sub          a6, a6, t0  
	vse32.v      v30, (s2)               
	vsetvli      t0, a6, e32, mf2  
	sub          a6, a6, t0  
	vse32.v      v31, (s3)               
	END38:                               
	
# 0 "" 2
#NO_APP
	addi	a7,a7,16
	add	t1,t1,t6
	addi	a2,a2,64
	bgtu	a3,a7,.L4
	ld	s1,40(sp)
	.cfi_restore 9
	ld	s2,32(sp)
	.cfi_restore 18
	ld	s3,24(sp)
	.cfi_restore 19
	ld	s4,16(sp)
	.cfi_restore 20
	ld	s5,8(sp)
	.cfi_restore 21
	ld	s6,0(sp)
	.cfi_restore 22
	addi	sp,sp,48
	.cfi_def_cfa_offset 0
	jr	ra
.L11:
	ret
	.cfi_endproc
.LFE4348:
	.size	_ZN16spacemit_kernels12_GLOBAL__N_1L22quick_m1_load_scheduleEmPKhS2_Pfmmm.constprop.0, .-_ZN16spacemit_kernels12_GLOBAL__N_1L22quick_m1_load_scheduleEmPKhS2_Pfmmm.constprop.0
	.align	1
	.type	_ZN16spacemit_kernels12_GLOBAL__N_1L15k1_m1_k32_fixedEmPKhS2_Pfmmm.constprop.0, @function
_ZN16spacemit_kernels12_GLOBAL__N_1L15k1_m1_k32_fixedEmPKhS2_Pfmmm.constprop.0:
.LFB4349:
	.cfi_startproc
	beq	a3,zero,.L25
	addi	sp,sp,-48
	.cfi_def_cfa_offset 48
	sd	s1,40(sp)
	sd	s2,32(sp)
	sd	s3,24(sp)
	sd	s4,16(sp)
	sd	s5,8(sp)
	sd	s6,0(sp)
	.cfi_offset 9, -8
	.cfi_offset 18, -16
	.cfi_offset 19, -24
	.cfi_offset 20, -32
	.cfi_offset 21, -40
	.cfi_offset 22, -48
	slli	t6,a4,5
	li	t1,0
	li	a7,0
	li	t5,16
.L18:
	slli	a5,t1,4
	srli	a5,a5,1
	add	a5,a5,t1
	sub	a6,a3,a7
	add	a5,a1,a5
	mv	t4,a4
	bleu	a6,t5,.L17
	li	a6,16
.L17:
#APP
# 1075 "/home/moyamryia/Projects/riscv-accl/lab/k1-quick-screen-final-20261011/ime-schedule.cpp" 1
	vsetvli      t0, zero, e32, m4       
	vxor.vv      v28, v28, v28           
	addi         s1, a5, 0             
	addi         s2, a5, 8             
	addi         s3, a5, 16            
	addi         s4, a5, 24            
	addi         s5, a0, 0             
	addi         s6, a0, 12            
	LOOP_K105:                            
	vsetvli      t0, zero, e16, mf4      
	vle16.v      v4, (s1)                
	addi         s1, s1, 32              
	vle16.v      v5, (s2)                
	addi         s2, s2, 56              
	vle16.v      v6, (s3)                
	addi         s3, s3, 80              
	vle16.v      v7, (s4)                
	addi         s4, s4, 104             
	flw          f1, (s5)                
	addi         s5, s5, 4               
	vfwcvt.f.f.v v8, v4                  
	vfwcvt.f.f.v v9, v5                  
	vfwcvt.f.f.v v10, v6                 
	vfwcvt.f.f.v v11, v7                 
	vsetvli      t0, zero, e32, mf2      
	vxor.vv      v16, v16, v16           
	vxor.vv      v18, v18, v18           
	vxor.vv      v20, v20, v20           
	vxor.vv      v22, v22, v22           
	vfmul.vf     v24, v8, f1             
	vfmul.vf     v25, v9, f1             
	vfmul.vf     v26, v10, f1            
	vfmul.vf     v27, v11, f1            
	addi         t4, t4, -1      
	vsetvli      t0, zero, e8, m1        
	vle8.v       v4, (s1)                
	addi         s1, s1, 128             
	vle8.v       v5, (s2)                
	addi         s2, s2, 128             
	vle8.v       v6, (s3)                
	addi         s3, s3, 128             
	vle8.v       v7, (s4)                
	addi         s4, s4, 128             
	vsetvli      t0, zero, e8, mf4       
	vle8.v       v14, (s5)               
	addi         s5, s5, 16              
	vle8.v       v15, (s6)               
	addi         s6, s6, 16              
	vsetvli      t0, zero, e8, m1        
	vand.vi      v0, v4, 15              
	vand.vi      v1, v5, 15              
	vand.vi      v2, v6, 15              
	vand.vi      v3, v7, 15              
	vsrl.vi      v4, v4, 4               
	vsrl.vi      v5, v5, 4               
	vsrl.vi      v6, v6, 4               
	vsrl.vi      v7, v7, 4               
	vadd.vi      v0, v0, -8              
	vadd.vi      v1, v1, -8              
	vadd.vi      v2, v2, -8              
	vadd.vi      v3, v3, -8              
	vadd.vi      v4, v4, -8              
	vadd.vi      v5, v5, -8              
	vadd.vi      v6, v6, -8              
	vadd.vi      v7, v7, -8              
	vmadot       v16, v14, v0            
	vmadot       v18, v14, v1            
	vmadot       v20, v14, v2            
	vmadot       v22, v14, v3            
	vmadot       v16, v15, v4            
	vmadot       v18, v15, v5            
	vmadot       v20, v15, v6            
	vmadot       v22, v15, v7            
	vle8.v       v4, (s1)                
	addi         s1, s1, 128             
	vle8.v       v5, (s2)                
	addi         s2, s2, 128             
	vle8.v       v6, (s3)                
	addi         s3, s3, 128             
	vle8.v       v7, (s4)                
	addi         s4, s4, 128             
	vsetvli      t0, zero, e8, mf4       
	vle8.v       v14, (s5)               
	addi         s5, s5, 16              
	vle8.v       v15, (s6)               
	addi         s6, s6, 16              
	vsetvli      t0, zero, e8, m1        
	vand.vi      v0, v4, 15              
	vand.vi      v1, v5, 15              
	vand.vi      v2, v6, 15              
	vand.vi      v3, v7, 15              
	vsrl.vi      v4, v4, 4               
	vsrl.vi      v5, v5, 4               
	vsrl.vi      v6, v6, 4               
	vsrl.vi      v7, v7, 4               
	vadd.vi      v0, v0, -8              
	vadd.vi      v1, v1, -8              
	vadd.vi      v2, v2, -8              
	vadd.vi      v3, v3, -8              
	vadd.vi      v4, v4, -8              
	vadd.vi      v5, v5, -8              
	vadd.vi      v6, v6, -8              
	vadd.vi      v7, v7, -8              
	vmadot       v16, v14, v0            
	vmadot       v18, v14, v1            
	vmadot       v20, v14, v2            
	vmadot       v22, v14, v3            
	vmadot       v16, v15, v4            
	vmadot       v18, v15, v5            
	vmadot       v20, v15, v6            
	vmadot       v22, v15, v7            
	vsetvli      t0, zero, e32, mf2      
	vfcvt.f.x.v  v16,  v16               
	vfcvt.f.x.v  v18,  v18               
	vfcvt.f.x.v  v20,  v20               
	vfcvt.f.x.v  v22,  v22               
	addi         s2, s1, 8               
	addi         s3, s1, 16              
	addi         s4, s1, 24              
	addi         s6, s5, 12              
	vfmacc.vv    v28, v16, v24           
	vfmacc.vv    v29, v18, v25           
	vfmacc.vv    v30, v20, v26           
	vfmacc.vv    v31, v22, v27           
	bnez         t4, LOOP_K105        
	addi         t3, zero, 16            
	addi         s1, a2, 16            
	addi         s2, a2, 32            
	addi         s3, a2, 48            
	blt          a6, t3, ST_TAIL105 
	vse32.v      v28, (a2)             
	vse32.v      v29, (s1)               
	vse32.v      v30, (s2)               
	vse32.v      v31, (s3)               
	jal          x0, END105               
	ST_TAIL105:                           
	vsetvli      t0, a6, e32, mf2  
	sub          a6, a6, t0  
	vse32.v      v28, (a2)             
	vsetvli      t0, a6, e32, mf2  
	sub          a6, a6, t0  
	vse32.v      v29, (s1)               
	vsetvli      t0, a6, e32, mf2  
	sub          a6, a6, t0  
	vse32.v      v30, (s2)               
	vsetvli      t0, a6, e32, mf2  
	sub          a6, a6, t0  
	vse32.v      v31, (s3)               
	END105:                               
	
# 0 "" 2
#NO_APP
	addi	a7,a7,16
	add	t1,t1,t6
	addi	a2,a2,64
	bgtu	a3,a7,.L18
	ld	s1,40(sp)
	.cfi_restore 9
	ld	s2,32(sp)
	.cfi_restore 18
	ld	s3,24(sp)
	.cfi_restore 19
	ld	s4,16(sp)
	.cfi_restore 20
	ld	s5,8(sp)
	.cfi_restore 21
	ld	s6,0(sp)
	.cfi_restore 22
	addi	sp,sp,48
	.cfi_def_cfa_offset 0
	jr	ra
.L25:
	ret
	.cfi_endproc
.LFE4349:
	.size	_ZN16spacemit_kernels12_GLOBAL__N_1L15k1_m1_k32_fixedEmPKhS2_Pfmmm.constprop.0, .-_ZN16spacemit_kernels12_GLOBAL__N_1L15k1_m1_k32_fixedEmPKhS2_Pfmmm.constprop.0
	.align	1
	.globl	_ZN16spacemit_kernels4ime118quantize_a_4row_i8EmPKfmPh
	.type	_ZN16spacemit_kernels4ime118quantize_a_4row_i8EmPKfmPh, @function
_ZN16spacemit_kernels4ime118quantize_a_4row_i8EmPKfmPh:
.LFB3583:
	.cfi_startproc
	flw	fa4,.LC0,a5
	flw	fa5,.LC1,a5
	addi	sp,sp,-16
	.cfi_def_cfa_offset 16
	addi	t4,a0,4
	sd	s1,8(sp)
	sd	s2,0(sp)
	.cfi_offset 9, -8
	.cfi_offset 18, -16
	mv	a4,a1
	addi	a3,a3,-16
	slli	t4,t4,2
	slli	t6,a2,2
	li	a5,16
	li	t5,32
.L29:
	add	a7,a3,a5
	mv	a6,a4
#APP
# 111 "/home/moyamryia/Projects/riscv-accl/lab/k1-quick-screen-final-20261011/ime-schedule.cpp" 1
	vsetvli            t0, zero, e32, m8        
	addi               t2, a2, 0         
	addi               a1, a7, 0            
	blt                t2, a0, TAIL160    
	LOOP160:                                     
	vsetvli            t0, a0, e32, m8   
	vle32.v            v0, (a6)             
	sub                t2, t2, t0               
	slli               t1, t0, 2                
	add                a6, a6, t1       
	add                s1, a1, a5        
	vmv.s.x            v16, zero                
	vfabs.v            v8, v0                   
	vfredmax.vs        v16, v8, v16             
	vfmv.f.s           f10, v16                 
	fmul.s             f10, f10, fa5     
	fsw                f10, (a1)                
	fdiv.s             f11, fa4, f10        
	vfmul.vf           v16, v0, f11             
	vfcvt.x.f.v        v16, v16                 
	vsetvli            t0, zero, e16, mf2       
	vnclip.wx          v16, v16, zero           
	vnclip.wx          v17, v17, zero           
	vnclip.wx          v18, v18, zero           
	vnclip.wx          v19, v19, zero           
	vnclip.wx          v20, v20, zero           
	vnclip.wx          v21, v21, zero           
	vnclip.wx          v22, v22, zero           
	vnclip.wx          v23, v23, zero           
	vsetvli            t0, zero, e8, mf4        
	vnclip.wx          v24, v16, zero           
	vnclip.wx          v25, v17, zero           
	vnclip.wx          v26, v18, zero           
	vnclip.wx          v27, v19, zero           
	vnclip.wx          v28, v20, zero           
	vnclip.wx          v29, v21, zero           
	vnclip.wx          v30, v22, zero           
	vnclip.wx          v31, v23, zero           
	addi               t1, a0, 0         
	vsetvli            t0, t1, e8, mf4          
	vse8.v             v24, (s1)                
	addi               s1, s1, 32               
	sub                t1, t1, t0               
	vsetvli            t0, t1, e8, mf4          
	vse8.v             v25, (s1)                
	addi               s1, s1, 32               
	sub                t1, t1, t0               
	vsetvli            t0, t1, e8, mf4          
	vse8.v             v26, (s1)                
	addi               s1, s1, 32               
	sub                t1, t1, t0               
	vsetvli            t0, t1, e8, mf4          
	vse8.v             v27, (s1)                
	addi               s1, s1, 32               
	sub                t1, t1, t0               
	vsetvli            t0, t1, e8, mf4          
	vse8.v             v28, (s1)                
	addi               s1, s1, 32               
	sub                t1, t1, t0               
	vsetvli            t0, t1, e8, mf4          
	vse8.v             v29, (s1)                
	addi               s1, s1, 32               
	sub                t1, t1, t0               
	vsetvli            t0, t1, e8, mf4          
	vse8.v             v30, (s1)                
	addi               s1, s1, 32               
	sub                t1, t1, t0               
	vsetvli            t0, t1, e8, mf4          
	vse8.v             v31, (s1)                
	add                a1, a1, t4        
	bge                t2, a0, LOOP160    
	TAIL160:                                     
	blez               t2, QUIT160               
	vsetvli            t0, zero, e32, m8        
	vxor.vv            v16, v16, v16            
	vxor.vv            v24, v24, v24            
	vsetvli            t0, t2, e32, m8          
	vle32.v            v0, (a6)             
	add                s1, a1, a5        
	vmv.s.x            v16, zero                
	vfabs.v            v8, v0                   
	vfredmax.vs        v16, v8, v16             
	vfmv.f.s           f10, v16                 
	fmul.s             f10, f10, fa5     
	fsw                f10, (a1)                
	fdiv.s             f11, fa4, f10        
	vfmul.vf           v16, v0, f11             
	vfcvt.x.f.v        v16, v16                 
	vsetvli            t0, zero, e16, mf2       
	vnclip.wx          v16, v16, zero           
	vnclip.wx          v17, v17, zero           
	vnclip.wx          v18, v18, zero           
	vnclip.wx          v19, v19, zero           
	vnclip.wx          v20, v20, zero           
	vnclip.wx          v21, v21, zero           
	vnclip.wx          v22, v22, zero           
	vnclip.wx          v23, v23, zero           
	vsetvli            t0, zero, e8, mf4        
	vnclip.wx          v24, v16, zero           
	vnclip.wx          v25, v17, zero           
	vnclip.wx          v26, v18, zero           
	vnclip.wx          v27, v19, zero           
	vnclip.wx          v28, v20, zero           
	vnclip.wx          v29, v21, zero           
	vnclip.wx          v30, v22, zero           
	vnclip.wx          v31, v23, zero           
	addi               t3, a0, 0         
	addi               s2, s1, 0                
	vsetvli            t0, zero, e8, mf4        
	vxor.vv            v8, v8, v8               
	SET_ZERO160:                                 
	vse8.v             v8, (s2)                 
	addi               s2, s2, 32               
	addi               t3, t3, -8               
	bnez               t3, SET_ZERO160           
	addi               t1, a0, 0         
	vsetvli            t0, t1, e8, mf4          
	vse8.v             v24, (s1)                
	addi               s1, s1, 32               
	sub                t1, t1, t0               
	vsetvli            t0, t1, e8, mf4          
	vse8.v             v25, (s1)                
	addi               s1, s1, 32               
	sub                t1, t1, t0               
	vsetvli            t0, t1, e8, mf4          
	vse8.v             v26, (s1)                
	addi               s1, s1, 32               
	sub                t1, t1, t0               
	vsetvli            t0, t1, e8, mf4          
	vse8.v             v27, (s1)                
	addi               s1, s1, 32               
	sub                t1, t1, t0               
	vsetvli            t0, t1, e8, mf4          
	vse8.v             v28, (s1)                
	addi               s1, s1, 32               
	sub                t1, t1, t0               
	vsetvli            t0, t1, e8, mf4          
	vse8.v             v29, (s1)                
	addi               s1, s1, 32               
	sub                t1, t1, t0               
	vsetvli            t0, t1, e8, mf4          
	vse8.v             v30, (s1)                
	addi               s1, s1, 32               
	sub                t1, t1, t0               
	vsetvli            t0, t1, e8, mf4          
	vse8.v             v31, (s1)                
	QUIT160:                                     
	
# 0 "" 2
#NO_APP
	addi	a5,a5,4
	add	a4,a4,t6
	bne	a5,t5,.L29
	ld	s1,8(sp)
	.cfi_restore 9
	ld	s2,0(sp)
	.cfi_restore 18
	addi	sp,sp,16
	.cfi_def_cfa_offset 0
	jr	ra
	.cfi_endproc
.LFE3583:
	.size	_ZN16spacemit_kernels4ime118quantize_a_4row_i8EmPKfmPh, .-_ZN16spacemit_kernels4ime118quantize_a_4row_i8EmPKfmPh
	.align	1
	.globl	_ZN16spacemit_kernels4ime117quantize_a_row_i8EmPKfmPh
	.type	_ZN16spacemit_kernels4ime117quantize_a_row_i8EmPKfmPh, @function
_ZN16spacemit_kernels4ime117quantize_a_row_i8EmPKfmPh:
.LFB3584:
	.cfi_startproc
	addi	sp,sp,-32
	.cfi_def_cfa_offset 32
	sd	s1,24(sp)
	sd	s2,16(sp)
	sd	s3,8(sp)
	sd	s4,0(sp)
	.cfi_offset 9, -8
	.cfi_offset 18, -16
	.cfi_offset 19, -24
	.cfi_offset 20, -32
	flw	fa5,.LC0,a4
	flw	fa4,.LC1,a4
	mv	a5,a2
	mv	a0,a1
	mv	a6,a3
#APP
# 169 "/home/moyamryia/Projects/riscv-accl/lab/k1-quick-screen-final-20261011/ime-schedule.cpp" 1
	addi         t3, zero, 32*4          
	addi         t2, zero, 32            
	addi         a1, a0, 0           
	addi         a2, a0, 128         
	addi         a3, a0, 256         
	addi         a4, a0, 384         
	addi         s1, a6, 0           
	addi         s2, a6, 36          
	addi         s3, a6, 72          
	addi         s4, a6, 108         
	blt          a5, t3, LOOP_K201      
	blt          a5, t2, TAIL201        
	LOOP_MAIN201:                         
	vsetvli      t1, zero, e32, m4       
	addi         a5, a5, -128        
	vle32.v      v0, (a1)                
	addi         a1, a1, 512             
	vle32.v      v4, (a2)                
	addi         a2, a2, 512             
	vle32.v      v8, (a3)                
	addi         a3, a3, 512             
	vle32.v      v12, (a4)               
	addi         a4, a4, 512             
	vfabs.v      v16, v0                 
	vfabs.v      v20, v4                 
	vfabs.v      v24, v8                 
	vfabs.v      v28, v12                
	vsetvli      t0, zero, e32, m2       
	vfmax.vv     v16, v16, v18           
	vfmax.vv     v20, v20, v22           
	vfmax.vv     v24, v24, v26           
	vfmax.vv     v28, v28, v30           
	vsetvli      t0, zero, e32, m1       
	vfmax.vv     v16, v16, v17           
	vfmax.vv     v20, v20, v21           
	vfmax.vv     v24, v24, v25           
	vfmax.vv     v28, v28, v29           
	vfredmax.vs  v17, v16, v17           
	vfredmax.vs  v21, v20, v21           
	vfredmax.vs  v25, v24, v25           
	vfredmax.vs  v29, v28, v29           
	vfmv.f.s     f10,  v17               
	vfmv.f.s     f11,  v21               
	vfmv.f.s     f12,  v25               
	vfmv.f.s     f13,  v29               
	fmul.s       f10, f10, fa4    
	fmul.s       f11, f11, fa4    
	fmul.s       f12, f12, fa4    
	fmul.s       f13, f13, fa4    
	fsw          f10, (s1)               
	addi         s1, s1, 4               
	fsw          f11, (s2)               
	addi         s2, s2, 4               
	fsw          f12, (s3)               
	addi         s3, s3, 4               
	fsw          f13, (s4)               
	addi         s4, s4, 4               
	fdiv.s       f10, fa5, f10       
	fdiv.s       f11, fa5, f11       
	fdiv.s       f12, fa5, f12       
	fdiv.s       f13, fa5, f13       
	vsetvli      t0, zero, e32, m4       
	vfmul.vf     v16, v0, f10            
	vfmul.vf     v20, v4, f11            
	vfmul.vf     v24, v8, f12            
	vfmul.vf     v28, v12, f13           
	vfcvt.x.f.v  v16, v16                
	vfcvt.x.f.v  v20, v20                
	vfcvt.x.f.v  v24, v24                
	vfcvt.x.f.v  v28, v28                
	vsetvli      t0, zero, e16, m2       
	vnclip.wx    v16, v16, zero          
	vnclip.wx    v20, v20, zero          
	vnclip.wx    v24, v24, zero          
	vnclip.wx    v28, v28, zero          
	vsetvli      t0, t1, e8, m1          
	vnclip.wx    v16, v16, zero          
	vnclip.wx    v20, v20, zero          
	vnclip.wx    v24, v24, zero          
	vnclip.wx    v28, v28, zero          
	vse8.v       v16, (s1)               
	addi         s1, s1, 140             
	vse8.v       v20, (s2)               
	addi         s2, s2, 140             
	vse8.v       v24, (s3)               
	addi         s3, s3, 140             
	vse8.v       v28, (s4)               
	addi         s4, s4, 140             
	bge          a5, t3, LOOP_MAIN201   
	blt          a5, t2, TAIL201        
	LOOP_K201:                            
	vsetvli      t1, a5, e32, m4       
	vle32.v      v0, (a1)                
	addi         a1, a1, 128             
	sub          a5, a5, t1          
	vfabs.v      v16, v0                 
	vsetvli      t0, zero, e32, m2       
	vfmax.vv     v16, v16, v18           
	vsetvli      t0, zero, e32, m1       
	vfmax.vv     v16, v16, v17           
	vfredmax.vs  v17, v16, v17           
	vfmv.f.s     f10,  v17               
	fmul.s       f10, f10, fa4    
	fsw          f10, (s1)               
	addi         s1, s1, 4               
	fdiv.s       f11, fa5, f10       
	vsetvli      t0, zero, e32, m4       
	vfmul.vf     v16, v0, f11            
	vfcvt.x.f.v  v16, v16                
	vsetvli      t0, zero, e16, m2       
	vnclip.wx    v16, v16, zero          
	vsetvli      t0, zero, e8, m1        
	vnclip.wx    v16, v16, zero          
	vse8.v       v16, (s1)               
	addi         s1, s1, 32              
	bge          a5, t2, LOOP_K201      
	TAIL201:                              
	blez         a5, END201             
	vsetvli      t0, t3, e32, m4         
	vxor.vv      v0, v0, v0              
	vxor.vv      v16, v16, v16           
	jal          x0, LOOP_K201            
	END201:                               
	
# 0 "" 2
#NO_APP
	ld	s1,24(sp)
	.cfi_restore 9
	ld	s2,16(sp)
	.cfi_restore 18
	ld	s3,8(sp)
	.cfi_restore 19
	ld	s4,0(sp)
	.cfi_restore 20
	addi	sp,sp,32
	.cfi_def_cfa_offset 0
	jr	ra
	.cfi_endproc
.LFE3584:
	.size	_ZN16spacemit_kernels4ime117quantize_a_row_i8EmPKfmPh, .-_ZN16spacemit_kernels4ime117quantize_a_row_i8EmPKfmPh
	.align	1
	.globl	spine_k1_ime_m1_test
	.type	spine_k1_ime_m1_test, @function
spine_k1_ime_m1_test:
.LFB3593:
	.cfi_startproc
	addi	sp,sp,-384
	.cfi_def_cfa_offset 384
	sd	s8,304(sp)
	sd	s11,280(sp)
	sd	ra,376(sp)
	li	t6,2
	.cfi_offset 24, -80
	.cfi_offset 27, -104
	.cfi_offset 1, -8
	ld	s11,384(sp)
	mv	s8,a2
	mv	t4,a3
	beq	a0,t6,.L100
	li	a2,1
	bne	a0,a2,.L36
	addi	a0,a1,-32
	seqz	a0,a0
	seqz	a2,a4
	and	a0,a0,a2
	bne	a0,zero,.L101
.L36:
	li	a2,3
	srli	t2,a1,4
	bgtu	a6,a2,.L102
	beq	a4,zero,.L41
	beq	a7,zero,.L39
	mul	a1,a1,s11
	sd	s0,368(sp)
	.cfi_offset 8, -16
	slli	s0,s11,1
	add	s0,s0,s11
	sd	s9,296(sp)
	sd	s1,360(sp)
	sd	s2,352(sp)
	sd	s3,344(sp)
	sd	s4,336(sp)
	sd	s5,328(sp)
	sd	s6,320(sp)
	sd	s7,312(sp)
	slli	s0,s0,4
	li	t6,0
	li	t1,0
	li	a2,0
	.cfi_offset 25, -88
	.cfi_offset 9, -24
	.cfi_offset 18, -32
	.cfi_offset 19, -40
	.cfi_offset 20, -48
	.cfi_offset 21, -56
	.cfi_offset 22, -64
	.cfi_offset 23, -72
	li	s9,16
	slli	a1,a1,4
.L54:
	srli	a3,t1,1
	add	a3,a3,t6
	sub	a4,a7,a2
	add	a3,t4,a3
	mv	a0,s11
	bleu	a4,s9,.L53
	li	a4,16
.L53:
#APP
# 825 "/home/moyamryia/Projects/riscv-accl/lab/k1-quick-screen-final-20261011/ime-schedule.cpp" 1
	vsetvli      t0, zero, e32, m4       
	vxor.vv      v28, v28, v28           
	vsetvli      t0, zero, e8, m1        
	vmv.v.i      v13, 3                  
	li           s1, 24                  
	vsetvli      t0, s1, e8, m1          
	vmv.v.i      v13, 2                  
	vsetvli      t0, zero, e8, mf2       
	vmv.v.i      v13, 1                  
	vsetvli      t0, zero, e8, mf4       
	vmv.v.i      v13, 0                  
	addi         s1, a3, 0             
	addi         s2, a3, 8             
	addi         s3, a3, 16            
	addi         s4, a3, 24            
	addi         s7, a3, 32            
	addi         s5, s8, 0             
	addi         s6, s8, 12            
	LOOP_K294:                            
	vsetvli      t0, zero, e16, mf4      
	vle16.v      v4, (s1)                
	addi         s1, s1, 48              
	vle16.v      v5, (s2)                
	addi         s2, s2, 72              
	vle16.v      v6, (s3)                
	addi         s3, s3, 96              
	vle16.v      v7, (s4)                
	addi         s4, s4, 120             
	flw          f1, (s5)                
	addi         s5, s5, 4               
	vfwcvt.f.f.v v8, v4                  
	vfwcvt.f.f.v v9, v5                  
	vfwcvt.f.f.v v10, v6                 
	vfwcvt.f.f.v v11, v7                 
	vsetvli      t0, zero, e32, mf2      
	addi         t5, t2, 0         
	vxor.vv      v16, v16, v16           
	vxor.vv      v18, v18, v18           
	vxor.vv      v20, v20, v20           
	vxor.vv      v22, v22, v22           
	vfmul.vf     v24, v8, f1             
	vfmul.vf     v25, v9, f1             
	vfmul.vf     v26, v10, f1            
	vfmul.vf     v27, v11, f1            
	addi         a0, a0, -1      
	vsetvli      t0, zero, e8, mf2       
	vle8.v       v1, (s7)                
	vsetvli      t0, zero, e8, m1        
	vrgather.vv  v8, v1, v13             
	vadd.vi      v13, v13, 4             
	vrgather.vv  v9, v1, v13             
	vadd.vi      v13, v13, 4             
	vrgather.vv  v10, v1, v13            
	vadd.vi      v13, v13, 4             
	vrgather.vv  v11, v1, v13            
	vadd.vi      v13, v13, -12           
	LOOP_INNER294:                        
	vle8.v       v4, (s1)                
	addi         s1, s1, 128             
	vle8.v       v5, (s2)                
	addi         s2, s2, 128             
	vle8.v       v6, (s3)                
	addi         s3, s3, 128             
	vle8.v       v7, (s4)                
	addi         s4, s4, 128             
	vsetvli      t0, zero, e8, mf4       
	vle8.v       v14, (s5)               
	addi         s5, s5, 16              
	vle8.v       v15, (s6)               
	addi         s6, s6, 16              
	addi         t5, t5, -1              
	vsetvli      t0, zero, e8, m1        
	vand.vi      v0, v4, 15              
	vand.vi      v1, v5, 15              
	vand.vi      v2, v6, 15              
	vand.vi      v3, v7, 15              
	vsrl.vi      v4, v4, 4               
	vsrl.vi      v5, v5, 4               
	vsrl.vi      v6, v6, 4               
	vsrl.vi      v7, v7, 4               
	vsub.vv      v0, v0, v8              
	vsub.vv      v4, v4, v8              
	vsub.vv      v1, v1, v9              
	vsub.vv      v5, v5, v9              
	vsub.vv      v2, v2, v10             
	vsub.vv      v6, v6, v10             
	vsub.vv      v3, v3, v11             
	vsub.vv      v7, v7, v11             
	vmadot       v16, v14, v0            
	vmadot       v18, v14, v1            
	vmadot       v20, v14, v2            
	vmadot       v22, v14, v3            
	vmadot       v16, v15, v4            
	vmadot       v18, v15, v5            
	vmadot       v20, v15, v6            
	vmadot       v22, v15, v7            
	bnez         t5, LOOP_INNER294        
	vsetvli      t0, zero, e32, mf2      
	vfcvt.f.x.v  v16,  v16               
	vfcvt.f.x.v  v18,  v18               
	vfcvt.f.x.v  v20,  v20               
	vfcvt.f.x.v  v22,  v22               
	addi         s2, s1, 8               
	addi         s3, s1, 16              
	addi         s4, s1, 24              
	addi         s6, s5, 12              
	vfmacc.vv    v28, v16, v24           
	vfmacc.vv    v29, v18, v25           
	vfmacc.vv    v30, v20, v26           
	vfmacc.vv    v31, v22, v27           
	addi         s7, s1, 32              
	bnez         a0, LOOP_K294        
	addi         t3, zero, 16            
	addi         s1, a5, 16            
	addi         s2, a5, 32            
	addi         s3, a5, 48            
	blt          a4, t3, ST_TAIL294 
	vse32.v      v28, (a5)             
	vse32.v      v29, (s1)               
	vse32.v      v30, (s2)               
	vse32.v      v31, (s3)               
	jal          x0, END294               
	ST_TAIL294:                           
	vsetvli      t0, a4, e32, mf2  
	sub          a4, a4, t0  
	vse32.v      v28, (a5)             
	vsetvli      t0, a4, e32, mf2  
	sub          a4, a4, t0  
	vse32.v      v29, (s1)               
	vsetvli      t0, a4, e32, mf2  
	sub          a4, a4, t0  
	vse32.v      v30, (s2)               
	vsetvli      t0, a4, e32, mf2  
	sub          a4, a4, t0  
	vse32.v      v31, (s3)               
	END294:                               
	
# 0 "" 2
#NO_APP
	addi	a2,a2,16
	add	t1,t1,a1
	add	t6,t6,s0
	addi	a5,a5,64
	bgtu	a7,a2,.L54
.L99:
	ld	s0,368(sp)
	.cfi_restore 8
	ld	s1,360(sp)
	.cfi_restore 9
	ld	s2,352(sp)
	.cfi_restore 18
	ld	s3,344(sp)
	.cfi_restore 19
	ld	s4,336(sp)
	.cfi_restore 20
	ld	s5,328(sp)
	.cfi_restore 21
	ld	s6,320(sp)
	.cfi_restore 22
	ld	s7,312(sp)
	.cfi_restore 23
	ld	s9,296(sp)
	.cfi_restore 25
.L39:
	ld	ra,376(sp)
	.cfi_remember_state
	.cfi_restore 1
	ld	s8,304(sp)
	.cfi_restore 24
	ld	s11,280(sp)
	.cfi_restore 27
	li	a0,1
	addi	sp,sp,384
	.cfi_def_cfa_offset 0
	jr	ra
.L102:
	.cfi_restore_state
	beq	a4,zero,.L40
	beq	a7,zero,.L48
	mul	a1,a1,s11
	ld	a4,392(sp)
	sd	s10,288(sp)
	.cfi_offset 26, -96
	slli	s10,s11,1
	add	s10,s10,s11
	sd	s0,368(sp)
	sd	s7,312(sp)
	sd	s9,296(sp)
	sd	s1,360(sp)
	sd	s2,352(sp)
	slli	a0,a1,4
	sd	s3,344(sp)
	sd	s4,336(sp)
	sd	s5,328(sp)
	sd	s6,320(sp)
	slli	s10,s10,4
	.cfi_offset 8, -16
	.cfi_offset 23, -72
	.cfi_offset 25, -88
	.cfi_offset 9, -24
	.cfi_offset 18, -32
	.cfi_offset 19, -40
	.cfi_offset 20, -48
	.cfi_offset 21, -56
	.cfi_offset 22, -64
	slli	s7,a4,2
	li	s0,0
	li	t6,0
	li	t5,0
	sd	a0,8(sp)
	mv	s9,t2
.L47:
	srli	a0,t6,1
	add	a0,a0,s0
	sub	a4,a7,t5
	li	a3,15
	add	a0,t4,a0
	mv	a6,a5
	bgtu	a4,a3,.L46
	addi	a6,sp,16
	li	s7,64
.L46:
#APP
# 651 "/home/moyamryia/Projects/riscv-accl/lab/k1-quick-screen-final-20261011/ime-schedule.cpp" 1
	vsetvli            t0, zero, e32, m8           
	vxor.vv            v24, v24, v24               
	addi               t3, s11, 0       
	vsetvli            t0, zero, e8, m1            
	li                 s1, 24                      
	vmv.v.i            v1, 3                       
	vsetvli            t0, s1, e8, m1              
	vmv.v.i            v1, 2                       
	vsetvli            t0, zero, e8, mf2           
	vmv.v.i            v1, 1                       
	vsetvli            t0, zero, e8, mf4           
	vmv.v.i            v1, 0                       
	addi               a1, s8, 0                 
	addi               s1, a0, 0                 
	BLOCK_COUNTK_LOOP392:                           
	addi               s5, s1, 0                   
	addi               s6, s1, 32                  
	addi               s1, s6, 16                  
	addi               s2, s1, 32                  
	addi               s3, s1, 32*2                
	addi               s4, s1, 32*3                
	vsetvli            t0, zero, e32, m8           
	vxor.vv            v16, v16, v16               
	flw                f1, (a1)                    
	flw                f2, 4(a1)                   
	flw                f3, 8(a1)                   
	flw                f4, 12(a1)                  
	addi               a1, a1, 16                  
	addi               t2, s9, 0             
	vsetvli      t0, zero, e8, mf2       
	vle8.v       v11, (s6)               
	vsetvli      t0, zero, e8, m1        
	vrgather.vv  v12, v11, v1            
	vadd.vi      v1, v1, 4               
	vrgather.vv  v13, v11, v1            
	vadd.vi      v1, v1, 4               
	vrgather.vv  v14, v11, v1            
	vadd.vi      v1, v1, 4               
	vrgather.vv  v15, v11, v1            
	vadd.vi      v1, v1, -12             
	BLOCK_INNER_LOOP392:                            
	vsetvli      t0, zero, e8, m1        
	vle8.v       v6, (s1)                
	addi         s1, s1, 32*4            
	vle8.v       v7, (s2)                
	addi         s2, s2, 32*4            
	vle8.v       v8, (s3)                
	addi         s3, s3, 32*4            
	vle8.v       v9, (s4)                
	addi         s4, s4, 32*4            
	vand.vi      v2, v6, 15              
	vand.vi      v3, v7, 15              
	vand.vi      v4, v8, 15              
	vand.vi      v5, v9, 15              
	vsrl.vi      v6, v6, 4               
	vsrl.vi      v7, v7, 4               
	vsrl.vi      v8, v8, 4               
	vsrl.vi      v9, v9, 4               
	vle8.v             v10, (a1)                   
	addi               a1, a1, 32                  
	vle8.v             v11, (a1)                   
	addi               a1, a1, 32                  
	vsub.vv            v2, v2, v12                 
	vsub.vv            v6, v6, v12                 
	vsub.vv            v3, v3, v13                 
	vsub.vv            v7, v7, v13                 
	vsub.vv            v4, v4, v14                 
	vsub.vv            v8, v8, v14                 
	vsub.vv            v5, v5, v15                 
	vsub.vv            v9, v9, v15                 
	vmadot       v16, v10, v2            
	vmadot       v18, v10, v3            
	vmadot       v20, v10, v4            
	vmadot       v22, v10, v5            
	vmadot       v16, v11, v6            
	vmadot       v18, v11, v7            
	vmadot       v20, v11, v8            
	vmadot       v22, v11, v9            
	addi               t2, t2, -1                  
	bnez               t2, BLOCK_INNER_LOOP392      
	addi         s2, s5, -8              
	addi         s3, s5, 8               
	addi         s4, s5, 16              
	addi         s6, s5, 24              
	li           t1, 0xf0                
	vmv.s.x      v0, t1                  
	vsetvli      t0, zero, e16, mf4      
	vle16.v      v9, (s5)                
	vle16.v      v11, (s3)               
	vle16.v      v13, (s4)               
	vle16.v      v15, (s6)               
	vsetvli      t0, zero, e16, mf2      
	vle16.v      v9, (s2), v0.t          
	vle16.v      v11, (s5), v0.t         
	vle16.v      v13, (s3), v0.t         
	vle16.v      v15, (s4), v0.t         
	vfwcvt.f.f.v v4, v9                  
	vfwcvt.f.f.v v5, v11                 
	vfwcvt.f.f.v v6, v13                 
	vfwcvt.f.f.v v7, v15                 
	vsetvli      t0, zero, e32, m1       
	vfmv.v.f     v2, f1                  
	vfmerge.vfm  v2, v2, f2, v0          
	vfmv.v.f     v3, f3                  
	vfmerge.vfm  v3, v3, f4, v0          
	vfmul.vv     v8, v4, v2              
	vfmul.vv     v9, v4, v3              
	vfmul.vv     v10, v5, v2             
	vfmul.vv     v11, v5, v3             
	vfmul.vv     v12, v6, v2             
	vfmul.vv     v13, v6, v3             
	vfmul.vv     v14, v7, v2             
	vfmul.vv     v15, v7, v3             
	vsetvli            t0, zero, e32, m8           
	vfcvt.f.x.v        v16, v16                    
	vfmacc.vv          v24, v16, v8                
	addi               t3, t3, -1                  
	bnez               t3, BLOCK_COUNTK_LOOP392     
	RESULT_SAVE392:                                 
	addi         a1, a6, 0             
	add          a2, a6, s7        
	add          a3, a2, s7          
	add          a4, a3, s7          
	addi         a2, a2, -16             
	addi         a4, a4, -16             
	li           t1, 0xf0                
	vmv.s.x      v0, t1                  
	vsetvli      t0, zero, e32, mf2      
	vse32.v      v24, (a1)               
	addi         a1, a1, 16              
	vse32.v      v25, (a3)               
	addi         a3, a3, 16              
	vse32.v      v26, (a1)               
	addi         a1, a1, 16              
	vse32.v      v27, (a3)               
	addi         a3, a3, 16              
	vse32.v      v28, (a1)               
	addi         a1, a1, 16              
	vse32.v      v29, (a3)               
	addi         a3, a3, 16              
	vse32.v      v30, (a1)               
	vse32.v      v31, (a3)               
	vsetvli      t0, zero, e32, m1       
	vse32.v      v24, (a2), v0.t         
	addi         a2, a2, 16              
	vse32.v      v25, (a4), v0.t         
	addi         a4, a4, 16              
	vse32.v      v26, (a2), v0.t         
	addi         a2, a2, 16              
	vse32.v      v27, (a4), v0.t         
	addi         a4, a4, 16              
	vse32.v      v28, (a2), v0.t         
	addi         a2, a2, 16              
	vse32.v      v29, (a4), v0.t         
	addi         a4, a4, 16              
	vse32.v      v30, (a2), v0.t         
	vse32.v      v31, (a4), v0.t         
	
# 0 "" 2
#NO_APP
	ld	a4,8(sp)
	addi	t5,t5,16
	add	s0,s0,s10
	add	t6,t6,a4
	addi	a5,a5,64
	bgtu	a7,t5,.L47
.L98:
	ld	s0,368(sp)
	.cfi_restore 8
	ld	s1,360(sp)
	.cfi_restore 9
	ld	s2,352(sp)
	.cfi_restore 18
	ld	s3,344(sp)
	.cfi_restore 19
	ld	s4,336(sp)
	.cfi_restore 20
	ld	s5,328(sp)
	.cfi_restore 21
	ld	s6,320(sp)
	.cfi_restore 22
	ld	s7,312(sp)
	.cfi_restore 23
	ld	s9,296(sp)
	.cfi_restore 25
	ld	s10,288(sp)
	.cfi_restore 26
.L48:
	ld	ra,376(sp)
	.cfi_remember_state
	.cfi_restore 1
	ld	s8,304(sp)
	.cfi_restore 24
	ld	s11,280(sp)
	.cfi_restore 27
	li	a0,4
	addi	sp,sp,384
	.cfi_def_cfa_offset 0
	jr	ra
.L101:
	.cfi_restore_state
	addi	a4,a6,-1
	seqz	a4,a4
	snez	a2,a7
	and	a4,a4,a2
	beq	a4,zero,.L37
	bne	s11,zero,.L42
	sd	s0,368(sp)
	sd	s1,360(sp)
	sd	s2,352(sp)
	sd	s3,344(sp)
	sd	s4,336(sp)
	sd	s5,328(sp)
	sd	s6,320(sp)
	sd	s7,312(sp)
	sd	s9,296(sp)
	.cfi_offset 8, -16
	.cfi_offset 9, -24
	.cfi_offset 18, -32
	.cfi_offset 19, -40
	.cfi_offset 20, -48
	.cfi_offset 21, -56
	.cfi_offset 22, -64
	.cfi_offset 23, -72
	.cfi_offset 25, -88
.L43:
	mul	a1,a1,s11
	slli	s9,s11,5
	li	s0,0
	li	t2,0
	li	t1,0
	li	s7,16
	slli	a0,a1,4
.L56:
	srli	a3,t2,1
	add	a3,a3,s0
	sub	a4,a7,t1
	add	a3,t4,a3
	mv	a2,s11
	bleu	a4,s7,.L55
	li	a4,16
.L55:
#APP
# 941 "/home/moyamryia/Projects/riscv-accl/lab/k1-quick-screen-final-20261011/ime-schedule.cpp" 1
	vsetvli      t0, zero, e32, m4       
	vxor.vv      v28, v28, v28           
	addi         s1, a3, 0             
	addi         s2, a3, 8             
	addi         s3, a3, 16            
	addi         s4, a3, 24            
	addi         s5, s8, 0             
	addi         s6, s8, 12            
	LOOP_K489:                            
	vsetvli      t0, zero, e16, mf4      
	vle16.v      v4, (s1)                
	addi         s1, s1, 32              
	vle16.v      v5, (s2)                
	addi         s2, s2, 56              
	vle16.v      v6, (s3)                
	addi         s3, s3, 80              
	vle16.v      v7, (s4)                
	addi         s4, s4, 104             
	flw          f1, (s5)                
	addi         s5, s5, 4               
	vfwcvt.f.f.v v8, v4                  
	vfwcvt.f.f.v v9, v5                  
	vfwcvt.f.f.v v10, v6                 
	vfwcvt.f.f.v v11, v7                 
	vsetvli      t0, zero, e32, mf2      
	addi         t5, t6, 0         
	vxor.vv      v16, v16, v16           
	vxor.vv      v18, v18, v18           
	vxor.vv      v20, v20, v20           
	vxor.vv      v22, v22, v22           
	vfmul.vf     v24, v8, f1             
	vfmul.vf     v25, v9, f1             
	vfmul.vf     v26, v10, f1            
	vfmul.vf     v27, v11, f1            
	addi         a2, a2, -1      
	vsetvli      t0, zero, e8, m1        
	LOOP_INNER489:                        
	vle8.v       v4, (s1)                
	addi         s1, s1, 128             
	vle8.v       v5, (s2)                
	addi         s2, s2, 128             
	vle8.v       v6, (s3)                
	addi         s3, s3, 128             
	vle8.v       v7, (s4)                
	addi         s4, s4, 128             
	vsetvli      t0, zero, e8, mf4       
	vle8.v       v14, (s5)               
	addi         s5, s5, 16              
	vle8.v       v15, (s6)               
	addi         s6, s6, 16              
	addi         t5, t5, -1              
	vsetvli      t0, zero, e8, m1        
	vand.vi      v0, v4, 15              
	vand.vi      v1, v5, 15              
	vand.vi      v2, v6, 15              
	vand.vi      v3, v7, 15              
	vsrl.vi      v4, v4, 4               
	vsrl.vi      v5, v5, 4               
	vsrl.vi      v6, v6, 4               
	vsrl.vi      v7, v7, 4               
	vadd.vi      v0, v0, -8              
	vadd.vi      v1, v1, -8              
	vadd.vi      v2, v2, -8              
	vadd.vi      v3, v3, -8              
	vadd.vi      v4, v4, -8              
	vadd.vi      v5, v5, -8              
	vadd.vi      v6, v6, -8              
	vadd.vi      v7, v7, -8              
	vmadot       v16, v14, v0            
	vmadot       v18, v14, v1            
	vmadot       v20, v14, v2            
	vmadot       v22, v14, v3            
	vmadot       v16, v15, v4            
	vmadot       v18, v15, v5            
	vmadot       v20, v15, v6            
	vmadot       v22, v15, v7            
	bnez         t5, LOOP_INNER489        
	vsetvli      t0, zero, e32, mf2      
	vfcvt.f.x.v  v16,  v16               
	vfcvt.f.x.v  v18,  v18               
	vfcvt.f.x.v  v20,  v20               
	vfcvt.f.x.v  v22,  v22               
	addi         s2, s1, 8               
	addi         s3, s1, 16              
	addi         s4, s1, 24              
	addi         s6, s5, 12              
	vfmacc.vv    v28, v16, v24           
	vfmacc.vv    v29, v18, v25           
	vfmacc.vv    v30, v20, v26           
	vfmacc.vv    v31, v22, v27           
	bnez         a2, LOOP_K489        
	addi         t3, zero, 16            
	addi         s1, a5, 16            
	addi         s2, a5, 32            
	addi         s3, a5, 48            
	blt          a4, t3, ST_TAIL489 
	vse32.v      v28, (a5)             
	vse32.v      v29, (s1)               
	vse32.v      v30, (s2)               
	vse32.v      v31, (s3)               
	jal          x0, END489               
	ST_TAIL489:                           
	vsetvli      t0, a4, e32, mf2  
	sub          a4, a4, t0  
	vse32.v      v28, (a5)             
	vsetvli      t0, a4, e32, mf2  
	sub          a4, a4, t0  
	vse32.v      v29, (s1)               
	vsetvli      t0, a4, e32, mf2  
	sub          a4, a4, t0  
	vse32.v      v30, (s2)               
	vsetvli      t0, a4, e32, mf2  
	sub          a4, a4, t0  
	vse32.v      v31, (s3)               
	END489:                               
	
# 0 "" 2
#NO_APP
	addi	t1,t1,16
	add	t2,t2,a0
	add	s0,s0,s9
	addi	a5,a5,64
	bgtu	a7,t1,.L56
	j	.L99
.L100:
	.cfi_restore 8
	.cfi_restore 9
	.cfi_restore 18
	.cfi_restore 19
	.cfi_restore 20
	.cfi_restore 21
	.cfi_restore 22
	.cfi_restore 23
	.cfi_restore 25
	addi	a0,a1,-32
	seqz	a0,a0
	seqz	a2,a4
	and	a2,a2,a0
	beq	a2,zero,.L36
	addi	a4,a6,-1
	seqz	a4,a4
	snez	a2,a7
	and	a4,a4,a2
	beq	a4,zero,.L37
	beq	s11,zero,.L38
	mv	a4,s11
	mv	a3,a7
	mv	a2,a5
	mv	a1,t4
	mv	a0,s8
	call	_ZN16spacemit_kernels12_GLOBAL__N_1L22quick_m1_load_scheduleEmPKhS2_Pfmmm.constprop.0
	j	.L39
.L37:
	li	a4,3
	bgtu	a6,a4,.L40
.L41:
	beq	a7,zero,.L39
.L38:
	sd	s0,368(sp)
	sd	s1,360(sp)
	sd	s2,352(sp)
	sd	s3,344(sp)
	sd	s4,336(sp)
	sd	s5,328(sp)
	sd	s6,320(sp)
	sd	s7,312(sp)
	sd	s9,296(sp)
	srli	t6,a1,4
	.cfi_remember_state
	.cfi_offset 8, -16
	.cfi_offset 9, -24
	.cfi_offset 18, -32
	.cfi_offset 19, -40
	.cfi_offset 20, -48
	.cfi_offset 21, -56
	.cfi_offset 22, -64
	.cfi_offset 23, -72
	.cfi_offset 25, -88
	j	.L43
.L40:
	.cfi_restore_state
	beq	a7,zero,.L48
	mul	a4,a1,s11
	ld	a3,392(sp)
	sd	s0,368(sp)
	sd	s7,312(sp)
	slli	t5,a3,2
	slli	a3,s11,5
	sd	s9,296(sp)
	sd	s10,288(sp)
	sd	s1,360(sp)
	sd	s2,352(sp)
	sd	s3,344(sp)
	sd	s4,336(sp)
	sd	s5,328(sp)
	sd	s6,320(sp)
	.cfi_offset 8, -16
	.cfi_offset 23, -72
	.cfi_offset 25, -88
	.cfi_offset 26, -96
	.cfi_offset 9, -24
	.cfi_offset 18, -32
	.cfi_offset 19, -40
	.cfi_offset 20, -48
	.cfi_offset 21, -56
	.cfi_offset 22, -64
	srli	s10,a1,4
	sd	a3,8(sp)
	li	s0,0
	li	a0,0
	li	s7,0
	slli	s9,a4,4
.L51:
	srli	a6,a0,1
	add	a6,a6,s0
	sub	a4,a7,s7
	li	a3,15
	add	a6,t4,a6
	mv	t6,a5
	bgtu	a4,a3,.L50
	addi	t6,sp,16
	li	t5,64
.L50:
#APP
# 740 "/home/moyamryia/Projects/riscv-accl/lab/k1-quick-screen-final-20261011/ime-schedule.cpp" 1
	vsetvli            t0, zero, e32, m8           
	vxor.vv            v24, v24, v24               
	addi               t3, s11, 0       
	addi               a1, s8, 0                 
	addi               s1, a6, 0                 
	BLOCK_COUNTK_LOOP615:                           
	addi               s5, s1, 0                   
	addi               s1, s5, 32                  
	addi               s2, s1, 32                  
	addi               s3, s1, 32*2                
	addi               s4, s1, 32*3                
	vsetvli            t0, zero, e32, m8           
	vxor.vv            v16, v16, v16               
	flw                f1, (a1)                    
	flw                f2, 4(a1)                   
	flw                f3, 8(a1)                   
	flw                f4, 12(a1)                  
	addi               a1, a1, 16                  
	addi               t2, s10, 0             
	BLOCK_INNER_LOOP615:                            
	vsetvli      t0, zero, e8, m1        
	vle8.v       v6, (s1)                
	addi         s1, s1, 32*4            
	vle8.v       v7, (s2)                
	addi         s2, s2, 32*4            
	vle8.v       v8, (s3)                
	addi         s3, s3, 32*4            
	vle8.v       v9, (s4)                
	addi         s4, s4, 32*4            
	vand.vi      v2, v6, 15              
	vand.vi      v3, v7, 15              
	vand.vi      v4, v8, 15              
	vand.vi      v5, v9, 15              
	vsrl.vi      v6, v6, 4               
	vsrl.vi      v7, v7, 4               
	vsrl.vi      v8, v8, 4               
	vsrl.vi      v9, v9, 4               
	vsetvli            t0, zero, e8, m1            
	vle8.v             v10, (a1)                   
	addi               a1, a1, 32                  
	vle8.v             v11, (a1)                   
	addi               a1, a1, 32                  
	vadd.vi            v2, v2, -8                  
	vadd.vi            v3, v3, -8                  
	vadd.vi            v4, v4, -8                  
	vadd.vi            v5, v5, -8                  
	vadd.vi            v6, v6, -8                  
	vadd.vi            v7, v7, -8                  
	vadd.vi            v8, v8, -8                  
	vadd.vi            v9, v9, -8                  
	vmadot       v16, v10, v2            
	vmadot       v18, v10, v3            
	vmadot       v20, v10, v4            
	vmadot       v22, v10, v5            
	vmadot       v16, v11, v6            
	vmadot       v18, v11, v7            
	vmadot       v20, v11, v8            
	vmadot       v22, v11, v9            
	addi               t2, t2, -1                  
	bnez               t2, BLOCK_INNER_LOOP615      
	addi         s2, s5, -8              
	addi         s3, s5, 8               
	addi         s4, s5, 16              
	addi         s6, s5, 24              
	li           t1, 0xf0                
	vmv.s.x      v0, t1                  
	vsetvli      t0, zero, e16, mf4      
	vle16.v      v9, (s5)                
	vle16.v      v11, (s3)               
	vle16.v      v13, (s4)               
	vle16.v      v15, (s6)               
	vsetvli      t0, zero, e16, mf2      
	vle16.v      v9, (s2), v0.t          
	vle16.v      v11, (s5), v0.t         
	vle16.v      v13, (s3), v0.t         
	vle16.v      v15, (s4), v0.t         
	vfwcvt.f.f.v v4, v9                  
	vfwcvt.f.f.v v5, v11                 
	vfwcvt.f.f.v v6, v13                 
	vfwcvt.f.f.v v7, v15                 
	vsetvli      t0, zero, e32, m1       
	vfmv.v.f     v2, f1                  
	vfmerge.vfm  v2, v2, f2, v0          
	vfmv.v.f     v3, f3                  
	vfmerge.vfm  v3, v3, f4, v0          
	vfmul.vv     v8, v4, v2              
	vfmul.vv     v9, v4, v3              
	vfmul.vv     v10, v5, v2             
	vfmul.vv     v11, v5, v3             
	vfmul.vv     v12, v6, v2             
	vfmul.vv     v13, v6, v3             
	vfmul.vv     v14, v7, v2             
	vfmul.vv     v15, v7, v3             
	vsetvli            t0, zero, e32, m8           
	vfcvt.f.x.v        v16, v16                    
	vfmacc.vv          v24, v16, v8                
	addi               t3, t3, -1                  
	bnez               t3, BLOCK_COUNTK_LOOP615     
	RESULT_SAVE615:                                 
	addi         a1, t6, 0             
	add          a2, t6, t5        
	add          a3, a2, t5          
	add          a4, a3, t5          
	addi         a2, a2, -16             
	addi         a4, a4, -16             
	li           t1, 0xf0                
	vmv.s.x      v0, t1                  
	vsetvli      t0, zero, e32, mf2      
	vse32.v      v24, (a1)               
	addi         a1, a1, 16              
	vse32.v      v25, (a3)               
	addi         a3, a3, 16              
	vse32.v      v26, (a1)               
	addi         a1, a1, 16              
	vse32.v      v27, (a3)               
	addi         a3, a3, 16              
	vse32.v      v28, (a1)               
	addi         a1, a1, 16              
	vse32.v      v29, (a3)               
	addi         a3, a3, 16              
	vse32.v      v30, (a1)               
	vse32.v      v31, (a3)               
	vsetvli      t0, zero, e32, m1       
	vse32.v      v24, (a2), v0.t         
	addi         a2, a2, 16              
	vse32.v      v25, (a4), v0.t         
	addi         a4, a4, 16              
	vse32.v      v26, (a2), v0.t         
	addi         a2, a2, 16              
	vse32.v      v27, (a4), v0.t         
	addi         a4, a4, 16              
	vse32.v      v28, (a2), v0.t         
	addi         a2, a2, 16              
	vse32.v      v29, (a4), v0.t         
	addi         a4, a4, 16              
	vse32.v      v30, (a2), v0.t         
	vse32.v      v31, (a4), v0.t         
	
# 0 "" 2
#NO_APP
	ld	a4,8(sp)
	addi	s7,s7,16
	add	a0,a0,s9
	add	s0,s0,a4
	addi	a5,a5,64
	bgtu	a7,s7,.L51
	j	.L98
.L42:
	.cfi_restore 8
	.cfi_restore 9
	.cfi_restore 18
	.cfi_restore 19
	.cfi_restore 20
	.cfi_restore 21
	.cfi_restore 22
	.cfi_restore 23
	.cfi_restore 25
	.cfi_restore 26
	mv	a4,s11
	mv	a3,a7
	mv	a2,a5
	mv	a1,t4
	mv	a0,s8
	call	_ZN16spacemit_kernels12_GLOBAL__N_1L15k1_m1_k32_fixedEmPKhS2_Pfmmm.constprop.0
	j	.L39
	.cfi_endproc
.LFE3593:
	.size	spine_k1_ime_m1_test, .-spine_k1_ime_m1_test
	.section	.rodata.str1.8,"aMS",@progbits,1
	.align	3
.LC2:
	.string	"SPINE_QUICK_IME_SCHEDULE"
	.align	3
.LC3:
	.string	"SPINE_QUICK_IME_SCHEDULE: mode=%d Q4_0 M1 K32 enabled\n"
	.text
	.align	1
	.globl	_ZN16spacemit_kernels4ime116gemm_kernel_i8i4EmPKhS2_S2_Pfmmmm
	.type	_ZN16spacemit_kernels4ime116gemm_kernel_i8i4EmPKhS2_S2_Pfmmmm, @function
_ZN16spacemit_kernels4ime116gemm_kernel_i8i4EmPKhS2_S2_Pfmmmm:
.LFB3594:
	.cfi_startproc
	addi	sp,sp,-96
	.cfi_def_cfa_offset 96
	mv	t3,a1
	mv	t1,a0
	mv	t4,a2
	lla	a1,.LANCHOR0
	sd	ra,88(sp)
	.cfi_offset 1, -8
	lb	a2,0(a1)
	fence	r,rw
	andi	a2,a2,0xff
	beq	a2,zero,.L123
.L104:
	addi	a2,t1,-32
	seqz	a2,a2
	seqz	a0,a3
	and	a2,a2,a0
	beq	a2,zero,.L108
	addi	a2,a5,-1
	snez	a0,a6
	seqz	a2,a2
	and	a2,a2,a0
	snez	a0,a7
	and	a2,a0,a2
	bne	a2,zero,.L124
.L108:
	ld	a2,96(sp)
	lw	a0,.LANCHOR0+8
	sd	a7,0(sp)
	sd	a2,8(sp)
	mv	a7,a6
	mv	a2,t3
	mv	a6,a5
	mv	a1,t1
	mv	a5,a4
	mv	a4,a3
	mv	a3,t4
	call	spine_k1_ime_m1_test@plt
	ld	ra,88(sp)
	.cfi_remember_state
	.cfi_restore 1
	addi	sp,sp,96
	.cfi_def_cfa_offset 0
	jr	ra
.L123:
	.cfi_restore_state
	sd	a0,16(sp)
	mv	a0,a1
	sd	a7,72(sp)
	sd	a6,64(sp)
	sd	a5,56(sp)
	sd	a4,48(sp)
	sd	a3,40(sp)
	sd	t4,32(sp)
	sd	t3,24(sp)
	call	__cxa_guard_acquire@plt
	ld	t1,16(sp)
	ld	t3,24(sp)
	ld	t4,32(sp)
	ld	a3,40(sp)
	ld	a4,48(sp)
	ld	a5,56(sp)
	ld	a6,64(sp)
	ld	a7,72(sp)
	lla	a1,.LANCHOR0
	beq	a0,zero,.L104
	lla	a0,.LC2
	call	getenv@plt
	ld	t1,16(sp)
	ld	t3,24(sp)
	ld	t4,32(sp)
	ld	a3,40(sp)
	ld	a4,48(sp)
	ld	a5,56(sp)
	ld	a6,64(sp)
	ld	a7,72(sp)
	li	a2,0
	lla	a1,.LANCHOR0
	beq	a0,zero,.L105
	lbu	t5,0(a0)
	addiw	t6,t5,-50
	mv	a2,t6
	beq	t6,zero,.L125
.L106:
	sext.w	t6,a2
	li	a2,2
	beq	t6,zero,.L105
	addiw	t5,t5,-49
	sext.w	a2,t5
	bne	t5,zero,.L107
	lbu	a2,1(a0)
.L107:
	seqz	a2,a2
.L105:
	lla	a0,.LANCHOR0
	sd	a7,72(sp)
	sd	a6,64(sp)
	sd	a5,56(sp)
	sd	a4,48(sp)
	sd	a3,40(sp)
	sd	t4,32(sp)
	sd	t3,24(sp)
	sd	t1,16(sp)
	sw	a2,8(a1)
	call	__cxa_guard_release@plt
	ld	a7,72(sp)
	ld	a6,64(sp)
	ld	a5,56(sp)
	ld	a4,48(sp)
	ld	a3,40(sp)
	ld	t4,32(sp)
	ld	t3,24(sp)
	ld	t1,16(sp)
	lla	a1,.LANCHOR0
	j	.L104
.L124:
	addi	a2,a1,16
	lb	a2,0(a2)
	andi	a2,a2,0xff
	bne	a2,zero,.L108
	lla	a0,.LANCHOR0+16
	andi	a1,a0,3
	slliw	a1,a1,3
	li	a2,255
	li	t5,1
	sllw	a2,a2,a1
	sllw	t5,t5,a1
	andi	a0,a0,-4
	not	t6,a2
	and	t5,t5,a2
	1:
	lr.w	a2, 0(a0)
	and	t0, a2, t6
	or	t0, t0, t5
	sc.w	t0, t0, 0(a0)
	bnez	t0, 1b
	sraw	a2,a2,a1
	andi	a2,a2,0xff
	bne	a2,zero,.L108
	la	a2,stderr
	ld	a0,0(a2)
	lw	a2,.LANCHOR0+8
	lla	a1,.LC3
	sd	a7,72(sp)
	sd	a6,64(sp)
	sd	a5,56(sp)
	sd	a4,48(sp)
	sd	a3,40(sp)
	sd	t4,32(sp)
	sd	t3,24(sp)
	sd	t1,16(sp)
	call	fprintf@plt
	ld	a7,72(sp)
	ld	a6,64(sp)
	ld	a5,56(sp)
	ld	a4,48(sp)
	ld	a3,40(sp)
	ld	t4,32(sp)
	ld	t3,24(sp)
	ld	t1,16(sp)
	j	.L108
.L125:
	lbu	a2,1(a0)
	j	.L106
	.cfi_endproc
.LFE3594:
	.size	_ZN16spacemit_kernels4ime116gemm_kernel_i8i4EmPKhS2_S2_Pfmmmm, .-_ZN16spacemit_kernels4ime116gemm_kernel_i8i4EmPKhS2_S2_Pfmmmm
	.section	.rodata.str1.8
	.align	3
.LC4:
	.string	"CountN % 16 == 0"
	.align	3
.LC5:
	.string	"GGML_ASSERT(%s) failed"
	.align	3
.LC6:
	.string	"/home/moyamryia/Projects/riscv-accl/lab/k1-quick-screen-final-20261011/ime-schedule.cpp"
	.text
	.align	1
	.globl	_ZN16spacemit_kernels4ime116gemm_kernel_i8i8EmPKhS2_S2_Pfmmmm
	.type	_ZN16spacemit_kernels4ime116gemm_kernel_i8i8EmPKhS2_S2_Pfmmmm, @function
_ZN16spacemit_kernels4ime116gemm_kernel_i8i8EmPKhS2_S2_Pfmmmm:
.LFB3601:
	.cfi_startproc
	addi	sp,sp,-80
	.cfi_def_cfa_offset 80
	sd	ra,72(sp)
	li	a3,3
	mv	t4,a1
	mv	t6,a2
	.cfi_offset 1, -8
	bgtu	a5,a3,.L145
	srli	a0,a0,4
	li	a2,0
	li	t2,16
	beq	a6,zero,.L136
	sd	s1,56(sp)
	sd	s2,48(sp)
	sd	s3,40(sp)
	sd	s4,32(sp)
	sd	s5,24(sp)
	sd	s6,16(sp)
	sd	s7,8(sp)
	.cfi_offset 9, -24
	.cfi_offset 18, -32
	.cfi_offset 19, -40
	.cfi_offset 20, -48
	.cfi_offset 21, -56
	.cfi_offset 22, -64
	.cfi_offset 23, -72
.L135:
	sub	a3,a6,a2
	bleu	a3,t2,.L134
	li	a3,16
.L134:
	srli	a1,a2,4
	mul	a1,a1,a7
	mv	t1,a7
	slli	a5,a1,4
	add	a5,a5,a1
	slli	a5,a5,5
	add	a5,t6,a5
#APP
# 1443 "/home/moyamryia/Projects/riscv-accl/lab/k1-quick-screen-final-20261011/ime-schedule.cpp" 1
	vsetvli      t0, zero, e32, m4       
	vxor.vv      v28, v28, v28           
	addi         s7, a5, 0             
	addi         s5, t4, 0             
	addi         s6, t4, 12            
	LOOP_K893:                            
	addi         s1, s7, 32              
	addi         s2, s7, 8               
	addi         s3, s7, 16              
	addi         s4, s7, 24              
	vsetvli      t0, zero, e16, mf4      
	vle16.v      v4, (s7)                
	vle16.v      v5, (s2)                
	vle16.v      v6, (s3)                
	vle16.v      v7, (s4)                
	addi         s7, s7, 544             
	flw          f1, (s5)                
	addi         s5, s5, 4               
	vfwcvt.f.f.v v8, v4                  
	vfwcvt.f.f.v v9, v5                  
	vfwcvt.f.f.v v10, v6                 
	vfwcvt.f.f.v v11, v7                 
	vsetvli      t0, zero, e32, mf2      
	addi         t5, a0, 0         
	vxor.vv      v16, v16, v16           
	vxor.vv      v18, v18, v18           
	vxor.vv      v20, v20, v20           
	vxor.vv      v22, v22, v22           
	vfmul.vf     v24, v8, f1             
	vfmul.vf     v25, v9, f1             
	vfmul.vf     v26, v10, f1            
	vfmul.vf     v27, v11, f1            
	addi         t1, t1, -1      
	vsetvli      t0, zero, e8, m1        
	LOOP_INNER893:                        
	vle8.v       v0, (s1)                
	addi         s1, s1, 32              
	vle8.v       v1, (s1)                
	addi         s1, s1, 32              
	vle8.v       v2, (s1)                
	addi         s1, s1, 32              
	vle8.v       v3, (s1)                
	addi         s1, s1, 32              
	vle8.v       v4, (s1)                
	addi         s1, s1, 32              
	vle8.v       v5, (s1)                
	addi         s1, s1, 32              
	vle8.v       v6, (s1)                
	addi         s1, s1, 32              
	vle8.v       v7, (s1)                
	addi         s1, s1, 32              
	vsetvli      t0, zero, e8, mf4       
	vle8.v       v14, (s5)               
	addi         s5, s5, 16              
	vle8.v       v15, (s6)               
	addi         s6, s6, 16              
	addi         t5, t5, -1              
	vsetvli      t0, zero, e8, m1        
	vmadot       v16, v14, v0            
	vmadot       v18, v14, v1            
	vmadot       v20, v14, v2            
	vmadot       v22, v14, v3            
	vmadot       v16, v15, v4            
	vmadot       v18, v15, v5            
	vmadot       v20, v15, v6            
	vmadot       v22, v15, v7            
	bnez         t5, LOOP_INNER893        
	vsetvli      t0, zero, e32, mf2      
	vfcvt.f.x.v  v16,  v16               
	vfcvt.f.x.v  v18,  v18               
	vfcvt.f.x.v  v20,  v20               
	vfcvt.f.x.v  v22,  v22               
	addi         s2, s1, 8               
	addi         s3, s1, 16              
	addi         s4, s1, 24              
	addi         s6, s5, 12              
	vfmacc.vv    v28, v16, v24           
	vfmacc.vv    v29, v18, v25           
	vfmacc.vv    v30, v20, v26           
	vfmacc.vv    v31, v22, v27           
	bnez         t1, LOOP_K893        
	addi         t3, zero, 16            
	addi         s1, a4, 16            
	addi         s2, a4, 32            
	addi         s3, a4, 48            
	blt          a3, t3, ST_TAIL893 
	vse32.v      v28, (a4)             
	vse32.v      v29, (s1)               
	vse32.v      v30, (s2)               
	vse32.v      v31, (s3)               
	jal          x0, END893               
	ST_TAIL893:                           
	vsetvli      t0, a3, e32, mf2  
	sub          a3, a3, t0  
	vse32.v      v28, (a4)             
	vsetvli      t0, a3, e32, mf2  
	sub          a3, a3, t0  
	vse32.v      v29, (s1)               
	vsetvli      t0, a3, e32, mf2  
	sub          a3, a3, t0  
	vse32.v      v30, (s2)               
	vsetvli      t0, a3, e32, mf2  
	sub          a3, a3, t0  
	vse32.v      v31, (s3)               
	END893:                               
	
# 0 "" 2
#NO_APP
	addi	a2,a2,16
	addi	a4,a4,64
	bgtu	a6,a2,.L135
	ld	s1,56(sp)
	.cfi_restore 9
	ld	s2,48(sp)
	.cfi_restore 18
	ld	s3,40(sp)
	.cfi_restore 19
	ld	s4,32(sp)
	.cfi_restore 20
	ld	s5,24(sp)
	.cfi_restore 21
	ld	s6,16(sp)
	.cfi_restore 22
	ld	s7,8(sp)
	.cfi_restore 23
.L136:
	ld	ra,72(sp)
	.cfi_remember_state
	.cfi_restore 1
	li	a0,1
	addi	sp,sp,80
	.cfi_def_cfa_offset 0
	jr	ra
.L145:
	.cfi_restore_state
	sd	s7,8(sp)
	sd	s0,64(sp)
	.cfi_offset 23, -72
	.cfi_offset 8, -16
	andi	s7,a6,15
	bne	s7,zero,.L146
	mv	a5,a4
	ld	a4,80(sp)
	srli	a0,a0,4
	slli	s0,a4,2
	beq	a6,zero,.L132
	sd	s1,56(sp)
	sd	s2,48(sp)
	sd	s3,40(sp)
	sd	s4,32(sp)
	sd	s5,24(sp)
	sd	s6,16(sp)
	.cfi_offset 9, -24
	.cfi_offset 18, -32
	.cfi_offset 19, -40
	.cfi_offset 20, -48
	.cfi_offset 21, -56
	.cfi_offset 22, -64
.L131:
	srli	a4,s7,4
	mul	a4,a4,a7
	slli	t5,a4,4
	add	t5,t5,a4
	slli	t5,t5,5
	add	t5,t6,t5
#APP
# 1354 "/home/moyamryia/Projects/riscv-accl/lab/k1-quick-screen-final-20261011/ime-schedule.cpp" 1
	vsetvli            t0, zero, e32, m8           
	vxor.vv            v24, v24, v24               
	addi               t3, a7, 0       
	addi               a1, t4, 0                 
	addi               s1, t5, 0                 
	BLOCK_COUNTK_LOOP961:                           
	addi               s5, s1, 0                   
	addi               s1, s5, 32                  
	vsetvli            t0, zero, e32, m8           
	vxor.vv            v16, v16, v16               
	flw                f1, (a1)                    
	flw                f2, 4(a1)                   
	flw                f3, 8(a1)                   
	flw                f4, 12(a1)                  
	addi               a1, a1, 16                  
	addi               t2, a0, 0             
	BLOCK_INNER_LOOP961:                            
	vsetvli            t0, zero, e8, m1            
	vle8.v             v2, (s1)                    
	addi               s1, s1, 32                  
	vle8.v             v3, (s1)                    
	addi               s1, s1, 32                  
	vle8.v             v4, (s1)                    
	addi               s1, s1, 32                  
	vle8.v             v5, (s1)                    
	addi               s1, s1, 32                  
	vle8.v             v6, (s1)                    
	addi               s1, s1, 32                  
	vle8.v             v7, (s1)                    
	addi               s1, s1, 32                  
	vle8.v             v8, (s1)                    
	addi               s1, s1, 32                  
	vle8.v             v9, (s1)                    
	addi               s1, s1, 32                  
	vle8.v             v10, (a1)                   
	addi               a1, a1, 32                  
	vle8.v             v11, (a1)                   
	addi               a1, a1, 32                  
	vmadot       v16, v10, v2            
	vmadot       v18, v10, v3            
	vmadot       v20, v10, v4            
	vmadot       v22, v10, v5            
	vmadot       v16, v11, v6            
	vmadot       v18, v11, v7            
	vmadot       v20, v11, v8            
	vmadot       v22, v11, v9            
	addi               t2, t2, -1                  
	bnez               t2, BLOCK_INNER_LOOP961      
	addi         s2, s5, -8              
	addi         s3, s5, 8               
	addi         s4, s5, 16              
	addi         s6, s5, 24              
	li           t1, 0xf0                
	vmv.s.x      v0, t1                  
	vsetvli      t0, zero, e16, mf4      
	vle16.v      v9, (s5)                
	vle16.v      v11, (s3)               
	vle16.v      v13, (s4)               
	vle16.v      v15, (s6)               
	vsetvli      t0, zero, e16, mf2      
	vle16.v      v9, (s2), v0.t          
	vle16.v      v11, (s5), v0.t         
	vle16.v      v13, (s3), v0.t         
	vle16.v      v15, (s4), v0.t         
	vfwcvt.f.f.v v8, v9                  
	vfwcvt.f.f.v v10, v11                
	vfwcvt.f.f.v v12, v13                
	vfwcvt.f.f.v v14, v15                
	vsetvli      t0, zero, e32, m1       
	vmv.v.v      v9, v8                  
	vmv.v.v      v11, v10                
	vmv.v.v      v13, v12                
	vmv.v.v      v15, v14                
	li           t1, 0xf0                
	vmv.s.x      v0, t1                  
	vsetvli      t0, zero, e32, mf2      
	vfmul.vf     v8, v8, f1              
	vfmul.vf     v10, v10, f1            
	vfmul.vf     v12, v12, f1            
	vfmul.vf     v14, v14, f1            
	vfmul.vf     v9, v9, f3              
	vfmul.vf     v11, v11, f3            
	vfmul.vf     v13, v13, f3            
	vfmul.vf     v15, v15, f3            
	vsetvli      t0, zero, e32, m1       
	vfmul.vf     v8, v8, f2, v0.t        
	vfmul.vf     v10, v10, f2, v0.t      
	vfmul.vf     v12, v12, f2, v0.t      
	vfmul.vf     v14, v14, f2, v0.t      
	vfmul.vf     v9, v9, f4, v0.t        
	vfmul.vf     v11, v11, f4, v0.t      
	vfmul.vf     v13, v13, f4, v0.t      
	vfmul.vf     v15, v15, f4, v0.t      
	vsetvli            t0, zero, e32, m8           
	vfcvt.f.x.v        v16, v16                    
	vfmacc.vv          v24, v16, v8                
	addi               t3, t3, -1                  
	bnez               t3, BLOCK_COUNTK_LOOP961     
	RESULT_SAVE961:                                 
	addi         a1, a5, 0             
	add          a2, a5, s0        
	add          a3, a2, s0          
	add          a4, a3, s0          
	addi         a2, a2, -16             
	addi         a4, a4, -16             
	li           t1, 0xf0                
	vmv.s.x      v0, t1                  
	vsetvli      t0, zero, e32, mf2      
	vse32.v      v24, (a1)               
	addi         a1, a1, 16              
	vse32.v      v25, (a3)               
	addi         a3, a3, 16              
	vse32.v      v26, (a1)               
	addi         a1, a1, 16              
	vse32.v      v27, (a3)               
	addi         a3, a3, 16              
	vse32.v      v28, (a1)               
	addi         a1, a1, 16              
	vse32.v      v29, (a3)               
	addi         a3, a3, 16              
	vse32.v      v30, (a1)               
	vse32.v      v31, (a3)               
	vsetvli      t0, zero, e32, m1       
	vse32.v      v24, (a2), v0.t         
	addi         a2, a2, 16              
	vse32.v      v25, (a4), v0.t         
	addi         a4, a4, 16              
	vse32.v      v26, (a2), v0.t         
	addi         a2, a2, 16              
	vse32.v      v27, (a4), v0.t         
	addi         a4, a4, 16              
	vse32.v      v28, (a2), v0.t         
	addi         a2, a2, 16              
	vse32.v      v29, (a4), v0.t         
	addi         a4, a4, 16              
	vse32.v      v30, (a2), v0.t         
	vse32.v      v31, (a4), v0.t         
	
# 0 "" 2
#NO_APP
	addi	s7,s7,16
	addi	a5,a5,64
	bgtu	a6,s7,.L131
	ld	s1,56(sp)
	.cfi_restore 9
	ld	s2,48(sp)
	.cfi_restore 18
	ld	s3,40(sp)
	.cfi_restore 19
	ld	s4,32(sp)
	.cfi_restore 20
	ld	s5,24(sp)
	.cfi_restore 21
	ld	s6,16(sp)
	.cfi_restore 22
.L132:
	ld	s0,64(sp)
	.cfi_remember_state
	.cfi_restore 8
	ld	ra,72(sp)
	.cfi_restore 1
	ld	s7,8(sp)
	.cfi_restore 23
	li	a0,4
	addi	sp,sp,80
	.cfi_def_cfa_offset 0
	jr	ra
.L146:
	.cfi_restore_state
	lla	a3,.LC4
	lla	a2,.LC5
	li	a1,1344
	lla	a0,.LC6
	sd	s1,56(sp)
	sd	s2,48(sp)
	sd	s3,40(sp)
	sd	s4,32(sp)
	sd	s5,24(sp)
	sd	s6,16(sp)
	.cfi_offset 9, -24
	.cfi_offset 18, -32
	.cfi_offset 19, -40
	.cfi_offset 20, -48
	.cfi_offset 21, -56
	.cfi_offset 22, -64
	call	ggml_abort@plt
	.cfi_endproc
.LFE3601:
	.size	_ZN16spacemit_kernels4ime116gemm_kernel_i8i8EmPKhS2_S2_Pfmmmm, .-_ZN16spacemit_kernels4ime116gemm_kernel_i8i8EmPKhS2_S2_Pfmmmm
	.section	.rodata.cst4,"aM",@progbits,4
	.align	2
.LC0:
	.word	1065353216
	.align	2
.LC1:
	.word	1006699012
	.bss
	.align	3
	.set	.LANCHOR0,. + 0
	.type	_ZGVZN16spacemit_kernels4ime116gemm_kernel_i8i4EmPKhS2_S2_PfmmmmE4mode, @object
	.size	_ZGVZN16spacemit_kernels4ime116gemm_kernel_i8i4EmPKhS2_S2_PfmmmmE4mode, 8
_ZGVZN16spacemit_kernels4ime116gemm_kernel_i8i4EmPKhS2_S2_PfmmmmE4mode:
	.zero	8
	.type	_ZZN16spacemit_kernels4ime116gemm_kernel_i8i4EmPKhS2_S2_PfmmmmE4mode, @object
	.size	_ZZN16spacemit_kernels4ime116gemm_kernel_i8i4EmPKhS2_S2_PfmmmmE4mode, 4
_ZZN16spacemit_kernels4ime116gemm_kernel_i8i4EmPKhS2_S2_PfmmmmE4mode:
	.zero	4
	.zero	4
	.type	_ZZN16spacemit_kernels4ime116gemm_kernel_i8i4EmPKhS2_S2_PfmmmmE6logged, @object
	.size	_ZZN16spacemit_kernels4ime116gemm_kernel_i8i4EmPKhS2_S2_PfmmmmE6logged, 1
_ZZN16spacemit_kernels4ime116gemm_kernel_i8i4EmPKhS2_S2_PfmmmmE6logged:
	.zero	1
	.ident	"GCC: (g6afcc4f6d) 16.1.0"
	.section	.note.GNU-stack,"",@progbits
