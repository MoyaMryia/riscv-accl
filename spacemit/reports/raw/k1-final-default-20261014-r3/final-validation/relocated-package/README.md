# K1 固定默认构建

本包提供一个生产构建。
两个模型共用同一份二进制和同一组默认参数。
源码已固化选中配置。
普通启动不需要性能参数或优化开关。
具体参数和选择证据见 `package/default-policy.json`。
已验证范围和测量限制见 `VALIDATION.md`。
项目验收要求见 `Requirements.md`。

## 文件

| 路径 | 用途 |
| --- | --- |
| `source/` | 完整交付源码 |
| `build/bin/` | 服务器、基准工具和数值检查工具 |
| `build/build-receipt.json` | 源码、编译器、运行库和二进制身份 |
| `package/start.py` | 固定默认启动入口 |
| `package/build.sh` | 从交付源码重新构建 |
| `package/unified.patch` | 相对固定厂商提交的完整补丁 |
| `package/default-policy.json` | 编译默认参数和选型记录 |
| `evidence/` | 测量记录和核验收据 |
| `SHA256SUMS` | 归档中文件的哈希 |

## 依赖

目标平台为 SpacemiT K1，操作系统必须提供 Linux RISC-V 用户空间。
运行依赖包含 SPERT 0.6.2、TCM 用户态库和系统动态库。
依赖路径与独立获取限制见 `package/DEPENDENCIES.md`。
必须使用构建收据中记录的运行库文件。
模型文件必须匹配 `package/manifest.json` 中的 SHA-256。
本包不包含模型权重。
模型来源和转换流程的验收状态见 `VALIDATION.md`。

## 启动

在 tmux 中执行命令。
将当前目录切换到解压后的版本根目录。
将模型路径替换为实际文件路径。

```sh
bash package/with-lock.sh python3 package/start.py --model /path/to/model.gguf
```

该命令会核对模型、二进制和运行库身份。
该入口会清除继承的实验环境变量。
服务器使用编译默认参数。
模型切换只需更换模型文件路径。

如果依赖不在默认位置，提供实际依赖目录。

```sh
bash package/with-lock.sh python3 package/start.py \
  --model /path/to/model.gguf \
  --spert /path/to/spine-runtime.riscv64.0.6.2 \
  --tcm /path/to/spine-tcm
```

可以使用 `--port` 设置服务端口。
可以使用 `--describe` 输出启动参数与编译配置，而不启动服务器。
入口不接收性能配置选项。

## 重新构建

必须使用构建收据指定的工具链和运行库。
在 tmux 中执行命令。
构建输出目录必须不存在。

```sh
bash package/with-lock.sh bash package/build.sh source rebuilt
```

重新构建完成后，可以指定新构建目录。

```sh
bash package/with-lock.sh python3 package/start.py \
  --build rebuilt --model /path/to/model.gguf
```

## 证据范围

默认配置来自两个模型、预填充与解码的均衡目标。
“选中配置”仅表示冻结搜索范围内的选择结果。
该结果不代表所有模型、硬件或负载上的全局最优。
起点对照包含构建和模型加载兼容处理。
主计算图与计算内核的原版身份记录随证据保留。
性能请求使用固定输出历史。
自然回答使用单独的无偏置请求。
两类请求的结果必须分别解释。
