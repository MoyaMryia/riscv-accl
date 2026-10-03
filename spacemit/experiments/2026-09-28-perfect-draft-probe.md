# Perfect-draft verify probe (x86 batch-shape mechanism)

> Dated campaign snapshot. Measurements apply to the stated workload and date.
> Queued/running statements below are historical; use the
> [current guide](../DOCS.md) and the [experiments index](README.md) for later results and current status.

Task A, step "x86 复现 + 机制定位". Isolates the mechanism behind the board's
direct/MTP divergence (2B first mismatch at generated index 179, 4B at 303;
margins in [2026-09-27-resumed-measures.md](../reports/2026-09-27-resumed-measures.md))
from draft-model quality: the draft is the *direct greedy trajectory itself*.

> October 3 clarification: the proposed tie guard below is unimplemented. An
> observed epsilon does not guarantee arbitrary-input identity, and hybrid
> models require recurrent-state restoration as well as attention KV rollback.
> See the [validation review](../reports/2026-10-03-validation-practice.md).

## Mechanism hypothesis

Speculative verification evaluates the draft's k tokens in one decode ubatch
(matmul M=k), while direct decoding evaluates one token per ubatch (M=1).
The CPU backend routes these through different GEMM/vec-dot paths with
different accumulation order, so the logits differ by rounding-scale noise.
At positions where the top-2 margin is below that noise, argmax flips and the
outputs diverge permanently. Board evidence: at 2B/179 the MTP (batched) top-2
margin was 0.0034 vs direct 0.069; at 4B/303 direct margin was 0.0022 and the
batched logits themselves moved by ~0.06.

The probe measures exactly this on x86, with the draft held perfect:

- `direct` mode replays one-token ubatches (M=1) and records the trajectory
  plus top-2 logits at every step.
- `verify` mode re-evaluates that trajectory in chunks of k tokens (M=k), the
  shape speculative verification produces, and compares each position's argmax
  and per-candidate logits against the direct record.

k=1 is the harness control: identical shapes must reproduce direct
bit-exactly (zero flips, zero shift). Any nonzero shift there would mean the
comparison itself is unsound.

## Board-parity details

- Prompt: the exact board prompt file
  [lifecycle-code-prompt.cpp](../reports/raw/2026-09-25-lifecycle/lifecycle-code-prompt.cpp)
  (the full ngram-mod.cpp source, 1194 bytes, sent raw via `--prompt-file` on
  the board). Copied to `E:\riscv-work\probe\prompt-ngram-mod.cpp` at build time.
- Model: Qwen3.5-2B Q4_0 (unsloth GGUF, same source as the board), F16 KV,
  greedy, 8 threads, ctx sized to prompt + n_predict.
- `ignore-eos` parity: n_predict is enforced exactly (no early stop).

## Usage

Build with [2026-09-28-build-probe.bat](2026-09-28-build-probe.bat) (MSVC x64
against the prebuilt upstream llama.cpp shared libs; outputs to
`E:\riscv-work\probe\`). Runtime file arguments must be ASCII paths.

```
verify-probe direct --model E:/riscv-work/models/Qwen3.5-2B-Q4_0.gguf \
  --prompt-file prompt-ngram-mod.cpp --n-predict 4096 --threads 8 \
  --traj traj-4096.jsonl
verify-probe verify --model ... --prompt-file ... --n-predict 4096 \
  --threads 8 --k K --traj traj-4096.jsonl --out v-kK.jsonl
```

Output JSONL per verified position: direct token/margin, verify argmax, the
verify logits at the two direct candidates (`v_at_d1`, `v_at_d2`), so the
per-candidate shift is `v_at_d1 - d1` regardless of which token won.

## Results (2026-09-28, Intel Ultra 7 255HX, upstream llama.cpp f916130)

All runs: Qwen3.5-2B Q4_0, greedy, 8 threads, 4096 generated tokens, F16 KV.
Raw records: [../reports/raw/2026-09-28-perfect-draft-probe/](../reports/raw/2026-09-28-perfect-draft-probe/).

### Harness control

k=1 over the full 4096-token ngram-mod trajectory: zero flips, per-candidate
shift max 1e-6 (print precision). Separate processes reproduce direct
bit-exactly, so the comparison is sound.

### Logit perturbation vs k (ngram-mod prompt)

| k | shift mean | p50 | p95 | max | tok/s | wall s |
|---|-----------|-----|-----|-----|-------|--------|
| 1 | 0.0       | 0.0 | 0.0 | 1e-6 | 22.7 | 180 |
| 2 | 0.152     | 0.116 | 0.418 | 0.952 | 36.8 | 111 |
| 3 | 0.152     | 0.116 | 0.418 | 0.952 | 46.3 | 88 |
| 4 | 0.152     | 0.116 | 0.418 | 0.952 | 62.2 | 66 |
| 8 | 0.151     | 0.112 | 0.422 | 1.106 | 68.0 | 60 |

Verify logits are **bitwise identical across k=2,3,4** at every position, and
k=8 differs at 4095/4096 positions. The M>1 result is therefore one fixed
kernel path (rows padded to a tile), independent of M within [2,4], crossing a
tiling boundary at 8. Mechanism located: upstream CPU repack routes M=1
through the gemv path and M>1 through the gemm path for the interleaved q4_0
weights — different accumulation order, rounding-scale logit noise of mean
~0.15 and max ~1.1 on this model. Same order as the board's measured flip
shifts (~0.06-0.07 at 2B/179 and 4B/303).

Note the decode-rate column: chunked verification is also where speculative
decoding gets its speed (2.7-3.0x per-token at k=4..8 here, draft quality
excluded by construction).

### Flip reproduction

Flips need a position where the top-2 margin is below the *relative* shift of
the two candidates. The board-parity ngram-mod trajectory is clean on x86
(min margin 0.181 over 4096 tokens, median 12.7) — no flips at any k. The two
sibling board prompts carry real near-tie density and flip at k=4:

| prompt | min margin | positions margin<1.0 | first flip | flips / 4096 |
|--------|-----------|----------------------|------------|--------------|
| ngram-mod | 0.181 | 1 | none | 0 |
| python-edit | 0.006 | 72 | 221 | 3 |
| prose | 0.0007 | 67 | 85 | 4 |

Flip rows (k=4): every flip has relative shift exceeding the direct margin —
python-edit at 221/396/601 (margins 0.048/0.036/0.006), prose at
85/99/164/169 (margins 0.0007-0.094). Example: python-edit 221, direct token
13784 ('Wait', 27.7733) vs verify token 9764 ('Let', 27.7612).

### Tie-guard sizing

Relative shift between the direct top-2 candidates, ngram-mod trajectory:

| k | p50 | p95 | p99.9 | max |
|---|-----|-----|-------|-----|
| 2 | 0.083 | 0.296 | 0.637 | 0.710 |
| 4 | 0.083 | 0.296 | 0.637 | 0.710 |
| 8 | 0.084 | 0.300 | 0.630 | 0.682 |

The shift scale is k-independent (same kernel path) — **epsilon = 0.75-1.0
covers the observed worst case** for this model/quant; it must be re-measured
per model and per board build. Guard trigger rate (python-edit margins):
0.9% of positions at eps=0.5, 1.8% at eps=1.0. Each trigger costs one
rollback + single-token M=1 re-decode, roughly trigger_rate x (1 - 1/k)
of verify throughput (~1.4% at k=4, eps=1.0) — within the <=5% budget with
margin to spare.

### Fix candidate

In speculative verification, after the M=k decode, any row whose top-2 margin
is below epsilon is decided by the M=1 path instead: remove that position's KV
cell, re-decode the preceding token alone (batch=1, the exact direct shape),
take its argmax, and continue the batched verification from there. This makes
every accepted token *defined* to equal the direct argmax at ties, at the cost
above. (Upstream KV API: llama_memory_seq_rm for the single cell.)

## Next steps

1. Implement the tie-guard on a real verification path (upstream server
   `--spec-type draft-mtp` or examples/speculative as the x86 proxy for the
   fork's integrated server).
2. Acceptance on x86: fixed spec vs direct, 4096 tokens, token-identical on
   all three prompts; perf cost <=5% measured paired.
3. 4B key verification (re-measure epsilon and flips on 4B Q4_0).
4. Port to the SpacemiT fork verify path for the board.

