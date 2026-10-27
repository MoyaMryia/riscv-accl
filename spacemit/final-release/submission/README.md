# K1 最终成果

本包面向成果评审与复现。
两个模型共用 `k1-final-20261013-r3` 的同一份生产二进制。
普通启动使用固化默认参数，无需手动开启优化配置。
完整文件身份见 `manifest.json` 和 `SHA256SUMS`。
六项交付内容与检查状态见 `SUBMISSION-CHECKLIST.md`。

## 结果

最终版完成一次请求的速度，2B 为厂商起点的 1.24～3.59 倍，4B 为 1.41～4.72 倍。
输入 512 词元时倍数最小，32768 词元时倍数最大。
服务器内存基本不变，两臂之差小于 3 MiB。
逐形状数据见 `reports/SUBMISSION-ZH.pdf`（中文）和 `reports/SUBMISSION-REPORT.pdf`（英文，含证据附录）。

## 核对文件

在成果包根目录执行完整文件检查。

```sh
sha256sum -c SHA256SUMS
python3 evidence/verification-tools/verify-submission.py \
  --root . --output /tmp/k1-submission-new-verification.json
```

输出文件必须不存在。
独立检查同时核对原生产源码、干净转换源码、模型身份和补测记录。

## 内容

| 路径 | 内容 |
| --- | --- |
| `runtime/source/` | 完整可构建源码与许可证 |
| `runtime/build/` | K1 可执行文件、项目动态库和构建收据 |
| `runtime/package/` | 固定默认启动器、重建脚本与完整补丁 |
| `deploy.sh` | 创建 tmux 会话并受锁启动服务的一键入口 |
| `converter-source/` | 固定官方转换工具源码 |
| `model-materials/` | 官方输入身份、转换、量化与打包脚本 |
| `tools/tcm/` | 真实 TCM 用户态接口；当前设备权限下明确拒绝硬件申请 |
| `docs/` | 部署、模型加工、设计和依赖说明 |
| `reports/` | 起点与优化性能报告、综合报告及 TeX/PDF |
| `evidence/` | 原始记录、核验收据和归档身份 |

## 启动

先准备 [依赖](DEPENDENCIES.md)中的确切运行库与现用模型。
在 K1 上解压本包。
在成果包根目录执行下列命令。

```sh
bash deploy.sh /absolute/path/to/model.gguf
```

入口创建独立 tmux 会话。
服务器取得项目共用锁后核对模型、二进制与运行库身份。
模型加载结果写入日志。
服务就绪必须通过 `/health` 核对。
完整步骤见 [部署说明](DEPLOYMENT.md)。

## TCM 补充检查

[TCM 调查报告](../../reports/2026-10-16-final-release-tcm.md)核对实际推理的设备访问。
[用户态接口](../../tcm/README.md)提供状态查询和受锁保护的块访问。
普通用户打开 `/dev/tcm` 返回 `EACCES`，测试推理没有使用硬件 TCM。
生产源码、二进制与默认参数保持原身份。

## 后续验收记录

下列报告记录 2026-10-16 之后的独立验收，随包放在 `reports/`。

- 官方检查点加工：两个检查点完成转换、量化和打包（[报告](../../reports/2026-10-21-official-conversion.md)）。
- 固定多轮 v2：48 轮请求全部完成；独立复核 2B 15/24、4B 19/24 正确（[报告](../../reports/2026-10-21-fixed-multi-turn-v2-results.md)）。
- 自然长上下文：短、16k、32k 档位共 12 次回答全部正确（[报告](../../reports/2026-10-22-long-context-natural-results.md)）。

## 适用范围

[模型转换说明](MODEL-CONVERSION.md)提供从固定官方检查点开始的完整命令。
当前实测使用历史加工的两个固定 GGUF。
旧独立硬件测试结果属于各自历史配置，不计入本发布推理收益；仓库内的完整范围见 `spacemit/reports/HISTORY.md`。
本包不包含模型权重、厂商运行库或凭据。
16k／32k 补测只扩大上下文容量，普通默认容量仍为 12288。
配置与样本数见综合报告的“适用范围”。

- 待验证：长状态正确性。阻塞：r3 上没有长状态检查。解除条件：在 r3 上执行长状态检查。
- 待验证：8192、16384 和 32768 输入的重复稳定性。阻塞：这些形状只有 1～2 对。解除条件：每形状至少测量 3 对。
- 待验证：真实 TCM 块读写与推理收益。阻塞：`/dev/tcm` 只允许 root 访问。解除条件：取得合法设备访问权限后执行块读写检查和配对推理测量。
