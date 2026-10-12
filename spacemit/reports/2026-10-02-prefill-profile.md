# Cold-prefill profiling after the layout screen

Status snapshot: 2026-10-02, Asia/Singapore. Profiling completed at 15:52:12
with exit 0, and it took 510.34 seconds. We recovered and verified all
artifacts locally.

## Completed layout decision

The [corrected fast screen](raw/k1-fast-20261001-224957/summary.md) completed
at 22:58:26 on October 1, with exit 0. It took 507.14 seconds (8.45 minutes),
including preparation. The numerical checks took 16.39 seconds, operator
timing 136.21 seconds, and the 2B/512 model screen 214.50 seconds.

All 241 concurrent cases per layout matched bit for bit. Six balanced operator
blocks produced all 216 records. All six model requests were uncached, and
they had matching input and output hashes. Q16 reduced the mean prompt time by
0.32%, and Q32 by 0.53%. Neither reduction exceeded the 3%/control-range
advancement threshold. No 2k/4B confirmation, no 8k comparison, and no quality
run followed. Retain layout 0.

## Profiling protocol

The [profiler](../bench/profile-k1-prefill.py), the
[launcher](../bench/start-k1-prefill-profile.py), and the
[commands](../bench/README.md#cold-prefill-profiling) implement the protocol.

One forced-cold 2048-token request per model uses the verified existing
binary: Q4_0 weights, F16 KV, four threads, batch/microbatch 32, wide RVV
attention, layout 0, and one direct greedy output token. The source, model,
and runtime hashes must match the completed fast screen. No inference source
rebuild is necessary.

Sampling attaches after server health and tokenization. An acknowledged perf
control command enables the disabled events immediately before the request,
and it disables them immediately afterwards. The runner checks completion and
the exact cold prompt counts. The profile includes first-token work and final
request handling. It excludes startup and tokenization. The profile is
diagnostic, not a speed comparison.

### Available board profiling

- `task-clock:u` and `cycles:u` counting worked, without a change of
  permissions.
- Hardware `cycles:u` sampling yielded no samples on the compute probe.
- Software `cpu-clock:u` sampling worked at 199 Hz.
- DWARF decoding emitted RISC-V IP/SP-register errors. Frame-pointer decoding
  worked, and it captured 243 samples in a separate compute probe, with no
  decoder errors. The frame completeness of the inference binary is measured
  separately.

The run uses **software user CPU-time sampling and frame-pointer stacks**. The
sample periods weight the CPU shares. Each sample belongs to one visible
operator group, and the code does not add parent and child costs together. The
runner saves self-symbol hotspots separately, as it saves the raw perf data,
the decoded stacks, the lost-event diagnostics, and selected
attention/GDN/copy disassembly annotations.

The visible recurrent, attention, and matmul stack shares are lower bounds,
because parents can be missing. The runner reports unknown leaves and
multi-frame sample coverage. The visible attention-copy subset does not
include the inlined K transpose, so it cannot establish the total packing
cost. The runner records annotation errors separately, and those errors do not
turn an otherwise complete sample capture into a packing measurement. A short
2k diagnostic cannot establish how the bottleneck changes at 8k.

## Applied run

The first launch, `k1-profile-20261002-153803`, exited 1 before it sent a
request. The board perf acknowledgment was `ack\n`, followed by a NUL byte.
The original strict check rejected that terminator. A direct board control
probe reproduced the behavior. The parser now accepts the line with or without
its NUL, and it still rejects other responses. We claim no inference profile
from that launch. The corrected run is fresh, and it retains the source,
model, and runtime checks.

Corrected run: `k1-profile-20261002-154340`.
Board tmux: `k1_profile_k1-profile-20261002-154340`.
Workstation collector: `k1_profile_collect_k1-profile-20261002-154340`.

Results directory: `spacemit/reports/raw/k1-profile-20261002-154340`.
The collector downloads the final summaries, the request telemetry, the
stacks, the annotations, and the raw perf data. Collection-only recovery is
available. The board run has a 30-minute limit, after it acquires the
benchmark lock. It stops on invalid samples, and it stops when the sample count is too low. The lock wait is
separate.

Four attribution and control tests passed, and the parser handled the actual
board perf output. The initial collector timed out during a transfer of a
69.6 MB repeated text trace. Recovery now creates a compressed archive,
verifies its SHA-256 and every extracted file, and rejects unsafe archive
members. The 18 MB archive and all final artifacts were recovered
successfully. No inference rerun was necessary.

## Measured profile and symbol ownership

The [raw summary](raw/k1-profile-20261002-154340/summary.md) groups the
visible stacks by function name. Its apparent 89% "other" category includes
assembly labels inside known kernels. That category is not mostly unknown
instruction addresses. The
[symbol analysis](raw/k1-profile-20261002-154340/symbol-analysis.json)
resolves three hot labels, with
[ELF symbol ranges](raw/k1-profile-20261002-154340/elf-symbols.txt).

| Measure | 2B | 4B |
| --- | ---: | ---: |
| Cold 2k prompt time under profiling | 93.19 s | 240.11 s |
| Samples | 92,292 | 237,893 |
| Three verified IME GEMM labels, self CPU share | 43.23% | 44.08% |
| Runtime `sync_impl`, self CPU share | 20.03% | 20.03% |
| Gated recurrent work, visible-stack CPU share | 7.20% | 7.46% |
| Attention, visible-stack CPU share | 3.23% | 3.36% |
| Samples with multiple frames | 32.06% | 31.13% |

`BLOCK_INNER_LOOP435`, `BLOCK_COUNTK_LOOP435`, and `RESULT_SAVE435` lie
inside `spacemit_kernels::ime1::gemm_kernel_i8i4`, at ELF addresses `0x146a46`
through `0x14786e` (exclusive). Their combined self samples are a subset of
the total GEMM work. This fact explains why the raw name-based matmul category
of only 0.07–0.09% is not an estimate of the total matrix-multiplication
cost. The hot loops originate in
`ggml/src/ggml-cpu/spacemit/ime1_kernels.cpp` in the verified source
checkout.

Only about one third of the samples have visible parents. The recurrent and
attention shares are therefore lower bounds. Runtime synchronization can poll
while the workers do useful work, so 20% sampled CPU does not imply 20%
removable wall latency. K/V packing remains unseparated: near-zero visible
attention-copy samples do not prove that packing is free. The inlined K
transpose needs a targeted measurement. One short 2k capture per model does
not establish the 8k/16k bottleneck.

## Next optimization decision

Investigate the existing IME int8/int4 GEMM hot loop first: instruction
scheduling, weight loading and unpacking, and redundant work inside the
current 32-token microbatch. Use its own operator timing and numerical checks,
before a change to model execution. An increase of the microbatch size has
earlier negative results, and you must not assume that it helps.

Eligible recurrent prefill fusion remains a separate secondary candidate, with
output and final-state correctness checks. The current evidence does not
justify a priority for another attention layout or for a shared K/V packing
cache. This profile implements no new optimization, and it claims no speedup.
The follow-up [IME scheduling screen](2026-10-02-ime-scheduling.md)
implements three isolated candidates, with numerical and staged timing gates.
