# 外部依赖与模型身份

## 构建与运行依赖

目标为 SpacemiT K1、Linux 与 RISC-V 64 位用户环境。
需要 Git、Python 3、CMake、Ninja、tmux、flock 和支持 IME 内建函数的 GCC 14。
运行需要与本次构建匹配的 SPERT 0.6.2 和 `libspine_tcm.so.3.0.1`。
运行还需要系统 C／C++ 动态库。
包内保留全部本项目生成的动态库。
启动器核验外部 SPERT 与 TCM 文件身份，拒绝不同字节的替代品。

本包不分发厂商编译器、SPERT 或 TCM 运行库。
请从当前 K1 厂商工具链安装或项目保留的依赖安装包取得这些文件。
本次没有补齐其统一公开下载归档，独立获取仍是交付限制。
实际编译器版本、文件 SHA-256 和依赖 SHA-256 见 `build/build-receipt.json`。
实际动态库解析路径见 `evidence/ldd-*.log`。
验证结束后的工具与动态库身份见 `evidence/post-validation-tools.json`。
新安装若使用其他版本，必须重新构建并保存新验证记录。

| 设置 | 作用 | 本项目默认路径 |
| --- | --- | --- |
| `K1_CC` | C 编译器 | `$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/gcc-14` |
| `K1_CXX` | C++ 编译器 | `$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14` |
| `K1_SPERT_DIR` | SPERT 安装根目录 | `$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2` |
| `K1_TCM_DIR` | TCM 兼容库目录 | `$HOME/Projects/llm-bench/.toolchain/spine-tcm` |

这些路径是外部依赖位置，不是候选实验动态库位置。
运行时可用 `--spert` 和 `--tcm` 指定新位置。
本包不要求旧实验目录存在。

## 两个模型

| 模型 | 文件名 | SHA-256 |
| --- | --- | --- |
| 2B | `Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf` | `56f0ddd90dfa0e2456af6cb4718ece419678d21a75d65e27353319b5e431a2fa` |
| 4B | `Qwen3.5-4B-MTP-Q4_0-embQ4_0-dv64k.gguf` | `0adf6cce5df53921606033c39a13fae2054543b78af0e7ff98860e86f078ac0f` |

权重必须另行取得，本包不附带模型文件。
当前直接复现需要项目保留的上述两个确切产物。
现有材料没有一个可以直接下载这两个最终产物的统一公开归档。
历史模型加工以第三方 GGUF 开始，不能记为已完成官方全链转换。
文件名包含 MTP 张量身份，默认推理仍为直接解码。

官方输入修订与复现准备见 `model-materials/official-source-lock.json` 和 `model-materials/REPRODUCIBILITY.md`。
完整官方检查点需要另行下载。
加工还需要转换器的 Python 依赖、可执行量化器、元数据证据和足够的中间文件空间。
`model-materials/tools/reproduce-official.sh` 提供转换、量化与打包入口。
两个模型的实际完整官方流程仍待验证。

包内 `source/` 已包含优化改动，不能冒充干净转换源码。
官方加工必须使用与 `package/vendor-source.json` 相同的干净厂商源码。
新的官方产物不能自动继承现用产物的性能。
新产物必须单独核验张量、词元器、模板、本地推理和匹配性能。
统一启动器会拒绝不符合现用清单的权重。
