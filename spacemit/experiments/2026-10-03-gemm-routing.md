# Production GEMM staging versus direct memory

Status: completed with exit status 0; modes 1 and 2 qualified.
All required model stages and independent collection verification passed.
Experimental and opt-in; confirmation before default adoption remains.
Run: `k1-gemm-routing-20261003-005740`.

## Evidence and scope

The October 2 production attribution found staging copies at 9.55% / 9.93%
of summed prefill worker elapsed time, with non-null 128 KiB SPERT buffers.
The separately loaded TCM API reports unavailable, fake and zero geometry.
Neither observation proves SPERT buffer placement. Attribution includes waits
and timer overhead and is not a prediction of removable model latency.

Earlier board reports (`~/Projects/llm-bench/COPY-CURVE-REPORT.md` and
`PLAN-tcm-dbuf.md`) rejected larger copy chunks and barrier removal under an
older real-TCM setup. That setup reported decode gains from real TCM. The
[OpenSolvers K1 study](https://www.opensolvers.com/apps/llamacpp.html) instead
found staging harmful on another board. These differing conditions justify
testing the existing direct-memory path on the current verified runtime.
No permissions, kernel modules or clock settings are changed.

The generator modifies only the buffer selection in production Q4_0
`forward_mul_mat`, with K32/N16 traits, IME1, K divisible by 32 and N divisible
by 16. Setting the selected buffer to null dispatches the existing direct
branch. Activation quantization, packed weight data and kernel arithmetic
remain unchanged. Other quantizations and traits retain their routing.

| `SPINE_K1_GEMM_ROUTE` | Policy |
| --- | --- |
| 0 or unset/invalid | Original staging |
| 1 | Bypass only when M > 1 (prefill) |
| 2 | Bypass only when M = 1 (single-row/decode) |
| 3 | Bypass both; numerical checks only |

All candidate code stays in an isolated CPU library. The original source,
objects and deployed server remain intact. Keep full prompts, both required
Qwen3.5 models, Q4_0 weights, F16 KV, four workers, batch/microbatch 32, direct
decoding and the already accepted wide attention/layout 0.

## Predeclared protocol

1. Verify baseline source/object/library/runtime/model hashes. Compile one
   `ime.cpp.o` and link the isolated library using original build flags.
2. Execute real GGML `MUL_MAT` graphs with SpaceMiT buffer allocation and
   weight repacking. Compare 104 cases per arm against the original library
   and generated modes 0/1/2/3. Require bitwise equality, finite fully written
   output, unchanged activation/packed weights and output/workspace guards.
   Cover M1/2/3/4/7/16/32, small K32/64/256 and actual K2048/2560/6144/9216,
   N16/32/64/128 and Q8 fallback cases. Require phase-specific dispatch logs
   and real non-null staging buffers in the control.
3. Screen production operators, including activation quantization and SPERT
   synchronization: both models' embedding-to-FFN and FFN-to-embedding shapes,
   M1 and M32. Six balanced blocks compare original library, generated mode 0
   and the phase-specific bypass. Use at least 100 ms timed work per arm,
   after initialization. Repeated weights are not cold model inference.
4. Each phase needs at least two of four shapes with reduction greater than
   both 3% and the full control range, no clear candidate regression and no
   clear generated-control regression against the original library.
5. Eligible prefill mode 1 receives cold ABBA 2B/512 and 4B/512 tests. Only
   when both pass the same gate run 2B/2k and 4B/1k. One output token measures
   prefill; it does not establish decode or answer quality.
6. Independently eligible single-row mode 2 receives cold ABBA requests for
   each model: full 256-token prompt, 64 generated tokens, ignore EOS. Require
   every requested token, equal input/text/token hashes, uncached counts,
   positive timings and correct per-phase activation. Both models must pass
   the decode-time gate, without a clear prefill regression. This is sustained
   bounded decode throughput, not complete-answer quality.
7. A qualifying mode remains opt-in pending independent confirmation on long
   context and complete answers. No candidate becomes the default here.

Board execution and local verified collection run in tmux. The board job
uses the shared lock, waits at most 12 hours for it, and has a separate one-hour
execution budget after lock acquisition. Original sources and unrelated jobs
must remain intact. All artifact hashes are verified during collection.

## Commands

```bash
python3 spacemit/bench/start-k1-gemm-routing.py
python3 spacemit/bench/start-k1-gemm-routing.py --collect-only \
  --run-dir /absolute/path/to/existing/run
python3 spacemit/bench/test-k1-gemm-routing.py
python3 spacemit/bench/test-k1-fast-test.py
python3 spacemit/bench/verify-k1-gemm-routing.py /absolute/path/to/completed/run
```

The final verifier rechecks artifact hashes, workload/runtime configuration,
phase activation and every required model stage. It recalculates operator and
model gates from individual records instead of accepting the stored summary.

## Completed results

Run `k1-gemm-routing-20261003-005740` completed with exit status **0** in
**38.16 minutes**. Both phase-specific modes qualified. The comparison is
against the **current optimized baseline**, including accepted wide attention
and layout 0. Each comparison contains four cold ABBA requests, two per arm.

### Prefill: mode 1, M > 1

Full input prompts and one output token:

| Model / full prompt | Control mean prefill | Bypass mean prefill | Time reduction | Control range |
| --- | ---: | ---: | ---: | ---: |
| 2B / 512 tokens | 22.052917 s | 20.625322 s | 6.47% | 0.05% |
| 4B / 512 tokens | 56.740043 s | 52.304415 s | 7.82% | 0.17% |
| 2B / 2048 tokens | 92.634959 s | 86.709042 s | **6.40%** | 0.27% |
| 4B / 1024 tokens | 115.551047 s | 106.596561 s | **7.75%** | 0.26% |

### Single-row/decode: mode 2, M = 1

Full 256-token input prompts and all 64 requested output tokens captured:

| Model | Control mean decode | Bypass mean decode | Time reduction | Throughput, control → bypass | Control range |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2B | 17.016656 s | 14.566911 s | **14.40%** | 3.76 → 4.39 token/s | 0.59% |
| 4B | 43.553046 s | 31.087887 s | **28.62%** | 1.47 → 2.06 token/s | 1.75% |

Mode 2 can also affect single-row work during prefill. Neither model showed
clear prefill regression in these requests. All six model comparisons passed
the predeclared time-reduction gate. These are engineering screens with two
samples per arm; they do not establish a population confidence interval.
Mode 3 passed numerical checks only; combined-mode model performance was not
tested, and the separate gains must not be added together.

### Verification and evidence boundary

- All **24 model requests** passed matching input and output text/token hashes,
  full requested token counts, uncached counts and actual phase activation.
  Models, Q4_0 weights, F16 KV, four workers and batch/microbatch 32 were verified.
- **104 native production graph cases per arm**, across five arms, gave identical
  output hashes, unchanged input/packed weights and intact output/workspace guards.
- **144 operator records**, six balanced blocks across eight production shapes,
  qualified every candidate shape. Generated mode 0 had no clear regression
  against the original library. Operator gains are not model speed estimates.
- **236 collected artifact hashes** passed an independent verifier, which also
  recalculated all required gates from individual records. End-of-run hashes
  matched all **46 baseline source/object/build files** checked.
- This run's lifecycle environment allowlist omitted `SPINE_K1_GEMM_ROUTE`.
  Mandatory actual kernel markers independently prove each arm's mode,
  eligibility and bypass. The verifier checks those markers and rejects a
  conflicting environment value when recorded. Future runs also capture the
  routing environment field; original raw records were preserved.

Evidence: [raw summary](../reports/raw/k1-gemm-routing-20261003-005740/summary.json),
[independent verification](../reports/raw/k1-gemm-routing-20261003-005740/verification.json),
[collection receipt](../reports/raw/k1-gemm-routing-20261003-005740/collection-receipt.json),
[baseline preservation](../reports/raw/k1-gemm-routing-20261003-005740/baseline-preservation-check.json).

The candidate remains **isolated and opt-in**. Independent long-context and
complete-answer confirmation is required before default adoption. The
64-token decode test establishes bounded throughput and exact agreement for
these outputs; it does not establish complete-answer quality.
