# Eligible recurrent prefill fusion

## Source decision

Both [IME screens](2026-10-02-ime-scheduling.md) completed without a qualifying
candidate. The [profile](2026-10-02-prefill-profile.md) showed about 7% of
sampled CPU on visible recurrent stacks; this is a lower bound, not a removable
wall-time share or a speed prediction.

The original `ggml_compute_forward_gated_delta_net_one_chunk` already loops
through tokens sequentially. Inside that loop, it dispatches to
`ggml_gdn_decode_step_rvv` only for scalar gates, K=1 and one-token input.
The helper combines gate scaling with the key dot, and the rank-one update
with the query dot. The generic path traverses the state separately for each.

[The candidate](../bench/k1-gdn-test.py) permits this existing per-token step
for multi-token input when `SPINE_GDN_PREFILL=1`. It retains scalar gates,
K=1, original token order, and the `SPINE_GDN_RVV=0` disable switch.
K>1 snapshot handling and vector gates keep their original paths.
The separate external/in-place state graph optimization is not expanded.
The candidate remains opt-in and is built in an isolated CPU library by
replacing only `ops.cpp.o`; the original build is preserved.

## Checks

[Native harness](../bench/test-k1-gdn.cpp) uses four GGML CPU workers with
strict placement on cores 0-3. It compares enabled/disabled attention outputs
and final/snapshot states bit for bit and checks input, output and scratch
guards. The 158-case matrix covers S32/128/256, one and multiple tokens,
two head counts, one/two sequences, scalar/vector gates, K1/K3, and the
existing single-token external-state path.

GGUF metadata establishes both models' state size as 128 and key groups as
16. Their value head counts are 16 for 2B and 32 for 4B, with inner sizes
2048/4096. The controller verifies these metadata values before timing.
Operator timing uses the actual S128/H16/Hk16 and S128/H32/Hk16 shapes with
8/32 tokens. Six balanced AB/BA blocks reuse a persistent GGML threadpool;
each arm calibrates to at least 100 ms wall time. This includes graph compute
and GGML synchronization, but excludes full-model costs.

At least two operator shapes must clear both 3% mean gain and the full control
range, with no clear regression. Only then does the inherited controller run
four ABBA cold 2B/512 requests, then conditionally 2B/2k and 4B/1k. Those
requests must prove no cache reuse, matching prompt token hashes, one output
token, matching outputs and the selected candidate activation. Settings stay
direct, four threads, batch/microbatch 32, F16 KV, wide attention and layout 0.
Long-context and complete-answer checks remain necessary before adoption.

## Completed run

Run: `k1-gdn-20261002-185831`.
Board tmux: `k1_gdn_k1-gdn-20261002-185831`.
Collector: `k1_gdn_collect_k1-gdn-20261002-185831`.

The isolated build completed and the 158-case numerical gate passed with
bitwise-equal attention/state and intact fallbacks/input/guards. Operator
timing completed with 48 records and qualified all four shapes:

| Value heads | Tokens | Mean reduction | Control range |
| --- | --- | --- | --- |
| 16 | 8 | 24.28% | 2.83% |
| 16 | 32 | 26.45% | 2.65% |
| 32 | 8 | 26.14% | 1.53% |
| 32 | 32 | 27.82% | 1.27% |

The run completed with **exit 0** in **441.59 seconds (7.36 minutes)**.
The collector completed; the archive and all 29 collected artifact hashes
were verified locally. The final screen status is **inconclusive**, because
the model gain fell below the preset 3% promotion threshold.

### Full-model result

Four balanced cold 2B/512 requests produced the following prefill timings:

| Arm | Individual prompt times | Mean | Prompt throughput |
| --- | --- | --- | --- |
| Control | 22.064222 s, 22.060098 s | 22.062160 s | 23.207 tokens/s |
| Recurrent fusion | 21.560296 s, 21.513857 s | 21.537077 s | 23.773 tokens/s |

The observed prompt-time reduction is **2.380%**, or **0.525 seconds** per
512-token prompt. Throughput rises 2.44%. Mean first-token time similarly
falls from 22.066584 s to 21.541556 s. Control prompt-time range was 0.0187%.
All four requests proved zero cache reuse and matching prompt token hashes;
the generated token and output hashes matched between arms.

This is a small positive pilot result, not a statistically established or
generalized model speedup. There are only two launches per arm, and each
request generates one token. The preset gate required a reduction above both
3% and the full control range, so it did not advance to 2B/2k or 4B/1k.
No long-context, 4B full-model, decode or complete-answer claim follows.

Keep this candidate opt-in. The 24-28% operator reductions apply to the
recurrent operator; most full-model work remains outside that operator.
A separate small-effect replication would be needed to establish whether
the 2.38% model reduction is worth adoption. The current run does not justify
lowering its gate after seeing the result.

Evidence: [summary](raw/k1-gdn-20261002-185831/summary.json),
[numerical gate](raw/k1-gdn-20261002-185831/numeric.log),
[operator arms](raw/k1-gdn-20261002-185831/operator.jsonl),
[control request](raw/k1-gdn-20261002-185831/2B-512-q0-pass1.jsonl),
[candidate request](raw/k1-gdn-20261002-185831/2B-512-q1-pass2.jsonl), and
[collection receipt](raw/k1-gdn-20261002-185831/collection-receipt.json).
