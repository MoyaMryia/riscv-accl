.text
.global load_control
load_control:
addi sp,sp,-64
sd s1,0(sp)
sd s2,8(sp)
sd s3,16(sp)
sd s4,24(sp)
sd s5,32(sp)
sd s6,40(sp)
vsetvli t0,zero,e8,m1,ta,ma
vmv.v.i v0,0
vmv.v.i v1,0
vmv.v.i v2,0
vmv.v.i v3,0
vmv.v.i v4,0
vmv.v.i v5,0
vmv.v.i v6,0
vmv.v.i v7,0
vmv.v.i v8,0
vmv.v.i v9,0
vmv.v.i v10,0
vmv.v.i v11,0
vmv.v.i v12,0
vmv.v.i v13,0
vmv.v.i v14,0
vmv.v.i v15,0
addi s1,a0,128
addi s2,a0,256
addi s3,a0,384
addi s4,a0,512
addi s5,a0,640
addi s6,a0,768
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
vs1r.v v0,(a1)
addi a1,a1,32
vs1r.v v1,(a1)
addi a1,a1,32
vs1r.v v2,(a1)
addi a1,a1,32
vs1r.v v3,(a1)
addi a1,a1,32
vs1r.v v4,(a1)
addi a1,a1,32
vs1r.v v5,(a1)
addi a1,a1,32
vs1r.v v6,(a1)
addi a1,a1,32
vs1r.v v7,(a1)
addi a1,a1,32
vs1r.v v14,(a1)
addi a1,a1,32
vs1r.v v15,(a1)
addi a1,a1,32
sd s1,0(a1)
sd s2,8(a1)
sd s3,16(a1)
sd s4,24(a1)
sd s5,32(a1)
sd s6,40(a1)
ld s1,0(sp)
ld s2,8(sp)
ld s3,16(sp)
ld s4,24(sp)
ld s5,32(sp)
ld s6,40(sp)
addi sp,sp,64
ret
.text
.global load_candidate
load_candidate:
addi sp,sp,-64
sd s1,0(sp)
sd s2,8(sp)
sd s3,16(sp)
sd s4,24(sp)
sd s5,32(sp)
sd s6,40(sp)
vsetvli t0,zero,e8,m1,ta,ma
vmv.v.i v0,0
vmv.v.i v1,0
vmv.v.i v2,0
vmv.v.i v3,0
vmv.v.i v4,0
vmv.v.i v5,0
vmv.v.i v6,0
vmv.v.i v7,0
vmv.v.i v8,0
vmv.v.i v9,0
vmv.v.i v10,0
vmv.v.i v11,0
vmv.v.i v12,0
vmv.v.i v13,0
vmv.v.i v14,0
vmv.v.i v15,0
addi s1,a0,128
addi s2,a0,256
addi s3,a0,384
addi s4,a0,512
addi s5,a0,640
addi s6,a0,768
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
vs1r.v v0,(a1)
addi a1,a1,32
vs1r.v v1,(a1)
addi a1,a1,32
vs1r.v v2,(a1)
addi a1,a1,32
vs1r.v v3,(a1)
addi a1,a1,32
vs1r.v v4,(a1)
addi a1,a1,32
vs1r.v v5,(a1)
addi a1,a1,32
vs1r.v v6,(a1)
addi a1,a1,32
vs1r.v v7,(a1)
addi a1,a1,32
vs1r.v v14,(a1)
addi a1,a1,32
vs1r.v v15,(a1)
addi a1,a1,32
sd s1,0(a1)
sd s2,8(a1)
sd s3,16(a1)
sd s4,24(a1)
sd s5,32(a1)
sd s6,40(a1)
ld s1,0(sp)
ld s2,8(sp)
ld s3,16(sp)
ld s4,24(sp)
ld s5,32(sp)
ld s6,40(sp)
addi sp,sp,64
ret
