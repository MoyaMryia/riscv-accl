#define main quick_numeric_main
#include "conv-kernel.cpp"
#undef main

int main(int argc, char **argv) {
    need(argc == 5, "usage: profile CHANNELS TOKENS ARM DUMP");
    int c = atoi(argv[1]), t = atoi(argv[2]), arm = atoi(argv[3]);
    need((c == 6144 || c == 8192) && (t == 8 || t == 32) && (arm == 0 || arm == 1), "profile shape");
    Workers pool(false);
    Conv f(c, t, 1, 0), original = f;
    std::vector<float> expected, tail;
    f.scalar(expected, tail);
    pool.run([&](int id) { f.step(pool, id, arm); });
    f.check(original, expected, tail);
    FILE *stream = fopen(argv[4], "wbx");
    need(stream != nullptr, "dump open");
    for (const auto *v : {&f.history, &f.input, &f.weights, &f.output, &f.state})
        need(fwrite(v->data(), sizeof(float), v->size(), stream) == v->size(), "dump write");
    need(fclose(stream) == 0, "dump close");
    puts("PASS: full input, output, state and guards");
}
