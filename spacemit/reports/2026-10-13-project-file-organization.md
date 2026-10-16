# 项目文件整理与检查记录

本页记录前期文档整理。
后续源码、构建、启动器和发布候选归档的实际整合见[独立整合记录](2026-10-13-unified-release-candidate.md)。
后续阶段继续保留本页所列原始文件和已有检查结果。

日期：2026-10-13，Asia/Singapore。
要求依据为根目录 [Requirements.md](../../Requirements.md)。
本次整理保留现有工作区改动，没有切换分支、重置文件或创建提交。
`spacemit/reports/raw/` 的文件位置和内容必须保持原样。
本次不运行新实机性能测试，也不添加新内核优化。

## 已完成的文件整理

| 文件或入口 | 修改目的 |
| --- | --- |
| [根目录入口](../../README.md) | 以现行要求、部署和缺口报告为主入口。 |
| [部署说明](../DEPLOYMENT.md) | 连接依赖、模型、固定源码、受锁构建、两个 profile 与本地请求。 |
| [模型入口](../models/README.md) | 连接产物身份、历史加工与尚未完成的官方全链转换。 |
| [测试入口](../bench/TESTS.md) | 区分本地复算、实机发布检查和历史测试。记录 tmux、共用锁及完成判据。 |
| [版本与结果索引](RESULTS.md) | 连接发布基线、优化版、独立候选、负结果与原始记录。 |
| [独立缺口报告](2026-10-13-requirements-gap.md) | 对应 5 项基础要求、15 个评分项、4 项进阶挑战及 8 条测量要求。 |
| [历史材料说明](HISTORY.md) | 保留旧补丁、早期报告和英文导出，并说明适用范围。 |
| [提交说明稿](SUBMISSION-ZH.md) | 采用现行导航，追加 10 月 13 日实机与 TCM 状态。 |
| [文档地图](../DOCS.md)、[发布说明](../release/README.md)、[测试总说明](../bench/README.md)、[报告索引](README.md) | 修正过时的连接恢复与 TCM 结论，接入新入口。 |
| [旧部署说明](../README.md)、[旧报告](../../FINAL-REPORT.md)、[文档服务](../serve/README.md)、[实验索引](../experiments/README.md) | 保留原路径，明确当前与历史用法。 |

当前发布仍是 `a990751` 固定包。
基线与优化 profile 只比较 route 0 和 route 3。
C1 已有独立模型验证，未加入该包。
新标量调度候选通过数值检查但未通过性能初筛，发布保留原内核。
sudo 可访问真实 TCM，不等于已测得模型收益。

## 工作区与证据保留

初始 `git status` 显示多个会话的未提交改动。
已有修改包括文档、算子工具、CPU 分析工具、模型来源脚本与原始证据。
本次修改上表中的文档入口，并另存本地检查脚本与日志。
已有实现、发布补丁、清单、模型锁定数据和原始证据不作重写。

整理前状态与差异快照位于本机 `/tmp/riscv-accl-organize-20261013/`。
该目录不是 Git 交付物。
整理前另保存全部原始文件的 SHA-256，用于整理后逐文件比较。
独立检查日志写入[本次检查目录](checks/2026-10-13-organization/)，不写入历史 `raw/`。

## 实际检查与会话记录

本地检查在独立 tmux 会话中执行。
会话名为 `riscv_delivery_checks`。
tmux 使用独立 socket 名 `riscv-delivery-20261013`。
运行目录为 `/home/moyamryia/Projects/riscv-accl`。
日志目录为 `spacemit/reports/checks/2026-10-13-organization/`。
完成状态以该目录中的 `exit-status` 和 `summary.json` 为准。

本次只复核已有证据和本地工具。
本次没有启动 K1 模型或板端性能任务。
已验证：发布工具的 3 项检查与模型身份工具的 7 项检查通过。
已验证：历史测量矩阵的 21 行、105 个数值单元复算通过。
已验证：20 份入口文档的本地文件与章节链接检查通过。
已验证：整理前后 22,252 个原始文件的 SHA-256 全部一致，没有新增或删除原始文件。
已验证：最新三批收据的 100 个文件身份核对通过。
其中 4 个二进制文件从保留归档直接读取核对，没有写回原始目录。

| 检查记录 | 结果 |
| --- | --- |
| [检查摘要](checks/2026-10-13-organization/summary.json) | 工具、链接、收据与原始文件保留检查通过。 |
| [矩阵复算日志](checks/2026-10-13-organization/03-command.log) | 21 行全部符合报告中的数值与完成状态。 |
| [原始文件保留](checks/2026-10-13-organization/raw-preservation.json) | 文件数量与全部原始哈希保持一致。 |
| [收据复核](checks/2026-10-13-organization/receipts.json) | 实机诊断 66 个、标量候选 30 个、TCM 检查 4 个文件通过。 |
| [任务状态快照](checks/2026-10-13-organization/task-status.json) | 2026-10-13 13:52:22，Asia/Singapore，本机与 K1 用户 socket 目录未发现活动 tmux 会话；未发现 `llama-server`。 |

本次 tmux 检查会话已结束，`exit-status` 为 `0`。
本次没有仍在 tmux 中运行的测试。
任务快照只覆盖所记录的用户 socket 目录与进程检查时刻。
前两次检查程序分别遇到收据格式差异与 Python 3.10 接口差异。
修正后检查通过，失败日志保留在检查目录的 `attempt-1/` 与 `attempt-2/`。
这些失败不属于模型测试失败。

复现本地工具与矩阵检查的命令见[测试入口](../bench/TESTS.md#本地工具与历史矩阵复算)。
文档链接、原始文件保留与收据检查由[本次检查脚本](checks/2026-10-13-organization/run-checks.py)执行。
检查启动命令为下列命令。

```bash
tmux -L riscv-delivery-20261013 new-session -d -s riscv_delivery_checks \
  -c /home/moyamryia/Projects/riscv-accl \
  'bash /home/moyamryia/Projects/riscv-accl/spacemit/reports/checks/2026-10-13-organization/run-checks.sh'
```

原始文件保留复核还需要整理前的 `/tmp/riscv-accl-organize-20261013/raw-before.json`。
它不是新克隆中自带的材料。
再次执行前必须另存本次日志，并使用新检查目录。
会话结束后可以直接读取已保存日志。
