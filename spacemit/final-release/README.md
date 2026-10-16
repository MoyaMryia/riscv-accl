# K1 单一默认交付

本目录提供交付元数据、启动脚本与成果包的组装模板。
六项材料与组装要求见[交付计划](SUBMISSION-PLAN.md)。
`submission/` 保存成果包的[顶层说明模板](submission/README.md)与独立部署说明。
[组装脚本](stage-submission.py)把这些模板复制到成果包。
本机根目录的 `final-release/` 保存完整成果包，但 Git 不分发该目录。
成果包内的 `SUBMISSION-CHECKLIST.md` 记录六项内容及验收限制。
补测收据、两模型新入口检查和报告均随包保存。
最终归档与解压核验身份见本目录的 `committee-receipt.json`。
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
官方来源、完整转换、长状态稳定性与固定多轮质量仍有验收缺口。
旧失败证据保留在完整归档中。
