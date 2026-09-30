# Opt-in context-aware MTP gate candidate

> Dated campaign snapshot. Measurements apply to the stated workload and date.
> Queued/running statements below are historical; use the
> [current guide](../DOCS.md) and the [experiments index](README.md) for later results and current status.

The adjacent patch applies to the integrated official-fork checkout at `a990751` after the packaged source patches. `SPINE_SPEC_MAX_CONTEXT=N` stops starting new speculative drafts once the current slot prompt reaches `N` tokens. The target model continues ordinary decoding and verifies any draft already in flight. The default `0` leaves behavior unchanged.

This is a long-context fallback candidate, not a replacement for true windowed MTP. It does not reduce cold prefill time or the allocated KV pool. It should be built and evaluated only after the direct/MTP 12k-context benchmark establishes whether drafting loses throughput there. Compare the same GGUF, prompt, context, output length, and greedy token hashes with the default speculative server and a separately configured direct server. Note that the gate itself is silent: the patch adds no log line when a draft is suppressed, so do not rely on the server log to confirm it — use the direct-server comparison above, or add a temporary log statement in `can_speculate()`. Repeat an A/B sequence before adopting a threshold, because long prefill and board load can dominate a short decode result.

`git apply --check` passed against the measured checkout. Build, runtime behavior, and performance are not yet verified.
