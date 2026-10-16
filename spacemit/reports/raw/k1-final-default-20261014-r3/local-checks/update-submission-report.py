"""用最终匹配对照更新综合报告与证据附录。"""
import json
from pathlib import Path
root=Path(__file__).resolve().parent
reports=Path('spacemit/reports')
rows=json.loads((root/'final-verification.json').read_text())['measurements']
def pair(r,m,scale=1,digits=3):return ' / '.join(f"{r['aggregate'][a][m]['mean']/scale:.{digits}f}" for a in ('baseline','final'))
prefill='\n'.join(f"| {r['model']} | {r['input_tokens']} | {r['pairs']} | {pair(r,'ttft_ms',1000)} | {pair(r,'prompt_ms',1000)} | {pair(r,'prefill_tps')} |" for r in rows)
decode='\n'.join(f"| {r['model']} | {r['input_tokens']} | {pair(r,'decode_tps')} | {r['final_change_percent']['decode_tps']:+.2f}% | {pair(r,'wall_s')} | {pair(r,'peak_rss_kib',1024,2)} |" for r in rows)
gains='\n'.join(f"| {r['model']} | {r['input_tokens']} | {-r['final_change_percent']['ttft_ms']:.2f}% | {r['final_change_percent']['prefill_tps']:+.2f}% | {-r['final_change_percent']['decode_ms']:.2f}% |" for r in rows)
text=f'''# Qwen3.5 inference on the SpaceMiT K1

**Evidence cutoff: October 14, 2026, Asia/Singapore**

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
| Verified | 28 matched performance requests and six complete natural code answers |
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

Runtime fallback does not prove that inference buffers use real TCM.
The earlier sudo device audit does not establish a TCM bandwidth or inference gain.
This campaign does not add such a claim.

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
{prefill}

| Model | Input | Decode, tokens/s | Throughput change | Request, s | Peak RSS, MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
{decode}

| Model | Input | TTFT reduction | Prefill throughput change | Decode time reduction |
| --- | ---: | ---: | ---: | ---: |
{gains}

RSS is resident memory for the server process.
The table reports the mean of sampled request peaks, with a 0.2 s sample interval.
It does not measure whole-machine memory or an instantaneous hardware peak.
The independent summary retains means, medians, minima, maxima, and each request identity.
No shape has a clear TTFT or decode-time regression under the frozen threshold.
The threshold is the greater of 3% and the full original-arm variation range.
Three samples do not establish a population confidence interval.
One long pair does not establish stability or complete long-context acceptance.

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

Official model origin and complete conversion remain pending.
The specified long-context and multi-turn acceptance checks remain incomplete.
The auxiliary performance evaluator remains bounded by its documented prediction errors.
The new matched speed results do not close these unrelated gaps.
'''
(reports/'SUBMISSION-REPORT.md').write_text(text)
e='raw/k1-final-default-20261014-r3'
appendix=f'''# Submission evidence appendix

Evidence cutoff: October 14, 2026, Asia/Singapore.
This appendix supports the [current report](SUBMISSION-REPORT.md).
The [October 12 appendix](snapshots/2026-10-12/SUBMISSION-EVIDENCE.md) retains the previous claim map in full.

## 1. Current claim map

| Claim | Records | Check and limit |
| --- | --- | --- |
| One compiled default for both models | [Policy]({e}/final-r3/package/default-policy.json), [build receipt]({e}/final-r3/build/build-receipt.json) | [Source generator](../bench/final-default/build_default.py); 3271 source files |
| Actual default startup | [Final validation]({e}/final-validation-r3/summary.json), [2B log]({e}/final-validation-r3/relocated-2B.server.log), [4B log]({e}/final-validation-r3/relocated-4B.server.log) | [Default checker](../bench/final-default/effective.py); no performance flags or experiment variables |
| Original compatibility boundary | [Baseline receipt]({e}/baseline-load-build/build-receipt.json), [compatibility patch]({e}/baseline-load-compatibility.patch) | Original graph and compute kernels retain their bytes; MTP remains disabled |
| Frozen balanced selection | [Search summary]({e}/search-r2/summary.json), [mask decision]({e}/search-r2/masks-cycle-0.json), [independent check]({e}/search-verification.json) | 104 requests; mask 3 selected under the frozen 3% tie rule |
| Matched original-to-final performance | [Comparison summary]({e}/comparison-r3/summary.json), [independent summary]({e}/final-verification.json) | 24 short requests and four long requests; each long shape has one pair |
| Natural answer quality | [2B final]({e}/comparison-r3/answer-2B-final/answer.json), [4B final]({e}/comparison-r3/answer-4B-final/answer.json) | 106 checks per answer; one Unicode task does not establish general quality |
| Native and default state identity | [Validation summary]({e}/final-validation-r3/summary.json), [state records]({e}/final-validation-r3/state.json) | 789 native cases and 64 short state records; long state remains pending |
| Preserved default failures | [r1 check]({e}/r1-failure-verification.json), [r2 check]({e}/r2-failure-verification.json) | Parser assertion and automatic four-slot startup remain in the evidence |
| Previous report preserved | [Snapshot receipts](snapshots/2026-10-12/receipts.json) | Original Markdown, TeX, PDF, template, filter, and export script retain their bytes |

## 2. Complete archive and compact text view

The archive path is `lab/final-default-20261013/release/k1-final-20261013-r3.tar.gz`.
The archive sidecar and final archive check supply its final identity.
The [text evidence guide]({e}/ARCHIVE.md) describes omitted large files.
A receipt that names an omitted dump cannot be fully replayed from Git alone.
The complete local evidence passes all recorded final checks.

## 3. Repeat the checks

Use the retained complete archive for strict receipt replay.
Run checks in tmux.
Board builds, inference, and tests must hold the fixed common lock.
Do not modify old raw records.

```sh
python3 spacemit/bench/final-default/verify_final.py \\
  --board lab/final-default-20261013/board \\
  --delivery lab/final-default-20261013/delivery-r3 \\
  --version r3 --output /tmp/k1-final-verification-new.json
```

The output file must not exist.
The checker verifies request order, identities, actual defaults, token history, cold counts, and sampled RSS.
It preserves arithmetic means and observed ranges.
The frozen selection replay uses `verify_search.py` and the original selected policy.
The current package acceptance metadata differs from the pre-test manifest only in its acceptance status.
The [package receipt]({e}/final-package-receipt.json) records that change.
Source, policy, and binary bytes retain their tested hashes.

## 4. Acceptance and historical limits

[Requirements.md](../../Requirements.md) controls acceptance.
The [gap map](2026-10-13-requirements-gap.md) retains official model origin, conversion, long-state, and multi-turn gaps.
The [previous stop audit](2026-10-12-combined-stop-audit.md) retains the 3.0220477% decode regression under its original conditions.
The [scalar schedule screen](2026-10-13-k1-live-inspect-and-scalar-schedule.md) retains its failed performance gate.
The [TCM audit](2026-10-13-k1-tcm-access.md) does not establish inference performance gains.
Historical evidence remains dated and must not be combined into an unmatched speedup.
'''
(reports/'SUBMISSION-EVIDENCE.md').write_text(appendix)
