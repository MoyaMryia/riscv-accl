# 官方模型转换与量化

## 状态与输入

已实现：固定官方输入的核验、BF16 转换、Q4_0 量化和草稿头打包脚本。
待验证：两个完整官方检查点的实际全链转换与 K1 推理。
现用实测 GGUF 来自历史第三方 GGUF 加工，不能标记为本次官方全链转换产物。
原始来源说明和输入身份保存在 `model-materials/REPRODUCIBILITY.md` 与 `official-source-lock.json`。
原始说明中的仓库链接保留其历史含义。
本页提供成果包内可直接定位的命令。

| 规格 | 官方后训练仓库 | 固定修订 |
| --- | --- | --- |
| 2B | `Qwen/Qwen3.5-2B` | `15852e8c16360a2fea060d615a32b45270f8a8fc` |
| 4B | `Qwen/Qwen3.5-4B` | `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` |

根要求名称为 `Qwen3.5-2B-Instruct` 和 `Qwen3.5-4B-Instruct`。
上述仓库的官方后训练属性已有元数据记录，验收名称对应说明仍有缺口。
不能以同名 `-Base` 仓库替代。
官方权重共约 13.87 GB，不含中间产物。
必须另为 BF16 GGUF、Q4_0 GGUF 和打包 GGUF 预留空间。

## 下载与转换环境

在转换主机的 tmux 内执行长任务。
如果转换主机是 K1，必须先取得部署说明中的固定共用锁。
使用独立 Python 环境安装 Hugging Face 客户端及转换器依赖。
保存安装日志、版本清单和依赖安装包的哈希。

```sh
hf download Qwen/Qwen3.5-2B \
  --revision 15852e8c16360a2fea060d615a32b45270f8a8fc \
  --local-dir /absolute/path/to/official-2B
hf download Qwen/Qwen3.5-4B \
  --revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a \
  --local-dir /absolute/path/to/official-4B
```

`converter-source/` 是固定厂商提交的干净源码。
脚本通过 `model-materials/metadata/converter-source-receipt.json` 核对该源码。
转换 Python 环境必须安装 `converter-source/requirements/requirements-convert_hf_to_gguf.txt`。
转换用 `llama-quantize` 必须在转换主机上从同一固定源码构建。
不能在 x86 主机直接执行随包的 K1 RISC-V 二进制。
必须记录量化器构建参数、编译器、动态依赖与完整文件哈希。

## 执行两个模型的加工

从成果包根目录执行下列命令。
替换 Python、官方输入、量化器和新输出目录的绝对路径。
输出目录必须不存在。

```sh
MODEL_PYTHON=/absolute/path/to/venv/bin/python \
bash model-materials/tools/reproduce-official.sh \
  2B /absolute/path/to/official-2B "$PWD/converter-source" \
  /absolute/path/to/llama-quantize "$PWD/model-materials/metadata" \
  /absolute/path/to/new-2B-output

MODEL_PYTHON=/absolute/path/to/venv/bin/python \
bash model-materials/tools/reproduce-official.sh \
  4B /absolute/path/to/official-4B "$PWD/converter-source" \
  /absolute/path/to/llama-quantize "$PWD/model-materials/metadata" \
  /absolute/path/to/new-4B-output
```

脚本先核对官方文件、分片索引、模型配置、词元器及转换源码身份。
随后生成 `official-BF16.gguf`、`official-Q4_0-embQ4_0.gguf` 和 `official-Q4_0-embQ4_0-dv64k.gguf`。
官方 BF16 路径只量化一次，不启用 `--allow-requantize`。
词嵌入与输出权重明确使用 Q4_0。
默认转换保留 MTP 张量，然后追加 65536 行草稿头。
官方默认转换已含 MTP，不得再次执行历史 4B MTP 追加流程。

脚本处理文本模型，不导出视觉投影器。
不能将该流程记为图像推理部署。
最终生产构建关闭 MTP 草稿解码，仍使用完整主输出词表。

## 产物验收与部署

保存输入前后收据、源码前后收据、工具收据、环境清单、全部日志、输出收据和退出状态。
成功阶段为 `conversion-complete-validation-pending`。
该状态只表示加工完成。
必须继续检查张量、词元器、模板、数值、自然回答及 K1 匹配性能。
文件哈希不同不自动表示模型错误，也不能自动表示等价。
新的产物必须建立独立身份与验收记录。

普通交付启动器只接受原实测清单中的两个完整文件哈希。
它会拒绝未经验证的官方新产物。
不能改写旧清单以绕过检查并沿用旧性能报告。
新产物通过验收后，才能作为独立发布材料部署。
