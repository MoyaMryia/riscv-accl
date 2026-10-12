.text
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_e1cdc:
ld t3,152(a1)
.Lpc_e1ce0:
c.addi16sp sp,-224
.Lpc_e1ce2:
c.sdsp s10,128(sp)
.Lpc_e1ce4:
lw a4,0(t3)
.Lpc_e1ce8:
ld s10,160(a1)
.Lpc_e1cec:
c.sdsp ra,216(sp)
.Lpc_e1cee:
ld a5,16(t3)
.Lpc_e1cf2:
ld t6,16(s10)
.Lpc_e1cf6:
bne a4,zero,.Lpc_e2262
.Lpc_e1cfa:
lw a4,0(s10)
.Lpc_e1cfe:
bne a4,zero,.Lpc_e2262
.Lpc_e1d02:
ld a4,48(t3)
.Lpc_e1d06:
c.li a2,4
.Lpc_e1d08:
bne a4,a2,.Lpc_e222e
.Lpc_e1d0c:
ld a2,48(s10)
.Lpc_e1d10:
bne a2,a4,.Lpc_e222e
.Lpc_e1d14:
ld a7,24(a1)
.Lpc_e1d18:
c.mv t5,a1
.Lpc_e1d1a:
ld a1,24(t3)
.Lpc_e1d1e:
c.sdsp s8,144(sp)
.Lpc_e1d20:
addi s8,t6,-1
.Lpc_e1d24:
add a4,s8,a7
.Lpc_e1d28:
bne a1,a4,.Lpc_e21fc
.Lpc_e1d2c:
ld a4,24(s10)
.Lpc_e1d30:
bne a5,a4,.Lpc_e21ca
.Lpc_e1d34:
ld a4,16(t5)
.Lpc_e1d38:
bne a5,a4,.Lpc_e21ca
.Lpc_e1d3c:
ld a4,32(t5)
.Lpc_e1d40:
ld a1,32(t3)
.Lpc_e1d44:
bne a1,a4,.Lpc_e2198
.Lpc_e1d48:
ld a1,48(t5)
.Lpc_e1d4c:
bne a1,a2,.Lpc_e2198
.Lpc_e1d50:
c.lw a2,4(a0)
.Lpc_e1d52:
c.lw a3,0(a0)
.Lpc_e1d54:
c.sdsp s11,120(sp)
.Lpc_e1d56:
add t2,a5,a2
.Lpc_e1d5a:
c.addi t2,-1
.Lpc_e1d5c:
div t2,t2,a2
.Lpc_e1d60:
mul s11,a3,t2
.Lpc_e1d64:
c.add t2,s11
.Lpc_e1d66:
blt a5,t2,.Lpc_e2166
.Lpc_e1d6a:
bge zero,a4,.Lpc_e1e28
.Lpc_e1d6e:
srli a5,t6,0x2
.Lpc_e1d72:
vsetivli zero,4,e32,m1,ta,ma
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_e1d76:
c.sdsp s5,168(sp)
.Lpc_e1d78:
slli s5,a5,0x4
.Lpc_e1d7c:
slli a5,s11,0x2
.Lpc_e1d80:
c.sdsp s1,200(sp)
.Lpc_e1d82:
c.sdsp a5,48(sp)
.Lpc_e1d84:
c.li s1,0
.Lpc_e1d86:
andi a5,t6,3
.Lpc_e1d8a:
c.sdsp s0,208(sp)
.Lpc_e1d8c:
c.sdsp s9,136(sp)
.Lpc_e1d8e:
c.sdsp s2,192(sp)
.Lpc_e1d90:
c.sdsp s3,184(sp)
.Lpc_e1d92:
c.sdsp s4,176(sp)
.Lpc_e1d94:
c.sdsp s6,160(sp)
.Lpc_e1d96:
c.sdsp s7,152(sp)
.Lpc_e1d98:
c.li s9,2
.Lpc_e1d9a:
andi s0,t6,-4
.Lpc_e1d9e:
c.sdsp a5,56(sp)
.Lpc_e1da0:
c.mv a3,s1
.Lpc_e1da2:
bge zero,a7,.Lpc_e1e10
.Lpc_e1da6:
ld a4,248(t3)
.Lpc_e1daa:
ld a1,56(t3)
.Lpc_e1dae:
ld a0,64(t3)
.Lpc_e1db2:
ld t1,64(t5)
.Lpc_e1db6:
ld a2,56(t5)
.Lpc_e1dba:
ld s3,248(t5)
.Lpc_e1dbe:
lw t0,84(t5)
.Lpc_e1dc2:
c.li a5,0
.Lpc_e1dc4:
mul t4,a1,a5
.Lpc_e1dc8:
mul a6,a3,a0
.Lpc_e1dcc:
mul s1,a3,t1
.Lpc_e1dd0:
c.add a6,t4
.Lpc_e1dd2:
add t4,a4,a6
.Lpc_e1dd6:
mul s2,a5,a2
.Lpc_e1dda:
c.add s1,s2
.Lpc_e1ddc:
c.add s1,s3
.Lpc_e1dde:
beq t0,s9,.Lpc_e1f4e
.Lpc_e1de2:
bge s11,t2,.Lpc_e1fd6
.Lpc_e1de6:
c.ldsp t0,48(sp)
.Lpc_e1de8:
c.sdsp s3,8(sp)
.Lpc_e1dea:
c.mv s2,s11
.Lpc_e1dec:
c.add a6,t0
.Lpc_e1dee:
add s3,a4,a6
.Lpc_e1df2:
c.add s1,t0
.Lpc_e1df4:
blt zero,t6,.Lpc_e1e34
.Lpc_e1df8:
sw zero,0(s1)
.Lpc_e1dfc:
c.addi s2,1
.Lpc_e1dfe:
c.addi s1,4
.Lpc_e1e00:
c.addi s3,4
.Lpc_e1e02:
bne t2,s2,.Lpc_e1df4
.Lpc_e1e06:
c.addi a5,1
.Lpc_e1e08:
blt a5,a7,.Lpc_e1fde
.Lpc_e1e0c:
ld a4,32(t5)
.Lpc_e1e10:
c.addi a3,1
.Lpc_e1e12:
blt a3,a4,.Lpc_e1da2
.Lpc_e1e16:
c.ldsp s0,208(sp)
.Lpc_e1e18:
c.ldsp s1,200(sp)
.Lpc_e1e1a:
c.ldsp s2,192(sp)
.Lpc_e1e1c:
c.ldsp s3,184(sp)
.Lpc_e1e1e:
c.ldsp s4,176(sp)
.Lpc_e1e20:
c.ldsp s5,168(sp)
.Lpc_e1e22:
c.ldsp s6,160(sp)
.Lpc_e1e24:
c.ldsp s7,152(sp)
.Lpc_e1e26:
c.ldsp s9,136(sp)
.Lpc_e1e28:
c.ldsp ra,216(sp)
.Lpc_e1e2a:
c.ldsp s8,144(sp)
.Lpc_e1e2c:
c.ldsp s11,120(sp)
.Lpc_e1e2e:
c.ldsp s10,128(sp)
.Lpc_e1e30:
c.addi16sp sp,224
.Lpc_e1e32:
c.jr ra
.Lpc_e1e34:
ld s7,56(s10)
.Lpc_e1e38:
add t0,t4,a1
.Lpc_e1e3c:
c.sdsp a4,104(sp)
.Lpc_e1e3e:
c.mv a4,t0
.Lpc_e1e40:
mul t0,s2,s7
.Lpc_e1e44:
ld s6,248(s10)
.Lpc_e1e48:
slli a6,a1,0x2
.Lpc_e1e4c:
c.sdsp a6,16(sp)
.Lpc_e1e4e:
slli a6,a1,0x1
.Lpc_e1e52:
c.sdsp a6,24(sp)
.Lpc_e1e54:
c.sdsp s10,64(sp)
.Lpc_e1e56:
c.sdsp s11,72(sp)
.Lpc_e1e58:
c.sdsp a7,88(sp)
.Lpc_e1e5a:
c.sdsp t2,0(sp)
.Lpc_e1e5c:
c.sdsp a5,32(sp)
.Lpc_e1e5e:
c.sdsp t3,40(sp)
.Lpc_e1e60:
c.sdsp a3,80(sp)
.Lpc_e1e62:
c.sdsp t5,96(sp)
.Lpc_e1e64:
c.ldsp a6,16(sp)
.Lpc_e1e66:
c.ldsp s10,24(sp)
.Lpc_e1e68:
c.ldsp s11,56(sp)
.Lpc_e1e6a:
fmv.w.x fa5,zero
.Lpc_e1e6e:
slli s4,s2,0x2
.Lpc_e1e72:
c.mv a7,a0
.Lpc_e1e74:
c.add t0,s6
.Lpc_e1e76:
bgeu s9,s8,.Lpc_e1f4a
.Lpc_e1e7a:
c.mv a0,t0
.Lpc_e1e7c:
add t5,s5,t0
.Lpc_e1e80:
add a3,s3,s10
.Lpc_e1e84:
c.mv a5,s3
.Lpc_e1e86:
flw fa4,0(a5)
.Lpc_e1e8a:
vle32.v v3,(a0)
.Lpc_e1e8e:
add t3,a5,a1
.Lpc_e1e92:
vfmv.s.f v2,fa5
.Lpc_e1e96:
flw fa3,0(t3)
.Lpc_e1e9a:
vfmv.v.f v1,fa4
.Lpc_e1e9e:
flw fa4,0(a3)
.Lpc_e1ea2:
add t2,a3,a1
.Lpc_e1ea6:
flw fa5,0(t2)
.Lpc_e1eaa:
vfslide1down.vf v1,v1,fa3
.Lpc_e1eae:
c.addi a0,16
.Lpc_e1eb0:
c.add a5,a6
.Lpc_e1eb2:
c.add a3,a6
.Lpc_e1eb4:
vfslide1down.vf v1,v1,fa4
.Lpc_e1eb8:
vfslide1down.vf v1,v1,fa5
.Lpc_e1ebc:
vfmul.vv v1,v1,v3
.Lpc_e1ec0:
vfredosum.vs v1,v1,v2
.Lpc_e1ec4:
vfmv.f.s fa5,v1
.Lpc_e1ec8:
bne a0,t5,.Lpc_e1e86
.Lpc_e1ecc:
c.mv a5,s0
.Lpc_e1ece:
beq s11,zero,.Lpc_e1f28
.Lpc_e1ed2:
mul a3,a1,a5
.Lpc_e1ed6:
add a0,t4,s4
.Lpc_e1eda:
sh2add t0,a5,t0
.Lpc_e1ede:
flw fa3,0(t0)
.Lpc_e1ee2:
addi t3,a5,1
.Lpc_e1ee6:
add t5,a0,a3
.Lpc_e1eea:
flw fa4,0(t5)
.Lpc_e1eee:
fmul.s fa4,fa4,fa3
.Lpc_e1ef2:
fadd.s fa5,fa5,fa4
.Lpc_e1ef6:
bge t3,t6,.Lpc_e1f28
.Lpc_e1efa:
c.add a3,a1
.Lpc_e1efc:
c.add a0,a3
.Lpc_e1efe:
flw fa3,0(a0)
.Lpc_e1f02:
flw fa4,4(t0)
.Lpc_e1f06:
c.addi a5,2
.Lpc_e1f08:
fmul.s fa4,fa4,fa3
.Lpc_e1f0c:
fadd.s fa5,fa5,fa4
.Lpc_e1f10:
bge a5,t6,.Lpc_e1f28
.Lpc_e1f14:
c.add s4,a4
.Lpc_e1f16:
c.add s4,a3
.Lpc_e1f18:
flw fa4,0(s4)
.Lpc_e1f1c:
flw fa3,8(t0)
.Lpc_e1f20:
fmul.s fa4,fa4,fa3
.Lpc_e1f24:
fadd.s fa5,fa5,fa4
.Lpc_e1f28:
c.ldsp a5,0(sp)
.Lpc_e1f2a:
fsw fa5,0(s1)
.Lpc_e1f2e:
c.addi s2,1
.Lpc_e1f30:
c.addi s1,4
.Lpc_e1f32:
c.addi s3,4
.Lpc_e1f34:
beq a5,s2,.Lpc_e2182
.Lpc_e1f38:
mul t0,s2,s7
.Lpc_e1f3c:
fmv.w.x fa5,zero
.Lpc_e1f40:
slli s4,s2,0x2
.Lpc_e1f44:
c.add t0,s6
.Lpc_e1f46:
bltu s9,s8,.Lpc_e1e7a
.Lpc_e1f4a:
c.li a5,0
.Lpc_e1f4c:
c.j .Lpc_e1ed2
.Lpc_e1f4e:
c.mv s2,s11
.Lpc_e1f50:
bge s11,t2,.Lpc_e216a
.Lpc_e1f54:
sub a0,t2,s2
.Lpc_e1f58:
vsetvli a0,a0,e32,m1,ta,ma
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_e1f5c:
slli a6,s2,0x2
.Lpc_e1f60:
vmv.v.i v2,0
.Lpc_e1f64:
bge zero,t6,.Lpc_e1f9e
.Lpc_e1f68:
ld a7,56(s10)
.Lpc_e1f6c:
ld a1,56(t3)
.Lpc_e1f70:
ld t0,248(s10)
.Lpc_e1f74:
mul t1,a7,s2
.Lpc_e1f78:
c.li a2,0
.Lpc_e1f7a:
sh2add a4,a2,t1
.Lpc_e1f7e:
c.add a4,t0
.Lpc_e1f80:
vlse32.v v3,(a4),a7
.Lpc_e1f84:
mul a4,a2,a1
.Lpc_e1f88:
c.addi a2,1
.Lpc_e1f8a:
c.add a4,a6
.Lpc_e1f8c:
c.add a4,t4
.Lpc_e1f8e:
vle32.v v1,(a4)
.Lpc_e1f92:
vfmul.vv v1,v1,v3
.Lpc_e1f96:
vfadd.vv v2,v2,v1
.Lpc_e1f9a:
bne t6,a2,.Lpc_e1f7a
.Lpc_e1f9e:
c.add a6,s1
.Lpc_e1fa0:
vse32.v v2,(a6)
.Lpc_e1fa4:
c.add s2,a0
.Lpc_e1fa6:
blt s2,t2,.Lpc_e1f54
.Lpc_e1faa:
ld a7,24(t5)
.Lpc_e1fae:
c.addi a5,1
.Lpc_e1fb0:
bge a5,a7,.Lpc_e215c
.Lpc_e1fb4:
ld a4,248(t3)
.Lpc_e1fb8:
vsetivli zero,4,e32,m1,ta,ma
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_e1fbc:
ld a1,56(t3)
.Lpc_e1fc0:
ld a0,64(t3)
.Lpc_e1fc4:
ld t1,64(t5)
.Lpc_e1fc8:
ld a2,56(t5)
.Lpc_e1fcc:
ld s3,248(t5)
.Lpc_e1fd0:
lw t0,84(t5)
.Lpc_e1fd4:
c.j .Lpc_e1dc4
.Lpc_e1fd6:
c.addi a5,1
.Lpc_e1fd8:
bge a5,a7,.Lpc_e2176
.Lpc_e1fdc:
c.sdsp s3,8(sp)
.Lpc_e1fde:
mul a6,a3,a0
.Lpc_e1fe2:
c.ldsp s1,48(sp)
.Lpc_e1fe4:
c.sdsp a3,72(sp)
.Lpc_e1fe6:
c.sdsp t3,64(sp)
.Lpc_e1fe8:
slli a0,a1,0x2
.Lpc_e1fec:
slli s4,a1,0x1
.Lpc_e1ff0:
c.sdsp t5,80(sp)
.Lpc_e1ff2:
mul s6,a3,t1
.Lpc_e1ff6:
c.ldsp a3,8(sp)
.Lpc_e1ff8:
add s7,a6,s1
.Lpc_e1ffc:
c.mv t1,a7
.Lpc_e1ffe:
c.mv a7,s7
.Lpc_e2000:
c.mv t3,s6
.Lpc_e2002:
mul t5,a1,a5
.Lpc_e2006:
mul t4,a2,a5
.Lpc_e200a:
add s3,t5,a6
.Lpc_e200e:
c.add s3,a4
.Lpc_e2010:
c.add t4,t3
.Lpc_e2012:
bge s11,t2,.Lpc_e2038
.Lpc_e2016:
c.ldsp s1,48(sp)
.Lpc_e2018:
c.add t5,a7
.Lpc_e201a:
c.add t4,s1
.Lpc_e201c:
add s2,a3,t4
.Lpc_e2020:
add s1,a4,t5
.Lpc_e2024:
c.mv t5,s11
.Lpc_e2026:
blt zero,t6,.Lpc_e204c
.Lpc_e202a:
sw zero,0(s2)
.Lpc_e202e:
c.addi t5,1
.Lpc_e2030:
c.addi s2,4
.Lpc_e2032:
c.addi s1,4
.Lpc_e2034:
bne t2,t5,.Lpc_e2026
.Lpc_e2038:
c.addi a5,1
.Lpc_e203a:
blt a5,t1,.Lpc_e2002
.Lpc_e203e:
c.ldsp t5,80(sp)
.Lpc_e2040:
c.ldsp t3,64(sp)
.Lpc_e2042:
c.ldsp a3,72(sp)
.Lpc_e2044:
ld a4,32(t5)
.Lpc_e2048:
c.mv a7,t1
.Lpc_e204a:
c.j .Lpc_e1e10
.Lpc_e204c:
ld s7,56(s10)
.Lpc_e2050:
c.sdsp s11,24(sp)
.Lpc_e2052:
ld s6,248(s10)
.Lpc_e2056:
mul s11,t5,s7
.Lpc_e205a:
c.sdsp t3,40(sp)
.Lpc_e205c:
c.sdsp t2,0(sp)
.Lpc_e205e:
c.sdsp a5,8(sp)
.Lpc_e2060:
c.sdsp s10,16(sp)
.Lpc_e2062:
c.sdsp t1,32(sp)
.Lpc_e2064:
fmv.w.x fa5,zero
.Lpc_e2068:
slli t0,t5,0x2
.Lpc_e206c:
c.mv t3,a6
.Lpc_e206e:
c.add s11,s6
.Lpc_e2070:
bgeu s9,s8,.Lpc_e2142
.Lpc_e2074:
c.mv t1,s11
.Lpc_e2076:
add s10,s5,s11
.Lpc_e207a:
add a6,s1,s4
.Lpc_e207e:
c.mv a5,s1
.Lpc_e2080:
flw fa4,0(a5)
.Lpc_e2084:
vle32.v v3,(t1)
.Lpc_e2088:
add t4,a5,a1
.Lpc_e208c:
vfmv.s.f v2,fa5
.Lpc_e2090:
flw fa3,0(t4)
.Lpc_e2094:
vfmv.v.f v1,fa4
.Lpc_e2098:
flw fa4,0(a6)
.Lpc_e209c:
add t2,a6,a1
.Lpc_e20a0:
flw fa5,0(t2)
.Lpc_e20a4:
vfslide1down.vf v1,v1,fa3
.Lpc_e20a8:
c.addi t1,16
.Lpc_e20aa:
c.add a5,a0
.Lpc_e20ac:
c.add a6,a0
.Lpc_e20ae:
vfslide1down.vf v1,v1,fa4
.Lpc_e20b2:
vfslide1down.vf v1,v1,fa5
.Lpc_e20b6:
vfmul.vv v1,v1,v3
.Lpc_e20ba:
vfredosum.vs v1,v1,v2
.Lpc_e20be:
vfmv.f.s fa5,v1
.Lpc_e20c2:
bne s10,t1,.Lpc_e2080
.Lpc_e20c6:
c.mv a5,s0
.Lpc_e20c8:
beq t6,s0,.Lpc_e2120
.Lpc_e20cc:
mul a6,a5,a1
.Lpc_e20d0:
sh2add s11,a5,s11
.Lpc_e20d4:
flw fa3,0(s11)
.Lpc_e20d8:
addi t1,a5,1
.Lpc_e20dc:
add t4,s3,a6
.Lpc_e20e0:
c.add t4,t0
.Lpc_e20e2:
flw fa4,0(t4)
.Lpc_e20e6:
fmul.s fa4,fa4,fa3
.Lpc_e20ea:
fadd.s fa5,fa5,fa4
.Lpc_e20ee:
bge t1,t6,.Lpc_e2120
.Lpc_e20f2:
c.add a6,a1
.Lpc_e20f4:
c.add t0,s3
.Lpc_e20f6:
c.add t0,a6
.Lpc_e20f8:
flw fa3,0(t0)
.Lpc_e20fc:
flw fa4,4(s11)
.Lpc_e2100:
c.addi a5,2
.Lpc_e2102:
fmul.s fa4,fa4,fa3
.Lpc_e2106:
fadd.s fa5,fa5,fa4
.Lpc_e210a:
bge a5,t6,.Lpc_e2120
.Lpc_e210e:
c.add t0,a1
.Lpc_e2110:
flw fa3,0(t0)
.Lpc_e2114:
flw fa4,8(s11)
.Lpc_e2118:
fmul.s fa4,fa4,fa3
.Lpc_e211c:
fadd.s fa5,fa5,fa4
.Lpc_e2120:
c.ldsp a5,0(sp)
.Lpc_e2122:
fsw fa5,0(s2)
.Lpc_e2126:
c.addi t5,1
.Lpc_e2128:
c.addi s2,4
.Lpc_e212a:
c.addi s1,4
.Lpc_e212c:
beq a5,t5,.Lpc_e2146
.Lpc_e2130:
mul s11,t5,s7
.Lpc_e2134:
fmv.w.x fa5,zero
.Lpc_e2138:
slli t0,t5,0x2
.Lpc_e213c:
c.add s11,s6
.Lpc_e213e:
bltu s9,s8,.Lpc_e2074
.Lpc_e2142:
c.li a5,0
.Lpc_e2144:
c.j .Lpc_e20cc
.Lpc_e2146:
c.mv t2,a5
.Lpc_e2148:
c.ldsp a5,8(sp)
.Lpc_e214a:
c.ldsp t1,32(sp)
.Lpc_e214c:
c.mv a6,t3
.Lpc_e214e:
c.addi a5,1
.Lpc_e2150:
c.ldsp s10,16(sp)
.Lpc_e2152:
c.ldsp s11,24(sp)
.Lpc_e2154:
c.ldsp t3,40(sp)
.Lpc_e2156:
blt a5,t1,.Lpc_e2002
.Lpc_e215a:
c.j .Lpc_e203e
.Lpc_e215c:
ld a4,32(t5)
.Lpc_e2160:
vsetivli zero,4,e32,m1,ta,ma
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_e2164:
c.j .Lpc_e1e10
.Lpc_e2166:
c.mv t2,a5
.Lpc_e2168:
c.j .Lpc_e1d6a
.Lpc_e216a:
c.addi a5,1
.Lpc_e216c:
blt a5,a7,.Lpc_e1dc4
.Lpc_e2170:
ld a4,32(t5)
.Lpc_e2174:
c.j .Lpc_e1e10
.Lpc_e2176:
ld a5,32(t5)
.Lpc_e217a:
c.addi a3,1
.Lpc_e217c:
blt a3,a5,.Lpc_e1dc2
.Lpc_e2180:
c.j .Lpc_e1e16
.Lpc_e2182:
c.mv a0,a7
.Lpc_e2184:
c.ldsp t2,0(sp)
.Lpc_e2186:
c.ldsp a5,32(sp)
.Lpc_e2188:
c.ldsp t3,40(sp)
.Lpc_e218a:
c.ldsp s10,64(sp)
.Lpc_e218c:
c.ldsp s11,72(sp)
.Lpc_e218e:
c.ldsp a3,80(sp)
.Lpc_e2190:
c.ldsp t5,96(sp)
.Lpc_e2192:
c.ldsp a7,88(sp)
.Lpc_e2194:
c.ldsp a4,104(sp)
.Lpc_e2196:
c.j .Lpc_e1e06
.Lpc_e2198:
auipc a3,0xe5
.Lpc_e219c:
addi a3,a3,-112 # .Lpc_1c7128
.Lpc_e21a0:
auipc a2,0xe4
.Lpc_e21a4:
addi a2,a2,-880 # .Lpc_1c5e30
.Lpc_e21a8:
c.li a1,21
.Lpc_e21aa:
auipc a0,0xe5
.Lpc_e21ae:
addi a0,a0,-434 # .Lpc_1c6ff8
.Lpc_e21b2:
c.sdsp s0,208(sp)
.Lpc_e21b4:
c.sdsp s1,200(sp)
.Lpc_e21b6:
c.sdsp s2,192(sp)
.Lpc_e21b8:
c.sdsp s3,184(sp)
.Lpc_e21ba:
c.sdsp s4,176(sp)
.Lpc_e21bc:
c.sdsp s5,168(sp)
.Lpc_e21be:
c.sdsp s6,160(sp)
.Lpc_e21c0:
c.sdsp s7,152(sp)
.Lpc_e21c2:
c.sdsp s9,136(sp)
.Lpc_e21c4:
c.sdsp s11,120(sp)
.Lpc_e21c6:
jal ra,.Lpc_85420
.Lpc_e21ca:
auipc a3,0xe5
.Lpc_e21ce:
addi a3,a3,-218 # .Lpc_1c70f0
.Lpc_e21d2:
auipc a2,0xe4
.Lpc_e21d6:
addi a2,a2,-930 # .Lpc_1c5e30
.Lpc_e21da:
c.li a1,20
.Lpc_e21dc:
auipc a0,0xe5
.Lpc_e21e0:
addi a0,a0,-484 # .Lpc_1c6ff8
.Lpc_e21e4:
c.sdsp s0,208(sp)
.Lpc_e21e6:
c.sdsp s1,200(sp)
.Lpc_e21e8:
c.sdsp s2,192(sp)
.Lpc_e21ea:
c.sdsp s3,184(sp)
.Lpc_e21ec:
c.sdsp s4,176(sp)
.Lpc_e21ee:
c.sdsp s5,168(sp)
.Lpc_e21f0:
c.sdsp s6,160(sp)
.Lpc_e21f2:
c.sdsp s7,152(sp)
.Lpc_e21f4:
c.sdsp s9,136(sp)
.Lpc_e21f6:
c.sdsp s11,120(sp)
.Lpc_e21f8:
jal ra,.Lpc_85420
.Lpc_e21fc:
auipc a3,0xe5
.Lpc_e2200:
addi a3,a3,-308 # .Lpc_1c70c8
.Lpc_e2204:
auipc a2,0xe4
.Lpc_e2208:
addi a2,a2,-980 # .Lpc_1c5e30
.Lpc_e220c:
c.li a1,19
.Lpc_e220e:
auipc a0,0xe5
.Lpc_e2212:
addi a0,a0,-534 # .Lpc_1c6ff8
.Lpc_e2216:
c.sdsp s0,208(sp)
.Lpc_e2218:
c.sdsp s1,200(sp)
.Lpc_e221a:
c.sdsp s2,192(sp)
.Lpc_e221c:
c.sdsp s3,184(sp)
.Lpc_e221e:
c.sdsp s4,176(sp)
.Lpc_e2220:
c.sdsp s5,168(sp)
.Lpc_e2222:
c.sdsp s6,160(sp)
.Lpc_e2224:
c.sdsp s7,152(sp)
.Lpc_e2226:
c.sdsp s9,136(sp)
.Lpc_e2228:
c.sdsp s11,120(sp)
.Lpc_e222a:
jal ra,.Lpc_85420
.Lpc_e222e:
auipc a3,0xe5
.Lpc_e2232:
addi a3,a3,-430 # .Lpc_1c7080
.Lpc_e2236:
auipc a2,0xe4
.Lpc_e223a:
addi a2,a2,-1030 # .Lpc_1c5e30
.Lpc_e223e:
c.li a1,18
.Lpc_e2240:
auipc a0,0xe5
.Lpc_e2244:
addi a0,a0,-584 # .Lpc_1c6ff8
.Lpc_e2248:
c.sdsp s0,208(sp)
.Lpc_e224a:
c.sdsp s1,200(sp)
.Lpc_e224c:
c.sdsp s2,192(sp)
.Lpc_e224e:
c.sdsp s3,184(sp)
.Lpc_e2250:
c.sdsp s4,176(sp)
.Lpc_e2252:
c.sdsp s5,168(sp)
.Lpc_e2254:
c.sdsp s6,160(sp)
.Lpc_e2256:
c.sdsp s7,152(sp)
.Lpc_e2258:
c.sdsp s8,144(sp)
.Lpc_e225a:
c.sdsp s9,136(sp)
.Lpc_e225c:
c.sdsp s11,120(sp)
.Lpc_e225e:
jal ra,.Lpc_85420
.Lpc_e2262:
auipc a3,0xe5
.Lpc_e2266:
addi a3,a3,-682 # .Lpc_1c6fb8
.Lpc_e226a:
auipc a2,0xe4
.Lpc_e226e:
addi a2,a2,-1082 # .Lpc_1c5e30
.Lpc_e2272:
c.li a1,17
.Lpc_e2274:
auipc a0,0xe5
.Lpc_e2278:
addi a0,a0,-636 # .Lpc_1c6ff8
.Lpc_e227c:
c.sdsp s0,208(sp)
.Lpc_e227e:
c.sdsp s1,200(sp)
.Lpc_e2280:
c.sdsp s2,192(sp)
.Lpc_e2282:
c.sdsp s3,184(sp)
.Lpc_e2284:
c.sdsp s4,176(sp)
.Lpc_e2286:
c.sdsp s5,168(sp)
.Lpc_e2288:
c.sdsp s6,160(sp)
.Lpc_e228a:
c.sdsp s7,152(sp)
.Lpc_e228c:
c.sdsp s8,144(sp)
.Lpc_e228e:
c.sdsp s9,136(sp)
.Lpc_e2290:
c.sdsp s11,120(sp)
.Lpc_e2292:
jal ra,.Lpc_85420
