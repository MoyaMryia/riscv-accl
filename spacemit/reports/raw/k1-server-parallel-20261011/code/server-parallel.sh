#!/bin/bash
set -euo pipefail
qemu_screen_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
cd "$qemu_screen_root"
source spacemit/bench/qemu-screen/server-env.sh
mkdir -p lab
exec 9>lab/qemu-screen-server.lock
flock 9
python3 spacemit/bench/qemu-screen/parallel.py "$@"
