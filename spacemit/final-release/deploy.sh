#!/usr/bin/env bash
# 在独立 tmux 会话中启动交付构建。
set -euo pipefail
deploy_here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
exec python3 "$deploy_here/deploy.py" "$@"
