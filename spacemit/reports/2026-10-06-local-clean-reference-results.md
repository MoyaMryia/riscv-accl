# Local clean-reference quality results — October 6, 2026

Status: **completed and independently verified**. Run `local-reference-quality-20261006-194015`, dispatched October 6 at 19:40 Asia/Singapore, completed in **1 h 10 min 30 s**, including exact-model copying, clean-build verification, inference and cloud judging. Generation and runner exit statuses are both 0; local tmux and its reference server have stopped. The monitor is paused after reporting completion.

## Answer to the attribution question

**The new SSM dispatch did not worsen measured quality in the board pilot:** all 12 board control/hybrid pairs were text-identical, and exact graph/state checks passed. **The clean local reference reproduces the 2B wrong sum and omitted citations, and both models still fail interval code.** This supports limitations of the tested Q4_0 weights and inference/prompt configuration rather than attributing those failures to the new SSM change.

On the six declared tasks, the local reference has **1/6 useful answers for 2B** and **5/6 for 4B**, compared with **2/6 and 5/6 in both board arms**. No task that failed on the board becomes useful in the clean local reference. One board-useful 2B answer becomes unhelpful locally; the local 4B interval answer also hits its output guard. These are observed results, not a technical fault or a reason to loosen checks.

This is **x86 versus K1**, with different attention and numerical implementations. It cannot independently prove that every earlier routing/attention change is harmless, or that the model itself rather than quantization, greedy decoding or prompt wording causes each error. Same seed at temperature zero is insufficient to guarantee identical logits across architectures. A clean comparison on the same board would be needed for causal attribution of the earlier changes.

## Matched inputs and reference build

The exact board GGUF files were copied over direct SSH `musepipro` and their full SHA-256 values independently verified:

| Model | Bytes | SHA-256 |
| --- | ---: | --- |
| Qwen3.5-2B Q4_0 | 1,181,126,112 | `56f0ddd90dfa0e2456af6cb4718ece419678d21a75d65e27353319b5e431a2fa` |
| Qwen3.5-4B Q4_0 | 2,542,264,480 | `0adf6cce5df53921606033c39a13fae2054543b78af0e7ff98860e86f078ac0f` |

The reference uses clean archived SpaceMiT fork commit `a990751d55a4c54acf2bb77d44282c2093652359`, matching model-format support. Every one of **3,266 archived source files** matches the extracted copy. Source archive SHA-256 is `5b4e0240fae5464f6b047f2689f5e534e500413a90dad489e518866af8723659`. No board kernel patches or benchmark dispatch markers are present. Archive identity is authoritative; embedded Git labels can inherit the outer repository and do not identify this snapshot.

The host is Intel Core Ultra 9 285H, x86_64, GCC 11.4. The generic CPU build disables native ISA selection, AVX/AMX, SSE4.2, FMA/F16C, weight repacking, KleidiAI, BLAS, GPU backends and the custom K1 path. Flash attention and MTP are off. Ordinary Release compiler optimization and baseline x86 ABI instructions remain. This is an unpatched inference reference, not an interpreter or debug build.

All **12 requests are byte-for-byte the saved board payloads**: seed **42**, temperature **0**, thinking off, full prompts, no cache, four workers, one slot, context 6144, batch/microbatch 32 and F16 K/V. Prompt token counts agree with the board for all tasks. The factual output guard is 512; code and policy guard is 2048, unchanged.

The initial `rsync` preparation failure and stopped slow WireGuard transfer are preserved as separate attempts. Neither generated an inference answer. Direct transfer resumed the saved partial 2B file, verified both full hashes and averaged approximately **26.34 MB/s for the remaining 2B transfer** and **25.45 MB/s for 4B** (receipts include final hash verification). The direct transfers took about 140 s in sequence; only this final run generated answers.

## Verified quality outcomes

Useful means natural completion, passing required facts/citations and held-out code checks, plus mean cloud score at least 4/5. The judge is `mimo-v2.6-flash`, blinded in both presentation orders. All 11 naturally stopped local answers were graded in both orders (**22 cloud judgments**). The length-capped answer is ungraded and counts as not useful.

| Model | Natural stop / capped | Fact+citation checks | Held-out code tasks | Useful local | Useful board control / hybrid | Exact text matches control / hybrid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2B | 6 / 0 | 2/4 | 1/2 | 1/6 | 2/6 / 2/6 | 2/6 / 2/6 |
| 4B | 5 / 1 | 4/4 | 1/2 | 5/6 | 5/6 / 5/6 | 2/6 / 2/6 |

The 2B mean local score is **2.58/5 over six judged answers** (saved board pilot 3.17/5). For 4B it is **5.00/5 over only five judged answers**; its failed, truncated sixth task is excluded from that mean but included in the 5/6 usefulness denominator. Thus 5.00/5 does not mean six correct answers. New board rescores are retained separately from original pilot scores; for example 4B trace is 4.5/5 in the new paired judging versus 5/5 originally. The judge remains an assessment, not correctness proof.

### Per task

Board scores below are from the original pilot; local scores are from the new paired judgment. Scores are means over two presentation orders. Tokens and stop status refer to the local response. All board control/hybrid outputs are identical to each other; local identity therefore agrees against both.

| Model/task | Local tokens | Stop | Local score /5 | Original board score /5 | Useful local / board | Exact text match |
| --- | ---: | --- | ---: | ---: | --- | --- |
| 2B/routes | 44 | stop | 2.0 | 5.0 | No / Yes | No |
| 2B/trace | 8 | stop | 5.0 | 5.0 | No / No | Yes |
| 2B/aggregation | 50 | stop | 0.0 | 0.0 | No / No | Yes |
| 2B/free_windows | 840 | stop | 1.0 | 1.0 | No / No | No |
| 2B/unicode_runs | 504 | stop | 5.0 | 5.0 | Yes / Yes | No |
| 2B/chinese_policy | 442 | stop | 2.5 | 3.0 | No / No | No |
| 4B/routes | 23 | stop | 5.0 | 5.0 | Yes / Yes | Yes |
| 4B/trace | 64 | stop | 5.0 | 5.0 | Yes / Yes | No |
| 4B/aggregation | 45 | stop | 5.0 | 5.0 | Yes / Yes | Yes |
| 4B/free_windows | 2048 | length | Not graded | 2.0 | No / No | No |
| 4B/unicode_runs | 595 | stop | 5.0 | 5.0 | Yes / Yes | No |
| 4B/chinese_policy | 308 | stop | 5.0 | 5.0 | Yes / Yes | No |

## Concrete failures and passing code

### 2B arithmetic: the same wrong answer

Both clean reference and board output exactly:

> Total: 79 units.
>
> Receipt A: 17 units [S1]; Receipt B: 23 units [S3]; Receipt C: 38 units [S5].

The listed numbers sum to **78**, not 79. The entire response is text-identical across clean reference, board control and hybrid. [Saved local answer](raw/local-reference-quality-20261006-194015/2B-reference-aggregation-answer.md).

### 2B citations: the same omission

The prompt explicitly asks to cite S2, S4 and S6. All three configurations output exactly:

> The cabinet is **cobalt**.

The color is correct, but all required citations are missing. Both judge orders still give 5/5; the deterministic citation checks reject usefulness. [Saved local answer](raw/local-reference-quality-20261006-194015/2B-reference-trace-answer.md).

### Interval code: still incorrect on both models

- **2B local:** `merge_intervals([(2,4),(0,2),(8,8)])` fails held-out check 2. The generated merge uses `a <= last_end or b >= last_start`, incorrectly merging separate ranges. Its `free_windows` also returns busy ranges rather than their complement. The board answer fails with `IndexError`; neither answer passes. [Saved local code](raw/local-reference-quality-20261006-194015/2B-reference-free_windows-answer.md).
- **4B local:** its code rejects zero-length intervals via `if start >= end: raise ValueError(...)`, despite an explicit instruction to ignore them. This reproduces the board failure on `(8,8)`. The local answer additionally continues with repetitive code comments until **2048 tokens**, finishing with `length`. It remains a failed useful answer; no cloud grade or automatic output-budget increase was applied. [Saved local code](raw/local-reference-quality-20261006-194015/4B-reference-free_windows-answer.md).

### Other results

- **2B routes:** the board correctly lists three route types. Locally, one item contains the whole list and the next two duplicate subsets. Keyword checks pass, but both judge orders give 2/5 for the malformed enumeration. This is the additional local usefulness failure.
- **2B Chinese policy:** the local answer still fails usefulness (2.5/5), with judged date/shipping inconsistencies and omitted return-postage details. Keyword checks alone pass, illustrating their limited coverage. Judge comments on dates are preserved as assessments, not independent calendar validation.
- **Unicode codec, both models:** all **106 held-out functional checks** pass, and local scores are 5/5. These answers differ from the board text while remaining useful. [4B complete local codec](raw/local-reference-quality-20261006-194015/4B-reference-unicode_runs-answer.md).
- **4B remaining factual/policy tasks:** all declared checks pass with local 5/5 grades. Its routes and aggregation answers are text-identical to the board.

## Timing record and limitations

These timings describe this generic x86 run only. They are not a matched hardware performance experiment and must not be divided by K1 times to claim an optimization speedup.

| Model/task | Local answer latency, s | TTFT, s |
| --- | ---: | ---: |
| 2B/routes | 196.239 | 190.304 |
| 2B/trace | 192.759 | 191.804 |
| 2B/aggregation | 197.862 | 191.096 |
| 2B/free_windows | 128.374 | 15.051 |
| 2B/unicode_runs | 81.578 | 14.351 |
| 2B/chinese_policy | 81.159 | 21.872 |
| 4B/routes | 516.132 | 509.384 |
| 4B/trace | 543.534 | 524.064 |
| 4B/aggregation | 687.834 | 675.038 |
| 4B/free_windows | 684.985 | 70.842 |
| 4B/unicode_runs | 238.457 | 63.774 |
| 4B/chinese_policy | 186.690 | 101.280 |

Total recorded request latency is 877.971 s for 2B and 2857.632 s for 4B. Whole-run elapsed time includes copies, model startup, verification and scoring. One request per task/model provides a descriptive comparison, not statistical equivalence or general model quality.

No new inference is launched to repair these negative outcomes. The test provides evidence that the observed failures persist without our custom K1 paths. It does not isolate weight quantization, thinking mode, model capability or cross-backend numerical drift. It does not qualify a production-default change, RS rollback or a reached hardware limit.

## Reproducibility evidence

- [Protocol](../experiments/2026-10-06-local-clean-reference.md), [run manifest](raw/local-reference-quality-20261006-194015/run.json)
- [Final summary](raw/local-reference-quality-20261006-194015/summary.json), [independent completion verification](raw/local-reference-quality-20261006-194015/completion-verification.json), [saved verification program](raw/local-reference-quality-20261006-194015/verify-completion.py)
- [Exact model verification](raw/local-reference-quality-20261006-194015/model-verification.json), [source verification](raw/local-reference-quality-20261006-194015/source-verification.json), [build configuration](raw/local-reference-quality-20261006-194015/build-config.json), [binary/build verification](raw/local-reference-quality-20261006-194015/build-verification.json)
- [2B responses and audits](raw/local-reference-quality-20261006-194015/2B-reference.json), [4B responses and audits](raw/local-reference-quality-20261006-194015/4B-reference.json)
- [2B two-order judgments](raw/local-reference-quality-20261006-194015/2B-judge.jsonl), [4B two-order judgments](raw/local-reference-quality-20261006-194015/4B-judge.jsonl)

Completion verification rechecks both full model hashes, all source/archive files, five frozen board inputs, the frozen runner, build/binary hashes and disabled compiler/backend flags, all request/answer hashes, cold/token/slot/draft audits, held-out functional results and all 11 judgment fingerprints. The result-file hash map covers local evidence; these files are not members of the prior 114-artifact board receipt.
