# Report source and export

This English export has an evidence cutoff of October 16, 2026, Asia/Singapore.
The October 12 source and exports remain in `snapshots/2026-10-12/`.
Use the [current gap report](2026-10-13-requirements-gap.md) for acceptance against [Requirements.md](../../Requirements.md).
Use the [result index](RESULTS.md) for later evidence and the [history guide](HISTORY.md) for snapshot limits.
The PDF contains the report and its evidence appendix.
The standalone TeX file contains the same text, tables, and references.
It does not require external images or a bibliography file.

## Source files

| File | Role |
| --- | --- |
| [SUBMISSION-REPORT.md](SUBMISSION-REPORT.md) | Editable technical report |
| [SUBMISSION-EVIDENCE.md](SUBMISSION-EVIDENCE.md) | Editable evidence appendix |
| [report-template.tex](report-template.tex) | Title page, fonts, page layout, and table style |
| [report-format.lua](report-format.lua) | Line breaks for long code paths and hashes |
| [build-report.py](build-report.py) | Repeatable export command |
| [SUBMISSION-REPORT.tex](SUBMISSION-REPORT.tex) | Generated standalone source |
| [SUBMISSION-REPORT.pdf](SUBMISSION-REPORT.pdf) | Generated review copy |

Edit the Markdown sources before each export.
Change the template if the page layout needs a change.
Regenerate both outputs after each source edit.
Direct TeX edits are possible, but the next export replaces them.

## Export commands

The exporter requires Python 3, Pandoc, and pdfLaTeX.
The template uses common TeX packages, including `fvextra`, `xurl`, and `fancyhdr`.
It does not require network access.
Run this command from the repository root.

```bash
python3 spacemit/reports/build-report.py
```

The command uses a temporary directory for compiler files.
It checks the compiler log for text outside page bounds and missing characters.
It copies the final TeX and PDF to this report directory.
Local report links become GitHub source links in the exported document.

Use this command to export only the standalone TeX source.

```bash
python3 spacemit/reports/build-report.py --tex-only
```

The standalone TeX file can also compile directly.
Run these commands from this directory.

```bash
pdflatex -interaction=nonstopmode -halt-on-error SUBMISSION-REPORT.tex
pdflatex -interaction=nonstopmode -halt-on-error SUBMISSION-REPORT.tex
pdflatex -interaction=nonstopmode -halt-on-error SUBMISSION-REPORT.tex
```

## Document update checks

1. Keep the evidence cutoff consistent across the report, appendix, and entry pages.
2. Keep each measured claim with its configuration, source, and limits.
3. Keep failed gates separate from pending checks.
4. Check local links after each document move.
5. Compile the standalone TeX source.
6. Inspect the PDF pages for table splits, clipped text, and page numbers.
7. Confirm that `raw/` files remain unchanged.

The exporter does not run a board experiment or update raw records.
The September [TeX report](k1-llm-inference-optimizations.tex) remains a historical export.
Its PDF is not the current report.
