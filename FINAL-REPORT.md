# MUSE-Pi-Pro Qwen3.5 推理优化最终报告（2B + 4B）

> 历史说明：本文保留 2026-09-21 的短输入测试记录。
> 当前综合报告截至 2026-10-12，见[报告正文](spacemit/reports/SUBMISSION-REPORT.md)、[PDF](spacemit/reports/SUBMISSION-REPORT.pdf)和[证据附录](spacemit/reports/SUBMISSION-EVIDENCE.md)。
> 本文的历史标题不表示当前所有候选均已完成验收。

> 2026-09-27 更新：本文保留 2026-09-21 的短输出基线结果。"投机无损"只适用于当时逐 token 验证过的 prompt 和 128-token 输出。后续固定代码 prompt 的 4096-token 测试发现：2B/4B 的 MTP 输出与直接解码的 token 不同。长代码生成若要求逐 token 一致，必须使用直接解码。冷启动 TTFT、12k 上下文、RVV 预填充、内存和并发补测见 [2026-09-27 生命周期快照](spacemit/reports/2026-09-27-completed-gates.md)。

日期：2026-09-21 ｜ 平台：MUSE-Pi-Pro（SpacemiT K1-x/X60，rv64，IME 核 0-3，Bianbu 2.3.5，kernel 6.6.63，16 GB）。
代码基线：**官方 `spacemit-com/llama.cpp` fork**（板子路径 `~/Projects/spacemit-llama`，HEAD 5ad05d8）加优化分支 `port-gdn`（4 个 commit）。
**红线：所有对外数字必须出自官方树。运行时必须把 spine-tcm 加进 `LD_LIBRARY_PATH`。** 否则 libspert 静默回退 DDR，tg 下降约 30%：

```bash
export LD_LIBRARY_PATH=$HOME/Projects/llm-bench/.toolchain/spine-tcm:$PWD/spert/spine-runtime.riscv64.0.6.2/lib:$PWD/build/bin
```

> 本文件镜像自板子 `~/Projects/llm-bench/FINAL-REPORT.md`。

---

## 一、最终成绩

### Qwen3.5-2B（Q4_0-embQ4_0，1.06 GB 权重，vocab 248320）

| 指标 | 官方基线 | 最终 | 提升 |
|---|---|---|---|
| llama-bench tg128 | 3.07（Q4_1，文档值） | **5.19 ± 0.00** | +69% |
| llama-bench pp128 | 10.32（Q4_1） | **22.07**（-ub 32） | +114% |
| server 单路 tg（MTP+dv64k，128-token 样本一致） | — | **6.31 t/s** | 对基线 +106% |
| server 多流聚合 conc=8 | — | **13.89 t/s** | — |

并发全景（server，-t 4 -ub 32 -fa on）：

| 配置 | conc=1 | conc=2 | conc=4 | conc=8 |
|---|---|---|---|---|
| 非投机 | 5.19 | 6.43 | 11.62 | 13.49 |
| 默认（checkpoint+gate1） | 5.40 | 6.32 | ~11.5 | **13.85** |
| RS 快照（纯单路最优） | **6.31** | 7.37 | 9.09 | 9.85 |

### Qwen3.5-4B（Q4_0-embQ4_0，2.21 GiB，32 层，embd 2560）

| 指标 | 数值 | 备注 |
|---|---|---|
| llama-bench tg128 | 2.30 | 2.38 GB÷5.4 GB/s=440 ms/tok，**已在带宽地板** |
| llama-bench pp128（-ub 32） | 9.04 | |
| server 单路 tg：非投机 → MTP 全词表 → **MTP+dv64k** | 2.23 → 2.88 → **3.20 t/s** | **+43%，128-token 样本一致** |
| server conc=8 聚合（非投机） | 6.50 t/s | conc1/2/4：2.21/2.97/5.48 |
| 4B-Q8_0 对照 | pp128 1.11 / tg 0.87 | 当时无 IME 核；2026-09-24 起可选 patch 0007 提供 Q8_0 IME1 核（见 spacemit/README.md），不再是死路 |

正确性：当时测试的所有投机配置在**多 prompt × 128 token** 范围内与非投机输出逐 token 一致。更长的固定代码输出见文首更新。

---

## 二、做了什么（按贡献排序）

### 1. TCM 链接修复（最大单点修复，3.8→5.2）

libspert 通过弱符号探测 `libspine_tcm.so`。该库不在 `LD_LIBRARY_PATH` 时，libspert **静默**使用 DDR 做 tile 缓冲，且无任何日志。
实测带宽：真 TCM 写 24.7 / 读 9.26 GB/s，DDR 回退写 2.2 / 读 5.2 GB/s。修复带来 3.8→5.2 t/s。
探针脚本：`~/Projects/spacemit-llama/probe-tcm2.cpp`、`probe-devtcm.cpp`。

### 2. GDN 状态原地写回 + RVV 融合（commit f106a7d，从上游 rescue-1 移植）

18 层 SSM 每层每 token 省一次约 1 MB 的状态拷贝。 kernel 为 fused decode kernel。
上游 tg128 4.79→5.16。官方树 3.5→3.8。

### 3. MTP 投机解码全链路（commit 01949d8、0f2c9fb、6562c22）

- **2B**：unsloth 2B GGUF 自带 MTP（nextn）张量。requant 得到 `Qwen3.5-2B-MTP-Q4_0-embQ4_0.gguf`。
- **截断草稿词表头（dv64k）**：草稿 lm_head 是带宽大头，每个草稿 token 为 2B 286 MB / 4B 365 MB。
  GGUF 手术追加 `nextn.shared_head_head.weight`，取 token_embd 前 65536 行（Q4_0）。graph_mtp 自动探测形状，并把截断 logits 补 -inf 到全词表。该方法**构造性无损**：verify 永远使用全词表。
  脚本：`gguf-add-dv32k.py`（参数化 N_ROWS/IL）。
- **4B MTP 从零手术**（`gguf-add-mtp-4b.py`）：unsloth 4B GGUF 不含 nextn。
  从 hf-mirror 拉 index.json，用 HTTP Range 精准提取 241 MB `mtp.*` bf16（共 15 个张量）。
  8 个权重转 q4_0，7 个 norm 转 f32（**+1，zero-centered RMSNorm**，见 conversion/qwen.py:303；漏掉则草稿全部被拒）。
  `block_count` 由 32 改为 33，`nextn_predict_layers=1`。
- **n_max=3 最优**。2、4、5 都更差：草稿 launch 有固定开销，而 verify 的 M 增大。

### 4. 自适应投机门控 + checkpoint 回滚默认（多流逆袭关键）

发现链：启用 spec 后设 `cparams.n_rs_seq=3`（recurrent 回滚快照），每轮维护 SSM 快照拷贝（conc=8 时 dup_bytes 8.6%），且**屏蔽 GDN 原地快路**。多流即使不打草稿也亏 24%（9.85 对 13.49）。
解法：

- `SPINE_SPEC_MAX_ACTIVE`（默认 1）：活跃槽超过阈值时自动停草稿，在途草稿仍正常验证。
- 默认 `n_rs_seq=0`（checkpoint 回滚，仅 SSM 状态）。`SPINE_SPEC_RS=1` 切回快照模式。

结果：高并发追平或反超非投机（13.85）。单路只付 12%（5.40 对 6.31）。纯单路评测用 RS 模式。
**投机交叉点实测**：低并发（≤2）时带宽受限的 spec 占优；高并发（≥4）时 IME 算力受限的 spec 吃亏。

### 5. pp ubatch 甜点（纯配置，pp128 +69%）

M≥64 时 BLOCK GEMM 调度效率骤降：pp128 在 ub=128 时仅 13.03，ub=32 时为 22.07。
server 和 bench 一律使用 `-ub 32 -b 32`。decode 和 verify 的批量 ≤32，不受影响。

### 6. 已排除的死路（勿再试）

- 主权重低于 Q4_0 的量化：IME1 白名单只有 q4_0、q4_1、q4_K。实测 Q8_0 的 pp 慢 8 倍。更新：2026-09-24 起可选 patch 0007 增加 Q8_0 IME1 核，Q8_0 已不再是死路（见 spacemit/README.md）。
- IME2/q2_k 核：板上 `use_ime2: 0`，不可用。
- TCM tile staging 尺寸调整（A″）：中性。A′ 半相位锁步回退已证伪。
- spert 环境变量（HOT_SPIN、ARBITER、CTX_RVV、RT_PRIO）：全部无效果。
- checkpoint 数据通路优化：实测仅 16 ms/轮。损耗在 spert synchronize 的流水线停顿，属结构性问题。
- 寄存器常驻 GDN 行变体：已拒绝。

---

## 三、推荐用法

```bash
cd ~/Projects/spacemit-llama
export LD_LIBRARY_PATH=$HOME/Projects/llm-bench/.toolchain/spine-tcm:$PWD/spert/spine-runtime.riscv64.0.6.2/lib:$PWD/build/bin

# llama-bench 合规数字
./build/bin/llama-bench -m models/Qwen3.5-2B-Q4_0-embQ4_0.gguf -t 4 -ub 32 -b 32 -fa 1

# server 综合（单双路投机自动开，高并发自动关）
./build/bin/llama-server -m models/Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf \
  -t 4 -c 16384 --parallel 8 -ub 32 -fa on --spec-type draft-mtp --spec-draft-n-max 3

# server 纯单路最优（快照回滚模式）
#   同上 + SPINE_SPEC_RS=1
```

## 四、产物清单

- 代码：官方树分支 `port-gdn`（f106a7d → 01949d8 → 0f2c9fb → 6562c22）
- 2B 模型：`Qwen3.5-2B-MTP-Q4_0-embQ4_0{,-dv32k,-dv64k}.gguf`（llm-bench/models，软链到 spacemit-llama/models）
- 4B 模型：`Qwen3.5-4B-MTP-Q4_0-embQ4_0{,-dv64k}.gguf`（2.45 / 2.54 GB，spacemit-llama/models）
- 脚本：`gguf-add-dv32k.py`、`gguf-add-dv64k.py`、`gguf-add-mtp-4b.py`、`gguf-add-dv64k-4b.py`（~/Projects/spacemit-llama/）
- 诊断环境变量：`SPINE_TCM_DEBUG`、`SPINE_GDN_DBG`、`SPINE_CKPT_PROF`、`SPINE_SPEC_MAX_ACTIVE`、`SPINE_SPEC_RS`

## 四点五、k1-integrated 并发补测（2026-09-24，Codex 分支 a990751）

2B，d2t32k 映射头加 M4 scale 构建，英文 prompt，聚合 t/s（conc 1/2/4/8）：
非投机 4.92 / 6.52 / **12.20** / **14.17** ｜ 默认（gate1+ckpt）5.21 / 6.30 / 11.46 / 13.77 ｜
RS 快照 6.80 / 5.48 / 9.12 / 10.57 ｜ ngram+MTP 5.20 / 6.31 / 11.81 / 13.91。

新发现：

1. **M4 scale 补丁多流 +5%**（conc4/8：11.62→12.20，13.49→14.17）。批量 decode 的 M=4/8 走 M4 GEMM，单流不可见该效果。
2. 交叉点依旧：RS 快照即使只有单槽草稿也拖累所有槽（conc2 5.48 < 6.52）。checkpoint 加门控的默认配置仍然正确。ngram 组合对并发为中性。

## 五、已知天花板

- 单路 decode 和 verify 均已在 5.4 GB/s 带宽地板。2B 非投机为 5.19；verify M=4 用时 265 ms，理想为 250 ms。
- 剩余空间在 spert 运行时内部：每次图 launch 有约 15–20 ms 固定开销。一轮投机 4–6 次 launch，约 89 ms/轮。必须改动 libspert 二进制层面才有进展。

---

## 六、2026-09-23 补充验证（4B）

以下测量在官方 fork 的 `port-gdn` 6562c22 上完成，均加载 spine-tcm。结果只适用于所列工作负载。

### 单路投机：使用 RS 快照回滚

`llama-server` 每组独立启动。参数：4B-MTP-dv64k，`-t 4 -c 8192 --parallel 1 -b 32 -ub 32 -fa on --spec-type draft-mtp --spec-draft-n-max 3`。
同一 prompt（`The theory of relativity states`），`n_predict=128`，`temperature=0`，`seed=42`，`cache_prompt=false`。

| 回滚 / 草稿头 | 128 token decode（t/s） | 备注 |
|---|---:|---|
| 默认 checkpoint / dv64k | 2.704、2.712 | 两次独立启动 |
| `SPINE_SPEC_RS=1` / dv64k | **3.355、3.343** | 相同设置下比默认快约 24% |
| `SPINE_SPEC_RS=1` / dv32k | 3.203 | 比 dv64k 慢约 4%，不采用 |

三种配置输出的 SHA-256 均为 `cabf0208d3ac688bca04b885f73741a603d842c499179b212ca4663de90f3a89`。
dv32k 接受草稿 81/135，dv64k（RS）接受 84/126。更小草稿头省下的带宽不足以弥补接受率下降。
专用单路 4B 服务可以在上述参数前设 `SPINE_SPEC_RS=1`。高并发仍用默认 checkpoint 加 gate 配置。
本文的 3.35 t/s 与第一节历史 3.20 t/s 的服务配置不同，两者的提速百分比不可直接比较。

### 4B prefill 微批量

`llama-bench -p 128 -n 0 -t 4 -b 128 -fa 1`，模型为同一 4B Q4_0-embQ4_0。
初扫 `-ub 16/24/32/48/64`（各 1 次）得 8.99 / 9.08 / 9.13 / 9.25 / 7.28 t/s。
`-r 3` 复测后，`-ub 32` 为 9.149 ± 0.001，`-ub 48` 为 **9.268 ± 0.003 t/s**（约 +1.3%）。
`-b 128 -ub 48` 只用于 4B pp128 这一个专项。综合 server 配置仍需单独测并发。
第一节与官方文档的 Q4_1 比较同时改变了量化和运行配置。该比较应读作端到端配置收益，不是单项代码收益。
