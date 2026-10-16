# 模型来源与转换复现记录

记录日期：2026-10-12，Asia/Singapore。
本文件对应 [Requirements.md](../../Requirements.md) 的模型来源与可复现加工要求。
GGUF 是本项目推理工具读取的模型文件格式。
safetensors 是本次官方检查点的张量存储格式。

## 当前结论

已验证：项目历史报告记录了现用模型从 Unsloth GGUF 开始的加工过程。
已验证：现用两个最终 GGUF 的 SHA-256 已写入发布清单。
已验证：当前 Unsloth 模型仓库把对应 Qwen 官方后训练模型列为来源。
已实现：从固定官方 safetensors 开始的转换、量化、打包和收据脚本。
待验证：两个完整官方检查点的实际转换与推理。
待验证：新官方产物与现用产物的文件、张量、词元器和推理差异。

能够转换出文件是必要步骤。
它不能单独证明历史模型来源、数值正确性或新模型性能。
复现记录必须包含实际成功日志和产物身份。
本次只准备流程并收集来源元数据，没有下载完整权重。

## 1. 官方名称与要求名称

| 要求中的名称 | 本次可公开核验的官方仓库 | 官方模型说明 | 对应关系状态 |
| --- | --- | --- | --- |
| `Qwen3.5-2B-Instruct` | [Qwen/Qwen3.5-2B](https://huggingface.co/Qwen/Qwen3.5-2B) | 后训练模型，提供对话用法与指令模式评测。 | 已验证官方产品属性。要求名称与仓库名称的对应说明仍需写入验收记录。 |
| `Qwen3.5-4B-Instruct` | [Qwen/Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B) | 后训练模型，提供对话用法与指令模式评测。 | 同上。 |

本次选择上述后训练仓库作为官方复现输入。
本次没有选择带 `-Base` 后缀的预训练仓库。
本次访问两个带 `-Instruct` 后缀的 API 路径均返回 HTTP 401。
这个响应不能证明对应仓库不存在。
本次没有改写 Requirements.md 的模型名称。

## 2. 现用模型来源链

历史报告见 [2026-09-21 记录](../reports/2026-09-21-final.md)。
现行加工工具见 [工具说明](tools/README.md)。

| 模型 | 已记录的历史加工链 | 最终产物 SHA-256 |
| --- | --- | --- |
| 2B | Unsloth GGUF 已包含 MTP 张量。项目执行 Q4_0 加工并追加 65,536 行草稿头。 | `56f0ddd90dfa0e2456af6cb4718ece419678d21a75d65e27353319b5e431a2fa` |
| 4B | Unsloth GGUF 缺少 MTP 张量。项目另取 safetensors 的 15 个 MTP 张量，完成量化、归一化权重转换和组装，再追加草稿头。 | `0adf6cce5df53921606033c39a13fae2054543b78af0e7ff98860e86f078ac0f` |

MTP 表示多词元预测。
草稿头只服务于相应投机解码路径。
主要性能验收关闭 MTP。
模型文件含有这些张量不表示运行时启用了 MTP。

本次保存了 [Unsloth 2B](https://huggingface.co/unsloth/Qwen3.5-2B-GGUF) 与 [Unsloth 4B](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF) 的当前元数据。
其来源字段分别为 `Qwen/Qwen3.5-2B` 和 `Qwen/Qwen3.5-4B`。
这支持模型家族来源说明。
它不能证明当初下载的确切仓库修订和原始文件。
本次查询得到的最新 Unsloth 修订不能倒填为历史下载修订。
历史加工不是本项目从完整官方 safetensors 开始转换的证明。

## 3. 固定官方输入

以下修订在本次公开元数据查询中固定。
权重 SHA-256 来自该仓库元数据，尚未通过本机完整下载核对。

| 模型 | 固定修订 | 官方权重文件及 SHA-256 |
| --- | --- | --- |
| 2B | `15852e8c16360a2fea060d615a32b45270f8a8fc` | `model.safetensors-00001-of-00001.safetensors`：`aa33250c4fc64891ddfaba3a314fd9542ea371843c387178b425fbcc5ed680b1` |
| 4B | `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` | `model.safetensors-00001-of-00002.safetensors`：`26a93f066e1916adb13453dae5a0c707c0fbc71299ed98779571a907b8e74c61`；`model.safetensors-00002-of-00002.safetensors`：`cb544bd9bfae93dc59b0f22b292f5933573854a7f9b97835c67060d7d910e188` |

2B 权重下载量为 4,548,221,488 字节。
4B 权重下载量为 9,319,828,096 字节。
这些数值不含转换中间文件和最终 GGUF。
下载前必须为源文件、BF16 GGUF 和两个 Q4_0 产物预留空间。

已验证：官方配置中的主模型层数分别为 24 和 32。
已验证：两个配置均声明一个 MTP 层。
已验证：两个官方索引各包含 15 个 MTP 张量名称。
分片索引中的全部张量数量分别为 632 和 738。
本次没有读取完整权重数据，因此这些检查不能替代权重内容验证。

## 4. 固定转换工具

转换源码使用 SpaceMiT `llama.cpp` 的固定快照。
修订为 `a990751d55a4c54acf2bb77d44282c2093652359`。
本机保留目录为 `lab/local-reference/source-a990751-clean/`。
本次重新核对该快照的 3,266 个文件，全部匹配已归档收据。
该目录没有自己的 Git 元数据，不能用向上查找得到的项目提交冒充其源码修订。

| 文件 | SHA-256 |
| --- | --- |
| `convert_hf_to_gguf.py` | `8f1bed9466221e57e434caa7ee720abe1569deb6bc2fe5a65da950ea66c8e737` |
| `conversion/qwen.py` | `07447bde7fcb7989d659a1d0c7ee6428a04493e4d6c67cd6b2bfd8759d30d8de` |
| `conversion/base.py` | `d4c8de9cd5bd6499c2a7ee9b41bc315e8b04a0cba9f19cd0f26140ecdf380484` |

已实现：该转换器支持 `Qwen3_5ForConditionalGeneration`。
已实现：默认转换包含 MTP 张量的映射与元数据。
已实现：`--no-mtp` 可以排除 MTP。
本复现脚本选择默认保留 MTP，再追加项目草稿头。
该选择是为了记录与现有文件结构接近的加工流程。
它不保证输出与 Unsloth 衍生产物逐字节相同。

官方检查点包含视觉组件。
本次脚本执行文本模型转换，没有请求 `--mmproj` 视觉投影器导出。
不能据此宣称完成图像推理部署。
文本转换不是简单复制张量。
转换器处理张量名称、布局、归一化权重和词元器元数据。

## 5. 可执行复现步骤

以下步骤尚未完成两个模型的实际运行验证。
命令从仓库根目录执行。
模型文件必须放在新的工作目录中。

### 下载固定官方检查点

在隔离 Python 环境中安装 Hugging Face 客户端。
保存实际客户端版本与依赖清单。
执行以下命令。

```bash
hf download Qwen/Qwen3.5-2B \
  --revision 15852e8c16360a2fea060d615a32b45270f8a8fc \
  --local-dir lab/official-models/2B
hf download Qwen/Qwen3.5-4B \
  --revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a \
  --local-dir lab/official-models/4B
```

### 准备转换环境和量化器

必须使用上述固定源码。
可以使用本机核验过的源码快照。
另行获取的快照必须通过同一源码收据。
在独立虚拟环境中安装该源码的 `requirements/requirements-convert_hf_to_gguf.txt`。
保存安装日志与实际依赖清单。
严格离线复现还必须保存依赖安装包及其哈希。
当前脚本只自动记录已安装依赖版本，没有自动封存依赖安装包。

在转换主机上构建该源码的 `llama-quantize`。
保存 CMake 配置、编译器版本、构建日志和动态依赖身份。
转换用量化器必须是转换主机能够执行的二进制。
不能把 K1 的 RISC-V 二进制直接当作本机 x86 量化器。
本次尚未执行新的量化器构建。

### 转换、量化和打包

设置 `MODEL_PYTHON` 为隔离环境中的 Python。
把 `/absolute/path/to/llama-quantize` 替换为已记录构建来源的量化器。

```bash
MODEL_PYTHON=/absolute/path/to/venv/bin/python \
bash spacemit/models/tools/reproduce-official.sh \
  2B lab/official-models/2B lab/local-reference/source-a990751-clean \
  /absolute/path/to/llama-quantize \
  spacemit/reports/raw/model-origin-preparation-20261012 \
  lab/official-models/2B-conversion-r1

MODEL_PYTHON=/absolute/path/to/venv/bin/python \
bash spacemit/models/tools/reproduce-official.sh \
  4B lab/official-models/4B lab/local-reference/source-a990751-clean \
  /absolute/path/to/llama-quantize \
  spacemit/reports/raw/model-origin-preparation-20261012 \
  lab/official-models/4B-conversion-r1
```

脚本拒绝复用已有输出目录。
脚本先核验官方分片、配置和词元器身份。
脚本核验全部固定转换源码文件。
随后脚本依次生成 BF16 GGUF、Q4_0 GGUF 和带草稿头的 Q4_0 GGUF。
量化明确指定词嵌入与输出权重为 Q4_0。
官方 BF16 路径不使用 `--allow-requantize`。
它与历史第三方量化文件再次量化的路径分别记录。

官方默认转换已经包含 MTP，因此不能再无条件执行历史 4B MTP 追加脚本。
重复追加同名张量属于错误加工。
脚本最后重新核验官方输入与固定源码。
成功状态为 `conversion-complete-validation-pending`。
该状态只表示加工完成。

## 6. 必须保存的实际执行记录

| 记录 | 用途 |
| --- | --- |
| `input-receipt.json`、`input-after-receipt.json` | 核验官方固定修订的源文件，并检查加工前后身份。 |
| `source-receipt.json`、`source-after-receipt.json` | 核验固定转换源码。 |
| `tool-receipt.json`、`python-packages.txt`、`python-version.txt` | 固定量化器、项目脚本与 Python 环境。依赖二进制另行保存。 |
| `driver.log`、`convert.log`、`quantize.log`、`pack.log`、`exit-status` | 保留实际命令、过程输出和退出状态。 |
| `output-receipt.json` | 固定三个加工阶段的完整文件身份。 |
| 后续模型验证记录 | 核验结构、张量、词元器、模板、推理与性能。加工脚本不自动生成这些结论。 |

## 7. 怎样关联历史性能

如果新产物与历史最终文件的完整 SHA-256 相同，可以直接确认文件身份相同。
如果哈希不同，不能立即认定模型错误。
GGUF 元数据、张量顺序、转换精度和重复量化都可能造成文件差异。
必须先比较文本主模型的张量名称、形状、类型及数据内容。
必须分别核对词元表、特殊词元和对话模板。
草稿头与视觉组件必须单独标明比较范围。

结构相同仍不能证明数值相同。
单个回答相同也不能证明所有输入等价。
如果最终采用不同的新 GGUF，必须对该文件执行 K1 本地推理和匹配基线／优化版测试。
历史 Unsloth 文件的性能保留为原产物的结果。
本次没有恢复板端测试。

## 8. 本次证据与下一步

本次来源准备证据位于 `spacemit/reports/raw/model-origin-preparation-20261012/`。
其中保留官方与 Unsloth 元数据、固定配置、分片索引、模板、模型卡摘要及来源收据。
其中也保留转换源码核验、工具检查和本次脚本副本。
6 项记录工具检查通过。
这些检查拒绝权重变化、配置变化、分片缺失、模型错误和源码变化。
它们不是完整模型转换测试。

下一步先完成两个官方检查点的实际加工。
然后核对新产物与历史产物的差异。
最后按选定交付产物补齐必要的 K1 推理与匹配性能证据。
本次准备不能写成“已经从官方权重完成转换”。
