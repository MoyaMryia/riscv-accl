# 历史材料的适用范围

[Requirements.md](../../Requirements.md) 是唯一现行验收依据。
已归档材料与原位保留的历史材料见[归档清单](../../archive/README.md)。
历史要求、实验门槛和过去的用户限定只解释当时结果。
当前部署、结果和验收缺口分别见[部署入口](../DEPLOYMENT.md)、[结果索引](RESULTS.md)和[缺口报告](2026-10-13-requirements-gap.md)。

| 保留材料 | 日期或源码边界 | 使用限制 |
| --- | --- | --- |
| [根目录早期报告](../../FINAL-REPORT.md) | 2026-09-21 短输入实验，含后续注记 | 历史“最终”标题不表示现行验收完成。不同量化的旧文档数值不是匹配基线。 |
| [早期部署说明](../README.md)、[补丁工具](../../archive/patches-5ad05d8/apply-patches.sh)、`../../archive/patches-5ad05d8/patches/` | 从 `5ad05d8` 开始的补丁栈 | 与 `a990751` 发布包使用不同的干净源码目录。保留 MTP 精确性限制。 |
| [9 月 TeX](../../archive/reports/k1-llm-inference-optimizations-2026-09-24.tex)、[9 月 PDF](../../archive/reports/k1-llm-inference-optimizations-2026-09-24.pdf) | 2026-09-24 内核实验 | 不包含后续长上下文、质量和矩阵路由结果。 |
| [旧英文报告快照](snapshots/2026-10-12/SUBMISSION-REPORT.pdf)、[文件收据](snapshots/2026-10-12/receipts.json) | 2026-10-12 导出快照 | 保留原 Markdown、TeX、PDF 与工具字节。主入口已更新为 2026-10-22；现行判定使用根目录要求与当前证据。 |
| [10 月 11 日进度](2026-10-11-project-progress.md)、[版本比较](2026-10-11-original-current-comparison.md) | 三项全开组合停止前 | 后续停止结论见 [10 月 12 日复核](2026-10-12-combined-stop-audit.md)。 |
| [10 月 12 日差距核对](2026-10-12-current-requirements-gap.md) | 当日要求核对 | 当前逐项缺口由 [10 月 13 日报告](2026-10-13-requirements-gap.md)接续。 |
| [实验协议目录](../experiments/README.md) | 各协议规定的版本与门槛 | 协议存在不表示测试已运行或已通过。必须查对应结果。 |
| `lab/` | 本机实验目录，大部分由 Git 排除 | 路径存在不表示新克隆可用。必须核对来源、收据及保留的大文件。 |
| `raw/` | 原始日志、逐字回答和机器摘要 | 不改写、不移动。原 SHA-256 收据仍用于原文件。 |

英文导出中的 1 词元/s、8 GB 或旧覆盖项不能增加现行硬性要求。
现行要求没有指定 32k／64k，也没有要求 ARM／x86 性能对照。
TCM 的普通用户不可用状态只描述该用户进程。
[sudo 检查](2026-10-13-k1-tcm-access.md)确认真实 TCM 可访问，但没有测量模型性能收益。

后续若修改英文导出正文，必须按[导出说明](REPORT-BUILD.md)同步生成 TeX 和 PDF。
2026-10-14 更新已将旧导出保留为快照，新综合报告记录单一默认构建与真实起点对照。
新报告仍保留根要求的验收缺口。
2026-10-16 更新追加[16k／32k 容量补测](2026-10-16-ultralong-final-comparison.md)与[最终版 TCM 调查](2026-10-16-final-release-tcm.md)。
补测沿用 r3 生产二进制，普通默认上下文仍为 12288。
2026-10-22 更新在综合报告新增第 9 节后续验收记录（官方检查点加工、固定多轮 v1／v2、自然长上下文），并把 16 份报告同步进成果包。
更新前的报告见[10 月 14 日快照](snapshots/2026-10-14-final-r3/SUBMISSION-REPORT.md)与[TCM 调查前快照](snapshots/2026-10-16-before-tcm/SUBMISSION-REPORT.md)。
