# Repaired SSM convolution: correct, batch benefit, decode regression

Run `k1-ssm-conv-20261006-115459` on SSH `musepipro-wg`, dispatched October 6,
2026 at 11:55 Asia/Singapore. Execution completed in **7m 36s**
(`455.7804` seconds). Board and collector exit statuses are both **0**;
an independent SSH check confirmed completion and that the board tmux session
ended. Baseline source/library/object preservation checks passed.

## Correctness and advancement

All **four arms pass 432 native graph cases each**: original CPU library,
private-library control, channels-major scalar, and channels-major RVV.
Convolution outputs and saved history are bitwise identical across all four
arms. The history-copy repair therefore clears the original failed gate.
Each case includes independent exact FP32/history checks, guards, strides,
immutable inputs and repeat execution.

The **72 operator samples** cover six alternating-order blocks, both actual
model channel counts (6144/8192), token counts 1/32 and modes 0/1/2. Each timed
sample exceeds 200 ms. These are warm native graph measurements including
history conversion, concat, convolution and history write-back. They are
neither standalone convolution-kernel timing nor full-model throughput.

| Model shape | Tokens | Control ms/call | Scalar ms/call | Scalar time change | RVV ms/call | RVV time change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2B, 6144 channels | 1 | 0.2313 | 0.4248 | **83.63% longer** | 0.3910 | **69.00% longer** |
| 2B, 6144 channels | 32 | 8.2171 | 3.1344 | 61.85% shorter | 2.1597 | **73.72% shorter** |
| 4B, 8192 channels | 1 | 0.3028 | 0.6268 | **107.00% longer** | 0.5605 | **85.10% longer** |
| 4B, 8192 channels | 32 | 13.4415 | 4.1198 | 69.35% shorter | 2.8327 | **78.93% shorter** |

Values are means of six samples per arm/shape. RVV graph throughput is
approximately **3.80x/4.75x** control at 32 tokens for the 2B/4B shapes.
The control timing ranges are 1.30%/1.97% (2B, tokens 1/32) and
3.43%/8.98% (4B, tokens 1/32). Both batch benefits and single-token regressions
exceed the applicable 3%/control-range thresholds.

Neither candidate satisfies the required no-regression gate. The controller
correctly records **inconclusive**, with reason `Operator gate failed; model
timing skipped.` This is a completed performance rejection, not a software
failure requiring automatic repair or a repeated identical benchmark.

| Later stage | Result |
| --- | --- |
| Full-model chunk/reset state checks | Skipped: operator gate rejected both candidates |
| RS=3 reference fallback checks | Skipped; no new fallback or rollback qualification |
| Cold prefill/decode versus route-3 control | **0 of at most 16 requests**, skipped |
| Useful-answer quality | Not measured by this campaign |

The corrected model libraries compiled, but the complete-model execution
gates did not run. Production defaults remain unchanged. There is no supported
end-to-end speedup or adoption claim.

## Interpretation and next candidate

The layout/RVV approach is promising for batch prefill and unsuitable as the
tested unconditional replacement. A **prefill-only dispatch**, retaining the
original single-token graph, is the next candidate to investigate. The
persistent history format is unchanged, which supports that design, but mixed
prefill/decode transitions still require exact model-state/reset checks.
Thresholds for token counts other than the measured 1/32 remain unmeasured.
No new benchmark was dispatched by this completion check.

The graph timing includes the history materialization workaround. Its share
of the decode overhead has not been isolated, so the measurements do not
establish which individual operation causes the regression.

## Collection and evidence

The archive checksum, exact archive member list, **all 97 artifact hashes**
inside the archive and in the local extracted files, and all staged code
hashes were independently verified. The matching native dump SHA256 is:

```text
7e154f0a52c2475581a62a64f549a17c7d342d46c55dae7adf05d09c05001c69
```

Archive SHA256:

```text
ea6a3c55602c1c536f671d5716780aa342f8f28ecc4e94b2585b0889a2d56dee
```

- [Summary and all timing samples](raw/k1-ssm-conv-20261006-115459/summary.json)
- [Operator records](raw/k1-ssm-conv-20261006-115459/operator.jsonl)
- [Build/runtime provenance](raw/k1-ssm-conv-20261006-115459/provenance.json)
- [Collection receipt](raw/k1-ssm-conv-20261006-115459/collection-receipt.json)
- [History-copy diagnosis](2026-10-06-ssm-history-diagnosis.md)
- [Protocol](../experiments/2026-10-06-ssm-conv-rvv.md)

The 30-minute follow-up is paused after reporting this completed result.
