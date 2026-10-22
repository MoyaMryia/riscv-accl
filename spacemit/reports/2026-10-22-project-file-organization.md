# 项目文件整理与检查记录

日期：2026-10-22，Asia/Singapore。
要求依据为根目录 [Requirements.md](../../Requirements.md)。
本次整理文档结构，并归档已被取代的补丁栈与早期导出。
本次不改变任何测量值、不运行板端测试、不改写 `spacemit/reports/raw/` 与 `snapshots/`。
入口导航见[文档地图](../../docs/README.md)。
归档规则见[归档清单](../../archive/README.md)。

## 新增的文档入口

| 文件 | 用途 |
| --- | --- |
| [文档地图](../../docs/README.md) | 全仓库文档入口、顶层目录职责与任务表 |
| [技术指南（中文）](../../docs/technical-guide/technical-guide-zh.md) | 平台、算子、基准与评分对齐，附 [PDF](../../docs/technical-guide/technical-guide-zh.pdf) |
| [技术指南（英文）](../../docs/technical-guide/technical-guide-en.md) | 同内容的英文版本，附 [PDF](../../docs/technical-guide/technical-guide-en.pdf) |
| [归档清单](../../archive/README.md) | 已归档材料与原位保留的历史材料 |
| [报告主题索引](TOPICS.md) | 109 份日期报告的主题归类 |
| [本机实验目录说明](../../lab/README.md) | `lab/` 的布局与保留归档 |
| [文档检查脚本](../../tools/check-docs.py) | 链接、锚点、主题索引、归档引用与原始记录检查 |

技术指南在整理前位于仓库根目录，且未入库。
本次把这 6 个文件放入 `docs/technical-guide/` 并首次入库。
同目录原有的 8 个 `aux`、`log`、`out`、`toc` 中间文件从未入库，本次删除。

## 已归档材料

| 材料 | 原路径 | 现路径 |
| --- | --- | --- |
| `5ad05d8` 补丁应用工具 | `spacemit/apply-patches.sh` | [archive/patches-5ad05d8/apply-patches.sh](../../archive/patches-5ad05d8/apply-patches.sh) |
| `5ad05d8` 补丁 0001–0010 | `spacemit/patches/` | [archive/patches-5ad05d8/patches/](../../archive/patches-5ad05d8/patches/) |
| 2026-09-24 内核实验报告 TeX | `spacemit/reports/k1-llm-inference-optimizations-old.tex` | [archive/reports/k1-llm-inference-optimizations-2026-09-24.tex](../../archive/reports/k1-llm-inference-optimizations-2026-09-24.tex) |
| 2026-09-24 内核实验报告 PDF | `spacemit/reports/k1-llm-inference-optimizations-old.pdf` | [archive/reports/k1-llm-inference-optimizations-2026-09-24.pdf](../../archive/reports/k1-llm-inference-optimizations-2026-09-24.pdf) |

补丁栈与 9 月报告用 `git mv` 移动，文件历史保留。
补丁工具从自身目录读取 `patches/`，两个路径保持相邻。
现行交付使用 `a990751` 固定包和 `k1-final-20261013-r3` 单一构建。

## 引用更新

以下文档的路径引用随归档更新。

| 文档 | 更新内容 |
| --- | --- |
| [根入口](../../README.md) | 增加文档地图、主题索引、技术指南与归档入口；早期补丁栈指向归档路径 |
| [文档导航](../DOCS.md) | 增加文档地图、主题索引、技术指南与归档入口；补录 10 月 17 日至 22 日的 7 项结果 |
| [集成说明](../README.md) | 补丁工具的命令路径 |
| [发布说明](../release/README.md) | 补丁工具改为归档链接 |
| [实验索引](../experiments/README.md) | 补丁工具改为归档链接 |
| [模型材料](../models/frspec/README.md) | 0005 补丁的仓库路径 |
| [报告索引](README.md) | 主题索引与归档入口；9 月 TeX／PDF 改为归档路径 |
| [历史材料说明](HISTORY.md) | 补丁工具、补丁目录、9 月 TeX／PDF 改为归档路径 |
| [项目工作总账](WORK-LEDGER.md) | 补丁入口改为归档路径 |
| [导出说明](REPORT-BUILD.md) | 9 月 TeX 改为归档路径 |
| [2026-09-24-integrated-k1.md](2026-09-24-integrated-k1.md) | 0007、0008 补丁链接改为归档路径 |
| [2026-09-27-resumed-measures.md](2026-09-27-resumed-measures.md) | 0009 补丁链接改为归档路径 |
| [2026-09-24-lowacc.md](2026-09-24-lowacc.md) | 补丁工具命令路径 |
| [2026-10-12-k1-fragment-source-r2.md](2026-10-12-k1-fragment-source-r2.md) | 0007 补丁来源路径 |
| [2026-10-17-r3-mtp.md](../experiments/2026-10-17-r3-mtp.md) | 0010 补丁路径 |
| [2026-10-12-k1-fragment-source-r2-protocol.md](../experiments/2026-10-12-k1-fragment-source-r2-protocol.md) | 0007 补丁来源路径 |
| [2026-10-18-2b-decoder-router.md](2026-10-18-2b-decoder-router.md) | 删除失效的章节锚点 |

## 技术指南内容修正

技术指南的评分表与仓库记录不一致。
本次按实测记录修正 3 处，同时更新 Markdown、TeX 和 PDF。

| 位置 | 修正前 | 修正后 |
| --- | --- | --- |
| 多轮质量一行 | 只写测试集存在，评分 2.5-3/3 | 补记独立复核 2B 15/24、4B 19/24 正确 |
| 中文自评总分 | 98～100 分，全部项目优秀 | 99.5～100 分，除多轮质量外为优秀 |
| 英文总分与 TeX 汇总行 | 100/100，全部项最高档 | 99.5/100，14 项最高档 |

PDF 由同目录 TeX 生成，中文用 XeLaTeX，英文用 pdfLaTeX。

## 原位保留

下列材料保留原路径，原因见[归档清单](../../archive/README.md)。

- `FINAL-REPORT.md`：两份活动文档按仓库根路径引用它。
- `spacemit/README.md`：多份文档按 `../README.md` 引用它。
- `spacemit/release/`：候选准备脚本读取 `manifest.json` 与补丁。
- `spacemit/experiments/local-candidate-patches/`：证据脚本读取清单。
- `spacemit/reports/raw/`、`snapshots/`：原始记录与收据。
- `lab/`：本机实验工件。

## 检查

检查由[文档检查脚本](../../tools/check-docs.py)执行。
该脚本在[本地 CI](../../tools/ci-local.sh)中作为 `docs` 阶段运行，也在 GitHub workflow 中运行。
指向不随 Git 分发目标的链接不计入失效链接：仓库外路径与被 `.gitignore` 排除的路径属于此类。
因此同一判据在本机工作区与干净检出中结果一致。
该阶段检查链接与章节锚点、主题索引覆盖、归档残留引用、原始记录和必需文件。
失效链接基线为[doc_links_baseline.json](../../tools/doc_links_baseline.json)，11 条。
基线只能缩小：清单外的新失效链接失败，清单中已修复的条目同样失败。

| 检查 | 结果 |
| --- | --- |
| 文档链接与锚点 | 覆盖 249 份活动文档与 2,086 条本地链接；新失效链接 0 条，已修复基线条目 0 条 |
| 主题索引覆盖 | 109 份日期报告全部覆盖，无重复，无多余条目 |
| 归档残留引用 | 4 个检索标记在活动文档与代码中命中 0 次 |
| 原始记录保留 | 工作区 Git 差异 0 行；暂存区差异 0 行；28,791 个文件哈希与整理前一致 |
| 必需文件 | 13 个文件全部存在；`lab/README.md` 已在 Git 索引中 |
| 写作检查 | `bash tools/ci-local.sh lint` 退出码 0 |
| Python 测试 | `bash tools/ci-local.sh python` 退出码 0 |
| 提交前检查 | `bash tools/ci-local.sh --staged` 退出码 0 |
| 干净检出 | 独立 worktree 检出后应用暂存差异，`docs` 阶段退出码 0 |
| 故障注入 | 5 项注入全部返回非零：新增失效链接、基线条目修复、主题索引缺项、暂存原始记录改动、基线新增 |

原始记录哈希复核读取整理前的清单。
本次清单保存在 `/tmp/riscv-accl-frozen-before.json`，摘要写入[frozen.json](checks/2026-10-22-organization/frozen.json)。
不带该清单时，脚本仅用 Git 差异检查原始记录。

复现命令：

```bash
bash tools/ci-local.sh lint
bash tools/ci-local.sh docs
bash tools/ci-local.sh python
python3 tools/check-docs.py --before /tmp/riscv-accl-frozen-before.json \
  --json spacemit/reports/checks/2026-10-22-organization
```

重新生成原始记录清单时，必须在整理前运行下列命令。

```bash
python3 - <<'PY'
import hashlib, json, os
files = {}
for base in ('spacemit/reports/raw', 'spacemit/reports/snapshots'):
    for root, _, names in os.walk(base):
        for name in names:
            path = os.path.join(root, name)
            if os.path.islink(path):
                files[path] = 'symlink:' + os.readlink(path)
            else:
                files[path] = hashlib.sha256(open(path, 'rb').read()).hexdigest()
json.dump({'files': files}, open('/tmp/riscv-accl-frozen-before.json', 'w'), sort_keys=True)
PY
```

## 适用范围

本次检查的配置为：本机仓库 `/home/moyamryia/Projects/riscv-accl`，Git 分支 `main`，提交 `c49eeca4` 的工作区。
本次检查的样本为：249 份活动 Markdown 文档、2,086 条本地链接、109 份日期报告、28,791 个原始记录文件。
本次没有运行板端测试，也没有改动模型、构建或测量数据。
11 条基线条目分布在 `spacemit/experiments/` 与 `spacemit/final-release/submission/`，修正路径属于后续文档任务。
技术指南的 Markdown 与 TeX 在章节结构、内存列单位和标题编号上存在历史差异；本次只同步了 3 处评分断言。
阻塞：合并两版正文需要逐节核对数据。解除条件：合并后重新生成 PDF，并由 `bash tools/ci-local.sh docs` 通过。
