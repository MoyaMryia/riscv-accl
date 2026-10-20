# 小型 BERT 意图分类器

本目录提供全参数微调脚本、原生编码器导出适配器和分类客户端。
模型使用 `uer/chinese_roberta_L-4_H-256`，包含 4 层、256 维隐藏状态和四类线性分类头。
标签顺序固定为 `code`、`qa`、`text`、`document`。
分类器识别交付意图；选路策略另行使用实测路径收益。

本次模型、准确率和 K1 延时见[微调实测报告](../../reports/2026-10-18-2b-bert-classifier.md)。
完整请求时间和逐题质量见[BERT 路由回归结果](../../reports/2026-10-18-2b-bert-router-results.md)。
生产入口与原 `model.json.gz` 保持不变。

## 已训练模型

本机模型包为 `lab/router-bert-20261018/bert-router-v1.tar.gz`。
解包目录包含 `encoder-f32.gguf`、`head.json`、`manifest.json`、`runtime/` 和使用说明。
GGUF 保存编码器权重，JSON 保存分类投影和输入配置。
两个文件共同组成模型；manifest 记录两者身份。

板端实际使用原 r3 的独立编码器进程。
配置为 4 线程、256 上下文、batch／ubatch 256、CLS 池化和关闭 Flash Attention。
客户端请求未归一化的 CLS 向量，再执行分类投影。
原生启动参数见[板端启动记录](../../reports/raw/router-bert-20261018-r1/board/result/launch.json)。

板端实验必须由一个外层进程持有共用锁。
编码器和解码后端共用该外层锁，不分别重复加锁。
锁路径与原生运行库设置见[部署指南](../../DEPLOYMENT.md)。

编码器启动后，在模型包目录调用客户端：

```python
import sys
sys.path.insert(0, "runtime")
from bert_runtime import Client

client = Client("head.json", "http://127.0.0.1:18120", 30)
result = client.predict("请实现一个 Python 函数，只返回源码，不使用第三方库。")
print(result["category"], result["score"])
```

`Client` 只接受带明确端口的 `127.0.0.1` HTTP 地址。
客户端包含分词、原生编码和线性分类三个步骤。
网络错误、编码器向量错误和投影溢出均使请求失败，不自动切换到旧分类器。
代理的 `--model` 参数继续读取旧线性模型。
使用 `--bert-head head.json --bert-url http://127.0.0.1:18120` 时，实验代理调用 BERT 编码器。
该模式返回 `X-Classifier: bert`，编码器网络失败返回 502，不切回旧分类器。
手工 `X-Decode-Mode` 继续旁路分类器。

## 从新目录完整复现

训练环境使用 Linux x86_64、CPython 3.13.14 和 CPU PyTorch。
准备 `uv`、`curl`、GNU tar、C++ 编译器和 CMake。
编译器和 CMake 用于安装冻结的 `sentencepiece==0.2.0`。
已验证的 `uv` 版本为 0.12.1。
入口只查找已安装的 Python，不自动下载解释器。

在仓库根目录执行：

```bash
bash spacemit/serve/decode-router/reproduce-bert.sh lab/bert-reproduce-new
```

输出目录必须是新目录，入口拒绝覆盖现有记录。
脚本创建独立虚拟环境，安装[冻结依赖](../../reports/raw/router-bert-20261018-r1/training/dependencies.txt)，并重新下载固定底座。
脚本使用仓库内的冻结训练源码、数据和转换器，不读取旧 `lab/` 模型缓存。
模型下载地址为 `https://hf-mirror.com/uer/chinese_roberta_L-4_H-256/resolve/68d674689f3c9d425e5436149c8acece077187f1/`。
底座与数据集 SHA-256 由 `data-v2/bert-source-receipt.json` 提供，训练入口在加载权重前核对。

完整入口依次执行下载、依赖检查、微调、评估、GGUF 导出和存档一致性检查。
原生编码器权重、分类头和 GGUF 必须与存档字节一致。
配置、依赖版本、参数数量、拆分数量、最佳轮次和三个混淆矩阵也必须一致。
任何门禁失败都使脚本返回非零，并保留日志。

| 输出 | 内容 |
| --- | --- |
| `run.log`、`exit-status` | 完整过程和退出状态 |
| `installed.txt` | 实际依赖版本 |
| `result/encoder/model.safetensors` | 微调后的编码器 |
| `result/head.json` | 分类头、标签顺序和输入配置 |
| `result/history.json`、`result/training.json` | 每轮开发指标、选择结果和最终评估 |
| `result/test-predictions.json` | 测试标签、预测、logits、CLS 向量和选中 token |
| `result/encoder-f32.gguf` | 原生 F32 编码器 |
| `reproduction.json` | 通过门禁后的身份和指标记录 |

本机已在新目录完成整套复现，退出码为 0。
三个模型产物与原记录逐字节一致，仍选中第 8 轮，测试命中仍为 83／96。
[复现记录](../../reports/raw/router-bert-20261018-r1/reproduction/reproduction.json)保存实际校验值。
另提供 `lab/bert-reproduction-source-v1.tar.gz`，包含同一入口、冻结源码、数据、依赖和转换器。
该源码包解压到独立目录后也完整重跑，退出码为 0，三个产物仍与存档一致。
[源码包校验记录](../../reports/raw/router-bert-20261018-r1/reproduction-source-package/source-package.json)给出包的字节数和 SHA-256。

## 固定数据与标签

数据使用冻结的合成请求，复现时直接读取数据文件，不重新生成请求。
`data-v2/tasks-bert-v1.jsonl` 包含 238 条训练、48 条开发和 96 条测试请求。
训练部分由旧训练集的 78 条与新编的 160 条组成。
每条记录包含 `id`、`text`、`label`、`split`、`group`。
`group` 表示任务族；入口拒绝同组跨拆分和归一化文本重复。
独立审查还检查异名近重复和资料完整性。

| 标签 | 交付意图 | 训练／开发／测试 |
| --- | --- | ---: |
| `code` | 交付源码、补丁、SQL、配置或 shell 命令 | 58／12／24 |
| `qa` | 解释或计算，代码解释题不要求交付实现 | 60／12／24 |
| `text` | 撰写、改写或翻译成文，即使用户附有资料 | 60／12／24 |
| `document` | 依据资料提取、比较、归纳或核对事实 | 60／12／24 |

请求的外层意图决定标签，引用材料中的编程指令不直接改变标签。
旧训练集中的 `train-code-01`、`train-code-20` 因持出任务族重合而排除。
测试文件在训练前固定，开发集与测试集不参与梯度更新。
`data-v2/regression.json` 的三个旧代码请求只用于回归检查，不进入训练。

## 输入处理与模型结构

分词使用底座的 `BertTokenizerFast`，`do_lower_case=false`，保留大小写。
先用 `add_special_tokens=False` 生成 WordPiece 序列，再选取最多 254 个内容 token。
短序列保留全部内容；长序列取开头 127 个、中间 63 个和结尾 64 个，保持原顺序。
之后加入 CLS 和 SEP，模型输入最多为 256 token。
每个 batch 动态补齐到该 batch 的最长序列，attention mask 标记有效位置，token type 均为 0。

编码器通过 `BertModel.from_pretrained(..., add_pooling_layer=False)` 加载。
分类头读取最后一层的 CLS 向量，不使用额外池化投影。
训练结构为 CLS 向量、概率 0.1 的 dropout、`Linear(256, 4)`。
编码器沿用底座的 embedding 和 attention dropout，概率均为 0.1。
推理关闭 dropout，并对四个 logits 执行 softmax。
标签索引顺序为 `code`、`qa`、`text`、`document`。

## 微调方法与选择规则

本次使用 FP32 全参数监督微调，优化器同时更新编码器和分类头。
损失为四类交叉熵，按 batch 均值计算，不添加类别权重。
每个 batch 清空梯度、前向计算、反向传播并执行一次优化器更新。
每轮先打乱训练样本，不进行重复采样。

| 参数 | 实际设置 |
| --- | --- |
| 优化器 | AdamW，betas 为 0.9、0.999，epsilon 为 1e-8 |
| 编码器学习率 | 5e-5，固定 |
| 分类头学习率 | 5e-4，固定 |
| weight decay | 0.01，作用于两组全部参数 |
| 轮数、batch | 12、16；末个 batch 为 14 |
| 优化器更新 | 每轮 15 次，共 180 次 |
| 随机性 | Python 与 PyTorch seed 均为 42，启用确定性算法 |
| CPU 线程 | 8 个计算线程，1 个 inter-op 线程 |
| 梯度与学习率策略 | 不累积梯度、不裁剪梯度、不预热、不使用学习率调度器 |

每轮训练后在 48 条开发请求上计算四类宏 F1。
宏 F1 优先，准确率次优；相同指标保留更早轮次。
全部 12 轮结束后恢复选中权重，再评估固定测试集和旧回归集。
新旧冻结模型使用同一测试集作最终比较，测试结果不参与权重选择。

实际选中第 8 轮，对应 120 次优化器更新。
编码器包含 8699904 个参数，分类头包含 1028 个参数，共 8700932 个参数。
可审查的原始实现见[冻结训练源码](../../reports/raw/router-bert-20261018-r1/training/tools/bert_train.py)。
训练结果同时保存编码器、分类投影、逐轮指标和逐题预测。

## 原生导出与数值检查

导出适配器接受当前大小写敏感的 BertNormalizer 和 WordPiece 配置。
转换器保留原词表索引与 normalizer 元数据。
适配器使用 WordPiece 路径，不套用已知 BPE 分词器。
其他分词配置触发明确错误。

[转换器快照](../../reports/raw/router-bert-20261018-r1/source/converter-source.tgz)保存实际使用的转换工具。
完整复现入口会校验并解包该快照，再执行冻结的导出适配器。
输出为 F32 GGUF，分类投影继续保存在 `head.json`，两者共同执行推理。

K1 验证入口为 `spacemit/bench/mtp-r3/bert_bench.py`。
它逐项对照 Hugging Face 选中 token、PyTorch logits 和最终类别。
参考向量和原生向量的长度分别在入口检查，内部比较直接读取已检查的输入。

## 适用范围

实现：4 层中文 BERT、256 token 输入预算、F32 原生编码器、独立 HTTP 客户端。
数据、准确率、资源采样和后续路由任务统一见[报告适用范围](../../reports/2026-10-18-2b-bert-classifier.md#适用范围)。
