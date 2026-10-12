#include "common.h"
#if defined(__riscv_vector)
#include <riscv_vector.h>
#endif

struct Conv {
    static constexpr float guard = 12345.25f;
    int channels, tokens, sequences, stride;
    std::vector<float> history, input, weights, assembled, output, state;
    Conv(int c, int t, int s, int pad): channels(c), tokens(t), sequences(s), stride(c+pad),
        history(s*c*3+32, guard), input(s*t*stride+32, guard), weights(c*4+32, guard),
        assembled(s*(t+3)*c+32, guard), output(s*t*c+32, guard), state(s*c*3+32, guard) {
        uint32_t seed = 42;
        auto next = [&] { seed = seed*1664525u+1013904223u; return (int(seed>>16)-32768)/32768.0f; };
        for (auto * v : {&history, &input, &weights})
            for (size_t i=16; i<v->size()-16; ++i) (*v)[i] = next();
    }
    const float * sample(int seq, int time, int c) const {
        if (time < 3) return history.data()+16+seq*channels*3+c*3+time;
        return input.data()+16+(seq*tokens+time-3)*stride+c;
    }
    void step(Workers & workers, int id, int mode) {
        const int first = (channels*id)/4, last = (channels*(id+1))/4;
        if (mode == 0) {
            for (int s=0; s<sequences; ++s) for (int t=0; t<tokens+3; ++t)
                for (int c=first; c<last; ++c)
                    assembled[16+(s*(tokens+3)+t)*channels+c] = *sample(s,t,c);
            workers.sync();
        }
        for (int s=0; s<sequences; ++s) for (int t=0; t<tokens; ++t) {
            int c = first;
#if defined(__riscv_vector)
            for (; c<last;) {
                const size_t vl = __riscv_vsetvl_e32m1(last-c);
                vfloat32m1_t sum = __riscv_vfmv_v_f_f32m1(0.0f, vl);
                for (int tap=0; tap<4; ++tap) {
                    const int time = t+tap;
                    vfloat32m1_t x;
                    if (mode == 0) x = __riscv_vle32_v_f32m1(
                        assembled.data()+16+(s*(tokens+3)+time)*channels+c, vl);
                    else if (time < 3) x = __riscv_vlse32_v_f32m1(sample(s,time,c), 3*sizeof(float), vl);
                    else x = __riscv_vle32_v_f32m1(sample(s,time,c), vl);
                    const auto w = __riscv_vlse32_v_f32m1(weights.data()+16+c*4+tap, 4*sizeof(float), vl);
                    const auto product = __riscv_vfmul_vv_f32m1(x, w, vl);
                    sum = __riscv_vfadd_vv_f32m1(sum, product, vl);
                }
                __riscv_vse32_v_f32m1(output.data()+16+(s*tokens+t)*channels+c, sum, vl);
                c += vl;
            }
#endif
            for (; c<last; ++c) {
                float sum = 0.0f;
                for (int tap=0; tap<4; ++tap) {
                    const float x = mode == 0 ? assembled[16+(s*(tokens+3)+t+tap)*channels+c] : *sample(s,t+tap,c);
                    sum += x*weights[16+c*4+tap];
                }
                output[16+(s*tokens+t)*channels+c] = sum;
            }
        }
        for (int s=0; s<sequences; ++s) for (int c=first; c<last; ++c) for (int h=0; h<3; ++h)
            state[16+s*channels*3+c*3+h] = mode == 0
                ? assembled[16+(s*(tokens+3)+tokens+h)*channels+c] : *sample(s,tokens+h,c);
        workers.sync();
    }
    void check(const Conv & original, const std::vector<float> & expected, const std::vector<float> & tail) const {
        need(same_bits(history,original.history) && same_bits(input,original.input) &&
            same_bits(weights,original.weights), "input identity");
        need(same_bits(output,expected) && same_bits(state,tail), "output or state differs bitwise");
        for (const auto * v : {&history, &input, &weights, &assembled, &output, &state})
            for (int i=0; i<16; ++i) need((*v)[i] == guard && (*v)[v->size()-1-i] == guard, "array guards");
    }
    void scalar(std::vector<float> & out, std::vector<float> & tail) const {
        out.assign(output.size(), guard); tail.assign(state.size(), guard);
        for (int s=0; s<sequences; ++s) for (int t=0; t<tokens; ++t) for (int c=0; c<channels; ++c) {
            float sum = 0.0f;
            for (int tap=0; tap<4; ++tap) sum += *sample(s,t+tap,c)*weights[16+c*4+tap];
            out[16+(s*tokens+t)*channels+c] = sum;
        }
        for (int s=0; s<sequences; ++s) for (int c=0; c<channels; ++c) for (int h=0; h<3; ++h)
            tail[16+s*channels*3+c*3+h] = *sample(s,tokens+h,c);
    }
};

int main(int argc, char ** argv) {
    const bool bench = argc == 5 && strcmp(argv[1], "--bench") == 0;
    need(argc == 1 || bench, "usage: conv [--bench CHANNELS TOKENS ARM]");
    Workers pool(bench);
    if (bench) {
#if !defined(__riscv_vector)
        need(false, "K1 timing requires RVV");
#endif
        const int c=atoi(argv[2]), t=atoi(argv[3]), arm=atoi(argv[4]);
        need((c == 6144 || c == 8192) && (t == 8 || t == 32) && (arm == 0 || arm == 1), "benchmark shape");
        Conv f(c,t,1,0), original=f;
        std::vector<float> expected, tail; f.scalar(expected, tail);
        char shape[80]; snprintf(shape, sizeof(shape), "C%d-T%d", c,t);
            measure("conv", shape, arm, 0, [&](int n) {
                return pool.run([&](int id) { for (int i=0; i<n; ++i) f.step(pool,id,arm); });
            }, [&] { f.check(original,expected,tail); });
    } else {
        int cases=0;
        for (int c : {1,7,65,6144,8192}) for (int t : {1,2,3,8,31,32}) for (int pad : {0,5}) {
            Conv f(c,t,2,pad), original=f;
            std::vector<float> expected, tail; f.scalar(expected,tail);
            for (int mode : {0,1}) {
                pool.run([&](int id) { f.step(pool,id,mode); });
                f.check(original,expected,tail);
            }
            ++cases;
        }
        printf("PASS: %d convolution cases; full output/state and guards\n", cases);
    }
}
