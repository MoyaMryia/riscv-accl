# Hybrid SSM complete-answer results — October 6, 2026

Status: **completed; the candidate is not qualified for adoption**. Run
`k1-ssm-quality-20261006-131234` on SSH `musepipro-wg`, dispatched at 13:12
UTC+8. The board execution took **1 h 34 min 40 s**, and it included the build,
the numerical, state, and operator gates, and the generation. All 24 responses
stopped naturally, and none hit the output guard. The cloud scoring completed
locally. The production defaults remain unchanged.

The candidate selects the channels-major RVV convolution graph for
per-sequence microbatches of at least 32 tokens. It selects the original graph
below 32 tokens. The persistent history retains its original time-major
format. The control uses the same isolated build, with mode 0, route 3, and
wide RVV attention. Both arms use full, cold prompts, four workers, Q4_0
weights, F16 K/V, context 6144, batch/microbatch 32, deterministic direct
inference, and MTP off. No document retrieval and no prompt reduction was
introduced.

## Completion and evidence

The board, collection, and collector/scorer exit statuses are all **0**. The
board tmux session ended. The archive checksum, the exact unique file list,
every archived and extracted artifact hash, and all staged source hashes
passed the verification. The receipt covers **114 board artifacts**. The local
scorer outputs are additional files. We recorded their hashes and the 12
judgment-input fingerprints, with two presentation orders each, separately.
The frozen board summary says that the judging is pending, because the judging
occurs after the collection. The separate final quality summary records that
the scoring is complete.

- [Protocol](../experiments/2026-10-06-ssm-complete-answers.md)
- [Board summary](raw/k1-ssm-quality-20261006-131234/summary.json),
  [final quality summary](raw/k1-ssm-quality-20261006-131234/ssm-quality-summary.json)
- [Collection receipt](raw/k1-ssm-quality-20261006-131234/collection-receipt.json),
  [independent completion verification](raw/k1-ssm-quality-20261006-131234/completion-verification.json)
- [Pinned build/source provenance](raw/k1-ssm-quality-20261006-131234/run.json)

## Graph, state and operator qualification

The original, control, and hybrid arms each pass **432 native graph cases**,
with identical output and history dump SHA-256
`7e154f0a52c2475581a62a64f549a17c7d342d46c55dae7adf05d09c05001c69`. Four
additional 31/32-token boundary cases cover both real channel counts, two
sequences, and padded projection inputs. There are no numerical failures.

Both models pass **16 exact full-vocabulary logit comparisons each**, with the
mixed chunks **32, 1, 31, 32**, the reset and repeat, and the RS=0/3 reference
fallback. The activation logs confirm RVV at 32 tokens, and the original path
for decode and partial tails. This evidence qualifies the RS reference
fallback. It does not qualify RS rollback. The immutable baseline and source
checks pass.

The 48 warm graph samples include the concatenation, the history conversion,
and the copies. A lower time is positive in this table:

| Shape | One-token time reduction | 32-token time reduction |
| --- | ---: | ---: |
| 2B | -0.67% | 73.61% |
| 4B | 0.70% | 79.02% |

The operator gate passes: the large batches improve beyond the declared
benefit/control-spread threshold, and the reference single-token path shows no
clear regression. These timings are warm graph timings. They are not
full-model or useful-answer speedups.

## Complete-answer latency and quality

Useful means that the required facts and citations and the held-out code checks
pass. It means also a cloud score of at least 4/5. The scores use
`mimo-v2.6-flash`, and a judge scored each pair in both presentation orders.
All **12 paired answers are text-identical**, with identical output lengths
and no measured candidate quality regression. Identical incorrect text remains
a failed useful answer.

| Model | Total control → hybrid answer time | Time reduction | Useful control → hybrid | Mean score control → hybrid |
| --- | ---: | ---: | ---: | ---: |
| 2B | 777.534 → 754.864 s | 2.92% | 2/6 → 2/6 | 3.17 → 3.17/5 |
| 4B | 1767.333 → 1729.709 s | 2.13% | 5/6 → 5/6 | 4.50 → 4.50/5 |

These totals include all completed tasks, and they include the incorrect
answers. On the subset that is useful in both arms, the total latency fell
**3.003% for 2B (2 pairs)** and **2.968% for 4B (5 pairs)**. This retrospective
subset does not replace the declared all-task gate, and it does not establish a
general useful-answer speedup.

### Per-task complete-answer results

The timings and the scores below are control → hybrid. Every row stopped
naturally in both arms.

| Model/task | Tokens each | Answer latency, s | TTFT, s | Time reduction | Score /5 | Useful both |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| 2B/routes | 31 | 99.902 → 93.188 | 91.850 → 85.123 | 6.72% | 5 → 5 | Yes |
| 2B/trace | 8 | 95.155 → 87.209 | 93.264 → 85.318 | 8.35% | 5 → 5 | No |
| 2B/aggregation | 50 | 106.269 → 98.673 | 93.115 → 85.543 | 7.15% | 0 → 0 | No |
| 2B/free_windows | 1086 | 264.440 → 264.541 | 7.441 → 7.062 | -0.04% | 1 → 1 | No |
| 2B/unicode_runs | 508 | 123.743 → 123.742 | 7.157 → 6.795 | 0.00% | 5 → 5 | Yes |
| 2B/chinese_policy | 337 | 88.025 → 87.511 | 10.658 → 9.865 | 0.58% | 3 → 3 | No |
| 4B/routes | 23 | 248.415 → 238.163 | 234.426 → 223.981 | 4.13% | 5 → 5 | Yes |
| 4B/trace | 64 | 277.022 → 265.601 | 236.878 → 224.952 | 4.12% | 5 → 5 | Yes |
| 4B/aggregation | 45 | 265.058 → 254.052 | 237.082 → 225.694 | 4.15% | 5 → 5 | Yes |
| 4B/free_windows | 982 | 524.579 → 523.839 | 18.740 → 18.251 | 0.14% | 2 → 2 | No |
| 4B/unicode_runs | 521 | 276.194 → 274.132 | 18.155 → 17.193 | 0.75% | 5 → 5 | Yes |
| 4B/chinese_policy | 302 | 176.065 → 173.922 | 26.790 → 25.173 | 1.22% | 5 → 5 | Yes |

### Phase measurements

The rates divide the phase token count by the measured phase time. The
aggregate rates use the summed counts and time. The rates exclude the server
startup, the build, the validation, and the cloud scoring. The per-task phase
rates are shown separately, because the prompt and output lengths differ.

| Model/task | Prefill tokens/s control → hybrid | Decode tokens/s control → hybrid |
| --- | ---: | ---: |
| 2B/routes | 23.20 → 25.04 | 3.85 → 3.85 |
| 2B/trace | 22.94 → 25.08 | 4.24 → 4.24 |
| 2B/aggregation | 22.90 → 24.97 | 3.80 → 3.81 |
| 2B/free_windows | 23.88 → 25.13 | 4.23 → 4.22 |
| 2B/unicode_runs | 23.69 → 24.92 | 4.36 → 4.34 |
| 2B/chinese_policy | 23.85 → 25.45 | 4.36 → 4.34 |
| 2B/aggregate | 23.08 → 25.04 | 4.26 → 4.25 |
| 4B/routes | 9.08 → 9.50 | 1.64 → 1.62 |
| 4B/trace | 9.02 → 9.50 | 1.59 → 1.57 |
| 4B/aggregation | 8.98 → 9.45 | 1.61 → 1.59 |
| 4B/free_windows | 9.36 → 9.59 | 1.94 → 1.94 |
| 4B/unicode_runs | 9.20 → 9.71 | 2.02 → 2.03 |
| 4B/chinese_policy | 9.40 → 9.87 | 2.02 → 2.03 |
| 4B/aggregate | 9.05 → 9.51 | 1.95 → 1.95 |

The summed prefill time falls **7.86% for 2B** (302.012 → 278.271 s) and
**4.77% for 4B** (769.898 → 733.154 s). The summed decode time rises 0.23% for
2B (474.034 → 475.143 s), and it falls 0.08% for 4B (995.248 → 994.451 s). The
phase data suggest why the large convolution graph gain produces a small
complete-answer gain: other prefill work remains, and the longer code and prose
spend most of their time in the reference decode path. We infer no CPU-share and
no hardware-bandwidth attribution from these timings.

## Shared task failures and a passing answer

- **2B trace:** the cobalt answer is correct, but it omits all the required
  S2/S4/S6 citations. The judge nevertheless gives 5/5. The deterministic
  citation checks correctly reject the usefulness. This result is a concrete
  limit of model-only grading.
- **2B aggregation:** the required total is wrong, and the score is 0/5. The
  source citations pass.
- **Free-window code, both models:** 2B fails with
  `IndexError: list index out of range`. 4B rejects a zero-length interval with
  `ValueError: Interval (8, 8) has start >= end.`. The scores are 1/5 and 2/5.
- **2B Chinese policy:** the coarse fact checks pass, but the cloud grades are
  3/5. The judge cited incorrect date and shipping inferences, and omissions.
  We preserve these judge findings. A cloud score is an assessment, not an
  independent proof.
- **Unicode run codec, both models:** the 106 held-out functional checks pass,
  and both arms receive 5/5. All the other 4B tasks pass the declared
  usefulness checks.

These failures occur identically in the control and the hybrid arm. They are
genuine baseline quality outcomes. They are not build or transport failures to
repair by a restart of the experiment. There are no candidate-only
regressions, no truncations, and no skipped qualification stages.

The
[complete saved 4B Unicode run codec answer](2026-10-06-ssm-useful-answer-example.md)
contains working `encode_runs` and `decode_runs` functions, including the input
validation. The answer passed 106 checks, and it received 5/5 in both judge
orders. That artifact displays the unmodified generated code. We did not repair
the code to pass.

## Decision and limits

The candidate passes the graph, state, operator, and relative-quality gates. It
fails the declared **greater-than-3% all-task latency gate** on both models,
and it fails the absolute **6/6 useful-answer requirement**. The final
`candidate_qualified=false` value is a completed measured rejection. It is not
a technical failure. Keep the implementation opt-in. No production-default
change and no automatic rerun is necessary. The 30-minute monitor is paused,
after the completion.

This experiment has one matched pair per task and model. The results are
descriptive. They include no significance claim, no statistical noninferiority
claim, and no universal identity claim. They establish neither general model
correctness nor a reached K1 hardware limit. Further infrastructure work can
target the shared activation packing and the phase-specific decode attribution,
under separate protocols.
