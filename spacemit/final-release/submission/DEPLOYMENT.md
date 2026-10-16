# 一键部署与重建

## 前提

目标设备为 SpacemiT K1，系统为 Linux RISC-V 64 位用户空间。
必须准备 Python 3、Bash、tmux、flock 和 `curl`。
必须提供 `DEPENDENCIES.md` 中匹配的模型及运行库。
生产构建的默认上下文为 12288，槽位为 1。
两个模型共用四线程、批大小 32、微批大小 32、F16 缓存和直接解码。
切换模型只需更改模型路径。

## 一键启动

在成果包根目录执行命令。
模型路径必须为本机实际文件。

```sh
bash deploy.sh /absolute/path/to/model.gguf
```

入口自动建立独立 tmux 会话及日志目录。
默认日志目录位于 `$HOME/Projects/k1-final-release-runs/`。
日志目录含 `deployment.json`、`server.log` 和 `launch.json`。
服务器退出后生成 `exit-status`。
部署入口拒绝覆盖已有日志目录或同名会话。
创建会话成功不表示模型加载成功。

依赖路径不同时，使用下列命令。
路径参数只定位依赖，不改变优化参数。

```sh
bash deploy.sh /absolute/path/to/model.gguf \
  --spert /absolute/path/to/spine-runtime.riscv64.0.6.2 \
  --tcm /absolute/path/to/spine-tcm \
  --session k1_committee_2b --port 8080
```

入口调用原 `runtime/package/start.py`。
该启动器核对模型、二进制和运行库 SHA-256，并清除继承的实验环境变量。
入口不接收线程、批大小、候选掩码或优化开关。
不能用其他 GGUF 文件名绕过身份检查。

## 共用锁与服务检查

全部板端测试与部署必须在 tmux 中持有固定共用锁。
一键入口自动满足此条件。
锁文件为 `$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock`。
已有任务持锁时，新会话等待锁释放。
不得结束其他人的进程以取得板卡。
不得在补测任务运行时重复启动本成果包。

查看入口输出的会话与日志路径。
确认 `server.log` 中没有身份或加载错误。
执行本地服务检查。

```sh
curl --fail --silent --show-error http://127.0.0.1:8080/health
```

接口成功只证明服务就绪，不替代性能或质量验收。
查看会话时，使用入口输出的实际会话名称。

```sh
tmux attach -t k1_committee_2b
```

只结束本次创建的会话与服务器。
不要同时运行两个模型服务。
服务器退出后，持锁命令退出并释放锁。

## 只读命令预览

下列命令输出部署命令，不创建会话或启动模型。
模型文件与成果包文件必须存在。
此预览不核验完整模型或运行库身份。

```sh
bash deploy.sh /absolute/path/to/model.gguf --describe
```

## 从源码重建

重建需要收据记录的 GCC 14、CMake、Ninja、SPERT 与 TCM 用户态库。
编译器必须支持厂商 IME 内建函数。
在 tmux 内执行下列命令。
新构建目录必须不存在。

```sh
bash runtime/package/with-lock.sh \
  bash runtime/package/build.sh runtime/source rebuilt
```

`runtime/package/build.sh` 保持原 r3 源码检查、编译选项和四任务构建上限。
新构建不自动继承原二进制的性能与数值验证。
默认一键部署始终使用随包的原生产构建。
重建验证必须单独保存收据和结果。

## 容量扩展

普通入口不提供性能或容量选项。
16k／32k 性能报告使用原二进制，并显式设置容量 20480／36864。
该补测不改变普通默认容量 12288。
复现容量扩展必须使用补测归档中的冻结控制器与协议。
