#!/usr/bin/env bash
# 在服务器串行执行部署检查。
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
server_result=lab/server-validation-20261011
mkdir "$server_result"
exec 9>lab/qemu-screen-server.lock
flock -n 9
trap 'server_status=$?; echo "$server_status" > "$server_result/exit-status"' EXIT
source spacemit/bench/qemu-screen/server-env.sh
printf '%s\n' verify-transfer > "$server_result/phase"
python3 lab/k1-server-deploy-20261011/verify-transfer.py
printf '%s\n' capability > "$server_result/phase"
python3 spacemit/bench/qemu-screen/run.py "$server_result/capability" \
  --qemu-prefix "$K1_QEMU_PREFIX" \
  --vendor-root lab/k1-qemu-feasibility-20261011/jdsk-qemu --os --os-vendor
printf '%s\n' cross-compile > "$server_result/phase"
python3 spacemit/bench/qemu-screen/prepare-conv.py "$server_result/conv-plan" \
  --tune spacemit-x60 --qemu-prefix "$K1_QEMU_PREFIX"
printf '%s\n' numerical-and-metrics > "$server_result/phase"
python3 spacemit/bench/qemu-screen/batch.py \
  "$server_result/conv-plan/plan.json" "$server_result/conv-result"
python3 - <<'PY'
import json
from pathlib import Path
result = json.loads(Path('lab/server-validation-20261011/conv-result/result.json').read_text())
assert result['status'] == 'screen-complete-needs-board'
assert len(result['cases']) == 4
for case in result['cases']:
    assert case['status'] == 'needs-board'
    assert case['arms']['control']['dump_sha256'] == case['arms']['candidate']['dump_sha256']
    assert case['arms']['control']['roi_threads'] == case['arms']['candidate']['roi_threads'] == 4
print('PASS: four shapes, full dumps and four threads')
PY
printf '%s\n' assembly-inventory > "$server_result/phase"
python3 spacemit/bench/qemu-screen/assembly-inventory.py \
  lab/k1-combined-fixture-r5-20261011-122000-work/payload/C/lib/libggml-cpu.so.0.16.0 \
  "$server_result/assembly" \
  --symbol-regex 'spine_k1_gdn_prefill128|spine_k1_ssm_conv_cpu|ggml_compute_forward_flash_attn_ext_f16_one_chunk|gemm_kernel_i8i4|gemm_kernel_i8i8|ggml_gdn_decode_step_rvv'
printf '%s\n' complete > "$server_result/phase"
