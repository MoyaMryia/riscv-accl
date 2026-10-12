# Current documentation guide

Evidence cutoff: October 12, 2026, Asia/Singapore.
This guide records completed evidence and pending work at that cutoff.
Dated queue statements do not establish current board activity.

## Read the project report

| Document | Purpose |
| --- | --- |
| [PDF report](reports/SUBMISSION-REPORT.pdf) | Complete report with the evidence appendix |
| [TeX source](reports/SUBMISSION-REPORT.tex) | Standalone PDF source |
| [Report text](reports/SUBMISSION-REPORT.md) | Editable technical report |
| [Evidence appendix](reports/SUBMISSION-EVIDENCE.md) | Claim-to-record map, source identities, and check commands |
| [Export instructions](reports/REPORT-BUILD.md) | Document update rules and repeatable export |

## Current decisions

| Area | Status | Evidence and limit |
| --- | --- | --- |
| Pinned release | Verified; RVV attention and routing remain opt-in | [Release guide](release/README.md); [October 7 checks](reports/2026-10-07-release-verification.md): clean build, 104 native cases per arm, four complete code answers with 106 checks each |
| Long-input attention | Matched gains on 2B and 4B | [Measurement matrix](reports/2026-09-27-resumed-measures.md): replicated 2k/8k; single-pair 16k; 2B/32k feasibility without a matched control |
| Routing | Phase gains on the optimized baseline | [Routing results](reports/2026-10-03-infrastructure-research.md); [independent confirmation](reports/2026-10-06-k1-roofline-results.md); no cumulative project speedup |
| Independent later candidates | Selected workload gains; not release defaults | [Candidate review](reports/2026-10-09-local-candidate-result-rejudgment.md); 96 complete answers, 48 identical pairs, shared model errors remain |
| Combined-r1 | Stopped after one failed decode gate | [October 12 stop audit](reports/2026-10-12-combined-stop-audit.md): F versus B increases 4B/2048/65 decode time by 3.0220477%; later stages do not run |
| Dispatch revision | Local checks only | [Revision protocol](experiments/2026-10-12-combined-dispatch-r2-local-protocol.md); native and model checks pending |
| Performance evaluator V7 | Portable replay verified; point directions unreliable | [V7 audit](reports/2026-10-12-k1-model-v7.md): 9/9 group interval coverage, 9/27 point-direction agreement |
| Operator training data | First batch verified on two hosts | [Operator report](reports/2026-10-12-k1-operator-data.md): 32 configurations and 1,344 observations; calibration and independent tests unmeasured |
| Board access | Remote access failure confirmed; physical cause unknown | [Connection report](reports/2026-10-12-k1-connection-interruption.md); second-batch start unconfirmed; wait for the physical check |

The October 11 [progress snapshot](reports/2026-10-11-project-progress.md) and
[version comparison](reports/2026-10-11-original-current-comparison.md) predate the combination stop.
Use the October 12 stop audit for its later decision.
The documentation task does not resume board tests or establish automatic retries.

## Use the code and records

| Task | Guide |
| --- | --- |
| Reproduce the pinned release | [Release source, patch, and launchers](release/README.md) |
| Prepare models and apply the older patch stack | [Integration guide](README.md); [model tools](models/tools/README.md) |
| Run native and model benchmarks | [Benchmark guide](bench/README.md) |
| Use full-document cache reuse | [Local document service](serve/README.md) |
| Replay portable performance examples | [Evaluator guide](bench/qemu-screen/predictor/README.md) |
| Inspect operator data and collector limits | [Operator tools](bench/operator-data/README.md) |
| Find a dated result | [Reports index](reports/README.md) |
| Find a predeclared experiment | [Experiments index](experiments/README.md) |

The release pins official-fork `a990751` and exact measured source hashes.
The older `apply-patches.sh` helper targets `5ad05d8`.
Use separate source checkouts for these packages.
The release guide supplies the current launch commands.

## Evidence rules

1. Keep the source, model, workload, precision, thread count, and cache state with each measurement.
2. Compare only matched arms from the stated campaign.
3. Keep time reductions separate from throughput increases.
4. Keep operator results separate from full-model results.
5. Use naturally complete answers to assess complete-answer quality.
6. Keep failed gates and pending checks visible.
7. Preserve every file in `reports/raw/`.

The common inference configuration uses Q4_0 weights, F16 K/V, four workers, and batch/microbatch 32.
Principal RVV and routing results use direct decoding.
MTP long-code identity remains unresolved.
Full-vocabulary verification does not establish universal numerical identity.
The optional cloud judge supplements local answer checks; inference remains local.

## Negative results and open limits

- [SSM complete answers](reports/2026-10-06-ssm-complete-answer-results.md): exact states and 24 natural answers pass; 2.92%/2.13% gains miss adoption gates.
- [Decode and packing audit](reports/2026-10-07-decode-packing-results.md): duplicate FFN packing is 0.024–0.035% of summed worker elapsed time; no implementation follows.
- [Fixed K32 M1 screen](reports/2026-10-07-ime-m1-k32-results.md): numerical checks pass; 144 operator samples do not qualify; model stages do not run.
- [Adaptive MTP](reports/2026-10-05-adaptive-mtp-results.md): code throughput gains do not establish faster useful answers; absolute correctness and overall time gates fail.
- [Cache quality](reports/2026-09-30-chat-quality-benchmark.md): 24 complete pairs; 2B/4k needs review; no universal quality pass.
- [GPU and page checks](reports/2026-09-27-resumed-measures.md): zero transferred OpenCL layers; no measured GPU or full paged-scheduler gain.

4B/32k and 64k performance remain unmeasured.
Physical TCM placement remains unverified under the current runtime.
Sampled CPU shares and traffic references do not establish removable wall time or a hardware performance limit.
A matched initial-vendor-to-final-combination regression does not exist.
The report retains further numerical, quality, and archive limits.
