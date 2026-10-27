# K1 性能建模与评估基建

统一入口为 `analyze.py`。
运行环境为 Python 3 标准库、项目交叉工具链、QEMU 插件头文件和 GLib 开发文件。
MCA 后端另外需要项目私有 LLVM 22.1.8。
工具不替换系统配置。

后续主线见 [K1 CPU 建模计划](../../../experiments/2026-10-12-k1-cpu-model-plan.md)。
计划覆盖执行资源、存储层次、多核与新算法独立检查。
[CPU 等待队列模型第六轮](../../../reports/2026-10-12-k1-cpu-queue-model-r6.md)已完成冻结后测。
9/9 组覆盖伴随 1.6495 的校准因子。
12 个可分辨版本均变慢，方向一致为 12/12。
收益误差最大仍为 30.3592 个百分点。
[第五轮退步](../../../reports/2026-10-12-k1-cpu-write-model-r5.md)与旧覆盖失败继续保留。

## 真实算子训练数据

[真实算子采集工具](../../operator-data/README.md) 已完成首轮受控输入测量。
IME 内核与 SSM 卷积共有 32 个训练配置和 1,344 条观测。
64 份完整数值转储的配对检查通过。
完整结果见 [首批报告](../../../reports/2026-10-12-k1-operator-data.md)。
首轮封存时，校准与后测形状尚未测量。
首轮短样本限制仍保留。
[第二轮报告](../../../reports/2026-10-12-k1-operator-data-r2.md) 记录延长时长后的验证。
两轮共有 2,688 条训练观测，仍只有 32 个不同配置。
通用指令模型未按这些数据重新拟合。
[固定算子形状模型 V1](../../../reports/2026-10-12-k1-operator-model-v1.md) 已完成独立校准与后测。
IME 后测方向一致为 18/18，卷积为 16/18。
卷积有一个形状组超出冻结界限。
该算子模型不改变 V1 至 V7 的精度声明。

## 当前用途

已实现：真实二进制轨迹、分项周期模型、访存诊断、独立误差校准与投入优先级接口。
已验证：用户态周期审计，以及重新测量的 246 组分项配置、30,618 个有效样本。
已验证：60 种访存配置、420 个有效样本，以及四线程共享缓存场景重放。
已验证：固定卷积算法对的独立形状检查，9/9 个保留组落入声明的 95% 区间。
该区间依赖形状组可交换性，不能推广到新算法或新二进制。
待验证：新算法的独立预测误差、共享缓存实际流量和完整 IME 时序。
未实现：经过标定的 gem5 后端。

全部候选均保留。
报告给出收益倾向、证据范围、覆盖缺口和补测顺序。
完整数值差异必须停止该次性能比较。
性能评估不使用淘汰门槛。
V1 与 V2 的原始记录保持不变。
旧通用周期计数器的用户态过滤未通过本次检查，不能改称用户态周期。
当前结果见 `spacemit/reports/2026-10-12-k1-model-v7.md`。

可以先运行有独立形状检查的完整算子示例。
该示例只需要 Python 3 标准库。

```bash
python3 spacemit/bench/qemu-screen/predictor/family-demo.py --output lab/k1-family-demo
```

模型、19 个误差校准组与 9 个最终检查组位于 `examples/conv-family-v3/`。
该示例拒绝超出冻结范围的形状。
它保留全部候选，并分开列出预测区间与板端观测。

## V7 混合 IME 失败范例

已验证：168 个完整原生数值转储与同一 ELF 的厂商 QEMU 转储一致。
336 条实际轨迹完整结束。
冻结误差区间覆盖 9/9 个保留组和 27/27 个展开版本。
比值误差因子约为 2.12，点预测方向符号一致性仅为 9/27。
单链配置差异接近零，方向符号不能解释为有统计依据的变化。
宽区间不能证明模型可以安排 IME 优化投入顺序。

可以把该失败检查加入标准 Python 便携包。
本机与 K1 原生 Python 的关键预测散列完全相同。
五个范例同时保留历史覆盖缺口。
全部候选均保留。

```bash
python3 spacemit/bench/qemu-screen/predictor/model-bundle.py \
  --include-ime-audit --output lab/k1-portable-v7
```

先核验外部散列收据，再解包到目标机器。
在 k1-models-v7/ 中执行 `python3 run-examples.py --output ../k1-replay`。
输出目录必须不存在。
该入口重放冻结证据，不提供任意新算法的预测置信度。
完整范围、协议与投入顺序见 V7 报告。

## V6 便携入口

已验证：V6 对齐循环的独立观测覆盖为 9/9 组和 27/27 个展开版本。
模型分别预测各展开版本，误差界限先于后测冻结。
声明的 95% 覆盖依赖固定范围内配置组的可交换性。
本次观测不能确认总体 95% 覆盖率。
V5 的 7/9 覆盖缺口仍保留。

可以生成只依赖 Python 3 标准库的便携包。
包内有分项周期、完整卷积、V5 混合指令和 V6 对齐循环四个范例。
工具同时核验完整性、冻结身份和独立检查数值。
本机与项目服务器的关键预测散列完全相同。
全部候选均保留。

```bash
python3 spacemit/bench/qemu-screen/predictor/model-bundle.py --output lab/k1-portable
```

先核验生成压缩包的外部散列收据。
解包后，在 k1-models-v6/ 中执行下列命令。
输出目录必须不存在。

```bash
python3 run-examples.py --output ../k1-replay
```

本轮范例主机重放用时约 0.38 s 与 0.32 s。
这不是 K1 运行时间。
新算法必须另建适用范围与独立误差校准。
模型能力、检查缺口与投入顺序见 V6 报告。

## 在其他机器使用 K1 模型

成本重放只需要 Python 3 标准库。
生成新轨迹另外需要 QEMU、插件头文件与二进制库存工具。
成本后端不需要 LLVM-MCA。
参数位于 `profiles/k1-cpu0-umode-20261012/`。
这些参数只对应本次 K1 的 CPU 0 和测试配置。

可以先运行随仓库提供的实际轨迹示例。
该示例不需要额外工具链或模拟器。

```bash
python3 spacemit/bench/qemu-screen/predictor/demo.py --output lab/k1-cost-demo
```

先将已核验的实际轨迹转换为紧凑成本程序。
此步骤逐条核对实际指令字节。
共享库必须提供正确的 `--load-bias`。

```bash
python3 spacemit/bench/qemu-screen/predictor/analyze.py compile-cost TRACE_DIRECTORY INVENTORY_JSON \
  --output lab/k1-cost-program
python3 spacemit/bench/qemu-screen/predictor/analyze.py cost lab/k1-cost-program \
  --profiles spacemit/bench/qemu-screen/predictor/profiles/k1-cpu0-umode-20261012/components.json \
  spacemit/bench/qemu-screen/predictor/profiles/k1-cpu0-umode-20261012/ime.json \
  spacemit/bench/qemu-screen/predictor/profiles/k1-cpu0-umode-20261012/reductions.json \
  spacemit/bench/qemu-screen/predictor/profiles/k1-cpu0-umode-20261012/scalar.json \
  spacemit/bench/qemu-screen/predictor/profiles/k1-cpu0-umode-20261012/gaps.json \
  --output lab/k1-cost-result
```

紧凑程序可以复制到另一台机器。
重放会再次检查全部操作与压缩轨迹的 SHA-256。
模型身份包含成本代码、语义代码、入口代码和全部参数文件的 SHA-256。
文件位置不改变模型身份。
参数发生变化时，原误差校准不能直接复用。

每条指令均具有非零成本。
未标定指令使用显式假设，并进入覆盖缺口。
模型使用寄存器 RAW 和 WAW 依赖。
同一虚拟缓存行还保守地约束访存 RAW、WAR 和 WAW。
该访存约束会引入虚假依赖，不能代替加载转发或别名标定。
IME 点积只支持已标定的有符号 4×4×8 编码与寄存器布局。

模型给出三个场景：低成本热缓存、中心成本热缓存和高成本容量惩罚。
一级、二级缓存与随机指针延迟只构成声明假设。
随机指针延迟同时包含访存模式和地址转换的影响，不能称为纯 DDR 延迟。
各线程最大值和总和是两种声明的组合，不是实际耗时上下界。
当前结果不输出 K1 墙钟时间。

## 访存与计数器诊断

`memory-reference.py` 查询固定模式的实测有效载荷吞吐率。
模式 3 为步长 16 的向量读取。
下面的配置使用四个线程，每个缓冲区的基础跨度为 8,388,608 字节。

```bash
python3 spacemit/bench/qemu-screen/predictor/memory-reference.py --mode 3 --threads 4 --span 8388608
```

工具拒绝未测配置，不外推算法耗时。
`shared-cache.py` 重放完整四线程紧凑轨迹。
它比较声明冷缓存与重复调用状态，并保留跨线程共享行。
缓存几何、线程交错与虚拟索引均为显式假设。
输出的下层流量不是实测 DDR 流量，也不是 K1 耗时。

```bash
python3 spacemit/bench/qemu-screen/predictor/shared-cache.py PROGRAM_DIRECTORY \
  --quantum 32 --passes 2 --segment-barriers --output lab/k1-cache-reference
```

只有外部屏障与轨迹区域段确实对应时，才使用 `--segment-barriers`。
`prepare-counter-audit.py` 生成用户循环和系统调用对照夹具。
`audit-counters.py` 核对通用周期与原始用户态周期的范围差异。
`prepare-counter-repair.py` 保留热点字节，并重新建立用户态周期标定载荷。
`matched-evaluate.py` 核对同一二进制的完整输出、墙钟配对收益和分线程周期斜率。
暂停同步计数会改变屏障到达时间，不能用两种模式相减获得同步成本。

## 投入优先级与误差范围

`rank` 保留输入的全部候选。
排序只比较相同 `workload` 和 `baseline_id`。
数值更高的中心收益只表示当前证据下的投入顺序。
区间重叠时，报告不确认两者的先后关系。

```bash
python3 spacemit/bench/qemu-screen/predictor/analyze.py rank PRIORITY_PLAN_JSON \
  --output lab/k1-priority
```

`cost-evidence.py` 可以复用冻结的卷积与 IME 轨迹，并生成预测优先级输入。
`prepare-measured-priority.py` 可以转换既有板端配对区块。
该适配器区分不同实验的对照区块，不混用 B2 的 tile8 与 tile16 对照样本。
`diagnose-cost.py` 按实际动态指令数量生成补齐顺序。
该顺序不表示指令的墙钟耗时占比。

测量结果采用配对区块自助法区间。
少量区块可能低估漂移，测量区间也不证明模型预测精度。
未校准的预测只给出声明场景的敏感性范围。
场景中更快的比例不是实际加速概率。

预测误差接口采用独立工作负载组的绝对对数比值残差。
每组取最大残差，再使用有限样本顺序统计量。
有限的 90% 区间至少需要 9 个独立组，95% 区间至少需要 19 个独立组。
这些数量只满足该统计构造，不能证明工作负载可交换性。
接口拒绝模型身份差异、适用范围差异、训练泄漏和待预测组泄漏。
区间目标是下一次配对夹具测量，不是无噪声硬件均值。

误差文件必须声明 `model_sha256`、`domain`、`training_groups` 和 `records`。
误差记录必须声明 `group`、`predicted_ratio`、`measured_ratio` 和 `scope_matched`。
预测记录还必须声明待预测的 `group` 和 `domain`。
`scope_matched` 的依据必须来自独立协议，工具不能自行证明适用范围。
轨迹完整、范围匹配、直接标定覆盖率至少为 98% 且无缺口时，接口才应用校准误差。
这些条件约束证据等级，不淘汰算法候选。

## 等待归因与组合指令检查

`explain-cost.py` 按声明调度器归因等待，并对两项依赖约束做敏感性检查。
`explain-suite.py` 逐线程核对默认结果与冻结成本模型一致。
归因之和等于声明模型周期，但不能解释为硬件停顿比例。
假设模式不表示已经验证的 K1 配置。

`prepare-load-use.py` 建立加载与消费指令的两种调度方式。
原生与 QEMU 使用同一二进制。
三个循环长度与三个展开数量分离固定入口和循环控制贡献。
组合成本不是纯加载延迟。
19 个误差校准组与 5 个保留组预先分开。
保留组测量发生在误差界限冻结之后。
首批保留观测覆盖为 4/5，不能确认其达到声明的 95% 总体覆盖率。
全部候选保留，原始界限不根据保留结果回调。

混合指令范围模型见 `schedule-family.py`。
V5 的九组后测方向一致，但区间观测覆盖为 7/9。
这个结果不能确认声明的 95% 总体覆盖率。
部分小展开函数的数量拟合相对残差达到约 12.2%。
后续入口 `schedule-neighbor.py` 直接使用每个展开版本的循环成本。
它按组校准三个版本的最大误差，避免把三个相关版本算成三个独立组。

## 新分项标定

`prepare-k1-profile.py` 生成向量算术、整数、加载、归约和随机指针测试。
`prepare-ime-profile.py` 生成已知 IME 编码测试。
`prepare-scalar-profile.py` 生成常用标量和压缩指令测试。
三个入口均接受 `--compiler`，并要求新的输出目录。
每个载荷固定指令数量、循环长度、重复轮次、完整输出检查和二进制身份。
归约使用较短循环，避免长累加越过逐次精确浮点累加范围。

每个载荷包含 `run-board-calibration.sh`。
板端必须在 tmux 内执行该包装脚本，并持有共用锁。
收回完整载荷后，用 `fit-k1-profile.py` 和实际二进制库存拟合成本。
拟合先分离循环入口贡献，再分离循环控制贡献。
全部样本均保留，报告列出频率快照和非自愿上下文切换次数。
重复测量的最小值与最大值只表示测量波动。
它们不是新算法的预测置信区间。

`prepare-cost-validation.py` 建立无计数器的旧标定轨迹夹具。
该入口核对全部函数字节与原板端二进制一致。
`validate-cost.py` 用两个循环长度分离模型入口贡献，并检查旧板端周期斜率。
这是回顾小内核检查，不能替代新完整算子的独立验证。

## 固定既有目标

输出目录必须不存在。
适配器使用既有二进制，不重新编译候选。
以下命令在项目根目录执行。

```bash
python3 spacemit/bench/qemu-screen/predictor/prepare-existing.py conv lab/predict-conv-plan \
  --conv-plan lab/k1-mca-trial-20261011/conv-plan/plan.json
python3 spacemit/bench/qemu-screen/predictor/prepare-existing.py ime lab/predict-ime-plan
```

B2 必须提供在 `-R 4G` 配置下生成的两个来宾加载记录。
记录必须包含 `libggml-cpu.so.0` 的基址。
每条动态指令仍须通过代码映像的字节检查。
错误基址必须停止分析。

```bash
python3 spacemit/bench/qemu-screen/predictor/prepare-existing.py b2 lab/predict-b2-plan \
  --tile 8 \
  --loader-control lab/k1-predictor-20261011-v1/b2-map-original.log \
  --loader-candidate lab/k1-predictor-20261011-v1/b2-map-b2.log
```

把 `--tile 8` 改为 `--tile 16` 可以选择另一个实际小块函数。
`--existing` 可以指定另一套冻结的既有载荷目录。
新的目标必须具有相同适配器接口。
不得将另一套编译器产生的代码归给既有二进制。

## 服务器执行

必须在 tmux 内执行正式批次。
包装脚本全程持有 `lab/qemu-screen-server.lock`。
包装脚本保存任务阶段、处理器拓扑、亲和性、日志和退出状态。
可以先用 `taskset` 固定宿主核心组。
宿主核心分配只控制处理效率。

```bash
bash spacemit/bench/qemu-screen/predictor/run-server.sh lab/predict-conv-run trace \
  lab/predict-conv-plan/plan.json --max-instructions 900000 --mca-window 1024 \
  --mca lab/k1-mca-trial-20261011/runtime/usr/lib/llvm-22/bin/llvm-mca
```

IME 可以使用相同入口。
B2 建议显式设置 `--max-instructions 30000`。
该上限按线程计算。
`--max-mca-threads` 默认只分析前四个线程标识。
MCA 默认分析每线程前 1024 条实际指令。
这些窗口不是完整函数耗时预测。

## 轨迹、依赖与缓存

插件支持已测的 QEMU API 4 和 API 7。
每个线程文件记录指令字节、程序计数器、顺序、区域段、VL、向量类型和掩码寄存器。
访存回调记录虚拟地址、大小与读写方向。
区域外执行只标记依赖边界，不记录其全部访存。
轨迹达到上限时必须输出 `trace-truncated`。

寄存器依赖区分 RAW、WAR 和 WAW。
RAW 表示读取前一条写入的值。
WAR 表示写入前一条读取的位置。
WAW 表示写入前一条写入的位置。
地址依赖检查同线程的逐字节 RAW 重叠。
它不证明跨线程内存顺序。
掩码元素依赖、未知控制与未支持指令必须保留为覆盖缺口。

缓存模型使用每核私有 32 KB 一级数据缓存与每簇共享 512 KB 二级缓存。
64 字节缓存行、八路相联、LRU 替换与写回策略均为未标定假设。
模型分别重放串行和逐访存回调轮转的声明式交错。
这两个交错不是 K1 实际线程顺序。
虚拟地址索引、区域前预热、预取、同步、一致性、TLB 与计算重叠仍有缺口。
工具不把未命中次数转换为 DDR 字节或周期。

已有轨迹可以直接重放。
重放不重新执行目标程序。

```bash
python3 spacemit/bench/qemu-screen/predictor/analyze.py replay TRACE_DIRECTORY INVENTORY_JSON \
  --output lab/predict-replay
```

共享库轨迹必须另外提供十进制 `--load-bias`。
每次重放都核验指令字节与结束记录。

## V1 历史标定与验收

协议为 `validation-protocol.json`。
中文说明为 `spacemit/experiments/2026-10-11-k1-predictor-v1-protocol.md`。
训练组与测试组在板端测量前固定。
历史候选只用于回顾检查。

```bash
python3 spacemit/bench/qemu-screen/predictor/prepare-calibration.py lab/predict-calibration \
  --compiler lab/toolchain/toolchain/riscv/bin/riscv64-unknown-linux-gnu-gcc
```

将该冻结目录复制到板端的新目录。
先检查现有任务与共用锁。
在板端 tmux 内执行下列命令。

```bash
bash run-board-calibration.sh PAYLOAD_DIRECTORY
```

包装脚本位于本目录，必须随载荷复制。
板端脚本必须全程持有 `document-quality-suite.lock`。
周期事件不可用、计数器复用或输出错误必须停止该方法。
脚本不修改计数器权限。
首次板端测量使用相同锁内命令，尚未执行此新增包装脚本。

收回完整目录后，在服务器执行实际二进制分析。
该步骤也必须在 tmux 和服务器锁内执行。

```bash
python3 spacemit/bench/qemu-screen/predictor/calibration-analysis.py BOARD_DIRECTORY \
  --mca lab/k1-mca-trial-20261011/runtime/usr/lib/llvm-22/bin/llvm-mca \
  --tool-prefix lab/toolchain/toolchain/riscv/bin/riscv64-unknown-linux-gnu- \
  --output lab/predict-calibration-analysis
```

周期结果是循环稳态斜率，不是每条指令的固定延迟。
工具保留全部样本，不选择最快样本。
训练拟合只使用一个无截距比例参数。
测试集检查周期误差、相对变化误差、排序和误淘汰风险。
观察误差区间不是总体置信区间。
原协议的阈值只用于复现 V1，不用于新的候选性能淘汰。

## 统一报告与来源

```bash
python3 spacemit/bench/qemu-screen/predictor/analyze.py coverage INVENTORY_JSON \
  --output lab/predict-coverage
python3 spacemit/bench/qemu-screen/predictor/analyze.py suite \
  --traces CONV_RESULT_JSON IME_RESULT_JSON B2_RESULT_JSON \
  --coverage COVERAGE_RESULT_JSON --validation VALIDATION_RESULT_JSON \
  --native NATIVE_RESULT_JSON \
  --output lab/predict-suite
python3 -m unittest discover -s spacemit/bench/qemu-screen/predictor -p 'test_*.py' -v
```

统一目录提供 `suite.json`、`report.md` 和 SHA-256 收据。
状态区分数值停止、指令不支持、夹具失败、模型覆盖不足与待板端验证。
模型验收失败不能改记为候选无收益。
单项结果不能直接相加为组合收益。

`--native` 是可选项。
该项汇总原型短测，不把它加入小内核训练集或留出集。
真实原型的计时对照、线程配置和测量范围必须单独说明。

## 板端原型与证据核验

`run-board-existing.py` 使用冻结载荷，不在板端重新编译候选。
载荷必须包含 `conv`、`test-b2`、`b2/`、`original/`、`common/`、`ime-native` 和 `SHA256SUMS`。
本次完整载荷及 IME 夹具源码保存在本报告的本地证据归档中。
载荷协议为其中的 `native-payload/protocol.md`。
必须把载荷复制到板端的新目录。
必须在 tmux 内执行下列命令。

```bash
python3 run-board-existing.py PAYLOAD_DIRECTORY
```

脚本全程持有板端共用锁。
脚本先核验载荷，再执行完整数值检查和六区块短测。
B2 对照为同一候选库的 tile0 路径。
IME 测试只覆盖热输入局部夹具。
输出包括逐样本记录、温度、频率、参数、退出状态和收据。
当前入口固定服务这三个原型；新增算子必须增加载荷适配器。
本次实测使用归档中的冻结脚本。
交付脚本另外检查样本身份、重复次数和计时值的一致性。
这些新增检查已对全部 156 个已有样本通过复核。

`verify-evidence.py` 独立核验文件收据或完整归档。
收据路径的基目录必须显式给出。
工具不解包归档，也不修改证据。
任何缺失文件、散列差异或超出基目录的路径都使核验失败。
输出文件必须不存在。

```bash
python3 spacemit/bench/qemu-screen/predictor/verify-evidence.py \
  --receipt PAYLOAD_DIRECTORY/run/SHA256SUMS --base PAYLOAD_DIRECTORY \
  --output lab/native-receipt-check.json
python3 spacemit/bench/qemu-screen/predictor/verify-evidence.py \
  --archive SERVER_ARCHIVE --expected-sha256 ORIGINAL_ARCHIVE_SHA256 \
  --output lab/archive-check.json
```

原始归档散列必须来自归档产生端。
本次服务器归档有 914 个文件和 38 个收据文件。
独立核验检查 948 个收据条目，未发现缺失或差异。

`freeze-sources.py` 保存官方来源、提交标识、许可文件和摘要。
下载、解析或写入失败时，脚本以非零状态退出。
全部文件保存成功后，脚本才生成 `SHA256SUMS`。
每次运行必须使用新目录。
本次固定来源和完整证据位于 `spacemit/reports/raw/k1-predictor-v1-20261011/`。
