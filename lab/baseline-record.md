# TinyLlama QEMU RISC-V 基线记录（2026-09-04）

## B 计划（收尾无聊时做，非承诺项）

- **3A5000 主板（¥168 二手）**：LoongArch 宿主。两个可选实验：
  ① 三宿主矩阵（x86/LoongArch/MIPS 宿主跑同一 RISC-V guest：三个墙钟、
  同一 instr/token → 证明尺度宿主无关）；
  ② 同宿主跑 x86_64/aarch64/riscv64 三 guest 比指令数（ISA 代码效率）。
  前提：Loongnix 的 QEMU 若为 7/8.x，plugin 按 v7 前 API 重编。
  红线：三 guest 墙钟不得进任何 CPU 对比表（那量的是 QEMU 翻译成本）。
- 排位在全部主线路径之后，闲鱼随时可补货，不构成依赖。

## 硬件定案（真机赛道）

- **唯一真机平台：Muse Pi 16G**（SpacemiT M1，8×X60 @1.8GHz，LPDDR4X-2400
  → 9.6GB/s，VLEN 256，IME gen1，2×M.2 2280，USB PD3.0 供电），¥810 二手
- 构建矩阵：标量 rv64gc / RVV rv64gcv_zvfh（自编）+ SpacemiT 官方 llama.cpp
  fork（IME kernel）三组
- 已否决：Lichee Pi 4A 16G（C910，xtheadvector 0.7.1 私有向量，¥400）——
  非标准 ISA、软件栈残缺、4 核纸面弱，跨 ISA 对比价值不抵叙事风险
- x86 阶梯四台全在手：T7100(2007) / i7-3632QM(2012) / Orin Nano Super
  CPU-only(2023) / 265K(2025, 兼任 Top Reference 与 QEMU 宿主)

## 结果

| Run | 二进制 | QEMU CPU | pp128 | tg64 | 备注 |
|---|---|---|---|---|---|
| A 基线 | 标量 rv64gc | `rv64` | 0.28 | 0.25 | 墙钟 1200s |
| B | 标量 rv64gc | `xiangshan-kunminghu` | 0.28 | 0.26 | **与 A 持平**：TCG 下 CPU 模型不影响标量性能，昆明湖选型零成本 |
| C | RVV `rv64gcv_zvfh` | `xiangshan-kunminghu` | 0.22 | **0.20** | 墙钟 1485s；**RVV 反而慢 ~25%** |
| D | 标量 rv64gc | `xiangshan-kunminghu`, **-smp 8 / -t 8** | **1.41** | **1.17** | 墙钟 241s；**指标线 1.0 过线**，8 线程 4.7x 扩展 |
| 参照 | x86 原生 AVX | 宿主 | 65.21 | 19.63 | 1 线程 |

## 指令数测量（2026-09-04，plugin: insnsum.so，7 次引导差分法）

原始计数（insn_total，含 boot）：

| boot | 内容 | insn_total |
|---|---|---|
| s-null | 纯引导 | 18.049G |
| s-load | 引导+加载+pp1 | 35.354G |
| s-tg | 引导+加载+tg64 | 1061.207G |
| s-pp | 引导+加载+pp128 | 1886.762G |
| r-load/r-tg/r-pp | RVV 版同三项 | 19.549G / 63.628G / 99.117G |

解联立（自洽解，pp1=ipt_pp）后：

| 指标 | 标量 | RVV | RVV 节省 |
|---|---|---|---|
| instr/token (tg) | **16.26G** | **0.699G** | **23.3×** |
| instr/token (pp) | 14.58G | 0.627G | 23.3× |
| 加载 L | 2.73G | 0.87G | 3.1× |

**TCG 翻案实锤**：墙钟 RVV 慢 25%（0.20 vs 0.25 t/s），但指令数少 95.7%——
TCG 对向量指令的单条翻译成本 ≈ 标量的 **29 倍**（4.06 vs 0.14 G-instr/s）。
**TCG 墙钟与算法效率反相关，指令数才是唯一诚实的 QEMU 尺度。**

## SpacemiT M1 投影（TinyLlama 1.1B Q4_K_M，8×X60 @1.8GHz，LPDDR4X-2400 9.6GB/s）

参考机已锁：**Muse Pi 16G**（M1，LPDDR4X-2400 → 理论 9.6GB/s，2×M.2 NVMe，
官方规格表确认为 M1 而非 K1；¥810 二手 vs 8G Pro ¥590，同芯片选大容量）

- 假设：IPC ∈ [1.0, 2.0]（X60 无官方值，最大误差源）；带宽效率 35–50%（K3 锚点 35% 下界 / K1 ORT 锚点 ~40%）
- tg 8 线程标量：min(0.89–1.77 计算, 5.2–7.5 带宽) = **0.9–1.8 t/s**（计算受限）
- tg 8 线程 RVV：min(20.6–41.2 计算, 5.2–7.5 带宽) = **5.2–7.5 t/s**（带宽受限）
- **RVV 真机加速比：~4–6×**（TCG 墙钟却显示 −25%——方法论差异的活标本）
- tg 单线程标量：0.11–0.22 t/s
- 指标线 1 t/s：标量 8 线程踩线过，RVV 稳过
- 上板后第一件事：用实测 tg 反推 X60 有效 IPC，闭环校准

## 负结果分析（Run C：RVV 拖慢）



- gcc 自动向量化（autovec）生成的 RVV 代码在 TCG 下每条向量指令翻译开销更高，
  净效果为负——**TCG 惩罚"指令翻译成本"，不奖励"每条指令干更多活"**
- 推论 1：QEMU 里堆 autovec 达不到 1 t/s，此路不通
- 推论 2：真实硬件上的 RVV 收益（尤其手写 intrinsics kernel）与 TCG 表现**不可互相外推**，
  比赛数据必须双平台分开陈述
- 后续优化方向必须转向"减少执行的指令总数"或"guest 内手写 kernel + 指令数论证"

- 模型：TinyLlama-1.1B-Chat-v1.0, Q4_K_M, 667,814,880 B
  （modelscope `lefromage/TinyLlama-1.1B-Chat-v1.0-Q4_K_M-GGUF`；HF 不可达）
- 源码：llama.cpp master `f9f09f0`（2026-09-03）

## QEMU 命令行

```
qemu-system-riscv64 -M virt -m 4096M -smp 1 -cpu rv64 \
  -bios /usr/local/share/qemu/opensbi-riscv64-generic-fw_dynamic.bin \
  -kernel <repo>/env/qemu/vmlinux-rv64 \
  -initrd ~/llm-artifacts/initramfs-baseline.cpio.gz \
  -append "console=ttyS0 rdinit=/init" -nographic -no-reboot
```

## llama.cpp 编译参数（交叉编译，宿主 Ubuntu 22.04 gcc-cross-riscv64 11.4）

```
cmake -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_SYSTEM_NAME=Linux -DCMAKE_SYSTEM_PROCESSOR=riscv64 \
  -DCMAKE_C_COMPILER=riscv64-linux-gnu-gcc -DCMAKE_CXX_COMPILER=riscv64-linux-gnu-g++ \
  -DCMAKE_FIND_ROOT_PATH=/usr/riscv64-linux-gnu \
  -DCMAKE_FIND_ROOT_PATH_MODE_PROGRAM=NEVER -DCMAKE_FIND_ROOT_PATH_MODE_LIBRARY=ONLY \
  -DCMAKE_FIND_ROOT_PATH_MODE_INCLUDE=ONLY \
  -DGGML_NATIVE=OFF -DGGML_OPENMP=OFF -DGGML_BACKEND_DL=OFF \
  -DGGML_RVV=OFF -DGGML_RV_ZFH=OFF -DGGML_RV_ZVFH=OFF -DGGML_RV_ZVFBFWMA=OFF \
  -DGGML_RV_ZICBOP=OFF -DGGML_RV_ZIHINTPAUSE=OFF -DGGML_RV_ZBA=OFF \
  -DBUILD_SHARED_LIBS=OFF -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_SERVER=OFF \
  -DCMAKE_C_FLAGS="-march=rv64gc -mabi=lp64d" \
  -DCMAKE_CXX_FLAGS="-march=rv64gc -mabi=lp64d" \
  -DCMAKE_EXE_LINKER_FLAGS="-static"
# 产物: bin/llama-bench（全静态, glibc-cross + 静态链接, musl guest 可直接跑;
#        objdump 已验证 0 条向量指令）
# 注意: ggml riscv64 分支默认追加 rv64gcv_zfh... march, 必须逐项显式 GGML_RVV/ZFH...=OFF
```

## 测试命令（guest 内 /init 调用）

```
/opt/llama-bench -m /opt/model.gguf -p 128 -n 64 -t 1 -r 1
```

## 工件位置（均不在 repo 内）

- 二进制: `~/llm-artifacts/llama.cpp-build/build-rv64/bin/`（llama-bench / llama-completion）
- 模型: `~/llm-artifacts/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf`
- initramfs: `~/llm-artifacts/initramfs-baseline.cpio.gz`（staging: `~/llm-artifacts/baseline-root/`，repo 的 initrd-root 未动）
- 完整日志: `~/llm-artifacts/baseline-run.log`

## 踩坑备忘

1. hf-mirror.com 从本机完全不可达（TCP 超时）；modelscope 可用
2. 下载 GGUF 严禁 `curl -C -` 续传——不同源半截文件拼接后大小一致但内容损坏
   （表现为 tensor data not within file bounds）
3. llama.cpp 2026-09 主线已无 `llama-cli`（改名 `llama-completion`）；基准用 `llama-bench`
4. 工具进程清理严禁 `pkill -f <模式>`——会匹配自身包装进程导致 shell 卡死；按 PID 杀
5. QEMU comm 截断 15 字符，`pgrep -x` 会假阴性，须用 `pgrep -f`
