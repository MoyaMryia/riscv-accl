# K1 性能分析基建证据索引

日期：2026-10-11，Asia/Singapore。
本目录是本轮新建的证据集。
原有证据目录保持不变。
封存后不得修改本目录文件。

## 直接结果

- [统一机器报告](suite.json)：真实代码覆盖、模型验收和独立原型板测。
- [统一中文报告](analysis-report.md)：与机器报告对应的可读结果。
- [周期模型验收](calibration-validation.json)：5 个独立测试组与最终排序统计。
- [原型板测结果](native-result.json)：13 组形状、156 个计时样本的门槛结果。
- [原型独立复核](native-audit.json)：身份、时长、亲和性、频率和门槛重算。
- [交付检查日志](delivery-tests.log)：32 项检查通过。

## 完整归档

两个归档都使用 `lab/k1-predictor-20261011-v1/` 作为顶层路径。
必须分别解包到不同的新目录，防止同名文件相互覆盖。
不需要解包即可检查归档 SHA-256。

| 文件 | 内容 | 原始 SHA-256 |
| --- | --- | --- |
| [服务器证据](server-evidence.tar.gz) | 完整动态轨迹、旧失败记录、最终重放、实际库存、MCA 输入输出、加载映射与板端周期副本 | `bdaba99711d303dc3e10c8f53b3018c0aa3af684ad5167b3bd8f28034542723b` |
| [本地证据](local-evidence.tar.gz) | 固定公开来源、补丁核验、API 4 实际执行、板端能力与周期原件、原型完整载荷、输出、工具源码和最终报告 | `b2fb49e3d3290094676914117593bd51511cf6658d24e82e9bbf0a68aaa825d5` |

服务器归档散列来自服务器产生端，并在本地独立核验。
[服务器核验结果](archive-verification.json)包含 914 个文件、38 个收据文件和 948 个已核验条目。
[本地核验结果](local-archive-verification.json)包含 602 个文件、40 个收据文件和 564 个已核验条目。
两个归档均未发现收据目标缺失或散列差异。

归档模式默认按各收据所在目录解释文件路径。
原型 `native-payload/run/SHA256SUMS` 的路径基准是 `native-payload/`。
该例外在本地核验结果的 `declared_receipt_bases` 中显式声明。
本地独立核验脚本为 [verify-local-archive.py](verify-local-archive.py)。
解包后，也可以使用通用 `verify-evidence.py --receipt` 并显式提供该基目录。

## 归档内位置

以下路径都相对于归档的顶层目录。

- `implementation/`：交付工具、中文说明、报告及源码收据。
- `suite-delivery/`：最终统一报告与输入、源码身份。
- `validation-final/`：最终模型验收结果。
- `board-capability/`：周期事件可用性与 `rdcycle` 失败证据。
- `board-calibration/`：240 个周期样本、实际二进制与原始收据。
- `native-payload/protocol.md`：真实原型补充协议。
- `native-payload/`：冻结执行脚本、实际二进制、共享库、IME 夹具源码与输入收据。
- `native-payload/run/`：完整数值输出、156 个计时样本、161 个命令记录和输出收据。
- `native-provenance/`：既有原型的源文件、构建命令和共享库清单。
- `native-environment.log` 与 `native-runtime-identities.log`：K1 处理器、运行库及版本散列。
- `sources/`、`source-addendum/`、`rvv-source-final/`：固定公开来源、许可、补丁和下载失败记录。
- `vendor-integration/`：API 4 与不支持 IME 编码的实际停止检查。

服务器归档另外包含 `conv/`、`ime-r2/`、`b2-r3/` 和 `b2-tile16/` 的完整轨迹。
早期 `ime/`、`b2/` 和 `b2-r2/` 记录保留初始夹具问题。
不得把这些问题改记为候选数值失败或性能结论。

## 固定边界

冻结执行脚本与交付脚本分别保存。
交付脚本增加的样本一致性检查已在全部已有样本上复核。
新增周期包装脚本尚未在板端执行，首次周期测量使用锁内原生命令。
MCA 模型未通过独立验收，自动性能淘汰保持关闭。
缓存统计不等于物理流量或周期。
真实原型短测不属于合成微内核测试集，也不构成整机收益结论。
