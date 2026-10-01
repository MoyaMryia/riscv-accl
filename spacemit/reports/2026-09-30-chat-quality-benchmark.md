# Chat-formatted cache quality benchmark

Completion update: 2026-10-01, Asia/Singapore.
See the [documentation guide](../DOCS.md) for related work.

The existing `bench-shared-document-cache.py` has a new `--quality-suite` mode.
The [complete runner](../bench/run-all-document-quality.py) stages code, starts
generation in board tmux, collects each configuration, judges completed pairs
through MiMo in both answer orders, and writes a combined report. Run it with
`--detach` to keep the workstation collector in tmux too.

Six questions cover route types, batch defaults, cache behavior, slot
assignment, health status and tokenization. The board constructs each document
from exact public server README passages and public corpus filler. Evidence is
labelled and distributed near the beginning, middle and end. The chat system
instruction and request format match the integrated document client. Generation
uses direct decoding, Q4_0 weights, F16 K/V, four threads, batch/microbatch 32,
enabled RVV attention, slot 0, temperature 0, seed 42 and disabled thinking.

New runs default to `--quality-schedule grouped`: one distinct primer,
all six cached targets, then six forced-cold controls. This reduces full
document passes from up to twelve to seven if reuse succeeds. Use
`--quality-schedule alternating` for the original order-controlled protocol,
with a different primer before each cached target. The completed matrix below
retains that original alternating schedule. Completed-answer scoring excludes
length-capped
answers, interrupted streams, reasoning output, wrong-slot responses, unverified
cache reuse and nonzero cold-cache reuse. Required-fact matching ignores Markdown
emphasis and checks for the batching explanation in the cache question. Checks
are term-based; the cloud judge additionally evaluates factual correctness.

## Completed pipeline smoke

The [2B/2k smoke](raw/document-quality-20260930-smoke/summary.md) compared one
question about cache behavior. Both answers ended naturally with `stop` and
had identical text. Cached first-answer latency was **3.453 s**, versus
**101.491 s** cold (29.39 times shorter). The cached request reported 2,077
cached prompt tokens; the cold request reported zero. Both used physical slot 0.
MiMo `mimo-v2.6-flash` scored both answers **4/5** in both answer orders.
It identified an omitted batching explanation and missing source citation in
both answers. This demonstrates the generation/collection/judging pipeline;
it is one pair and does not establish quality across documents or questions.

## Completed full matrix

The completed matrix is **2B/4B × 4k/8k documents × six questions = 24 pairs**, with
a 512-token output cap. Board generation and workstation cloud scoring run in
tmux. The [completed 2B/4k snapshot](raw/document-quality-20260930-full-v2/2B-4096.audit.md)
records six naturally completed, cache-verified pairs: mean cold/cached scores
were both 4.5/5 and median first-answer latency was 211.11/3.90 seconds.
The configuration requires quality review because the cache-behavior question
scored 2/5 in both arms; the other five questions scored 5/5 in both arms.
This does not establish a cache-specific quality regression.

All **24 of 24 pairs** completed naturally, passed cache/slot checks, and were
judged in both answer orders. The [combined report](raw/document-quality-20260930-full-v2/summary.md)
records the final results:

| Model / document | Cold / cached mean score | Median cold / cached TTFT | Descriptive gate |
| --- | ---: | ---: | --- |
| 2B / 4k | 4.50 / 4.50 | 211.11 / 3.90 s | Review required |
| 2B / 8k | 4.83 / 4.83 | 474.31 / 5.01 s | Pilot pass |
| 4B / 4k | 4.83 / 4.83 | 551.91 / 10.80 s | Pilot pass |
| 4B / 8k | 4.83 / 5.00 | 1271.37 / 14.65 s | Pilot pass |

Board generation exited successfully. Collector exit status **2** means quality
review is required for the 2B/4k cache question; it is not an inference failure.
The matrix does not pass every descriptive gate. One judge and six questions
per configuration cannot establish general answer-quality equivalence.

Detailed answers, exact documents, evidence, timing/cache fields, hashes,
scores, both judge orders and driver logs are saved in the completed directory.
The original alternating schedule was retained throughout. The earlier
`document-quality-20260930-full` launch was stopped before scoring to fix a
Markdown-sensitive fact-check false negative and is superseded by this v2 run.

The descriptive pilot gate requires all requested pairs to complete and be
judged, no required-fact or citation regression, cached mean score no more than
0.5 below cold, and every cached score at least 3/5. These thresholds are declared
checks, not statistical evidence of equivalence. Regression tests cover
stream integrity, final usage/slot telemetry, truncation, source placement,
Markdown normalization, judge order mapping, missing-pair detection, both
schedules, and resumed collection/judging without duplicate API calls.
