#include <qemu-plugin.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

QEMU_PLUGIN_EXPORT int qemu_plugin_version = QEMU_PLUGIN_VERSION;
enum { MAX_CPUS = 256 };
typedef struct {
    _Atomic uint64_t instructions, vector, ime, loads, stores, load_bytes, store_bytes;
    _Atomic uint64_t vector_load_bytes, vector_store_bytes;
} Counts;
static Counts counts[MAX_CPUS];
static uint64_t first, limit;
static const char *output;
static _Atomic bool overflow;

static void execute(unsigned cpu, void *data) {
    if (cpu >= MAX_CPUS) { atomic_store(&overflow, true); return; }
    uintptr_t kind = (uintptr_t)data;
    atomic_fetch_add(&counts[cpu].instructions, 1);
    if (kind & 1) atomic_fetch_add(&counts[cpu].vector, 1);
    if (kind & 2) atomic_fetch_add(&counts[cpu].ime, 1);
}

static void memory(unsigned cpu, qemu_plugin_meminfo_t info, uint64_t address, void *data) {
    (void)address;
    if (cpu >= MAX_CPUS) { atomic_store(&overflow, true); return; }
    unsigned shift = qemu_plugin_mem_size_shift(info);
    if (shift >= 63) { atomic_store(&overflow, true); return; }
    uint64_t bytes = UINT64_C(1) << shift;
    if (qemu_plugin_mem_is_store(info)) {
        atomic_fetch_add(&counts[cpu].stores, 1);
        atomic_fetch_add(&counts[cpu].store_bytes, bytes);
        if ((uintptr_t)data & 1) atomic_fetch_add(&counts[cpu].vector_store_bytes, bytes);
    } else {
        atomic_fetch_add(&counts[cpu].loads, 1);
        atomic_fetch_add(&counts[cpu].load_bytes, bytes);
        if ((uintptr_t)data & 1) atomic_fetch_add(&counts[cpu].vector_load_bytes, bytes);
    }
}

#if QEMU_PLUGIN_VERSION >= 7
static void translate(struct qemu_plugin_tb *tb, void *data) {
    (void)data;
#else
static void translate(qemu_plugin_id_t id, struct qemu_plugin_tb *tb) {
    (void)id;
#endif
    size_t length = qemu_plugin_tb_n_insns(tb);
    for (size_t i = 0; i < length; ++i) {
        struct qemu_plugin_insn *insn = qemu_plugin_tb_get_insn(tb, i);
        uint64_t pc = qemu_plugin_insn_vaddr(insn);
        if (pc < first || pc >= limit) continue;
        uint8_t bytes[4] = {0};
        size_t size = qemu_plugin_insn_data(insn, bytes, sizeof bytes);
        uint32_t word = bytes[0] | (uint32_t)bytes[1]<<8 |
            (uint32_t)bytes[2]<<16 | (uint32_t)bytes[3]<<24;
        unsigned opcode = word & 0x7f;
        uintptr_t kind = 0;
        if (size == 4 && (opcode == 0x57 ||
            ((opcode == 0x07 || opcode == 0x27) && ((word>>12)&7) != 2 && ((word>>12)&7) != 3))) kind |= 1;
        if (size == 4 && (word & 0xfe00707f) == 0xe200302b) kind |= 2;
        qemu_plugin_register_vcpu_insn_exec_cb(insn, execute, QEMU_PLUGIN_CB_NO_REGS, (void *)kind);
        qemu_plugin_register_vcpu_mem_cb(insn, memory, QEMU_PLUGIN_CB_NO_REGS, QEMU_PLUGIN_MEM_RW, (void *)kind);
    }
}

#if QEMU_PLUGIN_VERSION >= 7
static void finish(void *data) {
#else
static void finish(qemu_plugin_id_t id, void *data) {
    (void)id;
#endif
    (void)data;
    FILE *stream = fopen(output, "wx");
    if (!stream) { qemu_plugin_outs("metrics output failed\n"); return; }
    fprintf(stream, "{\"schema\":1,\"kind\":\"instruction-metrics-not-K1-time\",\"overflow\":%s,\"cpus\":[", atomic_load(&overflow)?"true":"false");
    bool comma = false;
    for (unsigned i = 0; i < MAX_CPUS; ++i) {
        Counts *c = &counts[i];
        if (!atomic_load(&c->instructions)) continue;
        fprintf(stream, "%s{\"cpu\":%u,\"instructions\":%"PRIu64",\"vector\":%"PRIu64",\"ime\":%"PRIu64",\"loads\":%"PRIu64",\"stores\":%"PRIu64",\"load_bytes\":%"PRIu64",\"store_bytes\":%"PRIu64",\"vector_load_bytes\":%"PRIu64",\"vector_store_bytes\":%"PRIu64"}",
            comma?",":"", i, atomic_load(&c->instructions), atomic_load(&c->vector), atomic_load(&c->ime),
            atomic_load(&c->loads), atomic_load(&c->stores), atomic_load(&c->load_bytes), atomic_load(&c->store_bytes),
            atomic_load(&c->vector_load_bytes), atomic_load(&c->vector_store_bytes));
        comma = true;
    }
    fputs("]}\n", stream); fclose(stream);
}

QEMU_PLUGIN_EXPORT int qemu_plugin_install(qemu_plugin_id_t id, const qemu_info_t *info, int argc, char **argv) {
    if (strcmp(info->target_name, "riscv64") != 0) return -1;
    for (int i = 0; i < argc; ++i) {
        if (strncmp(argv[i], "start=", 6) == 0) first = strtoull(argv[i]+6, NULL, 0);
        else if (strncmp(argv[i], "end=", 4) == 0) limit = strtoull(argv[i]+4, NULL, 0);
        else if (strncmp(argv[i], "out=", 4) == 0) output = argv[i]+4;
        else return -1;
    }
    if (!output || first >= limit) return -1;
#if QEMU_PLUGIN_VERSION >= 7
    qemu_plugin_register_vcpu_tb_trans_cb(id, translate, NULL);
#else
    qemu_plugin_register_vcpu_tb_trans_cb(id, translate);
#endif
    qemu_plugin_register_atexit_cb(id, finish, NULL);
    return 0;
}
