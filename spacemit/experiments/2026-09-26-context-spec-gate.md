# Opt-in context-aware MTP gate candidate

> Dated campaign snapshot. The measurements apply to the stated workload and date.
> Queued and running statements below are historical. Use the
> [current guide](../DOCS.md) and the [experiments index](README.md) for the later results and the current status.

The adjacent patch applies to the integrated official-fork checkout at `a990751` after the packaged source patches. `SPINE_SPEC_MAX_CONTEXT=N` stops new speculative drafts when the current slot prompt reaches `N` tokens. The target model continues ordinary decoding and verifies any draft already in flight. The default `0` leaves the behavior unchanged.

This is a long-context fallback candidate, not a replacement for true windowed MTP. It does not reduce cold prefill time or the allocated KV pool. Build and evaluate this candidate only after the direct/MTP 12k-context benchmark shows whether drafting loses throughput there. Compare the same GGUF, prompt, context, output length, and greedy token hashes. Use the default speculative server and a separately configured direct server. The gate itself is silent. The patch adds no log line when a draft is suppressed. Do not rely on the server log to confirm the suppression. Use the direct-server comparison above, or add a temporary log statement in `can_speculate()`. Repeat an A/B sequence before you adopt a threshold, because a long prefill and the board load can dominate a short decode result.

`git apply --check` passed against the measured checkout. The build, the runtime behavior, and the performance are not yet verified.
