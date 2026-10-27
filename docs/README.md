# 文档地图

本页是全仓库的文档入口。
[Requirements.md](../Requirements.md) 是要求、验收目标和评分口径的唯一现行依据。
[AGENTS.md](../AGENTS.md) 是写作与检查规则。
文档核对日期：2026-10-22，Asia/Singapore。

## 顶层目录职责

| 路径 | 职责 | 入库 |
| --- | --- | --- |
| `README.md`、`Requirements.md`、`AGENTS.md` | 项目入口、现行要求、写作与检查规则 | 是 |
| `docs/` | 文档地图与技术指南 | 是 |
| `spacemit/` | 交付主体：部署、模型、测试、协议、报告、原始证据 | 是，`raw/` 按记录规则处理 |
| `archive/` | 已归档的历史材料 | 是 |
| `tools/` | 仓库检查工具与本地 CI | 是 |
| `env/` | 比赛背景与 QEMU 环境说明 | 说明入库，QEMU 镜像保留本机 |
| `lab/` | 本机实验工件、保留归档与另一项目的 TinyLlama 基线材料 | 只入库 `README.md` |
| `bianbu/`、`TinyLlama/`、`llamacpp-conv/` | 厂商镜像、模型仓库与转换工具副本 | 否 |
| `final-release/` | 交付脚本生成的完整成果目录；`spacemit/final-release/` 是入库的交付说明与工具 | 否 |

## 现行依据与入口

| 文档 | 用途 |
| --- | --- |
| [README.md](../README.md) | 项目状态与任务入口 |
| [Requirements.md](../Requirements.md) | 现行要求与评分口径 |
| [AGENTS.md](../AGENTS.md) | 写作、归档、测试批次与复查规则 |
| [spacemit/DOCS.md](../spacemit/DOCS.md) | 当前工作导航与逐项决定 |

## 部署、构建与运行

| 文档 | 用途 |
| --- | --- |
| [部署说明](../spacemit/DEPLOYMENT.md) | 依赖、模型、固定源码、受锁构建与本地请求 |
| [固定默认交付](../spacemit/final-release/README.md) | `k1-final-20261013-r3` 单一构建与普通启动 |
| [统一发布候选](../spacemit/release-candidate/README.md) | 统一源码、同次构建与独立候选开关 |
| [固定发布包](../spacemit/release/README.md) | `a990751` 构建脚本、补丁、模型哈希与启动器 |
| [5ad05d8 集成说明](../spacemit/README.md) | 早期补丁栈的来源、构建与运行 |
| [文档服务](../spacemit/serve/README.md) | 本地文档服务与缓存复用 |
| [TCM 工具](../spacemit/tcm/README.md) | 真实 TCM 用户态接口与检查 |

## 模型材料

| 文档 | 用途 |
| --- | --- |
| [模型材料](../spacemit/models/README.md) | 模型身份、加工流程与来源 |
| [复现说明](../spacemit/models/REPRODUCIBILITY.md) | 固定输入与产物复现 |
| [模型工具](../spacemit/models/tools/README.md) | 量化、张量拼接与身份核对 |
| [频次排序草稿头](../spacemit/models/frspec/README.md) | 32k MTP 草稿头原型 |

## 测试与检查

| 文档 | 用途 |
| --- | --- |
| [测试入口](../spacemit/bench/TESTS.md) | 本地复算、实机发布检查、tmux 与完成判据 |
| [测试总说明](../spacemit/bench/README.md) | 基准工具与调用方式 |
| [本地 CI](../tools/ci-local.sh) | Lint、文档检查与 Python 测试的唯一命令定义 |
| [文档检查](../tools/check-docs.py) | 链接、锚点、主题索引、归档引用与原始记录检查 |
| [写作与异常检查](../tools/writing_lint.py) | 限制句与宽泛 `except` 检查 |

## 结果与总账

| 文档 | 用途 |
| --- | --- |
| [结果索引](../spacemit/reports/RESULTS.md) | 基线版、优化版、独立候选与负结果 |
| [结果账本](../spacemit/reports/RESULTS-LEDGER.md) | 逐条结果的机器可校验账本 |
| [项目工作总账](../spacemit/reports/WORK-LEDGER.md) | 做过什么、采用什么与停止原因 |
| [报告索引](../spacemit/reports/README.md) | 按日期的报告入口 |
| [报告主题索引](../spacemit/reports/TOPICS.md) | 109 份日期报告的主题归类 |
| [实验索引](../spacemit/experiments/README.md) | 预登记协议与当前解释 |
| [历史材料说明](../spacemit/reports/HISTORY.md) | 历史材料的适用范围 |

## 技术报告与技术指南

| 文档 | 用途 |
| --- | --- |
| [中文技术报告](../spacemit/reports/SUBMISSION-ZH.md) | 现行要求与限定结果 |
| [英文技术报告](../spacemit/reports/SUBMISSION-REPORT.md) | 同内容的英文版本 |
| [证据附录](../spacemit/reports/SUBMISSION-EVIDENCE.md) | 结论到记录的映射 |
| [导出说明](../spacemit/reports/REPORT-BUILD.md) | 报告导出与更新规则 |
| [中文技术指南](technical-guide/technical-guide-zh.md) | 平台、算子、基准与评分对齐（[PDF](technical-guide/technical-guide-zh.pdf)） |
| [英文技术指南](technical-guide/technical-guide-en.md) | 同内容的英文版本（[PDF](technical-guide/technical-guide-en.pdf)） |

技术指南同时保留 Markdown、TeX 和 PDF 三种形式。
修改正文后必须同步三种形式。
[文档检查](../tools/check-docs.py)逐行核对 Markdown 与 TeX 的标题、性能表数值与命令，并把数值与[中文技术报告](../spacemit/reports/SUBMISSION-ZH.md)比对。
PDF 从同目录的 TeX 生成；中文使用 XeLaTeX，英文使用 pdfLaTeX。

```bash
xelatex -interaction=nonstopmode -halt-on-error -output-directory=docs/technical-guide docs/technical-guide/technical-guide-zh.tex
xelatex -interaction=nonstopmode -halt-on-error -output-directory=docs/technical-guide docs/technical-guide/technical-guide-zh.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=docs/technical-guide docs/technical-guide/technical-guide-en.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=docs/technical-guide docs/technical-guide/technical-guide-en.tex
```

每条命令运行两次以生成目录页码。
中间文件由 `.gitignore` 排除。

## 原始证据

| 路径 | 用途 |
| --- | --- |
| [spacemit/reports/raw/](../spacemit/reports/raw/) | 原始日志、逐字回答与机器摘要，按记录保留 |
| [spacemit/reports/snapshots/](../spacemit/reports/snapshots/) | 已导出的报告快照与收据 |
| [spacemit/reports/checks/](../spacemit/reports/checks/) | 整理与检查日志 |

`raw/` 与 `snapshots/` 中的文件按原路径引用其他文档。
移动被引用文件会让这些记录中的链接失效。

## 归档

| 文档 | 用途 |
| --- | --- |
| [归档清单](../archive/README.md) | 已归档材料、原位保留的历史材料和归档规则 |

## 非 Git 材料

| 路径 | 说明 |
| --- | --- |
| [lab/README.md](../lab/README.md) | 本机实验目录的布局与保留归档 |
| `env/` | 比赛背景与 QEMU 环境说明；QEMU 镜像保留本机 |
| `bianbu/`、`TinyLlama/`、`llamacpp-conv/` | 第三方材料，保留在本机 |
| `final-release/` | 由交付脚本生成的完整成果目录，保留在本机 |
