# Failed initial harness and corrected diagnostic

The initial archive and collection receipt describe the original failed run.
`test-ime-debug.cpp` and `numeric-debug.log` were retrieved separately after
collection. They preserve the corrected harness and its successful native run.

The first diagnostic identified `mode=0 bl=64 kb=7 n=16 m=1 zp=0 row=0
col=2 value=inf`. The original one-row quantizer hardcodes K32 blocks, so its
output was not a valid K64 GEMM input. The corrected harness constructs generic
one-row blocks and adds a scalar full-M4 reference. The production source and
candidate library were unchanged during this diagnostic.

The successful diagnostic is not an operator/model speed result. A fresh
staged run, `k1-ime-20261002-183608`, repeats the corrected numerical gate
before any timing.

Subsequent diagnostic files `candidate-gather.cpp`, `test-ime-gather.cpp` and
`numeric-gather.log` preserve a separate scale-gather build. That diagnostic
passes all five modes and the scalar M4 reference. It used a distinct
`gather-debug/` library on the board, preserving the initial candidate library.
Timing is performed in fresh run `k1-ime-20261002-184503`.
