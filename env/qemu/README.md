# env/qemu — QEMU 11 (riscv64) 最小 Linux 启动

用 `qemu-system-riscv64`（QEMU **11.1.1**）启动一个 RISC-V 64 位最小 Linux，直接落到 root shell。

## 一、一键启动

```bash
cd env/qemu
./boot.sh                 # 默认 512MB 内存，落到 root shell
./boot.sh --rebuild 1024  # 先重建 initramfs，再用 1GB 内存启动
```

启动后进入 `(none):~#`（或 `#`）busybox root shell。退出用 `Ctrl-A x`（QEMU
`-nographic` 的默认停止快捷键），或 `Ctrl-C, quit`。

启动来源：`qemu-system-riscv64 -M virt -m 512M -smp 2 -bios <OpenSBI> \
  -kernel vmlinux-rv64 -initrd initramfs.cpio.gz -append "console=ttyS0 rdinit=/init" \
  -nographic -no-reboot`

## 二、组件（都在本目录）

| 文件 | 大小 | 说明 |
|---|---|---|
| `boot.sh` | 1.4KB | 启动脚本 |
| `vmlinux-rv64` | 31MB | 内核 Image（Debian 6.12.94 riscv64，EFI-stub） |
| `initramfs.cpio.gz` | 3.4MB | 已打好的 initramfs（busybox + `/init` + `/etc/inittab`） |
| `initrd-root/` | — | initramfs 源目录，用 `--rebuild` 重打 |

`boot.sh` 每次 `--rebuild` 会：`cd initrd-root && find . | cpio -o -H newc | gzip > initramfs.cpio.gz`。

## 三、镜像来源（教育网联，NJU 直连）

全部从 **`mirror.nju.edu.cn`**（校内直连）下载：

1. **内核**：Debian trixie riscv64 包，从 pool 提取 `boot/vmlinux`
   `https://mirror.nju.edu.cn/debian/pool/main/l/linux/linux-image-6.12.94+deb13-riscv64_6.12.94-1_riscv64.deb`
   提取：`dpkg-deb -x linux-image-riscv64.deb /tmp/x` 后取 `/tmp/x/boot/vmlinux-6.12.94+deb13-riscv64`。
2. **rootfs**：Alpine riscv64 minirootfs
   `https://mirror.nju.edu.cn/alpine/edge/releases/riscv64/alpine-minirootfs-20260805-riscv64.tar.gz`

注意：NJU 及国内教育镜像**没有** `debian-cloud-images`（Debian 官方 riscv64
cloud 镜像只在 `cloud.debian.org`，实测 ~210KB/s，慢且非教育网）；因此用
"Debian 内核 + Alpine rootfs" 组合，两种资源都落在 NJU 上。

## 四、验收标准

满足：能用 `qemu-system-riscv64` 启动、落到一个干净可用的 root shell。
自测（`/init` 打印后由 busybox init 在 ttyS0 上调起 `ash`，出现可交互提示符）：
`uname -m` → `riscv64`，且启动日志里**没有** `can't access tty` 或双 prompt。

实现细节：`/etc/inittab` 用 `::respawn:/bin/cttyhack /bin/ash`（而非
`/bin/getty`+`login`）——`cttyhack` 给 ash 一个合法的 controlling tty，
因此没有 `job control turned off` 警告，也不用 root 密码登录。之前用
`:/bin/ash` 的裸写法会在同一串口挂两只 shell，出现双 `(none):~#` 与
`can't access tty` 报错，已弃用。

## 五、为什么用 initramfs 而非 qcow2

Debian riscv64 内核把 `CONFIG_VIRTIO_BLK`、`CONFIG_EXT4_FS` 编为 `=m`，需要
内核模块才能挂盘；打包模块体积大。`CONFIG_BLK_DEV_INITRD=y` 且串口/控制台
（`CONFIG_SERIAL_8250_CONSOLE=y`、`CONFIG_VT_CONSOLE`）内建，故直接
`-kernel` + `-initrd` 落到 shell 最省事，无需挂盘。
