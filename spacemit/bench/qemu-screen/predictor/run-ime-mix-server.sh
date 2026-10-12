#!/usr/bin/env bash
# 在 tmux 内持有服务器共用锁。
set -euo pipefail
if [[ $# -ne 2 || -z ${TMUX:-} ]]; then
    echo '必须在 tmux 内提供载荷目录和新结果目录。' >&2
    exit 2
fi
ime_tools=$(cd "$(dirname "$0")" && pwd)
ime_payload=$(realpath "$1")
ime_output=$(realpath -m "$2")
mkdir "$ime_output"
ime_finish() {
    ime_status=$?
    printf '%s\n' "$ime_status" > "$ime_output/exit-status"
    exit "$ime_status"
}
trap ime_finish EXIT
exec 9>lab/qemu-screen-server.lock
printf '%s\n' waiting-lock > "$ime_output/phase"
flock 9
date -Is > "$ime_output/identity.log"
lscpu > "$ime_output/topology.log"
printf '%s\n' "$TMUX" > "$ime_output/tmux.log"
ime_vendor=$(realpath lab/k1-qemu-feasibility-20261011/jdsk-qemu)
export PKG_CONFIG_PATH="$(realpath lab/qemu-host-runtime/lib/pkgconfig)"
read -ra ime_flags <<< "$(pkg-config --cflags --libs glib-2.0)"
printf '%s\n' build-plugin > "$ime_output/phase"
cc -std=c11 -O2 -shared -fPIC -fvisibility=hidden -Wall -Wextra -Werror \
    -I"$ime_vendor/include" "$ime_tools/trace.c" -o "$ime_output/trace.so" \
    "${ime_flags[@]}" > "$ime_output/build-plugin.log" 2>&1
"$ime_vendor/bin/qemu-riscv64" --version > "$ime_output/qemu-version.log"
sha256sum "$ime_vendor/bin/qemu-riscv64" "$ime_vendor/include/qemu-plugin.h" \
    "$ime_tools/trace.c" "$ime_tools/load-use-trace.py" "$ime_output/trace.so" > "$ime_output/tool-identities.log"
printf '%s\n' running > "$ime_output/phase"
python3 "$ime_tools/load-use-trace.py" "$ime_payload" \
    --qemu "$ime_vendor/bin/qemu-riscv64" --cpu max,vlen=256,elen=64,vext_spec=v1.0 \
    --plugin "$ime_output/trace.so" \
    --profiles "$ime_tools/profiles/k1-cpu0-umode-20261012/components.json" \
    "$ime_tools/profiles/k1-cpu0-umode-20261012/ime.json" \
    "$ime_tools/profiles/k1-cpu0-umode-20261012/reductions.json" \
    "$ime_tools/profiles/k1-cpu0-umode-20261012/scalar.json" \
    "$ime_tools/profiles/k1-cpu0-umode-20261012/gaps.json" \
    --output "$ime_output/result" > "$ime_output/driver.log" 2>&1
printf '%s\n' complete > "$ime_output/phase"
