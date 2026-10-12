# Speculative settings sweep on SpaceMiT X60

> Dated campaign snapshot. The measurements apply to the stated workload and
> date. Queued/running statements below are historical. Use the
> [current guide](../DOCS.md) and the [reports index](README.md) for later
> results and for the current status.

Date: 2026-09-24. Board: `musepipro-wg`, official `spacemit-com/llama.cpp`
fork at `6562c22`, Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k. All runs used
spine-tcm in `LD_LIBRARY_PATH`, `SPINE_SPEC_RS=1`, four threads, context
8192, one slot, `-ub 32`, flash attention, `temperature=0`, seed 42, and
`cache_prompt=false`. Each setting started a fresh server. The measured rate
is server decode tokens/s, and the values are single runs, not confidence
intervals. Greedy response hashes matched within each prompt family across
all settings.

## N-gram burst length

The 160-token C++ near-copy prompt used `--spec-type ngram-mod,draft-mtp`,
n-gram lookup length 16, and MTP draft maximum 3. The table below shows the
n-gram minimum and maximum. A 32-token maximum with `-b 32` aborted the
server with `batch must be large enough to hold the sampled and draft
tokens`. The repaired benchmark runner now rejects that configuration before
launch. The runs with maxima 32 and 48 used `-b 64` and kept `-ub 32`.

| N-gram min/max | Batch | Decode tokens/s | Accepted/drafted |
| --- | ---: | ---: | ---: |
| 16/16 | 32 | 10.331 | 138/153 |
| 16/24 | 32 | 9.381 | 140/178 |
| 16/16 | 64 | 10.354 | 138/153 |
| 16/32 | 64 | 8.710 | 141/181 |
| 16/48 | 64 | 9.234 | 141/184 |
| 8/8 | 32 | 9.551 | 132/144 |
| 8/12 | 32 | 10.043 | 135/156 |
| 8/16 | 32 | 10.324 | 138/153 |

The existing 16-token cap remains the best tested setting for this prompt.
Longer bursts add rejected work. Shorter bursts need more verification
rounds. This result does not establish an optimum for other prompt shapes.

## MTP draft confidence threshold

The 128-token English, code, and Chinese prompts used MTP only, with draft
maximum 3 and batch and microbatch 32. The threshold is
`--spec-draft-p-min`. Zero is the server default.

| Threshold | English | Code | Chinese |
| ---: | ---: | ---: | ---: |
| 0 | 6.511 | 5.714 | 3.595 |
| 0.3 | 6.511 | 5.690 | 3.712 |
| 0.6 | 6.047 | 5.453 | 4.172 |
| 0.9 | 5.516 | 4.732 | 4.467 |

Higher thresholds help the low-acceptance Chinese prompt, but they slow
English and code. The Chinese case remains below the previously measured
direct-decoding rate of about 5.10 tokens/s. A single static threshold is
therefore not a general TPS gain for these prompts.

The raw JSONL records are in [`raw/`](raw/). The next experiment is an
opt-in, per-request fallback that observed draft acceptance drives, tested in
a separate official-fork worktree.
