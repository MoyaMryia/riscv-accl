// Read every byte of a buffer larger than LLC; GB/s counts source bytes only.
// Initialization, first touch and warm-up are outside each timed interval.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <pthread.h>
#include <sched.h>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>
#ifdef __riscv_vector
#include <riscv_vector.h>
#endif

using Clock = std::chrono::steady_clock;

__attribute__((noinline)) uint64_t read_all(const uint64_t *p, size_t n) {
    // Force fresh reads on each pass, including when this file is built with LTO.
    asm volatile("" ::: "memory");
    size_t i = 0;
    uint64_t result = 0;
#ifdef __riscv_vector
    const size_t vl = __riscv_vsetvlmax_e64m4();
    auto a = __riscv_vmv_v_x_u64m4(0, vl);
    auto b = __riscv_vmv_v_x_u64m4(0, vl);
    auto c = __riscv_vmv_v_x_u64m4(0, vl);
    auto d = __riscv_vmv_v_x_u64m4(0, vl);
    for (; i + 4 * vl <= n; i += 4 * vl) {
        a = __riscv_vxor_vv_u64m4(a, __riscv_vle64_v_u64m4(p + i, vl), vl);
        b = __riscv_vxor_vv_u64m4(b, __riscv_vle64_v_u64m4(p + i + vl, vl), vl);
        c = __riscv_vxor_vv_u64m4(c, __riscv_vle64_v_u64m4(p + i + 2 * vl, vl), vl);
        d = __riscv_vxor_vv_u64m4(d, __riscv_vle64_v_u64m4(p + i + 3 * vl, vl), vl);
    }
    a = __riscv_vxor_vv_u64m4(a, b, vl);
    c = __riscv_vxor_vv_u64m4(c, d, vl);
    a = __riscv_vxor_vv_u64m4(a, c, vl);
    const auto zero = __riscv_vmv_v_x_u64m1(0, 1);
    const auto reduced = __riscv_vredxor_vs_u64m4_u64m1(a, zero, vl);
    result = __riscv_vmv_x_s_u64m1_u64(reduced);
#endif
    for (; i < n; ++i) result ^= p[i];
    return result;
}

int main(int argc, char **argv) {
    try {
        if (argc != 5) throw std::runtime_error("usage: memory-read MiB cpus rounds seconds");
        const size_t bytes = std::stoull(argv[1]) * 1024 * 1024;
        const int rounds = std::stoi(argv[3]);
        const double seconds = std::stod(argv[4]);
        std::vector<int> cpus;
        std::istringstream ids(argv[2]);
        std::string id;
        while (std::getline(ids, id, ',')) cpus.push_back(std::stoi(id));
        if (bytes < 4096 || bytes > size_t(8) * 1024 * 1024 * 1024 || cpus.empty()
            || rounds < 1 || rounds > 50 || seconds <= 0 || seconds > 10)
            throw std::runtime_error("invalid size, CPU list, rounds or duration");
        auto sorted = cpus; std::sort(sorted.begin(), sorted.end());
        if (sorted.front() < 0 || sorted.back() >= CPU_SETSIZE
            || std::adjacent_find(sorted.begin(), sorted.end()) != sorted.end())
            throw std::runtime_error("invalid or duplicate CPU ID");
        uint64_t *data = nullptr;
        if (posix_memalign(reinterpret_cast<void **>(&data), 64, bytes))
            throw std::runtime_error("allocation failed");
        pthread_barrier_t barrier;
        if (pthread_barrier_init(&barrier, nullptr, cpus.size() + 1))
            throw std::runtime_error("barrier initialization failed");
        size_t passes = 1;
        std::vector<uint64_t> checks(cpus.size());
        std::vector<std::thread> workers;
        for (size_t t = 0; t < cpus.size(); ++t) {
            workers.emplace_back([&, t] {
                cpu_set_t mask; CPU_ZERO(&mask); CPU_SET(cpus[t], &mask);
                if (pthread_setaffinity_np(pthread_self(), sizeof(mask), &mask)) {
                    std::cerr << "CPU affinity failed for " << cpus[t] << '\n'; std::exit(3);
                }
                const size_t lines = bytes / 64;
                const size_t begin = (lines * t / cpus.size()) * 8;
                const size_t end = (lines * (t + 1) / cpus.size()) * 8;
                uint64_t expected = 0;
                for (size_t i = begin; i < end; ++i) {
                    data[i] = uint64_t(i) * UINT64_C(0x9e3779b97f4a7c15)
                              ^ UINT64_C(0x123456789abcdef0);
                    expected ^= data[i];
                }
                if (read_all(data + begin, end - begin) != expected) std::exit(4);
                pthread_barrier_wait(&barrier); // All pages initialized and warmed.
                for (int round = -1; round < rounds; ++round) {
                    pthread_barrier_wait(&barrier);
                    uint64_t sum = 0;
                    for (size_t pass = 0; pass < passes; ++pass)
                        sum += read_all(data + begin, end - begin);
                    checks[t] = sum;
                    if (sum != expected * uint64_t(passes)) std::exit(4);
                    pthread_barrier_wait(&barrier);
                }
            });
        }
        pthread_barrier_wait(&barrier);
        for (int round = -1; round < rounds; ++round) {
            const auto start = Clock::now();
            pthread_barrier_wait(&barrier);
            pthread_barrier_wait(&barrier);
            const double elapsed = std::chrono::duration<double>(Clock::now() - start).count();
            if (round >= 0) {
                uint64_t checksum = 0; for (auto check : checks) checksum ^= check;
                std::cout << "{\"buffer_bytes\":" << bytes << ",\"cpus\":\"" << argv[2]
                          << "\",\"round\":" << round << ",\"passes\":" << passes
                          << ",\"seconds\":" << elapsed << ",\"read_bytes\":" << bytes * passes
                          << ",\"GB_per_s\":" << bytes * passes / elapsed / 1e9
                          << ",\"checksum\":" << checksum << ",\"validated\":true,\"kernel\":\""
#ifdef __riscv_vector
                          << "rvv_full_read"
#else
                          << "host_full_read"
#endif
                          << "\"}" << std::endl;
            }
            // Calibration is one complete scan; later rounds target the duration.
            if (round == -1) passes = std::max<size_t>(1, std::min<size_t>(10000, std::ceil(seconds / elapsed)));
        }
        for (auto &worker : workers) worker.join();
        pthread_barrier_destroy(&barrier); free(data);
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n'; return 1;
    }
}
