# K1 infrastructure release verification

Date: October 7, 2026, Asia/Singapore. Status: independently verified.
Run: `k1-release-check-20261007-125712`, direct SSH `musepipro`.

## Release scope

The [release package](../release/README.md) pins the SpaceMiT fork at
`a990751d55a4c54acf2bb77d44282c2093652359`. Its single checked patch reproduces
the measured RVV F16 attention and Q4_0 IME routing source exactly. Baseline
and optimized profiles share wide RVV attention, layout 0, four workers,
batch/microbatch 32, F16 KV and direct decoding; routing is 0 and 3 respectively.
Routing stays opt-in because the broader absolute answer-quality gate is open.

Hybrid SSM, fixed-K32 M1, MTP, compact layouts and GPU offload are not enabled.
ARM/x86 comparison is outside the release requirements at the user's request.
The completed clean-reference quality diagnostic is retained as historical
evidence and is not a cross-architecture performance comparison.

## Reproducibility checks

Offline patch application checked all 3,266 files in the pinned clean source
archive and reproduced the three measured patched-file SHA-256 values.
Reapplication to the modified tree was rejected. The receipt is
[clean-apply-verification.json](raw/release-20261007/clean-apply-verification.json).

Eight local regression suites pass 33 checks, covering release pins and
profile isolation, SSM runner/quality behavior, strict decode clocks and
startup/request boundaries, M1 specialization, routing, fast gates and IME.
Python compilation and shell syntax checks pass for the release tools.
The existing routing and staged-validation artifact verifiers pass, retaining
their quality failures and skipped stages. The historical matrix verifier
reproduces 21 rows / 105 numeric cells. No previous measurement is rewritten.

## Fresh board verification

The isolated board/local tmux job starts from a clean detached checkout and
builds the complete server and benchmark with the packaged settings. Native
verification requires 104 production graph cases per routing arm, exact dump
identity to the preserved measured baseline and actual routing activation.

The complete-answer smoke test replays the frozen Unicode run encoder/decoder
task once per model/profile: four cold requests, seed 42, temperature 0,
thinking disabled, full 162-token input and a 2,048-token output budget.
Each answer must stop naturally, pass all 106 held-out functional checks and
match its paired control text. Truncation is a failure. These are complete
code answers, rather than capped throughput samples.

The complete clean build and smoke test finish in **57.01 minutes**. Board
and collector exit statuses are zero. Both 104-case native arms match the
preserved baseline dump hash
`e31997719879fb9a858f9e970af7e11ceb68124657d41c53bd3b3f82c4dbd4dc`.
All four responses stop naturally and pass all 106 checks, without prompt
reuse, draft tokens, thinking or input truncation. Each model's paired text
also matches its earlier frozen control.

| Model | Output tokens per arm | Baseline / optimized answer latency | Observed reduction | Baseline / optimized TTFT | Baseline / optimized prefill | Baseline / optimized decode |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2B | 508 | 146.565 / 124.634 s | 14.96% | 7.511 / 6.926 s | 22.06 / 23.95 tok/s | 3.65 / 4.32 tok/s |
| 4B | 521 | 380.611 / 280.354 s | 26.34% | 18.984 / 18.005 s | 8.60 / 9.07 tok/s | 1.44 / 1.99 tok/s |

These are **one paired observation per model**, in baseline/optimized order
for 2B and optimized/baseline for 4B. They show complete passing code answers
in the fresh package. They do not replace the prior performance replications,
establish general answer-quality equivalence, or prove a hardware limit.
Existing shared arithmetic/citation/interval-code failures stay documented;
this smoke test does not turn the broader absolute quality gate into a pass.

An actual passing complete answer is saved as
[4B optimized code](raw/k1-release-check-20261007-125712/4B-route3.answer.md),
with its [full request, completion audit and functional result](raw/k1-release-check-20261007-125712/4B-route3.answer.json).

## Independent artifact and source verification

The archive checksum, exact 35-file list and every artifact hash pass.
All 18 local and remote staged code files and three collector files match the
frozen run. Post-run verification checks 25 fresh source/build/code hashes,
the exact modified-file sets in fresh and measured-baseline checkouts, both
vendor runtime library hashes and the recorded GCC 14 version. Both checkouts
have only the expected three tracked source changes. CMake settings match
the packaged controls; clean source, patched source and both model pins match.

Derived analysis records are outside the original 35-artifact receipt:
[independent verification](raw/release-20261007/verification.json),
[post-run board preservation](raw/release-20261007/remote-preservation.json),
[local regression inventory](raw/release-20261007/local-checks.json).
The original collection is preserved:
[receipt](raw/k1-release-check-20261007-125712/collection-receipt.json),
[summary](raw/k1-release-check-20261007-125712/summary.json),
[paired full answers](raw/k1-release-check-20261007-125712/complete-answer-pairs.json).

## Evidence and repeat commands

- [Frozen run and code hashes](raw/k1-release-check-20261007-125712/run.json)
- [Release manifest](../release/manifest.json)
- [Fresh-build and complete-answer runner](../bench/k1-release-check.py)
- [Independent artifact/answer verifier](../bench/verify-k1-release.py)
- [Submission report](SUBMISSION-REPORT.md) and [evidence appendix](SUBMISSION-EVIDENCE.md)

```bash
python3 spacemit/release/test-release.py
python3 spacemit/bench/start-k1-release-check.py --board musepipro
python3 spacemit/reports/raw/release-20261007/preserve-board.py \
  spacemit/reports/raw/k1-release-check-20261007-125712 \
  spacemit/reports/raw/release-20261007/remote-preservation.json
python3 spacemit/bench/verify-k1-release.py \
  spacemit/reports/raw/k1-release-check-20261007-125712 \
  --preservation spacemit/reports/raw/release-20261007/remote-preservation.json \
  --output spacemit/reports/raw/release-20261007/verification.json
```

Strict archive verification needs the retained `.data` dumps and compressed
archive, which are stored locally with checksum inventories. Git contains
the source, frozen requests/answers, logs and receipts; it excludes generated
model/build binaries and credentials.
