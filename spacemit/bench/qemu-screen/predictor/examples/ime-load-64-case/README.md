# 实际 IME 加载轨迹示例

此示例包含 64 个完整夹具用例。
每臂包含 5,504 条实际指令。
原始 QEMU 轨迹来自 V1 的 `ime-r2/ime-load-isolated-*`。
生成端逐条核对实际程序计数器、指令字节和结束记录。
`program.json` 保存原始轨迹、库存和二进制的 SHA-256。

原始证据位于 `spacemit/reports/raw/k1-predictor-v1-20261011/server-evidence.tar.gz`。
V2 报告另存生成后的紧凑程序与跨机器复核记录。
紧凑程序只重放局部加载函数，不包含完整 IME 点积。
它不能提供完整 IME 加速结论。

在仓库根目录执行下列命令。
输出目录必须不存在。

```bash
python3 spacemit/bench/qemu-screen/predictor/demo.py --output lab/k1-cost-demo
```

此命令只需要 Python 3 标准库。
输出包括两臂成本、声明场景范围、覆盖缺口、投入优先级和收据。
全部候选均保留。
