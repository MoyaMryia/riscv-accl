# K1 统一发布候选

版本为 `k1-unified-20261013-rc1`。
本包把宽 RISC-V 向量扩展（RVV）注意力、矩阵指令扩展（IME）路由、C1、C2-r2 与 B1-r2 合入同一源码。
一次构建生成完整服务器和全部候选路径。
默认优化配置为 `optimized`，使用 route 3，关闭三个候选。
实验配置不自动获得正式性能结论。

验收依据为根目录 `Requirements.md`。
本包是发布候选，不表示项目已经完成正式验收。
模型来源、官方全链转换、长上下文和固定多轮质量仍有缺口。
实际验证结果见随包 `VALIDATION.md` 和 `evidence/`。

## 包内布局

| 路径 | 内容 |
| --- | --- |
| `source/` | 完整统一源码，固定厂商提交加一份补丁。 |
| `package/` | 构建、启动、测试、清单与本说明。 |
| `build/bin/` | 本次 K1 构建的服务器、基准工具、库和数值工具。 |
| `build/build-receipt.json` | 二进制、编译器、外部依赖与构建配置的身份。 |
| `reference-release/` | 10 月 7 日固定发布配方，用于另建对照。 |
| `model-materials/` | 模型来源锁定、加工脚本和已有元数据。 |
| `evidence/` | 本次实际日志、状态、逐请求数据和收据。 |
| `SHA256SUMS` | 包内普通文件清单；归档本身另附 SHA-256。 |

权重、GCC、SPERT 和 TCM 运行库必须另行取得。
依赖说明见 `package/DEPENDENCIES.md`。
候选形状、回退条件和负结果见 `package/CANDIDATES.md`。

## 在新目录使用

解压后进入归档根目录。
先查看现有 tmux 会话与 `llama-server` 进程。
不要结束其他任务来获取设备。
创建一个新会话。

```bash
tmux new-session -s k1_unified_use -c /absolute/path/to/k1-unified-20261013-rc1
```

以下命令均在该会话内执行。
新设备必须先建立共用锁的父目录。
该目录不需要包含旧实验构建。

```bash
mkdir -p "$HOME/Projects/riscv-accl-bench-2026-09-27"
```

先核对包内文件。

```bash
sha256sum -c SHA256SUMS
python3 package/package.py verify source
```

启动 2B 优化配置。
必须将权重和依赖路径换成实际位置。

```bash
bash package/with-lock.sh python3 package/run.py \
  --build build \
  --model /absolute/path/to/Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf \
  --spert /absolute/path/to/spine-runtime.riscv64.0.6.2 \
  --tcm /absolute/path/to/spine-tcm \
  --profile optimized --receipt 2B-launch.json
```

结束本次服务器后，启动 4B。

```bash
bash package/with-lock.sh python3 package/run.py \
  --build build \
  --model /absolute/path/to/Qwen3.5-4B-MTP-Q4_0-embQ4_0-dv64k.gguf \
  --spert /absolute/path/to/spine-runtime.riscv64.0.6.2 \
  --tcm /absolute/path/to/spine-tcm \
  --profile optimized --receipt 4B-launch.json
```

启动器固定四线程、6,144 上下文、单槽、批大小与微批大小 32、F16 键和值缓存以及 CPU 后端。
服务器只监听本机 `127.0.0.1:8080`。
推理不依赖云端 API。
在同一 tmux 会话的新窗口发送本地请求。

```bash
curl http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"local","messages":[{"role":"user","content":"计算 2 加 2。"}],"temperature":0,"seed":42,"max_tokens":128,"cache_prompt":false,"chat_template_kwargs":{"enable_thinking":false}}'
```

基线使用 `--profile baseline`。
单项实验使用 `--profile c1`、`--profile c2-r2` 或 `--profile b1-r2`。
`--profile prefill` 表示 C1 与 C2-r2。
`--profile all` 表示三项全开，已有历史解码退化。

自定义组合只能使用 `experimental` 配置。
每个候选均可明确启用或关闭。
下例只启用 C1。

```bash
bash package/with-lock.sh python3 package/run.py --build build \
  --model /absolute/path/to/Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf \
  --profile experimental --enable c1 --disable c2-r2 --disable b1-r2
```

同一候选不能同时出现在 `--enable` 和 `--disable`。
`--describe` 只核验并打印配置，不启动服务器。
`--trace` 只用于路径诊断，不能与关闭日志的计时结果混比。
外部实验环境变量不能隐式开启候选。
启动器替换库搜索路径，并清除预加载和后端覆盖变量。

## 从包内完整源码构建

在 tmux 会话内执行下列命令。
`source/` 已包含统一补丁。
构建目录必须不存在。
外部编译器与运行库仍必须按依赖说明准备。

```bash
bash package/with-lock.sh bash package/build.sh source rebuilt-build \
  > rebuild.log 2>&1
printf '%s\n' "$?" > rebuild-exit-status
```

构建入口先核对全部源码身份。
新的二进制与构建收据保存在 `rebuilt-build/`。
可以在启动命令中使用 `--build rebuilt-build`。

## 从固定厂商源码重新生成

所有重建和测试仍须在 tmux 内执行。
厂商源码固定为 `a990751d55a4c54acf2bb77d44282c2093652359`。
原发布补丁已经包含在 `unified.patch` 中。
不得先应用另一份候选或原发布补丁。

```bash
git clone https://github.com/spacemit-com/llama.cpp vendor-clean
git -C vendor-clean checkout --detach a990751d55a4c54acf2bb77d44282c2093652359
python3 package/package.py prepare vendor-clean rebuilt-source
bash package/with-lock.sh bash package/build.sh rebuilt-source rebuilt-build \
  > rebuild.log 2>&1
printf '%s\n' "$?" > rebuild-exit-status
```

输出源码与构建目录必须不存在。
工具核对全部厂商源码，再应用统一补丁。
构建不读取旧实验目录的动态库。
编译器和外部依赖通过 `K1_CC`、`K1_CXX`、`K1_SPERT_DIR`、`K1_TCM_DIR` 设置。
构建收据保存在新构建目录。
不同编译器、链接路径或工具版本可能改变二进制字节。
重新生成的包必须保存自己的构建身份与验证结果。

## 执行验证

协议见 `package/PROTOCOL.md`。
先按 `reference-release/README.md` 单独建立原发布对照。
不得用另一个候选库充当原发布对照。

```bash
bash package/with-lock.sh python3 package/validate.py \
  --source source --build build \
  --reference /absolute/path/to/original-release-build/bin \
  --models /absolute/path/to/models \
  --spert /absolute/path/to/spine-runtime.riscv64.0.6.2 \
  --tcm /absolute/path/to/spine-tcm \
  --output /absolute/path/to/new-validation \
  > validation-driver.log 2>&1
printf '%s\n' "$?" > validation-exit-status
```

`with-lock.sh` 是唯一的持锁入口。
不要在外层重复获取同一锁。
验证目录必须不存在。
读取 `summary.json` 的阶段结论，不能只查看退出码。
如果收集失败，只恢复文件收集，不重复长测试。

本地工具检查需要干净厂商源码。
它不需要 K1，也不能替代实机检查。

```bash
K1_TEST_VENDOR_SOURCE=/absolute/path/to/vendor-clean \
  python3 package/tests/test_package.py
```
