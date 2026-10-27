# 委员会交付包要求

用户于 2026-10-15 要求提供名为 `final-release` 的完整成果包。
本文件记录新增交付范围，不改变根目录 `Requirements.md` 的验收依据。
本文件记录组装规则；最终状态以成果包中的清单和核验收据为准。
不能把本目录的元数据入口当作完整成果包。
原 r3 归档必须保持原字节。

## 六项内容与目标路径

| 用户要求 | 成果包内路径 | 当前状态 |
| --- | --- | --- |
| 可运行代码 | `runtime/source/`、`runtime/build/`、`runtime/package/` | 原 r3 已验证；组装时复制完整源码和原生产二进制。 |
| 一键部署脚本 | `deploy.sh`、`deploy.py`、`docs/DEPLOYMENT.md` | 新入口已实现；本地检查与板端迁移检查分别记录。 |
| 官方原始模型转换与量化脚本 | `model-materials/tools/`、`converter-source/` | 已实现；必须同时提供固定转换源码和官方输入元数据。转换验收状态见 SUBMISSION-CHECKLIST.md。 |
| 模型转换与部署说明 | `docs/MODEL-CONVERSION.md`、`docs/DEPLOYMENT.md` | 独立说明随包提供，不能依赖本机实验路径。 |
| 起点与优化性能报告 | `reports/` | 普通默认对照已验证；16k／32k 补测结束后核验并纳入。 |
| 框架改造或模型压缩设计 | `docs/DESIGN.md` | 必须说明最终启用路径、回退条件、数值检查和未采用方案。 |

## 成果包结构

```text
final-release/
  README.md
  SUBMISSION-CHECKLIST.md
  manifest.json
  SHA256SUMS
  deploy.sh
  deploy.py
  runtime/
    source/
    build/
    package/
    Requirements.md
    VALIDATION.md
  converter-source/
  model-materials/
    tools/
    metadata/
    official-source-lock.json
  docs/
    DEPLOYMENT.md
    MODEL-CONVERSION.md
    DESIGN.md
    DEPENDENCIES.md
  reports/
  evidence/
```

`runtime/` 来自 `lab/final-default-20261013/release/k1-final-20261013-r3/`。
只复制其中的 `source/`、`build/`、`package/`、`Requirements.md` 和 `VALIDATION.md`。
`converter-source/` 来自核验过的 `lab/local-reference/source-a990751-clean/`。
不能把已打生产补丁的源码冒充官方复现脚本要求的干净转换源码。
`model-materials/` 使用原 r3 材料，并保留官方元数据与源码收据。
新增材料不得改写原收据或旧归档。

## 组装与冻结要求

1. 完成已有 12 次补测，保留失败与旧记录。
2. 下载并独立核验身份、收据、实际长度、配置、完成状态和内存采样。
3. 生成补测报告和独立补充归档。
4. 保存旧综合报告快照。
5. 更新综合报告、证据附录、TeX 和 PDF。
6. 核对编译与全部 PDF 页面。
7. 复制原 r3 运行材料及固定转换源码，不重建生产二进制。
8. 将本目录的新脚本与 `submission/` 中的独立说明复制到成果包。
9. 纳入普通默认对照、超长补测和综合报告的最终版本。
10. 修复成果包内说明和报告的相对链接，并保留引用的证据或明确归档入口。
11. 保存原 r3 归档及补充归档的文件身份。
12. 生成成果包清单、六项检查表和全部文件的 SHA-256。
13. 在本地 tmux 中核对源码、脚本、清单、链接和归档。
14. 在板端独立新目录中检查新一键入口，持有共用锁，不重复性能请求。
15. 生成独立 `final-release.tar.gz`，核对解压内容与所有收据。
16. 提供最终目录、归档、PDF 和验收限制。
17. 完成交付后暂停 `k1-2`。

最终目录建议使用仓库根目录的 `final-release/`。
大型成果包不提交 Git。
必须提供实际文件，不能只提供指向本机 `lab/` 的索引。
原 r3 二进制保持相同 SHA-256，默认参数保持相同身份。
模型权重与厂商依赖另行提供的限制必须写入顶层说明。
官方全链实际转换、固定多轮质量和长状态验收缺口必须保留。
本次要求提供官方加工脚本，不授权把未执行的加工写成已完成。

## 续接与任务

主续接文件为 `lab/ultralong-20261014/CONTINUATION.md`。
已有 `k1-2` 每 90 min 推进补测及本成果包。
用户另要求 2026-10-16 01:00 新加坡时间执行一次“继续”。
该一次性任务标识为 `automation`，它回到当前对话。
两个任务都必须先读取续接文件，避免重复请求或同时组装。
