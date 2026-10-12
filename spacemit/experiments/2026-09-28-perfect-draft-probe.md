# Perfect-draft verify probe (x86 batch-shape mechanism)

> Dated campaign snapshot. The measurements apply to the stated workload and date.
> The queued and running statements below are historical. Use the
> [current guide](../DOCS.md) and the [experiments index](README.md) for later results and current status.

Task A, step "x86 reproduction and mechanism location". This probe isolates the
mechanism behind the board's direct/MTP divergence from draft-model quality.
The 2B model has a first mismatch at generated index 179, and the 4B model at
303. The margins are in
[2026-09-27-resumed-measures.md](../reports/2026-09-27-resumed-measures.md).
The draft is the *direct greedy trajectory itself*.

> October 3 clarification: the proposed tie guard below is unimplemented. An
> observed epsilon does not guarantee identity for arbitrary input. Hybrid
> models also require recurrent-state restoration and attention KV rollback.
> See the [validation review](../reports/2026-10-03-validation-practice.md).

## Mechanism hypothesis

Speculative verification evaluates the draft's k tokens in one decode ubatch
(matmul M=k). Direct decoding evaluates one token per ubatch (M=1).
The CPU backend routes these requests through different GEMM/vec-dot paths.
The paths have a different accumulation order, so rounding-scale noise changes
the logits. At positions where the top-2 margin is below that noise, the argmax
flips. Then the outputs diverge permanently. Board evidence: at 2B/179 the MTP
(batched) top-2 margin was 0.0034 against direct 0.069. At 4B/303 the direct
margin was 0.0022, and the batched logits moved by ~0.06.

The probe measures this mechanism on x86 with a perfect draft:

- `direct` mode replays one-token ubatches (M=1) and records the trajectory
  and the top-2 logits at every step.
- `verify` mode re-evaluates that trajectory in chunks of k tokens (M=k). This
  shape is the shape that speculative verification produces. It compares each
  position's argmax and per-candidate logits against the direct record.

k=1 is the harness control. Identical shapes must reproduce direct
bit-exactly (zero flips, zero shift). Any nonzero shift would mean that the
comparison itself is unsound.

## Board-parity details

- Prompt: the exact board prompt file
  [lifecycle-code-prompt.cpp](../reports/raw/2026-09-25-lifecycle/lifecycle-code-prompt.cpp)
  (the full ngram-mod.cpp source, 1194 bytes, sent raw via `--prompt-file` on
  the board). The build copies it to
  `E:\riscv-work\probe\prompt-ngram-mod.cpp`.
- Model: Qwen3.5-2B Q4_0 (unsloth GGUF, same source as the board), F16 KV,
  greedy, 8 threads, ctx sized to prompt + n_predict.
- `ignore-eos` parity: n_predict is enforced exactly (no early stop).

## Usage

Build with [2026-09-28-build-probe.bat](2026-09-28-build-probe.bat). This file
uses MSVC x64 against the prebuilt upstream llama.cpp shared libs, and it
outputs to `E:\riscv-work\probe\`. Runtime file arguments must be ASCII paths.

```
verify-probe direct --model E:/riscv-work/models/Qwen3.5-2B-Q4_0.gguf \
  --prompt-file prompt-ngram-mod.cpp --n-predict 4096 --threads 8 \
  --traj traj-4096.jsonl
verify-probe verify --model ... --prompt-file ... --n-predict 4096 \
  --threads 8 --k K --traj traj-4096.jsonl --out v-kK.jsonl
```

Output JSONL per verified position: direct token/margin, verify argmax, and the
verify logits at the two direct candidates (`v_at_d1`, `v_at_d2`). The
per-candidate shift is `v_at_d1 - d1` for either winning token.

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
k=8 differs at 4095/4096 positions. Thus the M>1 result is one fixed
kernel path (rows padded to a tile). This path is independent of M within
[2,4] and crosses a tiling boundary at 8. Mechanism located: upstream CPU
repack routes M=1 through the gemv path and M>1 through the gemm path for the
interleaved q4_0 weights. The two paths have a different accumulation order and
rounding-scale logit noise of mean ~0.15 and max ~1.1 on this model. The order
is the same as the board's measured flip shifts (~0.06-0.07 at 2B/179 and
4B/303).

Note the decode-rate column. Chunked verification is also the source of the
speculative-decoding speed (2.7-3.0x per-token at k=4..8 here). The
construction excludes draft quality.

### Flip reproduction

A flip needs a position where the top-2 margin is below the *relative* shift of
the two candidates. The board-parity ngram-mod trajectory is clean on x86
(min margin 0.181 over 4096 tokens, median 12.7), so it has no flips at any k.
The two sibling board prompts have a real near-tie density and flip at k=4:

| prompt | min margin | positions margin<1.0 | first flip | flips / 4096 |
|--------|-----------|----------------------|------------|--------------|
| ngram-mod | 0.181 | 1 | none | 0 |
| python-edit | 0.006 | 72 | 221 | 3 |
| prose | 0.0007 | 67 | 85 | 4 |

Flip rows (k=4): every flip has a relative shift that exceeds the direct
margin. python-edit flips at 221/396/601 (margins 0.048/0.036/0.006), and
prose flips at 85/99/164/169 (margins 0.0007-0.094). Example: python-edit 221,
direct token 13784 ('Wait', 27.7733) against verify token 9764 ('Let', 27.7612).

### Tie-guard sizing

Relative shift between the direct top-2 candidates, ngram-mod trajectory:

| k | p50 | p95 | p99.9 | max |
|---|-----|-----|-------|-----|
| 2 | 0.083 | 0.296 | 0.637 | 0.710 |
| 4 | 0.083 | 0.296 | 0.637 | 0.710 |
| 8 | 0.084 | 0.300 | 0.630 | 0.682 |

The shift scale is k-independent (same kernel path). **epsilon = 0.75-1.0
covers the observed worst case** for this model/quant. You must re-measure it
per model and per board build. Guard trigger rate (python-edit margins):
0.9% of positions at eps=0.5, 1.8% at eps=1.0. Each trigger costs one
rollback and one single-token M=1 re-decode. The cost is about trigger_rate x
(1 - 1/k) of verify throughput (~1.4% at k=4, eps=1.0), within the <=5% budget
with margin to spare.

### Fix candidate

In speculative verification, after the M=k decode, the M=1 path decides any row
whose top-2 margin is below epsilon. Remove that position's KV cell, re-decode
the preceding token alone (batch=1, the exact direct shape), take its argmax,
and continue the batched verification from there. This step makes every
accepted token *defined* to equal the direct argmax at ties, at the cost above.
(Upstream KV API: llama_memory_seq_rm for the single cell.)

## Next steps

1. Implement the tie-guard on a real verification path (upstream server
   `--spec-type draft-mtp` or examples/speculative as the x86 proxy for the
   fork's integrated server).
2. Accept on x86: fixed spec against direct, 4096 tokens, token-identical on
   all three prompts; perf cost <=5% measured paired.
3. Verify the 4B key (re-measure epsilon and flips on 4B Q4_0).
4. Port to the SpacemiT fork verify path for the board.
