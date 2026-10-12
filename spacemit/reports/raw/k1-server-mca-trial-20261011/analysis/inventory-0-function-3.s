.text
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_e2e2e:
addi sp,sp,-640
.Lpc_e2e32:
sd s0,624(sp)
.Lpc_e2e36:
c.sdsp a5,0(sp)
.Lpc_e2e38:
c.ld s0,152(a1)
.Lpc_e2e3a:
c.ld a5,184(a1)
.Lpc_e2e3c:
sd s1,616(sp)
.Lpc_e2e40:
auipc s1,0x14a
.Lpc_e2e44:
ld s1,1912(s1) # .Lpc_22d5b8
.Lpc_e2e48:
sd s2,608(sp)
.Lpc_e2e4c:
sd s3,600(sp)
.Lpc_e2e50:
sd s5,584(sp)
.Lpc_e2e54:
sd s6,576(sp)
.Lpc_e2e58:
sd s9,552(sp)
.Lpc_e2e5c:
sd ra,632(sp)
.Lpc_e2e60:
sd s4,592(sp)
.Lpc_e2e64:
sd s7,568(sp)
.Lpc_e2e68:
sd s8,560(sp)
.Lpc_e2e6c:
sd s10,544(sp)
.Lpc_e2e70:
sd s11,536(sp)
.Lpc_e2e74:
c.sdsp s0,176(sp)
.Lpc_e2e76:
ld t1,0(s1)
.Lpc_e2e7a:
c.sdsp t1,424(sp)
.Lpc_e2e7c:
c.li t1,0
.Lpc_e2e7e:
c.sdsp a0,184(sp)
.Lpc_e2e80:
c.sdsp a4,128(sp)
.Lpc_e2e82:
c.sdsp a6,168(sp)
.Lpc_e2e84:
c.sdsp a5,144(sp)
.Lpc_e2e86:
c.mv s3,a7
.Lpc_e2e88:
ld s9,160(a1)
.Lpc_e2e8c:
ld s2,168(a1)
.Lpc_e2e90:
ld a7,176(a1)
.Lpc_e2e94:
c.mv s5,a2
.Lpc_e2e96:
c.mv s6,a3
.Lpc_e2e98:
beq s0,zero,.Lpc_e38ac
.Lpc_e2e9c:
c.ld a5,24(s0)
.Lpc_e2e9e:
c.ld a3,56(s0)
.Lpc_e2ea0:
c.ld a4,72(s0)
.Lpc_e2ea2:
c.sdsp a5,136(sp)
.Lpc_e2ea4:
c.ld a5,32(s0)
.Lpc_e2ea6:
c.sdsp a3,232(sp)
.Lpc_e2ea8:
c.ld a3,64(s0)
.Lpc_e2eaa:
c.sdsp a5,152(sp)
.Lpc_e2eac:
ld s10,16(s0)
.Lpc_e2eb0:
c.ld s1,40(s0)
.Lpc_e2eb2:
c.ld a5,48(s0)
.Lpc_e2eb4:
c.sdsp a3,240(sp)
.Lpc_e2eb6:
c.sdsp a4,224(sp)
.Lpc_e2eb8:
beq s9,zero,.Lpc_e389a
.Lpc_e2ebc:
ld a4,16(s9)
.Lpc_e2ec0:
ld s11,32(s9)
.Lpc_e2ec4:
ld s8,48(s9)
.Lpc_e2ec8:
c.sdsp a4,32(sp)
.Lpc_e2eca:
ld a4,40(s9)
.Lpc_e2ece:
c.sdsp a4,24(sp)
.Lpc_e2ed0:
ld a4,56(s9)
.Lpc_e2ed4:
c.sdsp a4,8(sp)
.Lpc_e2ed6:
ld a4,64(s9)
.Lpc_e2eda:
c.sdsp a4,328(sp)
.Lpc_e2edc:
ld a4,72(s9)
.Lpc_e2ee0:
c.sdsp a4,312(sp)
.Lpc_e2ee2:
beq s2,zero,.Lpc_e3888
.Lpc_e2ee6:
ld a4,16(s2)
.Lpc_e2eea:
c.sdsp a4,72(sp)
.Lpc_e2eec:
ld a4,32(s2)
.Lpc_e2ef0:
c.sdsp a4,48(sp)
.Lpc_e2ef2:
ld a4,40(s2)
.Lpc_e2ef6:
c.sdsp a4,56(sp)
.Lpc_e2ef8:
ld a4,48(s2)
.Lpc_e2efc:
c.sdsp a4,40(sp)
.Lpc_e2efe:
ld a4,56(s2)
.Lpc_e2f02:
c.sdsp a4,16(sp)
.Lpc_e2f04:
ld a4,64(s2)
.Lpc_e2f08:
c.sdsp a4,336(sp)
.Lpc_e2f0a:
ld a4,72(s2)
.Lpc_e2f0e:
c.sdsp a4,320(sp)
.Lpc_e2f10:
c.ld a4,24(a1)
.Lpc_e2f12:
c.ld a2,16(a1)
.Lpc_e2f14:
c.ld a3,32(a1)
.Lpc_e2f16:
c.sdsp a4,384(sp)
.Lpc_e2f18:
c.ld a4,56(a1)
.Lpc_e2f1a:
ld s7,48(a1)
.Lpc_e2f1e:
c.ld s0,64(a1)
.Lpc_e2f20:
c.sdsp a4,368(sp)
.Lpc_e2f22:
c.ldsp a4,72(sp)
.Lpc_e2f24:
ld s4,72(a1)
.Lpc_e2f28:
bne a2,a4,.Lpc_e397e
.Lpc_e2f2c:
c.ldsp a4,136(sp)
.Lpc_e2f2e:
bne a3,a4,.Lpc_e39ce
.Lpc_e2f32:
c.sdsp a5,80(sp)
.Lpc_e2f34:
c.ldsp a5,176(sp)
.Lpc_e2f36:
c.sdsp a1,88(sp)
.Lpc_e2f38:
c.sdsp a7,64(sp)
.Lpc_e2f3a:
c.lw a0,0(a5)
.Lpc_e2f3c:
jal ra,.Lpc_841a0
.Lpc_e2f40:
c.ldsp a5,80(sp)
.Lpc_e2f42:
c.ldsp a7,64(sp)
.Lpc_e2f44:
c.ldsp a1,88(sp)
.Lpc_e2f46:
bne a5,a0,.Lpc_e38ec
.Lpc_e2f4a:
lw a0,0(s9)
.Lpc_e2f4e:
c.sdsp a1,80(sp)
.Lpc_e2f50:
c.sdsp a7,64(sp)
.Lpc_e2f52:
jal ra,.Lpc_841a0
.Lpc_e2f56:
c.ldsp a7,64(sp)
.Lpc_e2f58:
c.ldsp a1,80(sp)
.Lpc_e2f5a:
bne s8,a0,.Lpc_e3a7e
.Lpc_e2f5e:
lw a0,0(s2)
.Lpc_e2f62:
c.sdsp a1,80(sp)
.Lpc_e2f64:
c.sdsp a7,64(sp)
.Lpc_e2f66:
jal ra,.Lpc_841a0
.Lpc_e2f6a:
c.ldsp a5,40(sp)
.Lpc_e2f6c:
c.ldsp a7,64(sp)
.Lpc_e2f6e:
c.ldsp a1,80(sp)
.Lpc_e2f70:
bne a5,a0,.Lpc_e3a2e
.Lpc_e2f74:
c.ldsp a5,32(sp)
.Lpc_e2f76:
bne a5,s10,.Lpc_e3b1e
.Lpc_e2f7a:
c.li a5,4
.Lpc_e2f7c:
bne s7,a5,.Lpc_e3ace
.Lpc_e2f80:
c.ldsp a4,368(sp)
.Lpc_e2f82:
c.li a5,3
.Lpc_e2f84:
bgeu a5,a4,.Lpc_e3c14
.Lpc_e2f88:
bltu s0,a4,.Lpc_e3bc2
.Lpc_e2f8c:
bltu s4,s0,.Lpc_e3b70
.Lpc_e2f90:
c.ldsp a4,152(sp)
.Lpc_e2f92:
c.fsdsp fs2,504(sp)
.Lpc_e2f94:
fsd fs0,520(sp)
.Lpc_e2f98:
div a5,a4,s11
.Lpc_e2f9c:
fsd fs1,512(sp)
.Lpc_e2fa0:
c.fsdsp fs3,496(sp)
.Lpc_e2fa2:
c.fsdsp fs7,464(sp)
.Lpc_e2fa4:
c.fsdsp fs8,456(sp)
.Lpc_e2fa6:
c.lw a3,92(a1)
.Lpc_e2fa8:
fmv.w.x fa5,zero
.Lpc_e2fac:
c.lw s0,88(a1)
.Lpc_e2fae:
fmv.w.x fs2,a3
.Lpc_e2fb2:
c.sdsp a5,248(sp)
.Lpc_e2fb4:
c.lw a5,84(a1)
.Lpc_e2fb6:
c.mv a2,a5
.Lpc_e2fb8:
c.swsp a5,40(sp)
.Lpc_e2fba:
c.ldsp a5,24(sp)
.Lpc_e2fbc:
div a5,s1,a5
.Lpc_e2fc0:
c.sdsp a5,256(sp)
.Lpc_e2fc2:
c.ldsp a5,48(sp)
.Lpc_e2fc4:
div a5,a4,a5
.Lpc_e2fc8:
c.sdsp a5,264(sp)
.Lpc_e2fca:
c.ldsp a5,56(sp)
.Lpc_e2fcc:
div a5,s1,a5
.Lpc_e2fd0:
c.sdsp a5,272(sp)
.Lpc_e2fd2:
feq.s a5,fs2,fa5
.Lpc_e2fd6:
beq a5,zero,.Lpc_e386a
.Lpc_e2fda:
c.ldsp a5,152(sp)
.Lpc_e2fdc:
c.sdsp a1,64(sp)
.Lpc_e2fde:
c.sdsp a7,24(sp)
.Lpc_e2fe0:
fcvt.d.wu fa0,a5
.Lpc_e2fe4:
addiw s1,a5,0
.Lpc_e2fe8:
fmv.w.x fs0,s0
.Lpc_e2fec:
jal ra,.Lpc_84e10
.Lpc_e2ff0:
jal ra,.Lpc_86e80
.Lpc_e2ff4:
fcvt.wu.d a5,fa0,rtz
.Lpc_e2ff8:
fmv.w.x fa5,s0
.Lpc_e2ffc:
c.li a3,1
.Lpc_e2ffe:
sllw a5,a3,a5
.Lpc_e3002:
fcvt.s.wu fs1,a5
.Lpc_e3006:
fsgnjn.s fa1,fa5,fa5
.Lpc_e300a:
auipc a4,0xe9
.Lpc_e300e:
flw fs3,-1122(a4) # .Lpc_1cbba8
.Lpc_e3012:
c.sdsp a5,360(sp)
.Lpc_e3014:
fdiv.s fa1,fa1,fs1
.Lpc_e3018:
fsgnj.s fa0,fs3,fs3
.Lpc_e301c:
jal ra,.Lpc_83ae0
.Lpc_e3020:
auipc a5,0xe9
.Lpc_e3024:
flw fa5,-1224(a5) # .Lpc_1cbb58
.Lpc_e3028:
fsgnj.s fs7,fa0,fa0
.Lpc_e302c:
fsgnj.s fa0,fs3,fs3
.Lpc_e3030:
fmul.s fa1,fs0,fa5
.Lpc_e3034:
fdiv.s fa1,fa1,fs1
.Lpc_e3038:
jal ra,.Lpc_83ae0
.Lpc_e303c:
lw a0,0(s9)
.Lpc_e3040:
fsgnj.s fs8,fa0,fa0
.Lpc_e3044:
jal ra,.Lpc_871e0
.Lpc_e3048:
c.lw a0,16(a0)
.Lpc_e304a:
jal ra,.Lpc_871e0
.Lpc_e304e:
c.mv a5,a0
.Lpc_e3050:
c.ld s0,0(a5)
.Lpc_e3052:
lw a0,0(s9)
.Lpc_e3056:
c.sdsp s0,280(sp)
.Lpc_e3058:
jal ra,.Lpc_871e0
.Lpc_e305c:
c.mv a5,a0
.Lpc_e305e:
c.ld a5,8(a5)
.Lpc_e3060:
lw a0,0(s2)
.Lpc_e3064:
c.sdsp a5,48(sp)
.Lpc_e3066:
jal ra,.Lpc_852e0
.Lpc_e306a:
c.ld a5,40(a0)
.Lpc_e306c:
c.ldsp a7,24(sp)
.Lpc_e306e:
c.ldsp a1,64(sp)
.Lpc_e3070:
c.sdsp a5,56(sp)
.Lpc_e3072:
beq s0,zero,.Lpc_e393e
.Lpc_e3076:
lw a5,0(s2)
.Lpc_e307a:
bne a5,zero,.Lpc_e3822
.Lpc_e307e:
c.ldsp a5,184(sp)
.Lpc_e3080:
c.lw a3,0(a5)
.Lpc_e3082:
bge s5,s6,.Lpc_e33f8
.Lpc_e3086:
c.ldsp a0,136(sp)
.Lpc_e3088:
c.ldsp a5,32(sp)
.Lpc_e308a:
subw s6,s6,s5
.Lpc_e308e:
mulw a4,a0,s1
.Lpc_e3092:
add.uw s0,s6,s5
.Lpc_e3096:
c.addi a5,16
.Lpc_e3098:
c.fsdsp fs4,488(sp)
.Lpc_e309a:
c.fsdsp fs5,480(sp)
.Lpc_e309c:
c.fsdsp fs6,472(sp)
.Lpc_e309e:
c.sdsp s0,288(sp)
.Lpc_e30a0:
fsw fs7,408(sp)
.Lpc_e30a4:
slli s0,s3,0x2
.Lpc_e30a8:
auipc a2,0xe9
.Lpc_e30ac:
flw fs5,-1396(a2) # .Lpc_1cbb34
.Lpc_e30b0:
auipc a2,0xe9
.Lpc_e30b4:
flw fs4,-1296(a2) # .Lpc_1cbba0
.Lpc_e30b8:
c.sdsp a4,304(sp)
.Lpc_e30ba:
c.ldsp a4,72(sp)
.Lpc_e30bc:
auipc a2,0xf2
.Lpc_e30c0:
flh fs6,-1652(a2) # .Lpc_1d4a48
.Lpc_e30c4:
fsgnj.s fs7,fs0,fs0
.Lpc_e30c8:
sh1add a5,a4,a5
.Lpc_e30cc:
mul a5,a5,a3
.Lpc_e30d0:
c.mv a3,a4
.Lpc_e30d2:
c.slli a4,0x1
.Lpc_e30d4:
addiw s6,a3,0
.Lpc_e30d8:
c.sdsp a4,376(sp)
.Lpc_e30da:
slli a4,a3,0x2
.Lpc_e30de:
c.sdsp a4,112(sp)
.Lpc_e30e0:
c.sdsp s0,296(sp)
.Lpc_e30e2:
addiw s0,a0,0
.Lpc_e30e6:
c.fsdsp fs9,448(sp)
.Lpc_e30e8:
c.fsdsp fs10,440(sp)
.Lpc_e30ea:
c.add a3,a5
.Lpc_e30ec:
mul a4,s3,s5
.Lpc_e30f0:
c.slli a5,0x2
.Lpc_e30f2:
c.sdsp a5,216(sp)
.Lpc_e30f4:
c.ldsp a5,152(sp)
.Lpc_e30f6:
c.slli a3,0x2
.Lpc_e30f8:
c.fsdsp fs11,432(sp)
.Lpc_e30fa:
c.sdsp s5,80(sp)
.Lpc_e30fc:
c.sdsp s0,208(sp)
.Lpc_e30fe:
c.sdsp a3,400(sp)
.Lpc_e3100:
c.mv s11,s6
.Lpc_e3102:
mul a5,a5,a0
.Lpc_e3106:
c.sdsp a1,392(sp)
.Lpc_e3108:
c.sdsp a5,200(sp)
.Lpc_e310a:
addi a5,a4,2
.Lpc_e310e:
c.ldsp a4,168(sp)
.Lpc_e3110:
sh2add a5,a5,a4
.Lpc_e3114:
c.sdsp a5,104(sp)
.Lpc_e3116:
c.ldsp a4,16(sp)
.Lpc_e3118:
c.ldsp a5,128(sp)
.Lpc_e311a:
mul a4,a4,a5
.Lpc_e311e:
c.sdsp a4,352(sp)
.Lpc_e3120:
c.ldsp a4,8(sp)
.Lpc_e3122:
mul a5,a4,a5
.Lpc_e3126:
c.sdsp a5,344(sp)
.Lpc_e3128:
c.ldsp a3,80(sp)
.Lpc_e312a:
c.ldsp a5,200(sp)
.Lpc_e312c:
c.ldsp a2,304(sp)
.Lpc_e312e:
fmv.w.x fa5,zero
.Lpc_e3132:
div a5,a3,a5
.Lpc_e3136:
fsgnj.s fs3,fs5,fs5
.Lpc_e313a:
addiw a4,a5,0
.Lpc_e313e:
mulw a5,a5,a2
.Lpc_e3142:
c.ldsp a2,152(sp)
.Lpc_e3144:
c.sdsp a4,88(sp)
.Lpc_e3146:
mul a4,a4,a2
.Lpc_e314a:
c.ldsp a2,136(sp)
.Lpc_e314c:
subw a5,a3,a5
.Lpc_e3150:
mul a4,a4,a2
.Lpc_e3154:
sub a4,a3,a4
.Lpc_e3158:
div a3,a4,a2
.Lpc_e315c:
c.ldsp a4,208(sp)
.Lpc_e315e:
mulw a4,a3,a4
.Lpc_e3162:
c.sdsp a3,160(sp)
.Lpc_e3164:
c.addiw a3,0
.Lpc_e3166:
c.sdsp a3,64(sp)
.Lpc_e3168:
c.subw a5,a4
.Lpc_e316a:
c.sdsp a5,96(sp)
.Lpc_e316c:
flt.s a5,fa5,fs7
.Lpc_e3170:
c.beqz a5,.Lpc_e3190
.Lpc_e3172:
c.ldsp a4,360(sp)
.Lpc_e3174:
c.sdsp a7,24(sp)
.Lpc_e3176:
bgeu a3,a4,.Lpc_e36be
.Lpc_e317a:
addiw a5,a3,1
.Lpc_e317e:
fcvt.s.wu fa1,a5
.Lpc_e3182:
flw fa0,408(sp)
.Lpc_e3186:
jal ra,.Lpc_83ae0
.Lpc_e318a:
fsgnj.s fs3,fa0,fa0
.Lpc_e318e:
c.ldsp a7,24(sp)
.Lpc_e3190:
c.ldsp a5,184(sp)
.Lpc_e3192:
c.ldsp a2,216(sp)
.Lpc_e3194:
lw a4,0(s2)
.Lpc_e3198:
c.ld a5,16(a5)
.Lpc_e319a:
c.sdsp a7,120(sp)
.Lpc_e319c:
c.mv a3,a5
.Lpc_e319e:
add s7,a3,a2
.Lpc_e31a2:
c.ldsp a3,112(sp)
.Lpc_e31a4:
c.sdsp a5,192(sp)
.Lpc_e31a6:
c.li a5,1
.Lpc_e31a8:
add s6,s7,a3
.Lpc_e31ac:
sh1add a3,a3,s7
.Lpc_e31b0:
c.sdsp a3,24(sp)
.Lpc_e31b2:
beq a4,a5,.Lpc_e36b0
.Lpc_e31b6:
c.ldsp a2,112(sp)
.Lpc_e31b8:
c.li a1,0
.Lpc_e31ba:
c.mv a0,s7
.Lpc_e31bc:
jal ra,.Lpc_86930
.Lpc_e31c0:
c.ldsp a7,120(sp)
.Lpc_e31c2:
c.li s4,0
.Lpc_e31c4:
beq a7,zero,.Lpc_e3200
.Lpc_e31c8:
c.ldsp a3,64(sp)
.Lpc_e31ca:
ld a5,32(a7)
.Lpc_e31ce:
ld a4,40(a7)
.Lpc_e31d2:
ld a2,72(a7)
.Lpc_e31d6:
rem a5,a3,a5
.Lpc_e31da:
c.ldsp a3,88(sp)
.Lpc_e31dc:
ld a1,64(a7)
.Lpc_e31e0:
ld s4,248(a7)
.Lpc_e31e4:
rem a4,a3,a4
.Lpc_e31e8:
ld a3,56(a7)
.Lpc_e31ec:
mul a4,a4,a2
.Lpc_e31f0:
c.ldsp a2,96(sp)
.Lpc_e31f2:
mul a5,a5,a1
.Lpc_e31f6:
mul a3,a2,a3
.Lpc_e31fa:
c.add a5,a4
.Lpc_e31fc:
c.add a5,a3
.Lpc_e31fe:
c.add s4,a5
.Lpc_e3200:
c.ldsp a4,88(sp)
.Lpc_e3202:
c.ldsp a5,256(sp)
.Lpc_e3204:
c.ldsp a3,248(sp)
.Lpc_e3206:
c.ldsp a6,96(sp)
.Lpc_e3208:
div s0,a4,a5
.Lpc_e320c:
c.ldsp a5,176(sp)
.Lpc_e320e:
c.ldsp a2,32(sp)
.Lpc_e3210:
c.ldsp a1,24(sp)
.Lpc_e3212:
c.ld a0,248(a5)
.Lpc_e3214:
c.ldsp a5,64(sp)
.Lpc_e3216:
c.sdsp a7,120(sp)
.Lpc_e3218:
div s10,a5,a3
.Lpc_e321c:
c.ldsp a3,272(sp)
.Lpc_e321e:
c.addiw s0,0
.Lpc_e3220:
div s3,a4,a3
.Lpc_e3224:
c.ldsp a3,264(sp)
.Lpc_e3226:
c.addiw s10,0
.Lpc_e3228:
div s1,a5,a3
.Lpc_e322c:
c.ldsp a3,240(sp)
.Lpc_e322e:
c.addiw s3,0
.Lpc_e3230:
mul a5,a5,a3
.Lpc_e3234:
c.ldsp a3,224(sp)
.Lpc_e3236:
c.addiw s1,0
.Lpc_e3238:
mul a3,a4,a3
.Lpc_e323c:
c.ldsp a4,232(sp)
.Lpc_e323e:
mul a4,a4,a6
.Lpc_e3242:
c.add a5,a3
.Lpc_e3244:
c.add a5,a4
.Lpc_e3246:
c.add a0,a5
.Lpc_e3248:
c.ldsp a5,280(sp)
.Lpc_e324a:
c.jalr a5
.Lpc_e324c:
c.ldsp a2,128(sp)
.Lpc_e324e:
c.ldsp a5,0(sp)
.Lpc_e3250:
csrrs a3,frm,zero
.Lpc_e3254:
c.ldsp a7,120(sp)
.Lpc_e3256:
bge a2,a5,.Lpc_e37aa
.Lpc_e325a:
c.ldsp a5,320(sp)
.Lpc_e325c:
vsetvli s8,zero,e8,m2,ta,ma
# LLVM-MCA-RISCV-LMUL M2
# LLVM-MCA-RISCV-SEW E8
.Lpc_e3260:
c.ldsp a1,328(sp)
.Lpc_e3262:
fsgnj.s fs10,fs4,fs4
.Lpc_e3266:
mul a4,s3,a5
.Lpc_e326a:
c.ldsp a5,312(sp)
.Lpc_e326c:
fmv.w.x fs11,zero
.Lpc_e3270:
c.mv s5,s6
.Lpc_e3272:
slliw s3,s8,0x1
.Lpc_e3276:
c.mv s6,s8
.Lpc_e3278:
mul s0,s0,a5
.Lpc_e327c:
c.ldsp a5,352(sp)
.Lpc_e327e:
c.add a4,a5
.Lpc_e3280:
c.ldsp a5,336(sp)
.Lpc_e3282:
mul s10,s10,a1
.Lpc_e3286:
mul s1,s1,a5
.Lpc_e328a:
c.ldsp a5,344(sp)
.Lpc_e328c:
c.add a5,s0
.Lpc_e328e:
c.add s10,a5
.Lpc_e3290:
c.mv s0,a2
.Lpc_e3292:
c.add s1,a4
.Lpc_e3294:
beq s4,zero,.Lpc_e3474
.Lpc_e3298:
sh1add a5,s0,s4
.Lpc_e329c:
lhu a5,0(a5)
.Lpc_e32a0:
fmv.h.x fa5,a5
.Lpc_e32a4:
fcvt.s.h fs0,fa5
.Lpc_e32a8:
fmul.s fs0,fs0,fs3
.Lpc_e32ac:
feq.s a5,fs0,fs4
.Lpc_e32b0:
bne a5,zero,.Lpc_e35a4
.Lpc_e32b4:
ld a3,248(s9)
.Lpc_e32b8:
c.ldsp a5,24(sp)
.Lpc_e32ba:
c.lwsp a0,32(sp)
.Lpc_e32bc:
c.ldsp t1,48(sp)
.Lpc_e32be:
c.li a7,1
.Lpc_e32c0:
c.li a6,0
.Lpc_e32c2:
c.add a3,s10
.Lpc_e32c4:
c.li a4,0
.Lpc_e32c6:
c.li a2,0
.Lpc_e32c8:
c.addi4spn a1,sp,420
.Lpc_e32ca:
c.jalr t1
.Lpc_e32cc:
fmv.w.x fa5,zero
.Lpc_e32d0:
flw fa0,420(sp)
.Lpc_e32d4:
flw fa4,40(sp)
.Lpc_e32d8:
feq.s a5,fs2,fa5
.Lpc_e32dc:
fmul.s fa0,fa4,fa0
.Lpc_e32e0:
c.bnez a5,.Lpc_e32ea
.Lpc_e32e2:
jal ra,.Lpc_83f40
.Lpc_e32e6:
fmul.s fa0,fa0,fs2
.Lpc_e32ea:
fadd.s fs0,fs0,fa0
.Lpc_e32ee:
ld a0,248(s2)
.Lpc_e32f2:
lw a4,0(s2)
.Lpc_e32f6:
c.li a5,1
.Lpc_e32f8:
add s8,a0,s1
.Lpc_e32fc:
fsw fs0,420(sp)
.Lpc_e3300:
beq a4,a5,.Lpc_e347a
.Lpc_e3304:
flt.s a5,fs10,fs0
.Lpc_e3308:
bne a5,zero,.Lpc_e35ee
.Lpc_e330c:
fsub.s fa0,fs0,fs10
.Lpc_e3310:
jal ra,.Lpc_851a0
.Lpc_e3314:
c.ldsp a5,56(sp)
.Lpc_e3316:
csrrs a3,frm,zero
.Lpc_e331a:
fsgnj.s fs1,fa0,fa0
.Lpc_e331e:
beq a5,zero,.Lpc_e3666
.Lpc_e3322:
c.ldsp a2,72(sp)
.Lpc_e3324:
c.mv a0,s8
.Lpc_e3326:
c.mv a1,s5
.Lpc_e3328:
c.jalr a5
.Lpc_e332a:
csrrs a3,frm,zero
.Lpc_e332e:
fsgnj.s fs9,fs5,fs5
.Lpc_e3332:
bge zero,s11,.Lpc_e3456
.Lpc_e3336:
c.li a4,0
.Lpc_e3338:
subw a5,s11,a4
.Lpc_e333c:
vsetvli a5,a5,e32,m8,ta,ma
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_e3340:
sh2add a2,a4,s7
.Lpc_e3344:
sh2add a1,a4,s5
.Lpc_e3348:
vle32.v v16,(a2)
.Lpc_e334c:
vle32.v v8,(a1)
.Lpc_e3350:
c.addw a4,a5
.Lpc_e3352:
vfmadd.vf v8,fs1,v16
.Lpc_e3356:
vse32.v v8,(a2)
.Lpc_e335a:
blt a4,s11,.Lpc_e3338
.Lpc_e335e:
c.ldsp a5,16(sp)
.Lpc_e3360:
c.addi s0,1
.Lpc_e3362:
fmadd.s fs11,fs9,fs11,fs1
.Lpc_e3366:
c.add s1,a5
.Lpc_e3368:
c.ldsp a5,8(sp)
.Lpc_e336a:
c.add s10,a5
.Lpc_e336c:
c.ldsp a5,0(sp)
.Lpc_e336e:
bne a5,s0,.Lpc_e3294
.Lpc_e3372:
lw a4,0(s2)
.Lpc_e3376:
c.li a5,1
.Lpc_e3378:
c.ldsp a7,120(sp)
.Lpc_e337a:
beq a4,a5,.Lpc_e35c0
.Lpc_e337e:
c.ldsp a5,144(sp)
.Lpc_e3380:
c.beqz a5,.Lpc_e33b0
.Lpc_e3382:
c.ldsp a5,128(sp)
.Lpc_e3384:
c.bnez a5,.Lpc_e33b0
.Lpc_e3386:
c.ldsp a5,144(sp)
.Lpc_e3388:
c.ldsp a4,160(sp)
.Lpc_e338a:
c.sdsp a7,24(sp)
.Lpc_e338c:
c.ld a5,248(a5)
.Lpc_e338e:
sh2add.uw a5,a4,a5
.Lpc_e3392:
flw fs1,0(a5)
.Lpc_e3396:
flt.s a5,fs10,fs1
.Lpc_e339a:
bne a5,zero,.Lpc_e37cc
.Lpc_e339e:
fsub.s fa0,fs1,fs10
.Lpc_e33a2:
jal ra,.Lpc_851a0
.Lpc_e33a6:
fadd.s fs11,fs11,fa0
.Lpc_e33aa:
csrrs a3,frm,zero
.Lpc_e33ae:
c.ldsp a7,24(sp)
.Lpc_e33b0:
c.ldsp a5,168(sp)
.Lpc_e33b2:
beq a5,zero,.Lpc_e36ea
.Lpc_e33b6:
c.ldsp a3,104(sp)
.Lpc_e33b8:
c.ldsp a4,112(sp)
.Lpc_e33ba:
c.mv t5,s7
.Lpc_e33bc:
fsw fs10,-8(a3)
.Lpc_e33c0:
fsw fs11,-4(a3)
.Lpc_e33c4:
vsetvli a5,a4,e8,m8,ta,ma
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E8
.Lpc_e33c8:
vle8.v v8,(t5)
.Lpc_e33cc:
c.sub a4,a5
.Lpc_e33ce:
c.add t5,a5
.Lpc_e33d0:
vse8.v v8,(a3)
.Lpc_e33d4:
c.add a3,a5
.Lpc_e33d6:
c.bnez a4,.Lpc_e33c4
.Lpc_e33d8:
c.ldsp a4,104(sp)
.Lpc_e33da:
c.ldsp a3,296(sp)
.Lpc_e33dc:
c.ldsp a5,80(sp)
.Lpc_e33de:
c.add a4,a3
.Lpc_e33e0:
c.sdsp a4,104(sp)
.Lpc_e33e2:
c.ldsp a4,288(sp)
.Lpc_e33e4:
c.addi a5,1
.Lpc_e33e6:
c.sdsp a5,80(sp)
.Lpc_e33e8:
bne a4,a5,.Lpc_e3128
.Lpc_e33ec:
c.fldsp fs4,488(sp)
.Lpc_e33ee:
c.fldsp fs5,480(sp)
.Lpc_e33f0:
c.fldsp fs6,472(sp)
.Lpc_e33f2:
c.fldsp fs9,448(sp)
.Lpc_e33f4:
c.fldsp fs10,440(sp)
.Lpc_e33f6:
c.fldsp fs11,432(sp)
.Lpc_e33f8:
auipc a5,0x14a
.Lpc_e33fc:
ld a5,448(a5) # .Lpc_22d5b8
.Lpc_e3400:
c.ldsp a4,424(sp)
.Lpc_e3402:
c.ld a5,0(a5)
.Lpc_e3404:
c.xor a5,a4
.Lpc_e3406:
c.li a4,0
.Lpc_e3408:
bne a5,zero,.Lpc_e3a1e
.Lpc_e340c:
ld ra,632(sp)
.Lpc_e3410:
ld s0,624(sp)
.Lpc_e3414:
fld fs0,520(sp)
.Lpc_e3418:
fld fs1,512(sp)
.Lpc_e341c:
c.fldsp fs2,504(sp)
.Lpc_e341e:
c.fldsp fs3,496(sp)
.Lpc_e3420:
c.fldsp fs7,464(sp)
.Lpc_e3422:
c.fldsp fs8,456(sp)
.Lpc_e3424:
ld s1,616(sp)
.Lpc_e3428:
ld s2,608(sp)
.Lpc_e342c:
ld s3,600(sp)
.Lpc_e3430:
ld s4,592(sp)
.Lpc_e3434:
ld s5,584(sp)
.Lpc_e3438:
ld s6,576(sp)
.Lpc_e343c:
ld s7,568(sp)
.Lpc_e3440:
ld s8,560(sp)
.Lpc_e3444:
ld s9,552(sp)
.Lpc_e3448:
ld s10,544(sp)
.Lpc_e344c:
ld s11,536(sp)
.Lpc_e3450:
addi sp,sp,640
.Lpc_e3454:
c.jr ra
.Lpc_e3456:
auipc a5,0xe8
.Lpc_e345a:
flw fs9,1758(a5) # .Lpc_1cbb34
.Lpc_e345e:
c.ldsp a5,16(sp)
.Lpc_e3460:
c.addi s0,1
.Lpc_e3462:
fmadd.s fs11,fs9,fs11,fs1
.Lpc_e3466:
c.add s1,a5
.Lpc_e3468:
c.ldsp a5,8(sp)
.Lpc_e346a:
c.add s10,a5
.Lpc_e346c:
c.ldsp a5,0(sp)
.Lpc_e346e:
bne a5,s0,.Lpc_e3294
.Lpc_e3472:
c.j .Lpc_e3372
.Lpc_e3474:
fmv.w.x fs0,zero
.Lpc_e3478:
c.j .Lpc_e32b4
.Lpc_e347a:
flt.s a5,fs10,fs0
.Lpc_e347e:
beq a5,zero,.Lpc_e3640
.Lpc_e3482:
fsub.s fa0,fs10,fs0
.Lpc_e3486:
jal ra,.Lpc_851a0
.Lpc_e348a:
subw a5,zero,s3
.Lpc_e348e:
and a5,s11,a5
.Lpc_e3492:
csrrs a3,frm,zero
.Lpc_e3496:
fsgnj.s fs9,fa0,fa0
.Lpc_e349a:
fcvt.h.s fa5,fa0
.Lpc_e349e:
bge zero,a5,.Lpc_e379e
.Lpc_e34a2:
slli a6,s3,0x1
.Lpc_e34a6:
vsetvli zero,s6,e16,m4,ta,ma
# LLVM-MCA-RISCV-LMUL M4
# LLVM-MCA-RISCV-SEW E16
.Lpc_e34aa:
c.mv a4,s5
.Lpc_e34ac:
slli a7,s6,0x1
.Lpc_e34b0:
c.li a1,0
.Lpc_e34b2:
vle16.v v4,(a4)
.Lpc_e34b6:
vfmul.vf v4,v4,fa5
.Lpc_e34ba:
vse16.v v4,(a4)
.Lpc_e34be:
add a2,a7,a4
.Lpc_e34c2:
vle16.v v4,(a2)
.Lpc_e34c6:
vfmul.vf v4,v4,fa5
.Lpc_e34ca:
vse16.v v4,(a2)
.Lpc_e34ce:
addw a1,s3,a1
.Lpc_e34d2:
c.add a4,a6
.Lpc_e34d4:
blt a1,a5,.Lpc_e34b2
.Lpc_e34d8:
bge a5,s11,.Lpc_e3592
.Lpc_e34dc:
c.mv a2,a5
.Lpc_e34de:
subw a4,s11,a2
.Lpc_e34e2:
vsetvli a4,a4,e16,m4,ta,ma
# LLVM-MCA-RISCV-LMUL M4
# LLVM-MCA-RISCV-SEW E16
.Lpc_e34e6:
sh1add a1,a2,s5
.Lpc_e34ea:
vle16.v v4,(a1)
.Lpc_e34ee:
c.addw a2,a4
.Lpc_e34f0:
vfmul.vf v4,v4,fa5
.Lpc_e34f4:
vse16.v v4,(a1)
.Lpc_e34f8:
blt a2,s11,.Lpc_e34de
.Lpc_e34fc:
fsgnj.h fa5,fs6,fs6
.Lpc_e3500:
fsgnj.s fs1,fs5,fs5
.Lpc_e3504:
slli a7,s6,0x1
.Lpc_e3508:
bge zero,a5,.Lpc_e354e
.Lpc_e350c:
vsetvli zero,s6,e16,m4,ta,ma
# LLVM-MCA-RISCV-LMUL M4
# LLVM-MCA-RISCV-SEW E16
.Lpc_e3510:
slli t6,s3,0x1
.Lpc_e3514:
c.mv a2,s8
.Lpc_e3516:
c.mv a4,s5
.Lpc_e3518:
c.li a6,0
.Lpc_e351a:
vle16.v v8,(a2)
.Lpc_e351e:
vle16.v v4,(a4)
.Lpc_e3522:
vfmacc.vf v4,fa5,v8
.Lpc_e3526:
vse16.v v4,(a4)
.Lpc_e352a:
add a1,a4,a7
.Lpc_e352e:
add a0,a7,a2
.Lpc_e3532:
vle16.v v4,(a1)
.Lpc_e3536:
vle16.v v8,(a0)
.Lpc_e353a:
vfmacc.vf v4,fa5,v8
.Lpc_e353e:
vse16.v v4,(a1)
.Lpc_e3542:
addw a6,a6,s3
.Lpc_e3546:
c.add a2,t6
.Lpc_e3548:
c.add a4,t6
.Lpc_e354a:
blt a6,a5,.Lpc_e351a
.Lpc_e354e:
bge a5,s11,.Lpc_e3578
.Lpc_e3552:
subw a4,s11,a5
.Lpc_e3556:
vsetvli a4,a4,e16,m4,ta,ma
# LLVM-MCA-RISCV-LMUL M4
# LLVM-MCA-RISCV-SEW E16
.Lpc_e355a:
sh1add a2,a5,s5
.Lpc_e355e:
sh1add a1,a5,s8
.Lpc_e3562:
vle16.v v4,(a2)
.Lpc_e3566:
vle16.v v8,(a1)
.Lpc_e356a:
c.addw a5,a4
.Lpc_e356c:
vfmacc.vf v4,fa5,v8
.Lpc_e3570:
vse16.v v4,(a2)
.Lpc_e3574:
blt a5,s11,.Lpc_e3552
.Lpc_e3578:
c.ldsp a5,16(sp)
.Lpc_e357a:
c.addi s0,1
.Lpc_e357c:
fmadd.s fs11,fs9,fs11,fs1
.Lpc_e3580:
c.add s1,a5
.Lpc_e3582:
c.ldsp a5,8(sp)
.Lpc_e3584:
fsgnj.s fs10,fs0,fs0
.Lpc_e3588:
c.add s10,a5
.Lpc_e358a:
c.ldsp a5,0(sp)
.Lpc_e358c:
bne a5,s0,.Lpc_e3294
.Lpc_e3590:
c.j .Lpc_e3372
.Lpc_e3592:
auipc a4,0xf1
.Lpc_e3596:
flh fa5,1206(a4) # .Lpc_1d4a48
.Lpc_e359a:
auipc a4,0xe8
.Lpc_e359e:
flw fs1,1434(a4) # .Lpc_1cbb34
.Lpc_e35a2:
c.j .Lpc_e3510
.Lpc_e35a4:
c.ldsp a5,16(sp)
.Lpc_e35a6:
c.addi s0,1
.Lpc_e35a8:
c.add s1,a5
.Lpc_e35aa:
c.ldsp a5,8(sp)
.Lpc_e35ac:
c.add s10,a5
.Lpc_e35ae:
c.ldsp a5,0(sp)
.Lpc_e35b0:
bne s0,a5,.Lpc_e3298
.Lpc_e35b4:
lw a4,0(s2)
.Lpc_e35b8:
c.li a5,1
.Lpc_e35ba:
c.ldsp a7,120(sp)
.Lpc_e35bc:
bne a4,a5,.Lpc_e337e
.Lpc_e35c0:
c.ldsp a5,72(sp)
.Lpc_e35c2:
bge zero,a5,.Lpc_e337e
.Lpc_e35c6:
c.ldsp a5,192(sp)
.Lpc_e35c8:
c.ldsp a4,400(sp)
.Lpc_e35ca:
c.ldsp a1,72(sp)
.Lpc_e35cc:
c.mv a2,s7
.Lpc_e35ce:
c.add a4,a5
.Lpc_e35d0:
vsetvli a5,a1,e16,mf2,ta,ma
# LLVM-MCA-RISCV-LMUL MF2
# LLVM-MCA-RISCV-SEW E16
.Lpc_e35d4:
vle16.v v2,(a4)
.Lpc_e35d8:
c.sub a1,a5
.Lpc_e35da:
sh1add a4,a5,a4
.Lpc_e35de:
vfwcvt.f.f.v v1,v2
.Lpc_e35e2:
vse32.v v1,(a2)
.Lpc_e35e6:
sh2add a2,a5,a2
.Lpc_e35ea:
c.bnez a1,.Lpc_e35d0
.Lpc_e35ec:
c.j .Lpc_e337e
.Lpc_e35ee:
fsub.s fa0,fs10,fs0
.Lpc_e35f2:
jal ra,.Lpc_851a0
.Lpc_e35f6:
csrrs a3,frm,zero
.Lpc_e35fa:
fsgnj.s fs9,fa0,fa0
.Lpc_e35fe:
bge zero,s11,.Lpc_e3768
.Lpc_e3602:
c.li a4,0
.Lpc_e3604:
subw a5,s11,a4
.Lpc_e3608:
vsetvli a5,a5,e32,m8,ta,ma
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_e360c:
sh2add a2,a4,s7
.Lpc_e3610:
vle32.v v8,(a2)
.Lpc_e3614:
c.addw a4,a5
.Lpc_e3616:
vfmul.vf v8,v8,fs9
.Lpc_e361a:
vse32.v v8,(a2)
.Lpc_e361e:
blt a4,s11,.Lpc_e3604
.Lpc_e3622:
c.ldsp a5,56(sp)
.Lpc_e3624:
c.beqz a5,.Lpc_e36dc
.Lpc_e3626:
c.ldsp a2,72(sp)
.Lpc_e3628:
c.mv a0,s8
.Lpc_e362a:
c.mv a1,s5
.Lpc_e362c:
c.jalr a5
.Lpc_e362e:
csrrs a3,frm,zero
.Lpc_e3632:
fsgnj.s fs10,fs0,fs0
.Lpc_e3636:
auipc a5,0xe8
.Lpc_e363a:
flw fs1,1278(a5) # .Lpc_1cbb34
.Lpc_e363e:
c.j .Lpc_e3336
.Lpc_e3640:
fsub.s fa0,fs0,fs10
.Lpc_e3644:
fsgnj.s fs9,fs5,fs5
.Lpc_e3648:
fsgnj.s fs0,fs10,fs10
.Lpc_e364c:
jal ra,.Lpc_851a0
.Lpc_e3650:
subw a5,zero,s3
.Lpc_e3654:
csrrs a3,frm,zero
.Lpc_e3658:
fsgnj.s fs1,fa0,fa0
.Lpc_e365c:
fcvt.h.s fa5,fa0
.Lpc_e3660:
and a5,s11,a5
.Lpc_e3664:
c.j .Lpc_e3504
.Lpc_e3666:
bge zero,s11,.Lpc_e3456
.Lpc_e366a:
auipc a5,0xe8
.Lpc_e366e:
flw fs9,1226(a5) # .Lpc_1cbb34
.Lpc_e3672:
c.li a4,0
.Lpc_e3674:
subw a5,s11,a4
.Lpc_e3678:
vsetvli a5,a5,e32,m8,ta,ma
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_e367c:
sh2add a2,a4,s7
.Lpc_e3680:
sh2add a1,a4,s8
.Lpc_e3684:
vle32.v v16,(a2)
.Lpc_e3688:
vle32.v v8,(a1)
.Lpc_e368c:
c.addw a4,a5
.Lpc_e368e:
vfmadd.vf v8,fs1,v16
.Lpc_e3692:
vse32.v v8,(a2)
.Lpc_e3696:
blt a4,s11,.Lpc_e3674
.Lpc_e369a:
c.ldsp a5,16(sp)
.Lpc_e369c:
c.addi s0,1
.Lpc_e369e:
fmadd.s fs11,fs9,fs11,fs1
.Lpc_e36a2:
c.add s1,a5
.Lpc_e36a4:
c.ldsp a5,8(sp)
.Lpc_e36a6:
c.add s10,a5
.Lpc_e36a8:
c.ldsp a5,0(sp)
.Lpc_e36aa:
bne a5,s0,.Lpc_e3294
.Lpc_e36ae:
c.j .Lpc_e3372
.Lpc_e36b0:
c.ldsp a2,376(sp)
.Lpc_e36b2:
c.li a1,0
.Lpc_e36b4:
c.mv a0,s6
.Lpc_e36b6:
jal ra,.Lpc_86930
.Lpc_e36ba:
c.ldsp a7,120(sp)
.Lpc_e36bc:
c.j .Lpc_e31c2
.Lpc_e36be:
subw a5,a3,a4
.Lpc_e36c2:
slliw a5,a5,0x1
.Lpc_e36c6:
c.addiw a5,1
.Lpc_e36c8:
fcvt.s.wu fa1,a5
.Lpc_e36cc:
fsgnj.s fa0,fs8,fs8
.Lpc_e36d0:
jal ra,.Lpc_83ae0
.Lpc_e36d4:
fsgnj.s fs3,fa0,fa0
.Lpc_e36d8:
c.ldsp a7,24(sp)
.Lpc_e36da:
c.j .Lpc_e3190
.Lpc_e36dc:
fsgnj.s fs10,fs0,fs0
.Lpc_e36e0:
auipc a5,0xe8
.Lpc_e36e4:
flw fs1,1108(a5) # .Lpc_1cbb34
.Lpc_e36e8:
c.j .Lpc_e3672
.Lpc_e36ea:
fmv.w.x fa5,zero
.Lpc_e36ee:
feq.s a5,fs11,fa5
.Lpc_e36f2:
c.bnez a5,.Lpc_e37a4
.Lpc_e36f4:
auipc a5,0xe8
.Lpc_e36f8:
flw fa5,1088(a5) # .Lpc_1cbb34
.Lpc_e36fc:
fdiv.s fa5,fa5,fs11
.Lpc_e3700:
csrrw zero,frm,a3
.Lpc_e3704:
bge zero,s11,.Lpc_e3728
.Lpc_e3708:
c.li a4,0
.Lpc_e370a:
subw a5,s11,a4
.Lpc_e370e:
sh2add a3,a4,s7
.Lpc_e3712:
vsetvli a5,a5,e32,m8,ta,ma
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_e3716:
vle32.v v8,(a3)
.Lpc_e371a:
c.addw a4,a5
.Lpc_e371c:
vfmul.vf v8,v8,fa5
.Lpc_e3720:
vse32.v v8,(a3)
.Lpc_e3724:
blt a4,s11,.Lpc_e370a
.Lpc_e3728:
c.ldsp a4,136(sp)
.Lpc_e372a:
c.ldsp a5,88(sp)
.Lpc_e372c:
c.ldsp a3,384(sp)
.Lpc_e372e:
c.ldsp a2,96(sp)
.Lpc_e3730:
mul a5,a5,a4
.Lpc_e3734:
c.ldsp a1,368(sp)
.Lpc_e3736:
c.ldsp a4,392(sp)
.Lpc_e3738:
c.mv t5,s7
.Lpc_e373a:
c.ld a4,248(a4)
.Lpc_e373c:
mul a5,a5,a3
.Lpc_e3740:
mul a2,a2,a3
.Lpc_e3744:
c.ldsp a3,64(sp)
.Lpc_e3746:
c.add a5,a3
.Lpc_e3748:
c.mv a3,a1
.Lpc_e374a:
c.add a5,a2
.Lpc_e374c:
mul a5,a5,a1
.Lpc_e3750:
c.add a5,a4
.Lpc_e3752:
vsetvli a4,a3,e8,m8,ta,ma
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E8
.Lpc_e3756:
vle8.v v8,(t5)
.Lpc_e375a:
c.sub a3,a4
.Lpc_e375c:
c.add t5,a4
.Lpc_e375e:
vse8.v v8,(a5)
.Lpc_e3762:
c.add a5,a4
.Lpc_e3764:
c.bnez a3,.Lpc_e3752
.Lpc_e3766:
c.j .Lpc_e33d8
.Lpc_e3768:
c.ldsp a5,56(sp)
.Lpc_e376a:
c.beqz a5,.Lpc_e377c
.Lpc_e376c:
c.ldsp a2,72(sp)
.Lpc_e376e:
sw a3,412(sp)
.Lpc_e3772:
c.mv a0,s8
.Lpc_e3774:
c.mv a1,s5
.Lpc_e3776:
c.jalr a5
.Lpc_e3778:
lw a3,412(sp)
.Lpc_e377c:
auipc a5,0xe8
.Lpc_e3780:
flw fs1,952(a5) # .Lpc_1cbb34
.Lpc_e3784:
c.ldsp a5,16(sp)
.Lpc_e3786:
c.addi s0,1
.Lpc_e3788:
fmadd.s fs11,fs9,fs11,fs1
.Lpc_e378c:
c.add s1,a5
.Lpc_e378e:
c.ldsp a5,8(sp)
.Lpc_e3790:
fsgnj.s fs10,fs0,fs0
.Lpc_e3794:
c.add s10,a5
.Lpc_e3796:
c.ldsp a5,0(sp)
.Lpc_e3798:
bne a5,s0,.Lpc_e3294
.Lpc_e379c:
c.j .Lpc_e3372
.Lpc_e379e:
blt a5,s11,.Lpc_e34dc
.Lpc_e37a2:
c.j .Lpc_e377c
.Lpc_e37a4:
fmv.w.x fa5,zero
.Lpc_e37a8:
c.j .Lpc_e3700
.Lpc_e37aa:
lw a4,0(s2)
.Lpc_e37ae:
c.li a5,1
.Lpc_e37b0:
beq a4,a5,.Lpc_e38c0
.Lpc_e37b4:
c.ldsp a5,144(sp)
.Lpc_e37b6:
c.beqz a5,.Lpc_e37ba
.Lpc_e37b8:
c.beqz a2,.Lpc_e387a
.Lpc_e37ba:
c.ldsp a5,168(sp)
.Lpc_e37bc:
c.beqz a5,.Lpc_e37a4
.Lpc_e37be:
auipc a5,0xe8
.Lpc_e37c2:
flw fs10,994(a5) # .Lpc_1cbba0
.Lpc_e37c6:
fmv.w.x fs11,zero
.Lpc_e37ca:
c.j .Lpc_e33b6
.Lpc_e37cc:
fsub.s fa0,fs10,fs1
.Lpc_e37d0:
jal ra,.Lpc_851a0
.Lpc_e37d4:
c.ldsp a7,24(sp)
.Lpc_e37d6:
c.li a4,0
.Lpc_e37d8:
bge zero,s11,.Lpc_e38d4
.Lpc_e37dc:
subw a5,s11,a4
.Lpc_e37e0:
vsetvli a5,a5,e32,m8,ta,ma
# LLVM-MCA-RISCV-LMUL M8
# LLVM-MCA-RISCV-SEW E32
.Lpc_e37e4:
sh2add a3,a4,s7
.Lpc_e37e8:
vle32.v v8,(a3)
.Lpc_e37ec:
c.addw a4,a5
.Lpc_e37ee:
vfmul.vf v8,v8,fa0
.Lpc_e37f2:
vse32.v v8,(a3)
.Lpc_e37f6:
blt a4,s11,.Lpc_e37dc
.Lpc_e37fa:
auipc a5,0xe8
.Lpc_e37fe:
flw fa4,826(a5) # .Lpc_1cbb34
.Lpc_e3802:
c.ldsp a5,168(sp)
.Lpc_e3804:
fsgnj.s fs10,fs1,fs1
.Lpc_e3808:
fmadd.s fs11,fa0,fs11,fa4
.Lpc_e380c:
bne a5,zero,.Lpc_e33b6
.Lpc_e3810:
fmv.w.x fa5,zero
.Lpc_e3814:
feq.s a5,fs11,fa5
.Lpc_e3818:
bne a5,zero,.Lpc_e3708
.Lpc_e381c:
fdiv.s fa5,fa4,fs11
.Lpc_e3820:
c.j .Lpc_e3708
.Lpc_e3822:
c.ldsp a5,56(sp)
.Lpc_e3824:
bne a5,zero,.Lpc_e307e
.Lpc_e3828:
auipc a5,0x14a
.Lpc_e382c:
ld a5,-624(a5) # .Lpc_22d5b8
.Lpc_e3830:
c.ldsp a4,424(sp)
.Lpc_e3832:
c.ld a5,0(a5)
.Lpc_e3834:
c.xor a5,a4
.Lpc_e3836:
c.li a4,0
.Lpc_e3838:
c.fsdsp fs4,488(sp)
.Lpc_e383a:
c.fsdsp fs5,480(sp)
.Lpc_e383c:
c.fsdsp fs6,472(sp)
.Lpc_e383e:
c.fsdsp fs9,448(sp)
.Lpc_e3840:
c.fsdsp fs10,440(sp)
.Lpc_e3842:
c.fsdsp fs11,432(sp)
.Lpc_e3844:
bne a5,zero,.Lpc_e3a2a
.Lpc_e3848:
c.lui a1,0x2
.Lpc_e384a:
addi a1,a1,361 # .Lpc_2169
.Lpc_e384e:
auipc a3,0xe4
.Lpc_e3852:
addi a3,a3,-1574 # .Lpc_1c7228
.Lpc_e3856:
auipc a2,0xe2
.Lpc_e385a:
addi a2,a2,1498 # .Lpc_1c5e30
.Lpc_e385e:
auipc a0,0xe3
.Lpc_e3862:
addi a0,a0,1514 # .Lpc_1c6e48
.Lpc_e3866:
jal ra,.Lpc_85420
.Lpc_e386a:
fmv.w.x fa5,a2
.Lpc_e386e:
fdiv.s fa5,fa5,fs2
.Lpc_e3872:
fsw fa5,40(sp)
.Lpc_e3876:
jal zero,.Lpc_e2fda
.Lpc_e387a:
auipc a5,0xe8
.Lpc_e387e:
flw fs10,806(a5) # .Lpc_1cbba0
.Lpc_e3882:
fmv.w.x fs11,zero
.Lpc_e3886:
c.j .Lpc_e3386
.Lpc_e3888:
c.sdsp zero,336(sp)
.Lpc_e388a:
c.sdsp zero,16(sp)
.Lpc_e388c:
c.sdsp zero,40(sp)
.Lpc_e388e:
c.sdsp zero,56(sp)
.Lpc_e3890:
c.sdsp zero,48(sp)
.Lpc_e3892:
c.sdsp zero,72(sp)
.Lpc_e3894:
c.sdsp zero,320(sp)
.Lpc_e3896:
jal zero,.Lpc_e2f10
.Lpc_e389a:
c.sdsp zero,328(sp)
.Lpc_e389c:
c.sdsp zero,8(sp)
.Lpc_e389e:
c.li s8,0
.Lpc_e38a0:
c.sdsp zero,24(sp)
.Lpc_e38a2:
c.li s11,0
.Lpc_e38a4:
c.sdsp zero,32(sp)
.Lpc_e38a6:
c.sdsp zero,312(sp)
.Lpc_e38a8:
jal zero,.Lpc_e2ee2
.Lpc_e38ac:
c.sdsp zero,240(sp)
.Lpc_e38ae:
c.sdsp zero,232(sp)
.Lpc_e38b0:
c.li a5,0
.Lpc_e38b2:
c.li s1,0
.Lpc_e38b4:
c.sdsp zero,152(sp)
.Lpc_e38b6:
c.sdsp zero,136(sp)
.Lpc_e38b8:
c.li s10,0
.Lpc_e38ba:
c.sdsp zero,224(sp)
.Lpc_e38bc:
jal zero,.Lpc_e2eb8
.Lpc_e38c0:
c.ldsp a5,72(sp)
.Lpc_e38c2:
bge zero,a5,.Lpc_e37b4
.Lpc_e38c6:
auipc a5,0xe8
.Lpc_e38ca:
flw fs10,730(a5) # .Lpc_1cbba0
.Lpc_e38ce:
fmv.w.x fs11,zero
.Lpc_e38d2:
c.j .Lpc_e35c6
.Lpc_e38d4:
auipc a5,0xe8
.Lpc_e38d8:
flw fa5,608(a5) # .Lpc_1cbb34
.Lpc_e38dc:
c.ldsp a5,168(sp)
.Lpc_e38de:
fsgnj.s fs10,fs1,fs1
.Lpc_e38e2:
fmadd.s fs11,fa0,fs11,fa5
.Lpc_e38e6:
bne a5,zero,.Lpc_e33b6
.Lpc_e38ea:
c.j .Lpc_e3728
.Lpc_e38ec:
auipc a5,0x14a
.Lpc_e38f0:
ld a5,-820(a5) # .Lpc_22d5b8
.Lpc_e38f4:
c.ldsp a4,424(sp)
.Lpc_e38f6:
c.ld a5,0(a5)
.Lpc_e38f8:
c.xor a5,a4
.Lpc_e38fa:
c.li a4,0
.Lpc_e38fc:
fsd fs0,520(sp)
.Lpc_e3900:
fsd fs1,512(sp)
.Lpc_e3904:
c.fsdsp fs2,504(sp)
.Lpc_e3906:
c.fsdsp fs3,496(sp)
.Lpc_e3908:
c.fsdsp fs4,488(sp)
.Lpc_e390a:
c.fsdsp fs5,480(sp)
.Lpc_e390c:
c.fsdsp fs6,472(sp)
.Lpc_e390e:
c.fsdsp fs7,464(sp)
.Lpc_e3910:
c.fsdsp fs8,456(sp)
.Lpc_e3912:
c.fsdsp fs9,448(sp)
.Lpc_e3914:
c.fsdsp fs10,440(sp)
.Lpc_e3916:
c.fsdsp fs11,432(sp)
.Lpc_e3918:
bne a5,zero,.Lpc_e3a2a
.Lpc_e391c:
c.lui a1,0x2
.Lpc_e391e:
addi a1,a1,312 # .Lpc_2138
.Lpc_e3922:
auipc a3,0xe4
.Lpc_e3926:
addi a3,a3,-1946 # .Lpc_1c7188
.Lpc_e392a:
auipc a2,0xe2
.Lpc_e392e:
addi a2,a2,1286 # .Lpc_1c5e30
.Lpc_e3932:
auipc a0,0xe3
.Lpc_e3936:
addi a0,a0,1302 # .Lpc_1c6e48
.Lpc_e393a:
jal ra,.Lpc_85420
.Lpc_e393e:
auipc a5,0x14a
.Lpc_e3942:
ld a5,-902(a5) # .Lpc_22d5b8
.Lpc_e3946:
c.ldsp a4,424(sp)
.Lpc_e3948:
c.ld a5,0(a5)
.Lpc_e394a:
c.xor a5,a4
.Lpc_e394c:
c.li a4,0
.Lpc_e394e:
c.fsdsp fs4,488(sp)
.Lpc_e3950:
c.fsdsp fs5,480(sp)
.Lpc_e3952:
c.fsdsp fs6,472(sp)
.Lpc_e3954:
c.fsdsp fs9,448(sp)
.Lpc_e3956:
c.fsdsp fs10,440(sp)
.Lpc_e3958:
c.fsdsp fs11,432(sp)
.Lpc_e395a:
c.bnez a5,.Lpc_e3a2a
.Lpc_e395c:
c.lui a1,0x2
.Lpc_e395e:
addi a1,a1,360 # .Lpc_2168
.Lpc_e3962:
auipc a3,0xe4
.Lpc_e3966:
addi a3,a3,-1898 # .Lpc_1c71f8
.Lpc_e396a:
auipc a2,0xe2
.Lpc_e396e:
addi a2,a2,1222 # .Lpc_1c5e30
.Lpc_e3972:
auipc a0,0xe3
.Lpc_e3976:
addi a0,a0,1238 # .Lpc_1c6e48
.Lpc_e397a:
jal ra,.Lpc_85420
.Lpc_e397e:
auipc a5,0x14a
.Lpc_e3982:
ld a5,-966(a5) # .Lpc_22d5b8
.Lpc_e3986:
c.ldsp a4,424(sp)
.Lpc_e3988:
c.ld a5,0(a5)
.Lpc_e398a:
c.xor a5,a4
.Lpc_e398c:
c.li a4,0
.Lpc_e398e:
fsd fs0,520(sp)
.Lpc_e3992:
fsd fs1,512(sp)
.Lpc_e3996:
c.fsdsp fs2,504(sp)
.Lpc_e3998:
c.fsdsp fs3,496(sp)
.Lpc_e399a:
c.fsdsp fs4,488(sp)
.Lpc_e399c:
c.fsdsp fs5,480(sp)
.Lpc_e399e:
c.fsdsp fs6,472(sp)
.Lpc_e39a0:
c.fsdsp fs7,464(sp)
.Lpc_e39a2:
c.fsdsp fs8,456(sp)
.Lpc_e39a4:
c.fsdsp fs9,448(sp)
.Lpc_e39a6:
c.fsdsp fs10,440(sp)
.Lpc_e39a8:
c.fsdsp fs11,432(sp)
.Lpc_e39aa:
c.bnez a5,.Lpc_e3a2a
.Lpc_e39ac:
c.lui a1,0x2
.Lpc_e39ae:
addi a1,a1,308 # .Lpc_2134
.Lpc_e39b2:
auipc a3,0xe3
.Lpc_e39b6:
addi a3,a3,1974 # .Lpc_1c7168
.Lpc_e39ba:
auipc a2,0xe2
.Lpc_e39be:
addi a2,a2,1142 # .Lpc_1c5e30
.Lpc_e39c2:
auipc a0,0xe3
.Lpc_e39c6:
addi a0,a0,1158 # .Lpc_1c6e48
.Lpc_e39ca:
jal ra,.Lpc_85420
.Lpc_e39ce:
auipc a5,0x14a
.Lpc_e39d2:
ld a5,-1046(a5) # .Lpc_22d5b8
.Lpc_e39d6:
c.ldsp a4,424(sp)
.Lpc_e39d8:
c.ld a5,0(a5)
.Lpc_e39da:
c.xor a5,a4
.Lpc_e39dc:
c.li a4,0
.Lpc_e39de:
fsd fs0,520(sp)
.Lpc_e39e2:
fsd fs1,512(sp)
.Lpc_e39e6:
c.fsdsp fs2,504(sp)
.Lpc_e39e8:
c.fsdsp fs3,496(sp)
.Lpc_e39ea:
c.fsdsp fs4,488(sp)
.Lpc_e39ec:
c.fsdsp fs5,480(sp)
.Lpc_e39ee:
c.fsdsp fs6,472(sp)
.Lpc_e39f0:
c.fsdsp fs7,464(sp)
.Lpc_e39f2:
c.fsdsp fs8,456(sp)
.Lpc_e39f4:
c.fsdsp fs9,448(sp)
.Lpc_e39f6:
c.fsdsp fs10,440(sp)
.Lpc_e39f8:
c.fsdsp fs11,432(sp)
.Lpc_e39fa:
c.bnez a5,.Lpc_e3a2a
.Lpc_e39fc:
c.lui a1,0x2
.Lpc_e39fe:
addi a1,a1,309 # .Lpc_2135
.Lpc_e3a02:
auipc a3,0xe3
.Lpc_e3a06:
addi a3,a3,1910 # .Lpc_1c7178
.Lpc_e3a0a:
auipc a2,0xe2
.Lpc_e3a0e:
addi a2,a2,1062 # .Lpc_1c5e30
.Lpc_e3a12:
auipc a0,0xe3
.Lpc_e3a16:
addi a0,a0,1078 # .Lpc_1c6e48
.Lpc_e3a1a:
jal ra,.Lpc_85420
.Lpc_e3a1e:
c.fsdsp fs4,488(sp)
.Lpc_e3a20:
c.fsdsp fs5,480(sp)
.Lpc_e3a22:
c.fsdsp fs6,472(sp)
.Lpc_e3a24:
c.fsdsp fs9,448(sp)
.Lpc_e3a26:
c.fsdsp fs10,440(sp)
.Lpc_e3a28:
c.fsdsp fs11,432(sp)
.Lpc_e3a2a:
jal ra,.Lpc_87330
.Lpc_e3a2e:
auipc a5,0x14a
.Lpc_e3a32:
ld a5,-1142(a5) # .Lpc_22d5b8
.Lpc_e3a36:
c.ldsp a4,424(sp)
.Lpc_e3a38:
c.ld a5,0(a5)
.Lpc_e3a3a:
c.xor a5,a4
.Lpc_e3a3c:
c.li a4,0
.Lpc_e3a3e:
fsd fs0,520(sp)
.Lpc_e3a42:
fsd fs1,512(sp)
.Lpc_e3a46:
c.fsdsp fs2,504(sp)
.Lpc_e3a48:
c.fsdsp fs3,496(sp)
.Lpc_e3a4a:
c.fsdsp fs4,488(sp)
.Lpc_e3a4c:
c.fsdsp fs5,480(sp)
.Lpc_e3a4e:
c.fsdsp fs6,472(sp)
.Lpc_e3a50:
c.fsdsp fs7,464(sp)
.Lpc_e3a52:
c.fsdsp fs8,456(sp)
.Lpc_e3a54:
c.fsdsp fs9,448(sp)
.Lpc_e3a56:
c.fsdsp fs10,440(sp)
.Lpc_e3a58:
c.fsdsp fs11,432(sp)
.Lpc_e3a5a:
c.bnez a5,.Lpc_e3a2a
.Lpc_e3a5c:
c.lui a1,0x2
.Lpc_e3a5e:
addi a1,a1,314 # .Lpc_213a
.Lpc_e3a62:
auipc a3,0xe3
.Lpc_e3a66:
addi a3,a3,1894 # .Lpc_1c71c8
.Lpc_e3a6a:
auipc a2,0xe2
.Lpc_e3a6e:
addi a2,a2,966 # .Lpc_1c5e30
.Lpc_e3a72:
auipc a0,0xe3
.Lpc_e3a76:
addi a0,a0,982 # .Lpc_1c6e48
.Lpc_e3a7a:
jal ra,.Lpc_85420
.Lpc_e3a7e:
auipc a5,0x14a
.Lpc_e3a82:
ld a5,-1222(a5) # .Lpc_22d5b8
.Lpc_e3a86:
c.ldsp a4,424(sp)
.Lpc_e3a88:
c.ld a5,0(a5)
.Lpc_e3a8a:
c.xor a5,a4
.Lpc_e3a8c:
c.li a4,0
.Lpc_e3a8e:
fsd fs0,520(sp)
.Lpc_e3a92:
fsd fs1,512(sp)
.Lpc_e3a96:
c.fsdsp fs2,504(sp)
.Lpc_e3a98:
c.fsdsp fs3,496(sp)
.Lpc_e3a9a:
c.fsdsp fs4,488(sp)
.Lpc_e3a9c:
c.fsdsp fs5,480(sp)
.Lpc_e3a9e:
c.fsdsp fs6,472(sp)
.Lpc_e3aa0:
c.fsdsp fs7,464(sp)
.Lpc_e3aa2:
c.fsdsp fs8,456(sp)
.Lpc_e3aa4:
c.fsdsp fs9,448(sp)
.Lpc_e3aa6:
c.fsdsp fs10,440(sp)
.Lpc_e3aa8:
c.fsdsp fs11,432(sp)
.Lpc_e3aaa:
c.bnez a5,.Lpc_e3a2a
.Lpc_e3aac:
c.lui a1,0x2
.Lpc_e3aae:
addi a1,a1,313 # .Lpc_2139
.Lpc_e3ab2:
auipc a3,0xe3
.Lpc_e3ab6:
addi a3,a3,1782 # .Lpc_1c71a8
.Lpc_e3aba:
auipc a2,0xe2
.Lpc_e3abe:
addi a2,a2,886 # .Lpc_1c5e30
.Lpc_e3ac2:
auipc a0,0xe3
.Lpc_e3ac6:
addi a0,a0,902 # .Lpc_1c6e48
.Lpc_e3aca:
jal ra,.Lpc_85420
.Lpc_e3ace:
auipc a5,0x14a
.Lpc_e3ad2:
ld a5,-1302(a5) # .Lpc_22d5b8
.Lpc_e3ad6:
c.ldsp a4,424(sp)
.Lpc_e3ad8:
c.ld a5,0(a5)
.Lpc_e3ada:
c.xor a5,a4
.Lpc_e3adc:
c.li a4,0
.Lpc_e3ade:
fsd fs0,520(sp)
.Lpc_e3ae2:
fsd fs1,512(sp)
.Lpc_e3ae6:
c.fsdsp fs2,504(sp)
.Lpc_e3ae8:
c.fsdsp fs3,496(sp)
.Lpc_e3aea:
c.fsdsp fs4,488(sp)
.Lpc_e3aec:
c.fsdsp fs5,480(sp)
.Lpc_e3aee:
c.fsdsp fs6,472(sp)
.Lpc_e3af0:
c.fsdsp fs7,464(sp)
.Lpc_e3af2:
c.fsdsp fs8,456(sp)
.Lpc_e3af4:
c.fsdsp fs9,448(sp)
.Lpc_e3af6:
c.fsdsp fs10,440(sp)
.Lpc_e3af8:
c.fsdsp fs11,432(sp)
.Lpc_e3afa:
c.bnez a5,.Lpc_e3a2a
.Lpc_e3afc:
c.lui a1,0x2
.Lpc_e3afe:
addi a1,a1,323 # .Lpc_2143
.Lpc_e3b02:
auipc a3,0xe2
.Lpc_e3b06:
addi a3,a3,1206 # .Lpc_1c5fb8
.Lpc_e3b0a:
auipc a2,0xe2
.Lpc_e3b0e:
addi a2,a2,806 # .Lpc_1c5e30
.Lpc_e3b12:
auipc a0,0xe3
.Lpc_e3b16:
addi a0,a0,822 # .Lpc_1c6e48
.Lpc_e3b1a:
jal ra,.Lpc_85420
.Lpc_e3b1e:
auipc a5,0x14a
.Lpc_e3b22:
ld a5,-1382(a5) # .Lpc_22d5b8
.Lpc_e3b26:
c.ldsp a4,424(sp)
.Lpc_e3b28:
c.ld a5,0(a5)
.Lpc_e3b2a:
c.xor a5,a4
.Lpc_e3b2c:
c.li a4,0
.Lpc_e3b2e:
fsd fs0,520(sp)
.Lpc_e3b32:
fsd fs1,512(sp)
.Lpc_e3b36:
c.fsdsp fs2,504(sp)
.Lpc_e3b38:
c.fsdsp fs3,496(sp)
.Lpc_e3b3a:
c.fsdsp fs4,488(sp)
.Lpc_e3b3c:
c.fsdsp fs5,480(sp)
.Lpc_e3b3e:
c.fsdsp fs6,472(sp)
.Lpc_e3b40:
c.fsdsp fs7,464(sp)
.Lpc_e3b42:
c.fsdsp fs8,456(sp)
.Lpc_e3b44:
c.fsdsp fs9,448(sp)
.Lpc_e3b46:
c.fsdsp fs10,440(sp)
.Lpc_e3b48:
c.fsdsp fs11,432(sp)
.Lpc_e3b4a:
bne a5,zero,.Lpc_e3a2a
.Lpc_e3b4e:
c.lui a1,0x2
.Lpc_e3b50:
addi a1,a1,316 # .Lpc_213c
.Lpc_e3b54:
auipc a3,0xe3
.Lpc_e3b58:
addi a3,a3,1684 # .Lpc_1c71e8
.Lpc_e3b5c:
auipc a2,0xe2
.Lpc_e3b60:
addi a2,a2,724 # .Lpc_1c5e30
.Lpc_e3b64:
auipc a0,0xe3
.Lpc_e3b68:
addi a0,a0,740 # .Lpc_1c6e48
.Lpc_e3b6c:
jal ra,.Lpc_85420
.Lpc_e3b70:
auipc a5,0x14a
.Lpc_e3b74:
ld a5,-1464(a5) # .Lpc_22d5b8
.Lpc_e3b78:
c.ldsp a4,424(sp)
.Lpc_e3b7a:
c.ld a5,0(a5)
.Lpc_e3b7c:
c.xor a5,a4
.Lpc_e3b7e:
c.li a4,0
.Lpc_e3b80:
fsd fs0,520(sp)
.Lpc_e3b84:
fsd fs1,512(sp)
.Lpc_e3b88:
c.fsdsp fs2,504(sp)
.Lpc_e3b8a:
c.fsdsp fs3,496(sp)
.Lpc_e3b8c:
c.fsdsp fs4,488(sp)
.Lpc_e3b8e:
c.fsdsp fs5,480(sp)
.Lpc_e3b90:
c.fsdsp fs6,472(sp)
.Lpc_e3b92:
c.fsdsp fs7,464(sp)
.Lpc_e3b94:
c.fsdsp fs8,456(sp)
.Lpc_e3b96:
c.fsdsp fs9,448(sp)
.Lpc_e3b98:
c.fsdsp fs10,440(sp)
.Lpc_e3b9a:
c.fsdsp fs11,432(sp)
.Lpc_e3b9c:
bne a5,zero,.Lpc_e3a2a
.Lpc_e3ba0:
c.lui a1,0x2
.Lpc_e3ba2:
addi a1,a1,326 # .Lpc_2146
.Lpc_e3ba6:
auipc a3,0xe2
.Lpc_e3baa:
addi a3,a3,1098 # .Lpc_1c5ff0
.Lpc_e3bae:
auipc a2,0xe2
.Lpc_e3bb2:
addi a2,a2,642 # .Lpc_1c5e30
.Lpc_e3bb6:
auipc a0,0xe3
.Lpc_e3bba:
addi a0,a0,658 # .Lpc_1c6e48
.Lpc_e3bbe:
jal ra,.Lpc_85420
.Lpc_e3bc2:
auipc a5,0x14a
.Lpc_e3bc6:
ld a5,-1546(a5) # .Lpc_22d5b8
.Lpc_e3bca:
c.ldsp a4,424(sp)
.Lpc_e3bcc:
c.ld a5,0(a5)
.Lpc_e3bce:
c.xor a5,a4
.Lpc_e3bd0:
c.li a4,0
.Lpc_e3bd2:
fsd fs0,520(sp)
.Lpc_e3bd6:
fsd fs1,512(sp)
.Lpc_e3bda:
c.fsdsp fs2,504(sp)
.Lpc_e3bdc:
c.fsdsp fs3,496(sp)
.Lpc_e3bde:
c.fsdsp fs4,488(sp)
.Lpc_e3be0:
c.fsdsp fs5,480(sp)
.Lpc_e3be2:
c.fsdsp fs6,472(sp)
.Lpc_e3be4:
c.fsdsp fs7,464(sp)
.Lpc_e3be6:
c.fsdsp fs8,456(sp)
.Lpc_e3be8:
c.fsdsp fs9,448(sp)
.Lpc_e3bea:
c.fsdsp fs10,440(sp)
.Lpc_e3bec:
c.fsdsp fs11,432(sp)
.Lpc_e3bee:
bne a5,zero,.Lpc_e3a2a
.Lpc_e3bf2:
c.lui a1,0x2
.Lpc_e3bf4:
addi a1,a1,325 # .Lpc_2145
.Lpc_e3bf8:
auipc a3,0xe2
.Lpc_e3bfc:
addi a3,a3,1000 # .Lpc_1c5fe0
.Lpc_e3c00:
auipc a2,0xe2
.Lpc_e3c04:
addi a2,a2,560 # .Lpc_1c5e30
.Lpc_e3c08:
auipc a0,0xe3
.Lpc_e3c0c:
addi a0,a0,576 # .Lpc_1c6e48
.Lpc_e3c10:
jal ra,.Lpc_85420
.Lpc_e3c14:
auipc a5,0x14a
.Lpc_e3c18:
ld a5,-1628(a5) # .Lpc_22d5b8
.Lpc_e3c1c:
c.ldsp a4,424(sp)
.Lpc_e3c1e:
c.ld a5,0(a5)
.Lpc_e3c20:
c.xor a5,a4
.Lpc_e3c22:
c.li a4,0
.Lpc_e3c24:
fsd fs0,520(sp)
.Lpc_e3c28:
fsd fs1,512(sp)
.Lpc_e3c2c:
c.fsdsp fs2,504(sp)
.Lpc_e3c2e:
c.fsdsp fs3,496(sp)
.Lpc_e3c30:
c.fsdsp fs4,488(sp)
.Lpc_e3c32:
c.fsdsp fs5,480(sp)
.Lpc_e3c34:
c.fsdsp fs6,472(sp)
.Lpc_e3c36:
c.fsdsp fs7,464(sp)
.Lpc_e3c38:
c.fsdsp fs8,456(sp)
.Lpc_e3c3a:
c.fsdsp fs9,448(sp)
.Lpc_e3c3c:
c.fsdsp fs10,440(sp)
.Lpc_e3c3e:
c.fsdsp fs11,432(sp)
.Lpc_e3c40:
bne a5,zero,.Lpc_e3a2a
.Lpc_e3c44:
c.lui a1,0x2
.Lpc_e3c46:
addi a1,a1,324 # .Lpc_2144
.Lpc_e3c4a:
auipc a3,0xe2
.Lpc_e3c4e:
addi a3,a3,902 # .Lpc_1c5fd0
.Lpc_e3c52:
auipc a2,0xe2
.Lpc_e3c56:
addi a2,a2,478 # .Lpc_1c5e30
.Lpc_e3c5a:
auipc a0,0xe3
.Lpc_e3c5e:
addi a0,a0,494 # .Lpc_1c6e48
.Lpc_e3c62:
jal ra,.Lpc_85420
