# Chat-formatted cache quality benchmark

Status snapshot: 2026-09-30, approximately 16:00 Asia/Singapore.
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
with a different primer before each cached target. The active matrix below
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

## Full matrix running

At the status check, the active matrix is **2B/4B × 4k/8k documents × six questions = 24 pairs**, with
a 512-token output cap. Board generation and workstation cloud scoring run in
tmux. The [completed 2B/4k snapshot](raw/document-quality-20260930-full-v2/2B-4096.audit.md)
records six naturally completed, cache-verified pairs: mean cold/cached scores
were both 4.5/5 and median first-answer latency was 211.11/3.90 seconds.
The configuration requires quality review because the cache-behavior question
scored 2/5 in both arms; the other five questions scored 5/5 in both arms.
This does not establish a cache-specific quality regression.

The collector has also completed and judged 2B/8k and 4B/4k, six pairs each.
Both have mean cold/cached scores of 4.83/5 and pass the descriptive pilot
gates. In total, 18 of 24 pairs have been collected and judged; 4B/8k board
generation is still active. These are partial-matrix results, not a full pass.

The collector updates `summary.md` and `summary.json` in the same run directory
as configurations finish. Changing collector output is kept outside the
completed-result snapshot. If collection stops, resume with
`python3 spacemit/bench/run-all-document-quality.py --collect-only --detach --run-dir /absolute/path/to/run`
from the repository root. This does not restart inference or change the
schedule. Detailed answers, exact documents, evidence,
timing/cache fields, hashes, scores, both judge orders, and driver logs are
saved there.

The initial `document-quality-20260930-full` launch was stopped before scoring
to fix a Markdown-sensitive fact-check false negative; it is superseded by
`document-quality-20260930-full-v2`. No full-matrix result is claimed here.

The descriptive pilot gate requires all requested pairs to complete and be
judged, no required-fact or citation regression, cached mean score no more than
0.5 below cold, and every cached score at least 3/5. These thresholds are declared
checks, not statistical evidence of equivalence. Regression tests cover
stream integrity, final usage/slot telemetry, truncation, source placement,
Markdown normalization, judge order mapping, missing-pair detection, both
schedules, and resumed collection/judging without duplicate API calls.
