# Experiments index

Use the [documentation guide](../DOCS.md) for current work and the
[integration guide](../README.md) for packaged patch application.
For the consolidated results and adoption decisions, use the
[submission report](../reports/SUBMISSION-REPORT.md).
The [current release](../release/README.md) pins `a990751`. The historical
`apply-patches.sh` helper targets `5ad05d8`; use separate checkouts and follow
each experiment's base and patch-order instructions.

| Experiment | Present interpretation |
| --- | --- |
| [Fixed K32 M1 specialization](2026-10-07-ime-m1-k32.md) | [Completed negative screen](../reports/2026-10-07-ime-m1-k32-results.md): exact native/full-output checks pass; 144 operator samples fail advancement, candidate disabled and model stages skipped. |
| [Decode and FFN packing audit](2026-10-07-decode-packing-audit.md) | [Completed](../reports/2026-10-07-decode-packing-results.md): eight exact matched cold requests, 86 artifacts verified; duplicate packing is only 0.024–0.035% of GEMM worker elapsed, candidate declined; monitor paused. |
| [Local clean-reference quality](2026-10-06-local-clean-reference.md) | [Completed](../reports/2026-10-06-local-clean-reference-results.md): exact models/clean source and same-seed requests verified; useful 1/6 and 5/6, 11 natural stops/one cap; existing errors persist; cross-backend causality limited. |
| [Hybrid SSM complete answers](2026-10-06-ssm-complete-answers.md) | [Completed results](../reports/2026-10-06-ssm-complete-answer-results.md): mixed-state checks pass, 24 natural answers and 12 identical pairs; time -2.92%/-2.13%, usefulness 2/6 and 5/6; adoption gates fail. |
| [Channels-major SSM convolution + RVV](2026-10-06-ssm-conv-rvv.md) | [Repaired screen completed](../reports/2026-10-06-ssm-conv-repaired-results.md): four arms pass 432 cases each; large 32-token graph gains but single-token regression rejects unconditional use; model checks/timing skipped, no adoption. |
| [Measured memory/inference roofline](2026-10-05-k1-roofline.md) | Completed: approximately 7 GB/s, 24 matching requests, routing gains confirmed; [results](../reports/2026-10-06-k1-roofline-results.md); no hardware-limit claim |
| [Original wide RVV](2026-09-26-wide-rvv-fa.md) | Superseded: its 128-byte-vector dispatcher did not activate on K1 |
| [256-bit RVV](2026-09-26-wide-rvv-vlen256.md) | Built, measured and integrated; optional patch 0009, enabled with `SPINE_FA_WIDE_TILE=1` for tested F16 KV |
| [Windowed MTP](2026-09-26-windowed-mtp.md) | Optional patch 0010; measured draft-memory savings, single-pair speed observations; MTP long-code limitation remains |
| [Context speculative gate](2026-09-26-context-spec-gate.md) | Separate proposal, no measured adoption claim |
| [Page gathering](2026-09-26-page-gather.md) | Evaluated negatively; not full paged allocation or adopted acceleration |
| [Target-logit trace](2026-09-27-spec-logits-trace.md) | Completed diagnostic; traced source removed and original server rebuilt |
| [Perfect-draft probe](2026-09-28-perfect-draft-probe.md) | x86 mechanism evidence; no K1 optimization or implemented tie guard |
| [Compact K1 layout](2026-09-30-k1-attention-layout.md) | Completed native/model pilot; small effects, no adoption; staged fast screen follows |
| [Fast-test method](2026-09-30-fast-test-design.md) | Implemented controller and concurrent timing; corrected screen completed in 8.45 minutes, model gains below threshold |
| [Attention infrastructure](2026-10-02-attention-infrastructure.md) | Completed: direct-V gains do not improve model prefill. GEMM attribution also completed; staging bypass results are in the production GEMM routing experiment. |
| [Production GEMM routing](2026-10-03-gemm-routing.md) | Completed: separate prefill/decode bypass modes qualify on both models; artifacts verified, experimental and opt-in. |
| [Checkpoint MTP usefulness](2026-10-03-mtp-usefulness.md) | Completed: relative quality gates pass; total latency falls 8.63%/15.22%. Absolute usefulness fails shared checks and prose slows down. Checkpoint MTP remains optional; RS disabled. |
| [Adaptive checkpoint MTP policy](2026-10-03-adaptive-mtp-policy.md) | Implemented and state-tested in the later isolated candidate; bounded timing is positive for code, useful-code checks fail. No default change. |
| [Adaptive MTP implementation](2026-10-04-adaptive-mtp-implementation.md) | Isolated server patch implemented; both native state gates passed. Quality screen stopped on 2B repetition and 4B code failure before timing; see the separate infrastructure screen. No adoption result. |
| [Adaptive MTP infrastructure screen](2026-10-05-adaptive-mtp-infrastructure.md) | Completed: 54 requests, code throughput +50.74%/+53.35%, quality failures retained, candidate unqualified; [results](../reports/2026-10-05-adaptive-mtp-results.md). |

Older queued-run instructions explain historical procedures. Consult completed
reports before repeating them. Experimental and rejected patches remain as
evidence; they are not all options in `apply-patches.sh`.
