# K1 第二版模型证据

本目录保存原始证据与机器生成复核结果。
不得改写已保存的记录。
当前阶段为可运行基建，完整算子预测精度仍待验证。
全部候选均保留。

## 归档

| 文件 | SHA-256 | 内容 |
| --- | --- | --- |
| `local-evidence.tar.gz` | `50d1de5d668d3ad755901abe5f07957621abd56b0dad33c4860da777a0e2699d` | 全部板端成功样本、夹具失败、参数、实际库存、紧凑轨迹、模型结果与交付代码 |
| `server-evidence.tar.gz` | `d04a6520675f95ce62cae0871883fa9fb418ca8d0b2296fe609346f37b625ae0` | 服务器全部模型版本、实际微内核轨迹、成本结果、任务日志和冻结代码 |

本地归档共核验 4,141 个文件、99 个收据文件和 8,209 个收据条目。
服务器归档共核验 1,520 个文件、67 个收据文件和 1,569 个收据条目。
两项核验均无缺失或散列差异。
本地归档的六个板端输出收据使用载荷根目录。
`receipt-bases.json` 明确记录这些基目录。
其他收据使用收据所在目录。

## 可直接读取的记录

- `state.json`：已完成项、精度限制与未完成项。
- `host-results.json`：最终模型全部场景、覆盖缺口与宿主耗时。
- `microkernel-validation.json`：旧留出组合的全部周期与收益误差。
- `priority-predicted.json`：声明场景优先级，范围不具有统计置信度。
- `priority-measured.json`：全部板端短测候选与配对区块测量区间。
- `model-diagnosis.json`：按实际动态指令数量生成的补齐顺序。
- `portability-check.json`：本机与服务器的模型身份及场景结果一致性。
- `unit-tests.log`：46 项检查的完整输出。
- `local-archive-verification.json`：本地归档独立复核。
- `server-archive-verification.json`：服务器归档独立复核。
- `v1-unchanged-verification.json`：V1 根收据的 12 项身份检查。
- `shipped-profile-verification.json`：随仓库交付参数的四项身份检查。

V1 的完整原始轨迹仍位于 `spacemit/reports/raw/k1-predictor-v1-20261011/`。
本版没有改写该目录。
板端所有正式批次使用 tmux 与共用锁。
本轮任务结束时，板端共用锁已释放。

## 独立核验

在项目根目录执行下列命令。
输出文件必须不存在。

```bash
python3 spacemit/bench/qemu-screen/predictor/verify-evidence.py \
  --archive spacemit/reports/raw/k1-model-v2-20261011/local-evidence.tar.gz \
  --expected-sha256 50d1de5d668d3ad755901abe5f07957621abd56b0dad33c4860da777a0e2699d \
  --receipt-bases spacemit/reports/raw/k1-model-v2-20261011/receipt-bases.json \
  --output lab/k1-v2-local-independent-check.json
```
