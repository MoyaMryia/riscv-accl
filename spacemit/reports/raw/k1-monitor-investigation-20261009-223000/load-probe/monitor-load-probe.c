#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

extern uint64_t probe_load(const void *);
static uint64_t expected(size_t index, unsigned pass) {
    if ((index & 7) == 0) return UINT64_C(0x6a8a28);
    return (UINT64_C(0x9e3779b97f4a7c15) * (index + 42 + pass)) ^ UINT64_C(0xa55a0123456789ab);
}
int main(void) {
    const size_t count = 131072;
    uint64_t *data = aligned_alloc(128, count * 128);
    if (!data) return 2;
    for (unsigned pass = 0; pass < 64; pass++) {
        for (size_t index = 0; index < count; index++) {
            for (size_t field = 0; field < 16; field++) data[index * 16 + field] = ~expected(index + field, pass);
            data[index * 16 + 13] = expected(index, pass);
        }
        for (size_t index = 0; index < count; index++) {
            uint64_t value = probe_load(data + index * 16);
            uint64_t want = expected(index, pass);
            if (value != want) {
                fprintf(stderr, "mismatch pass=%u index=%zu address=%p expected=%016lx actual=%016lx reread=%016lx\n", pass, index, (void *)(data + index * 16 + 13), (unsigned long)want, (unsigned long)value, (unsigned long)probe_load(data + index * 16));
                free(data);
                return 1;
            }
        }
    }
    free(data);
    puts("PASS: 8388608 loads; 16777216 bytes; seed 42");
    return 0;
}
