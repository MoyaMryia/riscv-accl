# Experiments index

[Requirements.md](../../Requirements.md) is the sole current acceptance reference.
Protocols define their own experiment conditions; they do not change project acceptance.
Use the [result index](../reports/RESULTS.md) and [gap report](../reports/2026-10-13-requirements-gap.md) for current conclusions.

Use the [documentation guide](../DOCS.md) for current work. Use the
[integration guide](../README.md) to apply a packaged patch.
For the consolidated results and the adoption decisions, use the
[submission report](../reports/SUBMISSION-REPORT.md).
The [current release](../release/README.md) pins `a990751`. The historical
`apply-patches.sh` helper targets `5ad05d8`. Use separate checkouts. Follow
the base and the patch-order instructions of each experiment.

| Experiment | Present interpretation |
| --- | --- |
| [Natural long-context answers](2026-10-21-long-context-natural.md) | [Completed](../reports/2026-10-22-long-context-natural-results.md): all 12 requests stop naturally and match independent references. Uses the existing r3 binaries and models. |
| [Fixed multi-turn v2](2026-10-21-fixed-multi-turn-v2.md) | Implements per-turn correctness and format warnings. The [gate audit](../reports/2026-10-21-local-multi-turn-gate-audit.md) preserves the prior failures. |
| [IME scalar schedule](2026-10-13-ime-scalar-schedule-r1-protocol.md) | [Completed screen](../reports/2026-10-13-k1-live-inspect-and-scalar-schedule.md): 288 exact native cases pass. All eight performance cells fail advancement. Model timing does not run. |
| [Finite fragment timing protocol R4](2026-10-12-k1-fragment-timing-r4-protocol.md) | Complete-call point estimates use a shared call loop. Same-family checks do not establish accuracy for new algorithm families. |
| [Fragment source protocol R2](2026-10-12-k1-fragment-source-r2-protocol.md) | Real Q8 payload pairs test the source workflow. Model gaps remain explicit, and all candidates remain available. |
| [K1 code fragment evaluator scope](2026-10-12-k1-code-fragment-evaluator-scope.md) | Current focus: single-thread code fragment costs and gains under declared input and cache conditions. Independent checks of new implementations remain pending. |
| [K1 CPU model plan](2026-10-12-k1-cpu-model-plan.md) | CPU model work covers instruction issue, vectors, IME, memory, multiple cores, and independent checks. The sixth state model has wide bounds and retained gain errors. |
| [Local candidate designs](2026-10-08-local-candidate-designs.md) | Proposed only. Four designs define source changes, numerical requirements, and test gates. No new board result. |
| [Fixed K32 M1 specialization](2026-10-07-ime-m1-k32.md) | [Completed negative screen](../reports/2026-10-07-ime-m1-k32-results.md): exact native and full-output checks pass. 144 operator samples fail advancement. The candidate is disabled and the model stages are skipped. |
| [Decode and FFN packing audit](2026-10-07-decode-packing-audit.md) | [Completed](../reports/2026-10-07-decode-packing-results.md): eight matched cold requests are exact and 86 artifacts are verified. Duplicate packing is only 0.024–0.035% of GEMM worker elapsed. The candidate is declined and the monitor is paused. |
| [Local clean-reference quality](2026-10-06-local-clean-reference.md) | [Completed](../reports/2026-10-06-local-clean-reference-results.md): the exact models, the clean source, and same-seed requests are verified. Usefulness is 1/6 and 5/6, with 11 natural stops and one cap. Existing errors persist. Cross-backend causality is limited. |
| [Hybrid SSM complete answers](2026-10-06-ssm-complete-answers.md) | [Completed results](../reports/2026-10-06-ssm-complete-answer-results.md): the mixed-state checks pass, with 24 natural answers and 12 identical pairs. Time is -2.92%/-2.13% and usefulness is 2/6 and 5/6. The adoption gates fail. |
| [Channels-major SSM convolution + RVV](2026-10-06-ssm-conv-rvv.md) | [Repaired screen completed](../reports/2026-10-06-ssm-conv-repaired-results.md): four arms pass 432 cases each. The 32-token graph shows large gains, but a single-token regression rejects unconditional use. The model checks and the timing are skipped, and there is no adoption. |
| [Measured memory/inference roofline](2026-10-05-k1-roofline.md) | Completed: approximately 7 GB/s and 24 matching requests. The routing gains are confirmed. See the [results](../reports/2026-10-06-k1-roofline-results.md). There is no hardware-limit claim. |
| [Original wide RVV](2026-09-26-wide-rvv-fa.md) | Superseded: its 128-byte-vector dispatcher did not activate on K1. |
| [256-bit RVV](2026-09-26-wide-rvv-vlen256.md) | Built, measured, and integrated. Optional patch 0009 is enabled with `SPINE_FA_WIDE_TILE=1` for the tested F16 KV. |
| [Windowed MTP](2026-09-26-windowed-mtp.md) | Optional patch 0010: the draft-memory savings are measured and the speed observations come from a single pair. The MTP long-code limitation remains. |
| [Context speculative gate](2026-09-26-context-spec-gate.md) | Separate proposal, no measured adoption claim. |
| [Page gathering](2026-09-26-page-gather.md) | Evaluated negatively. It is not a full paged allocation and not an adopted acceleration. |
| [Target-logit trace](2026-09-27-spec-logits-trace.md) | Completed diagnostic. The traced source is removed and the original server is rebuilt. |
| [Perfect-draft probe](2026-09-28-perfect-draft-probe.md) | x86 mechanism evidence. There is no K1 optimization and no implemented tie guard. |
| [Compact K1 layout](2026-09-30-k1-attention-layout.md) | Completed native and model pilot with small effects and no adoption. A staged fast screen follows. |
| [Fast-test method](2026-09-30-fast-test-design.md) | Implemented controller and concurrent timing. The corrected screen completed in 8.45 minutes. The model gains are below the threshold. |
| [Attention infrastructure](2026-10-02-attention-infrastructure.md) | Completed: the direct-V gains do not improve model prefill. The GEMM attribution is also completed. The staging bypass results are in the production GEMM routing experiment. |
| [Production GEMM routing](2026-10-03-gemm-routing.md) | Completed: separate prefill and decode bypass modes qualify on both models. The artifacts are verified, experimental, and opt-in. |
| [Checkpoint MTP usefulness](2026-10-03-mtp-usefulness.md) | Completed: the relative quality gates pass and the total latency falls 8.63%/15.22%. The absolute usefulness fails the shared checks and the prose slows down. Checkpoint MTP remains optional and RS is disabled. |
| [Adaptive checkpoint MTP policy](2026-10-03-adaptive-mtp-policy.md) | Implemented and state-tested in the later isolated candidate. The bounded timing is positive for code, and the useful-code checks fail. There is no default change. |
| [Adaptive MTP implementation](2026-10-04-adaptive-mtp-implementation.md) | The isolated server patch is implemented and both native state gates pass. The quality screen stopped on 2B repetition and on a 4B code failure before the timing. See the separate infrastructure screen. There is no adoption result. |
| [Adaptive MTP infrastructure screen](2026-10-05-adaptive-mtp-infrastructure.md) | Completed: 54 requests and code throughput +50.74%/+53.35%. The quality failures are retained and the candidate is unqualified. See the [results](../reports/2026-10-05-adaptive-mtp-results.md). |

Older queued-run instructions explain historical procedures. Consult the
completed reports before you repeat them. The experimental and rejected
patches remain as evidence. They are not all options in `apply-patches.sh`.
