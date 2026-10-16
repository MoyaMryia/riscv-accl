# 优化片段有限调用点估计

本入口对完整调用循环计算周期斜率。
它包含实际分支、函数调用、寄存器依赖与写入。
模型只使用明确支持的指令和热访存假设。
它不自动启动全量测试。

## 使用流程

先按[源码夹具说明](FRAGMENT-SOURCE.md)构建载荷并完成数值检查。
载荷必须包含新版 `fragment_repeat` 调用循环。
原生计时与轨迹采集必须使用该共同循环。
旧版 R2 载荷没有这个共同循环，不能直接用于本入口。

分别采集两个调用次数。
下面的示例使用 3 次与 9 次。

```sh
python3 -B spacemit/bench/cpu-model/fragment-call.py \
  --payload /path/to/payload --qemu-check /path/to/qemu-check \
  --qemu /path/to/qemu-riscv64 --header /path/to/qemu-plugin.h \
  --output /path/to/calls3 --cases 0 1 --trace-calls 3 --skip-decoded

python3 -B spacemit/bench/cpu-model/fragment-call.py \
  --payload /path/to/payload --qemu-check /path/to/qemu-check \
  --qemu /path/to/qemu-riscv64 --header /path/to/qemu-plugin.h \
  --output /path/to/calls9 --cases 0 1 --trace-calls 9 --skip-decoded

python3 -B spacemit/bench/cpu-model/fragment-predict.py \
  --model /path/to/bound-model.json --payload /path/to/payload \
  --freeze /path/to/pre-native-freeze.json \
  --short /path/to/calls3 --long /path/to/calls9 \
  --output /path/to/prediction.json
```

预测工具默认读取模型目录中的 `pre-native-freeze.json`。
如果收据位于其他目录，必须通过 `--freeze /path/to/pre-native-freeze.json` 指定。
收据必须与模型记录的 SHA-256 相同。
预测工具核验冻结拟合程序、时序引擎与解码器的身份。
模型必须包含 `runtime_binding`，并绑定全部本地工具依赖。
当前依赖包含公共文件读写、ELF 解析、采集核验、训练提取、拟合与评价模块。
任一依赖发生变化会停止预测。
工具同时核验两组轨迹的全部文件收据、单元身份与采集命令。
空收据、重复单元、错误配置、错误种子或错误调用次数均停止预测。
命令一致性检查不是全部寄存器值的独立重放。

预测需要计划中的全部配置。
示例计划必须只有配置 `0` 与 `1`。
每个配置和实现均必须有两份完整轨迹。
实际目标函数的进入次数必须与采集次数相同。

已有轨迹的便携重放只需要标准 Python。
新轨迹采集仍需要对应 QEMU、插件头文件、GLib 与 C 编译器。

## 模型行为

时序引擎不向轨迹添加合成计数器和循环分支。
引擎保留标量队列、写入队列、执行资源和寄存器依赖。
实际重叠的访存建立地址依赖。
加载与已有重叠写入之间建立先后关系。
重叠向量写入必须完成后才能执行后续重叠访存。
该规则是当前有效时序假设。

返回周期与全部结果完成周期分别报告。
调用斜率使用两个调用循环的返回周期差值。
引擎不把每次函数返回都当作全部写入已排空。
有限调用次数不能证明任意长期稳态。

未知指令停止预测。
除数、乘法高半部分、浮点、IME 与多数 RVV 指令尚未接入。
向量路径当前只覆盖已有说明中的配置、移动与 e8 连续写入。
显式缓存缺失、TLB、预取与写缓冲结构仍未标定。

## 标定与当前证据

R4 使用七种复制机制和四种配置。
仅对齐的 14 个单元参与拟合。
模型与预测冻结后才检查偏移 1 字节的 14 个单元。
84 份原生与 QEMU 完整转储相同。
840 条原生观测通过配对核验。

保留配置的周期绝对相对误差中位数为 1.69%。
最大误差为 30.70%，来自重复写入机制。
12 项相对基线的方向判断一致。
这些配置共享机制源码，不能称为独立算法族。
详细条件与全部缺口见 [R4 报告](../../reports/2026-10-13-k1-fragment-timing-r4.md)。

输出是点估计。
`prediction_confidence` 保持为 `null`。
观测重复范围不是预测置信区间。
所有候选继续保留。
当新片段的范围或假设缺少证据时，必须补充小规模原生检查。

## 训练与评价工具

`fragment-training-view.py` 只发布计划指定的训练观测。
新拟合必须使用 `fragment-fit-checked.py`。
`fragment-fit.py` 保留为 R4 冻结核心与历史重放入口。
新入口核验两组轨迹的全部单元，并重新从原生证据提取训练视图。
训练视图不同会在参数搜索前停止。
新入口同时核验拟合前固定的完整工具依赖。
拟合程序保留全部搜索候选。
`fragment-evaluate.py` 比较冻结预测与全部直接观测。
评价保留误差、退步、方向不一致与观测方向不确定。
评价必须包含两个进程各五次重复的全部周期斜率。
评价工具从这些斜率重算中位数、配对比值与重复范围。
缺失比较、重复配置、非有限数或矛盾的汇总值均停止评价。
这些工具不执行性能淘汰。

在新的采集协议中，必须先固定参数网格、采集配置和完整工具依赖。
下面的命令固定完整工具依赖。

```sh
python3 -B spacemit/bench/cpu-model/fragment-toolchain.py \
  --output /path/to/tool-freeze.json

python3 -B spacemit/bench/cpu-model/fragment-fit-checked.py \
  --payload /path/to/payload --short /path/to/calls3 --long /path/to/calls9 \
  --prior /path/to/prior-model.json --grid /path/to/parameter-grid.json \
  --training /path/to/training-view.json --freeze /path/to/pre-native-freeze.json \
  --tool-freeze /path/to/tool-freeze.json --qemu /path/to/qemu \
  --native /path/to/native --output /path/to/checked-model.json
```

旧 R4 模型没有完整依赖绑定。
必须先用封存包和其根收据发布新的绑定模型。
下面的命令核验历史核心模块与封存包中的文件相同。

```sh
python3 -B spacemit/bench/cpu-model/fragment-bind.py \
  --model /path/to/frozen-model.json --archive /path/to/portable.tar.gz \
  --receipt /path/to/raw/SHA256SUMS --output /path/to/bound-model.json
```

绑定模型使用新的文件身份，但保留原始参数。
该绑定发生在原始测量之后。
它不能补记为原始采集前已完成的核验。
新工具的兼容性检查也不能证明新算法精度。

2026-10-13 的检查修复了输入核验缺口。
R4 的冻结参数与原始封存包保持不变。
重新计算的 28 个单元预测与全部误差评价保持相同。
问题、检查范围与剩余限制见[检查报告](../../reports/2026-10-13-k1-fragment-review.md)。
后续完整依赖绑定与拟合修复见[修复报告](../../reports/2026-10-13-k1-fragment-hardening.md)。
