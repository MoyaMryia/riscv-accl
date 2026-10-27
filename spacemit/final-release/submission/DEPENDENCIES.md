# 运行依赖与模型身份

## 运行库

目标为 K1、Linux 和 RISC-V 64 位用户空间。
运行必须提供 Python 3、Bash、tmux、flock 和系统 C／C++ 动态库。
服务检查还需要 `curl`。
重建另需 CMake、Ninja 及支持厂商 IME 内建函数的 GCC 14。
模型加工的 Python 依赖由固定转换源码中的 requirements 文件指定。

| 运行库 | 已测版本 | SHA-256 |
| --- | --- | --- |
| `libspert.so.0.6.2` | SPERT 0.6.2 | `0db8febc30aa49d6915c174a8f65b076dbbc7f61a4a3a6e18319eb0aa289b7fe` |
| `libspine_tcm.so.3.0.1` | TCM 用户态库 3.0.1 | `cafb7ae99e0490e3df2f5b29c44c41e87dc07413a85bf19e7f4e68c0e99c4e2b` |

完整依赖及别名身份见 `runtime/build/build-receipt.json`。
启动器按该收据核对文件，不只核对版本号。
厂商编译器、SPERT 与 TCM 用户态库不随包分发。
当前没有一个统一公开归档提供全部确切依赖。
独立取得这些依赖仍是复现限制。
不同依赖字节必须独立验证。

| 设置 | 默认目录 |
| --- | --- |
| `K1_SPERT_DIR` | `$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2` |
| `K1_TCM_DIR` | `$HOME/Projects/llm-bench/.toolchain/spine-tcm` |
| `K1_CC` | `$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/gcc-14` |
| `K1_CXX` | `$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14` |

路径不同可以通过部署入口的 `--spert`、`--tcm` 或重建脚本环境变量指定。
这些设置只定位依赖，不选择优化配置。
本包保留项目生成的动态库，不包含厂商运行库。
迁移后必须重新核对动态库解析和文件身份。

## 实测模型

| 模型文件 | SHA-256 |
| --- | --- |
| `Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf` | `56f0ddd90dfa0e2456af6cb4718ece419678d21a75d65e27353319b5e431a2fa` |
| `Qwen3.5-4B-MTP-Q4_0-embQ4_0-dv64k.gguf` | `0adf6cce5df53921606033c39a13fae2054543b78af0e7ff98860e86f078ac0f` |

模型权重另行取得，不随本包分发。
当前没有一个公开归档直接提供这两个确切最终产物。
现用模型来自历史 Unsloth GGUF 加工。
官方检查点的转换、量化、打包与结构核验已验证（[2026-10-21 报告](../../reports/2026-10-21-official-conversion.md)）；新产物的 K1 加载与回答未执行。
文件名含 MTP 标识，但交付默认关闭草稿解码。
起点和优化版使用相同文件，性能收益不包含量化变化。
新模型产物必须重新检查结构、词元器、模板、自然回答和匹配性能。

## 设备能力边界

本次测量使用普通用户和固定共用锁。
实际设备权限、堆内存回退与相关限制保留在报告中。
模型缓冲区的 TCM 映射核验见[TCM 调查报告](../../reports/2026-10-16-final-release-tcm.md)。
旧独立硬件测试结果的范围见[交付说明](../README.md)适用范围。
