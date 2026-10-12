# Checkpoint MTP complete-answer results

Run: `mtp-quality-20261003-173915` on `musepipro-wg`. Generation completed
successfully: 24 of 24 requests in 5,976.876 seconds (1 h 39 m 37 s). All
requests stopped naturally, used complete task inputs, and passed the
cold-cache, prompt/output count, and slot checks. The 21 collected artifact
hashes are verified.

Configuration: Qwen3.5 2B/4B Q4_0, F16 KV, four threads, batch/microbatch 32,
context 6144, wide attention, and layout 0. Direct decoding against checkpoint
MTP, with draft length 3, routing 0 in both arms, and `SPINE_SPEC_RS=0`. See
the [protocol](../experiments/2026-10-03-mtp-usefulness.md).

## Complete-task latency

| Model | Direct total | MTP total | Time reduction | Identical answer pairs |
| --- | ---: | ---: | ---: | ---: |
| 2B | 884.978 s | 808.647 s | 8.63% | 4/6 |
| 4B | 2220.327 s | 1882.481 s | 15.22% | 3/6 |

The totals sum the six task responses in each arm. They exclude startup, model
loading, and hash verification. They are descriptive single-pair observations.
The output lengths differ: the faster interval-code answers are shorter and
incorrect in both arms. The total reduction is therefore not a fixed-token
kernel speedup, and not a successful-work-only speedup.

| Model | Task | Direct | MTP | Time reduction | Tokens direct/MTP |
| --- | --- | ---: | ---: | ---: | ---: |
| 2B | routes | 105.94 s | 110.57 s | -4.37% | 31/31 |
| 2B | trace | 101.97 s | 103.54 s | -1.54% | 8/8 |
| 2B | aggregation | 114.81 s | 115.72 s | -0.79% | 50/50 |
| 2B | free_windows | 311.98 s | 201.69 s | 35.35% | 1086/904 |
| 2B | unicode_runs | 146.60 s | 99.18 s | 32.35% | 508/508 |
| 2B | chinese_policy | 103.67 s | 177.94 s | -71.64% | 337/474 |
| 4B | chinese_policy | 238.38 s | 272.85 s | -14.46% | 302/296 |
| 4B | unicode_runs | 380.57 s | 288.60 s | 24.17% | 521/595 |
| 4B | free_windows | 721.16 s | 431.93 s | 40.11% | 982/814 |
| 4B | aggregation | 296.62 s | 295.17 s | 0.49% | 45/45 |
| 4B | trace | 312.31 s | 311.90 s | 0.13% | 64/64 |
| 4B | routes | 271.27 s | 282.04 s | -3.97% | 23/23 |

## Correctness and usefulness

- Routes: the required facts and the citation pass, and the answers are
  identical on both models.
- Tracing: cobalt is correct in all arms. 2B omits every requested source
  marker in both arms, and 4B includes them.
- Arithmetic: 2B returns 79 instead of 78, identically in both arms. 4B
  returns the correct 78, identically.
- Unicode code: all 106 functional checks pass in all four responses. The 4B
  MTP implementation differs from direct, but it passes the same checks.
  Latency falls 32.35% on 2B and 24.16% on 4B.
- Interval code: all four implementations fail the independent boundary
  tests. 2B direct raises IndexError, and the 2B MTP fails the touching and
  zero-length example. Both 4B implementations reject a zero-length interval,
  although the specification says to ignore it. Additional visible defects
  remain in the free-window handling.
- Chinese prose: the required fact patterns pass in all arms. Full usefulness
  depends also on the examples, the length, and unsupported claims. MTP
  increases the total latency by 71.64% on 2B and by 14.46% on 4B. Draft
  acceptance is 290/552 (52.54%) and 182/342 (53.22%).

There is no new failure in the predeclared binary fact, citation, and code
checks. But a shared failure does not mean that both answers are useful. The
absolute usefulness criteria cannot pass, because every MTP interval-code
response fails, and the 2B arithmetic is wrong.

## Cloud judge and recovery

The original collector verified and saved the board results. Then cloud
scoring stopped on an incomplete HTTP response. Scoring resumed in workstation
tmux, with bounded transport and malformed-JSON retries, and a 4096-token
judge-response budget. The original board generations, the rubric, and the
staged files remain intact. The hashes of the recovery code are recorded in
`scoring-recovery.json`. Cloud scores are supplementary. They do not override
functional failures or missing citations.

Scoring completed: all 12 pairs have both blind answer orders (24 judge
responses). Both models pass the relative quality gate. The
`candidate_useful_in_pilot` flag is false, and collector exit 2 means that a
completed review is necessary. That status is not an infrastructure failure.

| Model | Direct mean /5 | MTP mean /5 | Relative gate | Absolute usefulness |
| --- | ---: | ---: | --- | --- |
| 2B | 3.00 | 3.08 | Pass | Fail |
| 4B | 4.33 | 4.75 | Pass | Fail |

The cloud judge gave the 4B interval code 1/5 direct and 3.5/5 MTP, although
both implementations fail the executable tests. Its 2B tracing score is 5/5,
despite the missing requested citation markers in both arms. This behavior
shows why judge scores supplement the explicit checks. The overall mean
increase does not establish universally correct answers.

## Decision

Keep checkpoint MTP optional. This pilot supports a workload-specific
code-generation benefit. It demonstrates also that a different 4B Unicode
code implementation can remain correct. The pilot does not support an
enablement of MTP for all tasks: prose regresses in speed, and the complete
suite fails absolute usefulness. RS remains disabled. One pair per task and
model, and a single judge, cannot establish general semantic equivalence.

Evidence: [run manifest](raw/mtp-quality-20261003-173915/run.json),
[generation summary](raw/mtp-quality-20261003-173915/summary.json),
[2B answers](raw/mtp-quality-20261003-173915/2B-pairs.json),
[4B answers](raw/mtp-quality-20261003-173915/4B-pairs.json),
[collection receipt](raw/mtp-quality-20261003-173915/collection-receipt.json).
