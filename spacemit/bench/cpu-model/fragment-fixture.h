#ifndef K1_FRAGMENT_FIXTURE_H
#define K1_FRAGMENT_FIXTURE_H
#include <stddef.h>
#include <stdint.h>

/* 片段必须只读输入，并且完整写入声明的输出。 */
typedef void (*fragment_function)(const uint8_t *, uint8_t *, size_t);
struct fragment_case {
    const char *id;
    size_t work_units, input_bytes, output_bytes, offset;
};
struct fragment_kernel { const char *id; fragment_function function; };
extern const struct fragment_case fragment_cases[];
extern const size_t fragment_case_count;
extern const struct fragment_kernel fragment_kernels[];
extern const size_t fragment_kernel_count;
void fragment_reference(const uint8_t *, uint8_t *, size_t);
#endif
