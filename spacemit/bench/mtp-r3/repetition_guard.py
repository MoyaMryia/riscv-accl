#!/usr/bin/env python3
"""检测连续重复行，并在生成退化时提前停止请求。"""

DEFAULT_WINDOW = 3
DEFAULT_MIN_CHARS = 20


class DegenerateOutput(RuntimeError):
    """生成文本连续重复同一行。"""


class RepeatGuard:
    """按增量文本检测连续重复行。

    window 为连续相同行数。min_chars 为参与判断的最短行长。
    短行和空行会重置连续计数，避免把正常代码判为退化。
    """

    def __init__(self, window=DEFAULT_WINDOW, min_chars=DEFAULT_MIN_CHARS):
        if type(window) is not int or window < 2:
            raise ValueError('window must be an integer of at least 2')
        if type(min_chars) is not int or min_chars < 4:
            raise ValueError('min_chars must be an integer of at least 4')
        self.window = window
        self.min_chars = min_chars
        self.line = ''
        self.repeats = 0
        self.triggered_line = None

    def feed(self, delta):
        """接收一段增量文本；检测到连续重复时抛出 DegenerateOutput。"""
        if not isinstance(delta, str):
            raise TypeError('delta must be text')
        for char in delta:
            if char != '\n':
                self.line += char
                continue
            normalized = ' '.join(self.line.split())
            self.line = ''
            if len(normalized) < self.min_chars:
                self.repeats = 0
                continue
            if normalized == self.triggered_line:
                self.repeats += 1
            else:
                self.triggered_line = normalized
                self.repeats = 1
            if self.repeats >= self.window:
                raise DegenerateOutput('repeated line {} times: {}'.format(self.repeats, normalized[:80]))
