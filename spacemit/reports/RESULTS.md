# 版本、结果与证据索引

核对日期：2026-10-16，Asia/Singapore。
要求依据为 [Requirements.md](../../Requirements.md)。
本索引连接已有报告与原始记录，不产生新性能测量。
RVV 表示 RISC-V 向量扩展。
IME 表示项目使用的矩阵指令扩展。
首词元时延表示请求开始到客户端收到首个输出词元的时间。

## 发布边界

最终[单一默认交付](../final-release/README.md)为 `k1-final-20261013-r3`。
默认值、真实起点兼容范围、28 次性能对照和质量限制见[最终对照报告](2026-10-14-final-default-comparison.md)。
[16k／32k 补测](2026-10-16-ultralong-final-comparison.md)追加 12 次匹配请求，普通默认上下文仍为 12288。
[最终版 TCM 调查](2026-10-16-final-release-tcm.md)确认普通用户下两个模型的短推理没有使用真实 TCM。

10 月 7 日的[固定发布包](../release/README.md)保留为原发布对照。
新的[统一发布候选](../release-candidate/README.md)合入三个候选，并保留各自开关。
统一包的实际验证与归档身份见[整合记录](2026-10-13-unified-release-candidate.md)。
源码为进迭时空 `llama.cpp` 的 `a990751d55a4c54acf2bb77d44282c2093652359` 加清单中的补丁。
模型文件身份由[发布清单](../release/manifest.json)固定。
源码、构建、运行库与模型身份必须以各批次原始收据为准。

| 版本 | 配置 | 证据与结论 |
| --- | --- | --- |
| 最终默认 r3 | 同一生产构建；掩码 3、4 线程、批大小 32、上下文 12288 | 已验证：[真实起点对照](2026-10-14-final-default-comparison.md)，两模型 512/2048 各三对，8192 各一对；实际默认值和迁移通过。 |
| 发布基线版 | 宽 RVV 注意力、layout 0、route 0、直接解码 | 已验证：[10 月 7 日干净构建与检查](2026-10-07-release-verification.md)。 |
| 发布优化版 | 同一源码、模型与注意力，route 3 | 已验证：同一发布检查与[路由独立复验](2026-10-06-k1-roofline-results.md)。这是路由增量比较。 |
| 历史通用／RVV 对照 | 通用注意力与宽 RVV 注意力 | 已验证：[历史测量矩阵](2026-09-27-resumed-measures.md)。它不是发布启动器两种 profile 的比较。 |
| C1 | 条件卷积路径，基线已有 RVV 与 route 3 | 已验证：[独立候选判定](2026-10-09-local-candidate-result-rejudgment.md)。[10 月 13 日检查](2026-10-13-k1-live-inspect-and-scalar-schedule.md)另确认局部图路径。统一包将其列为显式实验配置。 |
| C2-r2、旧 C3、B1-r2 | 各候选分别开启 | 已验证限定模型负载：[独立候选判定](2026-10-09-local-candidate-result-rejudgment.md)。C3 使用旧 C2。补丁见[候选目录](../experiments/local-candidate-patches/README.md)。 |
| 三项全开组合 | B1-r2、C1、C2-r2 | 已验证退化：[停止复核](2026-10-12-combined-stop-audit.md)。第二轮与完整回答未执行。 |
| 组合分派修订 | 本地条件修改 | 已实现，板端收益待验证：[修订协议](../experiments/2026-10-12-combined-dispatch-r2-local-protocol.md)。 |
| IME 标量调度候选 | 移动标量地址与计数指令 | 已验证数值一致，性能初筛未通过：[实机报告](2026-10-13-k1-live-inspect-and-scalar-schedule.md)。未纳入发布，模型性能未测。 |

10 月 7 日发布启动器固定四线程、F16 键和值缓存、批量及微批量 32、单槽与 6,144 上下文。
这不是历史 16k 测量配置。
不能把不同基线的百分比相加或相乘。
共有模型错误仍属于现行质量验收缺口。

## 结果到记录

下表中的配置、样本量、指标与失败状态都在所列报告中。
原始目录保留实际请求、源码身份与逐臂数据。

| 要核对的成果 | 报告 | 原始记录 | 复核入口与限制 |
| --- | --- | --- | --- |
| 最终版 16k／32k 容量补测 | [补测报告](2026-10-16-ultralong-final-comparison.md) | [12 次请求与独立核验](raw/k1-ultralong-20261016-r1/) | 同一 r3 二进制；显式增加容量，保留普通默认值。 |
| 最终版普通用户 TCM 路径 | [TCM 调查](2026-10-16-final-release-tcm.md) | [跟踪与核验](raw/k1-tcm-final-release-20261016-r1/) | 两次短请求、13 份映射；设备打开分别返回 EACCES 和 ENOENT。 |
| 干净发布与两个模型完整回答 | [发布核验](2026-10-07-release-verification.md) | [请求与汇总](raw/k1-release-check-20261007-125712/)、[独立核验](raw/release-20261007/) | `verify-k1-release.py`；严格全工件检查需要完整归档和转储。 |
| 路由预填充与解码复验 | [路由复验](2026-10-06-k1-roofline-results.md) | [24 次匹配请求](raw/k1-roofline-20261005-225502/) | 每模型、每输入长度三对冷请求；不是总体性能保证。 |
| 历史 2k／8k／12k／16k 与 2B 32k | [长输入矩阵](2026-09-27-resumed-measures.md) | [生命周期记录](raw/2026-09-25-lifecycle/) | `verify-results-matrix.py`；16k 每臂一次，2B 32k 无匹配控制，4B 32k 缺测。 |
| 独立候选模型收益与完整回答 | [候选判定](2026-10-09-local-candidate-result-rejudgment.md) | 该报告逐版本所列目录 | 96 次完整回答、48 对全文相同。共有质量错误仍保留。 |
| 全开组合解码退化 | [停止复核](2026-10-12-combined-stop-audit.md) | [原摘要与独立复算](raw/k1-combined-stop-audit-20261012/) | `audit-combined-stop.py`；96 次第一轮冷请求，未执行后续阶段。 |
| 缓存问答质量 | [质量矩阵](2026-09-30-chat-quality-benchmark.md) | 该报告所列完整答案与评分记录 | 24 对完整回答；2B／4k 仍需复核，不等于携带历史的多轮验收。 |
| 官方模型复现准备 | [来源记录](../models/REPRODUCIBILITY.md) | [第二版来源准备](raw/model-origin-preparation-r2-20261012/) | `test_reproduction.py` 检查记录工具；不是完整权重转换验证。 |
| C1 实机路径与采样热点 | [10 月 13 日诊断](2026-10-13-k1-live-inspect-and-scalar-schedule.md) | [身份、图算子、采样](raw/k1-live-inspect-20261013/) | CPU 采样占比不是墙钟收益；局部图结果不是整模型加速比。 |
| 标量调度数值检查与负结果 | [10 月 13 日诊断](2026-10-13-k1-live-inspect-and-scalar-schedule.md) | [数值、初筛与源码](raw/k1-ime-scalar-schedule-20261013/) | 288 个数值配置、96 条算子记录、8 个配置均未过收益门槛。 |
| TCM 权限与真实设备 | [权限检查](2026-10-13-k1-tcm-access.md) | [普通用户与 sudo 对照](raw/k1-tcm-access-20261013/) | sudo 识别并只读映射四块真实 TCM；没有带宽或模型收益结论。 |

测试命令、tmux 会话记录和共用锁要求见[测试入口](../bench/TESTS.md)。
Git 不包含全部大文件。
原收据证明其记录的身份；缺少大文件时不能宣称重新完成严格全工件核验。

## 辅助分析与历史范围

性能评估器、CPU 模型与算子训练数据见[报告总索引](README.md#k1-performance-evaluator)。
这些工具用于分析，不替代两个模型的 K1 实测。
预测错误、宽区间与未通过的候选必须继续保留。
历史导出及旧源码入口的适用范围见[历史材料说明](HISTORY.md)。
