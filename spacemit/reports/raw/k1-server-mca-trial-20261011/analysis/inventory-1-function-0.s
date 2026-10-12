.text
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_15fc8:
lw t5,0(a0)
.Lpc_15fcc:
c.addi16sp sp,-240
.Lpc_15fce:
c.sdsp s1,216(sp)
.Lpc_15fd0:
mulw a5,t5,a2
.Lpc_15fd4:
c.sdsp s2,208(sp)
.Lpc_15fd6:
c.sdsp s0,224(sp)
.Lpc_15fd8:
c.sdsp s3,200(sp)
.Lpc_15fda:
c.sdsp s10,144(sp)
.Lpc_15fdc:
c.sdsp ra,232(sp)
.Lpc_15fde:
c.sdsp s4,192(sp)
.Lpc_15fe0:
c.sdsp s5,184(sp)
.Lpc_15fe2:
c.sdsp s6,176(sp)
.Lpc_15fe4:
c.sdsp s7,168(sp)
.Lpc_15fe6:
addw a4,a5,t5
.Lpc_15fea:
sraiw s1,a4,0x1f
.Lpc_15fee:
sraiw s2,a5,0x1f
.Lpc_15ff2:
srliw s1,s1,0x1e
.Lpc_15ff6:
srliw s2,s2,0x1e
.Lpc_15ffa:
c.addw s1,a4
.Lpc_15ffc:
addw s2,s2,a5
.Lpc_16000:
c.mv s0,a0
.Lpc_16002:
c.mv s3,a3
.Lpc_16004:
addi s10,a1,64
.Lpc_16008:
sraiw s1,s1,0x2
.Lpc_1600c:
sraiw s2,s2,0x2
.Lpc_16010:
beq a3,zero,.Lpc_16392
.Lpc_16014:
lw t5,8(a0)
.Lpc_16018:
bge zero,t5,.Lpc_16376
.Lpc_1601c:
c.lw a5,4(a0)
.Lpc_1601e:
c.sdsp s8,160(sp)
.Lpc_16020:
c.sdsp s9,152(sp)
.Lpc_16022:
c.sdsp s11,136(sp)
.Lpc_16024:
c.li a6,0
.Lpc_16026:
c.li a0,2
.Lpc_16028:
c.li t6,12
.Lpc_1602a:
c.li a1,16
.Lpc_1602c:
bge zero,a5,.Lpc_16822
.Lpc_16030:
c.li t1,1
.Lpc_16032:
c.li t2,2
.Lpc_16034:
c.li t0,3
.Lpc_16036:
c.li a7,0
.Lpc_16038:
bge s2,s1,.Lpc_167a6
.Lpc_1603c:
c.mv t5,a7
.Lpc_1603e:
c.mv s4,t1
.Lpc_16040:
addiw t4,t2,0
.Lpc_16044:
addiw t3,t0,0
.Lpc_16048:
c.mv a2,s2
.Lpc_1604a:
c.j .Lpc_16160
.Lpc_1604c:
lw s6,0(s0)
.Lpc_16050:
slliw s9,a2,0x1
.Lpc_16054:
ld s8,16(s0)
.Lpc_16058:
mulw s11,s6,a6
.Lpc_1605c:
addw s9,s9,a2
.Lpc_16060:
c.slli s5,0x2
.Lpc_16062:
slliw s7,s11,0x1
.Lpc_16066:
addw s7,s7,s11
.Lpc_1606a:
c.addi s7,16
.Lpc_1606c:
c.add s7,a7
.Lpc_1606e:
c.add s7,s9
.Lpc_16070:
c.slli s7,0x2
.Lpc_16072:
c.add s8,s7
.Lpc_16074:
ld s7,64(s0)
.Lpc_16078:
vlse32.v v2,(s8),t6
.Lpc_1607c:
c.add s5,s7
.Lpc_1607e:
vlse32.v v3,(s5),a1
.Lpc_16082:
vfmul.vv v2,v2,v3
.Lpc_16086:
vfadd.vv v1,v1,v2
.Lpc_1608a:
bltu a0,t1,.Lpc_161b8
.Lpc_1608e:
mulw s11,s6,a6
.Lpc_16092:
slliw s9,a2,0x1
.Lpc_16096:
ld s8,16(s0)
.Lpc_1609a:
addw s9,s9,a2
.Lpc_1609e:
c.addi a3,17
.Lpc_160a0:
c.slli a3,0x2
.Lpc_160a2:
slliw s5,s11,0x1
.Lpc_160a6:
addw s5,s5,s11
.Lpc_160aa:
c.addi s5,16
.Lpc_160ac:
c.add s5,t1
.Lpc_160ae:
c.add s5,s9
.Lpc_160b0:
c.slli s5,0x2
.Lpc_160b2:
c.add s8,s5
.Lpc_160b4:
add s5,s7,a3
.Lpc_160b8:
vlse32.v v2,(s8),t6
.Lpc_160bc:
vlse32.v v3,(s5),a1
.Lpc_160c0:
vfmul.vv v2,v2,v3
.Lpc_160c4:
vfadd.vv v1,v1,v2
.Lpc_160c8:
blt a0,t4,.Lpc_161f4
.Lpc_160cc:
mulw s11,s6,a6
.Lpc_160d0:
slliw s9,a2,0x1
.Lpc_160d4:
ld s8,16(s0)
.Lpc_160d8:
addw s9,s9,a2
.Lpc_160dc:
slliw s5,s11,0x1
.Lpc_160e0:
addw s5,s5,s11
.Lpc_160e4:
c.addi s5,16
.Lpc_160e6:
c.add s5,t2
.Lpc_160e8:
c.add s5,s9
.Lpc_160ea:
c.slli s5,0x2
.Lpc_160ec:
c.add s8,s5
.Lpc_160ee:
addi s5,a3,4
.Lpc_160f2:
c.add s5,s7
.Lpc_160f4:
vlse32.v v2,(s8),t6
.Lpc_160f8:
vlse32.v v3,(s5),a1
.Lpc_160fc:
vfmul.vv v2,v2,v3
.Lpc_16100:
vfadd.vv v1,v1,v2
.Lpc_16104:
blt a0,t3,.Lpc_1622e
.Lpc_16108:
mulw s11,s6,a6
.Lpc_1610c:
slliw s9,a2,0x1
.Lpc_16110:
ld s8,16(s0)
.Lpc_16114:
addw s9,s9,a2
.Lpc_16118:
slliw s5,s11,0x1
.Lpc_1611c:
addw s5,s5,s11
.Lpc_16120:
c.addi s5,16
.Lpc_16122:
c.add s5,t0
.Lpc_16124:
c.add s5,s9
.Lpc_16126:
c.slli s5,0x2
.Lpc_16128:
c.add s8,s5
.Lpc_1612a:
vlse32.v v2,(s8),t6
.Lpc_1612e:
mulw a5,a5,a6
.Lpc_16132:
c.addi a3,8
.Lpc_16134:
c.add a3,s7
.Lpc_16136:
vlse32.v v3,(a3),a1
.Lpc_1613a:
c.ld a3,112(s0)
.Lpc_1613c:
vfmul.vv v2,v2,v3
.Lpc_16140:
addw a5,a5,t5
.Lpc_16144:
mulw a5,s6,a5
.Lpc_16148:
vfadd.vv v1,v1,v2
.Lpc_1614c:
c.addi a5,16
.Lpc_1614e:
c.add a5,a2
.Lpc_16150:
c.slli a5,0x2
.Lpc_16152:
c.add a5,a3
.Lpc_16154:
vse32.v v1,(a5)
.Lpc_16158:
c.addw a2,a4
.Lpc_1615a:
c.lw a5,4(s0)
.Lpc_1615c:
bge a2,s1,.Lpc_167a6
.Lpc_16160:
subw a4,s1,a2
.Lpc_16164:
vsetvli a4,a4,e32,m1,ta,ma
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_16168:
slliw a3,a2,0x2
.Lpc_1616c:
vmv.v.i v1,0
.Lpc_16170:
addi s5,a3,16
.Lpc_16174:
bgeu a0,a7,.Lpc_1604c
.Lpc_16178:
mulw s11,a5,a6
.Lpc_1617c:
lw s7,12(s0)
.Lpc_16180:
ld s8,40(s0)
.Lpc_16184:
addiw s9,a2,16
.Lpc_16188:
c.slli s5,0x2
.Lpc_1618a:
lw s6,0(s0)
.Lpc_1618e:
addw s11,s11,t5
.Lpc_16192:
c.addiw s11,-3
.Lpc_16194:
mulw s7,s7,s11
.Lpc_16198:
c.add s7,s9
.Lpc_1619a:
c.slli s7,0x2
.Lpc_1619c:
c.add s8,s7
.Lpc_1619e:
ld s7,64(s0)
.Lpc_161a2:
vle32.v v2,(s8)
.Lpc_161a6:
c.add s5,s7
.Lpc_161a8:
vlse32.v v3,(s5),a1
.Lpc_161ac:
vfmul.vv v2,v2,v3
.Lpc_161b0:
vfadd.vv v1,v1,v2
.Lpc_161b4:
bgeu a0,t1,.Lpc_1608e
.Lpc_161b8:
mulw s11,a5,a6
.Lpc_161bc:
lw s5,12(s0)
.Lpc_161c0:
ld s8,40(s0)
.Lpc_161c4:
addiw s9,a2,16
.Lpc_161c8:
c.addi a3,17
.Lpc_161ca:
c.slli a3,0x2
.Lpc_161cc:
addw s11,s11,s4
.Lpc_161d0:
c.addiw s11,-3
.Lpc_161d2:
mulw s5,s5,s11
.Lpc_161d6:
c.add s5,s9
.Lpc_161d8:
c.slli s5,0x2
.Lpc_161da:
c.add s8,s5
.Lpc_161dc:
add s5,s7,a3
.Lpc_161e0:
vle32.v v2,(s8)
.Lpc_161e4:
vlse32.v v3,(s5),a1
.Lpc_161e8:
vfmul.vv v2,v2,v3
.Lpc_161ec:
vfadd.vv v1,v1,v2
.Lpc_161f0:
bge a0,t4,.Lpc_160cc
.Lpc_161f4:
mulw s11,a5,a6
.Lpc_161f8:
lw s5,12(s0)
.Lpc_161fc:
ld s8,40(s0)
.Lpc_16200:
addiw s9,a2,16
.Lpc_16204:
addw s11,s11,t4
.Lpc_16208:
c.addiw s11,-3
.Lpc_1620a:
mulw s5,s5,s11
.Lpc_1620e:
c.add s5,s9
.Lpc_16210:
c.slli s5,0x2
.Lpc_16212:
c.add s8,s5
.Lpc_16214:
addi s5,a3,4
.Lpc_16218:
c.add s5,s7
.Lpc_1621a:
vle32.v v2,(s8)
.Lpc_1621e:
vlse32.v v3,(s5),a1
.Lpc_16222:
vfmul.vv v2,v2,v3
.Lpc_16226:
vfadd.vv v1,v1,v2
.Lpc_1622a:
bge a0,t3,.Lpc_16108
.Lpc_1622e:
mulw s11,a5,a6
.Lpc_16232:
lw s5,12(s0)
.Lpc_16236:
ld s8,40(s0)
.Lpc_1623a:
addiw s9,a2,16
.Lpc_1623e:
addw s11,s11,t3
.Lpc_16242:
c.addiw s11,-3
.Lpc_16244:
mulw s5,s5,s11
.Lpc_16248:
c.add s5,s9
.Lpc_1624a:
c.slli s5,0x2
.Lpc_1624c:
c.add s8,s5
.Lpc_1624e:
vle32.v v2,(s8)
.Lpc_16252:
c.j .Lpc_1612e
.Lpc_16254:
c.lw a3,12(s0)
.Lpc_16256:
addiw t2,a5,-3
.Lpc_1625a:
addiw t0,a5,-2
.Lpc_1625e:
addiw a2,a5,-1
.Lpc_16262:
mulw s7,a5,a3
.Lpc_16266:
subw a7,s1,s2
.Lpc_1626a:
c.slli a7,0x20
.Lpc_1626c:
slliw a1,a4,0x1
.Lpc_16270:
srli a7,a7,0x20
.Lpc_16274:
c.sdsp s11,136(sp)
.Lpc_16276:
addw s11,a1,a4
.Lpc_1627a:
mulw t2,t2,a3
.Lpc_1627e:
add a4,a7,s2
.Lpc_16282:
ld s5,40(s0)
.Lpc_16286:
c.sdsp a4,32(sp)
.Lpc_16288:
addi a4,a5,16
.Lpc_1628c:
c.sdsp a4,8(sp)
.Lpc_1628e:
addi a4,t3,16
.Lpc_16292:
mulw t0,t0,a3
.Lpc_16296:
slli s3,s2,0x1
.Lpc_1629a:
c.sdsp a4,16(sp)
.Lpc_1629c:
addi a4,t1,16
.Lpc_162a0:
c.sdsp s8,160(sp)
.Lpc_162a2:
c.sdsp s9,152(sp)
.Lpc_162a4:
addi s5,s5,64
.Lpc_162a8:
mulw t6,a2,a3
.Lpc_162ac:
ld s9,16(s0)
.Lpc_162b0:
c.add s3,s2
.Lpc_162b2:
c.sdsp a4,24(sp)
.Lpc_162b4:
c.li s4,16
.Lpc_162b6:
c.li s8,0
.Lpc_162b8:
c.li a1,2
.Lpc_162ba:
c.mv s0,s10
.Lpc_162bc:
c.ldsp a4,24(sp)
.Lpc_162be:
addiw t4,s4,-16
.Lpc_162c2:
c.ldsp a0,32(sp)
.Lpc_162c4:
add s1,a4,t4
.Lpc_162c8:
c.ldsp a4,8(sp)
.Lpc_162ca:
add a2,s1,s3
.Lpc_162ce:
sub s1,zero,s1
.Lpc_162d2:
add a7,a4,t4
.Lpc_162d6:
c.ldsp a4,16(sp)
.Lpc_162d8:
c.slli s1,0x2
.Lpc_162da:
add a6,a0,t6
.Lpc_162de:
c.add t4,a4
.Lpc_162e0:
add a3,t6,s2
.Lpc_162e4:
add a4,s4,s3
.Lpc_162e8:
sub a0,zero,t6
.Lpc_162ec:
c.slli a7,0x2
.Lpc_162ee:
c.slli t4,0x2
.Lpc_162f0:
c.slli a0,0x2
.Lpc_162f2:
c.slli a2,0x2
.Lpc_162f4:
c.slli a3,0x2
.Lpc_162f6:
c.slli a4,0x2
.Lpc_162f8:
c.slli a6,0x2
.Lpc_162fa:
slli s10,t2,0x2
.Lpc_162fe:
c.add a7,s1
.Lpc_16300:
c.add t4,s1
.Lpc_16302:
slli s1,t0,0x2
.Lpc_16306:
c.add a2,s9
.Lpc_16308:
c.add a3,s5
.Lpc_1630a:
c.add a4,s6
.Lpc_1630c:
c.add a6,s5
.Lpc_1630e:
c.add s10,a0
.Lpc_16310:
c.add s1,a0
.Lpc_16312:
c.sdsp s6,40(sp)
.Lpc_16314:
add a0,a7,a2
.Lpc_16318:
bge a1,a5,.Lpc_16320
.Lpc_1631c:
add a0,s10,a3
.Lpc_16320:
flw fa5,0(a0)
.Lpc_16324:
add s6,a2,t4
.Lpc_16328:
c.mv a0,a2
.Lpc_1632a:
fsw fa5,0(a4)
.Lpc_1632e:
bge a1,t3,.Lpc_16336
.Lpc_16332:
add s6,a3,s1
.Lpc_16336:
flw fa5,0(s6)
.Lpc_1633a:
c.addi a2,12
.Lpc_1633c:
fsw fa5,4(a4)
.Lpc_16340:
bge a1,t1,.Lpc_16346
.Lpc_16344:
c.mv a0,a3
.Lpc_16346:
flw fa5,0(a0)
.Lpc_1634a:
c.addi a3,4
.Lpc_1634c:
c.addi a4,12
.Lpc_1634e:
fsw fa5,-4(a4)
.Lpc_16352:
bne a6,a3,.Lpc_16314
.Lpc_16356:
c.addiw s8,1
.Lpc_16358:
c.ldsp s6,40(sp)
.Lpc_1635a:
addw t2,s7,t2
.Lpc_1635e:
addw t0,t0,s7
.Lpc_16362:
addw t6,t6,s7
.Lpc_16366:
addw s4,s4,s11
.Lpc_1636a:
bne s8,t5,.Lpc_162bc
.Lpc_1636e:
c.ldsp s8,160(sp)
.Lpc_16370:
c.ldsp s9,152(sp)
.Lpc_16372:
c.ldsp s11,136(sp)
.Lpc_16374:
c.mv s10,s0
.Lpc_16376:
c.ldsp s0,224(sp)
.Lpc_16378:
c.ldsp ra,232(sp)
.Lpc_1637a:
c.ldsp s1,216(sp)
.Lpc_1637c:
c.ldsp s2,208(sp)
.Lpc_1637e:
c.ldsp s3,200(sp)
.Lpc_16380:
c.ldsp s4,192(sp)
.Lpc_16382:
c.ldsp s5,184(sp)
.Lpc_16384:
c.ldsp s6,176(sp)
.Lpc_16386:
c.ldsp s7,168(sp)
.Lpc_16388:
c.mv a0,s10
.Lpc_1638a:
c.ldsp s10,144(sp)
.Lpc_1638c:
c.addi16sp sp,240
.Lpc_1638e:
jal zero,.Lpc_3a460
.Lpc_16392:
c.lw a5,8(a0)
.Lpc_16394:
c.sdsp a5,56(sp)
.Lpc_16396:
bge zero,a5,.Lpc_16562
.Lpc_1639a:
c.lw a2,4(a0)
.Lpc_1639c:
c.li a5,-2
.Lpc_1639e:
blt a2,a5,.Lpc_16562
.Lpc_163a2:
bge s2,s1,.Lpc_16562
.Lpc_163a6:
slliw a4,t5,0x1
.Lpc_163aa:
addiw a1,a2,3
.Lpc_163ae:
addw a4,a4,t5
.Lpc_163b2:
c.sdsp a4,72(sp)
.Lpc_163b4:
mulw a4,t5,a1
.Lpc_163b8:
addiw t4,a2,2
.Lpc_163bc:
c.sdsp s8,160(sp)
.Lpc_163be:
c.sdsp s9,152(sp)
.Lpc_163c0:
c.sdsp s11,136(sp)
.Lpc_163c2:
c.sdsp a1,80(sp)
.Lpc_163c4:
c.li a3,2
.Lpc_163c6:
ld t1,40(a0)
.Lpc_163ca:
lw t0,12(a0)
.Lpc_163ce:
c.mv a5,t4
.Lpc_163d0:
c.sdsp a4,88(sp)
.Lpc_163d2:
c.ld a4,88(s0)
.Lpc_163d4:
c.ld a0,16(a0)
.Lpc_163d6:
c.sdsp a4,24(sp)
.Lpc_163d8:
blt a3,t4,.Lpc_16840
.Lpc_163dc:
subw a7,s1,s2
.Lpc_163e0:
c.slli a7,0x20
.Lpc_163e2:
srli a7,a7,0x20
.Lpc_163e6:
add s7,s2,a7
.Lpc_163ea:
slli a1,s7,0x1
.Lpc_163ee:
c.add a1,s7
.Lpc_163f0:
c.sdsp a1,64(sp)
.Lpc_163f2:
addiw s6,a5,1
.Lpc_163f6:
addiw a1,a5,0
.Lpc_163fa:
c.addiw a5,-2
.Lpc_163fc:
c.sdsp a5,104(sp)
.Lpc_163fe:
c.ldsp a5,24(sp)
.Lpc_16400:
addiw a4,s1,-1
.Lpc_16404:
slli a3,a7,0x2
.Lpc_16408:
addi a0,a0,64
.Lpc_1640c:
subw a4,a4,s2
.Lpc_16410:
csrrs t6,vlenb,zero
.Lpc_16414:
sub a3,a7,a3
.Lpc_16418:
addi a5,a5,64
.Lpc_1641c:
c.sdsp a0,96(sp)
.Lpc_1641e:
c.sdsp a4,32(sp)
.Lpc_16420:
c.slli a3,0x2
.Lpc_16422:
c.addi t6,-8
.Lpc_16424:
slli t3,t5,0x2
.Lpc_16428:
c.li s5,0
.Lpc_1642a:
c.li s8,0
.Lpc_1642c:
c.li s9,0
.Lpc_1642e:
c.li a4,0
.Lpc_16430:
c.sdsp zero,16(sp)
.Lpc_16432:
c.sdsp a5,112(sp)
.Lpc_16434:
addi s4,s2,17
.Lpc_16438:
addi t2,s2,16
.Lpc_1643c:
c.sdsp s10,120(sp)
.Lpc_1643e:
c.mv a0,s3
.Lpc_16440:
c.ldsp a5,16(sp)
.Lpc_16442:
c.ldsp a6,64(sp)
.Lpc_16444:
add s10,a4,s2
.Lpc_16448:
c.slli s10,0x2
.Lpc_1644a:
add s3,a5,a6
.Lpc_1644e:
c.ldsp a5,24(sp)
.Lpc_16450:
c.slli s3,0x2
.Lpc_16452:
c.li s11,0
.Lpc_16454:
c.add s10,a5
.Lpc_16456:
c.ldsp a5,96(sp)
.Lpc_16458:
c.add s3,a5
.Lpc_1645a:
add a5,s3,a3
.Lpc_1645e:
c.mv a6,s10
.Lpc_16460:
flw fa5,0(a5)
.Lpc_16464:
c.addi a5,12
.Lpc_16466:
c.addi a6,4
.Lpc_16468:
fsw fa5,60(a6)
.Lpc_1646c:
bne a5,s3,.Lpc_16460
.Lpc_16470:
c.addi s11,1
.Lpc_16472:
addiw a6,s11,0
.Lpc_16476:
c.add s10,t3
.Lpc_16478:
addi s3,a5,4
.Lpc_1647c:
bge a1,a6,.Lpc_1645a
.Lpc_16480:
blt t4,s6,.Lpc_16538
.Lpc_16484:
c.ldsp a6,104(sp)
.Lpc_16486:
addw a5,s6,s8
.Lpc_1648a:
mulw a5,a5,t5
.Lpc_1648e:
addw s3,a6,s9
.Lpc_16492:
c.ldsp a6,112(sp)
.Lpc_16494:
c.sdsp a2,40(sp)
.Lpc_16496:
c.mv s10,s6
.Lpc_16498:
c.mv a2,a1
.Lpc_1649a:
mulw s3,s3,t0
.Lpc_1649e:
c.add a5,s2
.Lpc_164a0:
c.slli a5,0x2
.Lpc_164a2:
c.add a5,a6
.Lpc_164a4:
c.ldsp a1,32(sp)
.Lpc_164a6:
c.li a6,2
.Lpc_164a8:
bgeu a6,a1,.Lpc_16506
.Lpc_164ac:
add a1,s4,s3
.Lpc_164b0:
c.slli a1,0x2
.Lpc_164b2:
c.add a1,t1
.Lpc_164b4:
c.sdsp s5,48(sp)
.Lpc_164b6:
sub a1,a5,a1
.Lpc_164ba:
bgeu t6,a1,.Lpc_16504
.Lpc_164be:
add s5,t2,s3
.Lpc_164c2:
c.slli s5,0x2
.Lpc_164c4:
c.add s5,t1
.Lpc_164c6:
c.mv a6,a5
.Lpc_164c8:
c.mv a1,a7
.Lpc_164ca:
c.sdsp t1,8(sp)
.Lpc_164cc:
vsetvli t1,a1,e8,mf4,ta,ma
# LLVM-MCA-RISCV-LMUL MF4
# LLVM-MCA-RISCV-SEW E8
.Lpc_164d0:
vle32.v v1,(s5)
.Lpc_164d4:
slli s11,t1,0x2
.Lpc_164d8:
sub a1,a1,t1
.Lpc_164dc:
c.add s5,s11
.Lpc_164de:
vse32.v v1,(a6)
.Lpc_164e2:
c.add a6,s11
.Lpc_164e4:
c.bnez a1,.Lpc_164cc
.Lpc_164e6:
c.addiw s10,1
.Lpc_164e8:
c.ldsp t1,8(sp)
.Lpc_164ea:
blt t4,s10,.Lpc_167cc
.Lpc_164ee:
addw s3,t0,s3
.Lpc_164f2:
add a1,s4,s3
.Lpc_164f6:
c.slli a1,0x2
.Lpc_164f8:
c.add a5,t3
.Lpc_164fa:
c.add a1,t1
.Lpc_164fc:
sub a1,a5,a1
.Lpc_16500:
bltu t6,a1,.Lpc_164be
.Lpc_16504:
c.ldsp s5,48(sp)
.Lpc_16506:
add a1,s2,s3
.Lpc_1650a:
add s11,s7,s3
.Lpc_1650e:
c.slli a1,0x2
.Lpc_16510:
c.slli s11,0x2
.Lpc_16512:
c.add a1,t1
.Lpc_16514:
c.add s11,t1
.Lpc_16516:
c.mv a6,a5
.Lpc_16518:
flw fa5,64(a1)
.Lpc_1651c:
c.addi a1,4
.Lpc_1651e:
c.addi a6,4
.Lpc_16520:
fsw fa5,-4(a6)
.Lpc_16524:
bne a1,s11,.Lpc_16518
.Lpc_16528:
c.addiw s10,1
.Lpc_1652a:
addw s3,t0,s3
.Lpc_1652e:
c.add a5,t3
.Lpc_16530:
bge t4,s10,.Lpc_164a4
.Lpc_16534:
c.mv a1,a2
.Lpc_16536:
c.ldsp a2,40(sp)
.Lpc_16538:
c.ldsp a6,16(sp)
.Lpc_1653a:
c.ldsp a5,72(sp)
.Lpc_1653c:
c.addiw s5,1
.Lpc_1653e:
addw s9,a2,s9
.Lpc_16542:
addw a5,a5,a6
.Lpc_16546:
c.sdsp a5,16(sp)
.Lpc_16548:
c.ldsp a5,88(sp)
.Lpc_1654a:
c.addw a4,a5
.Lpc_1654c:
c.ldsp a5,80(sp)
.Lpc_1654e:
addw s8,a5,s8
.Lpc_16552:
c.ldsp a5,56(sp)
.Lpc_16554:
bne s5,a5,.Lpc_16440
.Lpc_16558:
c.ldsp s10,120(sp)
.Lpc_1655a:
c.ldsp s8,160(sp)
.Lpc_1655c:
c.ldsp s9,152(sp)
.Lpc_1655e:
c.ldsp s11,136(sp)
.Lpc_16560:
c.mv s3,a0
.Lpc_16562:
c.mv a0,s10
.Lpc_16564:
jal ra,.Lpc_3a460
.Lpc_16568:
lw t5,8(s0)
.Lpc_1656c:
bge zero,t5,.Lpc_16376
.Lpc_16570:
c.lw a5,4(s0)
.Lpc_16572:
c.li t1,0
.Lpc_16574:
c.li a6,16
.Lpc_16576:
bge zero,a5,.Lpc_16834
.Lpc_1657a:
c.li a7,0
.Lpc_1657c:
c.li t5,3
.Lpc_1657e:
c.li t4,2
.Lpc_16580:
c.li t3,1
.Lpc_16582:
c.mv a0,s2
.Lpc_16584:
bge s2,s1,.Lpc_16666
.Lpc_16588:
addiw a3,a5,3
.Lpc_1658c:
mulw a3,a3,t1
.Lpc_16590:
lw t0,0(s0)
.Lpc_16594:
ld t2,88(s0)
.Lpc_16598:
ld t6,64(s0)
.Lpc_1659c:
addiw s4,a0,16
.Lpc_165a0:
slliw a2,a0,0x2
.Lpc_165a4:
addi s7,a2,16
.Lpc_165a8:
subw a4,s1,a0
.Lpc_165ac:
c.slli s7,0x2
.Lpc_165ae:
vsetvli a4,a4,e32,m1,ta,ma
# LLVM-MCA-RISCV-LMUL M1
# LLVM-MCA-RISCV-SEW E32
.Lpc_165b2:
addw s6,a3,a7
.Lpc_165b6:
mulw s6,t0,s6
.Lpc_165ba:
addw s5,a3,t3
.Lpc_165be:
addw a1,a3,t4
.Lpc_165c2:
addw a3,a3,t5
.Lpc_165c6:
c.add s7,t6
.Lpc_165c8:
vlse32.v v1,(s7),a6
.Lpc_165cc:
c.addi a2,17
.Lpc_165ce:
mulw s5,s5,t0
.Lpc_165d2:
c.slli a2,0x2
.Lpc_165d4:
add s7,t6,a2
.Lpc_165d8:
c.add s6,s4
.Lpc_165da:
c.slli s6,0x2
.Lpc_165dc:
c.add s6,t2
.Lpc_165de:
vle32.v v2,(s6)
.Lpc_165e2:
mulw a1,a1,t0
.Lpc_165e6:
vlse32.v v5,(s7),a6
.Lpc_165ea:
addi s6,a2,4
.Lpc_165ee:
c.add s5,s4
.Lpc_165f0:
c.slli s5,0x2
.Lpc_165f2:
c.add s5,t2
.Lpc_165f4:
vle32.v v4,(s5)
.Lpc_165f8:
mulw a3,a3,t0
.Lpc_165fc:
vfmul.vv v2,v2,v1
.Lpc_16600:
add s5,t6,s6
.Lpc_16604:
c.add a1,s4
.Lpc_16606:
c.slli a1,0x2
.Lpc_16608:
c.add a1,t2
.Lpc_1660a:
vle32.v v3,(a1)
.Lpc_1660e:
mulw a5,a5,t1
.Lpc_16612:
vlse32.v v6,(s5),a6
.Lpc_16616:
vmv.v.i v1,0
.Lpc_1661a:
c.add a3,s4
.Lpc_1661c:
vfmul.vv v4,v4,v5
.Lpc_16620:
c.slli a3,0x2
.Lpc_16622:
c.addi a2,8
.Lpc_16624:
c.add t2,a3
.Lpc_16626:
c.add t6,a2
.Lpc_16628:
vlse32.v v5,(t6),a6
.Lpc_1662c:
vfadd.vv v1,v1,v2
.Lpc_16630:
vle32.v v2,(t2)
.Lpc_16634:
addw a5,a5,a7
.Lpc_16638:
mulw a5,a5,t0
.Lpc_1663c:
vfmul.vv v3,v3,v6
.Lpc_16640:
vfadd.vv v1,v1,v4
.Lpc_16644:
c.ld a3,112(s0)
.Lpc_16646:
vfmul.vv v2,v2,v5
.Lpc_1664a:
vfadd.vv v1,v1,v3
.Lpc_1664e:
c.addi a5,16
.Lpc_16650:
vfadd.vv v1,v1,v2
.Lpc_16654:
c.add a5,a0
.Lpc_16656:
c.slli a5,0x2
.Lpc_16658:
c.add a5,a3
.Lpc_1665a:
vse32.v v1,(a5)
.Lpc_1665e:
c.addw a0,a4
.Lpc_16660:
c.lw a5,4(s0)
.Lpc_16662:
blt a0,s1,.Lpc_16588
.Lpc_16666:
c.addiw a7,1
.Lpc_16668:
c.addiw t3,1
.Lpc_1666a:
c.addiw t4,1
.Lpc_1666c:
c.addiw t5,1
.Lpc_1666e:
blt a7,a5,.Lpc_16582
.Lpc_16672:
lw t5,8(s0)
.Lpc_16676:
c.addiw t1,1
.Lpc_16678:
blt t1,t5,.Lpc_16576
.Lpc_1667c:
bge zero,t5,.Lpc_16376
.Lpc_16680:
bge s2,s1,.Lpc_16376
.Lpc_16684:
c.lw a4,0(s0)
.Lpc_16686:
ld s6,136(s0)
.Lpc_1668a:
addiw t3,a5,1
.Lpc_1668e:
addiw t1,a5,2
.Lpc_16692:
bne s3,zero,.Lpc_16254
.Lpc_16696:
mulw t3,t3,a4
.Lpc_1669a:
addiw t0,a5,3
.Lpc_1669e:
subw s1,s1,s2
.Lpc_166a2:
slli s4,s1,0x20
.Lpc_166a6:
srli s4,s4,0x20
.Lpc_166aa:
add s1,s2,s4
.Lpc_166ae:
slliw a3,a4,0x1
.Lpc_166b2:
mulw t1,t1,a4
.Lpc_166b6:
slli s5,s1,0x1
.Lpc_166ba:
slli t2,s2,0x1
.Lpc_166be:
ld t6,88(s0)
.Lpc_166c2:
addiw t4,t3,16
.Lpc_166c6:
c.add s5,s1
.Lpc_166c8:
addw s0,a3,a4
.Lpc_166cc:
mulw a5,a5,a4
.Lpc_166d0:
c.add t2,s2
.Lpc_166d2:
c.li s7,16
.Lpc_166d4:
addiw t3,t1,16
.Lpc_166d8:
mulw t0,t0,a4
.Lpc_166dc:
addiw t1,a5,16
.Lpc_166e0:
add a2,t2,s7
.Lpc_166e4:
add a5,t1,s1
.Lpc_166e8:
add a1,s7,s5
.Lpc_166ec:
add a7,t1,s2
.Lpc_166f0:
c.slli a2,0x2
.Lpc_166f2:
c.slli a5,0x2
.Lpc_166f4:
c.slli a1,0x2
.Lpc_166f6:
c.slli a7,0x2
.Lpc_166f8:
c.add a2,s6
.Lpc_166fa:
c.add a1,s6
.Lpc_166fc:
add a0,s1,t4
.Lpc_16700:
add a3,s2,t4
.Lpc_16704:
c.add a5,t6
.Lpc_16706:
c.add a7,t6
.Lpc_16708:
sltu a6,a7,a1
.Lpc_1670c:
c.slli a0,0x2
.Lpc_1670e:
c.slli a3,0x2
.Lpc_16710:
sltu a5,a2,a5
.Lpc_16714:
sltiu a6,a6,1
.Lpc_16718:
c.add a0,t6
.Lpc_1671a:
c.add a3,t6
.Lpc_1671c:
sltiu a5,a5,1
.Lpc_16720:
or a5,a5,a6
.Lpc_16724:
sltu a4,a2,a0
.Lpc_16728:
sltu a6,a3,a1
.Lpc_1672c:
sltiu a6,a6,1
.Lpc_16730:
sltiu a4,a4,1
.Lpc_16734:
or a4,a4,a6
.Lpc_16738:
c.and a5,a4
.Lpc_1673a:
add a6,s2,t3
.Lpc_1673e:
add a4,s1,t3
.Lpc_16742:
c.slli a4,0x2
.Lpc_16744:
c.slli a6,0x2
.Lpc_16746:
c.add a4,t6
.Lpc_16748:
c.add a6,t6
.Lpc_1674a:
sltu a4,a2,a4
.Lpc_1674e:
sltu a1,a6,a1
.Lpc_16752:
sltiu a1,a1,1
.Lpc_16756:
sltiu a4,a4,1
.Lpc_1675a:
c.or a4,a1
.Lpc_1675c:
c.and a5,a4
.Lpc_1675e:
c.mv a1,s4
.Lpc_16760:
c.beqz a5,.Lpc_167d0
.Lpc_16762:
vsetvli a5,a1,e8,mf4,ta,ma
# LLVM-MCA-RISCV-LMUL MF4
# LLVM-MCA-RISCV-SEW E8
.Lpc_16766:
vle32.v v3,(a7)
.Lpc_1676a:
vle32.v v4,(a3)
.Lpc_1676e:
vle32.v v5,(a6)
.Lpc_16772:
slli a4,a5,0x1
.Lpc_16776:
c.add a4,a5
.Lpc_16778:
slli a0,a5,0x2
.Lpc_1677c:
c.slli a4,0x2
.Lpc_1677e:
c.sub a1,a5
.Lpc_16780:
vsseg3e32.v v3,(a2)
.Lpc_16784:
c.add a7,a0
.Lpc_16786:
c.add a3,a0
.Lpc_16788:
c.add a6,a0
.Lpc_1678a:
c.add a2,a4
.Lpc_1678c:
c.bnez a1,.Lpc_16762
.Lpc_1678e:
c.addiw s3,1
.Lpc_16790:
addw t1,t0,t1
.Lpc_16794:
addw s7,s0,s7
.Lpc_16798:
addw t4,t0,t4
.Lpc_1679c:
addw t3,t0,t3
.Lpc_167a0:
bne s3,t5,.Lpc_166e0
.Lpc_167a4:
c.j .Lpc_16376
.Lpc_167a6:
c.addi a7,1
.Lpc_167a8:
addiw a4,a7,0
.Lpc_167ac:
c.addi t0,1
.Lpc_167ae:
c.addi t2,1
.Lpc_167b0:
c.addi t1,1
.Lpc_167b2:
blt a4,a5,.Lpc_16038
.Lpc_167b6:
lw t5,8(s0)
.Lpc_167ba:
c.addiw a6,1
.Lpc_167bc:
blt a6,t5,.Lpc_1602c
.Lpc_167c0:
c.ldsp s8,160(sp)
.Lpc_167c2:
c.ldsp s9,152(sp)
.Lpc_167c4:
c.ldsp s11,136(sp)
.Lpc_167c6:
blt zero,t5,.Lpc_16680
.Lpc_167ca:
c.j .Lpc_16376
.Lpc_167cc:
c.ldsp s5,48(sp)
.Lpc_167ce:
c.j .Lpc_16534
.Lpc_167d0:
sub a5,zero,t4
.Lpc_167d4:
c.slli a5,0x2
.Lpc_167d6:
slli a6,t1,0x2
.Lpc_167da:
slli a1,t3,0x2
.Lpc_167de:
add a4,a3,a6
.Lpc_167e2:
c.add a4,a5
.Lpc_167e4:
flw fa5,0(a4)
.Lpc_167e8:
add a4,a3,a1
.Lpc_167ec:
c.add a4,a5
.Lpc_167ee:
fsw fa5,0(a2)
.Lpc_167f2:
flw fa5,0(a3)
.Lpc_167f6:
c.addi a3,4
.Lpc_167f8:
c.addi a2,12
.Lpc_167fa:
fsw fa5,-8(a2)
.Lpc_167fe:
flw fa5,0(a4)
.Lpc_16802:
fsw fa5,-4(a2)
.Lpc_16806:
bne a3,a0,.Lpc_167de
.Lpc_1680a:
c.addiw s3,1
.Lpc_1680c:
addw t1,t0,t1
.Lpc_16810:
addw s7,s0,s7
.Lpc_16814:
addw t4,t0,t4
.Lpc_16818:
addw t3,t0,t3
.Lpc_1681c:
bne s3,t5,.Lpc_166e0
.Lpc_16820:
c.j .Lpc_16376
.Lpc_16822:
c.addiw a6,1
.Lpc_16824:
c.ldsp s8,160(sp)
.Lpc_16826:
c.ldsp s9,152(sp)
.Lpc_16828:
c.ldsp s11,136(sp)
.Lpc_1682a:
bge a6,t5,.Lpc_16680
.Lpc_1682e:
blt zero,t5,.Lpc_16680
.Lpc_16832:
c.j .Lpc_16376
.Lpc_16834:
c.addiw t1,1
.Lpc_16836:
bge t1,t5,.Lpc_16680
.Lpc_1683a:
blt zero,t5,.Lpc_16680
.Lpc_1683e:
c.j .Lpc_16376
.Lpc_16840:
c.mv a5,a3
.Lpc_16842:
c.j .Lpc_163dc
