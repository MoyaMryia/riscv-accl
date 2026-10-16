#!/usr/bin/env python3
"""Export the English and Chinese project reports to TeX and PDF."""

import argparse
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


REPORTS = Path(__file__).resolve().parent
ROOT = REPORTS.parents[1]
GITHUB = "https://github.com/MoyaMryia/riscv-accl/blob/main/"
TARGETS = {
    "en": {
        "sources": ("SUBMISSION-REPORT.md", "SUBMISSION-EVIDENCE.md"),
        "template": "report-template.tex",
        "engine": "pdflatex",
        "output": "SUBMISSION-REPORT",
        "title": "Qwen3.5 Inference on the SpaceMiT K1",
        "subtitle": "Infrastructure Optimization and Performance Evaluation",
        "date": "Evidence cutoff: October 16, 2026 (Asia/Singapore)",
    },
    "zh": {
        "sources": ("SUBMISSION-ZH.md",),
        "template": "report-template-zh.tex",
        "engine": "xelatex",
        "output": "SUBMISSION-ZH",
        "title": "面向进迭时空 K1 的 Qwen3.5 本地推理优化",
        "subtitle": "基础设施优化与性能评估",
        "date": "证据截止：2026-10-16（Asia/Singapore）",
    },
}


def link(match):
    """Replace a local report link with its GitHub source link."""
    label, target = match.groups()
    if "://" in target or target.startswith("#"):
        return match.group(0)
    path, separator, fragment = target.partition("#")
    url = GITHUB + (REPORTS / path).resolve().relative_to(ROOT).as_posix()
    if separator:
        url += "#" + fragment
    return f"[{label}]({url})"


def source_text(names):
    """Join the sources. The first source gives the body, later sources are appendices."""
    parts = []
    for index, name in enumerate(names):
        text = (REPORTS / name).read_text()
        if index == 0:
            text = text.split("\n", 1)[1]
            text = re.sub(r"^##", "#", text, flags=re.MULTILINE)
        else:
            text = text.replace("# Submission evidence appendix", "# Evidence appendix", 1)
            text = "\\clearpage\n\n" + text
        parts.append(re.sub(r"\[([^\]]+)\]\(([^\s)]+)\)", link, text))
    return "\n\n".join(parts)


def export(target, tex_only):
    """Write the TeX file and, if requested, the PDF file for one target."""
    with tempfile.TemporaryDirectory(prefix="riscv-report-") as directory:
        work = Path(directory)
        source = work / "report.md"
        source.write_text(source_text(target["sources"]))
        tex = work / (target["output"] + ".tex")
        subprocess.run(
            [
                "pandoc", str(source), "--standalone", "--toc", "--toc-depth=2",
                "--top-level-division=section", "--from=markdown+raw_tex-smart",
                "--template=" + str(REPORTS / target["template"]),
                "--lua-filter=" + str(REPORTS / "report-format.lua"),
                "--metadata=title:" + target["title"],
                "--metadata=subtitle:" + target["subtitle"],
                "--metadata=date:" + target["date"],
                "--output=" + str(tex),
            ],
            check=True,
        )
        if not tex_only:
            for _ in range(3):
                result = subprocess.run(
                    [target["engine"], "-interaction=nonstopmode", "-halt-on-error", tex.name],
                    cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                )
                if result.returncode:
                    raise SystemExit(result.stdout)
            log = (work / (target["output"] + ".log")).read_text()
            if "Overfull" in log or "Missing character:" in log:
                raise SystemExit("The PDF has text outside its bounds or missing characters.\n" + log)
            pdf = target["output"] + ".pdf"
            shutil.copyfile(work / pdf, REPORTS / pdf)
        shutil.copyfile(tex, REPORTS / tex.name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tex-only", action="store_true", help="Export only the TeX source.")
    parser.add_argument("--lang", choices=("en", "zh", "all"), default="all",
                        help="Report language to export.")
    args = parser.parse_args()
    names = ("en", "zh") if args.lang == "all" else (args.lang,)
    targets = [TARGETS[name] for name in names]
    required = {"pandoc"} | (set() if args.tex_only else {t["engine"] for t in targets})
    for command in sorted(required):
        if not shutil.which(command):
            raise SystemExit(f"Required command is unavailable: {command}")
    for target in targets:
        export(target, args.tex_only)
    print("Report export complete: " + ", ".join(names) + ".")


if __name__ == "__main__":
    main()
