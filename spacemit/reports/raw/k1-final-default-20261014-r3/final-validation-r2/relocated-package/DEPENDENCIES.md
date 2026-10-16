# 构建依赖与模型身份

## 工具链和运行库

目标为 SpacemiT K1、Linux 和 RISC-V 64 位用户空间。
重新构建需要 Git、Python 3、CMake、Ninja 和支持 IME 内建函数的 GCC 14。
测试需要 tmux 和 flock。
运行需要 SPERT 0.6.2、`libspine_tcm.so.3.0.1` 和系统 C／C++ 动态库。
必须核对 `build/build-receipt.json` 中的确切文件哈希。
版本号相同但文件字节不同的运行库不能自动继承本次验证结果。

本包保留本项目生成的动态库。
本包不分发厂商编译器、SPERT 或 TCM 用户态库。
当前没有补齐这些依赖的统一公开下载归档。
独立取得确切依赖仍是交付限制。
不同依赖版本必须单独构建和验证。

| 设置 | 用途 | 默认路径 |
| --- | --- | --- |
| `K1_CC` | C 编译器 | `$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/gcc-14` |
| `K1_CXX` | C++ 编译器 | `$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14` |
| `K1_SPERT_DIR` | SPERT 根目录 | `$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2` |
| `K1_TCM_DIR` | TCM 用户态库目录 | `$HOME/Projects/llm-bench/.toolchain/spine-tcm` |

这些设置指定依赖位置，不选择优化配置。
启动入口也可以接收 `--spert` 和 `--tcm`。
归档迁移后必须重新核对动态库解析路径。

## 模型

| 模型规格 | 文件名 | SHA-256 |
| --- | --- | --- |
| 2B | `Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf` | `56f0ddd90dfa0e2456af6cb4718ece419678d21a75d65e27353319b5e431a2fa` |
| 4B | `Qwen3.5-4B-MTP-Q4_0-embQ4_0-dv64k.gguf` | `0adf6cce5df53921606033c39a13fae2054543b78af0e7ff98860e86f078ac0f` |

模型权重必须另行取得。
当前直接复现需要上述两个确切产物。
当前没有一个公开归档可直接提供这两个最终产物。
历史加工从第三方 GGUF 开始，不能记为已完成官方全链转换。
模型来源与完整转换验收状态见 `VALIDATION.md`。
文件名包含 MTP 张量标识。
交付默认使用直接解码，不使用 MTP 草稿解码。

起点和最终构建使用相同权重与精度。
性能对照不包含模型量化变化的收益。
新的模型产物必须重新核验张量、词元器、模板、回答与性能。
启动入口会拒绝不符合清单的模型。

## 用户态库与硬件能力

TCM 用户态库可用不表示真实 TCM 映射已验证。
当前普通用户环境缺少 `/dev/tcm_sync_mem`，初始化屏障使用堆内存回退。
真实 TCM 访问的权限和映射限制见 `VALIDATION.md`。
不能把旧的独立硬件测试结果记为本次模型推理收益。
