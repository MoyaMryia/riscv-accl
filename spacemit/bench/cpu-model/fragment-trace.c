#include <qemu-plugin.h>
#include <glib.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* 采集第一次目标调用，包含全部被调用函数。 */
QEMU_PLUGIN_EXPORT int qemu_plugin_version = QEMU_PLUGIN_VERSION;
enum { CPUS = 4096, REGS = 5 };
static const char *names[REGS] = {"vl", "vtype", "vlenb", "vstart", "v0"};
typedef struct {
    FILE *file;
    struct qemu_plugin_register *ra;
    struct qemu_plugin_register *regs[REGS];
    GByteArray *buffer;
    uint64_t count, recorded, memory, return_pc;
    bool entered, active, closed, record;
} State;
typedef struct { uint64_t pc; uint32_t word; size_t size; bool vector; } Insn;
static State states[CPUS];
static uint64_t entry, maximum = 200000;
static const char *prefix;
static _Atomic bool failure;
static GPtrArray *allocations;

#if QEMU_PLUGIN_VERSION >= 7
static void init(unsigned cpu, void *data) {
    (void)data;
#else
static void init(qemu_plugin_id_t id, unsigned cpu) {
    (void)id;
#endif
    if (cpu >= CPUS) { atomic_store(&failure, true); return; }
    State *s = &states[cpu];
    s->buffer = g_byte_array_new();
    GArray *regs = qemu_plugin_get_registers();
    for (guint i = 0; regs && i < regs->len; ++i) {
        qemu_plugin_reg_descriptor *r = &g_array_index(regs, qemu_plugin_reg_descriptor, i);
        if (!strcmp(r->name, "ra") || !strcmp(r->name, "x1")) s->ra = r->handle;
        for (int j = 0; j < REGS; ++j)
            if (!strcmp(r->name, names[j])) s->regs[j] = r->handle;
    }
    if (regs) g_array_free(regs, true);
}

static void execute(unsigned cpu, void *data) {
    if (cpu >= CPUS) { atomic_store(&failure, true); return; }
    State *s = &states[cpu];
    Insn *insn = data;
    s->record = false;
    if (s->closed) return;
    if (!s->entered && insn->pc == entry) {
        s->entered = true;
        g_byte_array_set_size(s->buffer, 0);
        if (!s->ra || qemu_plugin_read_register(s->ra, s->buffer) != 8 || s->buffer->len != 8) {
            atomic_store(&failure, true); return;
        }
        for (int i = 0; i < 8; ++i) s->return_pc |= (uint64_t)s->buffer->data[i] << (8*i);
        if (!s->return_pc || s->return_pc == entry) { atomic_store(&failure, true); return; }
        char *path = g_strdup_printf("%s-cpu%u.jsonl", prefix, cpu);
        s->file = fopen(path, "wx");
        g_free(path);
        if (!s->file) { atomic_store(&failure, true); return; }
        setvbuf(s->file, NULL, _IOFBF, 1024*1024);
        fprintf(s->file, "{\"kind\":\"begin\",\"cpu\":%u,\"entry\":%"PRIu64",\"return_pc\":%"PRIu64"}\n", cpu, entry, s->return_pc);
        s->active = true;
    }
    if (!s->active) return;
    if (insn->pc == s->return_pc) {
        s->closed = true;
        s->active = false;
        return;
    }
    ++s->count;
    if (s->count > maximum) return;
    s->record = true;
    fprintf(s->file, "{\"kind\":\"instruction\",\"cpu\":%u,\"seq\":%"PRIu64",\"pc\":%"PRIu64",\"size\":%zu,\"encoding\":\"%0*x\"",
            cpu, s->count, insn->pc, insn->size, (int)insn->size*2, insn->word);
    if (insn->vector) for (int i = 0; i < REGS; ++i) {
        g_byte_array_set_size(s->buffer, 0);
        bool ok = s->regs[i] && qemu_plugin_read_register(s->regs[i], s->buffer) > 0;
        fprintf(s->file, ",\"%s\":", names[i]);
        if (!ok || (i < 4 && s->buffer->len != 8)) fputs("null", s->file);
        else if (i == 4) {
            fputc('"', s->file);
            for (guint j = 0; j < s->buffer->len; ++j) fprintf(s->file, "%02x", s->buffer->data[j]);
            fputc('"', s->file);
        } else {
            uint64_t value = 0;
            for (int j = 0; j < 8; ++j) value |= (uint64_t)s->buffer->data[j] << (8*j);
            fprintf(s->file, "%"PRIu64, value);
        }
    }
    fputs("}\n", s->file);
    ++s->recorded;
}

static void memory(unsigned cpu, qemu_plugin_meminfo_t info, uint64_t addr, void *data) {
    (void)data;
    if (cpu >= CPUS) { atomic_store(&failure, true); return; }
    State *s = &states[cpu];
    if (!s->active) return;
    ++s->memory;
    if (!s->record || !s->file) return;
    unsigned shift = qemu_plugin_mem_size_shift(info);
    if (shift >= 63) { atomic_store(&failure, true); return; }
    fprintf(s->file, "{\"kind\":\"memory\",\"seq\":%"PRIu64",\"address\":%"PRIu64",\"bytes\":%"PRIu64",\"store\":%s}\n",
            s->count, addr, UINT64_C(1)<<shift, qemu_plugin_mem_is_store(info) ? "true" : "false");
}

#if QEMU_PLUGIN_VERSION >= 7
static void translate(struct qemu_plugin_tb *tb, void *data) {
    (void)data;
#else
static void translate(qemu_plugin_id_t id, struct qemu_plugin_tb *tb) {
    (void)id;
#endif
    for (size_t i = 0; i < qemu_plugin_tb_n_insns(tb); ++i) {
        struct qemu_plugin_insn *item = qemu_plugin_tb_get_insn(tb, i);
        Insn *insn = g_new0(Insn, 1);
        uint8_t bytes[4] = {0};
        insn->pc = qemu_plugin_insn_vaddr(item);
        insn->size = qemu_plugin_insn_data(item, bytes, sizeof bytes);
        for (size_t j = 0; j < 4; ++j) insn->word |= (uint32_t)bytes[j] << (8*j);
        unsigned opcode = insn->word & 127;
        insn->vector = insn->size == 4 && (opcode == 0x57 || opcode == 0x07 || opcode == 0x27);
        g_ptr_array_add(allocations, insn);
        qemu_plugin_register_vcpu_insn_exec_cb(item, execute,
            insn->pc == entry || insn->vector ? QEMU_PLUGIN_CB_R_REGS : QEMU_PLUGIN_CB_NO_REGS, insn);
        qemu_plugin_register_vcpu_mem_cb(item, memory, QEMU_PLUGIN_CB_NO_REGS, QEMU_PLUGIN_MEM_RW, insn);
    }
}

#if QEMU_PLUGIN_VERSION >= 7
static void finish(void *data) {
#else
static void finish(qemu_plugin_id_t id, void *data) {
    (void)id;
#endif
    (void)data;
    for (unsigned cpu = 0; cpu < CPUS; ++cpu) {
        State *s = &states[cpu];
        if (s->file) {
            fprintf(s->file, "{\"kind\":\"end\",\"instructions\":%"PRIu64",\"recorded\":%"PRIu64",\"memory_callbacks\":%"PRIu64",\"closed\":%s,\"truncated\":%s,\"failure\":%s}\n",
                s->count, s->recorded, s->memory, s->closed ? "true" : "false",
                s->count > maximum ? "true" : "false", atomic_load(&failure) ? "true" : "false");
            if (ferror(s->file) || fclose(s->file)) qemu_plugin_outs("fragment trace write failed\n");
        }
        if (s->buffer) g_byte_array_unref(s->buffer);
    }
    g_ptr_array_free(allocations, true);
}

QEMU_PLUGIN_EXPORT int qemu_plugin_install(qemu_plugin_id_t id, const qemu_info_t *info, int argc, char **argv) {
    if (strcmp(info->target_name, "riscv64")) return -1;
    for (int i = 0; i < argc; ++i) {
        if (!strncmp(argv[i], "entry=", 6)) entry = strtoull(argv[i]+6, NULL, 0);
        else if (!strncmp(argv[i], "out=", 4)) prefix = argv[i]+4;
        else if (!strncmp(argv[i], "max=", 4)) maximum = strtoull(argv[i]+4, NULL, 0);
        else return -1;
    }
    if (!entry || !prefix || !maximum) return -1;
    allocations = g_ptr_array_new_with_free_func(g_free);
#if QEMU_PLUGIN_VERSION >= 7
    qemu_plugin_register_vcpu_init_cb(id, init, NULL);
    qemu_plugin_register_vcpu_tb_trans_cb(id, translate, NULL);
#else
    qemu_plugin_register_vcpu_init_cb(id, init);
    qemu_plugin_register_vcpu_tb_trans_cb(id, translate);
#endif
    qemu_plugin_register_atexit_cb(id, finish, NULL);
    return 0;
}
