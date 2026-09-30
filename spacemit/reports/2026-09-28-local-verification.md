# Local verification of archived measurements: matrix reproduction, small-effect intervals, and 32k microbatch scaling

Date: 2026-09-28. Scope: analysis of records already archived under `reports/raw/` on a workstation, with no board access. Nothing here is a new board measurement; every number below is reproduced by a committed script from the archived JSONL/log files, and the commands are listed so each can be re-run.

Correction on 2026-09-30: the output audit now requires valid token/text hashes
and agreement across both comparison arms. Confidence intervals below now use
the precise Student t quantile at fractional Welch degrees of freedom. The
original rounded lookup changed whether the M4 pp128 interval included zero.

## The compact results matrix reproduces from raw records

[verify-results-matrix.py](../bench/verify-results-matrix.py) reparses the matrix table in [the resumed-measures report](2026-09-27-resumed-measures.md) and recomputes every TTFT, prefill, decode, end-to-end, and peak-RSS cell from the lifecycle records, including the two-launch means for the isolated 2k/8k arms and the weight-comparison arms. It also checks the exact-output claim per model and prompt length from the recorded token hashes.

```bash
python3 bench/verify-results-matrix.py reports/2026-09-27-resumed-measures.md reports/raw/2026-09-25-lifecycle
```

Result: all 21 rows reproduce within rounding tolerance (105 numeric cells, exits 0), and every row's launches share one complete 32-token token-hash, matching the reported `Exact`/`Complete` audit wording. The matrix is a faithful summary of the archived records; the script exits nonzero if a future report edit drifts from the archives.

## Corrected intervals for the current small-effect claims

[paired-stats.py](../bench/paired-stats.py) extracts launch-level values from the three archived record shapes and reports a Welch 95% interval for the arm difference. Applied to the effects currently quoted as 1.8–3.3%:

```bash
python3 bench/paired-stats.py reports/raw/2026-09-24-integrated/codex-q4-scale-base-1.jsonl \
  reports/raw/2026-09-24-integrated/codex-q4-scale-base-4.jsonl \
  --candidate reports/raw/2026-09-24-integrated/codex-q4-scale-scale-2.jsonl \
  reports/raw/2026-09-24-integrated/codex-q4-scale-scale-3.jsonl --select n_prompt=128
```

| Comparison | Arms (launches) | Point estimate | Welch 95% interval |
| --- | --- | ---: | ---: |
| M4 scale, 4B pp128 | base vs scale (2/2) | +3.34% (+0.303 tok/s) | +0.095 to +0.511 tok/s |
| M4 scale, 2B mapped MTP English | base vs scale (2/2) | +1.76% (+0.122 tok/s) | −0.031 to +0.275 tok/s |
| M4 scale, 2B mapped MTP Chinese | base vs scale (2/2) | +1.81% (+0.091 tok/s) | −0.024 to +0.206 tok/s |
| Windowed MTP 12k decode, 2B | full vs window (1/1) | +8.55% (+0.223 tok/s) | not estimable (single pair) |
| Windowed MTP 12k decode, 4B | full vs window (1/1) | +15.50% (+0.119 tok/s) | not estimable (single pair) |
| Q4_0 KV long output, 4B decode | F16 vs Q4_0 (1/1) | +13.77% (+0.161 tok/s) | not estimable (single pair) |

All three two-launch point estimates reproduce the values quoted in the
integrated-K1 report. The corrected M4 pp128 interval excludes zero under the
independent-launch Welch assumptions; the English and Chinese MTP intervals
include zero. The original script floored M4's df=1.311984 to one and used
12.706 instead of the precise critical value 7.385864, producing the overly
wide interval −0.055 to +0.661. Two launches per arm give an unstable variance
estimate, so this corrected interval is conditional evidence for that workload,
not a general performance recommendation. Repeat alternating launches before
adopting small effects. Single-pair rows remain point estimates.

For the two MTP rows, reproduce the corrected intervals with:

```bash
python3 bench/paired-stats.py reports/raw/2026-09-24-integrated/scale-mtp-abba.jsonl \
  --candidate reports/raw/2026-09-24-integrated/scale-mtp-abba.jsonl \
  --metric tps --select prompt=english --baseline-regex '^base-' --candidate-regex '^scale-'
```

Repeat with `--select prompt=chinese`. Confidence-interval calculation requires
SciPy on the workstation; this dependency does not apply to board inference.

## 32k prefill cost is dominated by a linear-in-context term

[summarize-microbatch-scaling.py](../bench/summarize-microbatch-scaling.py) converts the 1,022 progress lines in the [bounded 2B 32k run](raw/2026-09-25-lifecycle/2B-q4w-f16kv-32768-rvv1-bounded.log) into 1,020 per-32-token chunk times and fits chunk time against the processed-context position:

```bash
python3 bench/summarize-microbatch-scaling.py reports/raw/2026-09-25-lifecycle/2B-q4w-f16kv-32768-rvv1-bounded.log
```

The fit is `chunk_s ≈ 1.296 + 0.00012 × context_position` with R² = 0.9977. Bracket means reproduce the four points quoted in the long-prefill research report (1.38 s near 256 through 5.11 s near 32k) and add the share of each chunk that scales with context: about 2% at 256 tokens, 43% at 8k, 60% at 16k, and 75% at 32k. In other words, by 32k roughly three quarters of every chunk is context-proportional work, and the fixed per-chunk floor is about 1.3 s (40 ms per token) for this 2B, four-thread, RVV-enabled configuration. A linear term is consistent with attention/history traffic dominating the growth; attributing it to a specific operator still requires on-board profiling.

Linear extrapolation puts a 2B 65,536-token cold prefill near 10,500 s (about 2.9 hours), which would consume nearly the whole three-hour wall cap used by the bounded long-context script before any decode. The 64k feasibility gate should therefore expect a 2B 64k request to sit at the cap and a 4B 64k request to exceed it by roughly the 4B/2B prefill cost ratio; both projections assume the linear term stays linear beyond 32k, which the archived data does not test.

## Scope

These checks cover only archived records: the matrix rows, the small-effect pairs, and the single 32k RVV-on log. They add no board measurements and do not change any recommendation. The verification script is intended to gate future matrix edits; the statistics script is ready for the queued alternating-launch repeats; the scaling fit sharpens the long-prefill decision inputs until operator-level profiling replaces it.
