# K1 性能仿真方法调查

日期：2026-10-11，Asia/Singapore。

## 结论与验证状态

建议采用“QEMU 功能执行、X60 调度分析、板端标定”的组合。
gem5 可以作为后续的详细模拟后端。
本次检索没有找到已经验证本项目 K1 工作负载预测误差的现成完整模型。
这一结论只限于本次查阅的公开来源。

已验证：LLVM 主线具有具名 `spacemit-x60` 调度模型。
已验证：本项目已有 QEMU 正确性、热点计数和服务器并发框架。
未实现：本项目尚未接入 LLVM MCA 或 gem5。
待验证：K1 周期预测误差、IME 时序覆盖和组合收益排序。
本次没有启动新的板端测试。

## 可用方法

| 方法 | 可以提供的结果 | 主要缺口 | 本项目用途 |
| --- | --- | --- | --- |
| QEMU 与插件 | 实际执行路径、指令和访存记录、完整数值对照 | 指令计数不等于处理器周期 | 保留现有功能检查，扩展热点轨迹 |
| LLVM MCA 与 X60 模型 | 汇编依赖、执行资源竞争和计算吞吐量估算 | 缓存、动态路径及部分指令参数不完整 | 第一版计算性能后端 |
| LLVM-MCA-Daemon | 将动态指令轨迹交给调度分析器 | 本项目的 RISC-V 接口尚未验证 | 参考其接口设计 |
| gem5 MinorCPU | 可配置的顺序流水线和存储系统模拟 | 没有经过本项目标定的 K1 配置 | 后续分析复杂访存与线程交互 |
| rvv-bench | RVV 微基准与指令测量程序 | 测量条件与延迟、吞吐量仍须分别核验 | 参考板端标定用例 |

## X60 调度模型

[LLVM 模型源码](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Target/RISCV/RISCVSchedSpacemitX60.td)说明其参数来自 C908 文档和 BPI-F3 实验。
[处理器定义](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Target/RISCV/RISCVProcessors.td)把 `spacemit-x60` 连接到该模型。
[进迭工具链上游记录](https://github.com/spacemit-com/.github/blob/main/upstream-status/toolchain.md)也列出 X60 模型支持。
因此，我们可以从现成模型开始，而不是从零猜测执行资源。

保存的源码设置 `IssueWidth=2` 和 `MicroOpBufferSize=0`。
该源码还设置 `CompleteModel=0`。
这些是上游模型参数，不是本项目测量结果。
源码仍保留未经实验确认的延迟和简化资源假设。
IME 指令能否解析及其时序是否准确，必须单独验证。

[LLVM MCA 文档](https://www.llvm.org/docs/CommandGuide/llvm-mca.html)说明分析质量取决于调度模型。
该工具没有完整缓存层次模型。
RISC-V 向量分析还需要正确的向量配置。
不能把一个静态循环自动当作所有输入的动态路径。

第一版必须分析目标 GCC 实际产生的汇编。
不能改用另一套编译器生成不同代码，再把分析结果归给原二进制。
必须核验指令字节、分析区域和向量配置。
未建模指令必须作为覆盖缺口保留。

## QEMU、轨迹与缓存

[QEMU 指令计数说明](https://www.qemu.org/docs/master/devel/tcg-icount.html)明确说明指令计数不提供周期准确模拟。
现有服务器框架可以批量检查数值并收集热点指标。
它尚未记录完整依赖、逐次地址和向量配置轨迹。
这些能力必须先补齐，才能分析访问顺序与计算重叠。

[QEMU 插件说明](https://www.qemu.org/docs/master/about/emulation.html)提供寄存器轨迹和缓存插件示例。
示例缓存插件按核配置二级缓存。
[K1 数据手册](https://github.com/spacemit-com/docs-chip/blob/main/en/key_stone/k1/k1_docs/k1_ds.md)则给出每簇共享的 512 KB 二级缓存。
手册给出每核 32 KB 指令缓存和 32 KB 数据缓存。
因此，不能直接把示例缓存插件当作 K1 缓存模型。

缓存行大小、替换策略、延迟和带宽仍须核验或标定。
访存字节数不能直接当作 DDR 流量。
QEMU 宿主线程的执行顺序也不能当作 K1 线程交错。
框架必须显式保存这些假设。

[LLVM-MCA-Daemon](https://github.com/securesystemslab/LLVM-MCA-Daemon)已有动态轨迹连接调度分析器的实现思路。
其公开示例不能证明本项目的 RISC-V、RVV 和 IME 载荷可以直接运行。
建议参考其分层接口，先验证小段热点，不先接入整个模型轨迹。

## gem5 的适用范围

[MinorCPU 文档](https://www.gem5.org/documentation/general_docs/cpu_models/minor_cpu)描述可配置的顺序流水线模型。
[RISC-V 处理器定义](https://github.com/gem5/gem5/blob/stable/src/arch/riscv/RiscvCPU.py)提供对应处理器类型。
[RISC-V ISA 配置](https://github.com/gem5/gem5/blob/stable/src/arch/riscv/RiscvISA.py)提供 RVV 和向量长度参数。
这些能力提供实现基础，但不能证明默认参数描述 K1。

必须验证目标指令、向量执行拆分、数值行为和 IME 覆盖。
必须标定流水线、缓存及存储参数。
不能因为 O3CPU 常用，就默认用乱序模型代表 X60。
建议先模拟小内核的关注区域，再考虑完整操作系统集成。
现有操作系统镜像可以保留用于集成检查。

## 标定与自动判定

既有[指令标定草案](../experiments/2026-10-11-k1-instruction-calibration.md)区分依赖延迟、独立吞吐量和访存行为。
[rvv-bench](https://github.com/camel-cdr/rvv-bench)可以提供用例参考。
其说明仍列有延迟与吞吐量测量改进项目。
不能直接把所有公开结果当作本板已验证参数。

拟合模型的内核与验收模型的内核必须分开。
历史成功与失败候选可以检查模型是否能解释既有结果。
这类回顾检查不能称为独立预测验证。
新的保留测试集必须在参数拟合前固定。

第一版只输出预测排序、覆盖缺口和误差范围。
误差尚未验证时，性能估算不能自动否决方案。
误差范围覆盖 3% 收益门槛时，候选必须保留为待板端验证。
完整数值差异可以立即停止候选。
构建与加载故障必须单独归类。
单项通过后仍须实测组合，不能相加单项收益。

## 实施顺序与证据

1. 在服务器的独立目录准备固定版本 LLVM MCA。
2. 对现有卷积热点执行指令覆盖与向量配置检查。
3. 补充每线程热点轨迹，并验证完整数值不变。
4. 在共用锁内执行板端小规模标定。
5. 用固定保留测试集检查误差与排序。
6. 对通过筛选的候选执行板端短测及组合验收。

这六项是后续实施顺序，不是本次已完成结果。
详细接口与停止规则见[框架设计](../experiments/2026-10-11-k1-predictive-screen-design.md)。
源码快照、来源与 SHA-256 收据保存在 `raw/k1-simulator-survey-20261011/`。
上游分支可以变化，保存的副本用于核验本次调查依据。
服务器框架速度只代表宿主处理效率，不能作为 K1 模拟精度证据。
