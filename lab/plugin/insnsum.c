/* insnsum: minimal QEMU TCG plugin - total guest instruction count at exit.
 * Build: gcc -shared -fPIC -O2 -I<qemu-src>/include/plugins -o libinsnsum.so insnsum.c
 * Use:   qemu-system-riscv64 ... -plugin file=libinsnsum.so
 * Output (stderr, at exit): insn_total=<uint64>
 * QEMU_PLUGIN_VERSION 7 (QEMU 11.x)
 */
#include <qemu-plugin.h>
#include <stdio.h>
#include <inttypes.h>

QEMU_PLUGIN_EXPORT int qemu_plugin_version = QEMU_PLUGIN_VERSION;

static struct qemu_plugin_scoreboard *counts;
static qemu_plugin_u64 insn_count;

static void plugin_exit(void *udata)
{
    fprintf(stderr, "insn_total=%" PRIu64 "\n", qemu_plugin_u64_sum(insn_count));
}

static void vcpu_tb_trans(struct qemu_plugin_tb *tb, void *userdata)
{
    qemu_plugin_register_vcpu_tb_exec_inline_per_vcpu(
        tb, QEMU_PLUGIN_INLINE_ADD_U64, insn_count,
        (uint64_t)qemu_plugin_tb_n_insns(tb));
}

QEMU_PLUGIN_EXPORT int qemu_plugin_install(qemu_plugin_id_t id,
                                           const qemu_info_t *info,
                                           int argc, char **argv)
{
    counts = qemu_plugin_scoreboard_new(sizeof(uint64_t));
    insn_count = qemu_plugin_scoreboard_u64(counts);
    qemu_plugin_register_vcpu_tb_trans_cb(id, vcpu_tb_trans, NULL);
    qemu_plugin_register_atexit_cb(id, plugin_exit, NULL);
    return 0;
}
