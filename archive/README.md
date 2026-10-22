# 归档清单

本页记录已归档材料和原位保留的历史材料。
历史材料的适用范围与使用限制由[历史材料说明](../spacemit/reports/HISTORY.md)负责。
现行要求与入口见[文档地图](../docs/README.md)。
日期：2026-10-22，Asia/Singapore。

## 归档规则

1. 归档材料只读。需要修改时先用 `git mv` 解档到主路径。
2. 每次归档同时更新全部引用链接。
3. `spacemit/reports/raw/` 与 `spacemit/reports/snapshots/` 中的记录保持原位。
4. 归档不删除材料。Git 历史保留原路径。
5. 归档原因、配置和检查记录写入[本次整理记录](../spacemit/reports/2026-10-22-project-file-organization.md)。

## 已归档材料

| 材料 | 原路径 | 现路径 | 归档原因 |
| --- | --- | --- | --- |
| `5ad05d8` 补丁应用工具 | `spacemit/apply-patches.sh` | [archive/patches-5ad05d8/apply-patches.sh](patches-5ad05d8/apply-patches.sh) | 现行交付使用 `a990751` 固定包和 `k1-final-20261013-r3` 单一构建 |
| `5ad05d8` 补丁 0001–0010 | `spacemit/patches/` | [archive/patches-5ad05d8/patches/](patches-5ad05d8/patches/) | 同上；补丁作为历史证据保留 |
| 2026-09-24 内核实验报告 TeX | `spacemit/reports/k1-llm-inference-optimizations-old.tex` | [archive/reports/k1-llm-inference-optimizations-2026-09-24.tex](reports/k1-llm-inference-optimizations-2026-09-24.tex) | 9 月内核实验导出；现行报告为 `SUBMISSION-REPORT` |
| 2026-09-24 内核实验报告 PDF | `spacemit/reports/k1-llm-inference-optimizations-old.pdf` | [archive/reports/k1-llm-inference-optimizations-2026-09-24.pdf](reports/k1-llm-inference-optimizations-2026-09-24.pdf) | 同上 |

补丁工具从自身目录读取 `patches/`。
解档后保持两个路径的相邻关系。

## 原位保留的历史材料

| 材料 | 位置 | 保留原因 |
| --- | --- | --- |
| 2026-09-21 早期报告 | [FINAL-REPORT.md](../FINAL-REPORT.md) | 两份活动文档按仓库根路径引用它；已导出快照也写出该路径 |
| `5ad05d8` 集成说明 | [spacemit/README.md](../spacemit/README.md) | 多份文档按 `../README.md` 引用它；本次只更新其中的补丁路径 |
| `a990751` 固定发布包 | [spacemit/release/](../spacemit/release/README.md) | 候选准备脚本直接读取 `manifest.json` 与补丁 |
| 独立候选补丁与清单 | [spacemit/experiments/local-candidate-patches/](../spacemit/experiments/local-candidate-patches/README.md) | 证据脚本按仓库路径读取这些清单 |
| 交付暂存目录 | [spacemit/final-release/submission/](../spacemit/final-release/submission/README.md) | `stage-submission.py` 写入该目录 |
| 本机实验工件 | [lab/](../lab/README.md) | 大部分由 Git 排除，路径见该目录说明 |
