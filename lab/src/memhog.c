/*
 * memhog — 占住指定容量物理内存，为 8G 包络测试充当硬隔离层
 *
 * 用法: memhog <MB> [--quiet]
 *   分配并触碰 MB MiB 匿名内存，mlock 钉死 + MADV_POPULATE_WRITE 预填充，
 *   OOM 豁免（oom_score_adj=-1000），完成后打印 "memhog READY <MB>" 到 stdout
 *   并阻塞等待 stdin EOF（或 SIGTERM/SIGINT）后释放退出。
 *
 * 退出码: 0 成功占住 | 1 分配/mlock 失败（包络未建立，调用方必须放弃测试）
 *
 * 用法约定: 由 bench-wrapper 在启动 llama-bench 前拉起，并验证
 *   /proc/meminfo MemAvailable 下降至预期值后才允许正式测试。
 * 构建: gcc -O2 -o memhog memhog.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <unistd.h>

static size_t total_mb;

static volatile sig_atomic_t g_stop = 0;
static void on_term(int sig) { (void)sig; g_stop = 1; }

int main(int argc, char **argv)
{
    if (argc < 2) { fprintf(stderr, "usage: memhog <MB>\n"); return 1; }
    total_mb = strtoul(argv[1], NULL, 10);
    size_t bytes = total_mb << 20;

    /* OOM 豁免：内存压力下 hog 绝不被杀，超支由 benchmark 方 OOM 暴露 */
    FILE *f = fopen("/proc/self/oom_score_adj", "w");
    if (f) { fprintf(f, "-1000"); fclose(f); }

    /* mlock 上限放开（root 下通常已无限，双保险） */
    struct rlimit rl = { RLIM_INFINITY, RLIM_INFINITY };
    setrlimit(RLIMIT_MEMLOCK, &rl);

    void *p = malloc(bytes);
    if (!p) { fprintf(stderr, "memhog: malloc %zu MB failed\n", total_mb); return 1; }

    /* 逐页触碰：填满全部页表项，任何失败都意味着包络不可信 */
    for (size_t off = 0; off < bytes; off += 4096) ((volatile char *)p)[off] = 1;
    if (mlock(p, bytes) != 0) { fprintf(stderr, "memhog: mlock failed (raise RLIMIT_MEMLOCK)\n"); return 1; }
    if (madvise(p, bytes, MADV_POPULATE_WRITE) != 0) {
        /* 老内核无 MADV_POPULATE_WRITE 可忽略——上面的逐页触碰已填充 */
    }

    printf("memhog READY %zu\n", total_mb);
    fflush(stdout);

    signal(SIGTERM, on_term);
    signal(SIGINT, on_term);

    /* 阻塞直到收到信号。stdin EOF 不释放（wrapper 场景 stdin 可能被关闭），
     * 释放的唯一途径是 SIGTERM/SIGINT —— 保证包络生命周期完全受控 */
    while (!g_stop) {
        int c = getchar();
        if (c == EOF) { while (!g_stop) pause(); }
        /* 收到换行也继续持有：正常终止只认信号 */
    }

    printf("memhog RELEASE %zu\n", total_mb);
    fflush(stdout);
    return 0;
}
