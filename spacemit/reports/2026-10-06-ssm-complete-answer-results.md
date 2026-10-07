# Hybrid SSM complete-answer results — October 6, 2026

Status: **completed; candidate not qualified for adoption**. Run `k1-ssm-quality-20261006-131234` on SSH `musepipro-wg`, dispatched at 13:12 UTC+8. Board execution took **1 h 34 min 40 s**, including build, numerical/state/operator gates and generation. All 24 responses stopped naturally; none hit the output guard. Cloud scoring completed locally. Production defaults remain unchanged.

The candidate selects the channels-major RVV convolution graph for per-sequence microbatches of at least 32 tokens and the original graph below 32. Persistent history retains its original time-major format. The control uses the same isolated build with mode 0, route 3 and wide RVV attention. Both use full, cold prompts, four workers, Q4_0 weights, F16 K/V, context 6144, batch/microbatch 32, deterministic direct inference and MTP off. No document retrieval or prompt reduction was introduced.

## Completion and evidence

Board, collection and collector/scorer exit statuses are all **0**. The board tmux session ended. The archive checksum, exact unique file list, every archived and extracted artifact hash and all staged source hashes passed verification. The receipt covers **114 board artifacts**. The local scorer outputs are additional files; their hashes and 12 judgment-input fingerprints, with two presentation orders each, are recorded separately. The frozen board summary says judging pending because judging occurs after collection; the separate final quality summary records scoring completed.

- [Protocol](../experiments/2026-10-06-ssm-complete-answers.md)
- [Board summary](raw/k1-ssm-quality-20261006-131234/summary.json), [final quality summary](raw/k1-ssm-quality-20261006-131234/ssm-quality-summary.json)
- [Collection receipt](raw/k1-ssm-quality-20261006-131234/collection-receipt.json), [independent completion verification](raw/k1-ssm-quality-20261006-131234/completion-verification.json)
- [Pinned build/source provenance](raw/k1-ssm-quality-20261006-131234/run.json)

## Graph, state and operator qualification

Original, control and hybrid each pass **432 native graph cases**, with identical output/history dump SHA-256 `7e154f0a52c2475581a62a64f549a17c7d342d46c55dae7adf05d09c05001c69`. Four additional 31/32-token boundary cases cover both real channel counts, two sequences and padded projection inputs. There are no numerical failures.

Both models pass **16 exact full-vocabulary logit comparisons each**, with mixed chunks **32, 1, 31, 32**, reset/repeat and RS=0/3 reference fallback. Activation logs confirm RVV at 32 and the original path for decode and partial tails. This qualifies RS reference fallback; it does not qualify RS rollback. Immutable baseline/source checks pass.

The 48 warm graph samples include concatenation, history conversion and copies. Lower time is positive in this table:

| Shape | One-token time reduction | 32-token time reduction |
| --- | ---: | ---: |
| 2B | -0.67% | 73.61% |
| 4B | 0.70% | 79.02% |

The operator gate passes: large batches improve beyond the declared benefit/control-spread threshold, and the reference single-token path shows no clear regression. These are warm graph timings, not full-model or useful-answer speedups.

## Complete-answer latency and quality

Useful means required facts/citations and held-out code checks pass, plus cloud score at least 4/5. Scores use `mimo-v2.6-flash`, each pair judged in both presentation orders. All **12 paired answers are text-identical**, with identical output lengths and no measured candidate quality regression. Identical incorrect text remains a failed useful answer.

| Model | Total control → hybrid answer time | Time reduction | Useful control → hybrid | Mean score control → hybrid |
| --- | ---: | ---: | ---: | ---: |
| 2B | 777.534 → 754.864 s | 2.92% | 2/6 → 2/6 | 3.17 → 3.17/5 |
| 4B | 1767.333 → 1729.709 s | 2.13% | 5/6 → 5/6 | 4.50 → 4.50/5 |

These totals include all completed tasks, including incorrect answers. On the subset useful in both arms, total latency fell **3.003% for 2B (2 pairs)** and **2.968% for 4B (5 pairs)**. This retrospective subset does not replace the declared all-task gate or establish a general useful-answer speedup.

### Per-task complete-answer results

Timings and scores below are control → hybrid. Every row stopped naturally in both arms.

| Model/task | Tokens each | Answer latency, s | TTFT, s | Time reduction | Score /5 | Useful both |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
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

Rates divide the phase token count by measured phase time; aggregate rates use summed counts/time. They exclude server startup, build, validation and cloud scoring. Per-task phase rates are shown separately because prompt/output lengths differ.

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

Summed prefill time falls **7.86% for 2B** (302.012 → 278.271 s) and **4.77% for 4B** (769.898 → 733.154 s). Summed decode time rises 0.23% for 2B (474.034 → 475.143 s) and falls 0.08% for 4B (995.248 → 994.451 s). The phase data suggest why the large convolution graph gain produces a small complete-answer gain: other prefill work remains, and longer code/prose spends most of its time decoding through the reference path. No CPU-share or hardware-bandwidth attribution is inferred from these timings.

## Shared task failures and a passing answer

- **2B trace:** correct cobalt answer but omits all required S2/S4/S6 citations. The judge nevertheless gives 5/5; deterministic citation checks correctly reject usefulness. This is a concrete limit of model-only grading.
- **2B aggregation:** wrong required total, score 0/5; source citations pass.
- **Free-window code, both models:** 2B fails with `IndexError: list index out of range`; 4B rejects a zero-length interval with `ValueError: Interval (8, 8) has start >= end.` Scores are 1/5 and 2/5 respectively.
- **2B Chinese policy:** coarse fact checks pass but cloud grades are 3/5, citing incorrect date/shipping inferences and omissions. These judge findings are preserved; a cloud score is an assessment, not an independent proof.
- **Unicode run codec, both models:** 106 held-out functional checks pass; both receive 5/5. All other 4B tasks pass the declared usefulness checks.

These failures occur identically in control and hybrid. They are genuine baseline quality outcomes, not build/transport failures to repair by restarting the experiment. There are no candidate-only regressions, truncations or skipped qualification stages.

The [complete saved 4B Unicode run codec answer](2026-10-06-ssm-useful-answer-example.md) contains working `encode_runs` and `decode_runs`, including input validation. It passed 106 checks and 5/5 in both judge orders. The unmodified generated code is displayed in that artifact; it was not repaired to pass.

## Decision and limits

The candidate passes graph, state, operator and relative-quality gates. It fails the declared **greater-than-3% all-task latency gate** on both models and the absolute **6/6 useful-answer requirement**. Final `candidate_qualified=false` is a completed measured rejection, not a technical failure. Keep the implementation opt-in; no production-default change or automatic rerun is warranted. The 30-minute monitor is paused after completion.

There is one matched pair per task/model. These results are descriptive, with no significance, statistical noninferiority or universal identity claim. They establish neither general model correctness nor a reached K1 hardware limit. Further infrastructure work can target shared activation packing and phase-specific decode attribution under separate protocols.
