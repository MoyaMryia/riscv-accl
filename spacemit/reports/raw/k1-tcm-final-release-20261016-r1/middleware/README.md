# TCM 用户态薄封装

本目录从 `final-release` 的固定 TCM ABI 开始实现。
TCM 表示紧耦合存储器。
接口使用现有 `libspine_tcm.so.3.0.1`。
本目录不分发该厂商库。
接口不修改设备权限、驱动或生产推理参数。

## 使用接口

Python 3 接口只依赖标准库。
将本目录加入 Python 模块搜索路径。
在 tmux 内运行板端检查。
所有设备访问必须持有项目固定共用锁。
封装自动取得该锁，也可以复用 `with-lock.sh` 继承的文件描述符 9。

```python
from tcm import Runtime

runtime = Runtime('/path/to/libspine_tcm.so.3.0.1')
print(runtime.status())
with runtime.acquire(0) as block:
    saved = block.read(4)
    try:
        block.write(b'TCM!')
        assert block.read(4) == b'TCM!'
    finally:
        block.write(saved)
```

示例会写入已申请块的前 4 个字节。
运行前必须确认没有其他未经共用锁保护的 TCM 使用者。
申请使用厂商 `mem_try_wait` 与 `mem_release` 配对接口。
读写必须在申请上下文和申请线程内执行。
接口拒绝越界范围、已释放块和跨进程对象。
接口要求块元数据与完整的可读写 `/dev/tcm` 映射一致。

命令行只提供查询和只读检查。

```bash
python3 spacemit/tcm/tcm.py status
python3 spacemit/tcm/tcm.py read 0 --size 16
```

运行库可以缓存首次初始化结果。
设备权限发生变化后，必须在新进程中重新检查。
普通用户没有设备权限时，中间层不能授予权限。
真实硬件不可用或运行库报告假 TCM 时，申请明确失败。
接口不回退到普通内存。

## 验证边界

本地测试使用内存夹具，检查边界、所有权、释放和回退拒绝行为。
夹具通过不证明真实硬件读写通过。
硬件状态与交付推理路径的调查见 `lab/tcm-final-release-20261016/`。
该中间层没有接入生产推理图。
不能从接口存在推断生产推理使用真实 TCM。
