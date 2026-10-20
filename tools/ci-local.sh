#!/usr/bin/env bash
# 本地和 CI 共用的检查命令。CI 依赖安装留在 workflow 中。
#   tools/ci-local.sh <lint|python>  在工作区运行一个阶段
#   tools/ci-local.sh --staged       提交前检查，pre-commit hook 调用
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# 触发路径（扩展正则，匹配暂存文件路径）。
PYTHON_PATHS='^(tools/|spacemit/bench/qemu-screen/predictor/freeze-sources\.py$|spacemit/bench/mtp-r3/|spacemit/serve/cached-document-chat\.py$|spacemit/serve/decode-router/)'

stage_lint() { python3 tools/writing_lint.py "$@"; }
stage_python() {
    bash -n spacemit/serve/decode-router/reproduce-bert.sh
    python3 -m unittest discover -s tools/tests -p 'test_*.py' -v
    python3 -m unittest discover -s spacemit/bench/mtp-r3 -p 'test_*.py' -v
    python3 -m unittest discover -s spacemit/serve/decode-router -p 'test_*.py' -v
}

# 测试读取工作区。检查范围内的工作区必须与暂存区一致，测试结果才对应将要提交的内容。
require_clean() {
    local paths="$1" dirty
    dirty=$( { git diff --name-only; git ls-files --others --exclude-standard; } | grep -E "$paths" || true)
    if [ -n "$dirty" ]; then
        echo "以下文件有未暂存或未跟踪的改动。暂存、还原或移走后再提交：" >&2
        echo "$dirty" >&2
        exit 1
    fi
}

staged() {
    local changed base
    changed=$(git diff --cached --name-only)
    [ -n "$changed" ] || exit 0
    base=HEAD
    git rev-parse -q --verify HEAD >/dev/null || base=
    stage_lint --staged ${base:+--base-ref "$base"}
    if grep -qE "$PYTHON_PATHS" <<<"$changed"; then
        require_clean "$PYTHON_PATHS"
        echo "== python ==" >&2
        stage_python
    fi
}

case "${1:-}" in
    --staged) staged ;;
    lint) shift; stage_lint "$@" ;;
    python) stage_python ;;
    *) echo "用法：$0 <lint|python|--staged>" >&2; exit 2 ;;
esac
