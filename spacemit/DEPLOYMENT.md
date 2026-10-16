# K1 本地部署入口

要求依据为根目录 [Requirements.md](../Requirements.md)。
最终[单一默认交付](final-release/README.md)提供同一二进制与编译默认值。
普通启动命令和完整归档身份见该入口。
已验证范围与实测提升见[最终对照](reports/2026-10-14-final-default-comparison.md)。

旧的[统一发布候选](release-candidate/README.md)提供同次构建和独立候选开关。
其实际验证、归档身份和限制见[整合记录](reports/2026-10-13-unified-release-candidate.md)。
本页下列步骤保留 10 月 7 日已核验发布包的对照用法。
已验证范围见[发布检查](reports/2026-10-07-release-verification.md)。
后续候选、失败组合及旧补丁的边界见[结果索引](reports/RESULTS.md)。
profile 表示启动配置名称。

## 1. 准备依赖与模型

在 K1 上准备 Git、Python 3、CMake、Ninja、tmux 和 flock。
安装支持 IME 内建函数的 GCC 14、SPERT 与 TCM 兼容库。
这些厂商依赖不随本仓库分发。
当前脚本使用下列默认路径。
其他安装位置必须通过同名环境变量覆盖。

| 环境变量 | 默认位置 |
| --- | --- |
| `K1_CC` | `$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/gcc-14` |
| `K1_CXX` | `$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14` |
| `K1_SPERT_DIR` | `$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2` |
| `K1_TCM_DIR` | `$HOME/Projects/llm-bench/.toolchain/spine-tcm` |

将项目放在 K1 的 `$HOME/Projects/riscv-accl`，或修改下面的项目路径。
板端已有实验目录不等于已有这个项目检出。
准备[发布清单](release/manifest.json)中的两个 GGUF。
现用产物的完整 SHA-256 见清单，启动器会重新核对。
模型来源和加工步骤见[模型材料入口](models/README.md)。
完整官方检查点转换仍待验证，不能把准备脚本写成已完成的转换。

TCM 表示紧耦合存储器。
普通用户的 `/dev/tcm` 权限与 `/dev/tcm_sync_mem` 缺失是两个独立问题。
[sudo 只读检查](reports/2026-10-13-k1-tcm-access.md)确认四块真实 TCM 可访问。
该结果不能证明推理缓冲区已使用真实 TCM，也没有提供性能收益。
复现必须保存实际 UID、设备权限与运行库身份。

## 2. 在受锁保护的会话中构建

先查看已有会话与任务。
如果同名会话已存在，先查看它的日志。
不要结束其他任务来获取板卡。

```bash
tmux list-sessions
pgrep -a -x llama-server
```

在 K1 上创建部署会话。

```bash
tmux new-session -s k1_release_deploy -c "$HOME/Projects/riscv-accl"
```

在该会话内执行下列命令。
共用锁必须使用此固定位置。
新运行目录保存日志，不能复用已有目录。

```bash
deploy_repo="$PWD"
deploy_run="$deploy_repo/lab/release-deploy-$(date +%Y%m%d-%H%M%S)"
deploy_board_root="$HOME/Projects/riscv-accl-bench-2026-09-27"
mkdir -p "$deploy_board_root"
mkdir "$deploy_run" || exit 1
exec 9> "$deploy_board_root/document-quality-suite.lock"
flock -n 9 || exit 1
pgrep -x llama-server >/dev/null && exit 1
printf '%s\n' k1_release_deploy > "$deploy_run/session-name"
printf '%s\n' "$PWD" > "$deploy_run/working-directory"
uname -a > "$deploy_run/hardware.txt"
cat /proc/meminfo >> "$deploy_run/hardware.txt"
id >> "$deploy_run/hardware.txt"
set -o pipefail
```

使用独立的干净源码目录。
下面的构建目录只服务于此发布包。

```bash
git clone https://github.com/spacemit-com/llama.cpp "$deploy_run/source"
git -C "$deploy_run/source" checkout --detach a990751d55a4c54acf2bb77d44282c2093652359
python3 spacemit/release/apply-release.py "$deploy_run/source" \
  2>&1 | tee "$deploy_run/apply.log"
```

只有补丁命令成功后，才执行构建。

```bash
bash spacemit/release/build.sh "$deploy_run/source" "$deploy_run/build" \
  2>&1 | tee "$deploy_run/build.log"
deploy_build_status=$?
printf '%s\n' "$deploy_build_status" > "$deploy_run/build-exit-status"
```

`build-exit-status` 必须为 `0`。
补丁工具核验固定源码和补丁身份，并拒绝重复应用。
构建脚本限定四个编译任务与四小时编译时间。
必须保存 CMake 配置、编译器版本及运行库哈希。
这些材料位于构建目录和对应运行日志中，完整自动收集入口见[发布测试](bench/TESTS.md#发布包实机检查)。

## 3. 分别启动基线版与优化版

在同一受锁保护的 tmux 会话中设置路径。
`deploy_model` 必须指向清单中的 2B 或 4B 文件。

```bash
deploy_model="$HOME/Projects/spacemit-llama/models/Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf"
deploy_runtime="${K1_TCM_DIR:-$HOME/Projects/llm-bench/.toolchain/spine-tcm}:${K1_SPERT_DIR:-$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2}/lib:$deploy_run/build/bin"
deploy_profile=baseline
python3 spacemit/release/run-server.py \
  --server "$deploy_run/build/bin/llama-server" \
  --model "$deploy_model" --runtime "$deploy_runtime" \
  --profile "$deploy_profile" --port 8080 \
  2>&1 | tee "$deploy_run/server-$deploy_profile.log"
deploy_server_status=$?
printf '%s\n' "$deploy_server_status" > "$deploy_run/server-$deploy_profile-exit-status"
```

基线版使用宽向量注意力与 route 0。
停止前一个服务器后，将 `deploy_profile` 改为 `optimized` 并重复服务器命令。
优化版使用同一注意力与 route 3。
测试 4B 时，将模型路径改为清单中的 4B 文件。
两个模型与两个 profile 必须分别执行，不能同时占用此单槽服务。

启动器清除继承的 `SPINE_` 实验开关。
两个 profile 均使用四线程、F16 键和值缓存、批量及微批量 32、直接解码和零 GPU 卸载。
上下文分配为 6,144 词元。
输入与最大输出总量必须在此范围内。
实际 16k 历史结果使用另一套上下文分配，不能由此命令直接复现。

## 4. 发送本地请求

在 K1 的另一个终端发送请求。
此请求只检查本地接口，不构成质量或速度验收。

```bash
curl --fail --silent --show-error http://127.0.0.1:8080/health
curl --fail --silent --show-error \
  http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"local","messages":[{"role":"user","content":"计算 2 + 3，并给出结果。"}],"seed":42,"temperature":0,"max_tokens":128,"cache_prompt":false,"chat_template_kwargs":{"enable_thinking":false}}'
```

必须检查响应中的完成状态。
仅成功启动服务器不能记为本地推理已验证。
输出到达长度上限不等于自然完成答案。
固定完整回答检查使用[发布测试入口](bench/TESTS.md#发布包实机检查)。
完整文档缓存复用使用[文档客户端](serve/README.md)。

服务器停止后，在原 tmux 会话执行 `exit` 以释放共用锁。
不要在持锁会话内再调用会自行获取同一锁的测试控制器。
从其他终端可以用 `tmux attach -t k1_release_deploy` 查看会话。

## 5. 复现结果与完成验收

[结果索引](reports/RESULTS.md)连接基线、优化版、请求记录与负结果。
[测试入口](bench/TESTS.md)区分本地复算、完整实机检查和历史测试脚本。
现有发布检查已经完成，不需要为文件整理重复长时间测试。
[独立缺口报告](reports/2026-10-13-requirements-gap.md)列出仍缺少的来源、转换与验收材料。
