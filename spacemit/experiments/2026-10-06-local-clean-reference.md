# Local clean-reference answer check

Status: **completed and independently verified**, run `local-reference-quality-20261006-194015`.
Both exact model hashes, 3,266 clean source files and request/build audits pass.
All 12 tasks ran: 11 natural stops and one 4B interval-code length cap. Useful
answers are 1/6 for local 2B and 5/6 for local 4B, versus 2/6 and 5/6 on both
board arms. The same 2B arithmetic/citation failures and both interval-code
failures persist. The monitor is paused. See [measured results](../reports/2026-10-06-local-clean-reference-results.md).

## Question

The [hybrid SSM pilot](../reports/2026-10-06-ssm-complete-answer-results.md)
produced identical answers with and without the new convolution dispatch.
That excludes a measured SSM quality regression on those tasks, but both
board arms share earlier routing and attention changes. Replay the exact
weights and requests on an unpatched local reference to investigate whether
their arithmetic, citation and interval-code failures persist.

## Reference configuration

- Copy the exact 2B and 4B Q4_0 GGUFs from direct SSH `musepipro`. Require full-file
  SHA-256 equality with the prior campaign; retain the existing quantization,
  embedding format and mapped model metadata.
- Use `git archive` of clean SpaceMiT fork commit
  `a990751d55a4c54acf2bb77d44282c2093652359`. This matching revision understands
  these model files. Verify every extracted source file against the archive.
  Do not use the board checkout's three uncommitted CPU kernel patches.
- Build an isolated generic x86 CPU reference. Native ISA selection, AVX/AMX,
  SSE4.2, FMA/F16C, CPU weight repacking, KleidiAI, BLAS and GPU backends are
  disabled. The custom K1 build path is disabled. Ordinary Release compiler
  optimization and baseline x86 ABI instructions remain; this is an inference
  reference, not a deliberately slowed debug build.
- Disable flash attention and MTP; remove inherited custom runtime/preload
  variables. Use four workers, one slot, context 6144, batch/microbatch 32,
  F16 K/V and no context shifting.
- Send the **unchanged saved requests**: seed **42**, temperature **0**,
  thinking disabled, full prompt, no prompt cache and the same output guards.
  Require matching prompt token counts before generation. Never regenerate
  the document from a newer README or shorten it.

The local host is Intel x86, whereas the saved comparison is RISC-V K1.
Floating-point reduction order and the attention implementation differ.
The same seed does not guarantee identical output across these backends;
at temperature zero, numerical changes can still alter the highest logit.
Local wall time is recorded but is not a K1 optimization speed measurement.
The source archive and full file hashes are authoritative: embedded build
Git labels may inherit the outer repository during an archive-snapshot build.

## Tasks and checks

Run all six tasks on each model, for **12 local responses**: routes, trace,
receipt aggregation, interval/free-window code, Unicode run code and Chinese
policy prose. Save complete answers, request/answer hashes, prompt/output
lengths, natural stop, cold-input audits and phase timings. A guard-stopped
answer remains a truncation/usefulness failure.

Use the frozen fact/citation checks and restricted held-out Python tests.
Compare exact text separately against **both** saved board arms. Grade each
completed local answer against board control in both presentation orders,
using the existing authorized `mimo-v2.6-flash` endpoint. The key stays local
and is never staged, logged or transferred. Deterministic failures override
an overly generous judge mark. Preserve the prior board grades separately
from the new blinded comparison grades.

Interpretation:

1. An error reproduced by the clean local reference supports a limitation
   of these weights, quantization and decoding/prompt configuration.
2. An error fixed locally is evidence of a possible shared implementation
   or backend effect. A clean **same-board** comparison would be needed to
   attribute that difference specifically to our earlier optimizations.
3. These six tasks do not establish general model quality. Thinking mode,
   full-precision weights and alternative prompts are not tested here.

## Offload and recovery

[Campaign state](../reports/raw/local-reference-quality-campaign.json) identifies
the current run and monitor. The saved runner in each run is immutable.

```bash
tmux attach -t local_ref_20261006-194015
python3 spacemit/bench/local-reference-quality.py RUN_DIR
# After completed generation, recover cloud scoring only:
python3 RUN_DIR/local-reference-quality.py RUN_DIR --score-only
```

The initial preparation attempt `local-reference-quality-20261006-192949`
failed before inference because the board has no `rsync`. Its logs are retained.
The repaired run resumes task-owned model partial files through SSH `dd`,
then verifies the complete SHA-256 before renaming or loading. It waits for
the first attempt's build to finish before reusing the same clean build cache.
Both jobs use local tmux and exit markers. Technical repairs get fresh runs
and new scheduled monitors; valid negative quality results are reported
without weakening checks or repeatedly rerunning them.

## Direct transport update

At the user's request, the WireGuard preparation run
`local-reference-quality-20261006-193313` was stopped before inference
(zero requests). The direct `musepipro` alias was verified to reach the same
board. Run `local-reference-quality-20261006-194015` resumes the saved partial
GGUFs over that direct connection. Initial observed transfer speed rose from
approximately 0.33 MB/s to 20-30 MB/s; both full model hashes passed before
loading. The replacement monitor is now paused after completion.
