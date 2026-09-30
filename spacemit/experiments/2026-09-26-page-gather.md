# Occupied-page KV gathering experiment

> Dated campaign snapshot. Measurements apply to the stated workload and date.
> Queued/running statements below are historical; use the
> [current guide](../DOCS.md) and the [experiments index](README.md) for later results and current status.

This candidate evaluates page-addressed attention on the existing unified KV
store. It is opt-in with `SPINE_KV_PAGE_GATHER=1`, and is **not adopted**. The
[patch](2026-09-26-page-gather.patch) applies to the board's integrated checkout
at `a990751` and changes only KV and graph plumbing. It requires Qwen3.5,
unified F16 K/V, flash attention, and no shared or sliding cache. Other
configurations fail at cache construction rather than silently enabling only
part of the experiment. The board campaign uses direct decoding.

The current dense attention view spans physical cell zero through the highest
occupied cell, rounded to the backend padding. Empty low pages can therefore
extend the attention shape when later pages still hold data. The prototype
groups physical cells into pages of 32. It builds a logical-to-physical row map
from occupied pages, preserves physical order, and rounds the gathered view to
the existing attention padding. The graph gathers K and V through this map.
The causal/sequence mask uses the same mapping, including empty cells inside
selected pages. Padding rows read physical row zero but are always masked;
they cannot duplicate an actual attention contribution.

The page map is a graph input, refreshed on every microbatch, including graph
reuse. Gathering uses the existing `GET_ROWS` operation followed by F16
conversion so the attention input format stays comparable with the control.
That operation temporarily produces F32 values, so copying and temporary
buffers can erase any gain from a shorter attention span. Runtime logs report
`physical_span`, `gathered_span`, and `occupied_page_rows`, making a claimed
span reduction independently checkable.

The backing KV buffers and cell allocation policy remain unchanged. This is
an experiment in mapped attention access and its interaction with request
reuse; it provides no allocation-capacity saving and does not complete a
page-based allocator/scheduler. A production paged implementation would also
need page allocation/reclamation and preferably a kernel that reads page
indices directly, avoiding the gather copies. The original paged-scheduling
requirement remains open until those semantics and their board benefit are
implemented and evaluated.

## Validation completed

The isolated host `llama-server` and backend test executable compile. The
[synthetic test](2026-09-26-page-gather-test.cpp) checks empty mappings, a
partial final page, undersized-map rejection, holes inside occupied pages,
masked padding, causal tails, 256-dimensional heads, two KV heads with grouped
query attention, and graph reuse after the occupied physical pages change.
It compares dense attention at a physical span of 1,024 with gathered
attention at 256. Both rounds had maximum absolute output error **0** on the
host. [Recorded output](../reports/raw/2026-09-25-lifecycle/page-gather-host-test.txt).
This tests the map and attention operations; it is not a full-model output or
board speed result. `git apply --check` also passed on the board's exact source.

Example test build after applying the patch and building the CPU backend:

```bash
g++ -std=c++17 -O2 /path/to/2026-09-26-page-gather-test.cpp \
  -I/path/to/checkout/src -I/path/to/checkout/ggml/include \
  -L/path/to/checkout/build/bin -lggml-cpu -lggml-base -lggml \
  -o /tmp/test-page-gather
LD_LIBRARY_PATH=/path/to/checkout/build/bin /tmp/test-page-gather
```

## Queued board gates

[The serialized script](../reports/raw/2026-09-25-lifecycle/run-lifecycle-page-gather.sh)
waits for the existing 4B KV ABBA job, creates an isolated worktree, applies the
patch, and builds with the measured SpaceMiT compiler/runtime settings. It
first runs the synthetic numerical test on X60, then 128-prompt/32-output
direct generation with gathering off/on for both 2B and 4B. Any build,
completion, or exact-token mismatch stops this experiment.

If the smoke gate passes, each model gets off/on/on/off runs at four pinned
slots with prompt lengths 128/256/512/1024, 32 output tokens, two rounds per
server, and rotated lengths in round two. Both modes use the same patched
binary, F16, unified KV, and 8k total context. Capture TTFT, aggregate rate,
RSS, exact output hashes, actual slot IDs, and logged physical/gathered spans.
Do not infer a benefit if page compaction never occurs in the measured arm.
Any speedup claim also requires accounting for output correctness and the
additional gather buffers; otherwise retain the dense control.

## Completed board result

The X60 numerical test passed. Both model smoke arms and 64 completions in
the four-slot rotated ABBA passed exact token-count and hash audits.
Gathering reduced aggregate throughput by about 2.1% for 2B and 2.9% for
4B, with a small peak-RSS increase. A negative configuration test with the
flag enabled but without unified KV failed with the patch's explicit
validation error, confirming the runtime flag is read. The default server
log level omitted span telemetry, so the campaign does not prove how many
pages were compacted in each run. This candidate remains unadopted. See the
[completed-gates report](../reports/2026-09-27-completed-gates.md).
