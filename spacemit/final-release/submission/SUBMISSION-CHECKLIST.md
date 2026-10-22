# 六项交付检查

| 项目 | 材料 | 状态与限制 |
| --- | --- | --- |
| 可运行代码 | `runtime/source/`、`runtime/build/`、`runtime/package/` | 已验证原 r3 生产构建，两个模型共用同一二进制。 |
| 一键部署 | `deploy.sh`、`deploy.py` | 7 项本地入口检查及两模型板端迁移、默认值、共用锁和健康检查通过。 |
| 官方转换与量化脚本 | `model-materials/tools/`、`converter-source/` | 已验证：两个官方检查点完成实际全链转换与打包，新产物与历史 GGUF 分别记录。 |
| 转换与部署说明 | `docs/` | 提供固定修订、命令、依赖身份、日志和新产物验收步骤。模型权重与厂商依赖另行提供。 |
| baseline 与优化性能报告 | `reports/`、`evidence/` | 已验证：28 次普通默认请求、12 次容量扩展请求；固定多轮 v2 完成 48 轮请求，2B 15/24、4B 19/24 正确；自然长上下文 12 次回答正确。中文报告 `reports/SUBMISSION-ZH.pdf`，英文报告 `reports/SUBMISSION-REPORT.pdf`。 |
| 框架改造设计 | `docs/DESIGN.md` | 说明宽 RVV、IME route 3、B1-r2、C1、固化默认值、回退和未采用方案。 |

数值算子、短状态与自然回答的原验证记录随生产归档保留。
长状态正确性和重复稳定性列为后续验收项。
本包不把标准 Q4_0 量化描述为新量化算法。
已补充 TCM 用户态工具与设备访问证据；本轮推理没有使用硬件 TCM。
