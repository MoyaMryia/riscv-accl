# 源材料补证收据

本目录保存 `source-proof-20261016-135448-r2` 的机器生成收据。
运行入口为 [run.sh](run.sh)，退出码记录为 [exit-status](exit-status) 中的 0。
原始日志为 [run.log](run.log)。

## 结论

| 项目 | 记录值 |
| --- | --- |
| 官方仓库与修订 | `Qwen/Qwen3.5-4B`，`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` |
| MTP 张量数量 | 15 |
| MTP 张量字节合计 | 241199104 |
| 张量数据类型 | BF16 |
| 官方输入范围 | 见 [result/proof.json](result/proof.json) 的 `official_tensors.ranges` |
| 重建 4B MTP GGUF | 2447892576 字节，SHA-256 `e575502912e015bd3eed928758736a31fd6a0fe5c59d3c49c2682f4569738b2a` |
| 参考模型 | 2447892576 字节，SHA-256 `e575502912e015bd3eed928758736a31fd6a0fe5c59d3c49c2682f4569738b2a` |
| 文件哈希比较 | `model_hash_match` 为 `true` |
| GCC 驱动 | SHA-256 `86da68a5e45428d55f75bed370c0f2a76fee28f2b1e7f502a7025f2f536fabcc` |
| G++ 驱动 | SHA-256 `0b6e036db6feff00507b4b3ff7b4d80bd708683557f45bebe570b8184da2d2f2` |
| GCC 软件包 | SHA-256 `f4b8e008cbfc905d6d994c8a4968b4483d99acd4aa85fca343cff05306026d02`，29512878 字节 |
| G++ 软件包 | SHA-256 `1809d9acc79cf617bb66206156fa004dff165d614f56879a6a17caf51242dd40`，16590580 字节 |

两条结论如下。
第一，15 个 BF16 MTP 张量来自固定的官方修订，字节数与逐张量 SHA-256 均记录在 `proof.json`。
第二，用相同输入重建的 4B MTP GGUF 与历史参考模型逐字节相同，两个文件的 SHA-256 一致。

## 文件清单

| 文件 | 字节 | SHA-256 |
| --- | ---: | --- |
| `add-mtp-4b.py` | 8661 | `da10cd6faca26f7cb62c947e7a4a8f1546519b77a5c40e8326ee9541b44de408` |
| `exit-status` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| `extract-mtp-safetensors.py` | 4405 | `78ee9ad37747aecda9b5076c17113bbe672810a1c1b81298d52d7b4b711f7205` |
| `official-source-lock.json` | 2747 | `13c19ea464d028091859ae6ee6d64592cbc6d64f8fe2ccbce3c5cd7b3229aab1` |
| `prove-sources.py` | 11539 | `2035c0f4d493d914022118249085e8208563dc3339b7eebeb772feeeae27c23a` |
| `result/compiler-result.json` | 913 | `1c332ee51e20d68501c79eaf0b31fe996028f35851b06e2c0df40bbc03f0120e` |
| `result/mtp-tensors/meta.json` | 8737 | `4dc3e085b975bfc1eb9a7ca58e1116c45b807714e1dc74628f67823f8ed0d0ed` |
| `result/proof.json` | 12942 | `52a04ee32a4474d6e9b431a7856f7b70915c5cb62bd59bfb6485569aa0ad48a8` |
| `run.log` | 2165 | `50fd73080dc6835e7b32711ae566ad005a9bebc87a33c0e545a8d069bcefd4f9` |
| `run.sh` | 1180 | `c3b298a43417628404e8b5fff954f37e9cdefa1d9331e75423b99d54190c3b8c` |

## 复现边界

本目录保存收据和脚本，不保存 2.4 GB 的重建 GGUF 与 2.3 GB 的基础模型。
两个大文件的路径、字节数和 SHA-256 记录在 [result/proof.json](result/proof.json) 的 `inputs` 与 `reproduced_model`。
`add-mtp-4b.py` 与 `extract-mtp-safetensors.py` 与 [加工工具目录](../../../models/tools/)中的同名文件哈希相同。
`prove-sources.py` 与 `official-source-lock.json` 在本目录保存，后者与[官方输入锁定清单](../../../models/official-source-lock.json)逐字节相同。
复现需要网络连接、HF 镜像和约 5 GB 工作空间；命令见 [run.sh](run.sh)。
