# K1 channels-major SSM convolution and channel RVV

Status: repaired campaign **completed; the operator gate rejected the decode
regression**. The original, control, scalar, and RVV arms each pass 432
cases with identical output and history hashes. At 32 tokens, RVV graph time
falls 73.72%/78.93% for the 2B/4B shapes. At one token, it increases
69.00%/85.10%. Model state/fallback and cold inference timing were skipped.
See the [repaired results](../reports/2026-10-06-ssm-conv-repaired-results.md).

The historical initial screen **failed history write-back** after 6m 28s.
The original arm and candidate mode 0 each pass 432 numerical cases, and
channels-major mode 1 fails. RVV, operator timing, and model checks were
skipped. See the [measured results](../reports/2026-10-06-ssm-conv-rvv-results.md).
The [subsequent diagnosis](../reports/2026-10-06-ssm-history-diagnosis.md)
traces the failure to the fork's CPY transpose shortcut. The repaired native
graph passes 432 cases each in the control, scalar, and RVV modes, with
identical output and history hashes. The subsequent private model build
succeeded, and the full native gate passed. The operator no-regression gate
prevented model execution. Run: `k1-ssm-conv-20261006-073927` on SSH
`musepipro-wg`.

The first attempt, `k1-ssm-conv-20261006-072705`, stopped at compilation,
because the common graph context has no `model` member. Its evidence is
retained. The corrected guard uses `arch` and the actual CPU-only scheduler.
The second attempt, `k1-ssm-conv-20261006-073310`, compiled the operator and
the state builder but stopped on a protected field in the activation log.
The corrected log reports scheduler status without access to model
internals.

The repaired campaign `k1-ssm-conv-20261006-115459` was dispatched October 6
at 11:55 Asia/Singapore, and it completed in 7m 36s. Board and collector
exit statuses are 0, and all 97 collected artifact hashes are verified. The
30-minute follow-up is paused after this valid performance-gate rejection.
The [campaign state](../reports/raw/k1-ssm-conv-campaign.json) tracks the
current run and the repair attempts.

## Mechanism

The tested compiler already vectorizes the original convolution across taps.
It uses `vfmul.vv` and then `vfredosum.vs`. The new path vectorizes across
channels, and it retains a separate FP32 multiply and add for each tap, in
order. It uses contiguous activation loads and strided convolution-weight
loads. It introduces no weight conversion, no FMA, no tap reassociation,
and no double sum.

The channels-major projection is concatenated with a small converted
history. The new convolution returns the original `[channels, tokens,
sequences]` output. The code materializes the small transposed tail before
it copies persistent history back in the original time-major layout. This
order avoids the incompatible CPY transpose shortcut. The timing includes
this temporary history copy. The approach also avoids a conversion of the
whole microbatch to time-major, and it retains the state serialization
format. This candidate includes no SiLU fusion.

| `SPINE_K1_SSM_CONV` | Behavior |
| --- | --- |
| Unset / `0` | Original graph and original convolution |
| `1` | Channels-major graph, scalar-C convolution control |
| `2` | Channels-major graph, explicit RVV channel loop |

Only dense Qwen3.5 with an exclusively CPU scheduler and `n_rs_seq=0`
selects the graph change. Other architectures, GPU configurations, and RS
configurations retain the reference. The internal operator flag is used only
by the experimental CPU operator. It is not a public cross-backend API. On a
build without RVV, mode 2 uses the scalar implementation. K1 validation
requires the recorded RVV compile flags and instruction evidence.

## Build isolation

The source remains the preserved `a990751` benchmark copy. The controller
checks the frozen modified-source and runtime hashes, and it pins the
convolution and state source hashes from the October 6 audit. It rebuilds
only `ops.cpp`, `delta-net-base.cpp`, `qwen35.cpp`, and the already
qualified routing variant of `ime.cpp`. Then it relinks private
`libggml-cpu` and `libllama` overlays. The original server and all other
objects are reused. The runner rechecks the original source, library, and
object hashes at completion.

Every model arm uses routing mode 3, wide RVV attention, layout 0, four
workers, batch/microbatch 32, Q4_0 weights, F16 K/V, full prompts, and
direct decoding. The candidate remains opt-in. Production files are not
modified.

## Qualification stages

1. **Native graph:** 432 cases per arm. The arms are the original CPU
   library, candidate mode 0, channels-major mode 1, and RVV mode 2. Kernel
   widths 3/4/9; channels 1/7/8/9/31/129/1024/6144/8192; token counts
   1/3/32/33; one and two sequences; contiguous and strided projection
   inputs. Check exact FP32 outputs against an independent reference. Check
   exact history tails, input/output and scratch guards, immutable inputs,
   and repeat execution. All arm dumps must have the same hash. The measured
   model channels are 6144 and 8192.
2. **Operator timing:** six alternating-order blocks for modes 0, 1, and 2,
   both model channel counts, and M=1/32. Time the graph including history
   conversion, concat, and state copy, after warm-up. Each timed sample must
   exceed 200 ms. At least two shape gains must exceed 3% and the observed
   control range, with no clear required-shape regression.
3. **Actual model state:** for the winning mode, compare every vocabulary
   logit against mode 0 after forced chunks 3/29/1/3. Repeat the comparison
   after you clear the context state. Test both models, RS=0, and reference
   fallback RS=3. Require 16 exact comparisons per model. This stage
   validates the fallback. It does not validate RS rollback.
4. **Model timing:** cold ABBA control/candidate with identical prompts and
   64 capped outputs: 2B/256, 2B/2048, 4B/256, and 4B/2048. Stop the
   advancement if prefill fails the existing 3%/control-spread gate, or if
   decode clearly regresses. Require zero prompt reuse, full input counts,
   exact output IDs and text, and convolution/routing/attention activation
   markers.

The warm operator screen can overstate cache benefits. Capped timing cannot
establish useful-answer quality. A screen winner still needs separate
complete-answer confirmation before any adoption or default decision.

## Commands and recovery

```bash
python3 spacemit/bench/test-k1-ssm-runner.py
python3 spacemit/bench/start-k1-ssm-conv.py

# Recover artifact collection only; never restart inference for status checks.
python3 spacemit/bench/start-k1-ssm-conv.py --collect-only \
  --run-dir spacemit/reports/raw/k1-ssm-conv-20261006-073927
```

Board session: `k1_ssm_k1-ssm-conv-20261006-073927`.
Local collector: `k1_ssm_collect_verified_k1-ssm-conv-20261006-073927`.
The board holds the shared benchmark lock and a two-hour execution timeout.
Collection archives and verifies each board artifact. The
`collector-exit-status` marker reports collection success independently of
`exit-status` and of qualification. The runner hashes intermediate binary
dumps and then removes them. Summary hashes and exact checks remain. Local
staged source and header copies preserve the dispatched code.

The initial run remains complete with exit status 1. The repaired campaign
completed with exit status 0 and an inconclusive performance result. A
genuine operator regression needs no automatic rerun. A future prefill-only
candidate requires a new declared experiment and exact mixed
prefill/decode state checks. A repaired technical-failure rerun receives a
new 30-minute scheduled task, and the runner pauses the previous monitor
after the creation.

## Sources

The [downstream channels-major patch](https://github.com/AMD-Ecosystem/llama.cpp/pull/52)
informs the layout direction. This implementation is restricted to the
audited CPU configuration, and it adds its own RVV channel loop and state
gates. Published AMD results do not predict K1 gains. See the
[source audit](../reports/2026-10-06-next-infrastructure-methods.md) and the
[measured starting point](../reports/2026-10-06-k1-roofline-results.md).
