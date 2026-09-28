#!/usr/bin/env bash
# Continue independent board checks only after the active 4B baseline exits.
set -u

WAIT_PID=${1:?pass the active benchmark wrapper PID}
BENCH_ROOT=${BENCH_ROOT:-"$HOME/Projects/riscv-accl-bench-2026-09-27"}
exec 9>"$BENCH_ROOT/serial-followups.lock"
flock -n 9 || { echo 'another follow-up queue is active' >&2; exit 1; }

while [ -r "/proc/$WAIT_PID/status" ] &&
      ! grep -q '^State:.*Z' "/proc/$WAIT_PID/status"; do
  sleep 60
done

# A server may need a few seconds to release after its wrapper exits.
for ((tries=0; tries<24; tries++)); do
  if ! pgrep -x llama-server >/dev/null; then break; fi
  sleep 5
done
if pgrep -x llama-server >/dev/null; then
  echo 'server still active after wrapper exit; refusing to overlap jobs' >&2
  exit 1
fi

echo "START serial follow-ups $(date -Is)"
run_step() {
  local name=$1
  shift
  echo "START $name $(date -Is)"
  "$@" >"$BENCH_ROOT/$name.log" 2>&1
  local rc=$?
  echo "END $name rc=$rc $(date -Is)"
  tail -3 "$BENCH_ROOT/$name.log" | cut -c1-220
  return "$rc"
}

run_step run-weight-compare-2k \
  bash "$BENCH_ROOT/run-weight-compare-board.sh" || true
run_step run-2b-32k-feasibility \
  bash "$BENCH_ROOT/run-bounded-long-context-board.sh" || true

VULKAN_ROOT="$HOME/Projects/spacemit-llama-vulkan"
if [ -d "$VULKAN_ROOT/build" ]; then
  if run_step build-vulkan-resume \
    timeout --signal=TERM --kill-after=20s 7200s \
    cmake --build "$VULKAN_ROOT/build" --target llama-server -j4; then
    run_step run-vulkan-smoke \
      bash "$BENCH_ROOT/run-vulkan-smoke-board.sh" || true
  fi
fi
echo "END serial follow-ups $(date -Is)"
