# Validation priorities: long context and MTP correctness

Research date: October 3, 2026, Asia/Singapore. This is a proposed validation
plan, not a new benchmark result. It supplements the [submission report](SUBMISSION-REPORT.md).

Implementation: the [staged validation protocol](../experiments/2026-10-03-staged-validation.md)
and tmux runner implement the first bounded round. The [completed results](2026-10-03-staged-validation-results.md)
retain unsupported state cases and failed gates explicitly.

## Decision

| Check | Priority | When it is required |
| --- | --- | --- |
| Recurrent-state rollback / restore | Highest for MTP | Before enabling MTP broadly or claiming exact direct/MTP identity |
| Latest GEMM routing at 8k plus complete answers | Highest for adopting the new optimization | Before changing its default; test combined mode separately if enabling both phase policies |
| 4B actual 32k | Useful next coverage point | To claim demonstrated 32k support for both models; start with bounded feasibility |
| 2B/4B actual 64k | Conditional | To claim measured 64k support, or if the recipient explicitly requires it |

Existing matched 2k/8k RVV results and bounded 16k observations demonstrate
an infrastructure improvement without requiring every context cell. The
submission can retain explicit unmeasured cells. MTP correctness is a separate
deployment gate; the principal submitted routing/attention results use direct
decoding and do not depend on resolving it.

## Search coverage and primary sources

Google Scholar was accessed through the browser with two queries:
`RULER LongBench long context evaluation` and
`speculative decoding numerical precision batch invariance`.
Scholar surfaced LongBench v2, RULER and a speculative-decoding forensics paper.
The latter appeared under its older title, *Batch speculative decoding done
right*; the latest arXiv title was checked directly. Technical conclusions use
the following primary sources and upstream code, rather than search snippets.

| Source | Practice applicable here |
| --- | --- |
| [RULER paper](https://arxiv.org/abs/2404.06654), [code](https://github.com/NVIDIA/RULER) | Evaluate several long-context tasks, including tracing and aggregation; a successful simple needle task does not establish broad context capability. |
| [LongBench v2 paper](https://aclanthology.org/2025.acl-long.183/), [code](https://github.com/THUDM/LongBench) | Add realistic understanding/reasoning tasks. A declared length-stratified subset can be a pilot; it is not a full benchmark score. Tokenize with our model and preserve the complete selected input. |
| [Correctness Forensics for Batch Speculative Decoding](https://arxiv.org/abs/2510.22876) | Check positions, masks and cache synchronization independently of speed. The authors distinguish implementation corruption from residual floating-point divergence; aggregate text metrics can miss corruption. |
| [Original speculative-decoding paper](https://arxiv.org/abs/2211.17192) | The theoretical algorithm preserves the target distribution; this does not independently validate our finite-precision backend or state-management implementation. |
| [vLLM batch-invariance documentation](https://docs.vllm.ai/en/latest/features/batch_invariance/) | Reproducibility across batch sizes requires deliberate kernel support. Its feature currently targets NVIDIA/Intel accelerator platforms, so its environment flag is not a K1 fix. |
| [llama.cpp rollback test](https://github.com/ggml-org/llama.cpp/blob/master/tests/test-recurrent-state-rollback.cpp) | Compare replay logits after restore into fresh and already-used contexts; exercise rollback across microbatch boundaries and multiple sequences. Unsupported/skipped cases are not passes. |
| [llama.cpp issue #26695](https://github.com/ggml-org/llama.cpp/issues/26695) | Reporter reproduces full-decode rollback leaving recurrent state modified even when removal reports success. The issue is closed; that alone does not establish a fix in our fork. |
| [llama.cpp issue #29493](https://github.com/ggml-org/llama.cpp/issues/29493) | Open report describes Qwen3.5 restore-into-used-context failures. It concerns another model size/build/backend; it motivates a local reproducer rather than proving our cause. |
| [Proposed upstream PR #25004](https://github.com/ggml-org/llama.cpp/pull/25004) | Contains rollback-depth and cross-microbatch test ideas. It is open at review time, not a verified drop-in patch for the SpaceMiT source. |

## MTP: start with small, discriminating tests

Our [board trace](2026-09-27-resumed-measures.md) shows first mismatches at
generated indices 179/303 and changed top-two rankings. The [x86 perfect-draft
probe](../experiments/2026-09-28-perfect-draft-probe.md) demonstrates batch-shape
logit perturbation on another backend. These support a numerical hypothesis
but do not exclude a recurrent-state error on the board.

A read-only inspection of the tested board source on October 3 found custom
bounded `rs_idx` rollback and `split_equal` batching that keeps the trailing
snapshot tokens together. Its code differs from the upstream PR baseline.
No new correctness test or patch was executed during this research review.

Recommended sequence:

1. **Same-shape reference.** Use identical token IDs, positions, model and
   execution shape in two fresh contexts; require finite matching logits.
2. **Restore reference.** Decode a prefix, save state, advance, restore and
   replay. Compare with a context that never advanced beyond that prefix.
   Test full/partial restore only where the fork supports them, into both
   fresh and already-used contexts. Check attention KV and recurrent state.
3. **Rollback boundaries.** Cover rejection after zero/one/several accepted
   drafts, whole-last-batch removal, repeated rollback, microbatch boundaries,
   sequence isolation and end-of-generation handling. Exercise the actual
   checkpoint and RS paths separately; capture logits, not just argmax.
4. **Batch-shape isolation.** Replay the same forced direct token trajectory
   with M=1 and M>1. Compare per-token logits and top-two margins before the
   first divergence. Free-running outputs after divergence have different
   histories and cannot isolate the numerical cause.
5. **End-to-end replication.** Start with 512 outputs, enough to include the
   known mismatch positions on both models; then test varied code/prose/
   multilingual prompts and longer completed generations once the mechanism
   is understood. Separate speed measurements from diagnostic instrumentation.

If the implementation is claimed to reproduce direct greedy decoding,
token equality remains an acceptance requirement. If only comparable answer
usefulness is claimed, define task-quality checks explicitly and disclose
the differing trajectories; cloud scores alone cannot dismiss state errors.
Stochastic distribution preservation is a different claim and is not proved
by matching outputs under one seed.

The earlier proposed near-tie fallback remains unimplemented. An empirically
chosen epsilon is not a universal numerical-error bound; it cannot guarantee
direct identity on arbitrary inputs. A hybrid model also requires valid
recurrent-state restoration, not just deleting an attention KV cell.

## Long context: separate feasibility, performance and usefulness

1. **Confirm the candidate at 8k first.** Use independent paired requests on
   both models against the current optimized baseline, preserving Q4_0/F16,
   full input, four workers and batch/microbatch 32. Test mode 3 explicitly
   before reporting a combined policy. Complete-answer confirmation is separate
   from fixed-length phase timing.
2. **Run one bounded 4B/32k feasibility case.** Verify the actual tokenized
   input count, allow context space for template and output, prohibit automatic
   truncation/context shifting, and log completion, RSS, available RAM, swap,
   errors and timings. A timeout is an incomplete run within that budget, not
   proof that the model can never support 32k.
3. **Measure an effect only with a control.** If an optimization effect at
   32k is claimed, add matched baseline/candidate comparisons and repetition.
   One enabled-only request demonstrates feasibility, not acceleration.
4. **Add deterministic task checks.** Use known-answer retrieval, multi-fact
   aggregation and multi-hop tracing with evidence at different positions,
   plus realistic document/code questions. Every selected input remains full;
   asking the model to find information inside it is not preprocessing retrieval
   or prompt shortening. Predeclare the tasks and include all outcomes.
5. **Gate 64k on need and measured resources.** Advance after 32k completion,
   using observed per-chunk growth and memory headroom to set a time/RAM budget.
   The old 2B fit projected roughly 2.9 hours of cold prefill at 64k; that is an
   extrapolation from another baseline, not a measurement or a new-routing ETA.
   Do not launch a full long-context matrix just to eliminate every blank cell.

A small RULER/LongBench-inspired pilot must be labelled as such. It should
detect regressions relative to the same model baseline; low absolute accuracy
on a difficult task may be a model limitation rather than an infrastructure
regression. Record both, including truncation and naturally stopped answers.

## Submission treatment

Retain the current limitations until actual tests pass. Prioritize the
new-routing adoption checks and small rollback reproducers. Then add 4B/32k
coverage. 64k can remain future work when it is outside the required measured
claim. Research references and proposed protocols are not new board results.
