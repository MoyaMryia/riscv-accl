# IME M4 独立标量指令调度

本目录提供一项默认关闭的实验补丁。
已验证：288 个原生数值配置逐位相等。
性能初筛未通过，发布路径保留原内核。
补丁只移动四条 B 地址推进指令和一条循环计数指令。
向量指令顺序、指令集合和浮点运算顺序保持原样。
`SPINE_IME_SCALAR_SCHEDULE=1` 开启候选。
缺省值、`0` 和无效值使用原内核。

本轮口径见[试验计划](../../experiments/2026-10-13-ime-scalar-schedule-r1-protocol.md)。
实机结论见[诊断与试验报告](../../reports/2026-10-13-k1-live-inspect-and-scalar-schedule.md)。

## 生成补丁

在项目根目录执行下列命令。
`SOURCE` 必须包含固定版本的原始 IME 内核。
生成器核对内核 SHA-256，并拒绝其他源码。
输出包含候选源码、补丁和指令顺序收据。

```sh
python3 spacemit/bench/ime-scalar-schedule/prepare.py \
  SOURCE/ggml/src/ggml-cpu/spacemit/ime1_kernels.cpp \
  lab/ime-scalar-schedule/candidate.cpp
```

## 生成实机测试目录

使用新目录，避免覆盖旧证据。
下列命令复制已固定身份的数值测试，并生成本轮测试入口。
基线收据来自本次实机诊断。

```sh
python3 spacemit/bench/ime-scalar-schedule/prepare.py \
  --bundle lab/ime-scalar-schedule-payload \
  --expected spacemit/reports/raw/k1-live-inspect-20261013/profile/expected-provenance.json
```

将测试目录复制到 K1 的新实验目录。
在 K1 的 tmux 会话内执行下列命令。
`RUN_ROOT` 必须是已复制目录的绝对路径。

```sh
bash "$RUN_ROOT/run.sh" "$RUN_ROOT"
```

测试入口使用现有板端源码、GCC 14 与已验证 C1 目标文件。
板端基目录固定为 `$HOME/Projects/riscv-accl-bench-2026-09-27`。
测试入口核对源码、模型和运行时身份。
测试入口重建 C1 库并核对 SHA-256，然后只替换 IME 目标文件。
测试全程持有项目共用锁。

## 读取结果

`exit-status` 为 `0` 表示试验流程正常结束，不表示候选已通过。
`summary.json` 保留数值检查、全部算子对照和初筛状态。
`operator.jsonl` 保留六个交错顺序块的逐臂记录。
`provenance.json` 保留模型、目标文件、编译命令、库和实机身份。
`candidate-ime1.patch` 保留实际编译的补丁。

算子初筛失败后，不执行模型性能测试。
通过初筛后，两个模型各执行四次 512 输入、1 输出的无提示缓存命中请求。
完整答案、状态回滚、解码与长上下文仍须单独验证。
本目录不修改发布默认配置。
