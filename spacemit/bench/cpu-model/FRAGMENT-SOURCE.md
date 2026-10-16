# 优化片段源码夹具

本入口把基线与候选放进同一可核验夹具。
它固定源码、编译命令、实际 ELF 与测量边界。
它先检查数值，再报告轨迹覆盖与模型缺口。
它可以支持小规模原生配对实测。
它不自动启动全量测试。

## C 片段接口

每个实现提供以下函数形式。

```c
void fragment_baseline(const uint8_t *input, uint8_t *output, size_t work_units);
void fragment_candidate(const uint8_t *input, uint8_t *output, size_t work_units);
void fragment_reference(const uint8_t *input, uint8_t *output, size_t work_units);
```

基线与候选的符号名称由构建清单指定。
参考函数必须使用 `fragment_reference`。
每个函数只读输入，并完整写入声明的输出。
当前接口使用独立输入与输出缓冲区。
原地修改与输入输出别名不在当前范围内。
当前数值比较采用完整字节相同规则。

夹具记录完整输入、输出与保护区。
夹具检查输入不变，并核对输出与保护区。
单次片段调用不能依赖此前的输出内容。
当前热重复测量不支持每次调用后累积状态的片段。
需要此类语义时，必须扩展状态恢复与测量协议。

## 构建清单

清单使用 `schema=1`。
`sources` 保存 C 源文件路径与 SHA-256。
`compiler_flags` 保存实际编译参数数组。
`kernels` 保存实现身份与函数符号。
`baseline` 指定基线身份。
`contract.boundary` 指定测量边界。

`cases` 的每个配置包含以下字段。

| 字段 | 含义 |
| --- | --- |
| `id` | 配置身份，只使用 C 标识符字符。 |
| `work_units` | 传给函数的逻辑工作量。 |
| `input_bytes` | 完整输入长度。 |
| `output_bytes` | 完整输出长度。 |
| `offset` | 指针相对 64 字节对齐基址的偏移，范围为 0 至 63 字节。 |

`q8-layout-fragment.c` 提供实际项目片段的首个接入样例。
来源与运行条件见[固定协议](../../experiments/2026-10-12-k1-fragment-source-r2-protocol.md)。
这个样例不代表原生产函数的完整调用成本。

```sh
python3 -B spacemit/bench/cpu-model/fragment-build.py plan.json \
  --compiler /path/to/riscv64-unknown-linux-gnu-gcc --output /path/to/new-payload
```

构建目录必须此前不存在。
构建程序复制源码、生成配置表并记录文件身份。
编译命令不通过 shell 执行。
构建程序保留编译器的入口路径，避免破坏依赖入口名称的编译器包装器。
构建成功不能证明数值或预测精度。

## 数值与轨迹

```sh
python3 -B spacemit/bench/cpu-model/fragment-check.py \
  --payload /path/to/payload --qemu /path/to/qemu-riscv64 \
  --plugin /path/to/trace.so --output /path/to/new-qemu-check
```

数值检查使用三个确定性输入种子。
种子为 `0`、`1` 与 `17`。
每个配置与实现均检查完整参考输出。
轨迹只采集第一个配置的每个实现。
函数范围轨迹不包含地址范围之外的被调用函数。
完整片段预测必须另行补齐这些路径。
新增[完整调用入口](FRAGMENT-CALL.md)可以记录所选调用的全部被调用函数。
该入口仍不提供完整调用周期预测。

当前真实函数输出 `numerically-checked-model-gap`。
该状态说明数值检查通过，但完整函数模型仍有缺口。
程序不把部分覆盖的成本累加为完整函数预测。
固定循环比较仍使用[有限比较入口](FRAGMENT-COMPARE.md)。

## K1 小规模配对实测

先检查机器任务与共用锁。
先核验已完成的 QEMU 数值检查。
板端必须使用新的批次目录。
在 tmux 内运行载荷的 `run-fragment-board.sh`。
该脚本全程持有项目共用锁。
锁冲突或明确失败后，不自动重复同一批次。

测量范围为 CPU 0、单线程、热输入重复调用。
实现共用相同工作量与调用次数。
试测目标为每个实现至少 10 ms。
正式样本保留实际耗时，不按这个目标删除样本。
三种调用次数分别为基础次数的 1、2 与 4 倍。
两个进程各执行五次重复。

原生退出记录必须为 `0`。
必须等传输完成后再核验完整归档。
同一 ELF 的原生与 QEMU 完整转储必须相同。

`fragment-fetch.py` 先取得归档收据，再接收完整归档。
接收程序只在传输退出、散列核验与证据检查全部通过后发布目录。
失败只留下 `.partial` 目录与失败记录。
该程序不会恢复或重复原生任务。

```sh
python3 -B spacemit/bench/cpu-model/fragment-fetch.py --host musepipro-wg \
  --remote /path/to/completed-batch --output /path/to/new-received
```

```sh
python3 -B spacemit/bench/cpu-model/fragment-assess.py \
  --payload /path/to/payload --qemu /path/to/qemu-check \
  --native /path/to/native --output /path/to/new-assessment.json
```

评价保留每个进程与重复的斜率、截距和残差。
评价先计算斜率的整数分子与分母，再转换为浮点结果。
该步骤避免不同 Python 版本的浮点求和差异。
评价报告周期、墙钟与线程 CPU 时间的配对比例。
重复比例范围只描述观测波动。
它不是预测置信区间。
所有候选与退步都保留。

## 当前缺口

源码提取可能改变内联、寄存器分配与调用开销。
原调用位置仍需独立核验。
其他参考容差、可变状态与别名语义仍待接入。
真实函数的写入、多循环、缓存条件与调用路径仍待建模。
新代码改进族的预测精度与分阶段总成本仍待验证。
