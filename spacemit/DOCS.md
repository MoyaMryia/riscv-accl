# Current documentation guide

Last status check: 2026-09-30, approximately 16:00 Asia/Singapore.
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
| Complete-answer quality protocol and partial results | [Chat quality benchmark](reports/2026-09-30-chat-quality-benchmark.md) |
| Compact attention layout code and queued tests | [K1 layout experiment](experiments/2026-09-30-k1-attention-layout.md) |
| Proposed faster developer test loop | [Fast-test design](experiments/2026-09-30-fast-test-design.md) |
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

## Active work at the status check

| Work | State | Evidence boundary |
| --- | --- | --- |
| Chat quality matrix, `document-quality-20260930-full-v2` | 2B/4k, 2B/8k and 4B/4k collected and judged; 4B/8k generation active | 18 of 24 pairs collected/judged. 2B/4k needs review; other completed configurations pass descriptive pilot gates. No full-matrix pass. |
| Compact layout, `k1-layout-20260930-153134` | Code committed and staged; board tmux waits for the quality lock | Q16/Q32 scratch spans are 96/128 KiB per worker vs 288 KiB. Native compilation, numerical gates and timing are pending; planner reservation is unchanged. |
| Faster test method | Design committed; runner not implemented | Proposed 15-30 minute screen estimate excludes build/queue time and is unmeasured. |

The active quality matrix retains its original **alternating** protocol.
New quality runs default to **grouped**: one primer, six cached answers, then
six cold controls. Collection-only recovery resumes existing records and does
not alter board generation or its schedule. Grouping reduces full document
passes from up to twelve to seven; its speedup has not been measured.

Full model inference is local. The optional answer judge uses a cloud API;
its scores supplement facts/citations and completion checks. One- or 32-token
speed requests cannot establish answer quality. Length-capped answers cannot
pass the complete-answer quality gate.

## Next work

1. Finish and audit the current quality matrix and queued layout pilot.
2. Implement concurrent operator timing and the staged fast-test controller.
3. Confirm a promising layout at 8k before adoption; retain the control when
   results are inconclusive. Do not rerun the full quality matrix per edit.
4. Profile remaining cold-prefill cost, then test eligible recurrent fusion
   and K/V packing reuse as separate changes.

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
