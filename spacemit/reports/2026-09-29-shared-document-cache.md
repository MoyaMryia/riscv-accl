# Changed-question cache test on MUSE-Pi-Pro

> Dated campaign snapshot. The measurements apply to the stated workload and
> date. Queued/running statements below are historical. Use the
> [current guide](../DOCS.md) and the [reports index](README.md) for later
> results and for the current status.

Date: 2026-09-28–29 (Asia/Singapore). This report tests whether a long shared
document prefix remains usable when the question at the end changes. The
corpus is unmodified, public `README.md` and `docs/*.md`, already present in
the SpaceMiT llama.cpp checkout on the board. The corpus has 70,721 model
tokens. Its exact archived bytes are
[here](raw/2026-09-25-lifecycle/shared-document-public-llamacpp.txt), and
each JSONL configuration records its SHA-256. We did not transfer local
project reports to the board, because the automatic approval review rejected
that transfer.

The [runner](../bench/run-shared-document-cache-board.sh) uses one server
process and one slot per model and context. It sends question A with a cold
document prefix and `cache_prompt=true`. It sends question B with the same
document prefix and `cache_prompt=true`. Then it sends question B again with
`cache_prompt=false`, to force a cold control. The
[auditor](../bench/audit-shared-document-cache.py) requires 32 output tokens,
a cold control with `cache_n=0`, at least 90% document-prefix reuse for warm
B, warm TTFT at most half of cold B, and exact warm/cold B token IDs and
text. Every arm uses Q4_0 weights, F16 K/V, direct decoding, four threads,
batch/microbatch 32, and the enabled 256-bit RVV attention kernel.

| Model | Document tokens | New question cold TTFT | New question warm TTFT | Cached tokens | Warm/cold B output | Gate |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| 2B | 8,192 | 468.47 s | 4.12 s | 8,181 | Identical 32 token IDs | PASS |
| 2B | 16,384 | 1,172.90 s | 6.31 s | 16,373 | First difference at generated token index 5 | **FAIL** |
| 4B | 8,192 | 1,227.53 s | 12.78 s | 8,181 | Identical 32 token IDs | PASS |
| 4B | 16,384 | 3,229.58 s | 21.29 s | 16,373 | Identical 32 token IDs | PASS |

The warm B request evaluated 37 tokens at each length: the 26-token question
plus 11 reprocessed prefix tokens. The cold B control evaluated all document
and question tokens. All requests completed without server errors. The warm
2B/16k request was fast, but its token IDs diverged from the cold control at
index 5. The same exact whole-prompt repeat passed at 16k and 32k in the
[earlier experiment](2026-09-28-long-prefill-research.md). A changed suffix
is a distinct correctness condition. These records do not establish the cause
of the 2B mismatch. Numerical sensitivity, recurrent-state reuse, and another
cache-path difference all remain possible.

The gated sequence stopped 2B before 32k, after its 16k failure. 4B ran
independently, and it passed at 8k and 16k. We did not schedule 4B/32k,
because its two cold controls would be very long. Raw records:
[2B/8k](raw/2026-09-25-lifecycle/2B-shared-document-8192-rvv1.jsonl),
[2B/16k](raw/2026-09-25-lifecycle/2B-shared-document-16384-rvv1.jsonl),
[4B/8k](raw/2026-09-25-lifecycle/4B-shared-document-8192-rvv1.jsonl),
[4B/16k](raw/2026-09-25-lifecycle/4B-shared-document-16384-rvv1.jsonl), and
the [driver log](raw/2026-09-25-lifecycle/shared-document-driver.log). The
detached [tmux completion audit](raw/2026-09-25-lifecycle/shared-document-detached-audit.log)
passed 4B/16k.

**Deployment decision:** Exact-prefix reuse with a changed question is
demonstrated only for the measured 2B/8k and 4B/8k–16k cases. Do not promise
exact 2B answers for changed questions at 16k or longer on the basis of this
cache path. A useful follow-up is a targeted 2B/16k repeat, with target
logits or cache-state diagnostics around the first differing generated token.
A varied-question correctness set can follow, if we fix the mismatch. The
full 32k cold prefill remains slow for unique documents.

## Cloud judge follow-up

The recovered readable text for the original 2B/16k 32-token pair is in the
[judge input](raw/2026-09-25-lifecycle/2B-shared-document-16384-judge-input.json).
MiMo `mimo-v2.6-flash` returned **0/5 for both the cold and the warm
answers**, in both blind answer orders
([raw marks](raw/2026-09-25-lifecycle/2B-shared-document-16384-mimo-v26-judge.jsonl)).
Its reasons state that both responses were cut off before they gave
substantive information. We detokenized the token IDs locally with the board
model, and both reconstructed texts matched their stored stream hashes. These
scores therefore validate the scoring API path. They do not establish
semantic equivalence. We started a detached 256-token, EOS-enabled 2B/16k
run, to produce scoreable answers. You must audit and judge its result
separately, after the completion.

## 256-token quality follow-up (completed 2026-09-29)

The [detached quality run](../bench/run-shared-document-quality-board.sh)
repeated the 2B/16k changed-question setup. It used a 256-token generation
cap, EOS allowed, readable text saved, and the same public document. All
three requests completed without a server error. Question B reused 16,373
document tokens and evaluated 37 tokens. Its client TTFT was **6.25 s**
against **1,174.41 s** for the forced-cold B control. The warm and cold B
token sequences still first differed at generated index 5. Both B answers hit
the 256-token limit, instead of a natural stop. The warm answer contained
actionable installation and run steps. The cold answer continued into an
unrelated Contributing section, and it ended partway through a link. The cold
A answer repeatedly emitted empty `<think>` blocks. That behavior is another sign
that this raw document-plus-question prompt is not a clean user-facing answer
format.

The
[MiMo judge input](raw/2026-09-25-lifecycle/2B-shared-document-16384-quality256-rvv1-judge-input.json)
supplied the question, the README Quick Start excerpt, and the full captured
warm/cold B texts. MiMo `mimo-v2.6-flash` scored the cold answer **3/5** and
the warm answer **4/5**, in both blinded answer orders
([raw marks](raw/2026-09-25-lifecycle/2B-shared-document-16384-quality256-rvv1-mimo-v26-judge.jsonl)).
The judge found both answers broadly correct. It marked the cold answer down
for omissions, for irrelevant Contributing content, and for an unsupported
quick-start path. It found also minor omissions and unsupported links in the
warm answer. These marks come from one cloud judge, on one question, with an
882-character evidence excerpt. They are not a statistically reliable quality
result. The excerpt can omit facts that are elsewhere in the full document,
and both responses were still capped at 256 tokens. The raw
[benchmark record](raw/2026-09-25-lifecycle/2B-shared-document-16384-quality256-rvv1.jsonl),
[server log](raw/2026-09-25-lifecycle/2B-shared-document-16384-quality256-rvv1.log),
and [tmux/cloud watcher log](raw/2026-09-25-lifecycle/quality256-cloud-watcher.log)
are archived.

**Updated interpretation:** The observed 2B/16k token mismatch did not make
the cached answer worse on this question. The single judged pair favored the
warm answer. The experiment is still not enough to establish general
semantic safety for changed questions. The later
[chat quality benchmark](2026-09-30-chat-quality-benchmark.md) implements
chat formatting, checkable included evidence, completion gates, and multiple
question positions. Do not treat its partial results as a general
semantic-safety guarantee.
