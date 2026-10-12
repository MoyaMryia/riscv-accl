.text
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_15f08:
lw t5,0(a0)
.Lpc_15f0c:
c.addi16sp sp,-224
.Lpc_15f0e:
c.sdsp s1,200(sp)
.Lpc_15f10:
c.sdsp s2,192(sp)
.Lpc_15f12:
c.sdsp s0,208(sp)
.Lpc_15f14:
c.mv s0,a0
.Lpc_15f16:
c.sdsp s3,184(sp)
.Lpc_15f18:
c.mv s3,a3
.Lpc_15f1a:
mulw a5,t5,a2
.Lpc_15f1e:
c.sdsp s10,128(sp)
.Lpc_15f20:
c.sdsp ra,216(sp)
.Lpc_15f22:
addi s10,a1,64
.Lpc_15f26:
c.sdsp s4,176(sp)
.Lpc_15f28:
addw a4,a5,t5
.Lpc_15f2c:
c.sdsp s5,168(sp)
.Lpc_15f2e:
sraiw s1,a4,0x1f
.Lpc_15f32:
c.sdsp s6,160(sp)
.Lpc_15f34:
sraiw s2,a5,0x1f
.Lpc_15f38:
c.sdsp s7,152(sp)
.Lpc_15f3a:
srliw s1,s1,0x1e
.Lpc_15f3e:
c.sdsp s8,144(sp)
.Lpc_15f40:
srliw s2,s2,0x1e
.Lpc_15f44:
c.sdsp s9,136(sp)
.Lpc_15f46:
c.addw s1,a4
.Lpc_15f48:
addw s2,s2,a5
.Lpc_15f4c:
sraiw s1,s1,0x2
.Lpc_15f50:
sraiw s2,s2,0x2
.Lpc_15f54:
beq a3,zero,.Lpc_162d0
.Lpc_15f58:
lw t5,8(a0)
.Lpc_15f5c:
bge zero,t5,.Lpc_162b0
.Lpc_15f60:
c.sdsp s11,120(sp)
.Lpc_15f62:
c.li a6,0
.Lpc_15f64:
c.lw a5,4(a0)
.Lpc_15f66:
c.li t6,12
.Lpc_15f68:
c.li a0,2
.Lpc_15f6a:
c.li a1,16
.Lpc_15f6c:
bge zero,a5,.Lpc_16758
.Lpc_15f70:
c.li t1,1
.Lpc_15f72:
c.li t2,2
.Lpc_15f74:
c.li t0,3
.Lpc_15f76:
c.li a7,0
.Lpc_15f78:
bge s2,s1,.Lpc_166dc
.Lpc_15f7c:
c.mv t5,a7
.Lpc_15f7e:
c.mv s4,t1
.Lpc_15f80:
addiw t4,t2,0
.Lpc_15f84:
addiw t3,t0,0
.Lpc_15f88:
c.mv a2,s2
.Lpc_15f8a:
c.j .Lpc_160a2
.Lpc_15f8c:
lw s6,0(s0)
.Lpc_15f90:
slliw s9,a2,0x1
.Lpc_15f94:
ld s8,16(s0)
.Lpc_15f98:
addw s9,s9,a2
.Lpc_15f9c:
c.slli s5,0x2
.Lpc_15f9e:
mulw s11,s6,a6
.Lpc_15fa2:
slliw s7,s11,0x1
.Lpc_15fa6:
addw s7,s7,s11
.Lpc_15faa:
c.addi s7,16
.Lpc_15fac:
c.add s7,a7
.Lpc_15fae:
c.add s7,s9
.Lpc_15fb0:
c.slli s7,0x2
.Lpc_15fb2:
c.add s8,s7
.Lpc_15fb4:
ld s7,64(s0)
.Lpc_15fb8:
vlse32.v v2,(s8),t6
.Lpc_15fbc:
c.add s5,s7
.Lpc_15fbe:
vlse32.v v3,(s5),a1
.Lpc_15fc2:
vfmul.vv v2,v2,v3
.Lpc_15fc6:
vfadd.vv v1,v1,v2
.Lpc_15fca:
bltu a0,t1,.Lpc_160fa
.Lpc_15fce:
mulw s11,s6,a6
.Lpc_15fd2:
ld s8,16(s0)
.Lpc_15fd6:
slliw s9,a2,0x1
.Lpc_15fda:
addw s9,s9,a2
.Lpc_15fde:
slliw s5,s11,0x1
.Lpc_15fe2:
addw s5,s5,s11
.Lpc_15fe6:
c.addi s5,16
.Lpc_15fe8:
c.add s5,t1
.Lpc_15fea:
c.add s5,s9
.Lpc_15fec:
c.addi a3,17
.Lpc_15fee:
c.slli s5,0x2
.Lpc_15ff0:
c.slli a3,0x2
.Lpc_15ff2:
c.add s8,s5
.Lpc_15ff4:
add s5,s7,a3
.Lpc_15ff8:
vlse32.v v2,(s8),t6
.Lpc_15ffc:
vlse32.v v3,(s5),a1
.Lpc_16000:
vfmul.vv v2,v2,v3
.Lpc_16004:
vfadd.vv v1,v1,v2
.Lpc_16008:
blt a0,t4,.Lpc_16136
.Lpc_1600c:
mulw s11,s6,a6
.Lpc_16010:
ld s8,16(s0)
.Lpc_16014:
slliw s9,a2,0x1
.Lpc_16018:
addw s9,s9,a2
.Lpc_1601c:
slliw s5,s11,0x1
.Lpc_16020:
addw s5,s5,s11
.Lpc_16024:
c.addi s5,16
.Lpc_16026:
c.add s5,t2
.Lpc_16028:
c.add s5,s9
.Lpc_1602a:
c.slli s5,0x2
.Lpc_1602c:
c.add s8,s5
.Lpc_1602e:
addi s5,a3,4
.Lpc_16032:
vlse32.v v2,(s8),t6
.Lpc_16036:
c.add s5,s7
.Lpc_16038:
vlse32.v v3,(s5),a1
.Lpc_1603c:
vfmul.vv v2,v2,v3
.Lpc_16040:
vfadd.vv v1,v1,v2
.Lpc_16044:
blt a0,t3,.Lpc_16170
.Lpc_16048:
mulw s11,s6,a6
.Lpc_1604c:
ld s8,16(s0)
.Lpc_16050:
slliw s9,a2,0x1
.Lpc_16054:
addw s9,s9,a2
.Lpc_16058:
slliw s5,s11,0x1
.Lpc_1605c:
addw s5,s5,s11
.Lpc_16060:
c.addi s5,16
.Lpc_16062:
c.add s5,t0
.Lpc_16064:
c.add s5,s9
.Lpc_16066:
c.slli s5,0x2
.Lpc_16068:
c.add s8,s5
.Lpc_1606a:
vlse32.v v2,(s8),t6
.Lpc_1606e:
mulw a5,a5,a6
.Lpc_16072:
ld s5,112(s0)
.Lpc_16076:
c.addi a3,8
.Lpc_16078:
c.add a3,s7
.Lpc_1607a:
addw a5,a5,t5
.Lpc_1607e:
vlse32.v v3,(a3),a1
.Lpc_16082:
mulw a5,s6,a5
.Lpc_16086:
vfmul.vv v2,v2,v3
.Lpc_1608a:
vfadd.vv v1,v1,v2
.Lpc_1608e:
c.addi a5,16
.Lpc_16090:
c.add a5,a2
.Lpc_16092:
c.slli a5,0x2
.Lpc_16094:
c.add s5,a5
.Lpc_16096:
vse32.v v1,(s5)
.Lpc_1609a:
c.addw a2,a4
.Lpc_1609c:
c.lw a5,4(s0)
.Lpc_1609e:
bge a2,s1,.Lpc_166dc
.Lpc_160a2:
subw a4,s1,a2
.Lpc_160a6:
vsetvli a4,a4,e32,m1,ta,ma
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_160aa:
slliw a3,a2,0x2
.Lpc_160ae:
vmv.v.i v1,0
.Lpc_160b2:
addi s5,a3,16
.Lpc_160b6:
bgeu a0,a7,.Lpc_15f8c
.Lpc_160ba:
lw s7,12(s0)
.Lpc_160be:
mulw s11,a5,a6
.Lpc_160c2:
ld s8,40(s0)
.Lpc_160c6:
addiw s9,a2,16
.Lpc_160ca:
c.slli s5,0x2
.Lpc_160cc:
lw s6,0(s0)
.Lpc_160d0:
addw s11,s11,t5
.Lpc_160d4:
c.addiw s11,-3
.Lpc_160d6:
mulw s7,s7,s11
.Lpc_160da:
c.add s7,s9
.Lpc_160dc:
c.slli s7,0x2
.Lpc_160de:
c.add s8,s7
.Lpc_160e0:
ld s7,64(s0)
.Lpc_160e4:
vle32.v v2,(s8)
.Lpc_160e8:
c.add s5,s7
.Lpc_160ea:
vlse32.v v3,(s5),a1
.Lpc_160ee:
vfmul.vv v2,v2,v3
.Lpc_160f2:
vfadd.vv v1,v1,v2
.Lpc_160f6:
bgeu a0,t1,.Lpc_15fce
.Lpc_160fa:
lw s5,12(s0)
.Lpc_160fe:
mulw s11,a5,a6
.Lpc_16102:
ld s8,40(s0)
.Lpc_16106:
addiw s9,a2,16
.Lpc_1610a:
c.addi a3,17
.Lpc_1610c:
addw s11,s11,s4
.Lpc_16110:
c.addiw s11,-3
.Lpc_16112:
mulw s5,s5,s11
.Lpc_16116:
c.slli a3,0x2
.Lpc_16118:
c.add s5,s9
.Lpc_1611a:
c.slli s5,0x2
.Lpc_1611c:
c.add s8,s5
.Lpc_1611e:
add s5,s7,a3
.Lpc_16122:
vle32.v v2,(s8)
.Lpc_16126:
vlse32.v v3,(s5),a1
.Lpc_1612a:
vfmul.vv v2,v2,v3
.Lpc_1612e:
vfadd.vv v1,v1,v2
.Lpc_16132:
bge a0,t4,.Lpc_1600c
.Lpc_16136:
lw s5,12(s0)
.Lpc_1613a:
mulw s11,a5,a6
.Lpc_1613e:
ld s8,40(s0)
.Lpc_16142:
addiw s9,a2,16
.Lpc_16146:
addw s11,s11,t4
.Lpc_1614a:
c.addiw s11,-3
.Lpc_1614c:
mulw s5,s5,s11
.Lpc_16150:
c.add s5,s9
.Lpc_16152:
c.slli s5,0x2
.Lpc_16154:
c.add s8,s5
.Lpc_16156:
addi s5,a3,4
.Lpc_1615a:
vle32.v v2,(s8)
.Lpc_1615e:
c.add s5,s7
.Lpc_16160:
vlse32.v v3,(s5),a1
.Lpc_16164:
vfmul.vv v2,v2,v3
.Lpc_16168:
vfadd.vv v1,v1,v2
.Lpc_1616c:
bge a0,t3,.Lpc_16048
.Lpc_16170:
lw s5,12(s0)
.Lpc_16174:
mulw s11,a5,a6
.Lpc_16178:
ld s8,40(s0)
.Lpc_1617c:
addiw s9,a2,16
.Lpc_16180:
addw s11,s11,t3
.Lpc_16184:
c.addiw s11,-3
.Lpc_16186:
mulw s5,s5,s11
.Lpc_1618a:
c.add s5,s9
.Lpc_1618c:
c.slli s5,0x2
.Lpc_1618e:
c.add s8,s5
.Lpc_16190:
vle32.v v2,(s8)
.Lpc_16194:
c.j .Lpc_1606e
.Lpc_16196:
subw a7,s1,s2
.Lpc_1619a:
c.lw a3,12(s0)
.Lpc_1619c:
c.slli a7,0x20
.Lpc_1619e:
c.sdsp s11,120(sp)
.Lpc_161a0:
slliw a2,a4,0x1
.Lpc_161a4:
ld s5,40(s0)
.Lpc_161a8:
srli a7,a7,0x20
.Lpc_161ac:
ld s9,16(s0)
.Lpc_161b0:
addw s11,a2,a4
.Lpc_161b4:
add a4,a7,s2
.Lpc_161b8:
c.sdsp a4,24(sp)
.Lpc_161ba:
addi a4,a5,16
.Lpc_161be:
c.sdsp a4,0(sp)
.Lpc_161c0:
addi a4,t3,16
.Lpc_161c4:
c.sdsp a4,8(sp)
.Lpc_161c6:
addiw t2,a5,-3
.Lpc_161ca:
addiw t0,a5,-2
.Lpc_161ce:
addiw t6,a5,-1
.Lpc_161d2:
addi a4,t1,16
.Lpc_161d6:
mulw s8,a5,a3
.Lpc_161da:
c.sdsp a4,16(sp)
.Lpc_161dc:
mulw t2,t2,a3
.Lpc_161e0:
mulw t0,t0,a3
.Lpc_161e4:
mulw t6,t6,a3
.Lpc_161e8:
slli s3,s2,0x1
.Lpc_161ec:
addi s5,s5,64
.Lpc_161f0:
c.add s3,s2
.Lpc_161f2:
c.li s4,16
.Lpc_161f4:
c.li s7,0
.Lpc_161f6:
c.li a1,2
.Lpc_161f8:
c.mv s0,s10
.Lpc_161fa:
c.ldsp a4,16(sp)
.Lpc_161fc:
addiw t4,s4,-16
.Lpc_16200:
c.ldsp a0,24(sp)
.Lpc_16202:
add a3,t6,s2
.Lpc_16206:
c.sdsp s6,32(sp)
.Lpc_16208:
c.slli a3,0x2
.Lpc_1620a:
slli s10,t2,0x2
.Lpc_1620e:
c.add a3,s5
.Lpc_16210:
add s1,a4,t4
.Lpc_16214:
c.ldsp a4,0(sp)
.Lpc_16216:
add a2,s1,s3
.Lpc_1621a:
sub s1,zero,s1
.Lpc_1621e:
c.slli s1,0x2
.Lpc_16220:
add a6,a0,t6
.Lpc_16224:
add a7,a4,t4
.Lpc_16228:
c.ldsp a4,8(sp)
.Lpc_1622a:
sub a0,zero,t6
.Lpc_1622e:
c.slli a7,0x2
.Lpc_16230:
c.slli a0,0x2
.Lpc_16232:
c.slli a2,0x2
.Lpc_16234:
c.add t4,a4
.Lpc_16236:
c.slli t4,0x2
.Lpc_16238:
add a4,s4,s3
.Lpc_1623c:
c.slli a4,0x2
.Lpc_1623e:
c.slli a6,0x2
.Lpc_16240:
c.add a7,s1
.Lpc_16242:
c.add t4,s1
.Lpc_16244:
slli s1,t0,0x2
.Lpc_16248:
c.add a2,s9
.Lpc_1624a:
c.add a4,s6
.Lpc_1624c:
c.add a6,s5
.Lpc_1624e:
c.add s10,a0
.Lpc_16250:
c.add s1,a0
.Lpc_16252:
add a0,a7,a2
.Lpc_16256:
bge a1,a5,.Lpc_1625e
.Lpc_1625a:
add a0,s10,a3
.Lpc_1625e:
flw fa5,0(a0)
.Lpc_16262:
add s6,a2,t4
.Lpc_16266:
c.mv a0,a2
.Lpc_16268:
c.addi a2,12
.Lpc_1626a:
fsw fa5,0(a4)
.Lpc_1626e:
bge a1,t3,.Lpc_16276
.Lpc_16272:
add s6,a3,s1
.Lpc_16276:
flw fa5,0(s6)
.Lpc_1627a:
fsw fa5,4(a4)
.Lpc_1627e:
bge a1,t1,.Lpc_16284
.Lpc_16282:
c.mv a0,a3
.Lpc_16284:
flw fa5,0(a0)
.Lpc_16288:
c.addi a3,4
.Lpc_1628a:
c.addi a4,12
.Lpc_1628c:
fsw fa5,-4(a4)
.Lpc_16290:
bne a6,a3,.Lpc_16252
.Lpc_16294:
c.addiw s7,1
.Lpc_16296:
c.ldsp s6,32(sp)
.Lpc_16298:
addw t2,s8,t2
.Lpc_1629c:
addw t0,t0,s8
.Lpc_162a0:
addw t6,t6,s8
.Lpc_162a4:
addw s4,s4,s11
.Lpc_162a8:
bne s7,t5,.Lpc_161fa
.Lpc_162ac:
c.ldsp s11,120(sp)
.Lpc_162ae:
c.mv s10,s0
.Lpc_162b0:
c.ldsp s0,208(sp)
.Lpc_162b2:
c.mv a0,s10
.Lpc_162b4:
c.ldsp ra,216(sp)
.Lpc_162b6:
c.ldsp s1,200(sp)
.Lpc_162b8:
c.ldsp s2,192(sp)
.Lpc_162ba:
c.ldsp s3,184(sp)
.Lpc_162bc:
c.ldsp s4,176(sp)
.Lpc_162be:
c.ldsp s5,168(sp)
.Lpc_162c0:
c.ldsp s6,160(sp)
.Lpc_162c2:
c.ldsp s7,152(sp)
.Lpc_162c4:
c.ldsp s8,144(sp)
.Lpc_162c6:
c.ldsp s9,136(sp)
.Lpc_162c8:
c.ldsp s10,128(sp)
.Lpc_162ca:
c.addi16sp sp,224
.Lpc_162cc:
jal zero,.Lpc_3a388
.Lpc_162d0:
c.lw a5,8(a0)
.Lpc_162d2:
c.sdsp a5,40(sp)
.Lpc_162d4:
bge zero,a5,.Lpc_16492
.Lpc_162d8:
c.lw a2,4(a0)
.Lpc_162da:
c.li a5,-2
.Lpc_162dc:
blt a2,a5,.Lpc_16492
.Lpc_162e0:
bge s2,s1,.Lpc_16492
.Lpc_162e4:
c.ld a5,88(s0)
.Lpc_162e6:
slliw a4,t5,0x1
.Lpc_162ea:
addw a4,a4,t5
.Lpc_162ee:
ld t1,40(a0)
.Lpc_162f2:
lw t2,12(a0)
.Lpc_162f6:
addiw a0,a2,3
.Lpc_162fa:
c.sdsp a4,56(sp)
.Lpc_162fc:
mulw a4,t5,a0
.Lpc_16300:
c.sdsp s11,120(sp)
.Lpc_16302:
addiw t4,a2,2
.Lpc_16306:
c.sdsp a5,8(sp)
.Lpc_16308:
c.li a3,2
.Lpc_1630a:
c.sdsp a0,64(sp)
.Lpc_1630c:
c.mv a5,t4
.Lpc_1630e:
c.sdsp a4,72(sp)
.Lpc_16310:
c.ld a1,16(s0)
.Lpc_16312:
blt a3,t4,.Lpc_16772
.Lpc_16316:
addi a3,a1,64
.Lpc_1631a:
c.ldsp a1,8(sp)
.Lpc_1631c:
subw a7,s1,s2
.Lpc_16320:
c.sdsp a3,80(sp)
.Lpc_16322:
c.slli a7,0x20
.Lpc_16324:
c.sdsp zero,0(sp)
.Lpc_16326:
srli a7,a7,0x20
.Lpc_1632a:
c.sdsp a2,104(sp)
.Lpc_1632c:
addiw a4,s1,-1
.Lpc_16330:
subw a4,a4,s2
.Lpc_16334:
add s9,s2,a7
.Lpc_16338:
c.sdsp a4,16(sp)
.Lpc_1633a:
slli a3,a7,0x2
.Lpc_1633e:
slli a4,s9,0x1
.Lpc_16342:
c.add a4,s9
.Lpc_16344:
addi a1,a1,64
.Lpc_16348:
c.sdsp a4,48(sp)
.Lpc_1634a:
csrrs t6,vlenb,zero
.Lpc_1634e:
c.sdsp a1,96(sp)
.Lpc_16350:
sub a3,a7,a3
.Lpc_16354:
addiw t0,a5,0
.Lpc_16358:
addiw s8,a5,1
.Lpc_1635c:
c.addiw a5,-2
.Lpc_1635e:
c.sdsp a5,88(sp)
.Lpc_16360:
c.addi t6,-8
.Lpc_16362:
c.slli a3,0x2
.Lpc_16364:
slli t3,t5,0x2
.Lpc_16368:
c.li s7,0
.Lpc_1636a:
c.li s6,0
.Lpc_1636c:
c.li a5,0
.Lpc_1636e:
c.li a4,0
.Lpc_16370:
addi s5,s2,17
.Lpc_16374:
addi s4,s2,16
.Lpc_16378:
c.mv a0,s10
.Lpc_1637a:
c.mv a1,s3
.Lpc_1637c:
c.ldsp a2,0(sp)
.Lpc_1637e:
add s10,a4,s2
.Lpc_16382:
c.ldsp a6,48(sp)
.Lpc_16384:
c.slli s10,0x2
.Lpc_16386:
c.li s11,0
.Lpc_16388:
add s3,a2,a6
.Lpc_1638c:
c.ldsp a2,8(sp)
.Lpc_1638e:
c.slli s3,0x2
.Lpc_16390:
c.add s10,a2
.Lpc_16392:
c.ldsp a2,80(sp)
.Lpc_16394:
c.add s3,a2
.Lpc_16396:
add a2,s3,a3
.Lpc_1639a:
c.mv a6,s10
.Lpc_1639c:
flw fa5,0(a2)
.Lpc_163a0:
c.addi a2,12
.Lpc_163a2:
c.addi a6,4
.Lpc_163a4:
fsw fa5,60(a6)
.Lpc_163a8:
bne a2,s3,.Lpc_1639c
.Lpc_163ac:
c.addi s11,1
.Lpc_163ae:
addiw a6,s11,0
.Lpc_163b2:
c.add s10,t3
.Lpc_163b4:
addi s3,a2,4
.Lpc_163b8:
bge t0,a6,.Lpc_16396
.Lpc_163bc:
blt t4,s8,.Lpc_1646c
.Lpc_163c0:
c.ldsp a2,88(sp)
.Lpc_163c2:
addw s3,s8,s6
.Lpc_163c6:
mulw s3,s3,t5
.Lpc_163ca:
c.sdsp s7,24(sp)
.Lpc_163cc:
c.mv s11,s8
.Lpc_163ce:
c.add s3,s2
.Lpc_163d0:
addw s10,a2,a5
.Lpc_163d4:
c.ldsp a2,96(sp)
.Lpc_163d6:
mulw s10,s10,t2
.Lpc_163da:
c.slli s3,0x2
.Lpc_163dc:
c.add s3,a2
.Lpc_163de:
c.mv a2,a0
.Lpc_163e0:
c.ldsp a0,16(sp)
.Lpc_163e2:
c.li a6,2
.Lpc_163e4:
bgeu a6,a0,.Lpc_1643a
.Lpc_163e8:
c.sdsp a2,32(sp)
.Lpc_163ea:
add a2,s5,s10
.Lpc_163ee:
c.slli a2,0x2
.Lpc_163f0:
c.add a2,t1
.Lpc_163f2:
sub a2,s3,a2
.Lpc_163f6:
bgeu t6,a2,.Lpc_16438
.Lpc_163fa:
add s7,s4,s10
.Lpc_163fe:
c.slli s7,0x2
.Lpc_16400:
c.add s7,t1
.Lpc_16402:
c.mv a6,s3
.Lpc_16404:
c.mv a0,a7
.Lpc_16406:
vsetvli a2,a0,e32,m1,ta,ma
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_1640a:
vle32.v v1,(s7)
.Lpc_1640e:
c.sub a0,a2
.Lpc_16410:
vse32.v v1,(a6)
.Lpc_16414:
c.slli a2,0x2
.Lpc_16416:
c.add s7,a2
.Lpc_16418:
c.add a6,a2
.Lpc_1641a:
c.bnez a0,.Lpc_16406
.Lpc_1641c:
c.addiw s11,1
.Lpc_1641e:
blt t4,s11,.Lpc_166fe
.Lpc_16422:
addw s10,t2,s10
.Lpc_16426:
add a2,s5,s10
.Lpc_1642a:
c.slli a2,0x2
.Lpc_1642c:
c.add s3,t3
.Lpc_1642e:
c.add a2,t1
.Lpc_16430:
sub a2,s3,a2
.Lpc_16434:
bltu t6,a2,.Lpc_163fa
.Lpc_16438:
c.ldsp a2,32(sp)
.Lpc_1643a:
add a0,s2,s10
.Lpc_1643e:
add s7,s9,s10
.Lpc_16442:
c.slli a0,0x2
.Lpc_16444:
c.slli s7,0x2
.Lpc_16446:
c.add a0,t1
.Lpc_16448:
c.add s7,t1
.Lpc_1644a:
c.mv a6,s3
.Lpc_1644c:
flw fa5,64(a0)
.Lpc_16450:
c.addi a0,4
.Lpc_16452:
c.addi a6,4
.Lpc_16454:
fsw fa5,-4(a6)
.Lpc_16458:
bne a0,s7,.Lpc_1644c
.Lpc_1645c:
c.addiw s11,1
.Lpc_1645e:
addw s10,t2,s10
.Lpc_16462:
c.add s3,t3
.Lpc_16464:
bge t4,s11,.Lpc_163e0
.Lpc_16468:
c.ldsp s7,24(sp)
.Lpc_1646a:
c.mv a0,a2
.Lpc_1646c:
c.ldsp a6,0(sp)
.Lpc_1646e:
c.addiw s7,1
.Lpc_16470:
c.ldsp a2,56(sp)
.Lpc_16472:
addw a2,a2,a6
.Lpc_16476:
c.sdsp a2,0(sp)
.Lpc_16478:
c.ldsp a2,72(sp)
.Lpc_1647a:
c.addw a4,a2
.Lpc_1647c:
c.ldsp a2,104(sp)
.Lpc_1647e:
c.addw a5,a2
.Lpc_16480:
c.ldsp a2,64(sp)
.Lpc_16482:
addw s6,a2,s6
.Lpc_16486:
c.ldsp a2,40(sp)
.Lpc_16488:
bne s7,a2,.Lpc_1637c
.Lpc_1648c:
c.ldsp s11,120(sp)
.Lpc_1648e:
c.mv s10,a0
.Lpc_16490:
c.mv s3,a1
.Lpc_16492:
c.mv a0,s10
.Lpc_16494:
jal ra,.Lpc_3a388
.Lpc_16498:
lw t5,8(s0)
.Lpc_1649c:
bge zero,t5,.Lpc_162b0
.Lpc_164a0:
c.lw a5,4(s0)
.Lpc_164a2:
c.li t3,0
.Lpc_164a4:
c.li a7,16
.Lpc_164a6:
bge zero,a5,.Lpc_16766
.Lpc_164aa:
c.li a6,0
.Lpc_164ac:
c.li t5,3
.Lpc_164ae:
c.li t4,2
.Lpc_164b0:
c.li t1,1
.Lpc_164b2:
c.mv a0,s2
.Lpc_164b4:
bge s2,s1,.Lpc_165a6
.Lpc_164b8:
lw s7,0(s0)
.Lpc_164bc:
addiw a3,a5,3
.Lpc_164c0:
mulw a3,a3,t3
.Lpc_164c4:
ld s4,88(s0)
.Lpc_164c8:
mulw a2,a5,t3
.Lpc_164cc:
ld t2,64(s0)
.Lpc_164d0:
addiw t0,a0,16
.Lpc_164d4:
ld t6,112(s0)
.Lpc_164d8:
addw a5,a3,a6
.Lpc_164dc:
mulw a5,s7,a5
.Lpc_164e0:
addw s6,a3,t1
.Lpc_164e4:
slliw s5,a0,0x2
.Lpc_164e8:
mulw s6,s6,s7
.Lpc_164ec:
addw a4,a3,t4
.Lpc_164f0:
c.add a5,t0
.Lpc_164f2:
addi s8,s5,16
.Lpc_164f6:
mulw a1,a4,s7
.Lpc_164fa:
c.slli s8,0x2
.Lpc_164fc:
slli a4,a5,0x2
.Lpc_16500:
subw a5,s1,a0
.Lpc_16504:
vsetvli a5,a5,e32,m1,ta,ma
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_16508:
c.add s6,t0
.Lpc_1650a:
c.add a4,s4
.Lpc_1650c:
vmv.v.i v1,0
.Lpc_16510:
addw a3,a3,t5
.Lpc_16514:
vle32.v v2,(a4)
.Lpc_16518:
c.addi s5,17
.Lpc_1651a:
c.add s8,t2
.Lpc_1651c:
c.slli s5,0x2
.Lpc_1651e:
vlse32.v v3,(s8),a7
.Lpc_16522:
mulw a3,a3,s7
.Lpc_16526:
vfmul.vv v2,v2,v3
.Lpc_1652a:
c.slli s6,0x2
.Lpc_1652c:
vfadd.vv v1,v1,v2
.Lpc_16530:
add a4,a1,t0
.Lpc_16534:
add a1,s4,s6
.Lpc_16538:
add s6,t2,s5
.Lpc_1653c:
vle32.v v2,(a1)
.Lpc_16540:
vlse32.v v3,(s6),a7
.Lpc_16544:
addw a2,a2,a6
.Lpc_16548:
c.slli a4,0x2
.Lpc_1654a:
vfmul.vv v2,v2,v3
.Lpc_1654e:
mulw a2,a2,s7
.Lpc_16552:
vfadd.vv v1,v1,v2
.Lpc_16556:
c.add t0,a3
.Lpc_16558:
c.add a4,s4
.Lpc_1655a:
addi a3,s5,4
.Lpc_1655e:
vle32.v v2,(a4)
.Lpc_16562:
add a4,t2,a3
.Lpc_16566:
vlse32.v v3,(a4),a7
.Lpc_1656a:
c.slli t0,0x2
.Lpc_1656c:
addi a1,s5,8
.Lpc_16570:
vfmul.vv v2,v2,v3
.Lpc_16574:
addi a4,a2,16
.Lpc_16578:
vfadd.vv v1,v1,v2
.Lpc_1657c:
add a2,s4,t0
.Lpc_16580:
add a3,t2,a1
.Lpc_16584:
vle32.v v2,(a2)
.Lpc_16588:
c.add a4,a0
.Lpc_1658a:
vlse32.v v3,(a3),a7
.Lpc_1658e:
c.slli a4,0x2
.Lpc_16590:
vfmul.vv v2,v2,v3
.Lpc_16594:
c.add t6,a4
.Lpc_16596:
vfadd.vv v1,v1,v2
.Lpc_1659a:
c.addw a0,a5
.Lpc_1659c:
vse32.v v1,(t6)
.Lpc_165a0:
c.lw a5,4(s0)
.Lpc_165a2:
blt a0,s1,.Lpc_164b8
.Lpc_165a6:
c.addiw a6,1
.Lpc_165a8:
c.addiw t1,1
.Lpc_165aa:
c.addiw t4,1
.Lpc_165ac:
c.addiw t5,1
.Lpc_165ae:
blt a6,a5,.Lpc_164b2
.Lpc_165b2:
lw t5,8(s0)
.Lpc_165b6:
c.addiw t3,1
.Lpc_165b8:
blt t3,t5,.Lpc_164a6
.Lpc_165bc:
bge zero,t5,.Lpc_162b0
.Lpc_165c0:
bge s2,s1,.Lpc_162b0
.Lpc_165c4:
c.lw a4,0(s0)
.Lpc_165c6:
addiw t3,a5,1
.Lpc_165ca:
ld s6,136(s0)
.Lpc_165ce:
addiw t1,a5,2
.Lpc_165d2:
bne s3,zero,.Lpc_16196
.Lpc_165d6:
subw s1,s1,s2
.Lpc_165da:
ld t4,88(s0)
.Lpc_165de:
slli s0,s1,0x20
.Lpc_165e2:
mulw a7,a5,a4
.Lpc_165e6:
mulw t3,t3,a4
.Lpc_165ea:
mulw t1,t1,a4
.Lpc_165ee:
c.srli s0,0x20
.Lpc_165f0:
c.addiw a5,3
.Lpc_165f2:
add t2,s2,s0
.Lpc_165f6:
mulw t0,a5,a4
.Lpc_165fa:
slliw s4,a4,0x1
.Lpc_165fe:
slli s5,t2,0x1
.Lpc_16602:
slli t6,s2,0x1
.Lpc_16606:
c.addiw t3,16
.Lpc_16608:
c.addiw t1,16
.Lpc_1660a:
c.add s5,t2
.Lpc_1660c:
c.addiw a7,16
.Lpc_1660e:
addw s4,s4,a4
.Lpc_16612:
c.add t6,s2
.Lpc_16614:
c.li s1,16
.Lpc_16616:
add a5,t6,s1
.Lpc_1661a:
add a3,a7,t2
.Lpc_1661e:
add a4,s1,s5
.Lpc_16622:
add a2,a7,s2
.Lpc_16626:
add s8,t2,t3
.Lpc_1662a:
add s7,s2,t3
.Lpc_1662e:
c.slli a5,0x2
.Lpc_16630:
c.slli a3,0x2
.Lpc_16632:
c.slli a4,0x2
.Lpc_16634:
c.slli a2,0x2
.Lpc_16636:
c.slli s8,0x2
.Lpc_16638:
c.slli s7,0x2
.Lpc_1663a:
c.add a5,s6
.Lpc_1663c:
c.add a4,s6
.Lpc_1663e:
c.add s7,t4
.Lpc_16640:
c.add a3,t4
.Lpc_16642:
c.add a2,t4
.Lpc_16644:
c.add s8,t4
.Lpc_16646:
sltu a3,a5,a3
.Lpc_1664a:
sltu a6,a2,a4
.Lpc_1664e:
sltu a1,a5,s8
.Lpc_16652:
sltu a0,s7,a4
.Lpc_16656:
sltiu a6,a6,1
.Lpc_1665a:
sltiu a0,a0,1
.Lpc_1665e:
sltiu a3,a3,1
.Lpc_16662:
sltiu a1,a1,1
.Lpc_16666:
c.or a1,a0
.Lpc_16668:
or a3,a3,a6
.Lpc_1666c:
c.and a3,a1
.Lpc_1666e:
add a1,s2,t1
.Lpc_16672:
c.slli a1,0x2
.Lpc_16674:
c.mv a6,a5
.Lpc_16676:
c.mv a0,s7
.Lpc_16678:
c.add a1,t4
.Lpc_1667a:
c.beqz a3,.Lpc_16704
.Lpc_1667c:
add a3,t2,t1
.Lpc_16680:
c.slli a3,0x2
.Lpc_16682:
c.add a3,t4
.Lpc_16684:
sltu s9,a1,a4
.Lpc_16688:
sltu a4,a5,a3
.Lpc_1668c:
sltiu a4,a4,1
.Lpc_16690:
sltiu a3,s9,1
.Lpc_16694:
c.or a4,a3
.Lpc_16696:
c.mv a3,s0
.Lpc_16698:
c.beqz a4,.Lpc_16704
.Lpc_1669a:
vsetvli a5,a3,e32,m1,ta,ma
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_1669e:
slli a4,a5,0x1
.Lpc_166a2:
vle32.v v3,(a2)
.Lpc_166a6:
vle32.v v4,(a0)
.Lpc_166aa:
vle32.v v5,(a1)
.Lpc_166ae:
c.add a4,a5
.Lpc_166b0:
vsseg3e32.v v3,(a6)
.Lpc_166b4:
c.sub a3,a5
.Lpc_166b6:
c.slli a4,0x2
.Lpc_166b8:
c.slli a5,0x2
.Lpc_166ba:
c.add a6,a4
.Lpc_166bc:
c.add a2,a5
.Lpc_166be:
c.add a0,a5
.Lpc_166c0:
c.add a1,a5
.Lpc_166c2:
c.bnez a3,.Lpc_1669a
.Lpc_166c4:
c.addiw s3,1
.Lpc_166c6:
addw a7,t0,a7
.Lpc_166ca:
addw s1,s4,s1
.Lpc_166ce:
addw t3,t0,t3
.Lpc_166d2:
addw t1,t0,t1
.Lpc_166d6:
bne s3,t5,.Lpc_16616
.Lpc_166da:
c.j .Lpc_162b0
.Lpc_166dc:
c.addi a7,1
.Lpc_166de:
addiw a4,a7,0
.Lpc_166e2:
c.addi t0,1
.Lpc_166e4:
c.addi t2,1
.Lpc_166e6:
c.addi t1,1
.Lpc_166e8:
blt a4,a5,.Lpc_15f78
.Lpc_166ec:
lw t5,8(s0)
.Lpc_166f0:
c.addiw a6,1
.Lpc_166f2:
blt a6,t5,.Lpc_15f6c
.Lpc_166f6:
c.ldsp s11,120(sp)
.Lpc_166f8:
blt zero,t5,.Lpc_165c0
.Lpc_166fc:
c.j .Lpc_162b0
.Lpc_166fe:
c.ldsp s7,24(sp)
.Lpc_16700:
c.ldsp a0,32(sp)
.Lpc_16702:
c.j .Lpc_1646c
.Lpc_16704:
sub a3,zero,t3
.Lpc_16708:
c.mv a4,s7
.Lpc_1670a:
c.slli a3,0x2
.Lpc_1670c:
slli a0,a7,0x2
.Lpc_16710:
slli a1,t1,0x2
.Lpc_16714:
add a2,a4,a0
.Lpc_16718:
c.add a2,a3
.Lpc_1671a:
flw fa5,0(a2)
.Lpc_1671e:
add a2,a4,a1
.Lpc_16722:
c.add a2,a3
.Lpc_16724:
c.addi a4,4
.Lpc_16726:
c.addi a5,12
.Lpc_16728:
fsw fa5,-12(a5)
.Lpc_1672c:
flw fa5,-4(a4)
.Lpc_16730:
fsw fa5,-8(a5)
.Lpc_16734:
flw fa5,0(a2)
.Lpc_16738:
fsw fa5,-4(a5)
.Lpc_1673c:
bne a4,s8,.Lpc_16714
.Lpc_16740:
c.addiw s3,1
.Lpc_16742:
addw a7,t0,a7
.Lpc_16746:
addw s1,s4,s1
.Lpc_1674a:
addw t3,t0,t3
.Lpc_1674e:
addw t1,t0,t1
.Lpc_16752:
bne s3,t5,.Lpc_16616
.Lpc_16756:
c.j .Lpc_162b0
.Lpc_16758:
c.addiw a6,1
.Lpc_1675a:
c.ldsp s11,120(sp)
.Lpc_1675c:
bge a6,t5,.Lpc_165c0
.Lpc_16760:
blt zero,t5,.Lpc_165c0
.Lpc_16764:
c.j .Lpc_162b0
.Lpc_16766:
c.addiw t3,1
.Lpc_16768:
bge t3,t5,.Lpc_165c0
.Lpc_1676c:
blt zero,t5,.Lpc_165c0
.Lpc_16770:
c.j .Lpc_162b0
.Lpc_16772:
c.mv a5,a3
.Lpc_16774:
c.j .Lpc_16316
