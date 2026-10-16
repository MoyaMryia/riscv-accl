// Probe /dev/tcm directly: map all blocks, measure per-block read/write bandwidth.
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <chrono>
#include <sys/mman.h>
#include <unistd.h>

int main() {
    int fd = open("/dev/tcm", O_RDWR);
    if (fd < 0) { perror("open /dev/tcm"); return 1; }
    // try mapping 4 blocks x 128KB
    size_t blk = 128 * 1024;
    for (int b = 0; b < 4; b++) {
        void * p = mmap(NULL, blk, PROT_READ | PROT_WRITE, MAP_SHARED, fd, b * blk);
        if (p == MAP_FAILED) { perror("mmap"); return 1; }
        char * buf = (char *) p;
        auto t0 = std::chrono::steady_clock::now();
        const int reps = 2000;
        for (int r = 0; r < reps; r++) memset(buf, r, blk);
        auto t1 = std::chrono::steady_clock::now();
        volatile int64_t sink = 0;
        int64_t acc = 0;
        for (int r = 0; r < reps; r++) {
            const int64_t * q = (const int64_t *) buf;
            for (size_t i = 0; i < blk / 8; i += 8) acc += q[i];
        }
        auto t2 = std::chrono::steady_clock::now();
        sink = acc;
        double w_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
        double r_ms = std::chrono::duration<double, std::milli>(t2 - t1).count();
        double gb   = (double) blk * reps / 1e9;
        fprintf(stderr, "[tcm] blk%d va=%p write=%.2f GB/s read=%.2f GB/s\n", b, p, gb / (w_ms / 1e3), gb / (r_ms / 1e3));
        munmap(p, blk);
    }
    close(fd);
    return 0;
}
