#pragma once
#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <functional>
#include <pthread.h>
#include <sched.h>
#include <string>
#include <thread>
#include <vector>

static void need(bool ok, const char * reason) {
    if (!ok) { fprintf(stderr, "FAIL: %s\n", reason); std::exit(1); }
}

template<class T>
static bool same_bits(const std::vector<T> & a, const std::vector<T> & b) {
    return a.size() == b.size() && (a.empty() || memcmp(a.data(), b.data(), a.size()*sizeof(T)) == 0);
}

struct Workers {
    pthread_barrier_t start, finish, stage;
    std::array<std::thread, 4> threads;
    std::function<void(int)> work;
    bool stop = false;
    explicit Workers(bool pin) {
        need(pthread_barrier_init(&start, nullptr, 5) == 0, "start barrier");
        need(pthread_barrier_init(&finish, nullptr, 5) == 0, "finish barrier");
        need(pthread_barrier_init(&stage, nullptr, 4) == 0, "stage barrier");
        for (int id = 0; id < 4; ++id) threads[id] = std::thread([this, id, pin] {
            if (pin) {
                cpu_set_t mask; CPU_ZERO(&mask); CPU_SET(id, &mask);
                need(pthread_setaffinity_np(pthread_self(), sizeof(mask), &mask) == 0, "worker affinity");
            }
            fprintf(stderr, "QUICK_WORKER id=%d cpu=%d pinned=%d\n", id, sched_getcpu(), pin);
            while (true) {
                pthread_barrier_wait(&start);
                if (stop) break;
                work(id);
                pthread_barrier_wait(&finish);
            }
        });
    }
    void sync() { pthread_barrier_wait(&stage); }
    double run(std::function<void(int)> fn) {
        work = std::move(fn);
        const auto begin = std::chrono::steady_clock::now();
        pthread_barrier_wait(&start);
        pthread_barrier_wait(&finish);
        return std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now()-begin).count();
    }
    ~Workers() {
        stop = true;
        pthread_barrier_wait(&start);
        for (auto & thread : threads) thread.join();
        pthread_barrier_destroy(&start); pthread_barrier_destroy(&finish); pthread_barrier_destroy(&stage);
    }
};

template<class Run, class Check>
static void measure(const char * candidate, const char * shape, int arm, int block, Run run, Check check) {
    run(1);
    int iterations = 1;
    double elapsed;
    while (true) {
        elapsed = run(iterations);
        if (elapsed >= 100.0) break;
        need(iterations < 1048576, "calibration limit");
        iterations *= 2;
    }
    check();
    printf("{\"candidate\":\"%s\",\"shape\":\"%s\",\"arm\":%d,\"block\":%d,\"iterations\":%d,\"wall_ms\":%.9f,\"ms_per_call\":%.9f}\n",
        candidate, shape, arm, block, iterations, elapsed, elapsed/iterations);
    fflush(stdout);
}
