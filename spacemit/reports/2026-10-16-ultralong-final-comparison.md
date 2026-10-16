# Final-build 16k and 32k capacity extension

Evidence cutoff: October 16, 2026, Asia/Singapore.

## Status and identity

Verified: all 12 requests complete with 65 output tokens and zero prompt-cache reuse.
The controller exits with status 0 after 102171.886 s, or 28.381 h.
The independent check verifies 221 receipts and 101704 memory samples.
[Verification](raw/k1-ultralong-20261016-r1/verification-v2.json) retains every request and observed range.
[Protocol](raw/k1-ultralong-20261016-r1/PROTOCOL.md) fixes the workload, order, limits, and configuration.

The final arm uses the original `k1-final-20261013-r3` production binaries.
Its server SHA-256 is `f254f174919c0a97ef34366f116705f6d22574cab4c2bfc39928c0d315b5bfbd`.
The baseline uses `5ad05d8` with the previously recorded K1 build and draft-head loader compatibility changes.
Both arms retain the same weights, compiler, runtime, Q4_0 precision, F16 cache, and direct decode.
The [ordinary-default report](2026-10-14-final-default-comparison.md) records those identities and compatibility limits.
This supplement does not rebuild the production binaries or replace the original archive.

## Capacity and workload

Actual inputs contain 16384 or 32768 complete tokens.
Allocated context is 20480 or 36864, respectively.
Only `-c` extends the final arm's capacity; no optimization flags or experiment variables select its configuration.
Effective-default records confirm four threads, batch 32, physical batch 32, one slot, F16 K/V, flash attention, and mask 3.
Server properties confirm actual capacity, one slot, and disabled draft decode for both arms.
The ordinary production default remains 12288.
These requests do not verify ordinary startup at 32k capacity.

Each model has two pairs at 16384 inputs and one pair at 32768 inputs.
A fresh server handles each request.
The input lists and 65 forced output tokens match across both arms.
This synthetic output does not measure long semantic quality.
The tests do not clear the operating-system file cache.
Server load time is outside request time.
RSS samples cover server load and the request at a nominal 1 s interval.

## Results

Each slash separates baseline and final values, in that order.
Tables show arithmetic means of per-request metrics.
Time reductions and throughput increases use different formulas.

| Model | Input | Pairs | TTFT, s | Prefill, s | Prefill, tokens/s |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2B | 16384 | 2 | 2829.646 / 1034.907 | 2829.614 / 1034.876 | 5.797 / 15.832 |
| 2B | 32768 | 1 | 10761.012 / 2983.902 | 10760.952 / 2983.845 | 3.045 / 10.982 |
| 4B | 16384 | 2 | 11256.195 / 2975.716 | 11256.164 / 2975.685 | 1.456 / 5.506 |
| 4B | 32768 | 1 | 42070.823 / 8866.022 | 42070.765 / 8865.966 | 0.779 / 3.696 |

| Model | Input | Decode, tokens/s | Request, s | Peak RSS, MiB |
| --- | ---: | ---: | ---: | ---: |
| 2B | 16384 | 1.659 / 2.914 | 2868.832 / 1057.226 | 2571.781 / 2569.617 |
| 2B | 32768 | 1.051 / 2.141 | 10822.886 / 3014.282 | 2767.641 / 2766.426 |
| 4B | 16384 | 0.490 / 1.117 | 11388.985 / 3033.905 | 5600.367 / 5600.611 |
| 4B | 32768 | 0.291 / 0.752 | 42294.220 / 8952.505 | 6117.164 / 6117.809 |

| Model | Input | TTFT reduction | Prefill gain | Decode gain |
| --- | ---: | ---: | ---: | ---: |
| 2B | 16384 | 63.43% | +173.13% | +75.59% |
| 2B | 32768 | 72.27% | +260.64% | +103.72% |
| 4B | 16384 | 73.56% | +278.29% | +128.23% |
| 4B | 32768 | 78.93% | +374.52% | +158.34% |

All observed final TTFT and decode throughput values improve within these matched shapes.
Two samples per arm do not establish a population confidence interval.
One 32k pair per model does not establish repeat stability.
The [independent record](raw/k1-ultralong-20261016-r1/verification-v2.json) preserves each sample, minima, maxima, identities, and complete configuration.

## Memory and completion limits

No request reaches the frozen memory or time limit.
The minimum sampled system availability is 11396.441 MiB, from the 4B baseline at 32768 inputs.
The largest sampled server RSS is 6117.809 MiB, from the final 4B at 32768 inputs.
These values describe this nominal 16 GB K1 board, not an 8 GB device.
RSS does not measure whole-machine memory or an instantaneous hardware peak.
The pre-launch requirement is 8 GiB available memory.
Runtime limits are 1 GiB available memory and 12 GiB server RSS.
Request limits are 8 h at 16384 inputs and 24 h at 32768 inputs.
No failed, timed-out, or interrupted request directory appears in this campaign.
Earlier failures remain unchanged in the original production archive.

Pending: long state correctness, long semantic quality, and formal fixed multi-turn acceptance.
Successful fixed-output requests cannot replace those checks.
The observed context growth still reduces throughput substantially.
This report claims measured improvement over the matched original baseline, not constant throughput as context grows.

## Evidence and repeat checks

The supplement archive is `k1-ultralong-20261016-r1.tar.gz`.
Its SHA-256 is `b3e953e2dc74731de8fc08e416055c28422d4a2415ab13649c8f4091892b034e`.
Its size is 1413591 bytes.
The archive check verifies 138 file hashes.
[Archive receipt](raw/k1-ultralong-20261016-r1/archive-receipt.json) records its identity.
The archive contains the complete board collection, fixed tools, protocol, original build receipts, and independent checks.
No model weights, vendor libraries, or credentials form part of this supplement.

Extract the supplement and enter its version directory.
Run the following command in tmux.
The output path must not exist.

```sh
python3 verify-ultralong.py \
  --board board/k1-ultralong-20261014-r1 --task . \
  --original reference-build-receipts \
  --output /tmp/k1-ultralong-new-verification.json
```

The portable replay passes against the archive's retained layout.
The original production archive remains `k1-final-20261013-r3.tar.gz`.
Its SHA-256 remains `d2adc88afcb3996047b6e925d40b0bcc0054a449f9616238f698eee1c092855a`.
