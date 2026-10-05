# K1 measured memory bandwidth and direct-inference reference

Run: `k1-roofline-20261005-225502`, SSH `musepipro-wg`.
Completed **October 6, 2026 at 00:01:41 Asia/Singapore**, after **66m 38s**.
Board and collector exit status: **0**. All **24/24** cold inference requests,
**150/150** native full-read scans and both separate CPU profiles completed.
The collected archive and all **150 artifact hashes** were independently
verified against the collection receipt. No further benchmark was launched.

## Memory measurements

Initialization, worker first touch and warm-up are excluded. Every source
word contributes to a checked RVV reduction. Rates count source bytes only
and use decimal GB/s. Each median includes five scans before and five after
inference. Working sets were chosen before measuring.

| Cores | 256 MiB | 1,024 MiB | 2,304 MiB |
| --- | ---: | ---: | ---: |
| 0 | 7.5505 | 7.5957 | 7.6174 |
| 0–1 | 6.5221 | 6.1318 | 6.1152 |
| 0–3, inference cluster | 7.0369 | 6.9963 | 6.9570 |
| 4–7 | 7.0542 | 7.0191 | 6.9842 |
| 0–7 | 8.2880 | 8.2691 | 8.2908 |

The predeclared inference reference uses cores 0–3 and the model-sized
buffer, rather than selecting the highest observed rate.

| Model reference | Working set | Before median GB/s | After median GB/s |
| --- | ---: | ---: | ---: |
| 2B | 1,024 MiB | 6.9883 | 7.0070 |
| 4B | 2,304 MiB | 6.9553 | 6.9930 |

The current approximately **7 GB/s** reference exceeds the historical
5.2–6 GB/s used in the previous estimate. The old 50–55 GB/s claim remains
invalid. More workers do not monotonically improve this streaming kernel;
these measurements do not establish the best model thread count.

## Model traffic accounting

| Model | Main layers | Full-attention layers | Main weight read proxy | Excluded MTP draft | F16 KV bytes per context token |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2B | 24 | 6 | 1,060,412,672 B | 109,750,272 B | 12,288 B |
| 4B | 32 | 8 | 2,369,040,384 B | 162,254,848 B | 32,768 B |

The full tied output head is counted once. A weight-only reference divides
measured streaming bandwidth by these main weight bytes. The second
reference adds one pass through F16 KV at the average context length over
the 64 generated tokens. These are **traffic proxies**, not measured DDR
traffic or attainable inference guarantees: recurrent state, activations,
repeated loads, caches and computation are not fully represented.

## Direct inference: routing mode 0 versus mode 3

All requests use the same model, prompt tokens, sampler, four workers,
batch/microbatch 32, F16 KV, wide RVV attention, layout 0, no GPU layers,
no MTP and no context shifting. Each server starts afresh and reports zero
prompt-cache reuse. There are three alternating-order matched repetitions
per model/context. Exactly 64 output tokens are generated with EOS ignored.
Every matched group has identical output token IDs and text hashes.

| Model | Prompt tokens | Route 0 decode tok/s | Route 3 decode tok/s | Median paired throughput gain | Weight-only reference tok/s | + one KV pass reference tok/s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2B | 256 | 3.793 | 4.480 | **18.01%** | 6.598 | 6.576 |
| 2B | 2,048 | 3.307 | 3.832 | **15.47%** | 6.598 | 6.442 |
| 4B | 256 | 1.480 | 2.058 | **38.70%** | 2.937 | 2.925 |
| 4B | 2,048 | 1.221 | 1.619 | **32.36%** | 2.937 | 2.855 |

Rates in the table are arm medians. Paired gains are medians of the three
within-repeat rate ratios, so they need not equal the ratio of arm medians.
Mode 0 is the same validated routing library with its staging bypass
disabled; mode 3 enables bypass for both prefill and single-token work.
These gains are a fresh confirmation of an existing optimization, not an
additional improvement to multiply by earlier routing gains.

| Model | Prompt tokens | Route 0 prefill tok/s | Route 3 prefill tok/s | Route 0 TTFT | Route 3 TTFT |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2B | 256 | 23.144 | 24.666 | 11.065 s | 10.383 s |
| 2B | 2,048 | 22.150 | 23.563 | 92.465 s | 86.921 s |
| 4B | 256 | 9.020 | 9.707 | 28.385 s | 26.378 s |
| 4B | 2,048 | 8.531 | 9.200 | 240.069 s | 222.605 s |

At 256 prompt tokens, optimized decode reaches about **68%/70%** of the
2B/4B weight-only streaming reference. At 2k it reaches **58%/55%**.
The differences do not prove removable overhead or identify a bottleneck.
In particular, the single-pass KV estimate alone does not explain all of
the context-dependent slowdown.

The datasheet's 32-bit, 2,666 MT/s interface gives a raw 10.664 GB/s bus
peak and weight-only references of **10.06/4.50 tok/s**. Actual board DDR
frequency was not established. These raw figures exclude bus overhead
and model work. [K1 datasheet](https://github.com/spacemit-com/docs-chip/blob/main/en/key_stone/k1/k1_docs/k1_ds.md)

## Optimized 2k prefill profiles

Both separate one-output-token profiles completed, with **86,843/220,668**
samples for 2B/4B and no reported lost samples. Their timings do not enter
the paired throughput comparisons.

| Visible self CPU work | 2B | 4B |
| --- | ---: | ---: |
| `BLOCK_INNER_LOOP435` + `BLOCK_COUNTK_LOOP435` | 42.73% | 44.20% |
| SPERT `sync_impl` | 20.02% | 20.04% |
| SSM convolution | 6.08% | 5.12% |
| Gated delta net | 5.13% | 5.48% |
| F32 vector dot | 4.90% | 5.11% |
| Visible attention stack group | 3.39% | 3.65% |

The generic stack classifier misses assembly labels, so its near-zero
"matmul visible" category must not be interpreted as negligible matrix
work. The assembly self samples above remain visible. These are sampled
user CPU shares, not wall-time shares, and this is a **prefill** profile;
it does not identify the direct-decode bottleneck or imply a 20% saving
from removing synchronization.

## Interpretation and next work

The current board has a higher streaming reference than the earlier
estimate assumed. We have **not demonstrated the hardware limit**.
The present optimized short decode is 4.48/2.06 tok/s, with lower rates
at 2k. Further work should first attribute decode time and memory stalls
under the same routing mode, then test activation-packing reuse and
runtime dispatch changes one at a time. Eight-core streaming throughput
does not justify an eight-thread IME configuration; the second cluster
does not provide the same IME capability.

This run measures capped synthetic infrastructure throughput. It adds
no complete-answer quality evidence, long-context qualification, MTP
qualification or production-default change. Three repeats support this
bounded engineering comparison, not general significance or a universal
speedup. The scheduled follow-up is paused after the final report.

## Evidence

- [Generated summary](raw/k1-roofline-20261005-225502/summary.md)
- [Machine-readable results](raw/k1-roofline-20261005-225502/summary.json)
- [Memory scans](raw/k1-roofline-20261005-225502/memory-results.json)
- [Timing records](raw/k1-roofline-20261005-225502/timing-results.json)
- [GGUF traffic audit](raw/k1-roofline-20261005-225502/model-traffic.json)
- [Runtime provenance](raw/k1-roofline-20261005-225502/provenance.json)
- [Collection receipt](raw/k1-roofline-20261005-225502/collection-receipt.json)
- [Protocol and recovery command](../experiments/2026-10-05-k1-roofline.md)
