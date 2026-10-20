#!/usr/bin/env python3
"""代码检查的兼容入口。

检查实现只保留在发布候选目录。
本文件按路径加载该实现并重新导出公开名字，避免两份白名单漂移。
"""
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().parents[1] / 'release-candidate/tests/quality.py'
_SPEC = importlib.util.spec_from_file_location('release_candidate_quality', _PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
globals().update({name: value for name, value in vars(_MODULE).items() if not name.startswith('_')})
