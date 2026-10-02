# Current documentation guide

Last status check: 2026-10-02 Asia/Singapore.
This is a dated snapshot. Read a run's `phase`, logs, and final exit status
for live progress. A queued experiment is not a measured optimization.

## Start here

| Need | Document |
| --- | --- |
| Apply patches, build, prepare models, run inference | [Integration guide](README.md) |
| Ask follow-up questions over a local document | [Cached-document workflow](serve/README.md) |
| Run and collect benchmarks | [Benchmark commands](bench/README.md) |
| Verified measurements through 16k, plus 2B 32k feasibility | [Resumed measurements](reports/2026-09-27-resumed-measures.md) |
| Matrix verification and corrected small-effect intervals | [Local analysis](reports/2026-09-28-local-verification.md) |
| Complete-answer quality protocol and completed matrix | [Chat quality benchmark](reports/2026-09-30-chat-quality-benchmark.md) |
| Compact attention layout code and completed pilot | [K1 layout experiment](experiments/2026-09-30-k1-attention-layout.md) |
| Implemented staged developer test loop | [Fast-test design](experiments/2026-09-30-fast-test-design.md) |
| Cold-prefill sampling and next bottleneck | [Profiling protocol](reports/2026-10-02-prefill-profile.md) |
| IME M4 scheduling candidates and isolated tests | [IME screen](reports/2026-10-02-ime-scheduling.md) |
| Multi-token reuse of the existing recurrent RVV step | [Recurrent screen](reports/2026-10-02-recurrent-prefill.md) |
| Other candidates and source provenance | [Code audit](reports/2026-09-30-code-optimization-audit.md) |

## Implemented and measured

- The integrated board source uses `a990751` plus the wide RVV changes.
  The packaged helper starts from official-fork `5ad05d8`; these are different
  source states. Follow the integration guide when rebuilding from scratch.
- The 256-bit RVV F16 attention path is integrated and opt-in through
  `SPINE_FA_WIDE_TILE=1`. Matched 2k/8k comparisons exist for both models;
  12k/16k comparisons have one pair per model. The optimized 2B 32k run is
  a feasibility result with no matched disabled-path control.
- Q4_0 weights, F16 KV, four threads, batch/microbatch 32, and direct decoding
  are the common configuration for the current document workflow.
- Same-process prefix reuse is measured. Changed questions can produce different
  token sequences, so cache reuse does not promise identical answers.
- The MTP long-code mismatch remains unresolved. Smaller draft lengths and RS
  rollback did not remove it; target-logit and FA-off diagnostics are complete.
  Direct decoding is the choice when agreement with direct greedy output matters.
- GPU offload was not demonstrated: OpenCL transferred zero layers, and the
  Vulkan route was dropped. Page gathering did not improve the tested workloads.
- Small M4 effects have corrected Welch intervals. Two launches per arm remain
  a limitation; the interval tool does not implement a paired-block test.

## Latest results and active work

| Work | State | Evidence boundary |
| --- | --- | --- |
| Chat quality, `document-quality-20260930-full-v2` | Completed: 24/24 pairs verified and judged | 2B/4k requires review because one question scores 2/5 in both arms. Three descriptive pilot passes; no full-matrix pass. |
| Compact layout, `k1-layout-20260930-153134` | Completed: 235 numerical cases/layout and 24 model requests pass | Q32 2k TTFT reductions: 0.89% on 2B, 1.98% on 4B. Small pilot effects; no adoption or 8k claim. |
| Fast method, `k1-fast-20261001-224957` | Completed in 8.45 minutes; inconclusive | 241 concurrent cases/layout passed; 216 operator records; Q16/Q32 model gains 0.32%/0.53%, below threshold. Longer stages skipped. |
| Prefill profile, `k1-profile-20261002-154340` | Completed in 8.51 minutes; collection recovered | Three verified IME GEMM labels: 43-44% self CPU; visible recurrent/attention: 7%/3.3%. CPU shares are not wall-time or gain estimates. |
| IME scheduling, `k1-ime-20261002-183608` | Completed in 4.20 minutes; no candidate qualified | 288 numerical cases and 256 operator arms pass. Unrolling averages +0.67%; scheduled loads regress. Model stages skipped. |
| IME scale gathering, `k1-ime-20261002-184503` | Completed in 3.98 minutes; no candidate qualified | All five variants pass 288 numerical cases; gathering regresses seven of eight operator shapes. Model stages skipped. |
| Recurrent prefill fusion, `k1-gdn-20261002-185831` | Operator timing in tmux | Isolated build and 158 attention/state/fallback numerical cases pass bit for bit. No speed claim yet. |

See the [October 1 update](reports/2026-10-01-fast-method.md) for commands,
run identities, timeout evidence and decision boundaries.

The completed quality matrix retained its original **alternating** protocol.
New quality runs default to **grouped**: one primer, six cached answers, then
six cold controls. Grouping reduces full document passes from up to twelve to
seven; its speedup has not been measured. Collection-only recovery resumes
existing records without changing board generation or its schedule.

Full model inference is local. The optional answer judge uses a cloud API;
its scores supplement facts/citations and completion checks. One- or 32-token
speed requests cannot establish answer quality. Length-capped answers cannot
pass the complete-answer quality gate.

## Next work

1. Finish the isolated recurrent prefill screen. Advance only candidates clearing
   representative operator and cold model gates; require longer-context and
   complete-answer confirmation before adoption.
2. Keep layout 0; the fast screen did not qualify either compact layout. Do not
   run an 8k layout comparison or repeat the quality matrix for this result.
3. Review the low-scoring 2B/4k cache answer separately from kernel timing.
4. K/V packing needs targeted attribution before prioritizing a shared packing
   cache; the completed IME screens do not justify enabling their variants.

## Older documents

[Reports index](reports/README.md) and [experiments index](experiments/README.md)
distinguish campaign evidence, prototypes, and designs. Dates in filenames
identify the original campaign, even when a later correction was added.
Earlier references to running jobs, queued diagnostics, and "final" results
describe that campaign's snapshot. The 2026-09-27 board reboot ended its old
queue; do not use that queue as today's plan.

Raw records are evidence. Generated `reports/raw/*/summary.md` files may
still change while collectors run. Live summaries and unfinished outputs
are not stable completed-result archives.
