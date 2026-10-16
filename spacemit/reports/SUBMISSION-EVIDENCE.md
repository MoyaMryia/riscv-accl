# Submission evidence appendix

Evidence cutoff: October 16, 2026, Asia/Singapore.
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

## 5. Final-build capacity supplement

The [supplement report](2026-10-16-ultralong-final-comparison.md) separates explicit capacity extension from ordinary default startup.
The [frozen protocol](raw/k1-ultralong-20261016-r1/PROTOCOL.md) fixes actual 16384/32768 inputs and 65 outputs.
The [independent check](raw/k1-ultralong-20261016-r1/verification-v2.json) verifies all 12 requests, 221 receipts, and 101704 memory samples.
The [controller summary](raw/k1-ultralong-20261016-r1/board/k1-ultralong-20261014-r1/results/summary.json) records completion and no failures.
The [archive receipt](raw/k1-ultralong-20261016-r1/archive-receipt.json) records the separate supplement archive and file checks.
Its complete layout supports an independent replay without the original local directory paths.
The production archive and all previous raw records retain their original bytes.
The [pre-update snapshot receipt](snapshots/2026-10-14-final-r3/snapshot-receipt.json) fixes the previous report set.

The supplement uses two pairs at 16384 inputs and one pair at 32768 inputs for each model.
Only allocated capacity changes; optimization defaults and binaries retain their original identity.
The ordinary context default remains 12288.
Fixed-output completion does not establish long semantic quality, long state correctness, or formal multi-turn acceptance.

## 6. Committee deployment entry

The [entry checks](raw/k1-committee-entry-20261016-r1/smoke-summary.json) cover both fixed models.
The [receipts](raw/k1-committee-entry-20261016-r1/receipts.json) retain launch commands, effective defaults, properties, health replies, and common-lock records.
The new entry sends no inference request.
The first upload fails because scp rejects the directory name `.`; no model starts.
Its log and exit status remain in the same evidence directory.
A second upload uses explicit filenames and both model checks pass.

## 7. Default-build TCM investigation

The [TCM report](2026-10-16-final-release-tcm.md) separates library access, hardware permissions, and buffer-copy routing.
The [independent check](raw/k1-tcm-final-release-20261016-r1/verification.json) verifies two completed short requests and 13 process maps.
Both server processes fail to open `/dev/tcm` with `EACCES`; neither maps that device.
The [source check](raw/k1-tcm-final-release-20261016-r1/source-audit.json) matches four TCM-related files to the fixed vendor source.
Ten local fixture tests pass for the [user API](../tcm/README.md).
The board API rejects hardware allocation under the current permissions.
Real hardware read/write and inference gains remain pending.
The original production binaries and prior raw records retain their bytes.
