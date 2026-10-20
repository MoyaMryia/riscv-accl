# riscv-accl

本项目在进迭时空 K1 平台上部署 Qwen3.5 2B 和 4B 本地文本推理。
[Requirements.md](Requirements.md) 是要求、验收目标和评分口径的唯一现行依据。
文档核对日期：2026-10-16，Asia/Singapore。

> **Notice：来源补证（2026-10-16）**
>
> 已验证：两个模型的 Unsloth GGUF 输入哈希均与固定修订的公开文件一致。
> 已验证：现用 GCC／G++ 与 Bianbu `14.2.0-4ubuntu2~24.04bb2` 公开包中的编译器哈希一致。
> 已验证：从固定官方修订提取 15 个多词元预测（MTP）张量后，重建的 4B MTP GGUF 与历史产物哈希一致。
>
> 模型输入记录：`musepipro-wg:~/Projects/riscv-accl-bench-2026-09-27/source-trace-20261016-034448/file-identities.json`。
> 编译器与 MTP 补证记录：[源材料补证收据](spacemit/reports/raw/source-proof-20261016-135448-r2/README.md)。
> 任务：更新 `final-release` 的清单与归档；现有归档保持原字节。

最终版完成一次请求的速度，2B 为厂商起点的 1.24～3.59 倍，4B 为 1.41～4.72 倍。
输入越长，倍数越大；服务器内存两臂之差小于 3 MiB。
逐形状数据见[中文报告](spacemit/reports/SUBMISSION-ZH.pdf)和[英文报告](spacemit/reports/SUBMISSION-REPORT.pdf)。

GGUF 是当前推理引擎读取的模型文件格式。
已验证：现有两个 GGUF 产物均有 K1 本地推理记录。
已实现：固定源码发布包、模型加工脚本、测试工具与证据索引。
指定基座的来源链、官方检查点全链转换及现行质量验收的状态见[独立缺口报告](spacemit/reports/2026-10-13-requirements-gap.md)。

| 任务 | 可用入口 |
| --- | --- |
| 从依赖准备到两个模型的本地请求 | [部署入口](spacemit/DEPLOYMENT.md) |
| 使用最终单一构建与编译默认值 | [固定默认交付](spacemit/final-release/README.md) |
| 核对真实起点到最终默认的实测提升 | [最终对照报告](spacemit/reports/2026-10-14-final-default-comparison.md) |
| 使用统一源码、同次构建和独立候选开关 | [统一发布候选](spacemit/release-candidate/README.md) |
| 查明做过什么、采用什么及停止原因 | [项目工作总账](spacemit/reports/WORK-LEDGER.md) |
| 确认基线版、优化版和历史版本 | [版本与结果索引](spacemit/reports/RESULTS.md) |
| 获取补丁、构建脚本、模型哈希和启动器 | [固定发布包](spacemit/release/README.md) |
| 复现模型加工并核对来源 | [模型材料](spacemit/models/README.md) |
| 检查已有证据或运行新测试 | [测试入口](spacemit/bench/TESTS.md) |
| 阅读中文技术报告 | [SUBMISSION-ZH.md](spacemit/reports/SUBMISSION-ZH.md)、[PDF](spacemit/reports/SUBMISSION-ZH.pdf) |
| 查找全部报告与协议 | [报告索引](spacemit/reports/README.md)、[实验索引](spacemit/experiments/README.md) |
| 查看本次整理和检查记录 | [整理记录](spacemit/reports/2026-10-13-project-file-organization.md) |

已验证：最终单一构建已完成两模型普通启动与真实起点匹配对照。
默认启用 B1-r2、C1、宽 RVV 与 route 3，具体范围见[最终交付](spacemit/final-release/README.md)。
下面的 RC1 和历史候选结论继续按原条件保留。

10 月 7 日已核验的 `a990751` 包保留为固定对照。
新的[统一发布候选](spacemit/release-candidate/README.md)合入 C1、C2-r2 和 B1-r2。
本次实际状态见[整合记录](spacemit/reports/2026-10-13-unified-release-candidate.md)。
基线版和优化版都启用宽向量注意力，分别使用矩阵路由配置 route 0 和 route 3。
C1 有独立模型验证记录，统一包中的候选配置保持实验状态。
三项全开组合未通过解码门槛。
新增 IME 标量调度候选通过数值检查，但未通过性能初筛，发布路径保留原内核。

[10 月 13 日实机诊断](spacemit/reports/2026-10-13-k1-live-inspect-and-scalar-schedule.md)确认板端访问和 C1 路径。
[TCM 权限检查](spacemit/reports/2026-10-13-k1-tcm-access.md)确认 sudo 可以识别并只读映射四块真实 TCM。
普通用户的访问限制不能单独证明当前性能瓶颈。

中文与英文技术报告及 TeX／PDF 已更新为 2026-10-16，旧版快照单独保留。
[16k／32k 补测](spacemit/reports/2026-10-16-ultralong-final-comparison.md)记录 12 次匹配请求。
[最终版 TCM 调查](spacemit/reports/2026-10-16-final-release-tcm.md)确认普通用户下两个模型的短推理没有使用真实 TCM。
`FINAL-REPORT.md`、早期补丁栈及旧 `lab/` 记录保留历史范围。
其适用日期、源码和限制见[历史材料说明](spacemit/reports/HISTORY.md)。
`spacemit/reports/raw/` 保存不可改写的原始记录与 SHA-256 收据。
模型权重、部分二进制转储和完整归档不随 Git 分发。
