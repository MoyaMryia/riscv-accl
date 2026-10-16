# Submission evidence appendix

Evidence cutoff: October 14, 2026, Asia/Singapore.
This appendix supports the [current report](SUBMISSION-REPORT.md).
The [October 12 appendix](snapshots/2026-10-12/SUBMISSION-EVIDENCE.md) retains the previous claim map in full.

## 1. Current claim map

| Claim | Records | Check and limit |
| --- | --- | --- |
| One compiled default for both models | [Policy](raw/k1-final-default-20261014-r3/final-r3/package/default-policy.json), [build receipt](raw/k1-final-default-20261014-r3/final-r3/build/build-receipt.json) | [Source generator](../bench/final-default/build_default.py); 3271 source files |
| Actual default startup | [Final validation](raw/k1-final-default-20261014-r3/final-validation-r3/summary.json), [2B log](raw/k1-final-default-20261014-r3/final-validation-r3/relocated-2B.server.log), [4B log](raw/k1-final-default-20261014-r3/final-validation-r3/relocated-4B.server.log) | [Default checker](../bench/final-default/effective.py); no performance flags or experiment variables |
| Original compatibility boundary | [Baseline receipt](raw/k1-final-default-20261014-r3/baseline-load-build/build-receipt.json), [compatibility patch](raw/k1-final-default-20261014-r3/baseline-load-compatibility.patch) | Original graph and compute kernels retain their bytes; MTP remains disabled |
| Frozen balanced selection | [Search summary](raw/k1-final-default-20261014-r3/search-r2/summary.json), [mask decision](raw/k1-final-default-20261014-r3/search-r2/masks-cycle-0.json), [independent check](raw/k1-final-default-20261014-r3/search-verification.json) | 104 requests; mask 3 selected under the frozen 3% tie rule |
| Matched original-to-final performance | [Comparison summary](raw/k1-final-default-20261014-r3/comparison-r3/summary.json), [independent summary](raw/k1-final-default-20261014-r3/final-verification.json) | 24 short requests and four long requests; each long shape has one pair |
| Natural answer quality | [2B final](raw/k1-final-default-20261014-r3/comparison-r3/answer-2B-final/answer.json), [4B final](raw/k1-final-default-20261014-r3/comparison-r3/answer-4B-final/answer.json) | 106 checks per answer; one Unicode task does not establish general quality |
| Native and default state identity | [Validation summary](raw/k1-final-default-20261014-r3/final-validation-r3/summary.json), [state records](raw/k1-final-default-20261014-r3/final-validation-r3/state.json) | 789 native cases and 64 short state records; long state remains pending |
| Preserved default failures | [r1 check](raw/k1-final-default-20261014-r3/r1-failure-verification.json), [r2 check](raw/k1-final-default-20261014-r3/r2-failure-verification.json) | Parser assertion and automatic four-slot startup remain in the evidence |
| Previous report preserved | [Snapshot receipts](snapshots/2026-10-12/receipts.json) | Original Markdown, TeX, PDF, template, filter, and export script retain their bytes |

## 2. Complete archive and compact text view

The archive path is `lab/final-default-20261013/release/k1-final-20261013-r3.tar.gz`.
The archive SHA-256 is `d2adc88afcb3996047b6e925d40b0bcc0054a449f9616238f698eee1c092855a`.
Its size is 1,503,683,264 bytes.
The internal check verifies 5331 file receipts, 12 symbolic links, and 28 binary hashes.
The [archive receipt](../final-release/archive-receipt.json) records the complete check result.
The [text evidence guide](raw/k1-final-default-20261014-r3/ARCHIVE.md) describes omitted large files.
A receipt that names an omitted dump cannot be fully replayed from Git alone.
The complete local evidence passes all recorded final checks.

## 3. Repeat the checks

Use the retained complete archive for strict receipt replay.
Run checks in tmux.
Board builds, inference, and tests must hold the fixed common lock.
Do not modify old raw records.

```sh
python3 spacemit/bench/final-default/verify_final.py \
  --board lab/final-default-20261013/board \
  --delivery lab/final-default-20261013/delivery-r3 \
  --version r3 --output /tmp/k1-final-verification-new.json
```

The output file must not exist.
The command above uses the complete local collection.
An extracted archive stores production binaries only in its root `build/bin/`.
Create the following internal link before a receipt replay from the extracted version directory:

```sh
ln -s ../../../build/bin evidence/final-r3/build/bin
python3 evidence/verification-tools/verify_final.py \
  --board evidence --delivery . --version r3 \
  --output /tmp/k1-extracted-verification-new.json
```

The link supplies the original evidence layout without a second production build.
The checker verifies request order, identities, actual defaults, token history, cold counts, and sampled RSS.
It preserves arithmetic means and observed ranges.
The frozen selection replay uses `verify_search.py` and the original selected policy.
The current package acceptance metadata differs from the pre-test manifest only in its acceptance status.
The [package receipt](raw/k1-final-default-20261014-r3/final-package-receipt.json) records that change.
Source, policy, and binary bytes retain their tested hashes.

## 4. Acceptance and historical limits

[Requirements.md](../../Requirements.md) controls acceptance.
The [gap map](2026-10-13-requirements-gap.md) retains official model origin, conversion, long-state, and multi-turn gaps.
The [previous stop audit](2026-10-12-combined-stop-audit.md) retains the 3.0220477% decode regression under its original conditions.
The [scalar schedule screen](2026-10-13-k1-live-inspect-and-scalar-schedule.md) retains its failed performance gate.
The [TCM audit](2026-10-13-k1-tcm-access.md) does not establish inference performance gains.
Historical evidence remains dated and must not be combined into an unmatched speedup.
