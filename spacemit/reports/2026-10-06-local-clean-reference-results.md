# Local clean-reference quality results — October 6, 2026

Status: **completed and independently verified**. Run
`local-reference-quality-20261006-194015`, dispatched October 6 at 19:40
Asia/Singapore, and completed in **1 h 10 min 30 s**. The run included the
exact-model copying, the clean-build verification, the inference, and the
cloud judging. The generation and runner exit statuses are both 0. The local
tmux and its reference server have stopped. The monitor is paused, after the
report of the completion.

## Answer to the attribution question

**The new SSM dispatch did not worsen the measured quality in the board
pilot.** All 12 board control/hybrid pairs were text-identical, and the exact
graph and state checks passed. **The clean local reference reproduces the 2B
wrong sum and the omitted citations, and both models still fail the interval
code.** This evidence supports limitations of the tested Q4_0 weights and of
the inference/prompt configuration. It does not support an attribution of
those failures to the new SSM change.

On the six declared tasks, the local reference has **1 useful answer out of 6
for 2B** and **5 out of 6 for 4B**, against **2 out of 6 and 5 out of 6 in
both board arms**. No task that failed on the board becomes useful in the
clean local reference. One board-useful 2B answer becomes unhelpful locally,
and the local 4B interval answer also hits its output guard. These results are
observed results. They are not a technical fault and not a reason to loosen
the checks.

This comparison is **x86 against K1**, with different attention and numerical
implementations. It cannot independently prove that every earlier routing and
attention change is harmless. It cannot prove that the model itself, rather
than quantization, greedy decoding, or prompt wording, causes each error. The
same seed at temperature zero is not enough for a guarantee of identical
logits across architectures. A clean comparison on the same board would be
necessary, for a causal attribution of the earlier changes.

## Matched inputs and reference build

We copied the exact board GGUF files over direct SSH `musepipro`, and we
independently verified their full SHA-256 values:

| Model | Bytes | SHA-256 |
| --- | ---: | --- |
| Qwen3.5-2B Q4_0 | 1,181,126,112 | `56f0ddd90dfa0e2456af6cb4718ece419678d21a75d65e27353319b5e431a2fa` |
| Qwen3.5-4B Q4_0 | 2,542,264,480 | `0adf6cce5df53921606033c39a13fae2054543b78af0e7ff98860e86f078ac0f` |

The reference uses the clean archived SpaceMiT fork commit
`a990751d55a4c54acf2bb77d44282c2093652359`, which matches the model-format
support. Every one of **3,266 archived source files** matches the extracted
copy. The source archive SHA-256 is
`5b4e0240fae5464f6b047f2689f5e534e500413a90dad489e518866af8723659`. No board
kernel patch and no benchmark dispatch marker is present. The archive identity
is authoritative. Embedded Git labels can inherit the outer repository, and
they do not identify this snapshot.

The host is Intel Core Ultra 9 285H, x86_64, GCC 11.4. The generic CPU build
disables native ISA selection, AVX/AMX, SSE4.2, FMA/F16C, weight repacking,
KleidiAI, BLAS, GPU backends, and the custom K1 path. Flash attention and MTP
are off. Ordinary Release compiler optimization and baseline x86 ABI
instructions remain. This build is an unpatched inference reference. It is not
an interpreter and not a debug build.

All **12 requests are byte for byte the saved board payloads**: seed **42**,
temperature **0**, thinking off, full prompts, no cache, four workers, one
slot, context 6144, batch/microbatch 32, and F16 K/V. The prompt token counts
agree with the board for all tasks. The factual output guard is 512, and the
code and policy guard is 2048. Both guards are unchanged.

The initial `rsync` preparation failure and the stopped slow WireGuard
transfer are preserved as separate attempts. Neither attempt generated an
inference answer. The direct transfer resumed the saved partial 2B file, and
it verified both full hashes. It averaged approximately **26.34 MB/s for the
remaining 2B transfer** and **25.45 MB/s for 4B**. The receipts include the
final hash verification. The direct transfers took about 140 s in sequence.
Only this final run generated answers.

## Verified quality outcomes

Useful means three things: a natural completion, passing required fact and
citation checks, and passing held-out code checks. It means also a mean cloud
score of at least 4/5. The judge is `mimo-v2.6-flash`, blinded in both
presentation orders. A judge graded all 11 naturally stopped local answers in
both orders (**22 cloud judgments**). The length-capped answer is ungraded,
and it counts as not useful.

| Model | Natural stop / capped | Fact+citation checks | Held-out code tasks | Useful local | Useful board control / hybrid | Exact text matches control / hybrid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2B | 6 / 0 | 2/4 | 1/2 | 1/6 | 2/6 / 2/6 | 2/6 / 2/6 |
| 4B | 5 / 1 | 4/4 | 1/2 | 5/6 | 5/6 / 5/6 | 2/6 / 2/6 |

The 2B mean local score is **2.58/5 over six judged answers** (the saved
board pilot was 3.17/5). For 4B, the mean is **5.00/5 over only five judged
answers**. The failed and truncated sixth task is excluded from that mean, but
it is included in the 5/6 usefulness denominator. The 5.00/5 score therefore
does not mean six correct answers. We retain the new board rescores separately
from the original pilot scores. For example, the 4B trace is 4.5/5 in the new
paired judging, against 5/5 originally. The judge remains an assessment, not a
proof of correctness.

### Per task

The board scores below come from the original pilot. The local scores come
from the new paired judgment. The scores are means over two presentation
orders. The token counts and the stop status refer to the local response. All
board control and hybrid outputs are identical to each other. The local
identity therefore agrees against both.

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

The clean reference and the board output exactly this text:

> Total: 79 units.
>
> Receipt A: 17 units [S1]; Receipt B: 23 units [S3]; Receipt C: 38 units [S5].

The listed numbers sum to **78**, not 79. The entire response is
text-identical across the clean reference, the board control, and the hybrid.
See the [saved local answer](raw/local-reference-quality-20261006-194015/2B-reference-aggregation-answer.md).

### 2B citations: the same omission

The prompt asks explicitly for citations S2, S4, and S6. All three
configurations output exactly:

> The cabinet is **cobalt**.

The color is correct, but all the required citations are missing. Both judge
orders still give 5/5. The deterministic citation checks reject the usefulness.
See the [saved local answer](raw/local-reference-quality-20261006-194015/2B-reference-trace-answer.md).

### Interval code: still incorrect on both models

- **2B local:** `merge_intervals([(2,4),(0,2),(8,8)])` fails held-out check 2.
  The generated merge uses `a <= last_end or b >= last_start`, and it
  incorrectly merges separate ranges. Its `free_windows` returns the busy
  ranges, rather than their complement. The board answer fails with
  `IndexError`. Neither answer passes. See the
  [saved local code](raw/local-reference-quality-20261006-194015/2B-reference-free_windows-answer.md).
- **4B local:** the code rejects zero-length intervals with
  `if start >= end: raise ValueError(...)`, despite an explicit instruction to
  ignore them. This behavior reproduces the board failure on `(8,8)`. The
  local answer continues with repetitive code comments until **2048 tokens**,
  and it finishes with `length`. It remains a failed useful answer. No cloud
  grade and no automatic output-budget increase was applied. See the
  [saved local code](raw/local-reference-quality-20261006-194015/4B-reference-free_windows-answer.md).

### Other results

- **2B routes:** the board correctly lists three route types. Locally, one
  item contains the whole list, and the next two items duplicate subsets of it.
  The keyword checks pass, but both judge orders give 2/5 for the malformed
  enumeration. This result is the additional local usefulness failure.
- **2B Chinese policy:** the local answer still fails usefulness (2.5/5). A
  judge found date and shipping inconsistencies, and omitted return-postage
  details. The keyword checks alone pass. That behavior illustrates their
  limited coverage. We preserve the judge comments on the dates as
  assessments, not as an independent calendar validation.
- **Unicode codec, both models:** all **106 held-out functional checks** pass,
  and the local scores are 5/5. These answers differ from the board text,
  while they remain useful. See the
  [4B complete local codec](raw/local-reference-quality-20261006-194015/4B-reference-unicode_runs-answer.md).
- **4B remaining factual and policy tasks:** all declared checks pass, with
  local 5/5 grades. Its routes and aggregation answers are text-identical to
  the board.

## Timing record and limitations

These timings describe this generic x86 run only. They are not a matched
hardware performance experiment. You must not divide them by K1 times to
claim an optimization speedup.

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

The total recorded request latency is 877.971 s for 2B and 2,857.632 s for 4B.
The whole-run elapsed time includes the copies, the model startup, the
verification, and the scoring. One request per task and model gives a
descriptive comparison. It is not statistical equivalence and not general model
quality.

We launched no new inference to repair these negative outcomes. The test gives
evidence that the observed failures persist without our custom K1 paths. It
does not isolate weight quantization, thinking mode, model capability, or
cross-backend numerical drift. It does not qualify a production-default
change, RS rollback, or a reached hardware limit.

## Reproducibility evidence

- [Protocol](../experiments/2026-10-06-local-clean-reference.md),
  [run manifest](raw/local-reference-quality-20261006-194015/run.json)
- [Final summary](raw/local-reference-quality-20261006-194015/summary.json),
  [independent completion verification](raw/local-reference-quality-20261006-194015/completion-verification.json),
  [saved verification program](raw/local-reference-quality-20261006-194015/verify-completion.py)
- [Exact model verification](raw/local-reference-quality-20261006-194015/model-verification.json),
  [source verification](raw/local-reference-quality-20261006-194015/source-verification.json),
  [build configuration](raw/local-reference-quality-20261006-194015/build-config.json),
  [binary/build verification](raw/local-reference-quality-20261006-194015/build-verification.json)
- [2B responses and audits](raw/local-reference-quality-20261006-194015/2B-reference.json),
  [4B responses and audits](raw/local-reference-quality-20261006-194015/4B-reference.json)
- [2B two-order judgments](raw/local-reference-quality-20261006-194015/2B-judge.jsonl),
  [4B two-order judgments](raw/local-reference-quality-20261006-194015/4B-judge.jsonl)

The completion verification rechecks both full model hashes, all source and
archive files, the five frozen board inputs, the frozen runner, the build and
binary hashes, the disabled compiler and backend flags, all request and answer
hashes, the cold, token, slot, and draft audits, the held-out functional
results, and all 11 judgment fingerprints. The result-file hash map covers the
local evidence. These files are not members of the prior 114-artifact board
receipt.
