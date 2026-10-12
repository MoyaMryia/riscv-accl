#!/usr/bin/env python3
"""Export the project report and evidence appendix."""

import argparse
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


REPORTS = Path(__file__).resolve().parent
ROOT = REPORTS.parents[1]
GITHUB = "https://github.com/MoyaMryia/riscv-accl/blob/main/"


def source_text():
    parts = []
    for name in ("SUBMISSION-REPORT.md", "SUBMISSION-EVIDENCE.md"):
        text = (REPORTS / name).read_text()
        if name == "SUBMISSION-REPORT.md":
            text = text.split("\n", 1)[1]
            text = re.sub(r"^##", "#", text, flags=re.MULTILINE)
        else:
            text = text.replace("# Submission evidence appendix", "# Evidence appendix", 1)
            text = "\\clearpage\n\n" + text

        def link(match):
            label, target = match.groups()
            if "://" in target or target.startswith("#"):
                return match.group(0)
            path, separator, fragment = target.partition("#")
            relative = (REPORTS / path).resolve().relative_to(ROOT)
            url = GITHUB + relative.as_posix()
            if separator:
                url += "#" + fragment
            return f"[{label}]({url})"

        text = re.sub(r"\[([^\]]+)\]\(([^\s)]+)\)", link, text)
        parts.append(text)
    return "\n\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tex-only", action="store_true", help="Export only the TeX source.")
    args = parser.parse_args()
    required = ["pandoc"] + ([] if args.tex_only else ["pdflatex"])
    for command in required:
        if not shutil.which(command):
            raise SystemExit(f"Required command is unavailable: {command}")

    with tempfile.TemporaryDirectory(prefix="riscv-report-") as directory:
        work = Path(directory)
        source = work / "report.md"
        source.write_text(source_text())
        tex = work / "SUBMISSION-REPORT.tex"
        subprocess.run(
            [
                "pandoc", str(source), "--standalone", "--toc", "--toc-depth=2",
                "--top-level-division=section", "--from=markdown+raw_tex-smart",
                "--template=" + str(REPORTS / "report-template.tex"),
                "--lua-filter=" + str(REPORTS / "report-format.lua"),
                "--metadata=title:Qwen3.5 Inference on the SpaceMiT K1",
                "--metadata=subtitle:Infrastructure Optimization and Performance Evaluation",
                "--metadata=date:Evidence cutoff: October 12, 2026 (Asia/Singapore)",
                "--output=" + str(tex),
            ],
            check=True,
        )
        if not args.tex_only:
            for _ in range(3):
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex.name],
                    cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                )
                if result.returncode:
                    raise SystemExit(result.stdout)
            log = (work / "SUBMISSION-REPORT.log").read_text()
            if "Overfull" in log or "Missing character:" in log:
                raise SystemExit("The PDF has text outside its bounds or missing characters.\n" + log)
            shutil.copyfile(work / "SUBMISSION-REPORT.pdf", REPORTS / "SUBMISSION-REPORT.pdf")
        shutil.copyfile(tex, REPORTS / "SUBMISSION-REPORT.tex")
    print("Report export complete.")


if __name__ == "__main__":
    main()
