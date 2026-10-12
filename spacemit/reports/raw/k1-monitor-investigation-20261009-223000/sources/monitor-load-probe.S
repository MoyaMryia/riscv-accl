.text
.option rvc
.global probe_load
.type probe_load, @function
probe_load:
    addi sp, sp, -16
    sd s1, 8(sp)
    mv s1, a0
    c.ld a0, 104(s1)
    ld s1, 8(sp)
    addi sp, sp, 16
    ret
.size probe_load, .-probe_load
.section .note.GNU-stack,"",@progbits
