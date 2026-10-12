#define _GNU_SOURCE
#include <errno.h>
#include <inttypes.h>
#include <linux/perf_event.h>
#include <sched.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>

static uint64_t cycle(void) {
    uint64_t value;
    __asm__ volatile("rdcycle %0" : "=r"(value));
    return value;
}

int main(void) {
    cpu_set_t mask;
    CPU_ZERO(&mask);
    CPU_SET(0, &mask);
    if (sched_setaffinity(0, sizeof mask, &mask)) return 2;
    struct perf_event_attr attr = {0};
    attr.size = sizeof attr;
    attr.type = PERF_TYPE_HARDWARE;
    attr.config = PERF_COUNT_HW_CPU_CYCLES;
    attr.disabled = 1;
    attr.exclude_kernel = 1;
    attr.exclude_hv = 1;
    attr.read_format = PERF_FORMAT_TOTAL_TIME_ENABLED | PERF_FORMAT_TOTAL_TIME_RUNNING;
    int fd = syscall(__NR_perf_event_open, &attr, 0, -1, -1, 0);
    int open_error = fd < 0 ? errno : 0;
    struct { uint64_t value, enabled, running; } sample = {0};
    int valid = 0;
    if (fd >= 0) {
        int reset = ioctl(fd, PERF_EVENT_IOC_RESET, 0);
        int enable = ioctl(fd, PERF_EVENT_IOC_ENABLE, 0);
        uint64_t value = 0;
        for (int i = 0; i < 100000; ++i)
            __asm__ volatile("addi %0,%0,1" : "+r"(value));
        int disable = ioctl(fd, PERF_EVENT_IOC_DISABLE, 0);
        ssize_t size = read(fd, &sample, sizeof sample);
        valid = !reset && !enable && !disable && size == sizeof sample && value == 100000 &&
            sample.value > 0 && sample.enabled > 0 && sample.enabled == sample.running;
        close(fd);
    }
    fflush(stdout);
    pid_t child = fork();
    if (child == 0) {
        uint64_t first = cycle(), value = 0;
        for (int i = 0; i < 100000; ++i)
            __asm__ volatile("addi %0,%0,1" : "+r"(value));
        uint64_t last = cycle();
        printf("{\"kind\":\"rdcycle\",\"first\":%"PRIu64",\"last\":%"PRIu64",\"output\":%"PRIu64"}\n", first,last,value);
        fflush(stdout);
        _exit(last > first && value == 100000 ? 0 : 3);
    }
    int status = 0;
    if (child < 0 || waitpid(child, &status, 0) != child) return 4;
    printf("{\"kind\":\"capability\",\"cpu\":%d,\"perf_errno\":%d,\"perf_valid\":%s,\"cycles\":%"PRIu64",\"enabled\":%"PRIu64",\"running\":%"PRIu64",\"rdcycle_signal\":%d,\"rdcycle_exit\":%d}\n",
        sched_getcpu(),open_error,valid ? "true":"false",sample.value,sample.enabled,sample.running,
        WIFSIGNALED(status) ? WTERMSIG(status):0, WIFEXITED(status) ? WEXITSTATUS(status):-1);
    return 0;
}
