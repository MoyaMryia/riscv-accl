# 本机实验目录

本目录保存本机实验工件与保留归档。
大部分内容由 Git 排除，见仓库根目录 `.gitignore`。
随 Git 分发的只有本页。
[文档地图](../docs/README.md)给出仓库的文档入口。

## 布局

| 路径 | 内容 |
| --- | --- |
| `<实验名>-YYYYMMDD` | 一次板端或主机实验的完整目录 |
| `<实验名>-YYYYMMDD.tar.gz` | 同名实验的保留归档包 |
| `official-models/` | 本机下载的官方模型与转换输入 |
| `models/` | 本机模型副本 |
| `toolchain/` | 板端编译器、SPERT 与 TCM 运行库 |
| `llama.cpp/` | 本机 llama.cpp 检出 |
| `bin/`、`roots/`、`logs/` | 运行脚本、根文件系统与运行日志 |
| `src/`、`plugin/` | QEMU 指令统计与内存探针，属于另一项目的测量工具 |
| `baseline-record.md` | TinyLlama QEMU 基线记录，属于另一项目 |

实验目录名与 `spacemit/reports/raw/` 中的批次名对应。
需要复现某个批次时，先按批次名找到目录，再读取该目录中的协议或脚本。

## 归档

`*.tar.gz` 是实验目录的保留归档。
归档包文件名不固定，按前缀匹配实验名。
需要长期保留的材料按[归档清单](../archive/README.md)的规则处理。
