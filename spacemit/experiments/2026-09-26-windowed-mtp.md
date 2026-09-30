# Draft-only windowed MTP prototype

> Dated campaign snapshot. Measurements apply to the stated workload and date.
> Queued/running statements below are historical; use the
> [current guide](../DOCS.md) and the [experiments index](README.md) for later results and current status.

The adjacent patch applies after the integrated official-fork source at `a990751`. Set `SPINE_MTP_WINDOW=2048` (or another positive token count smaller than the per-slot context) when launching a Qwen3.5 MTP server. The default, with the variable unset, keeps the existing full draft history.

Qwen3.5 creates a separate attention-only KV cache for its MTP context. The patch configures **only that cache** with a standard sliding mask and a bounded cell pool: window + microbatch + 256 cells, rounded to 256 and capped at the slot context. The target's full KV cache, attention, and verification graph remain unchanged. Draft proposals may change and acceptance may fall, but target verification should preserve greedy output. The cache already supports overwriting cells outside its sliding window and uses its own mask settings when preparing attention.

For the tested 16,384-token context, 32-token microbatch, and 2,048-token window, the draft pool is 2,560 cells. Source review confirms `LLAMA_SWA_TYPE_STANDARD` masks keys when the query-key position distance reaches 2,048, and the cache can reuse those masked cells. `get_n_kv()` remains a contiguous-span calculation, but cannot exceed this reduced draft pool. The target cache still spans the full context.

The patch built on the host and K1 and completed short and 12k full-history/window runs for both Qwen3.5 GGUFs. The initial 12k comparison used separate builds; the later [same-binary controls](../reports/raw/2026-09-25-lifecycle/lifecycle-windowed-control.jsonl) removed that build difference. All measured 128-token full/window outputs matched exactly. The optional patch also passes `git apply --check` against the integrated checkout containing the RVV prefill change, but the combined build has not yet been benchmarked.

Before adoption, use an isolated board build and compare full draft history against windows such as 2k and 4k on the same 2B/4B GGUFs at 8k and 12k prompt lengths. Verify the startup log reports the draft window and smaller KV cell count, compare exact generated token hashes against direct decoding, inspect accepted drafts, RSS, TTFT, and total decode throughput, and check that the server finishes a long generation without cache-allocation or position errors. A shorter window is useful only if the saved draft attention work outweighs lost acceptance and any extra cache bookkeeping. Keep the context gate candidate separate so each intervention can be attributed.

The [selector](../bench/select-windowed-control.py) required a full 128-token completion and returned token IDs before running each same-binary control. The planned [full/window/window/full campaign](../reports/raw/2026-09-25-lifecycle/run-windowed-abba.sh) belonged to the pre-reboot queue. It is not an active job. The archived single-pair speed observations still need fresh fixed replication before a reliable speed claim.

## Completed 12k same-binary controls

Both selected full-history controls completed 128 output tokens on the
patched build and matched their 2,048-token-window counterpart's exact token
hash. The 2B full/window pair had 2,654.2/2,585.7 MiB peak RSS and
2.61/2.83 decode tok/s; 4B had 5,730.3/5,595.0 MiB and 0.77/0.89
tok/s. Windowed TTFT was lower in these single same-build comparisons, but
the arms were not interleaved and short same-build arms had no speed change.
Treat the long speed difference as provisional. The
[completed-gates report](../reports/2026-09-27-completed-gates.md) records
the exact values and remaining adoption gate. The separate 4,096-token code
soak found direct/MTP token-hash divergence in both models; that correctness
limit applies before recommending MTP for arbitrary long output.
