# Cold-prefill profiling after the layout screen

Status snapshot: 2026-10-02, Asia/Singapore. Profiling is running; its final
`phase`, `summary.json` and `exit-status` determine completion.

## Completed layout decision

The [corrected fast screen](raw/k1-fast-20261001-224957/summary.md) completed
at 22:58:26 on October 1 with exit 0, taking 507.14 seconds (8.45 minutes)
including preparation. Numerical checks took 16.39 seconds, operator timing
136.21 seconds and the 2B/512 model screen 214.50 seconds.

All 241 concurrent cases per layout matched bit for bit. Six balanced operator
blocks produced all 216 records. All six model requests were uncached and had
matching input/output hashes. Q16 reduced mean prompt time by 0.32%, Q32 by
0.53%; neither exceeded the 3%/control-range advancement threshold. No 2k/4B
confirmation, 8k comparison or quality run followed. Retain layout 0.

## Profiling protocol

[Profiler](../bench/profile-k1-prefill.py),
[launcher](../bench/start-k1-prefill-profile.py), and
[commands](../bench/README.md#cold-prefill-profiling).

One forced-cold 2048-token request per model uses the verified existing binary:
Q4_0 weights, F16 KV, four threads, batch/microbatch 32, wide RVV attention,
layout 0 and one direct greedy output token. Source, model and runtime hashes
must match the completed fast screen. No inference source rebuild is needed.

Sampling attaches after server health and tokenization. Disabled events are
enabled with an acknowledged perf control command immediately before the
request and disabled immediately afterwards. Completion and exact cold prompt
counts are checked. The profile includes first-token work and final request
handling; it excludes startup and tokenization. It is diagnostic, not a speed
comparison.

### Available board profiling

- `task-clock:u` and `cycles:u` counting worked without changing permissions.
- Hardware `cycles:u` sampling yielded no samples on the compute probe.
- Software `cpu-clock:u` sampling worked at 199 Hz.
- DWARF decoding emitted RISC-V IP/SP-register errors. Frame-pointer decoding
  worked, capturing 243 samples in a separate compute probe with no decoder
  errors. Frame completeness in the inference binary is measured separately.

The run uses **software user CPU-time sampling and frame-pointer stacks**.
Sample periods weight the CPU shares. Each sample belongs to one visible
operator group; parent and child costs are not added together. Self-symbol
hotspots are saved separately, as are raw perf data, decoded stacks, lost-event
diagnostics and selected attention/GDN/copy disassembly annotations.

Visible recurrent/attention/matmul stack shares are lower bounds if parents
are missing. Unknown leaves and multi-frame sample coverage are reported.
The visible attention-copy subset does not include inlined K transpose, so it
cannot establish total packing cost. Annotation errors are recorded separately
and do not turn an otherwise complete sample capture into a packing measurement.
A short 2k diagnostic cannot establish how the bottleneck changes at 8k.

## Applied run

The first launch, `k1-profile-20261002-153803`, exited 1 before sending a
request. The board perf acknowledgment was `ack\n` followed by a NUL byte.
The original strict check rejected that terminator. A direct board control
probe reproduced it; the parser now accepts the line with or without its NUL
and still rejects other responses. No inference profile from that launch is
claimed. The corrected run is fresh and retains source/model/runtime checks.


Corrected run: `k1-profile-20261002-154340`.
Board tmux: `k1_profile_k1-profile-20261002-154340`.
Workstation collector: `k1_profile_collect_k1-profile-20261002-154340`.

Results directory: `spacemit/reports/raw/k1-profile-20261002-154340`.
The collector downloads final summaries, request telemetry, stacks, annotations
and raw perf data. Collection-only recovery is available. The board run has a
30-minute limit after acquiring the benchmark lock and stops on invalid or
insufficient samples. The lock wait is separate.

Four attribution/control tests and parsing of actual board perf output passed. No
inference profile percentages or next optimization are claimed yet. Inspect
both model profiles before selecting recurrent fusion, packing reuse or another
change. If stacks leave substantial recurrent helper work unattributed, add
isolated operator timing before making a whole-operator cost claim.
