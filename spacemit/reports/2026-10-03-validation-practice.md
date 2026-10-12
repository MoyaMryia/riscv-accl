# Validation priorities: long context and MTP correctness

Research date: October 3, 2026, Asia/Singapore. This document is a proposed
validation plan, not a new benchmark result. It supplements the
[submission report](SUBMISSION-REPORT.md).

Implementation: the
[staged validation protocol](../experiments/2026-10-03-staged-validation.md)
and the tmux runner implement the first bounded round. The
[completed results](2026-10-03-staged-validation-results.md) retain the
unsupported state cases and the failed gates explicitly.

## Decision

| Check | Priority | When it is required |
| --- | --- | --- |
| Recurrent-state rollback / restore | Highest for MTP | Before an enablement of MTP broadly, or a claim of exact direct/MTP identity |
| Latest GEMM routing at 8k plus complete answers | Highest for the adoption of the new optimization | Before a change of its default; test the combined mode separately, if you enable both phase policies |
| 4B actual 32k | Useful next coverage point | To claim demonstrated 32k support for both models; start with bounded feasibility |
| 2B/4B actual 64k | Conditional | To claim measured 64k support, or if the recipient requires it explicitly |

The existing matched 2k/8k RVV results and the bounded 16k observations
demonstrate an infrastructure improvement, without a requirement for every
context cell. The submission can retain explicit unmeasured cells. MTP
correctness is a separate deployment gate. The principal submitted routing and
attention results use direct decoding, and they do not depend on its
resolution.

## Search coverage and primary sources

We accessed Google Scholar through the browser, with two queries:
`RULER LongBench long context evaluation` and
`speculative decoding numerical precision batch invariance`. Scholar surfaced
LongBench v2, RULER, and a speculative-decoding forensics paper. The last
paper appeared under its older title, *Batch speculative decoding done
right*. We checked the latest arXiv title directly. The technical conclusions
use the following primary sources and upstream code, rather than search
snippets.

| Source | Practice applicable here |
| --- | --- |
| [RULER paper](https://arxiv.org/abs/2404.06654), [code](https://github.com/NVIDIA/RULER) | Evaluate several long-context tasks, including tracing and aggregation. A successful simple needle task does not establish broad context capability. |
| [LongBench v2 paper](https://aclanthology.org/2025.acl-long.183/), [code](https://github.com/THUDM/LongBench) | Add realistic understanding and reasoning tasks. A declared length-stratified subset can be a pilot. It is not a full benchmark score. Tokenize with our model, and preserve the complete selected input. |
| [Correctness Forensics for Batch Speculative Decoding](https://arxiv.org/abs/2510.22876) | Check positions, masks, and cache synchronization independently of speed. The authors distinguish implementation corruption from residual floating-point divergence. Aggregate text metrics can miss corruption. |
| [Original speculative-decoding paper](https://arxiv.org/abs/2211.17192) | The theoretical algorithm preserves the target distribution. That theory does not independently validate our finite-precision backend or our state-management implementation. |
| [vLLM batch-invariance documentation](https://docs.vllm.ai/en/latest/features/batch_invariance/) | Reproducibility across batch sizes requires deliberate kernel support. That feature currently targets NVIDIA/Intel accelerator platforms, so its environment flag is not a K1 fix. |
| [llama.cpp rollback test](https://github.com/ggml-org/llama.cpp/blob/master/tests/test-recurrent-state-rollback.cpp) | Compare replay logits after a restore into fresh and already-used contexts. Exercise rollback across microbatch boundaries and across multiple sequences. Unsupported and skipped cases are not passes. |
| [llama.cpp issue #26695](https://github.com/ggml-org/llama.cpp/issues/26695) | The reporter reproduces a full-decode rollback that leaves recurrent state modified, even when the removal reports success. The issue is closed. That closure alone does not establish a fix in our fork. |
| [llama.cpp issue #29493](https://github.com/ggml-org/llama.cpp/issues/29493) | An open report describes Qwen3.5 restore-into-used-context failures. It concerns another model size, build, and backend. It motivates a local reproducer, and it does not prove our cause. |
| [Proposed upstream PR #25004](https://github.com/ggml-org/llama.cpp/pull/25004) | It contains rollback-depth and cross-microbatch test ideas. It was open at review time, and it is not a verified drop-in patch for the SpaceMiT source. |

## MTP: start with small, discriminating tests

Our [board trace](2026-09-27-resumed-measures.md) shows first mismatches at
generated indices 179 and 303, and changed top-two rankings. The
[x86 perfect-draft probe](../experiments/2026-09-28-perfect-draft-probe.md)
demonstrates batch-shape logit perturbation on another backend. These results
support a numerical hypothesis, but they do not exclude a recurrent-state
error on the board.

A read-only inspection of the tested board source on October 3 found custom
bounded `rs_idx` rollback and `split_equal` batching. That batching keeps the
trailing snapshot tokens together, and the code differs from the upstream PR
baseline. We executed no new correctness test and no patch during this
research review.

Recommended sequence:

1. **Same-shape reference.** Use identical token IDs, positions, model, and
   execution shape in two fresh contexts. Require finite matching logits.
2. **Restore reference.** Decode a prefix, save the state, advance, restore,
   and replay. Compare the result with a context that never advanced beyond
   that prefix. Test full and partial restore only where the fork supports
   them, and test both fresh and already-used contexts. Check the attention KV
   and the recurrent state.
3. **Rollback boundaries.** Cover a rejection after zero, one, and several
   accepted drafts. Cover a whole-last-batch removal, repeated rollback,
   microbatch boundaries, sequence isolation, and end-of-generation handling.
   Exercise the actual checkpoint and RS paths separately, and capture logits,
   not only the argmax.
4. **Batch-shape isolation.** Replay the same forced direct token trajectory
   with M=1 and M>1. Compare the per-token logits and the top-two margins
   before the first divergence. Free-running outputs after the divergence have
   different histories, and they cannot isolate the numerical cause.
5. **End-to-end replication.** Start with 512 outputs, which is enough to
   include the known mismatch positions on both models. Then test varied
   code, prose, and multilingual prompts, and longer completed generations,
   once the mechanism is understood. Separate the speed measurements from the
   diagnostic instrumentation.

If we claim that the implementation reproduces direct greedy decoding, token
equality remains an acceptance requirement. If we claim only comparable answer
usefulness, define the task-quality checks explicitly, and disclose the
differing trajectories. Cloud scores alone cannot dismiss state errors.
Stochastic distribution preservation is a different claim. Matching outputs
under one seed does not prove it.

The earlier proposed near-tie fallback remains unimplemented. An empirically
chosen epsilon is not a universal numerical-error bound. It cannot guarantee
direct identity on arbitrary inputs. A hybrid model requires also valid
recurrent-state restoration, not only a deletion of an attention KV cell.

## Long context: separate feasibility, performance and usefulness

1. **Confirm the candidate at 8k first.** Use independent paired requests on
   both models, against the current optimized baseline. Preserve Q4_0/F16, the
   full input, four workers, and batch/microbatch 32. Test mode 3 explicitly,
   before you report a combined policy. Complete-answer confirmation is
   separate from fixed-length phase timing.
2. **Run one bounded 4B/32k feasibility case.** Verify the actual tokenized
   input count. Allow context space for the template and the output. Prohibit
   automatic truncation and context shifting. Log completion, RSS, available
   RAM, swap, errors, and timings. A timeout is an incomplete run inside that
   budget. It is not proof that the model can never support 32k.
3. **Measure an effect only with a control.** If you claim an optimization
   effect at 32k, add matched baseline and candidate comparisons, and add
   repetition. One enabled-only request demonstrates feasibility, not
   acceleration.
4. **Add deterministic task checks.** Use known-answer retrieval, multi-fact
   aggregation, and multi-hop tracing, with evidence at different positions.
   Add also realistic document and code questions. Every selected input
   remains full. A task that asks the model to find information inside the
   input is not preprocessing retrieval and not prompt shortening. Predeclare
   the tasks, and include all outcomes.
5. **Gate 64k on need and on measured resources.** Advance after the 32k
   completion. Use the observed per-chunk growth and the memory headroom to set
   a time and RAM budget. The old 2B fit projected roughly 2.9 hours of cold
   prefill at 64k. That projection is an extrapolation from another baseline.
   It is not a measurement and not a new-routing ETA. Do not launch a full
   long-context matrix only to eliminate every blank cell.

A small RULER/LongBench-inspired pilot must carry that label. It must detect
regressions relative to the same model baseline. A low absolute accuracy on a
difficult task can be a model limitation rather than an infrastructure
regression. Record both, including the truncation and the naturally stopped
answers.

## Submission treatment

Retain the current limitations until the actual tests pass. Prioritize the
new-routing adoption checks and the small rollback reproducers. Then add the
4B/32k coverage. 64k can remain future work, while it is outside the required
measured claim. Research references and proposed protocols are not new board
results.
