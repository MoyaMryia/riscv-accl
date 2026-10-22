# K1 单一默认交付

本目录提供交付元数据、启动脚本与成果包的组装模板。
六项材料与组装要求见[交付计划](SUBMISSION-PLAN.md)。
`submission/` 保存成果包的[顶层说明模板](submission/README.md)与独立部署说明。
[组装脚本](stage-submission.py)把这些模板复制到成果包。
本机根目录的 `final-release/` 保存完整成果包，但 Git 不分发该目录。
成果包内的 `SUBMISSION-CHECKLIST.md` 记录六项内容及验收限制。
补测收据、两模型新入口检查和报告均随包保存。
最终归档与解压核验身份见本目录的 `committee-receipt.json`。
2026-10-22 同步后的成果包归档身份见[package-receipt.json](package-receipt.json)。
本目录原有 r3 元数据与原归档身份仍保留。

已验证版本为 `k1-final-20261013-r3`。
两个模型共用同一份生产二进制和同一组编译默认值。
普通启动不需要性能参数或优化环境变量。
默认值为 4 线程、批大小与微批大小 32、上下文 12288、单槽、F16 缓存、宽 RVV、IME route 3、B1-r2 与 C1。
C2-r2 与 MTP 草稿解码关闭。

完整交付归档位于本机 `lab/final-default-20261013/release/k1-final-20261013-r3.tar.gz`。
文件身份与核验结果见本目录的 `archive-receipt.json`。
归档不随 Git 分发，也不包含模型权重或厂商运行库。
依赖身份和独立获取限制见 [DEPENDENCIES.md](DEPENDENCIES.md)。
模型身份见 [manifest.json](manifest.json)。
选择记录见 [default-policy.json](default-policy.json)。
实测结果和样本限制见[最终对照报告](../reports/2026-10-14-final-default-comparison.md)。
[16k／32k 补测](../reports/2026-10-16-ultralong-final-comparison.md)追加 12 次匹配请求。
[TCM 调查](../reports/2026-10-16-final-release-tcm.md)记录最终版的实际设备访问。

## 后续验收记录

| 项目 | 当前记录 |
| --- | --- |
| 官方全链加工 | 已验证：两个检查点完成转换、量化和打包，收据见[加工报告](../reports/2026-10-21-official-conversion.md)。 |
| 固定多轮质量 | 已验证：原 r3 与历史模型完成 [v2 全部 48 轮测量与人工复核](../reports/2026-10-21-fixed-multi-turn-v2-results.md)；[原验收失败](../reports/2026-10-21-fixed-multi-turn-results.md)分别保留。 |
| 长上下文自然回答 | 已验证：原 r3 与历史模型完成两个任务的短、16k、32k 档位检查，见[自然回答与内存结果](../reports/2026-10-22-long-context-natural-results.md)。 |
| 部分请求 MTP | 文档字符串收益规则与 BERT 类别代理分别记录，见[版本澄清](../reports/2026-10-21-routing-version-clarification.md)。 |

上述记录作为独立补充材料提供。
同步脚本把报告、入口页、清单与文件散列更新到当前仓库状态。
原始归档、生产二进制与模型权重保持不变。

## 同步成果包

[同步脚本](update-package.py)从当前仓库复制报告与引用闭包，并重新生成清单与散列。

```sh
python3 spacemit/final-release/update-package.py
```

同步覆盖 `reports/`、`project/`、入口页、`manifest.json` 与 `SHA256SUMS`。
脚本不改写 `evidence/` 中的原始归档，也不复制模型权重。
报告身份见[report-receipt.json](report-receipt.json)；本次同步的计数与归档身份见 `evidence/report-refresh-receipt.json`。
原 r3 和委员会成果包的归档、生产模型、二进制与默认配置保持不变。
原归档内的说明按冻结时的状态读取。

## 使用

解压归档。
在 tmux 中切换到版本根目录。
将模型路径替换为现用文件。

```sh
bash package/with-lock.sh python3 package/start.py --model /path/to/model.gguf
```

两个模型只需更换模型路径。
依赖目录不同时，可以传入 `--spert` 和 `--tcm`。
入口核对模型、二进制和运行库身份，并清除继承的实验变量。
归档内的 README、完整源码、构建脚本、测试与收据用于复现。

## 验证范围

已验证：789 项算子检查、64 条短状态全词表记录、两模型迁移启动、6 次自然回答和 28 次匹配性能请求。
短输入各形状每臂 3 次，8192 输入各模型每臂 1 次。
配置是冻结搜索范围内的均衡选择，不能解释为所有负载的全局最优。
后续验收状态见上表与对应报告。
原冻结归档和旧失败记录保持原字节。
