# QEMU 候选筛选框架原型

本目录用 QEMU 执行固定工作量，并记录指令与内存访问数据。
本目录不把模拟器耗时换算成 K1 耗时。
本目录不修改生产默认配置。
本目录不自动派发板端任务。

## 已实现与已验证

`run.py` 检查通用 RVV、进迭 IME 和现有 Linux 镜像。
`metrics.c` 是 QEMU 插件。
插件支持本机 API 7 和官方进迭包 API 4。
插件按函数地址范围统计指令、向量指令、已测试的有符号 `vmadot`、访问次数和字节数。
插件分别记录每个虚拟处理器的数据。
向量指令计数包含 `vsetvli`。
`ime` 字段只匹配本次测试的有符号矩阵点积编码，不覆盖全部 IME 指令。

`prepare-conv.py` 为上一批卷积原型生成固定计划。
它复制原型，并只给 `Conv::step` 增加禁止内联属性。
原始原型与已冻结载荷保持不变。
`conv-profile.cpp` 每臂执行一次完整卷积。
它先核验标量参考、完整状态、输入和保护区。
它再输出完整输入、权重、输出和状态转储。

`batch.py` 读取计划并串行执行各形状。
它核验来源、二进制哈希、热点范围和实际工作线程数。
它比较两臂完整转储的 SHA-256。
数值差异会终止后续用例。
指令或访问变化只产生筛选信号。
数值通过的结果仍为 `needs-board`。

本机已经验证四种卷积形状。
每形状的两个臂都具有四个工作线程计数。
故意改变一个输出元素的负向检查已触发 `rejected-numeric-difference`。
详细数据见 [可行性报告](../../reports/2026-10-11-qemu-screen-framework.md)。

## 使用方法

以下命令从仓库根目录执行。
输出目录必须不存在。

```bash
python3 spacemit/bench/qemu-screen/run.py lab/qemu-capability-new \
  --vendor-root lab/k1-qemu-feasibility-20261011/jdsk-qemu --os --os-vendor

python3 spacemit/bench/qemu-screen/prepare-conv.py lab/qemu-conv-plan-new
python3 spacemit/bench/qemu-screen/batch.py \
  lab/qemu-conv-plan-new/plan.json lab/qemu-conv-result-new
```

进迭包来源为 [官方示例](https://github.com/spacemit-com/riscv-ime-extension-spec/blob/master/example/README.md)。
已下载的包仅位于实验目录，未替换系统 QEMU。
新机器必须先准备工具链、QEMU、插件头文件与 GLib 开发文件。
`--os` 使用仓库已有内核与根文件系统副本。
`--os-vendor` 另外在来宾 Linux 中执行 IME 检查。
原系统镜像保持不变。

## 计划与结果约定

计划中的 `sources` 固定源文件与工具链哈希。
每个用例声明两个臂的 ELF 路径、哈希、参数和精确热点符号。
每个用例必须声明 `roi_threads`。
参数中的 `{dump}` 由控制器替换为新的转储路径。
适配器必须保证转储覆盖全部需比较的数据。
同一转储布局必须用于两臂。
入口参数必须固定工作量，不能用模拟器时间标定循环数。

当前适配器使用带符号的静态非位置无关 ELF。
其他适配器必须采用相同地址约定，或先实现动态装载地址解析。
热点只包含指定函数本体。
被调用函数和内核代码不计入该热点。
主程序仍会执行这些代码。
这一区别必须保留在报告中。

每次执行保存命令、日志、转储、计数、结果与 SHA-256 收据。
控制执行失败、候选执行失败、指令不支持和数值差异使用不同状态。
超时属于执行失败，不能记为性能负结果。
控制与候选同样的错误不能据此归因于候选。
批次正常返回仍可能包含有效负结果，后续工具必须检查 `result.json`。

## 性能解释边界

一次 RVV 指令可以处理多个元素。
元素数与向量配置、掩码及指令形式有关。
访存回调字节数不是 DDR 流量。
访问可能命中缓存，也可能访问同一缓存行。
QEMU 宿主耗时也不是 K1 耗时。
有故障时，指令回调次数不能直接视为已退休指令数。

单纯调整加载顺序的方案可能具有相同指令数。
指令数相同不能证明该方案无效。
当前框架没有 K1 发射、依赖、缓存一致性、预取或带宽模型。
当前框架不能根据这些计数自动否决全部性能方案。

## 后续接口

下一阶段可以加入 B2 和 IME 调度的固定工作量适配器。
这些适配器必须保留各自的完整正确性检查。
静态栈溢出扫描、地址轨迹、缓存模型和板端校准仍待实现。
缓存模型必须声明全部参数及证据来源。
板端自动派发必须复用现有 tmux、共用锁与收益门槛。
模型与计时任务必须串行执行。
原有组合实验运行时，本框架只执行本机任务。

## 交叉编译与汇编清单

`prepare-conv.py --tune spacemit-x60` 使用本机编译器的 X60 调优模型。
该选项保持原指令集选项和浮点收缩规则。
编译器的其他默认选项仍可能随调优模型变化。
必须保存实际目标选项，并重新核验完整输出。
调优参数不能证明生成代码已经达到最优性能。

`assembly-inventory.py` 从目标二进制提取指定函数的汇编。
它使用符号地址和长度，保留函数内部的局部标签。
它检查反汇编是否完整覆盖函数字节。
它保存静态指令清单、向量配置、栈引用和相邻指令对。
它另外识别本项目已验证的有符号 `vmadot` 编码。
其他无法解码的指令保持未解析状态。
静态计数不是执行频率。
地址相邻关系不是已证明的数据依赖。
栈引用也不能单独证明寄存器溢出。

```bash
python3 spacemit/bench/qemu-screen/prepare-conv.py \
  lab/qemu-conv-x60-new --tune spacemit-x60

python3 spacemit/bench/qemu-screen/assembly-inventory.py \
  lab/qemu-conv-x60-new/conv-profile lab/qemu-assembly-new \
  --symbol-regex '_ZN4Conv4stepE'
```

汇编清单用于选择板端标定项目。
必须结合实际执行覆盖和访存条件确定测量优先级。
本机验证及首批清单见 [交叉编译报告](../../reports/2026-10-11-cross-compile-calibration-inventory.md)。

## 独立服务器环境

`prepare-host-runtime.py` 收集本机 QEMU、插件头文件和运行依赖。
输出目录必须不存在。
该工具不复制宿主机的动态加载器或标准 C 库。
接收服务器必须另行验证二进制兼容性。

`server-env.sh` 只在当前 shell 中启用项目私有工具。
它不修改系统工具或用户启动配置。
`run.py` 与 `prepare-conv.py` 的 `--qemu-prefix` 参数选择私有 QEMU 目录。
进迭包仍由独立的 `--vendor-root` 参数选择。

```bash
source spacemit/bench/qemu-screen/server-env.sh
python3 spacemit/bench/qemu-screen/run.py lab/server-capability-new \
  --qemu-prefix "$K1_QEMU_PREFIX" \
  --vendor-root lab/k1-qemu-feasibility-20261011/jdsk-qemu --os --os-vendor
python3 spacemit/bench/qemu-screen/prepare-conv.py lab/server-conv-plan-new \
  --tune spacemit-x60 --qemu-prefix "$K1_QEMU_PREFIX"
python3 spacemit/bench/qemu-screen/batch.py \
  lab/server-conv-plan-new/plan.json lab/server-conv-result-new
```

部署必须核验普通文件哈希、符号链接及执行权限。
测试计划必须在服务器重新生成，不能复用旧机器的绝对路径或工具身份。
部署检查通过后，服务器可以执行编译与模拟筛选。
K1 周期参数仍须在板端测量。

## 物理核心分组与并发

`parallel.py` 从 Linux 读取允许使用的核心、物理核心标识和缓存结构。
它从混合处理器的性能监控单元读取性能核与能效核集合。
没有该信息时，核心类型记录为 `unknown`。
它不根据主频猜测核心类型。

每个组只包含同类核心。
每个组只选择同一处理器插槽和同一 NUMA 节点的核心。
NUMA 表示非一致内存访问结构。
一个物理核心最多选择一个逻辑处理器。
能效核组不得跨越共享二级缓存边界。
不足一个完整组的核心保持空闲。

每个控制与候选配对在同一核心组内串行执行。
独立配对可以并发执行。
所有子进程继承对应核心组的亲和性设置。
结果保存核心类型、实际亲和性、完整输出和指令计数。
失败时调度器停止派发，并终止本次调度器拥有的剩余进程组。
必须检查 `result.json` 的状态，不能只检查控制器退出码。

`server-parallel.sh` 启用私有环境并取得服务器工作区锁。
以下命令在服务器启动较长批次。
输出目录必须不存在。

```bash
tmux new-session -d -s k1_screen_new \
  'bash spacemit/bench/qemu-screen/server-parallel.sh lab/screen-new \
  --plan lab/server-conv-plan-new/plan.json --cores-per-job 4 --max-jobs 5 \
  > lab/screen-new-driver.log 2>&1'
```

`--reserve-cpus` 可以排除指定逻辑处理器及其物理核心。
`--max-jobs` 可以减少同时执行的用例数。
性能核与能效核的宿主耗时必须分别记录。
各组仍共享部分缓存、内存和系统资源。
核心亲和性不等于操作系统独占核心。
宿主耗时不能作为 K1 收益。

本次服务器验证见 [服务器部署报告](../../reports/2026-10-11-server-test-workspace.md)。
