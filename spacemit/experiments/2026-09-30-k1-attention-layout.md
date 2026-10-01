# Compact attention layouts for SpacemiT K1

See the [documentation guide](../DOCS.md) for the dated status snapshot.
The [fast-test design](2026-09-30-fast-test-design.md) now implements a shorter
staged protocol; the completed run below used its original pilot protocol.

Date: 2026-09-30. This is an opt-in experiment based on the inspected
integrated source at `a990751` with the existing wide RVV patch. It changes
attention scratch packing and query blocking. Model head dimensions, KV
cache contents, weight format, microbatch size, and 64-key softmax grouping
retain their existing values.

## Layouts

The K1 has 256-bit vector registers, 32 KiB private data caches, and a
512 KiB L2 shared by the four preferred IME cores. The experiment uses F16
storage for packed Q/K/V and F32 storage for logits, masks, and output
accumulators. Each worker owns its scratch; rows remain contiguous across
the 256-dimensional head.

| Buffer | Current Q64 layout span | Compact Q32 | Compact Q16 |
| --- | ---: | ---: | ---: |
| Packed Q | 64 KiB reservation, F16 alias | 16 KiB | 8 KiB |
| Logits | 16 KiB | 8 KiB | 4 KiB |
| Mask | 16 KiB | 8 KiB | 4 KiB |
| Output accumulation | 64 KiB | 32 KiB | 16 KiB |
| Packed V | 64 KiB reservation, F16 alias | 32 KiB | 32 KiB |
| Transposed K | 64 KiB reservation, F16 alias | 32 KiB | 32 KiB |
| Total layout span per worker | 288 KiB | 128 KiB | 96 KiB |
| Four workers | 1,152 KiB | 512 KiB | 384 KiB |

The table omits cache-line padding and small stack arrays. Layout span is
not a measured cache working set. Q16 leaves more nominal L2 space, but
splitting a 32-query microbatch into two tiles repeats K/V packing and scans.
Q32 avoids that extra split but leaves less cache capacity for other data.
The completed pilot below found small effects; neither layout has been adopted.

The existing planner still reserves the larger generic workspace so fallback
paths have sufficient memory. The compact kernel packs worker buffers into
the smaller span within that allocation. This experiment targets locality
and scratch traffic; it does not establish a reduction in process RSS.

## Implementation and gates

[The patch](2026-09-30-k1-attention-layout.patch) specializes the existing
tiled routine for Q16/Q32, with KV=64 and compact F16 packing. It removes
full K/V scratch clears from those specializations and initializes padded
V entries on partial tiles. PV still consumes all 64 entries, so padding
must remain initialized even when its probabilities are zero. Only valid
output rows are cleared. The original layout remains available as the
same-binary control.

`SPINE_FA_K1_LAYOUT=0`, `16`, or `32` selects the layout. The experiment
requires the existing `SPINE_FA_WIDE_TILE=1` dispatcher. Compact execution
is limited to VLEN=256, F32 Q, F16 K/V, 256-dimensional heads, at least
16 query rows, and non-reference execution. The kernel logs its activation.

[The native harness](../bench/test-k1-attention-layout.cpp) compares 235
cases per mode: partial query/key tiles, grouped query heads, thread chunks
that cross head boundaries, causal masks, fully masked rows, short-query
fallback, and a smaller-head fallback. Scratch starts filled with NaNs and
has canaries on both sides. Each mode dumps its float outputs; `cmp` requires
both candidates to match the control bit for bit before model tests start.
This exercises kernel output and boundaries; it does not test a changed
recurrent algorithm because this patch leaves that algorithm unchanged.

After the numerical gate, the board runner compares the same server binary
with layouts `0/16/32/32/16/0` on both required models, at 128 and 2,048
prompt tokens, producing 32 greedy output tokens per request. It requires
matching output hashes and activation markers. Two launches per arm provide
a pilot comparison; no statistical significance or 8k speedup is implied.

## Run and collect

```bash
python3 spacemit/bench/start-k1-attention-layout.py
```

The launcher verifies the baseline commit and source hashes, stages the
code, starts a board tmux job, and starts a local tmux collector. The board
job waits up to 12 hours for the document-quality lock, then checks that no
other server is active. It builds a separate checkout under the printed
run directory. A concurrent quality benchmark retains its existing binary.

The numerical and model tests have explicit timeouts and stop on failure.
The collector downloads logs and summaries after the board exits. Numeric
binary dumps and the isolated checkout stay on the board. If collection
is interrupted, resume it with:

```bash
python3 spacemit/bench/start-k1-attention-layout.py --collect-only \
  --run-dir /absolute/path/to/the/printed/run
```

The printed run directory contains `run.json`, source provenance, collector
logs, and eventually `summary.md`, `summary.json`, and `exit-status`.
Until an exit status and successful gates exist, this is a queued or active
experiment, not a demonstrated optimization. If a layout helps the short
test, confirm its effect at 8k before adopting it for long documents.

## Completed pilot

Completion verified on 2026-10-01. The original run
[`k1-layout-20260930-153134`](../reports/raw/k1-layout-20260930-153134/summary.md)
exited **0**. Native compilation passed and all 235 cases per layout matched
bit for bit. All 24 model completions matched token and text hashes within
each model/context group, with two launches per arm.

| Model | Prompt | Control TTFT | Q16 reduction | Q32 reduction |
| --- | ---: | ---: | ---: | ---: |
| 2B | 128 | 5.691 s | 0.40% | 0.28% |
| 2B | 2048 | 95.357 s | 0.32% | 0.89% |
| 4B | 128 | 14.634 s | 0.88% | 1.29% |
| 4B | 2048 | 248.249 s | -0.29% | 1.98% |

These are small pilot effects, without statistical significance or an 8k
comparison. Retain the original layout. The completed isolated build is
reused by the [fast controller](../bench/start-k1-fast-test.py), after source,
build and model verification.

The new harness runs four numerical workers concurrently and adds long KV
cases for **241 cases per layout**. The first fast run passed that gate but
exceeded the initial 90-second operator budget; it is an incomplete timing
run. The corrected run uses a 300-second budget and retains all six balanced
blocks and all model shapes. See the [October 1 update](../reports/2026-10-01-fast-method.md)
for its status.
