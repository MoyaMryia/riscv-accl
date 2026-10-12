# 本地仓库复查：还有什么值得做

日期：2026-10-08，Asia/Singapore。本次仅检查本地文件和已有实验记录，没有连接 MUSE-Pi-Pro、调用云评分、联网检索或启动新的模型推理，也没有修改生产内核、默认配置或旧实验结论。

**结论：尚无证据说明优化空间已耗尽。若干小修小补的实现已失败。下一轮最值得做的不是继续删 IME 分支，而是检查单 token、长历史的 attention 数据流。另一个可以直接利用已有工作的方向，是把预填充收益与长输出总耗时分开评估。**

## 检查范围和版本边界

本次按目录检查了根报告、`env/` 和 QEMU 方法记录、`lab/` 历史瓶颈记录、本地源码快照、`spacemit/` 的发布包、补丁、模型工具、服务客户端、实验控制器、报告及相关原始数据。
`TinyLlama/` 和 `llamacpp-conv/` 属于旧模型和转换工作，未把它们当成可替换当前两个 Qwen3.5 模型的优化方案。本次没有逐行审计全部第三方代码、系统镜像或全部原始日志。

源码结论以 `a990751` 的本地干净快照、归档 routing 候选和发布准备副本为准，本次重新校验了八个相关源码文件的哈希。`lab/llama.cpp` 的其他版本不能当作当前测量源码，旧的真 TCM 实验也不能与当前 staging bypass 实验混合比较。

## 1. 第一优先级：256 维头的单 token attention

发布源码的 `spacemit/ime.cpp` 明确要求：

```cpp
const bool wide_tile = enable_wide_tile && !params->use_ref &&
                       DK == 256 && DV == 256 && neq1 >= 16;
```

单 token 解码时 `neq1 == 1`，不满足该条件，会进入通用 attention。通用路径在历史长度至少 512 时按 KV 区间切分，每个 worker 遍历全部 query heads，每个历史 token 调用一次 F16 点积，并执行在线 softmax 和 V 更新。
这不是"没有 RVV"：`vec.cpp:321` 已有 RVV F16 点积，`vec.h` 也有 RVV F16 更新。缺口是适配这些模型的专用解码数据流，而不是再开一个 RVV 开关。

源码位置：

- [发布 attention 调度](../../lab/release-preparation/ggml/src/ggml-cpu/spacemit/ime.cpp)
- [通用 attention：one_chunk 及 split-KV](../../lab/local-reference/source-a990751-clean/ggml/src/ggml-cpu/ops.cpp)，约 8468、9120 行
- [现有 RVV 点积](../../lab/local-reference/source-a990751-clean/ggml/src/ggml-cpu/vec.cpp)，264–343 行

本次重新解析了四份已归档、仅覆盖 decode 的 perf stacks，逐份校验了输入哈希，复算的样本数和原汇总一致。下表两列 self CPU 来自互不重叠的叶子样本：

| 模型 / prompt | Attention 叶子 self CPU | 独立 F16 dot 叶子 self CPU | 两类叶子合计 | 当次 decode tok/s |
| --- | ---: | ---: | ---: | ---: |
| 2B / 256 | 0.68% | 0.59% | 1.27% | 4.49 |
| 2B / 2048 | 5.98% | 6.06% | 12.04% | 3.80 |
| 4B / 256 | 1.54% | 1.52% | 3.06% | 2.08 |
| 4B / 2048 | 10.05% | 9.94% | 19.99% | 1.57 |

**边界**：全部 F16 dot 叶子都缺少可辨认的调用者。合计一列不能直接命名为"已确认 attention 占比"，更不能称为可节省的墙钟时间。源码证明 attention 调用此函数，样本随历史增长的走势支持继续调查。精确归属仍需补证。原报告的 visible attention stack 是下界，原始记录没有错误。

两个模型的 query/KV heads 分别为 8/2 和 16/4，均为 4:1。当前 generic 路径逐 query head 遍历历史，同一 KV head 对应的四个 query head 没有显式合并加载。预填充 tiled 路径同样限制 tile 不跨 query head 边界。这给出两个不同候选：

1. 先做保留既有数值顺序的解码专用实现，检查点积间接调用、Q 的重复加载、向量配置及临时 accumulator 读写，保持每个头的点积归约、F16 舍入、KV 遍历顺序和 split-KV 合并语义。
2. 再独立测试同 KV group 的 query heads 共享 K/V 加载或 packing。源码重复访问不等于四倍 DDR 流量，缓存可能吸收部分读，必须实测。

不能只把 `neq1 >= 16` 改成 `>= 1`：现有 tiled 算术和 scratch 为另一种路径，直接启用既不证明速度，也不证明解码数值一致。旧 one-chunk 特化还存在 VLEN 和 head-size 假设，不能直接用于 VLEN=256、DK=256。

下一轮最小 gate：单算子 DK=DV=256、query=1、GQA=4、KV=256/2048，先做精确输出、mask/sinks/tails 和 scratch guards，再做原库、候选关闭、候选开启三臂交错计时。通过后才跑短冷模型 ABBA，8k、完整答案和长代码放在后面。本次没有实现或测量这个候选。

## 2. 预填充已有正向信号，被不同目标的总耗时门槛挡住

[Hybrid SSM 完整答案实验](2026-10-06-ssm-complete-answer-results.md)记录：

| 指标 | 2B | 4B |
| --- | ---: | ---: |
| 汇总 prefill 时间减少 | 7.86% | 4.77% |
| 六任务完整回答总时间减少 | 2.92% | 2.13% |
| 候选/控制完整回答 | 六对文本相同 | 六对文本相同 |

该候选对大 batch 使用 RVV，对单 token 保留 reference。长代码和长回答主要花在 decode，预填充收益被总时间稀释。原实验按预设 >3% 总时间和 6/6 useful 要求判失败是正确的，但该判定不能推导出"预填充实现没有价值"。每个任务仅一对，仍需复验，不能直接改默认。

[Recurrent prefill fusion](2026-10-02-recurrent-prefill.md)也不是零收益：operator 时间少 24–28%，2B/512 prefill 少 2.38%，每臂两次启动。该候选只尝试复用已有逐 token RVV step，没有证明所有 recurrent prefill 数据流均已穷尽。

建议另立预填充实验，并在看新数据前固定目标：同一完整输入、route 3、F16 KV，先看 TTFT 和 prefill，再要求 decode 不退化、完整输出和状态不退化。hybrid SSM 和 recurrent fusion 可分别作为候选，二者单独复验成功后才测组合，收益不能相加。如果实际目标仍是这六任务总耗时，原来的拒绝结论继续有效。

## 3. 同步还有研究空间，但没有"白捡 20%"

[decode 审计](2026-10-07-decode-packing-results.md)已证明：约 20% `sync_impl` 样本来自调用线程等待四个 worker。删除等待不会让 worker 更快完成。worker `barrier_coro` 只有约 4.7–6.8% self CPU，其中也包含必要依赖与负载差。

共享 FFN 量化的重复部分仅 0.024–0.035% GEMM worker elapsed。为这点复制或缓存量化结果不划算。但是，该审计没有测量"合并 gate/up 的节点调度"或"conv + SiLU"的收益，不能据此把图融合一并否决。

需先做每节点、每 worker 的入口、compute 完成和 barrier 等待时间归属，再选一个有共同分片和明确依赖的融合点。已有 RMS_NORM+MUL 在 CPU 和 SPERT 图遍历中都尝试过融合，FFN 也已有 SwiGLU 表达，不应把它们包装成新发现。全图本来已一次 SPERT dispatch，不应误当成每个算子重新 launch。

这是次优先级调查，不是安全删除 barrier 的方案。

## 4. 不再优先押注的方向

| 方向 | 本地证据与判断 |
| --- | --- |
| 固定 K32 M1 删内层分支 | 正确性通过，但八形状、144 次 operator 记录没有一个过门槛，不要重复原实现。尚未试过的 load/dataflow 属于新候选 |
| 输出头单独调度 | 确有较大工作量，但原库 full-head operator 已约 44.50 / 55.95 ms。按 Q4_0 逻辑权重字节计算约 6.43 / 6.39 GB/s，接近约 7 GB/s streaming 参考，优先级低于长历史 attention。该比值不是 DDR 测量或硬件上限 |
| 再做紧凑 attention scratch 或 direct V | 已有 operator/model 负结果，不能直接重复；共享 K 和 group-head 是不同机制 |
| 无条件启用 RVV convolution | 单 token 已明确回退，已有 hybrid 避免它，不必重做无条件版本 |
| 继续放大 MTP 吞吐数字 | 长代码逐 token 一致、RS replay 和 useful-code 问题仍在，短输出匹配不能替代修复 |
| 低比特换模型、裁词表、截输入 | 不能作为当前同模型、同精度、完整输入和完整词表基础设施对照的收益 |
| 用 QEMU 墙钟挑板端快路径 | 旧实验已证明：RVV 指令数减少可以同时使 TCG 墙钟变慢；QEMU 适合功能验证，不能代替 K1 性能 |

MTP 仍有独立的修复价值：[原生 replay](2026-10-03-staged-validation-results.md) 每模型 18 个 mismatch，完整状态恢复及同形状控制通过，已有可缩小的复现。但修好状态管理不自动消除 batch 形状引发的数值差异，它是正确性项目，不能把历史 50% 吞吐提升当作修复后的保证。

## 5. "无可用答案"与"内核无优化空间"需要分别判断

本地干净 x86 reference 同样复现 2B 错误求和和漏引用，以及两模型 interval 代码失败。它没有隔离量化、thinking 模式和模型能力的因果贡献，但表明确有错误不能统统归罪于 K1 候选。

对内核研究，可以同时保留三项判据：算子和状态正确、相对输出和质量不退化、产品绝对 usefulness。若控制本身只能 2/6 useful，而候选与控制逐字相同，6/6 gate 必然阻止产品采纳，它并不回答"内核是否加速且无新增回归"。必须事先声明新实验目的，不能事后降低旧门槛来翻转结果。

## 本次离线复核与交付

- `python3 spacemit/release/test-release.py`：3 项通过。
- `verify-k1-gemm-routing.py`：236 artifacts、104 native cases/臂、144 operator 记录及六个模型比较复算通过。
- `verify-k1-release.py`，使用已有 remote-preservation 文件：35 artifacts、两臂 native identity 和四个自然停止代码答案复核通过，每答案 106 项检查。该程序只读取本地归档，没有发起远端连接。
- [本次分析脚本](raw/local-opportunity-audit-20261008/analyze.py) 与 [结果及输入/源码哈希](raw/local-opportunity-audit-20261008/analysis.json)：四份 decode profiles 共 102,164 样本、八个相关源码文件重新校验。

本次新增内容是机会排序与离线分析，不是新的加速成果。最先值得做的是长历史单 token attention 的归属和精确数值实现；若当前重点是冷请求首 token，则先复验已有 hybrid SSM 的阶段收益。板子关机不影响完成这些源码分析和准备工作，但 K1 的候选性能必须等实机验证。
