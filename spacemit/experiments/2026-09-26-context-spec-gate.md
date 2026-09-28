# Opt-in context-aware MTP gate candidate

The adjacent patch applies to the integrated official-fork checkout at `a990751` after the packaged source patches. `SPINE_SPEC_MAX_CONTEXT=N` stops starting new speculative drafts once the current slot prompt reaches `N` tokens. The target model continues ordinary decoding and verifies any draft already in flight. The default `0` leaves behavior unchanged.

This is a long-context fallback candidate, not a replacement for true windowed MTP. It does not reduce cold prefill time or the allocated KV pool. It should be built and evaluated only after the direct/MTP 12k-context benchmark establishes whether drafting loses throughput there. Compare the same GGUF, prompt, context, output length, and greedy token hashes with the default speculative server and a separately configured direct server. Check the server log for actual draft suppression; do not infer it from an environment variable alone. Repeat an A/B sequence before adopting a threshold, because long prefill and board load can dominate a short decode result.

`git apply --check` passed against the measured checkout. Build, runtime behavior, and performance are not yet verified.
