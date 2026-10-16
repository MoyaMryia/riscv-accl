# Qwen3.5 inference on the SpaceMiT K1

**Evidence cutoff: October 16, 2026, Asia/Singapore**

## Abstract

The project provides one K1 build for the two tested Qwen3.5 models.
Version `k1-final-20261013-r3` sets the selected parameters in the source.
Normal startup requires no performance flags or experiment variables.
The same build passes native checks, state checks, natural code answers, and relocation checks.

A new comparison uses the original vendor commit `5ad05d8` with two compatibility changes.
Both arms use identical Q4_0 weights, F16 cache, inputs, and output histories.
At 512/2048 input tokens, 2B decode throughput increases by 26.69%/34.68%.
The corresponding 4B increases are 62.17%/73.37%.
Each short shape has three pairs.
At 8192 input tokens, first-token time decreases by 51.77% on 2B and 65.17% on 4B.
Each long shape has only one pair.
These long observations do not establish repeat stability.
A separate capacity extension completes 12 matched requests at 16384 and 32768 inputs.
It uses the same production binaries and retains the ordinary context default of 12288.

The default is a balanced choice within a frozen search.
It is not a claim of a global optimum for all workloads.
Model origin, full conversion, long state correctness, and formal multi-turn quality retain acceptance gaps.
The [October 12 report](snapshots/2026-10-12/SUBMISSION-REPORT.pdf) preserves the previous report in full.
Its source and SHA-256 receipts remain available in the same snapshot directory.

## 1. Requirements and status

[Requirements.md](../../Requirements.md) is the sole current acceptance reference.
It requires both specified model bases, local inference, the vendor fork, matched improvements, and reproducible deployment materials.
It does not set an 8 GB device requirement or a 32k/64k context requirement.
The [gap report](2026-10-13-requirements-gap.md) retains the complete requirement map.

| Status | Verified scope or limit |
| --- | --- |
| Implemented | One complete source tree, one production build, fixed defaults, dependency checks, and a common launcher |
| Verified | Both current GGUF files run locally on K1 without a cloud API |
| Verified | 28 ordinary-default performance requests, 12 capacity-extension requests, and six complete natural code answers |
| Verified | Exact native dumps, 64 short state records, and two relocated model launches |
| Pending | Full official model origin and reproducible conversion of both final weights |
| Pending | Repeated long-context stability, long state acceptance, and the fixed multi-turn quality suite |
| Not implemented in this release | GPU acceleration, KV compression, and memory reduction through page allocation |

A passing Unicode code task does not establish general answer quality.
Earlier shared model errors remain relevant to formal quality acceptance.
No external competition submission is recorded.

## 2. Platform and software identity

The tested board is a MUSE-Pi-Pro with eight K1/X60 CPU cores.
Its nominal RAM is 16 GB; Linux reports approximately 15.528 GiB.
Recorded CPU frequency is 1.6 GHz.
Tests use an ordinary user in tmux under the common board lock.
No device permission or system change forms part of this campaign.

| Item | Identity |
| --- | --- |
| Final version | `k1-final-20261013-r3` |
| Vendor source | `a990751d55a4c54acf2bb77d44282c2093652359` |
| Complete source count | 3271 files |
| Final patch SHA-256 | `b03d193f618d8303ce563c4fcd4e03726a1f6f452dcc10ecedb1a7938550477b` |
| Server SHA-256 | `f254f174919c0a97ef34366f116705f6d22574cab4c2bfc39928c0d315b5bfbd` |
| Policy SHA-256 | `aeef14e2356dc9e33b1fc6ab595545eb67af81894f2c7cbd282948628453bdb0` |
| Compiler | GCC 14.2.0 with vendor IME support |
| Runtime | SPERT 0.6.2 and `libspine_tcm.so.3.0.1`; exact file hashes remain in the build receipt |
| Build | Release, IME1 enabled, OpenMP disabled, Native disabled, ZBA enabled, repack disabled, CPU backend |

The two model files use Q4_0 weights and Q4_0 embeddings.
Their names contain MTP tensors, but this release uses direct decode.
The package does not contain weights or vendor runtime libraries.
Exact dependencies do not yet have a unified public download archive.

| Model | GGUF SHA-256 |
| --- | --- |
| `Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf` | `56f0ddd90dfa0e2456af6cb4718ece419678d21a75d65e27353319b5e431a2fa` |
| `Qwen3.5-4B-MTP-Q4_0-embQ4_0-dv64k.gguf` | `0adf6cce5df53921606033c39a13fae2054543b78af0e7ff98860e86f078ac0f` |

The [default-build TCM trace](2026-10-16-final-release-tcm.md) verifies device access during two short requests.
Both servers load the fixed library, but hardware TCM access fails with `EACCES`.
No `/dev/tcm` mapping appears in 13 recorded process maps.
The shared barrier falls back to heap memory because `/dev/tcm_sync_mem` is absent.
The new user API rejects fake TCM; hardware read/write tests remain pending.
These traced requests establish no new performance or answer-quality result.

## 3. Original baseline and compatibility

The original source is `5ad05d8796cb094ee23a3a0152874f8a2b3060f8` from the SpaceMiT fork.
Its K1 build includes an IME2 file and fails.
The first compatibility change removes that single CMake source-list entry.
The resulting build cannot load the current reduced MTP draft head.
The second change loads `d2t` and uses the stored draft head width.
Neither arm enables the draft decoder.

Only the CMake list and the tensor loader in `src/models/qwen35.cpp` change.
The main output head, graph code, and all compute kernels retain their original bytes.
The compatibility patch SHA-256 is `2e8c40a4a056787380e37750bab005777580978d3d9a58d901e911dc12fe01d7`.
Both failures and both compatibility records remain in the evidence.
This is a compatibility baseline, not an unmodified binary.

Both arms use four threads, batch 32, context 12288, one slot, and F16 K/V.
They use the same compiler and runtime libraries.
The measured gain spans the original software state to the final software state.
It excludes historical weight quantization changes.
It does not isolate each individual kernel contribution.

## 4. Balanced default selection

The frozen search uses one verified RC1 build and 104 requests.
Four preflight requests check both models on the original and candidate builds.
The mask stage tests eight combinations on two models and two lengths, with two rounds.
The parameter stage tests 2/4 threads and batch sizes 16/32/64/128.
Four natural answers complete the selection checks.
The parameter stage retains four threads and batch 32.
No additional parameter confirmation or fallback is required.

The balanced score gives equal weight to both models, both lengths, TTFT, and decode time.
TTFT means client time to the first output token.
A difference within 3% of the lowest score is unresolved under the frozen rule.
This rule prefers fewer enabled candidates within that interval.
Mask 7 has the lowest observed score, 0.8904876472483813.
Mask 3 scores 0.915536301962804 and lies within that interval.
The rule therefore selects mask 3.
The selection score uses the same-build C0 control, not the original baseline.

| Compiled default | Value |
| --- | --- |
| Threads and batch threads | 4 / 4 |
| Batch and physical batch | 32 / 32 |
| Context and slots | 12288 / 1 |
| Cache and attention | F16 K/V, flash attention enabled |
| GPU layers and decode | 0, direct decode |
| Common paths | Wide RVV attention and IME route 3 enabled |
| Candidate mask | 3: B1-r2 and C1 enabled; C2-r2 disabled |

The launcher clears inherited experiment variables.
The measured final server receives only the model, alias, host, and port.
Runtime logs and server properties confirm the actual defaults.

## 5. Matched performance results

Performance requests use complete fixed input token lists and 65 fixed output tokens.
A single-token bias forces identical decode histories across versions.
This synthetic workload measures performance, not answer quality.
Natural answers use a separate request without this bias.

All requests have zero prompt-cache reuse.
The tests do not clear the operating-system file cache.
Each server starts before one request; server load time is outside request timing.
All 28 requests complete and generate exactly 65 tokens.
Input hashes, output tokens, full text, and finite timings match the protocol.

Short shapes use three pairs with alternating arm order.
Long shapes use one pair per model, with opposite order between models.
Tables show arithmetic means of per-request metrics.
Each slash separates original and final values, in that order.
Time reductions and throughput increases use different formulas.

| Model | Input | Pairs | TTFT, s | Server prefill, s | Prefill, tokens/s |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2B | 512 | 3 | 23.835 / 19.556 | 23.831 / 19.551 | 21.485 / 26.188 |
| 2B | 2048 | 3 | 115.639 / 81.633 | 115.632 / 81.626 | 17.712 / 25.090 |
| 2B | 8192 | 1 | 846.321 / 408.162 | 846.303 / 408.145 | 9.680 / 20.071 |
| 4B | 512 | 3 | 63.697 / 49.865 | 63.692 / 49.860 | 8.039 / 10.269 |
| 4B | 2048 | 3 | 354.441 / 213.497 | 354.434 / 213.490 | 5.778 / 9.593 |
| 4B | 8192 | 1 | 3234.172 / 1126.535 | 3234.155 / 1126.518 | 2.533 / 7.272 |

| Model | Input | Decode, tokens/s | Throughput change | Request, s | Peak RSS, MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2B | 512 | 3.387 / 4.292 | +26.69% | 43.031 / 34.714 | 2471.97 / 2469.73 |
| 2B | 2048 | 3.108 / 4.186 | +34.68% | 136.554 / 97.169 | 2472.29 / 2469.96 |
| 2B | 8192 | 2.239 / 3.600 | +60.82% | 875.359 / 426.221 | 2473.30 / 2471.19 |
| 4B | 512 | 1.315 / 2.133 | +62.17% | 113.128 / 80.346 | 5342.20 / 5340.58 |
| 4B | 2048 | 1.133 / 1.965 | +73.37% | 411.793 / 246.579 | 5342.20 / 5340.88 |
| 4B | 8192 | 0.724 / 1.485 | +104.91% | 3323.894 / 1170.324 | 5342.88 / 5342.11 |

| Model | Input | TTFT reduction | Prefill throughput change | Decode time reduction |
| --- | ---: | ---: | ---: | ---: |
| 2B | 512 | 17.96% | +21.89% | 21.04% |
| 2B | 2048 | 29.41% | +41.66% | 25.72% |
| 2B | 8192 | 51.77% | +107.35% | 37.82% |
| 4B | 512 | 21.72% | +27.74% | 38.34% |
| 4B | 2048 | 39.77% | +66.02% | 42.32% |
| 4B | 8192 | 65.17% | +187.09% | 51.20% |

RSS is resident memory for the server process.
The table reports the mean of sampled request peaks, with a 0.2 s sample interval.
It does not measure whole-machine memory or an instantaneous hardware peak.
The independent summary retains means, medians, minima, maxima, and each request identity.
No shape has a clear TTFT or decode-time regression under the frozen threshold.
The threshold is the greater of 3% and the full original-arm variation range.
Three samples do not establish a population confidence interval.
One long pair does not establish stability or complete long-context acceptance.

### 5.1. Final-build capacity extension

A separate frozen protocol extends capacity to 20480 or 36864 for actual 16384 or 32768 input tokens.
The final server receives only the capacity flag in addition to model, alias, host, and port.
Its optimization defaults remain unchanged; ordinary context remains 12288.
Both models complete all requests with 65 matched output tokens and zero prompt reuse.
The test uses two pairs per model at 16384 inputs and one pair per model at 32768 inputs.

| Model | Input | Pairs | TTFT, s | Prefill, s | Prefill, tokens/s |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2B | 16384 | 2 | 2829.646 / 1034.907 | 2829.614 / 1034.876 | 5.797 / 15.832 |
| 2B | 32768 | 1 | 10761.012 / 2983.902 | 10760.952 / 2983.845 | 3.045 / 10.982 |
| 4B | 16384 | 2 | 11256.195 / 2975.716 | 11256.164 / 2975.685 | 1.456 / 5.506 |
| 4B | 32768 | 1 | 42070.823 / 8866.022 | 42070.765 / 8865.966 | 0.779 / 3.696 |

| Model | Input | Decode, tokens/s | Request, s | Peak RSS, MiB |
| --- | ---: | ---: | ---: | ---: |
| 2B | 16384 | 1.659 / 2.914 | 2868.832 / 1057.226 | 2571.781 / 2569.617 |
| 2B | 32768 | 1.051 / 2.141 | 10822.886 / 3014.282 | 2767.641 / 2766.426 |
| 4B | 16384 | 0.490 / 1.117 | 11388.985 / 3033.905 | 5600.367 / 5600.611 |
| 4B | 32768 | 0.291 / 0.752 | 42294.220 / 8952.505 | 6117.164 / 6117.809 |

| Model | Input | TTFT reduction | Prefill gain | Decode gain |
| --- | ---: | ---: | ---: | ---: |
| 2B | 16384 | 63.43% | +173.13% | +75.59% |
| 2B | 32768 | 72.27% | +260.64% | +103.72% |
| 4B | 16384 | 73.56% | +278.29% | +128.23% |
| 4B | 32768 | 78.93% | +374.52% | +158.34% |

Each slash separates baseline and final means.
The independent check verifies 12 requests, 221 receipts, and 101704 memory samples.
Total controller time is 28.381 h; no request reaches its frozen time or memory limit.
RSS samples include server load and the request at a nominal 1 s interval.
The minimum sampled system availability is 11396.441 MiB; the maximum sampled server RSS is 6117.809 MiB.
These observations apply to the tested nominal 16 GB board.
They do not establish operation on an 8 GB device.

The [capacity-extension report](2026-10-16-ultralong-final-comparison.md) retains the complete protocol, sample ranges, archive identity, and repeat command.
This synthetic output does not test long semantic quality or long state correctness.
Two 16k pairs and one 32k pair do not establish general repeat stability.
The [previous report snapshot](snapshots/2026-10-14-final-r3/SUBMISSION-REPORT.pdf) retains the pre-supplement report and its original claims.

## 6. Correctness and failure records

The final build passes 104 route, 95 attention, 432 SSM, and 158 GDN native cases.
Its dump hashes match the verified RC1 reference.
Two models produce 64 bitwise-equal full-vocabulary state records.
These records cover RS 0/3, reset states, and prefixes 32/33/64/96 at context 4096.
They do not replace long state acceptance.

Six complete natural answers cover original, RC1 C0, and final arms for both models.
Each answer stops naturally and passes the frozen Unicode task's 106 functional checks.
All 2B answers have identical text and 508 output tokens.
The 4B original answer has 595 tokens and different text.
The RC1 and final 4B answers have identical text and 521 tokens.
Both 4B texts pass the functional checks.
This single task does not establish broad quality or multi-turn acceptance.

The r1 delivery passes numerical checks but fails an argument-parser GPU-default assertion.
The r2 delivery fixes that assertion but starts with four automatic slots.
The r3 source fixes the server default to one slot and receives a fresh complete build.
Both failed versions retain their source, build identities, and logs.
No manual performance flag bypasses these checks.

The previous full-combination regression remains 3.0220477% for 4B/2048/65 against B1 under its original conditions.
The new search does not erase that failed gate.
The IME scalar schedule remains excluded after its failed performance screen.
Earlier MTP output differences require direct decode when exact output identity is required.
GPU offload and page-allocation memory benefits remain unqualified.
Predictor errors and wide intervals remain separate from measured model results.

## 7. Deployment and evidence package

The committee directory `final-release` collects runnable code, a one-command deployment entry, official conversion scripts, deployment guides, performance reports, and a design document.
It includes complete production source and binaries, a fixed clean converter tree, model identity metadata, and separate evidence archives.
The same production binaries retain the original verified hashes.
The new entry creates tmux and acquires the fixed common lock before the server starts.
Both model launches pass identity, actual-default, lock, and health checks without an inference request.
The full official conversion remains untested; script availability does not establish a completed conversion.

```sh
bash deploy.sh /absolute/path/to/model.gguf
```

The committee manifest, checklist, and file hashes describe its complete contents and retained acceptance limits.
The [submission plan](../final-release/SUBMISSION-PLAN.md) maps all six requested materials.

The package contains the complete source, production binaries, fixed launcher, policy, dependency guide, and complete evidence.
Both models use the same binary and defaults.
Only the model path changes.
Run this command in tmux from the extracted version directory:

```sh
bash package/with-lock.sh python3 package/start.py --model /path/to/model.gguf
```

Use `--spert` and `--tcm` only when dependency locations differ.
These options select library locations, not performance profiles.
The launcher checks binary, model, and runtime hashes.
The final build passes two model launches after binary relocation.

The archive is `lab/final-default-20261013/release/k1-final-20261013-r3.tar.gz`.
Its external sidecar records the archive SHA-256 without a self-reference.
The evidence appendix records the final archive identity after the archive check.
The Git text view omits large dumps, thread samples, and binaries.
Strict receipt replay requires the retained complete archive.
The local check verifies 338 comparison receipts and 119 final-validation receipts.
The separate search check verifies 951 search receipts and 19 native receipts.

## 8. Historical evidence and remaining acceptance

The [October 12 snapshot](snapshots/2026-10-12/SUBMISSION-REPORT.pdf) retains all previous report claims and caveats.
Its [evidence appendix](snapshots/2026-10-12/SUBMISSION-EVIDENCE.md) and [receipts](snapshots/2026-10-12/receipts.json) preserve the previous record.
Historical percentages with different controls must not be added or multiplied.
The [October 7 release](2026-10-07-release-verification.md) and [October 13 RC1](2026-10-13-unified-release-candidate.md) remain comparison records.
The new r3 package supplies the fixed default delivery for this campaign.
