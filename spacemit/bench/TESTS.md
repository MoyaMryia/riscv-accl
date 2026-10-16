# 测试与结果复核入口

要求依据为根目录 [Requirements.md](../../Requirements.md)。
已有结果与证据位置见[结果索引](../reports/RESULTS.md)。
先检查已有证据，再决定是否需要新测试。
所有测试必须在 tmux 会话中执行。
本地证据复算不访问 K1。

统一包的独立验证入口为[验证说明](../release-candidate/README.md#执行验证)。
[固定协议](../release-candidate/PROTOCOL.md)规定本轮源码、配置、原发布对照与停止条件。
[整合记录](../reports/2026-10-13-unified-release-candidate.md)保存实际执行状态。
统一包的 `with-lock.sh` 已取得共用锁，外层不得重复持锁。

## 会话与共用锁

每次执行必须记录会话名、运行目录、日志位置、命令和退出状态。
使用新的输出目录，保留旧记录。
下例用于本地检查。
在 tmux 会话内执行后续本地命令。

```bash
tmux new-session -s riscv_delivery_checks -c /absolute/path/to/riscv-accl
```

实机计时、构建与推理必须持有 K1 的项目共用锁：

```text
$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock
```

自动板端控制器自行获取此锁。
不要在外部先持有同一锁，否则控制器会等待自己。
手动部署的持锁命令见[部署入口](../DEPLOYMENT.md#2-在受锁保护的会话中构建)。
不要删除锁文件来解除等待。
`exit-status=0` 只证明流程正常结束，是否通过必须读取各阶段结论。
会话存在只证明任务已启动。

## 本地工具与历史矩阵复算

在仓库根目录执行。
把输出保存到新的本地检查目录。

```bash
python3 spacemit/release/test-release.py
python3 spacemit/models/tools/test_reproduction.py
python3 spacemit/bench/verify-results-matrix.py \
  spacemit/reports/2026-09-27-resumed-measures.md \
  spacemit/reports/raw/2026-09-25-lifecycle
```

发布工具检查固定源码、补丁和模型身份拒绝条件，以及两个 profile 的环境隔离。
模型记录工具检查身份拒绝条件，不执行完整官方转换。
历史矩阵复算首词元时延、预填充、解码、完成状态和内存数值。
本地检查不能替代模型实机测试。

严格路由与发布核验还需要原始归档中的全部文件。
取得完整工件后，可以在同一 tmux 会话执行：

```bash
python3 spacemit/bench/verify-k1-gemm-routing.py \
  /absolute/path/to/full-routing-run
python3 spacemit/bench/verify-k1-release.py \
  /absolute/path/to/full-release-run \
  --preservation /absolute/path/to/post-run-board-preservation.json
```

Git 文本收据不是全部二进制转储。
缺少文件时必须记录“待验证”，不能跳过后仍称严格全工件检查通过。
不要用新结果覆盖 `reports/raw/` 中的既有文件。

## 发布包实机检查

已完成结果见 [10 月 7 日核验](../reports/2026-10-07-release-verification.md)。
仅在需要复现或验证新环境时启动下列测试。
从本地 tmux 会话执行，`musepipro` 是已配置的 SSH 别名。
其他设备必须设置对应 `--board`。

```bash
python3 spacemit/bench/start-k1-release-check.py --board musepipro \
  --run-dir /absolute/path/to/new-release-run
```

控制器建立板端 tmux 会话与本地收集会话。
板端脚本持有共用锁，并拒绝已有 `llama-server`。
该流程构建固定源码，检查每臂 104 个原生用例，并执行两个模型、两个 profile 的完整代码回答。
每个回答必须自然停止并通过 106 项功能检查。
`run.json` 保存实际会话名、板端运行目录及代码身份。
`driver.log`、`collector.log`、`exit-status` 和 `collector-exit-status` 保存过程与完成状态。
严格收据与保存检查的步骤见[核验报告](../reports/2026-10-07-release-verification.md#evidence-and-repeat-commands)。

如果测试已结束而收集失败，只恢复收集。

```bash
python3 spacemit/bench/start-k1-release-check.py \
  --collect-only --run-dir /absolute/path/to/existing-release-run
```

不要为取回结果重复推理。
四个完整回答是限定任务检查，不能证明一般质量或统计性能。

## 性能、长上下文与质量入口

| 目的 | 脚本或说明 | 解释范围 |
| --- | --- | --- |
| 首词元时延、服务端预填充、解码与内存 | [生命周期工具](bench-lifecycle.py)、[使用说明](README.md#first-token-long-context-and-stability-measurements) | 记录实际词元长度、上下文、线程、缓存状态和完成状态。直接脚本不自动获得共用锁。 |
| 复核生命周期完成数和词元身份 | [审计工具](audit-lifecycle.py)、[汇总工具](summarize-lifecycle.py) | 已保存的词元序列哈希与文本哈希分别判断。 |
| 路由匹配性能复验 | [控制器](start-k1-roofline.py)、[完成报告](../reports/2026-10-06-k1-roofline-results.md) | 已有 24 次冷请求；带宽参考与 CPU 采样不能证明硬件极限。 |
| 固定文档完整回答 | [质量矩阵说明](README.md#extended-chat-quality-matrix)、[已完成结果](../reports/2026-09-30-chat-quality-benchmark.md) | 现有质量限制保留。不能替代携带对话历史的多轮验收。 |
| 独立候选复现 | [候选说明](local-candidates/README.md)、[补丁清单](../experiments/local-candidate-patches/README.md) | 使用各候选的固定源码与协议。已验证候选和失败组合分别判断。 |
| 标量调度负结果 | [候选入口](ime-scalar-schedule/README.md) | 数值通过，性能初筛未通过，不需要为了整理重复执行。 |
| 性能分析器与算子数据 | [分析器](qemu-screen/predictor/README.md)、[CPU 工具](cpu-model/README.md)、[算子数据](operator-data/README.md) | 辅助工具准确性不等于整模型加速验收。 |

现行要求没有规定长上下文验收长度、可用速度、稳定时长与质量分界。
这些条件属于[缺口报告](../reports/2026-10-13-requirements-gap.md)中的待确定项。
不能自行把历史测试参数变成新的硬性门槛。

本次文件整理的实际会话、命令、日志与完成状态见[整理记录](../reports/2026-10-13-project-file-organization.md)。
